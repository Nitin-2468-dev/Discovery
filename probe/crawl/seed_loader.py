"""
probe/crawl/seed_loader.py

Utility for loading and managing seed URLs from text files.
"""

from pathlib import Path
from typing import List
from urllib.parse import urlparse


class SeedLoader:
    """Load and validate seed URLs from text files."""

    def __init__(self, seeds_dir: str = "seeds"):
        self.seeds_dir = Path(seeds_dir)

    def load_file(self, filename: str) -> List[str]:
        """
        Load URLs from a seed file.

        Accepts either:
        - a filename inside the `seeds/` directory (e.g., "aviation_engines.txt"), or
        - an absolute or relative path to a file (e.g., "./seeds/aviation_engines.txt").

        Format:
        - One URL per line
        - Lines starting with # are comments
        - Blank lines are ignored
        - Inline comments supported (text after #)

        Args:
            filename: Name or path to seed file

        Returns:
            List of valid URLs
        """
        from pathlib import Path

        # If the provided name looks like a path or exists as-is, use it directly
        candidate = Path(filename)
        if candidate.is_file():
            filepath = candidate
        else:
            filepath = self.seeds_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"Seed file not found: {filepath}")

        urls = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and full-line comments
                if not line or line.startswith("#"):
                    continue

                # Remove inline comments
                if "#" in line:
                    line = line.split("#")[0].strip()

                # Validate URL
                if self._is_valid_url(line):
                    urls.append(line)
                else:
                    print(f"Warning: Invalid URL at line {line_num}: {line}")

        return urls

    def load_multiple(self, filenames: List[str]) -> List[str]:
        """
        Load URLs from multiple seed files.
        Automatically deduplicates.
        """
        all_urls = []
        for filename in filenames:
            try:
                urls = self.load_file(filename)
                all_urls.extend(urls)
                print(f"✓ Loaded {len(urls)} URLs from {filename}")
            except FileNotFoundError as e:
                print(f"✗ {e}")

        # Deduplicate while preserving order
        seen = set()
        unique_urls = []
        for url in all_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)

        print(f"✓ Total unique URLs: {len(unique_urls)}")
        return unique_urls

    def filter_by_domain(self, urls: List[str], domains: List[str]) -> List[str]:
        """Filter URLs to only include specific domains."""
        allowed_domains = set(domains)
        filtered = []

        for url in urls:
            domain = self._extract_domain(url)
            if domain in allowed_domains:
                filtered.append(url)

        return filtered

    def group_by_domain(self, urls: List[str]) -> Dict[str, List[str]]:
        """Group URLs by their domain."""
        groups: Dict[str, List[str]] = {}

        for url in urls:
            domain = self._extract_domain(url)
            if domain not in groups:
                groups[domain] = []
            groups[domain].append(url)

        return groups

    def _is_valid_url(self, url: str) -> bool:
        """Check if string is a valid HTTP(S) URL."""
        try:
            parsed = urlparse(url)
            return parsed.scheme in ("http", "https") and parsed.netloc != ""
        except Exception:
            return False

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc


# Backwards compatible helpers


def load_file(path: str):
    return SeedLoader().load_file(path)


def filter_by_domain(urls, domains):
    return SeedLoader().filter_by_domain(urls, domains)


def summarize(urls):
    groups: Dict[str, List[str]] = SeedLoader().group_by_domain(urls)
    return {k: len(v) for k, v in groups.items()}


def create_seed_files():
    """Helper to create seed directory structure."""
    seeds_dir = Path("seeds")
    seeds_dir.mkdir(exist_ok=True)

    # Create README
    readme = seeds_dir / "README.md"
    readme.write_text(
        """# Seed URLs

This directory contains seed URL lists for testing and investigation.

## Format

- One URL per line
- Lines starting with `#` are comments
- Blank lines are ignored
- Inline comments supported: `https://example.com  # comment`

## Files

- `test_simple.txt` - Simple, reliable sites for initial testing
- `test_challenging.txt` - Edge cases and error handling
- `aviation_engines.txt` - Aviation engine documentation
- `pdf_focused.txt` - Sites with technical PDFs
- `example_queries.txt` - Query-based seed examples

## Usage

```python
from probe.crawl.seed_loader import SeedLoader

loader = SeedLoader()
urls = loader.load_file("test_simple.txt")
print(f"Loaded {len(urls)} URLs")
```
"""
    )

    print(f"✓ Created seed directory: {seeds_dir}")
    print(f"✓ Created README: {readme}")


if __name__ == "__main__":
    # Test the loader
    import sys

    if len(sys.argv) > 1:
        filename = sys.argv[1]
        loader = SeedLoader()

        try:
            urls = loader.load_file(filename)
            print(f"\n✓ Loaded {len(urls)} URLs from {filename}\n")

            # Show domains
            domains = loader.group_by_domain(urls)
            print("Domains:")
            for domain, domain_urls in sorted(
                domains.items(), key=lambda x: len(x[1]), reverse=True
            ):
                print(f"  {domain}: {len(domain_urls)} URLs")

        except Exception as e:
            print(f"Error: {e}")
    else:
        # Create seed structure
        create_seed_files()
        print("\nUsage: python seed_loader.py <filename>")
        print("Example: python seed_loader.py test_simple.txt")
