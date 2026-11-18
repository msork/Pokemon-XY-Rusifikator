#!/usr/bin/env python3
"""Verify byte-exact no-change serialization for every supported source TextFile."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.garc import GARC  # noqa: E402
from src.extraction.messages import TextFile, rebuild_identity  # noqa: E402

RESOURCES = ("a/0/7/4", "a/0/8/2")
DATASETS = {
    "pokemon-x": ("base", "update-1.5"),
    "pokemon-y": ("base", "update-1.5"),
}


def main() -> int:
    results = []
    for game, versions in DATASETS.items():
        for version in versions:
            message_count = member_count = 0
            for resource in RESOURCES:
                source = ROOT / "workspace" / game / version / Path(*resource.split("/"))
                if not source.is_file():
                    continue
                archive = GARC.parse(source.read_bytes())
                for member in archive.members:
                    text_file = TextFile.parse(member.data)
                    if rebuild_identity(text_file) != member.data:
                        raise RuntimeError(f"TextFile round-trip mismatch: {game}/{version}/{resource}/{member.entry_id}/{member.subfile_id}")
                    member_count += 1
                    message_count += len(text_file.lines)
            results.append({"game": game, "version": version, "text_members": member_count, "messages": message_count})
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
