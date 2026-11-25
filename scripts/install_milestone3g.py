#!/usr/bin/env python3
"""Install or roll back the verified Milestone 3G AzaharPlus test candidates."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.rebuilding.installation import azaharplus_paths, backup_targets, rollback_targets  # noqa: E402

BUILD_ROOT = ROOT / "build" / "milestone-3g" / "candidate"
MANIFEST_PATH = BUILD_ROOT / "manifest.json"
RECORD_ROOT = ROOT / "build" / "milestone-3g"
GAMES = {
    "pokemon-x": "0004000000055D00",
    "pokemon-y": "0004000000055E00",
}
EXPECTED_RESOURCES = {"a/0/7/4": "update-1.5", "a/0/8/2": "base"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _candidate_targets(manifest_path: Path) -> tuple[dict, list[tuple[str, dict, Path]]]:
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("milestone") != "3G"
            or manifest.get("build_state") != "unapproved_runtime_test_candidate"
            or manifest.get("runtime_tested") is not False
            or manifest.get("installed") is not False
            or manifest.get("original_assets_modified") is not False):
        raise ValueError("Manifest is not an uninstalled, untested Milestone 3G candidate")
    candidate_root = manifest_path.parent.resolve()
    targets: list[tuple[str, dict, Path]] = []
    for game, title_id in GAMES.items():
        game_manifest = manifest.get("games", {}).get(game, {})
        if game_manifest.get("title_id") != title_id:
            raise ValueError(f"Unexpected or missing Title ID for {game}")
        resources = game_manifest.get("resources", [])
        by_resource = {row.get("resource"): row for row in resources}
        if len(resources) != len(EXPECTED_RESOURCES) or set(by_resource) != set(EXPECTED_RESOURCES):
            raise ValueError(f"Unexpected resource set for {game}: {sorted(by_resource)}")
        for resource, effective_version in EXPECTED_RESOURCES.items():
            proof = by_resource[resource]
            if proof.get("source_version") != effective_version:
                raise ValueError(f"Wrong effective source for {game}/{resource}")
            relative_output = PurePosixPath(proof["output_path"])
            if relative_output.is_absolute() or any(part in ("", ".", "..") for part in relative_output.parts):
                raise ValueError(f"Unsafe candidate path: {proof['output_path']}")
            candidate = (candidate_root / Path(*relative_output.parts)).resolve(strict=True)
            if candidate_root not in candidate.parents or not candidate.is_file():
                raise ValueError(f"Candidate escapes build root or is not a file: {candidate}")
            if candidate.stat().st_size != int(proof["output_size"]):
                raise ValueError(f"Candidate size differs from manifest: {candidate}")
            if sha256(candidate) != proof["output_sha256"]:
                raise ValueError(f"Candidate hash differs from manifest: {candidate}")
            targets.append((f"{title_id}/romfs/{resource}", proof, candidate))
    if len(targets) != 4 or len({target[0] for target in targets}) != 4:
        raise ValueError("Expected four distinct X/Y LayeredFS targets")
    return manifest, targets


def install(manifest_path: Path = MANIFEST_PATH, appdata: Path | None = None,
            record_root: Path = RECORD_ROOT) -> dict:
    manifest, targets = _candidate_targets(manifest_path)
    profile, mod_root = azaharplus_paths(appdata)
    record_root = record_root.resolve()
    install_record = record_root / "installation-record.json"
    rollback_record = record_root / "rollback-record.json"
    if install_record.exists() or rollback_record.exists():
        raise FileExistsError(f"Milestone 3G installation/rollback record already exists: {record_root}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = record_root / "installation-backups" / stamp
    if backup_root.exists():
        raise FileExistsError(f"Backup path already exists: {backup_root}")

    relative_paths = [relative for relative, _, _ in targets]
    backup_manifest = backup_targets(mod_root, backup_root, relative_paths)
    backed_up = {row["relative_path"]: row for row in backup_manifest["files"]}
    try:
        for relative, _, _ in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            prior = backed_up[relative]
            if prior["existed"] != destination.is_file():
                raise RuntimeError(f"Target existence changed after backup: {relative}")
            if prior["existed"] and sha256(destination) != prior["sha256"]:
                raise RuntimeError(f"Target changed after backup: {relative}")

        installed_files = []
        for relative, proof, candidate in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".milestone-3g-tmp")
            if temporary.exists():
                raise FileExistsError(f"Temporary install path already exists: {temporary}")
            shutil.copyfile(candidate, temporary)
            if sha256(temporary) != proof["output_sha256"]:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Copied candidate hash mismatch: {relative}")
            temporary.replace(destination)
            installed_files.append({
                "relative_path": relative,
                "installed_sha256": proof["output_sha256"],
                "size": proof["output_size"],
                "resource": proof["resource"],
                "source_version": proof["source_version"],
            })

        for row in installed_files:
            destination = mod_root.joinpath(*PurePosixPath(row["relative_path"]).parts)
            if sha256(destination) != row["installed_sha256"]:
                raise OSError(f"Installed file hash mismatch: {row['relative_path']}")

        record = {
            "milestone": "3G",
            "mod_root": str(mod_root),
            "appdata_root": str(profile),
            "build_manifest": str(Path(manifest_path).resolve()),
            "backup_manifest": str((backup_root / "manifest.json").resolve()),
            "backup_files": backup_manifest["files"],
            "installed_files": installed_files,
            "original_assets_modified": False,
            "updates_modified": False,
            "saves_modified": False,
            "emulator_launched": False,
            "translations_human_approved": False,
        }
        record_root.mkdir(parents=True, exist_ok=True)
        install_record.write_text(json.dumps(record, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
        return record
    except Exception:
        rollback_targets(mod_root, backup_root, backup_manifest)
        raise


def rollback(record_root: Path = RECORD_ROOT, appdata: Path | None = None) -> dict:
    record_root = record_root.resolve(strict=True)
    install_record = json.loads((record_root / "installation-record.json").read_text(encoding="utf-8"))
    backup_path = Path(install_record["backup_manifest"]).resolve(strict=True)
    backup_manifest = json.loads(backup_path.read_text(encoding="utf-8"))
    profile, active_mod_root = azaharplus_paths(appdata)
    mod_root = Path(install_record["mod_root"]).resolve(strict=True)
    if Path(install_record["appdata_root"]).resolve() != profile or mod_root != active_mod_root:
        raise ValueError("Recorded mod root is outside the current AzaharPlus user profile")
    if (record_root / "rollback-record.json").exists():
        raise FileExistsError("Rollback record already exists")

    originals = {row["relative_path"]: row for row in backup_manifest["files"]}
    for row in install_record["installed_files"]:
        relative = row["relative_path"]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or sha256(target) != row["installed_sha256"]:
            raise ValueError(f"Installed target changed; refusing rollback: {relative}")
        original = originals[relative]
        if original["existed"]:
            saved = backup_path.parent.joinpath(*PurePosixPath(relative).parts)
            if not saved.is_file() or saved.stat().st_size != original["size"] or sha256(saved) != original["sha256"]:
                raise ValueError(f"Backup missing or hash mismatch; refusing rollback: {relative}")

    restored = rollback_targets(mod_root, backup_path.parent, backup_manifest)
    verified = []
    for relative in restored:
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        original = originals[relative]
        if original["existed"]:
            if not target.is_file() or sha256(target) != original["sha256"]:
                raise OSError(f"Restored file failed hash verification: {relative}")
            verified.append({"relative_path": relative, "restored_sha256": original["sha256"]})
        elif target.exists():
            raise OSError(f"Originally absent target still exists after rollback: {relative}")
        else:
            verified.append({"relative_path": relative, "removed_as_originally_absent": True})
    result = {"milestone": "3G", "rollback_verified": True, "restored_files": verified,
              "saves_modified": False, "unrelated_mods_modified": False}
    (record_root / "rollback-record.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--install", action="store_true", help="back up and install four verified candidates")
    action.add_argument("--rollback", action="store_true", help="restore exact pre-install state")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--record-root", type=Path, default=RECORD_ROOT,
                        help="Use a new build directory for the active profile's records")
    args = parser.parse_args()
    if ROOT / "build" not in args.record_root.resolve().parents:
        parser.error("--record-root must be inside build/")
    result = rollback(record_root=args.record_root) if args.rollback else install(args.manifest, record_root=args.record_root)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
