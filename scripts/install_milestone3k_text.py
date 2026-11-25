#!/usr/bin/env python3
"""Install or roll back only the four verified Milestone 3J text archives."""
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
from src.extraction.garc import GARC
from src.rebuilding.installation import azaharplus_paths, backup_targets, rollback_targets

BUILD_ROOT = ROOT / "build/milestone-3j/text-candidate"
RECORD_ROOT = ROOT / "build/milestone-3k"
GAMES = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCES = {"a/0/7/4": "update-1.5", "a/0/8/2": "base"}
PRIOR_RECORD = ROOT / "build/milestone-3g/installation-record.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def candidate_targets(manifest_path: Path) -> tuple[dict, list[tuple[str, dict, Path]]]:
    manifest_path = manifest_path.resolve(strict=True)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (manifest.get("milestone") != "3J"
            or manifest.get("build_state") != "unapproved_integrated_runtime_candidate"
            or manifest.get("runtime_tested") is not False
            or manifest.get("installed") is not False
            or manifest.get("original_assets_modified") is not False
            or manifest.get("translation_records") != 227):
        raise ValueError("Manifest is not the verified, uninstalled Milestone 3J candidate")
    candidate_root = manifest_path.parent.resolve()
    targets: list[tuple[str, dict, Path]] = []
    for game, title_id in GAMES.items():
        game_data = manifest.get("games", {}).get(game, {})
        if game_data.get("title_id") != title_id:
            raise ValueError(f"Unexpected or missing base Title ID for {game}")
        rows = game_data.get("resources", [])
        by_resource = {row.get("resource"): row for row in rows}
        if len(by_resource) != len(rows) or set(by_resource) != set(RESOURCES):
            raise ValueError(f"Unexpected resource set in candidate for {game}")
        for resource, expected_version in RESOURCES.items():
            proof = by_resource[resource]
            if proof.get("source_version") != expected_version:
                raise ValueError(f"Wrong effective source version for {game}/{resource}")
            relative = PurePosixPath(proof.get("output_path", ""))
            if relative.is_absolute() or any(part in ("", ".", "..") for part in relative.parts):
                raise ValueError(f"Unsafe candidate-relative path: {relative}")
            source = (candidate_root / Path(*relative.parts)).resolve(strict=True)
            if candidate_root not in source.parents or not source.is_file():
                raise ValueError(f"Candidate path escapes build root: {source}")
            if source.stat().st_size != int(proof["output_size"]):
                raise ValueError(f"Candidate size mismatch: {source}")
            if sha256_file(source) != proof["output_sha256"]:
                raise ValueError(f"Candidate SHA-256 mismatch: {source}")
            raw = source.read_bytes()
            archive = GARC.parse(raw)
            if archive.rebuild() != raw:
                raise ValueError(f"Candidate GARC identity round trip failed: {source}")
            targets.append((f"{title_id}/romfs/{resource}", proof, source))
    if len(targets) != 4 or len({item[0] for item in targets}) != 4:
        raise ValueError("Expected exactly four separate X/Y text targets")
    return manifest, targets


def _verify_prior_3g(mod_root: Path, relative_paths: list[str], prior_record_path: Path = PRIOR_RECORD) -> None:
    """Require current targets to be the files recorded by 3G before stacking 3K."""
    if not prior_record_path.is_file():
        return
    prior = json.loads(prior_record_path.read_text(encoding="utf-8"))
    if prior.get("milestone") != "3G":
        raise ValueError("Existing Milestone 3G installation record has an unexpected format")
    expected = {row["relative_path"]: row["installed_sha256"] for row in prior.get("installed_files", [])}
    if not expected:
        raise ValueError("Milestone 3G installation record has no installed-file hashes")
    for relative in relative_paths:
        if relative not in expected:
            raise ValueError(f"Target is not covered by the prior 3G record: {relative}")
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or sha256_file(target) != expected[relative]:
            raise ValueError(f"Current mod target differs from its Milestone 3G hash; refusing replacement: {relative}")


def install(manifest_path: Path = BUILD_ROOT / "manifest.json", *,
            appdata: Path | None = None, record_root: Path = RECORD_ROOT,
            prior_record_path: Path = PRIOR_RECORD) -> dict:
    _, targets = candidate_targets(manifest_path)
    profile, mod_root = azaharplus_paths(appdata)
    record_root = record_root.resolve()
    install_record_path = record_root / "installation-record.json"
    rollback_record_path = record_root / "rollback-record.json"
    if install_record_path.exists() or rollback_record_path.exists():
        raise FileExistsError(f"Milestone 3K records already exist; refusing to overwrite: {record_root}")
    relative_paths = [relative for relative, _, _ in targets]
    _verify_prior_3g(mod_root, relative_paths, prior_record_path)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_root = record_root / "installation-backups" / stamp
    if backup_root.exists():
        raise FileExistsError(f"Milestone 3K backup already exists: {backup_root}")
    backup_manifest = backup_targets(mod_root, backup_root, relative_paths)
    backups = {row["relative_path"]: row for row in backup_manifest["files"]}
    try:
        # Recheck target existence/hashes after backup to detect concurrent edits.
        for relative, _, _ in targets:
            target = mod_root.joinpath(*PurePosixPath(relative).parts)
            saved = backups[relative]
            if not saved["existed"] or not target.is_file():
                raise RuntimeError(f"Expected existing target changed during backup: {relative}")
            if sha256_file(target) != saved["sha256"]:
                raise RuntimeError(f"Target changed during backup: {relative}")

        installed = []
        for relative, proof, candidate in targets:
            destination = mod_root.joinpath(*PurePosixPath(relative).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name(destination.name + ".milestone-3k-tmp")
            if temporary.exists():
                raise FileExistsError(f"Temporary target already exists: {temporary}")
            shutil.copyfile(candidate, temporary)
            if sha256_file(temporary) != proof["output_sha256"]:
                temporary.unlink(missing_ok=True)
                raise OSError(f"Staged copy hash mismatch: {relative}")
            temporary.replace(destination)
            installed.append({"relative_path": relative, "sha256": proof["output_sha256"],
                              "resource": proof["resource"], "source_version": proof["source_version"],
                              "size": proof["output_size"]})
        for row in installed:
            path = mod_root.joinpath(*PurePosixPath(row["relative_path"]).parts)
            if sha256_file(path) != row["sha256"]:
                raise OSError(f"Installed read-back hash mismatch: {row['relative_path']}")

        record_root.mkdir(parents=True, exist_ok=True)
        record = {"milestone": "3K", "build_milestone": "3J", "mod_root": str(mod_root),
                  "appdata_root": str(profile), "build_manifest": str(Path(manifest_path).resolve()),
                  "backup_manifest": str((backup_root / "manifest.json").resolve()),
                  "backup_files": backup_manifest["files"], "installed_files": installed,
                  "original_assets_modified": False, "updates_modified": False,
                  "saves_modified": False, "unrelated_mods_modified": False,
                  "emulator_launched": False, "translations_approved": False}
        install_record_path.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n",
                                       encoding="utf-8", newline="\n")
        return record
    except Exception:
        rollback_targets(mod_root, backup_root, backup_manifest)
        raise


def rollback(*, record_root: Path = RECORD_ROOT, appdata: Path | None = None) -> dict:
    record_root = record_root.resolve(strict=True)
    record_path = record_root / "installation-record.json"
    record = json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("milestone") != "3K" or record.get("build_milestone") != "3J":
        raise ValueError("Refusing rollback from a non-3K installation record")
    backup_manifest_path = Path(record["backup_manifest"]).resolve(strict=True)
    backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8"))
    profile, active_mod_root = azaharplus_paths(appdata)
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if Path(record["appdata_root"]).resolve() != profile or mod_root != active_mod_root:
        raise ValueError("Recorded AzaharPlus mod root is outside the current user profile")
    originals = {row["relative_path"]: row for row in backup_manifest["files"]}
    # Preflight every target and backup before changing any target.
    for row in record["installed_files"]:
        relative = row["relative_path"]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        original = originals[relative]
        if not target.is_file() or sha256_file(target) != row["sha256"]:
            raise ValueError(f"Installed target changed; refusing rollback: {relative}")
        saved = backup_manifest_path.parent.joinpath(*PurePosixPath(relative).parts)
        if (not original["existed"] or not saved.is_file() or saved.stat().st_size != original["size"]
                or sha256_file(saved) != original["sha256"]):
            raise ValueError(f"Prior file backup missing or invalid; refusing rollback: {relative}")
    restored = rollback_targets(mod_root, backup_manifest_path.parent, backup_manifest)
    for relative in restored:
        prior = originals[relative]
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not prior["existed"] or not target.is_file() or sha256_file(target) != prior["sha256"]:
            raise OSError(f"Rollback read-back verification failed: {relative}")
    result = {"milestone": "3K", "rollback_verified": True, "restored_paths": restored,
              "saves_modified": False, "unrelated_mods_modified": False}
    (record_root / "rollback-record.json").write_text(json.dumps(result, sort_keys=True, indent=2) + "\n",
                                                       encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--rollback", action="store_true")
    parser.add_argument("--manifest", type=Path, default=BUILD_ROOT / "manifest.json")
    parser.add_argument("--record-root", type=Path, default=RECORD_ROOT,
                        help="Use a new build directory for the active profile's records")
    parser.add_argument("--prior-record", type=Path, default=PRIOR_RECORD)
    args = parser.parse_args()
    if ROOT / "build" not in args.record_root.resolve().parents:
        parser.error("--record-root must be inside build/")
    if args.rollback:
        result = rollback(record_root=args.record_root)
    else:
        if not args.prior_record.is_file():
            parser.error("--prior-record must name an existing 3G installation record")
        result = install(args.manifest, record_root=args.record_root, prior_record_path=args.prior_record)
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
