#!/usr/bin/env python3
"""Verify the live Milestone 3G install and exact pre-install backups."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECORD = ROOT / "build" / "milestone-3g" / "installation-record.json"
TITLE_IDS = {"0004000000055D00", "0004000000055E00"}
RESOURCES = {"a/0/7/4", "a/0/8/2"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    profile = Path(os.environ["APPDATA"]).resolve(strict=True)
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if record.get("milestone") != "3G" or Path(record["appdata_root"]).resolve() != profile:
        raise ValueError("Installation record is not for this user's Milestone 3G install")
    if profile not in mod_root.parents or len(record.get("installed_files", [])) != 4:
        raise ValueError("Unexpected mod root or target count")

    backup_manifest_path = Path(record["backup_manifest"]).resolve(strict=True)
    backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8"))
    candidate_manifest = json.loads(Path(record["build_manifest"]).read_text(encoding="utf-8"))
    installed = {row["relative_path"]: row for row in record["installed_files"]}
    backups = {row["relative_path"]: row for row in backup_manifest["files"]}
    expected = {f"{title_id}/romfs/{resource}" for title_id in TITLE_IDS for resource in RESOURCES}
    if set(installed) != expected or set(backups) != expected:
        raise ValueError("Installed and backup target sets do not match the four expected files")

    results = []
    for relative in sorted(expected):
        title_id, _, resource = relative.split("/", 2)
        game = "pokemon-x" if title_id == "0004000000055D00" else "pokemon-y"
        proof = next((item for item in candidate_manifest["games"][game]["resources"]
                      if item["resource"] == resource), None)
        if proof is None or proof["output_sha256"] != installed[relative]["installed_sha256"]:
            raise ValueError(f"Install record does not match candidate manifest: {relative}")
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        if not target.is_file() or sha256(target) != installed[relative]["installed_sha256"]:
            raise ValueError(f"Installed target hash mismatch: {relative}")

        prior = backups[relative]
        backup_hash = None
        if prior["existed"]:
            backup = backup_manifest_path.parent.joinpath(*PurePosixPath(relative).parts)
            if (not backup.is_file() or backup.stat().st_size != prior["size"]
                    or sha256(backup) != prior["sha256"]):
                raise ValueError(f"Backup missing or hash mismatch: {relative}")
            backup_hash = prior["sha256"]
        results.append({
            "relative_path": relative,
            "installed_sha256": installed[relative]["installed_sha256"],
            "original_existed": prior["existed"],
            "original_sha256": backup_hash,
            "installed_size": target.stat().st_size,
        })

    print(json.dumps({"result": "PASS", "targets_verified": len(results),
                      "saves_modified": False, "emulator_launched": False,
                      "targets": results}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
