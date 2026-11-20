#!/usr/bin/env python3
"""Build the scoped Milestone 3I text candidate without bulk early-game drafts."""
from __future__ import annotations

import hashlib
import json
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rebuilding.pilot import build_archive, effective_resource, parse_record_id
from src.translation.catalog import read_jsonl

GAMES = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCES = ("a/0/7/4", "a/0/8/2")
OUTPUT = ROOT / "build/milestone-3i/text-candidate"
SOURCE_FILES = (ROOT / "translations/milestone3g-battle.jsonl", ROOT / "translations/milestone3h-ui-battle.jsonl")
PC_MIRROR_IDS = {"gen6:a/0/8/2:0055/00:00001", "gen6:a/0/8/2:0055/00:00003"}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_text_candidate(output_root: Path = OUTPUT) -> dict[str, object]:
    rows = [row for path in SOURCE_FILES for row in read_jsonl(path)]
    early = [row for row in read_jsonl(ROOT / "translations/early-game.jsonl")
             if row["record_id"] in PC_MIRROR_IDS]
    if {row["record_id"] for row in early} != PC_MIRROR_IDS:
        raise ValueError("The two owner-runtime-confirmed PC/mirror rows are missing")
    rows.extend(early)
    ids = [row["record_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate message IDs in scoped Milestone 3I text candidate")
    if len(rows) != 90:
        raise ValueError(f"Expected 55 Milestone 3H + 33 Milestone 3G + 2 PC/mirror records, got {len(rows)}")

    report = {"milestone": "3I", "build_state": "unapproved_text_runtime_candidate",
              "runtime_tested": False, "installed": False, "original_assets_modified": False,
              "translation_records": len(rows), "included_sources": {
                  "milestone_3h_drafts": 55, "milestone_3g_battle_drafts": 33,
                  "owner_runtime_confirmed_pc_mirror_records": sorted(PC_MIRROR_IDS)},
              "excluded": ["other early-game draft records", "keyboard/input changes"], "games": {}}
    for game, title_id in GAMES.items():
        game_root = ROOT / "workspace" / game
        output_records = []
        for resource in RESOURCES:
            relative = Path(*resource.split("/"))
            selected, version = effective_resource(game_root / "base" / relative,
                                                   game_root / "update-1.5" / relative)
            source = selected.read_bytes()
            before = sha256(source)
            built, proof = build_archive(source, resource, game, version, rows, include_machine_drafts=True)
            if sha256(selected.read_bytes()) != before:
                raise RuntimeError(f"Source changed while building: {selected}")
            destination = output_root / game / "romfs" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(built)
            proof.update({"resource": resource, "source_version": version,
                          "source_path": selected.relative_to(ROOT).as_posix(),
                          "output_path": destination.relative_to(output_root).as_posix(),
                          "layeredfs_title_id": title_id, "translations_applied": proof.pop("message_ids")})
            output_records.append(proof)
        game_count = sum(record["messages_applied"] for record in output_records)
        expected = sum(1 for row in rows if row["scope"] in {"shared", "x" if game == "pokemon-x" else "y"}
                       and parse_record_id(row["record_id"])[0] in RESOURCES)
        if game_count != expected:
            raise ValueError(f"Wrong scoped message count for {game}: {game_count} != {expected}")
        report["games"][game] = {"title_id": title_id, "resources": output_records}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                            encoding="utf-8", newline="\n")
    return report


def rollback_text_candidate(output_root: Path = OUTPUT) -> list[str]:
    manifest_path = output_root / "manifest.json"
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("milestone") != "3I" or manifest.get("build_state") != "unapproved_text_runtime_candidate":
        raise ValueError("Refusing to remove an output without a Milestone 3I candidate manifest")
    removed = []
    for game in GAMES:
        for resource in RESOURCES:
            target = output_root / game / "romfs" / Path(*resource.split("/"))
            if target.is_file():
                target.unlink()
                removed.append(target.relative_to(output_root).as_posix())
    manifest_path.unlink()
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true", help="remove only the four archives in a Milestone 3I text-candidate build")
    args = parser.parse_args()
    if args.rollback:
        print(json.dumps({"rolled_back": rollback_text_candidate()}, sort_keys=True, indent=2))
        return 0
    report = build_text_candidate()
    print(json.dumps({"output": OUTPUT.relative_to(ROOT).as_posix(), "records": report["translation_records"],
                      "runtime_tested": False, "installed": False,
                      "archive_hashes": {game: {item["resource"]: item["output_sha256"]
                                               for item in data["resources"]}
                                         for game, data in report["games"].items()}}, ensure_ascii=False,
                     sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
