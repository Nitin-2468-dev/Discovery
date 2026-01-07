"""Simple sync fetcher for v0.2.

Public API:
- fetch(url, timeout=10, max_size=10_000_000) -> dict with keys:
  url, status_code, headers, content_type, is_pdf, text, links, error, metadata

This is an initial, test-driven implementation focusing on HTML cleaning and link extraction.
"""
from typing import Tuple, List, Dict, Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 10
DEFAULT_MAX_SIZE = 10_000_000  # 10 MB


def fetch(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_size: int = DEFAULT_MAX_SIZE,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    sleep_func=None,
) -> Dict[str, Any]:
    """Fetch a URL and return structured result.

    Parameters:
    - url: URL to fetch
    - timeout: seconds for httpx client timeout
    - max_size: maximum response size in bytes
    - max_retries: retry attempts for transient errors (429, 5xx, timeouts)
    - backoff_factor: base backoff multiplier (seconds)
    - sleep_func: optional function to call for sleeping (useful in tests)

    Returns a dict with keys: url, status_code, headers, content_type, is_pdf,
    text, links, title, raw_bytes, error, metadata
    """
    result: Dict[str, Any] = {
        "url": url,
        "status_code": None,
        "headers": {},
        "content_type": None,
        "is_pdf": False,
        "text": "",
        "links": [],
        "error": None,
        "metadata": {},
    }

    import time

    # retry/backoff params (allow overriding sleep in tests)
    def _sleep(s):
        time.sleep(s)

    # Parameters for retries/backoff
    max_retries = 3
    backoff_factor = 0.5
    sleep_func = _sleep

    with httpx.Client(timeout=timeout, headers={"User-Agent": "probe/0.1"}) as client:
        for attempt in range(0, max_retries + 1):
            try:
                resp = client.get(url, follow_redirects=True)
                result["status_code"] = resp.status_code
                result["headers"] = dict(resp.headers)
                content_type = resp.headers.get("content-type", "").lower()
                result["content_type"] = content_type

                # 429 / 5xx handling: retryable
                if resp.status_code == 429 and attempt < max_retries:
                    ra = resp.headers.get("retry-after")
                    try:
                        delay = int(ra) if ra is not None else backoff_factor * (2 ** attempt)
                    except Exception:
                        delay = backoff_factor * (2 ** attempt)
                    sleep_func(delay)
                    continue
                if 500 <= resp.status_code < 600 and attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    sleep_func(delay)
                    continue

                if resp.status_code >= 400:
                    result["error"] = f"http_{resp.status_code}"
                    return result

                            # Stream content while enforcing max_size
                content = bytearray()
                for chunk in resp.iter_bytes():
                    content.extend(chunk)
                    if len(content) > max_size:
                        result["error"] = "max_size_exceeded"
                        result["metadata"]["downloaded"] = len(content)
                        return result

                # Save raw bytes for hashing/storage
                result["raw_bytes"] = bytes(content)

                # PDF handling (real pdfplumber extraction)
                if "application/pdf" in content_type or url.lower().endswith(".pdf"):
                    result["is_pdf"] = True
                    try:
                        import pdfplumber
                        from io import BytesIO

                        with pdfplumber.open(BytesIO(content)) as pdf:
                            pages = [p.extract_text() or "" for p in pdf.pages]
                            result["text"] = "\n".join(pages)
                            result["metadata"]["pages"] = len(pages)
                    except Exception:
                        # Best-effort: leave text empty and surface a hint
                        result["error"] = "pdf_extraction_failed"
                    return result

                # Otherwise treat as HTML/text
                encoding = resp.encoding or "utf-8"
                html = bytes(content).decode(encoding, errors="replace")
                cleaned_text, links, title = _clean_html_and_extract_links(html, base_url=url)
                result["text"] = cleaned_text
                result["links"] = links
                result["title"] = title
                return result

            except httpx.TimeoutException:
                # retry on timeout if attempts remain
                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    sleep_func(delay)
                    continue
                result["error"] = "timeout"
                return result
            except httpx.HTTPError as exc:  # covers many transport errors
                if attempt < max_retries:
                    delay = backoff_factor * (2 ** attempt)
                    sleep_func(delay)
                    continue
                result["error"] = f"http_error: {exc}"
                return result


def _clean_html_and_extract_links(html: str, base_url: str) -> Tuple[str, List[Dict[str, str]], str]:
    """Return (cleaned_text, links, title).

    Links are normalized absolute HTTP(s) URLs with anchor text. Title is taken
    from the `<title>` tag when present.
    """
    soup = BeautifulSoup(html, "lxml")

    # Remove scripts/styles
    for elt in soup(["script", "style"]):
        elt.decompose()

    # Remove comments
    from bs4 import Comment
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        try:
            comment.extract()
        except Exception:
            pass

    title_tag = soup.title.string.strip() if soup.title and soup.title.string else None
    text = soup.get_text(" ", strip=True)

    links: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        raw = a["href"].strip()
        if not raw:
            continue
        abs_url = urljoin(base_url, raw)
        p = urlparse(abs_url)
        if p.scheme in ("http", "https"):
            links.append({"url": abs_url, "text": a.get_text(" ", strip=True)})

    return text, links, title_tag or ""
