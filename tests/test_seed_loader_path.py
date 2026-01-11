from probe.crawl.seed_loader import load_file


def test_load_file_with_explicit_path(tmp_path):
    p = tmp_path / "custom_seeds.txt"
    p.write_text("https://example.com/\n#comment\nhttps://example.org/page\n")

    urls = load_file(str(p))
    assert len(urls) == 2
    assert "https://example.org/page" in urls
