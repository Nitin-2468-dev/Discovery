# Seeds & Seed Runner

This page documents how to run seed lists for v0.2 testing and ad-hoc investigations.

Files
-----
Place seed lists in `seeds/` or use ad-hoc files. Each file is newline-separated, comments (lines starting with `#`) are ignored.

Example seed file (test_simple.txt):
```
# small test set
https://example.com/
https://example.org/
```

CLI
---
- `python cli.py seeds run <file>`: run seeds with safe defaults
  - `--limit`: limit number of seeds to run (default 10)
  - `--ingest`: persist results into DB
  - `--db`: database path

- `python cli.py health-check <url>`: lightweight check to verify fetch + extraction

Phases (recommended)
--------------------
1. Basic Fetching: use `test_simple.txt` (first 5 URLs)
2. PDF Extraction: use `pdf_focused.txt` (3-5 PDF URLs)
3. Link Following: use `aviation_engines.txt`
4. Edge Cases: `test_challenging.txt` run one at a time
5. Real Investigation: `example_queries.txt`

Safety & Tips
-------------
- Start small (3-5 seeds) and check logs.
- Respect site robots and terms; add politeness later.
- Use conservative timeouts and backoff settings.

Example
-------
```
python cli.py seeds run seeds/test_simple.txt --limit 5 --ingest --db myprobe.db
```

You can also use the convenience PowerShell wrapper `run_seeds.ps1` (Windows):

```powershell
# Run 5 seeds and ingest results
.\run_seeds.ps1 -File seeds/test_simple.txt -Limit 5 -Ingest -Db myprobe.db

# Dry-run (shows the command that would run)
.\run_seeds.ps1 -File seeds/test_simple.txt -Limit 5 -DryRun
```

This will load the seeds, print a domain summary, fetch each URL, optionally ingest successful results, and print a final summary.
