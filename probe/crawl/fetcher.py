"""Simple sync fetcher for v0.2.

Public API:
- fetch(url, timeout=10, max_size=10_000_000) -> dict with keys:
  url, status_code, headers, content_type, is_pdf, text, links, error, metadata

This is an initial, test-driven implementation focusing on HTML cleaning and link extraction.
"""

import threading
from typing import Any, Dict, List, Tuple
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from probe.observability import get_logger

logger = get_logger("fetcher")

# In-memory per-domain politeness tracker (monotonic timestamps)
_last_fetch: Dict[str, float] = {}
_last_fetch_lock = threading.Lock()


DEFAULT_TIMEOUT = 10
DEFAULT_MAX_SIZE = 10_000_000  # 10 MB


class Fetcher:
    """Stateful fetcher with per-instance politeness, user-agent rotation and DI.

    Parameters:
    - user_agents: optional list of user-agent strings to rotate per request (round-robin)
    - metrics: optional metrics object (defaults to probe.observability.metrics)
    - logger: optional logger (defaults to probe.observability.get_logger('fetcher'))
    - sleep_func: optional sleep function for testing/time control
    """

    def __init__(
        self, user_agents=None, metrics_obj=None, logger_obj=None, sleep_func=None
    ):
        self.user_agents = list(user_agents) if user_agents else ["probe/0.1"]
        self._ua_index = 0
        self._ua_lock = threading.Lock()
        # dependency injection (defaults to module-level observability)
        from probe import observability as _obs

        self.metrics = metrics_obj if metrics_obj is not None else _obs.metrics
        self.logger = logger_obj if logger_obj is not None else get_logger("fetcher")
        self._sleep_func = sleep_func
        self._last_fetch = {}
        self._last_fetch_lock = threading.Lock()

    def fetch(  # noqa: C901 - complex fetch/retry logic, will refactor in follow-up
        self,
        url: str,
        timeout: int = DEFAULT_TIMEOUT,
        max_size: int = DEFAULT_MAX_SIZE,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        min_delay: float = 0.0,
        honor_retry_after: bool = True,
        sleep_func=None,
    ) -> Dict[str, Any]:
        """Fetch a URL and return structured result (instance method).

        Mirrors the old functional API but keeps per-instance politeness state.
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

        def _default_sleep(s):
            time.sleep(s)

        # choose sleep function: instance override -> call param -> default
        if self._sleep_func is not None:
            default_sleep = self._sleep_func
        else:
            default_sleep = _default_sleep

        if sleep_func is None:
            sleep_func = default_sleep

        # Enforce per-instance per-domain politeness
        try:
            domain = urlparse(url).netloc
            now_mon = time.monotonic()
            if min_delay and min_delay > 0:
                with self._last_fetch_lock:
                    last = self._last_fetch.get(domain)
                    if last is not None:
                        elapsed = now_mon - last
                        if elapsed < min_delay:
                            wait = min_delay - elapsed
                            sleep_func(wait)
                    # reserve domain
                    self._last_fetch[domain] = time.monotonic()

            # Select and rotate User-Agent
            with self._ua_lock:
                ua = self.user_agents[self._ua_index % len(self.user_agents)]
                self._ua_index += 1

            with httpx.Client(timeout=timeout, headers={"User-Agent": ua}) as client:
                for attempt in range(0, max_retries + 1):
                    try:
                        start = time.monotonic()
                        resp = client.get(url, follow_redirects=True)
                        elapsed = int((time.monotonic() - start) * 1000)

                        result["status_code"] = resp.status_code
                        result["headers"] = dict(resp.headers)
                        content_type = resp.headers.get("content-type", "").lower()
                        result["content_type"] = content_type
                        result["final_url"] = str(resp.url)
                        # redirect history length
                        try:
                            result["redirect_count"] = (
                                len(resp.history)
                                if getattr(resp, "history", None) is not None
                                else 0
                            )
                        except Exception:
                            result["redirect_count"] = 0

                        # metrics & logs: record attempt/start
                        try:
                            self.metrics.increment("fetch_total")
                            self.logger.debug("Fetching %s attempt=%s", url, attempt)
                        except Exception:
                            pass

                        # 429 handling: Retry-After header
                        try:
                            logger.debug(
                                "resp_status=%s attempt=%s", resp.status_code, attempt
                            )
                        except Exception:
                            pass
                        if resp.status_code == 429 and attempt < max_retries:
                            ra = resp.headers.get("retry-after")
                            delay = None
                            parsed_info = None
                            if ra is not None and honor_retry_after:
                                # Try numeric seconds first
                                try:
                                    delay = float(ra)
                                    parsed_info = ("seconds", delay)
                                except Exception:
                                    # Then try HTTP-date formats (RFC-1123 etc.)
                                    try:
                                        from datetime import datetime, timezone
                                        from email.utils import \
                                            parsedate_to_datetime

                                        dt = parsedate_to_datetime(ra)
                                        if dt.tzinfo is None:
                                            dt = dt.replace(tzinfo=timezone.utc)
                                        now = datetime.now(timezone.utc)
                                        delta = (dt - now).total_seconds()
                                        delay = max(0.0, delta)
                                        parsed_info = ("http-date", dt.isoformat())
                                    except Exception:
                                        delay = None
                            else:
                                # honoring disabled or no header
                                delay = backoff_factor * (2**attempt)
                                parsed_info = (
                                    (
                                        "ignored"
                                        if ra is not None and not honor_retry_after
                                        else "backoff"
                                    ),
                                    delay,
                                )

                            # Debug log about Retry-After parsing / policy
                            try:
                                logger.debug(
                                    "Retry-After header=%r honor=%r parsed_as=%r delay=%s",
                                    ra,
                                    honor_retry_after,
                                    parsed_info,
                                    delay,
                                )
                            except Exception:
                                pass

                            # metrics: record retry/backoff wait
                            try:
                                self.metrics.increment("fetch_retries")
                                if delay is not None:
                                    self.metrics.observe(
                                        "fetch_backoff_seconds", float(delay)
                                    )
                            except Exception:
                                pass

                            sleep_func(delay)
                            continue
                        if 500 <= resp.status_code < 600 and attempt < max_retries:
                            delay = backoff_factor * (2**attempt)
                            sleep_func(delay)
                            continue

                        if resp.status_code >= 400:
                            result["error"] = f"http_{resp.status_code}"
                            result["fetch_duration_ms"] = elapsed
                            result["retry_count"] = attempt
                            try:
                                self.metrics.increment("fetch_failures")
                            except Exception:
                                pass
                            self.logger.info(
                                "Fetch failed %s status=%s", url, resp.status_code
                            )
                            return result

                        # Stream content while enforcing max_size
                        content = bytearray()
                        for chunk in resp.iter_bytes():
                            content.extend(chunk)
                            if len(content) > max_size:
                                result["error"] = "max_size_exceeded"
                                result["metadata"]["downloaded"] = len(content)
                                result["fetch_duration_ms"] = elapsed
                                result["retry_count"] = attempt
                                return result

                        # Save raw bytes for hashing/storage
                        result["raw_bytes"] = bytes(content)
                        result["content_length"] = (
                            len(result["raw_bytes"]) if result.get("raw_bytes") else 0
                        )
                        result["fetch_duration_ms"] = elapsed
                        result["retry_count"] = attempt
                        # Expose user-agent used
                        try:
                            result["user_agent"] = client.headers.get("User-Agent")
                        except Exception:
                            # Use selected UA as fallback
                            result["user_agent"] = ua

                        # metrics: observe duration
                        try:
                            self.metrics.observe(
                                "fetch_duration_seconds", elapsed / 1000.0
                            )
                        except Exception:
                            pass

                        # PDF handling (real pdfplumber extraction with OCR fallback)
                        if "application/pdf" in content_type or url.lower().endswith(
                            ".pdf"
                        ):
                            result["is_pdf"] = True
                            try:
                                from io import BytesIO

                                import pdfplumber

                                with pdfplumber.open(BytesIO(content)) as pdf:
                                    pages = [p.extract_text() or "" for p in pdf.pages]
                                    text = "\n".join(pages)
                                    if not text.strip():
                                        raise ValueError("empty_pdf_text")
                                    result["text"] = text
                                    result["metadata"]["pages"] = len(pages)
                                    result["link_count"] = 0
                                    result["has_pdf_links"] = False
                            except Exception:
                                # Attempt OCR fallback if available
                                try:
                                    ocr_text = _ocr_pdf(bytes(content))
                                    result["text"] = ocr_text
                                    result["metadata"]["ocr_used"] = True
                                except Exception:
                                    result["error"] = "pdf_extraction_failed"
                            return result  # Otherwise treat as HTML/text
                        encoding = resp.encoding or "utf-8"
                        html = bytes(content).decode(encoding, errors="replace")
                        cleaned_text, links, title = _clean_html_and_extract_links(
                            html, base_url=url
                        )
                        result["text"] = cleaned_text
                        result["links"] = links
                        result["title"] = title
                        result["link_count"] = len(links)
                        result["has_pdf_links"] = any(
                            str(link.get("url", "")).lower().endswith(".pdf")
                            for link in links
                        )
                        return result

                    except httpx.TimeoutException:
                        # retry on timeout if attempts remain
                        if attempt < max_retries:
                            delay = backoff_factor * (2**attempt)
                            sleep_func(delay)
                            continue
                        result["error"] = "timeout"
                        result["fetch_duration_ms"] = 0
                        result["retry_count"] = attempt
                        return result
                    except httpx.HTTPError as exc:  # covers many transport errors
                        if attempt < max_retries:
                            delay = backoff_factor * (2**attempt)
                            sleep_func(delay)
                            continue
                        result["error"] = f"http_error: {exc}"
                        result["fetch_duration_ms"] = 0
                        result["retry_count"] = attempt
                        return result
        except Exception as exc:
            # Unexpected error during setup or client creation
            result["error"] = f"client_error: {exc}"
            return result

        # Ensure we always return a result (mypy can't always prove loop returns)
        return result


def _ocr_pdf(pdf_bytes: bytes) -> str:
    """OCR fallback: attempts to convert PDF bytes to images and run Tesseract.

    Requires `pdf2image` and `pytesseract` to be available. If not available, raises ImportError.
    This function is best-effort and may be slow; callers should guard by size/timeout.
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except Exception as exc:
        raise ImportError("OCR dependencies not available") from exc

    images = convert_from_bytes(pdf_bytes)
    texts = []
    for img in images:
        text = pytesseract.image_to_string(img)
        texts.append(text)
    return "\n".join(texts)


# Backwards compatibility: module-level default fetcher and helper
DEFAULT_FETCHER = Fetcher()


def fetch(
    url: str,
    timeout: int = DEFAULT_TIMEOUT,
    max_size: int = DEFAULT_MAX_SIZE,
    max_retries: int = 3,
    backoff_factor: float = 0.5,
    min_delay: float = 0.0,
    honor_retry_after: bool = True,
    sleep_func=None,
) -> Dict[str, Any]:
    return DEFAULT_FETCHER.fetch(
        url,
        timeout=timeout,
        max_size=max_size,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
        min_delay=min_delay,
        honor_retry_after=honor_retry_after,
        sleep_func=sleep_func,
    )


def _clean_html_and_extract_links(
    html: str, base_url: str
) -> Tuple[str, List[Dict[str, object]], str]:
    """Return (cleaned_text, links, title).

    Links are normalized absolute HTTP(s) URLs with anchor text and metadata. Title
    is taken from the `<title>` tag when present.
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

    title_tag = (
        str(soup.title.string).strip() if soup.title and soup.title.string else None
    )
    text = soup.get_text(" ", strip=True)

    links: List[Dict[str, object]] = []
    for a in soup.find_all("a", href=True):
        raw = str(a["href"]).strip()
        if not raw:
            continue
        abs_url = urljoin(base_url, raw)
        p = urlparse(abs_url)
        if p.scheme in ("http", "https"):
            links.append({"url": abs_url, "text": a.get_text(" ", strip=True)})

    return text, links, title_tag or ""
