"""Exact-file backup and rollback primitives for LayeredFS pilot files."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
from typing import Any


def azaharplus_paths(appdata: Path | None = None) -> tuple[Path, Path]:
    """Resolve the active profile and its existing LayeredFS root."""
    override = os.environ.get("AZAHARPLUS_DATA_DIR")
    if appdata is not None or (sys.platform == "win32" and not override):
        profile = appdata if appdata is not None else Path(os.environ["APPDATA"])
        data = profile / "AzaharPlus"
    elif override:
        profile = data = Path(override).expanduser()
        if not data.is_absolute():
            raise ValueError("AZAHARPLUS_DATA_DIR must be absolute")
    elif sys.platform.startswith("linux"):
        xdg = Path(os.environ.get("XDG_DATA_HOME", ""))
        if not xdg.is_absolute():
            xdg = Path.home() / ".local/share"
        profile = data = xdg / "azaharplus-emu"
    else:
        raise ValueError("Set AZAHARPLUS_DATA_DIR to the verified emulator data directory")

    profile = profile.resolve(strict=True)
    mods = (data / "load/mods").resolve(strict=True)
    if not mods.is_dir() or profile not in mods.parents:
        raise ValueError(f"Invalid AzaharPlus LayeredFS root: {mods}")
    return profile, mods


def _safe_target(root: Path, relative: str) -> Path:
    if "\\" in relative:
        raise ValueError(f"Use slash-separated LayeredFS relative paths: {relative}")
    rel = PurePosixPath(relative)
    if rel.is_absolute() or not rel.parts or any(part in ("", ".", "..") for part in rel.parts):
        raise ValueError(f"Unsafe mod-relative path: {relative}")
    root = root.resolve()
    target = (root / Path(*rel.parts)).resolve()
    if root != target and root not in target.parents:
        raise ValueError(f"Target escapes LayeredFS root: {relative}")
    return target


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def backup_targets(mod_root: Path, backup_root: Path, relative_paths: list[str]) -> dict[str, Any]:
    """Snapshot only listed existing mod files and record previously absent targets."""
    mod_root = mod_root.resolve()
    backup_root = backup_root.resolve()
    if mod_root == backup_root or mod_root in backup_root.parents or backup_root in mod_root.parents:
        raise ValueError("Backup and mod roots must be disjoint")
    if backup_root.exists() and any(backup_root.iterdir()):
        raise FileExistsError(f"Refusing to overwrite nonempty backup directory: {backup_root}")
    seen: set[str] = set()
    records = []
    for relative in relative_paths:
        if relative in seen:
            raise ValueError(f"Duplicate backup target: {relative}")
        seen.add(relative)
        source = _safe_target(mod_root, relative)
        record: dict[str, Any] = {"relative_path": PurePosixPath(relative).as_posix(), "existed": source.is_file()}
        if source.is_file():
            data = source.read_bytes()
            destination = _safe_target(backup_root, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied = destination.read_bytes()
            if _sha256(copied) != _sha256(data):
                raise OSError(f"Backup verification failed for {relative}")
            record.update({"size": len(data), "sha256": _sha256(data)})
        records.append(record)
    backup_root.mkdir(parents=True, exist_ok=True)
    manifest = {"schema_version": 1, "mod_root": str(mod_root), "backup_root": str(backup_root), "files": records}
    (backup_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifest


def rollback_targets(mod_root: Path, backup_root: Path, manifest: dict[str, Any]) -> list[str]:
    """Restore snapshotted files and remove only files recorded as previously absent."""
    mod_root = mod_root.resolve()
    backup_root = backup_root.resolve()
    if Path(manifest.get("mod_root", "")).resolve() != mod_root or Path(manifest.get("backup_root", "")).resolve() != backup_root:
        raise ValueError("Rollback roots do not match the backup manifest")
    restored = []
    for record in manifest.get("files", []):
        relative = str(record["relative_path"])
        target = _safe_target(mod_root, relative)
        if record["existed"]:
            backup = _safe_target(backup_root, relative)
            data = backup.read_bytes()
            if len(data) != record["size"] or _sha256(data) != record["sha256"]:
                raise ValueError(f"Backup hash mismatch; refusing rollback for {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".rollback-tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
        elif target.is_file():
            target.unlink()
        restored.append(relative)
    return restored
