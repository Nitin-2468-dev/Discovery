from probe.crawl.link_signals import (
    LinkContextStore,
    analyze_link_from_lines,
    extract_context_text,
    extract_tokens,
    score_tokens,
)


def test_extract_context_lines_mode():
    lines = [
        "Intro line",
        "# Section A",
        "Some content about drivers",
        "Link anchor here",
        "More detail about RTL8111 driver",
        "Footer",
    ]
    ctx, heading = extract_context_text(lines, 3, mode="lines", radius=2)
    assert "Link anchor here" in ctx
    assert heading is None


def test_extract_context_heading_mode():
    lines = [
        "Title",
        "# Drivers",
        "Info about drivers",
        "Link anchor here",
    ]
    ctx, heading = extract_context_text(lines, 3, mode="heading", radius=2)
    assert "Drivers" in heading
    assert "Link anchor here" in ctx


def test_extract_tokens_and_score():
    text = "Linux kernel drivers RTL8111 Gigabit Ethernet Controller Supported kernels 5.10+"
    tokens = extract_tokens(text)
    assert "linux" in tokens
    assert "rtl8111" in tokens
    score = score_tokens(
        tokens,
        heuristics={
            "keyword_weight": 0.3,
            "entity_weight": 0.4,
            "section_weight": 0.2,
            "file_hint_weight": 0.1,
            "keywords": {"driver": 0.3},
            "entities": {"rtl8111"},
            "file_hints": {},
        },
    )
    assert score > 0


def test_analyze_and_store(tmp_path):
    lines = [
        "Intro",
        "# Drivers",
        "Linux kernel drivers",
        "Link anchor here",
        "RTL8111 Gigabit Ethernet Controller",
    ]
    ctx = analyze_link_from_lines(
        "/page.html", "https://example.com/rtl8111", lines, 3, mode="lines", radius=2
    )
    assert ctx.relevance_score >= 0
    store = LinkContextStore(str(tmp_path / "lc.db"))
    rid = store.insert(ctx)
    assert rid > 0
    rows = store.list_recent(10)
    assert any(r.to_url == ctx.to_url for r in rows)
