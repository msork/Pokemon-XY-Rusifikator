#!/usr/bin/env python3
"""Export selected stable message IDs to a local, editable draft batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import write_jsonl
from src.translation.workflow import export_batch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--ids", type=Path, required=True, help="UTF-8 text file with one stable record_id per line")
    parser.add_argument("--output", type=Path, default=ROOT / "build/translation-batch.jsonl")
    args = parser.parse_args()
    ids = {line.strip() for line in args.ids.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")}
    selected = []
    with args.catalog.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("record_id") in ids:
                selected.append(row)
    rows = export_batch(selected, ids)
    write_jsonl(args.output.resolve(), rows)
    print(json.dumps({"records": len(rows), "output": args.output.resolve().as_posix()}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
