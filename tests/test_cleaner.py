from probe.crawl.cleaner import clean_html


def test_cleaner_removes_noisy_tags_and_extracts_text():
    html = """
    <html>
      <head><title>  Test Page  </title><style>body{}</style></head>
      <body>
        <nav>menu</nav>
        <h1>Article Heading</h1>
        <p>Some <b>useful</b> content.</p>
        <script>console.log('x')</script>
        <footer>copyright</footer>
      </body>
    </html>
    """

    res = clean_html(html, "https://example.com/page.html")
    assert res["title"] == "Test Page"
    assert "Article Heading" in res["text"]
    assert "Some useful content." in res["text"]
    # Ensure scripts/styles/footer/nav removed from text
    assert "menu" not in res["text"]
    assert res["text_length"] == len(res["text"])


def test_cleaner_resolves_relative_links():
    html = '<a href="/about">About</a> <a href="../contact">Contact</a>'
    res = clean_html(html, "https://example.com/dir/page.html")
    urls = [link["url"] for link in res["links"]]
    assert "https://example.com/about" in urls
    assert "https://example.com/contact" in urls


def test_cleaner_extracts_link_text_and_handles_empty_href():
    html = '<a href="/a">Link A</a><a href="">Empty</a>'
    res = clean_html(html, "https://example.com/")
    assert any(
        link["text"] == "Link A" and link["url"].endswith("/a") for link in res["links"]
    )
    # ensure empty href is ignored
    assert not any(link["text"] == "Empty" for link in res["links"])
