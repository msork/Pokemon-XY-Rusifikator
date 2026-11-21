#!/usr/bin/env python3
"""Install or roll back only the manually edited Milestone 3L battle image archive."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.extraction.garc import GARC
from src.rebuilding.installation import backup_targets, rollback_targets

IMAGE_MANIFEST = ROOT / "build/milestone-3i/image-candidate/manifest.json"
TEXT_RECORD = ROOT / "build/milestone-3k/installation-record.json"
RECORD_ROOT = ROOT / "build/milestone-3l/image-install"
EXPECTED_HASH = "1becfbb516f81ce2f885490b9dfba6b2404524b7b1cf87e0669cdba56f58fc0e"
RESOURCE = "a/2/4/0"
GAMES = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
TEXT_RESOURCES = {"a/0/7/4", "a/0/8/2"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_text_install(mod_root: Path, text_record_path: Path = TEXT_RECORD) -> list[dict]:
    record = json.loads(text_record_path.resolve(strict=True).read_text(encoding="utf-8"))
    if record.get("milestone") != "3K" or record.get("build_milestone") != "3J":
        raise ValueError("Expected the installed Milestone 3K text record")
    files = record.get("installed_files", [])
    expected_paths = {f"{title_id}/romfs/{resource}" for title_id in GAMES.values()
                      for resource in TEXT_RESOURCES}
    indexed = {row.get("relative_path"): row for row in files}
    if set(indexed) != expected_paths or len(files) != 4:
        raise ValueError("Milestone 3K record does not cover exactly the four text archives")
    for relative, row in indexed.items():
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or file_hash(target) != row.get("sha256"):
            raise ValueError(f"Installed text archive changed; refusing image operation: {relative}")
    return files


def candidate_targets(manifest_path: Path = IMAGE_MANIFEST) -> list[tuple[str, dict, Path]]:
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("milestone") != "3I" or manifest.get("build_state") != "uninstalled_image_candidate"
            or manifest.get("installed") is not False or manifest.get("runtime_tested") is not False
            or manifest.get("original_assets_modified") is not False):
        raise ValueError("Manifest is not an uninstalled, untested Milestone 3I image candidate")
    candidate_root = manifest_path.parent.resolve()
    games = manifest.get("games", {})
    if set(games) != set(GAMES):
        raise ValueError("Image manifest must contain exactly Pokémon X and Pokémon Y")
    targets = []
    for game, title_id in GAMES.items():
        game_info = games[game]
        if game_info.get("title_id") != title_id:
            raise ValueError(f"Unexpected base Title ID for {game}")
        resource_rows = game_info.get("resources", [])
        selected = [row for row in resource_rows if row.get("resource") == RESOURCE]
        if len(selected) != 1:
            raise ValueError(f"Expected exactly one {RESOURCE} candidate for {game}")
        row = selected[0]
        if row.get("source_version") != "base":
            raise ValueError(f"Unexpected effective source for {game}/{RESOURCE}")
        if row.get("output_sha256") != EXPECTED_HASH:
            raise ValueError(f"Unexpected candidate hash for {game}/{RESOURCE}")
        relative = PurePosixPath(row.get("output_path", ""))
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            raise ValueError(f"Unsafe candidate path: {relative}")
        candidate = (candidate_root / Path(*relative.parts)).resolve(strict=True)
        if candidate_root not in candidate.parents or not candidate.is_file():
            raise ValueError(f"Candidate escapes image build root: {candidate}")
        if candidate.stat().st_size != int(row["output_size"]) or file_hash(candidate) != EXPECTED_HASH:
            raise ValueError(f"Candidate size/hash mismatch: {candidate}")
        raw = candidate.read_bytes()
        archive = GARC.parse(raw)
        if archive.rebuild() != raw:
            raise ValueError(f"Candidate GARC identity verification failed: {candidate}")
        targets.append((f"{title_id}/romfs/{RESOURCE}", row, candidate))
    if len(targets) != 2 or len({row[0] for row in targets}) != 2:
        raise ValueError("Expected exactly two X/Y image targets")
    return targets


def install(manifest_path: Path = IMAGE_MANIFEST, *, appdata: Path | None = None,
            record_root: Path = RECORD_ROOT, text_record_path: Path = TEXT_RECORD) -> dict:
    targets = candidate_targets(manifest_path)
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = (profile / "AzaharPlus/load/mods").resolve(strict=True)
    if profile not in mod_root.parents or not mod_root.is_dir():
        raise ValueError(f"AzaharPlus mod root is outside the current profile or missing: {mod_root}")
    text_before = _verify_text_install(mod_root, text_record_path)
    record_root = record_root.resolve()
    if (record_root / "installation-record.json").exists() or (record_root / "rollback-record.json").exists():
        raise FileExistsError(f"Milestone 3L image records already exist: {record_root}")
    relative_paths = [relative for relative, _, _ in targets]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = record_root / "installation-backups" / stamp
    if backup_root.exists():
        raise FileExistsError(f"Milestone 3L backup directory already exists: {backup_root}")
    backup_manifest = backup_targets(mod_root, backup_root, relative_paths)
    saved = {row["relative_path"]: row for row in backup_manifest["files"]}
    try:
        installed = []
        for relative, proof, candidate in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            prior = saved[relative]
            if prior["existed"] != destination.is_file():
                raise RuntimeError(f"Image target changed during backup: {relative}")
            if prior["existed"] and file_hash(destination) != prior["sha256"]:
                raise RuntimeError(f"Image target hash changed during backup: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".milestone-3l-image-tmp")
            if temporary.exists():
                raise FileExistsError(f"Temporary image target exists: {temporary}")
            shutil.copyfile(candidate, temporary)
            if file_hash(temporary) != EXPECTED_HASH:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Staged image hash mismatch: {relative}")
            temporary.replace(destination)
            if file_hash(destination) != EXPECTED_HASH:
                raise OSError(f"Installed image read-back mismatch: {relative}")
            installed.append({"relative_path": relative, "resource": RESOURCE,
                              "sha256": EXPECTED_HASH, "size": destination.stat().st_size})
        text_after = _verify_text_install(mod_root, text_record_path)
        if [(row["relative_path"], row["sha256"]) for row in text_before] != [
                (row["relative_path"], row["sha256"]) for row in text_after]:
            raise OSError("Text install record changed during image installation")
        record_root.mkdir(parents=True, exist_ok=True)
        result = {"milestone": "3L-image", "build_milestone": "3I", "mod_root": str(mod_root),
                  "appdata_root": str(profile), "build_manifest": str(Path(manifest_path).resolve()),
                  "text_install_record": str(Path(text_record_path).resolve()),
                  "backup_manifest": str((backup_root / "manifest.json").resolve()),
                  "backup_files": backup_manifest["files"], "installed_files": installed,
                  "text_files_verified_unchanged": [
                      {"relative_path": row["relative_path"], "sha256": row["sha256"]}
                      for row in text_after],
                  "unrelated_mods_modified": False, "saves_modified": False,
                  "original_assets_modified": False, "updates_modified": False,
                  "runtime_tested": False, "emulator_launched": False}
        (record_root / "installation-record.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                                              encoding="utf-8", newline="\n")
        return result
    except Exception:
        rollback_targets(mod_root, backup_root, backup_manifest)
        raise


def rollback(*, record_root: Path = RECORD_ROOT, appdata: Path | None = None,
             text_record_path: Path = TEXT_RECORD) -> dict:
    record_root = record_root.resolve(strict=True)
    record = json.loads((record_root / "installation-record.json").read_text(encoding="utf-8"))
    if record.get("milestone") != "3L-image":
        raise ValueError("Refusing rollback from a different installation record")
    backup_manifest_path = Path(record["backup_manifest"]).resolve(strict=True)
    backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8"))
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if Path(record["appdata_root"]).resolve() != profile or profile not in mod_root.parents:
        raise ValueError("Recorded mod root is outside the current AzaharPlus profile")
    _verify_text_install(mod_root, text_record_path)
    originals = {row["relative_path"]: row for row in backup_manifest["files"]}
    for row in record["installed_files"]:
        relative = row["relative_path"]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        original = originals[relative]
        if not target.is_file() or file_hash(target) != row["sha256"]:
            raise ValueError(f"Installed image target changed; refusing rollback: {relative}")
        saved = backup_manifest_path.parent.joinpath(*PurePosixPath(relative).parts)
        if original["existed"] and (not saved.is_file() or saved.stat().st_size != original["size"]
                                     or file_hash(saved) != original["sha256"]):
            raise ValueError(f"Image backup missing or invalid; refusing rollback: {relative}")
    restored = rollback_targets(mod_root, backup_manifest_path.parent, backup_manifest)
    for relative in restored:
        original = originals[relative]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if original["existed"]:
            if not target.is_file() or file_hash(target) != original["sha256"]:
                raise OSError(f"Restored image target verification failed: {relative}")
        elif target.exists():
            raise OSError(f"Originally absent image target still exists: {relative}")
    text_after = _verify_text_install(mod_root, text_record_path)
    expected_text = record.get("text_files_verified_unchanged", [])
    if [(row["relative_path"], row["sha256"]) for row in text_after] != [
            (row["relative_path"], row["sha256"]) for row in expected_text]:
        raise ValueError("Text archives changed; image rollback record will not be written")
    result = {"milestone": "3L-image", "rollback_verified": True, "restored_paths": restored,
              "text_files_unchanged": True, "unrelated_mods_modified": False, "saves_modified": False}
    rollback_record = record_root / "rollback-record.json"
    if rollback_record.exists():
        raise FileExistsError(f"Rollback record already exists: {rollback_record}")
    rollback_record.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                               encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    parser.add_argument("--manifest", type=Path, default=IMAGE_MANIFEST)
    args = parser.parse_args()
    result = rollback() if args.rollback else install(args.manifest)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
