#!/usr/bin/env python3
"""Read-only inventory and byte-level comparison for extracted RomFS trees."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def inventory(root: Path) -> list[dict[str, object]]:
    """Return deterministic per-file path, size, and SHA-256 records."""
    root = root.resolve(strict=True)
    records = []
    for path in sorted((p for p in root.rglob("*") if p.is_file()), key=lambda p: p.relative_to(root).as_posix()):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        records.append({"path": path.relative_to(root).as_posix(), "size": path.stat().st_size, "sha256": digest.hexdigest()})
    return records


def compare(left: list[dict[str, object]], right: list[dict[str, object]]) -> dict[str, list[str]]:
    """Classify paths as identical, differing, left-only, or right-only."""
    a = {str(row["path"]): row for row in left}
    b = {str(row["path"]): row for row in right}
    common = a.keys() & b.keys()
    return {
        "identical": sorted(p for p in common if a[p]["sha256"] == b[p]["sha256"]),
        "different": sorted(p for p in common if a[p]["sha256"] != b[p]["sha256"]),
        "left_only": sorted(a.keys() - b.keys()),
        "right_only": sorted(b.keys() - a.keys()),
    }


def write_manifest(root: Path, output: Path) -> list[dict[str, object]]:
    rows = inventory(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inv = sub.add_parser("inventory", help="write a SHA-256 JSONL manifest")
    inv.add_argument("root", type=Path)
    inv.add_argument("output", type=Path)
    cmp = sub.add_parser("compare", help="compare two RomFS trees by relative path and hash")
    cmp.add_argument("left", type=Path)
    cmp.add_argument("right", type=Path)
    args = parser.parse_args()
    if args.command == "inventory":
        rows = write_manifest(args.root, args.output)
        print(json.dumps({"root": str(args.root.resolve()), "files": len(rows), "bytes": sum(int(r["size"]) for r in rows), "manifest": str(args.output)}, indent=2))
    else:
        result = compare(inventory(args.left), inventory(args.right))
        print(json.dumps({k: len(v) for k, v in result.items()}, indent=2))
        for category, paths in result.items():
            if paths:
                print(f"\n[{category}]\n" + "\n".join(paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
