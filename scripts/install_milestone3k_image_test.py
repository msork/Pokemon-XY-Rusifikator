#!/usr/bin/env python3
"""Install or roll back only the separate Milestone 3K FIGHT image test."""
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

MANIFEST = ROOT / "build/milestone-3k/image-candidate/manifest.json"
RECORD_ROOT = ROOT / "build/milestone-3k/image-install"
EXPECTED = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCE = "a/2/4/0"


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_targets(manifest_path: Path = MANIFEST) -> list[tuple[str, dict, Path]]:
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("milestone") != "3K" or manifest.get("build_state") != "disposable_uninstalled_battle_art_test"
            or manifest.get("installed") is not False or manifest.get("runtime_tested") is not False
            or manifest.get("original_assets_modified") is not False
            or manifest.get("canonical_png_modified") is not False):
        raise ValueError("Not a verified uninstalled Milestone 3K artwork test")
    candidate_root = manifest_path.parent.resolve()
    rows = manifest.get("games")
    if not isinstance(rows, list) or {item.get("game") for item in rows} != set(EXPECTED):
        raise ValueError("Image test manifest must contain exactly X and Y")
    targets = []
    for item in rows:
        game = item["game"]
        if (item.get("title_id") != EXPECTED[game] or item.get("resource") != RESOURCE
                or item.get("source_version") != "base" or item.get("modified_texture") != "fight_text.bclim"
                or item.get("dimensions") != [80, 50] or item.get("bclim_format") != 8
                or item.get("unchanged_garc_members_verified") != 6
                or item.get("unchanged_textures_verified") != 10):
            raise ValueError(f"Unexpected image test target proof for {game}")
        relative = PurePosixPath(item.get("output_path", ""))
        if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
            raise ValueError(f"Unsafe image candidate path: {relative}")
        source = (candidate_root / Path(*relative.parts)).resolve(strict=True)
        if candidate_root not in source.parents or not source.is_file():
            raise ValueError(f"Image candidate escapes build root: {source}")
        if source.stat().st_size != int(item["output_size"]) or file_hash(source) != item["output_sha256"]:
            raise ValueError(f"Image candidate size/hash mismatch: {source}")
        raw = source.read_bytes()
        archive = GARC.parse(raw)
        if archive.rebuild() != raw:
            raise ValueError(f"Image candidate GARC validation failed: {source}")
        targets.append((f"{EXPECTED[game]}/romfs/{RESOURCE}", item, source))
    if len(targets) != 2 or len({row[0] for row in targets}) != 2:
        raise ValueError("Expected exactly two separate X/Y image targets")
    return targets


def install(manifest_path: Path = MANIFEST, *, appdata: Path | None = None,
            record_root: Path = RECORD_ROOT) -> dict:
    targets = candidate_targets(manifest_path)
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = (profile / "AzaharPlus/load/mods").resolve(strict=True)
    if profile not in mod_root.parents or not mod_root.is_dir():
        raise ValueError(f"AzaharPlus mod root is outside the current profile or missing: {mod_root}")
    record_root = record_root.resolve()
    if (record_root / "installation-record.json").exists() or (record_root / "rollback-record.json").exists():
        raise FileExistsError(f"Separate Milestone 3K image-install records already exist: {record_root}")
    relative_paths = [row[0] for row in targets]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = record_root / "installation-backups" / stamp
    if backup_root.exists():
        raise FileExistsError(f"Image backup directory already exists: {backup_root}")
    backup_manifest = backup_targets(mod_root, backup_root, relative_paths)
    saved = {row["relative_path"]: row for row in backup_manifest["files"]}
    try:
        installed = []
        for relative, proof, candidate in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            prior = saved[relative]
            if prior["existed"] != destination.is_file():
                raise RuntimeError(f"Target changed during backup: {relative}")
            if prior["existed"] and file_hash(destination) != prior["sha256"]:
                raise RuntimeError(f"Target hash changed during backup: {relative}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".milestone-3k-image-tmp")
            if temporary.exists():
                raise FileExistsError(f"Temporary target already exists: {temporary}")
            shutil.copyfile(candidate, temporary)
            if file_hash(temporary) != proof["output_sha256"]:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Staged candidate hash mismatch: {relative}")
            temporary.replace(destination)
            if file_hash(destination) != proof["output_sha256"]:
                raise OSError(f"Installed image read-back mismatch: {relative}")
            installed.append({"relative_path": relative, "sha256": proof["output_sha256"],
                              "size": proof["output_size"], "resource": RESOURCE})
        record_root.mkdir(parents=True, exist_ok=True)
        result = {"milestone": "3K-image", "mod_root": str(mod_root), "appdata_root": str(profile),
                  "build_manifest": str(Path(manifest_path).resolve()),
                  "backup_manifest": str((backup_root / "manifest.json").resolve()),
                  "backup_files": backup_manifest["files"], "installed_files": installed,
                  "saves_modified": False, "original_assets_modified": False,
                  "updates_modified": False, "unrelated_mods_modified": False,
                  "emulator_launched": False, "runtime_tested": False}
        (record_root / "installation-record.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                                              encoding="utf-8", newline="\n")
        return result
    except Exception:
        rollback_targets(mod_root, backup_root, backup_manifest)
        raise


def rollback(*, record_root: Path = RECORD_ROOT, appdata: Path | None = None) -> dict:
    record_root = record_root.resolve(strict=True)
    record = json.loads((record_root / "installation-record.json").read_text(encoding="utf-8"))
    if record.get("milestone") != "3K-image":
        raise ValueError("Refusing rollback from a different install record")
    backup_path = Path(record["backup_manifest"]).resolve(strict=True)
    manifest = json.loads(backup_path.read_text(encoding="utf-8"))
    profile = (appdata or Path(os.environ["APPDATA"])).resolve(strict=True)
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if Path(record["appdata_root"]).resolve() != profile or profile not in mod_root.parents:
        raise ValueError("Recorded mod root is outside current AzaharPlus profile")
    originals = {row["relative_path"]: row for row in manifest["files"]}
    for row in record["installed_files"]:
        relative = row["relative_path"]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or file_hash(target) != row["sha256"]:
            raise ValueError(f"Installed target changed; refusing rollback: {relative}")
        original = originals[relative]
        saved = backup_path.parent.joinpath(*PurePosixPath(relative).parts)
        if original["existed"] and (not saved.is_file() or file_hash(saved) != original["sha256"]):
            raise ValueError(f"Prior image target backup is missing/invalid: {relative}")
    restored = rollback_targets(mod_root, backup_path.parent, manifest)
    result = {"milestone": "3K-image", "rollback_verified": True, "restored_paths": restored,
              "unrelated_mods_modified": False, "saves_modified": False}
    (record_root / "rollback-record.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                                       encoding="utf-8", newline="\n")
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
