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


def write_csv_report(
    seed_name: str,
    rows: list,
    dir_path: Path = RUN_REPORTS_DIR,
    file_path: Path | None = None,
) -> Path:
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


def write_scoring_export(
    reports: list,
    dir_path: Path = RUN_REPORTS_DIR,
    file_path: Path | None = None,
    fmt: str = "csv",
) -> Path:
    """Write scoring reports to CSV or Markdown.

    Reports should be a list of dict-like rows with keys:
    - id, page_id, url, score, components, metadata, created_at
    """
    ensure_dir(dir_path)
    if file_path:
        out = file_path
        ensure_dir(out.parent)
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out = dir_path / f"scoring_{ts}.{fmt}"

    if fmt == "csv":
        fields = [
            "created_at",
            "url",
            "page_id",
            "score",
            "top_component",
            "component_scores",
            "metadata",
        ]
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in reports:
                # components is expected to be JSON string or dict
                comps = r.get("components")
                if not isinstance(comps, str):
                    import json

                    comps = json.dumps(comps) if comps is not None else ""
                writer.writerow(
                    {
                        "created_at": r.get("created_at"),
                        "url": r.get("url"),
                        "page_id": r.get("page_id"),
                        "score": r.get("score"),
                        "top_component": r.get("top_component", ""),
                        "component_scores": comps,
                        "metadata": r.get("metadata", ""),
                    }
                )
    else:
        # Markdown output
        lines = [
            "# Scoring Report",
            "",
            "| created_at | url | page_id | score | top_component | components |",
            "|---|---|---:|---:|---|---|",
        ]
        import json

        total = 0.0
        count = 0
        for r in reports:
            comps = r.get("components")
            if not isinstance(comps, str):
                comps_s = json.dumps(comps)
            else:
                comps_s = comps
            lines.append(
                f"| {r.get('created_at')} | {r.get('url')} | {r.get('page_id') or ''} | {r.get('score') or ''} | {r.get('top_component','')} | `{comps_s}` |"
            )
            try:
                total += float(r.get("score") or 0.0)
                count += 1
            except Exception:
                pass
        avg = (total / count) if count else 0.0
        lines.append("")
        lines.append(f"**Average score:** {avg:.3f} ({count} records)")
        out.write_text("\n".join(lines), encoding="utf-8")

    return out
