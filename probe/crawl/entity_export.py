from pathlib import Path
from datetime import datetime
import csv
import json


def write_entity_export(
    entity_name: str,
    docs: list,
    dir_path: Path = Path("run_reports"),
    file_path: Path | None = None,
    fmt: str = "md",
) -> Path:
    """Export entity documents to CSV or Markdown.

    docs: list of dicts with keys: title, url, doc_type, hash, score, metadata
    """
    if file_path:
        out = file_path
        out.parent.mkdir(parents=True, exist_ok=True)
    else:
        dir_path.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out = dir_path / f"{entity_name.replace(' ', '_')}_export_{ts}.{fmt}"

    if fmt == "csv":
        fields = ["title", "url", "doc_type", "hash", "score", "metadata"]
        with open(out, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for d in docs:
                md = d.get("metadata")
                md_s = json.dumps(md) if md is not None else ""
                writer.writerow(
                    {
                        "title": d.get("title"),
                        "url": d.get("url"),
                        "doc_type": d.get("doc_type"),
                        "hash": d.get("hash"),
                        "score": d.get("score"),
                        "metadata": md_s,
                    }
                )
    else:
        lines = [
            f"# Export for entity: {entity_name}",
            "",
            "| Title | URL | Type | Hash | Score | Metadata |",
            "|---|---|---|---|---:|---|",
        ]
        for d in docs:
            md = d.get("metadata")
            md_s = json.dumps(md) if md is not None else ""
            lines.append(
                f"| {d.get('title') or ''} | {d.get('url') or ''} | {d.get('doc_type') or ''} | {d.get('hash') or ''} | {d.get('score') or ''} | `{md_s}` |"
            )
        out.write_text("\n".join(lines), encoding="utf-8")

    return out
