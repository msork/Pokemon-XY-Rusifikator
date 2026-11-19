#!/usr/bin/env python3
"""Scan the four extracted RomFS trees read-only and export a local TextFile catalog."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import ROMFS_ROOT, catalog_roots, write_jsonl


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=ROMFS_ROOT)
    parser.add_argument("--output", type=Path, default=Path("build/milestone-3b/source-catalog.jsonl"))
    parser.add_argument("--report", type=Path, default=Path("reports/milestone-3b/asset-catalog.json"))
    args = parser.parse_args()
    workspace = args.workspace.resolve(strict=True)
    roots = [workspace / game / version for game in ("pokemon-x", "pokemon-y") for version in ("base", "update-1.5")]
    records, report = catalog_roots(roots)
    output_path = args.output.resolve()
    report_path = args.report.resolve()
    write_jsonl(output_path, records)
    report["catalog_path"] = output_path.as_posix()
    report["catalog_record_count"] = len(records)
    report["report_path"] = report_path.as_posix()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in (
        "files_scanned", "garc_candidates", "garc_parsed", "textfile_members", "messages",
        "unique_coordinate_variants", "non_text_members", "catalog_record_count", "catalog_path", "report_path"
    )}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
