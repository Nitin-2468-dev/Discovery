from probe.crawl.seed_loader import filter_by_domain, load_file, summarize


def test_load_file(tmp_path):
    p = tmp_path / "seeds.txt"
    p.write_text("# comment\nhttps://example.com/\n\nhttps://example.org/page\n")
    urls = load_file(str(p))
    assert len(urls) == 2
    assert urls[0] == "https://example.com/"


def test_filter_and_summarize():
    urls = [
        "https://example.com/a",
        "https://example.org/b",
        "https://example.com/c",
    ]
    filtered = filter_by_domain(urls, ["example.com"])
    assert len(filtered) == 2
    sums = summarize(urls)
    assert sums.get("example.com") == 2
    assert sums.get("example.org") == 1
