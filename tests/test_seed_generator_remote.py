from probe.analysis.seed_generator import SeedGenerator


def test_discover_sitemap_and_robots(monkeypatch):
    sg = SeedGenerator(None, fetch_remote=True)

    # Mock httpx.get to return a sample sitemap and robots
    class Dummy:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            return None

    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url>
        <loc>https://example.com/datasheet1.pdf</loc>
      </url>
    </urlset>
    """

    robots_txt = """
    User-agent: *
    Disallow: /private
    """

    def fake_get(url, timeout=0):
        if url.endswith("sitemap.xml"):
            return Dummy(sitemap_xml)
        if url.endswith("robots.txt"):
            return Dummy(robots_txt)
        raise RuntimeError("unexpected")

    monkeypatch.setattr("httpx.get", fake_get)

    urls = sg.discover_sitemap("example.com")
    assert "https://example.com/datasheet1.pdf" in urls

    dis = sg.discover_robots_disallows("example.com")
    assert "/private" in dis

    # generate_seeds_for_domain should avoid disallowed paths
    seeds = sg.generate_seeds_for_domain(
        "example.com", "datasheet", limit=5, fetch_remote=True
    )
    assert all("/private" not in s for s in seeds)
