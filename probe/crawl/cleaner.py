"""HTML cleaning utilities for Probe crawl pipeline.

Provides:
- clean_html(html: str, base_url: str) -> dict

Returns dict with keys:
- title: str
- text: str (cleaned, whitespace-normalized)
- text_length: int
- links: list[dict] with keys 'url' and 'text'
"""
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict


def clean_html(html: str, base_url: str) -> Dict:
    """Clean HTML and extract title, normalized text, and absolute links.

    Args:
        html: raw HTML string
        base_url: base URL used to resolve relative links

    Returns:
        dict with title, text, text_length, links
    """
    soup = BeautifulSoup(html, "lxml") if html is not None else BeautifulSoup("", "lxml")

    # Remove noisy, non-content elements
    for tag in soup(["script", "style", "nav", "footer", "aside", "header", "noscript"]):
        tag.decompose()

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # Main text: get_text with a space separator then normalize whitespace
    raw_text = soup.get_text(separator=" ", strip=True)
    text = " ".join(raw_text.split())

    # Extract links and resolve relative URLs
    links: List[Dict[str, str]] = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href:
            continue
        abs_url = urljoin(base_url, href)
        links.append({"url": abs_url, "text": a.get_text(strip=True)})

    return {"title": title, "text": text, "text_length": len(text), "links": links}
