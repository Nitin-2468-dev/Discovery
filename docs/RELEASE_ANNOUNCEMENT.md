# Release v0.5 Announcement Drafts

Short (Slack/GitHub):

- Probe v0.5 baseline snapshot (2026-01-18): packaging and CI resilience improvements, packaging smoke job, wheel-install retry and test diagnostic uploads. See `CHANGELOG.md` and the packaging smoke job artifacts in CI for details.

---

# Release v0.4.1 Announcement Drafts

Short (Slack/GitHub):

- Probe v0.4.1 is released — adds an opt-in real-network integration test and a small FetcherAdapter to validate crawling behavior. Artifacts (sdist & wheel) are attached to the release: https://github.com/Nitin-2468-dev/Discovery/releases/tag/v0.4.1

Patch (2026-01-15): CI & docs maintenance — removed lingering `tmp_ci_check` gitlink that caused Actions post-checkout failures, made the Autofix workflow tolerant of push failures for forked PRs, and updated CHANGELOG/docs/constraints.log with the details. (See PR #36)


Tweet (short):

- Probe v0.4.1 is out! 🎉 Opt-in real-network integration tests + FetcherAdapter for easier validation. Check release notes & download: https://github.com/Nitin-2468-dev/Discovery/releases/tag/v0.4.1

Slack (long):

- Heads up — Probe v0.4.1 is released. Highlights:
  - Opt-in real-network integration workflow (`.github/workflows/research-integration.yml`) to safely validate end-to-end crawling (RUN_REAL_NET_TESTS=true to run).
  - `probe/crawl/fetcher_adapter.py` and `tests/test_crawler_integration.py` added for easier testing.

  Artifacts (sdist & wheel) are attached to the release: https://github.com/Nitin-2468-dev/Discovery/releases/tag/v0.4.1

Email (long):

- Subject: Probe v0.4.1 released — opt-in real-network tests & FetcherAdapter

  Body: Probe v0.4.1 is now available. This release adds an opt-in real-network integration workflow and a small `FetcherAdapter` to make real-network crawling tests easier to run during development. The release includes prebuilt sdist and wheel assets; see the release page for details and usage instructions.

---

If you want, I can post the Slack message to a specific channel and/or schedule the tweet. Tell me where to post or I can leave these drafts here for you to publish.
