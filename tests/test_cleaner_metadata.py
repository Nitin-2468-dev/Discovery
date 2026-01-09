from probe.crawl.cleaner import clean_html


def test_cleaner_returns_description_and_pdf_counts():
    html = '''
    <html>
      <head>
        <title> Test </title>
        <meta name="description" content="This is a short desc">
      </head>
      <body>
        <p>Content here</p>
        <a href="/file.pdf">PDF</a>
        <a href="/other">Other</a>
        <nav>Nav text</nav>
      </body>
    </html>
    '''

    res = clean_html(html, "https://example.com/page.html")
    assert res["description"] == "This is a short desc"
    assert res["pdf_link_count"] == 1
    assert res["link_count"] == 2
    # Boilerplate ratio should be a float between 0 and 1
    assert 0.0 <= res["boilerplate_ratio"] <= 1.0
