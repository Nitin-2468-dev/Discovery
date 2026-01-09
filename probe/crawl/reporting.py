"""Reporting helpers: CSV reports and failure log entries."""
from pathlib import Path
from datetime import datetime
import csv

CONSTRAINTS_LOG = Path("constraints.log")
RUN_REPORTS_DIR = Path("run_reports")

CSV_FIELDS = [
    "timestamp",
    "url",
    "domain",
    "status_code",
    "success",
    "error_message",
    "content_type",
    "content_length",
    "fetch_duration_ms",
    "redirect_count",
    "final_url",
    "link_count",
    "has_pdf_links",
    "retry_count",
    "user_agent",
    # scoring fields
    "score",
    "top_component",
    "component_scores",
]


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_csv_report(seed_name: str, rows: list, dir_path: Path = RUN_REPORTS_DIR, file_path: Path | None = None) -> Path:
    # If an explicit file_path is provided, write there; otherwise create a timestamped file in dir_path
    if file_path:
        ensure_dir(file_path.parent)
        out = file_path
    else:
        ensure_dir(dir_path)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        fname = f"{ts}_{Path(seed_name).stem}.csv"
        out = dir_path / fname

    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in CSV_FIELDS})

    return out


def append_failure_log(url: str, error: str, seed_name: str, cmd: str):
    ensure_dir(CONSTRAINTS_LOG.parent)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = (
        f"[{ts}] FETCHER_FAILURE\n"
        f"Phase: v0.2\n"
        f"URL: {url}\n"
        f"Error: {error}\n"
        f"Command: {cmd}\n"
        f"Outcome: logged by seed-runner\n"
        "---\n"
    )
    with open(CONSTRAINTS_LOG, "a", encoding="utf-8") as f:
        f.write(entry)
    return CONSTRAINTS_LOG
