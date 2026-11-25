#!/usr/bin/env python3
"""Install or roll back the verified Milestone 3C pilot in AzaharPlus LayeredFS."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.rebuilding.installation import azaharplus_paths, backup_targets, rollback_targets  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "build" / "milestone-3c"
BUILD_MANIFEST = BUILD / "manifest.json"
BACKUP_ROOT = BUILD / "installation-backups" / "2026-11-19-pilot"
BACKUP_MANIFEST = BACKUP_ROOT / "manifest.json"
INSTALL_RECORD = BUILD / "installation-record.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _targets(manifest: dict) -> list[tuple[str, dict, Path]]:
    targets = []
    for game in ("pokemon-x", "pokemon-y"):
        entry = manifest["games"][game]
        title_id = entry["title_id"]
        expected_title = "0004000000055D00" if game == "pokemon-x" else "0004000000055E00"
        if title_id != expected_title:
            raise ValueError(f"Unexpected Title ID for {game}: {title_id}")
        for resource in entry["resources"]:
            relative = f"{title_id}/romfs/{resource['resource']}"
            candidate = BUILD / resource["output_path"]
            if not candidate.is_file() or candidate.stat().st_size != resource["output_size"]:
                raise ValueError(f"Candidate missing or wrong size: {candidate}")
            if sha256(candidate) != resource["output_sha256"]:
                raise ValueError(f"Candidate hash mismatch: {candidate}")
            targets.append((relative, resource, candidate))
    if len(targets) != 4 or len({item[0] for item in targets}) != 4:
        raise ValueError("Expected exactly four distinct X/Y pilot targets")
    return targets


def install() -> dict:
    manifest = json.loads(BUILD_MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("milestone") != "3C" or manifest.get("build_state") != "unapproved_runtime_test_candidate":
        raise ValueError("Build manifest is not the expected unapproved Milestone 3C candidate")
    _, mod_root = azaharplus_paths()
    if INSTALL_RECORD.exists() or BACKUP_ROOT.exists():
        raise FileExistsError("Installation record or backup exists; refusing to overwrite it")

    targets = _targets(manifest)
    paths = [relative for relative, _, _ in targets]
    backup = backup_targets(mod_root, BACKUP_ROOT, paths)
    try:
        # Check that no target changed between the backup and replacement.
        for relative, _, _ in targets:
            current = mod_root.joinpath(*PurePosixPath(relative).parts)
            state = next(item for item in backup["files"] if item["relative_path"] == relative)
            if state["existed"] != current.is_file():
                raise RuntimeError(f"Target existence changed after backup: {relative}")
            if state["existed"] and sha256(current) != state["sha256"]:
                raise RuntimeError(f"Target changed after backup: {relative}")

        installed = []
        for relative, resource, candidate in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".milestone-3c-tmp")
            shutil.copyfile(candidate, temporary)
            if sha256(temporary) != resource["output_sha256"]:
                raise OSError(f"Copied file hash mismatch: {relative}")
            temporary.replace(destination)
            installed.append({
                "relative_path": relative,
                "sha256": resource["output_sha256"],
                "size": resource["output_size"],
            })
        for item in installed:
            target = mod_root.joinpath(*PurePosixPath(item["relative_path"]).parts)
            if sha256(target) != item["sha256"]:
                raise OSError(f"Installed file hash mismatch: {item['relative_path']}")
        record = {
            "milestone": "3C",
            "mod_root": str(mod_root.resolve()),
            "backup_manifest": str(BACKUP_MANIFEST.resolve()),
            "build_manifest": str(BUILD_MANIFEST.resolve()),
            "installed_files": installed,
            "original_assets_modified": False,
            "saves_modified": False,
            "emulator_launched": False,
            "translations_human_approved": False,
        }
        INSTALL_RECORD.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8", newline="\n")
        return record
    except Exception:
        rollback_targets(mod_root, BACKUP_ROOT, backup)
        raise


def rollback() -> list[str]:
    record = json.loads(INSTALL_RECORD.read_text(encoding="utf-8"))
    backup = json.loads(BACKUP_MANIFEST.read_text(encoding="utf-8"))
    mod_root = Path(record["mod_root"]).resolve()
    if mod_root != azaharplus_paths()[1]:
        raise ValueError("Recorded mod root is outside the current user profile")
    for item in record["installed_files"]:
        target = mod_root.joinpath(*PurePosixPath(item["relative_path"]).parts)
        if not target.is_file() or sha256(target) != item["sha256"]:
            raise ValueError(f"Installed target changed; refusing automatic rollback: {target}")
    restored = rollback_targets(mod_root, BACKUP_ROOT, backup)
    return restored


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rollback", action="store_true", help="restore exact pre-install state")
    args = parser.parse_args()
    result = rollback() if args.rollback else install()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
