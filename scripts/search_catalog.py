#!/usr/bin/env python3
"""Search source-catalog English strings without copying source assets."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pattern", help="regular expression matched against decoded source text")
    parser.add_argument("--resource", action="append", help="resource path filter, such as a/0/8/2")
    parser.add_argument("--archive-member", action="append", help="GARC member index, such as 0055/00")
    parser.add_argument("--record-id", action="append", help="exact stable record ID")
    parser.add_argument("--catalog", type=Path, default=ROOT / "build/milestone-3b/source-catalog.jsonl")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--segments", action="store_true", help="include decoded TextFile segments")
    args = parser.parse_args()
    expression = re.compile(args.pattern, re.IGNORECASE)
    found = 0
    with args.catalog.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("source_language") != "en":
                continue
            if args.resource and row.get("resource") not in args.resource:
                continue
            if args.record_id and row.get("record_id") not in args.record_id:
                continue
            parts = row.get("record_id", "").split(":")
            member_id = parts[2] if len(parts) == 4 else ""
            if args.archive_member and member_id not in args.archive_member:
                continue
            source_text = str(row.get("source_text", ""))
            if expression.search(source_text):
                result = {"record_id": row["record_id"], "source_variant_sha256": row["source_variant_sha256"],
                          "source_text": source_text}
                if args.segments:
                    result["source_segments"] = row.get("source_segments", [])
                print(json.dumps(result, ensure_ascii=False))
                found += 1
                if found >= args.limit:
                    break
    print(json.dumps({"matches_printed": found, "catalog": args.catalog.as_posix()}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
