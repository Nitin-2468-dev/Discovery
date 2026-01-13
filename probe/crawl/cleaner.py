"""HTML cleaning utilities for Probe crawl pipeline.

Provides:
- clean_html(html: str, base_url: str) -> dict

Returns dict with keys:
- title: str
- text: str (cleaned, whitespace-normalized)
- text_length: int
- links: list[dict] with keys 'url' and 'text'
"""

from typing import Dict, List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup


def clean_html(html: str, base_url: str) -> Dict:
    """Clean HTML and extract title, normalized text, and absolute links.

    Args:
        html: raw HTML string
        base_url: base URL used to resolve relative links

    Returns:
        dict with title, text, text_length, links
    """
    soup = (
        BeautifulSoup(html, "lxml") if html is not None else BeautifulSoup("", "lxml")
    )

    # Remove noisy, non-content elements
    for tag in soup(
        ["script", "style", "nav", "footer", "aside", "header", "noscript"]
    ):
        tag.decompose()

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Meta description
    meta_desc = ""
    md = soup.find("meta", attrs={"name": "description"})
    if md and md.get("content"):
        meta_desc = md.get("content").strip()

    # Main text: get_text with a space separator then normalize whitespace
    raw_text = soup.get_text(separator=" ", strip=True)
    text = " ".join(raw_text.split())

    # Extract links and resolve relative URLs, ignore mailto: javascript: and fragments
    links: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href.startswith(("#", "javascript:", "mailto:")):
            continue
        abs_url = urljoin(base_url, href)
        p = urlparse(abs_url)
        if p.scheme not in ("http", "https"):
            continue
        links.append(
            {
                "url": abs_url,
                "text": a.get_text(strip=True),
                "is_pdf": abs_url.lower().endswith(".pdf"),
            }
        )

    link_count = len(links)
    pdf_link_count = sum(1 for link in links if link.get("is_pdf"))

    # Calculate a simple boilerplate ratio: text in nav/footer/aside vs total text
    nav_text = " ".join(
        [t.get_text(" ", strip=True) for t in soup.find_all(["nav", "footer", "aside"])]
    )
    boilerplate_ratio = (len(nav_text) / max(len(text), 1)) if text else 0.0

    return {
        "title": title,
        "description": meta_desc,
        "text": text,
        "text_length": len(text),
        "links": links,
        "link_count": link_count,
        "pdf_link_count": pdf_link_count,
        "boilerplate_ratio": boilerplate_ratio,
    }
