#!/usr/bin/env python3
"""Build isolated Pokémon X/Y LayeredFS pilot archives; never edits source RomFS."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rebuilding.pilot import build_archive, effective_resource
from src.translation.catalog import read_jsonl


GAMES = {
    "pokemon-x": "0004000000055D00",
    "pokemon-y": "0004000000055E00",
}
RESOURCES = ("a/0/7/4", "a/0/8/2")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--include-machine-drafts", action="store_true",
                        help="required acknowledgment that the generated pilot is not human-approved")
    parser.add_argument("--translations", type=Path, default=ROOT / "translations/pilot.jsonl")
    parser.add_argument("--workspace", type=Path, default=ROOT / "workspace")
    parser.add_argument("--output", type=Path, default=ROOT / "build/milestone-3c")
    args = parser.parse_args()
    if not args.include_machine_drafts:
        parser.error("pilot rows remain unapproved machine drafts; pass --include-machine-drafts to create local test candidates")
    translations = read_jsonl(args.translations)
    output_root = args.output.resolve()
    if ROOT.resolve() not in output_root.parents:
        parser.error("output directory must remain inside the project root")
    report = {
        "milestone": "3C",
        "build_state": "unapproved_runtime_test_candidate",
        "runtime_tested": False,
        "installed": False,
        "original_assets_modified": False,
        "translation_statuses": sorted({str(row["status"]) for row in translations}),
        "games": {},
    }
    for game, title_id in GAMES.items():
        game_root = args.workspace.resolve(strict=True) / game
        output_records = []
        effective_versions = {}
        for resource in RESOURCES:
            relative = Path(*resource.split("/"))
            selected, version = effective_resource(game_root / "base" / relative,
                                                   game_root / "update-1.5" / relative)
            effective_versions[resource] = version
            source_bytes = selected.read_bytes()
            source_hash_before = hashlib.sha256(source_bytes).hexdigest()
            output_bytes, proof = build_archive(source_bytes, resource, game, version, translations,
                                                include_machine_drafts=True)
            destination = output_root / game / "romfs" / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(output_bytes)
            source_hash_after = hashlib.sha256(selected.read_bytes()).hexdigest()
            if source_hash_after != source_hash_before:
                raise RuntimeError(f"Source resource changed during build: {selected}")
            proof.update({
                "resource": resource,
                "source_version": version,
                "source_path": selected.relative_to(args.workspace.resolve()).as_posix(),
                "output_path": destination.relative_to(output_root).as_posix(),
                "layeredfs_title_id": title_id,
                "translations_applied": proof.pop("message_ids"),
            })
            output_records.append(proof)
        expected = 0
        for row in translations:
            parts = str(row["record_id"]).split(":")
            resource = parts[1] if len(parts) == 4 else ""
            applicable_game = row.get("scope") == "shared" or row.get("scope") == ("x" if game == "pokemon-x" else "y")
            if applicable_game and resource in effective_versions and effective_versions[resource] in row.get("version_scope", []):
                expected += 1
        applied = sum(int(item["messages_applied"]) for item in output_records)
        if applied != expected:
            raise RuntimeError(f"Incomplete translation application for {game}: applied={applied}, expected={expected}")
        report["games"][game] = {"title_id": title_id, "resources": output_records}
    manifest = output_root / "manifest.json"
    manifest.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8", newline="\n")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
