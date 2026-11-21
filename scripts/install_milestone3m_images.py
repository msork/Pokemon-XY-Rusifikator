#!/usr/bin/env python3
"""Install or roll back exactly the four Milestone 3M battle-image GARCs."""
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

BUILD_ROOT = ROOT / "build/milestone-3m/candidate"
MANIFEST = BUILD_ROOT / "milestone-3m-manifest.json"
TEXT_RECORD = ROOT / "build/milestone-3k/installation-record.json"
RECORD_ROOT = ROOT / "build/milestone-3m/installation"
GAMES = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCES = {"a/2/4/0", "a/2/3/9"}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _verify_text(mod_root: Path, text_record_path: Path = TEXT_RECORD) -> list[dict]:
    record = json.loads(text_record_path.resolve(strict=True).read_text(encoding="utf-8"))
    if record.get("milestone") != "3K" or record.get("build_milestone") != "3J":
        raise ValueError("Expected the installed Milestone 3K text record")
    files = record.get("installed_files", [])
    expected = {f"{title_id}/romfs/{resource}" for title_id in GAMES.values()
                for resource in ("a/0/7/4", "a/0/8/2")}
    by_path = {row.get("relative_path"): row for row in files}
    if set(by_path) != expected or len(files) != 4:
        raise ValueError("Milestone 3K record does not cover exactly four text targets")
    for relative, row in by_path.items():
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or file_hash(target) != row.get("sha256"):
            raise ValueError(f"Text patch changed; refusing image operation: {relative}")
    return files


def candidate_targets(manifest_path: Path = MANIFEST) -> list[tuple[str, dict, Path]]:
    manifest_path = manifest_path.resolve(strict=True)
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (data.get("milestone") != "3M" or data.get("build_state") != "uninstalled_integrated_24_texture_candidate"
            or data.get("installed") is not False or data.get("runtime_tested") is not False
            or data.get("original_assets_modified") is not False or data.get("source_png_count") != 24
            or data.get("deterministic_hashes_match") is not True):
        raise ValueError("Not a verified uninstalled deterministic Milestone 3M candidate")
    root = manifest_path.parent.resolve()
    games = data.get("games", {})
    if set(games) != set(GAMES):
        raise ValueError("Candidate must contain exactly X and Y")
    targets = []
    for game, title_id in GAMES.items():
        game_data = games[game]
        if game_data.get("title_id") != title_id:
            raise ValueError(f"Unexpected Title ID for {game}")
        rows = game_data.get("resources", [])
        by_resource = {row.get("resource"): row for row in rows}
        if len(by_resource) != len(rows) or set(by_resource) != RESOURCES:
            raise ValueError(f"Unexpected resource list for {game}")
        for resource in sorted(RESOURCES):
            proof = by_resource[resource]
            relative = PurePosixPath(proof.get("output_path", ""))
            if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
                raise ValueError(f"Unsafe candidate path: {relative}")
            source = (root / Path(*relative.parts)).resolve(strict=True)
            if root not in source.parents or not source.is_file():
                raise ValueError(f"Candidate escapes build root: {source}")
            if source.stat().st_size != int(proof["output_size"]) or file_hash(source) != proof["output_sha256"]:
                raise ValueError(f"Candidate size/hash mismatch: {source}")
            raw = source.read_bytes()
            if GARC.parse(raw).rebuild() != raw:
                raise ValueError(f"Candidate GARC round trip failed: {source}")
            targets.append((f"{title_id}/romfs/{resource}", proof, source))
    if len(targets) != 4 or len({row[0] for row in targets}) != 4:
        raise ValueError("Expected exactly four unique image targets")
    return targets


def install(manifest_path: Path = MANIFEST, *, appdata: Path | None = None,
            record_root: Path = RECORD_ROOT, text_record_path: Path = TEXT_RECORD) -> dict:
    targets = candidate_targets(manifest_path)
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = (profile / "AzaharPlus/load/mods").resolve(strict=True)
    if profile not in mod_root.parents or not mod_root.is_dir():
        raise ValueError(f"AzaharPlus mod root is outside current profile or missing: {mod_root}")
    text_before = _verify_text(mod_root, text_record_path)
    record_root = record_root.resolve()
    install_path, rollback_path = record_root / "installation-record.json", record_root / "rollback-record.json"
    if install_path.exists() or rollback_path.exists():
        raise FileExistsError(f"Milestone 3M installation record already exists: {record_root}")
    relatives = [row[0] for row in targets]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = record_root / "installation-backups" / stamp
    if backup_root.exists():
        raise FileExistsError(f"Milestone 3M backup exists: {backup_root}")
    backup = backup_targets(mod_root, backup_root, relatives)
    before = {row["relative_path"]: row for row in backup["files"]}
    try:
        installed = []
        for relative, proof, candidate in targets:
            target = mod_root.joinpath(*PurePosixPath(relative).parts)
            old = before[relative]
            if old["existed"] != target.is_file():
                raise RuntimeError(f"Image target existence changed during backup: {relative}")
            if old["existed"] and file_hash(target) != old["sha256"]:
                raise RuntimeError(f"Image target changed during backup: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".milestone-3m-tmp")
            if temporary.exists():
                raise FileExistsError(f"Temporary install file exists: {temporary}")
            shutil.copyfile(candidate, temporary)
            if file_hash(temporary) != proof["output_sha256"]:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Staged file hash mismatch: {relative}")
            temporary.replace(target)
            if file_hash(target) != proof["output_sha256"]:
                raise OSError(f"Installed read-back mismatch: {relative}")
            installed.append({"relative_path": relative, "resource": proof["resource"],
                              "source_version": proof["source_version"], "sha256": proof["output_sha256"],
                              "size": proof["output_size"]})
        text_after = _verify_text(mod_root, text_record_path)
        text_hashes = [(row["relative_path"], row["sha256"]) for row in text_before]
        if [(row["relative_path"], row["sha256"]) for row in text_after] != text_hashes:
            raise OSError("Milestone 3K text installation changed during image install")
        record_root.mkdir(parents=True, exist_ok=True)
        record = {"milestone": "3M", "mod_root": str(mod_root), "appdata_root": str(profile),
                  "build_manifest": str(Path(manifest_path).resolve()), "text_install_record": str(Path(text_record_path).resolve()),
                  "backup_manifest": str((backup_root / "manifest.json").resolve()),
                  "backup_files": backup["files"], "installed_files": installed,
                  "text_files_verified_unchanged": [{"relative_path": p, "sha256": h} for p, h in text_hashes],
                  "saves_modified": False, "original_assets_modified": False,
                  "updates_modified": False, "unrelated_mods_modified": False,
                  "runtime_tested": False, "emulator_launched": False}
        install_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        return record
    except Exception:
        rollback_targets(mod_root, backup_root, backup)
        raise


def rollback(*, record_root: Path = RECORD_ROOT, appdata: Path | None = None,
             text_record_path: Path = TEXT_RECORD) -> dict:
    record_root = record_root.resolve(strict=True)
    record = json.loads((record_root / "installation-record.json").read_text(encoding="utf-8"))
    if record.get("milestone") != "3M":
        raise ValueError("Refusing rollback from a non-3M install record")
    backup_path = Path(record["backup_manifest"]).resolve(strict=True)
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if Path(record["appdata_root"]).resolve() != profile or profile not in mod_root.parents:
        raise ValueError("Recorded mod root is outside current AzaharPlus profile")
    _verify_text(mod_root, text_record_path)
    originals = {row["relative_path"]: row for row in backup["files"]}
    for row in record["installed_files"]:
        rel = row["relative_path"]
        target = mod_root.joinpath(*PurePosixPath(rel).parts)
        old = originals[rel]
        if not target.is_file() or file_hash(target) != row["sha256"]:
            raise ValueError(f"Installed image changed; refusing rollback: {rel}")
        saved = backup_path.parent.joinpath(*PurePosixPath(rel).parts)
        if old["existed"] and (not saved.is_file() or saved.stat().st_size != old["size"]
                                or file_hash(saved) != old["sha256"]):
            raise ValueError(f"Image backup missing/corrupt; refusing rollback: {rel}")
    restored = rollback_targets(mod_root, backup_path.parent, backup)
    for rel in restored:
        old = originals[rel]
        target = mod_root.joinpath(*PurePosixPath(rel).parts)
        if old["existed"]:
            if not target.is_file() or file_hash(target) != old["sha256"]:
                raise OSError(f"Restored image failed verification: {rel}")
        elif target.exists():
            raise OSError(f"Originally absent image still exists: {rel}")
    text = _verify_text(mod_root, text_record_path)
    expected = record["text_files_verified_unchanged"]
    if [(row["relative_path"], row["sha256"]) for row in text] != [
            (row["relative_path"], row["sha256"]) for row in expected]:
        raise ValueError("Text archives changed; refusing to record rollback")
    result = {"milestone": "3M", "rollback_verified": True, "restored_paths": restored,
              "text_files_unchanged": True, "saves_modified": False, "unrelated_mods_modified": False}
    rollback_file = record_root / "rollback-record.json"
    if rollback_file.exists():
        raise FileExistsError(f"Rollback record exists: {rollback_file}")
    rollback_file.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    print(json.dumps(rollback() if args.rollback else install(args.manifest), sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
