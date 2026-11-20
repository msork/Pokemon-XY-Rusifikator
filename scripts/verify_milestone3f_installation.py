#!/usr/bin/env python3
"""Verify the live Milestone 3F install and its exact pre-install backups."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
RECORD = ROOT / "build" / "milestone-3f" / "installation-record.json"
GAMES = {"0004000000055D00", "0004000000055E00"}
RESOURCES = {"a/0/7/4", "a/0/8/2"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=RECORD)
    args = parser.parse_args()
    record = json.loads(args.record.read_text(encoding="utf-8"))
    expected_profile = Path(os.environ["APPDATA"]).resolve()
    mod_root = Path(record["mod_root"]).resolve(strict=True)
    if Path(record["appdata_root"]).resolve() != expected_profile or expected_profile not in mod_root.parents:
        raise ValueError("Installation record is outside the current user profile")
    if record.get("milestone") != "3F" or len(record.get("installed_files", [])) != 4:
        raise ValueError("Unexpected installation record or target count")
    backup_path = Path(record["backup_manifest"]).resolve(strict=True)
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    candidate_manifest = json.loads(Path(record["build_manifest"]).read_text(encoding="utf-8"))
    installed = {row["relative_path"]: row for row in record["installed_files"]}
    backup_rows = {row["relative_path"]: row for row in backup["files"]}
    expected = {f"{title}/romfs/{resource}" for title in GAMES for resource in RESOURCES}
    if set(installed) != expected or set(backup_rows) != expected:
        raise ValueError("Installed and backed-up target sets differ from the four expected files")
    results = []
    for relative in sorted(expected):
        target = mod_root.joinpath(*PurePosixPath(relative).parts)
        prior = backup_rows[relative]
        title_id, _, resource = relative.split("/", 2)
        game = "pokemon-x" if title_id == "0004000000055D00" else "pokemon-y"
        candidate = next((row for row in candidate_manifest["games"][game]["resources"]
                          if row["resource"] == resource), None)
        if candidate is None or candidate["output_sha256"] != installed[relative]["installed_sha256"]:
            raise ValueError(f"Installed record does not match candidate manifest: {relative}")
        if not target.is_file() or sha256(target) != installed[relative]["installed_sha256"]:
            raise ValueError(f"Installed target hash mismatch: {relative}")
        backup_hash = None
        if prior["existed"]:
            saved = backup_path.parent.joinpath(*PurePosixPath(relative).parts)
            if not saved.is_file() or saved.stat().st_size != prior["size"] or sha256(saved) != prior["sha256"]:
                raise ValueError(f"Original backup hash mismatch: {relative}")
            backup_hash = prior["sha256"]
        results.append({"relative_path": relative, "installed_sha256": installed[relative]["installed_sha256"],
                        "original_existed": prior["existed"], "original_sha256": backup_hash,
                        "installed_size": target.stat().st_size})
    print(json.dumps({"result": "PASS", "targets_verified": len(results), "saves_modified": False,
                      "emulator_launched": False, "targets": results}, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
