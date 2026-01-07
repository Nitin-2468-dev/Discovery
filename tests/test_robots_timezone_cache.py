from datetime import datetime, timedelta, timezone
import probe.crawl.robots as robots
from urllib.robotparser import RobotFileParser


def test_robots_cache_timestamps_are_timezone_aware(monkeypatch):
    robots.clear_cache()
    domain = "example.com"

    # monkeypatch the fetch to return a simple parser
    def fake_fetch_and_parse(d):
        rp = RobotFileParser()
        rp.parse([])
        return rp

    monkeypatch.setattr(robots, "_fetch_and_parse", fake_fetch_and_parse)

    rp = robots._get_parser(domain)
    assert rp is not None

    # ensure cached timestamp is timezone-aware and in UTC
    entry = robots._cache.get(domain)
    assert entry is not None
    _, fetched_at = entry
    assert isinstance(fetched_at, datetime)
    assert fetched_at.tzinfo is not None
    assert fetched_at.tzinfo == timezone.utc


def test_robots_cache_respects_ttl_and_refetches(monkeypatch):
    robots.clear_cache()
    domain = "example.org"

    # first fetch returns rp1
    rp1 = RobotFileParser()
    rp1.parse([])
    monkeypatch.setattr(robots, "_fetch_and_parse", lambda d: rp1)
    got1 = robots._get_parser(domain)
    assert got1 is rp1

    # make cached timestamp stale: older than CACHE_TTL
    stale_time = datetime.now(timezone.utc) - robots.CACHE_TTL - timedelta(minutes=1)
    robots._cache[domain] = (rp1, stale_time)

    # new fetch returns rp2
    rp2 = RobotFileParser()
    rp2.parse(["User-agent: *\nDisallow: /"])
    monkeypatch.setattr(robots, "_fetch_and_parse", lambda d: rp2)

    got2 = robots._get_parser(domain)
    assert got2 is rp2
