#!/usr/bin/env python3
"""Validate and merge a local editable translation batch without source assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.translation.catalog import read_jsonl, write_jsonl
from src.translation.workflow import import_batch


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--batch", type=Path, required=True, help="edited JSONL exported by export_translation_batch.py")
    parser.add_argument("--translations", type=Path, default=ROOT / "translations/early-game.jsonl")
    args = parser.parse_args()
    batch = read_jsonl(args.batch)
    ids = {row.get("record_id") for row in batch}
    source = []
    with args.catalog.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("record_id") in ids:
                source.append(row)
    existing = read_jsonl(args.translations) if args.translations.exists() else []
    merged = import_batch(source, batch, existing)
    write_jsonl(args.translations.resolve(), merged)
    print(json.dumps({"imported": len(batch), "translation_records": len(merged),
                      "output": args.translations.resolve().as_posix()}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
