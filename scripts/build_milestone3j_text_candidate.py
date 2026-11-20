#!/usr/bin/env python3
"""Build the complete non-conflicting translation candidate for Milestone 3J."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rebuilding.pilot import build_archive, effective_resource, parse_record_id
from src.translation.catalog import read_jsonl

GAMES = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCES = ("a/0/7/4", "a/0/8/2")
OUTPUT = ROOT / "build/milestone-3j/text-candidate"
SOURCE_FILES = (ROOT / "translations/pilot.jsonl", ROOT / "translations/early-game.jsonl",
                ROOT / "translations/milestone3g-battle.jsonl", ROOT / "translations/milestone3h-ui-battle.jsonl")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_translations(source_files: tuple[Path, ...] = SOURCE_FILES) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows: list[dict[str, object]] = []
    first_by_id: dict[str, tuple[dict[str, object], Path]] = {}
    source_summaries = []
    conflicts = []
    for path in source_files:
        file_rows = read_jsonl(path)
        status_counts = Counter(str(row.get("status")) for row in file_rows)
        source_summaries.append({"path": path.relative_to(ROOT).as_posix() if ROOT in path.resolve().parents else path.name,
                                 "sha256": sha256(path.read_bytes()), "record_count": len(file_rows),
                                 "status_counts": dict(sorted(status_counts.items()))})
        for row in file_rows:
            record_id = str(row.get("record_id", ""))
            previous = first_by_id.get(record_id)
            if previous:
                old, old_path = previous
                old_hash = old.get("source_variant_sha256")
                new_hash = row.get("source_variant_sha256")
                category = "source-hash conflict" if old_hash != new_hash else "duplicate record ID"
                conflicts.append(f"{category}: {record_id} in {old_path.name} and {path.name}")
                continue
            first_by_id[record_id] = (row, path)
            rows.append(row)
    if conflicts:
        raise ValueError("Translation input conflicts; no row was selected:\n" + "\n".join(conflicts))
    ids = [str(row["record_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise AssertionError("Internal duplicate-ID check failed")
    for row in rows:
        if len(str(row.get("source_variant_sha256", ""))) != 64:
            raise ValueError(f"Invalid source hash: {row.get('record_id')}")
        if row.get("scope") not in {"shared", "x", "y"}:
            raise ValueError(f"Invalid game scope: {row.get('record_id')}")
        if not row.get("version_scope"):
            raise ValueError(f"Missing source version scope: {row.get('record_id')}")
    summary = {"input_files": source_summaries, "record_count": len(rows),
               "unique_id_count": len(ids), "duplicate_ids": 0, "source_hash_conflicts": 0,
               "status_counts": dict(sorted(Counter(str(row.get("status")) for row in rows).items()))}
    return rows, summary


def build_text_candidate(output_root: Path = OUTPUT) -> dict[str, object]:
    rows, input_summary = collect_translations()
    report: dict[str, object] = {
        "milestone": "3J", "build_state": "unapproved_integrated_runtime_candidate",
        "runtime_tested": False, "installed": False, "original_assets_modified": False,
        "translation_records": len(rows), "translation_inputs": input_summary,
        "source_version_policy": "update-1.5 overrides base when the resource exists; otherwise use base",
        "effective_resources": {}, "games": {},
    }
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
            if destination.exists():
                backup = destination.with_suffix(destination.suffix + ".bak")
                backup_manifest_path = output_root / "candidate-backup-manifest.json"
                backups = json.loads(backup_manifest_path.read_text(encoding="utf-8")) if backup_manifest_path.exists() else {"backups": {}}
                key = destination.relative_to(output_root).as_posix()
                if not backup.exists():
                    shutil.copyfile(destination, backup)
                    backups["backups"][key] = sha256(backup.read_bytes())
                elif key not in backups["backups"] or sha256(backup.read_bytes()) != backups["backups"][key]:
                    raise ValueError(f"Candidate backup hash missing or invalid: {backup}")
                backup_manifest_path.write_text(json.dumps(backups, sort_keys=True, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
            destination.write_bytes(built)
            proof.update({"resource": resource, "source_version": version,
                          "source_path": selected.relative_to(ROOT).as_posix(),
                          "output_path": destination.relative_to(output_root).as_posix(),
                          "layeredfs_title_id": title_id, "translations_applied": proof.pop("message_ids")})
            output_records.append(proof)
            report["effective_resources"][f"{game}:{resource}"] = {
                "version": version, "source_sha256": before, "source_path": selected.relative_to(ROOT).as_posix()}
        expected = sum(1 for row in rows
                       if row["scope"] in {"shared", "x" if game == "pokemon-x" else "y"}
                       and parse_record_id(str(row["record_id"]))[0] in RESOURCES)
        applied = sum(int(record["messages_applied"]) for record in output_records)
        if applied != expected:
            raise ValueError(f"Incomplete translation application for {game}: {applied} != {expected}")
        report["games"][game] = {"title_id": title_id, "resources": output_records,
                                 "translations_applied": applied}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                                encoding="utf-8", newline="\n")
    return report


def rollback_text_candidate(output_root: Path = OUTPUT) -> list[str]:
    manifest_path = output_root / "manifest.json"
    if not manifest_path.is_file():
        return []
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("milestone") != "3J" or manifest.get("build_state") != "unapproved_integrated_runtime_candidate":
        raise ValueError("Refusing to remove output without a Milestone 3J integrated candidate manifest")
    backup_manifest_path = output_root / "candidate-backup-manifest.json"
    backups = json.loads(backup_manifest_path.read_text(encoding="utf-8")) if backup_manifest_path.exists() else {"backups": {}}
    removed = []
    for game in GAMES:
        for resource in RESOURCES:
            target = output_root / game / "romfs" / Path(*resource.split("/"))
            if not target.exists():
                continue
            backup = target.with_suffix(target.suffix + ".bak")
            key = target.relative_to(output_root).as_posix()
            if backup.exists():
                expected_hash = backups.get("backups", {}).get(key)
                if not expected_hash or sha256(backup.read_bytes()) != expected_hash:
                    raise ValueError(f"Candidate backup hash mismatch; refusing rollback: {backup}")
                target.unlink()
                backup.replace(target)
                removed.append(key + " (previous candidate restored)")
            else:
                target.unlink()
                removed.append(key + " (generated candidate removed)")
    manifest_path.unlink()
    if backup_manifest_path.exists():
        backup_manifest_path.unlink()
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true", help="restore prior generated candidates or remove this build")
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
