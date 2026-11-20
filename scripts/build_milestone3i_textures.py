#!/usr/bin/env python3
"""Build owner-editable battle UI textures and isolated X/Y image candidates."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.extract_milestone3h_textures import TITLE_IDS, write_png
from src.extraction.garc import GARC
from src.extraction.lz11 import decompress as lz11_decompress
from src.rebuilding.textures import (backup_workspace, decode_bclim, encode_bclim,
                                     parse_texture_pack, read_png_rgba, replace_archive_member,
                                     replace_texture_pack, restore_workspace, sha256)

RESOURCE_TARGETS: dict[str, dict[str, tuple[int, int]]] = {
    "a/2/4/0": {name: (0, 2) for name in (
        "fight_text.bclim", "bag_button.bclim", "pokemon_button.bclim", "run_button.bclim",
        "ally_gauge.bclim", "enemy_gauge.bclim")},
    "a/2/3/9": {f"type_icon_{index:02d}_{name}.bclim": (0, 2) for index, name in enumerate((
        "normal", "kakutou", "hikou", "doku", "jimen", "iwa", "mushi", "ghost", "hagane",
        "honoo", "mizu", "kusa", "denki", "esper", "koori", "dragon", "aku", "yousei"))},
}
EXPECTED_INTERNAL = set(RESOURCE_TARGETS["a/2/4/0"]) | set(RESOURCE_TARGETS["a/2/3/9"])
EXPECTED_PNGS = {f"{name}.png" for name in EXPECTED_INTERNAL}
EDITING = ROOT / "build/milestone-3i/editing"
OUTPUT = ROOT / "build/milestone-3i/image-candidate"
BACKUPS = ROOT / "build/milestone-3i/backups"


def _effective(game: str, resource: str) -> tuple[Path, str]:
    base = ROOT / "workspace" / game / "base" / Path(*resource.split("/"))
    update = ROOT / "workspace" / game / "update-1.5" / Path(*resource.split("/"))
    if update.is_file():
        return update, "update-1.5"
    if base.is_file():
        return base, "base"
    raise FileNotFoundError(f"No base/update resource: {resource} ({game})")


def _member_pack(archive_bytes: bytes, member_key: tuple[int, int]) -> tuple[bytes, bytes, bool]:
    archive = GARC.parse(archive_bytes)
    member = next((m for m in archive.members if (m.entry_id, m.subfile_id) == member_key), None)
    if member is None:
        raise ValueError(f"Archive lacks texture member {member_key}")
    compressed = member.data[:1] == b"\x11"
    return (lz11_decompress(member.data) if compressed else member.data), member.data, compressed


def initialize_editing_workspace(editing_root: Path = EDITING) -> dict[str, object]:
    if editing_root.exists() and any(editing_root.iterdir()):
        raise ValueError(f"Refusing to overwrite non-empty editing workspace: {editing_root}")
    rows = []
    for filename in sorted(EXPECTED_INTERNAL):
        resources = [resource for resource, files in RESOURCE_TARGETS.items() if filename in files]
        if len(resources) != 1:
            raise ValueError(f"Ambiguous canonical texture filename: {filename}")
        resource = resources[0]
        member_key = RESOURCE_TARGETS[resource][filename]
        source_path, source_version = _effective("pokemon-x", resource)
        y_path, y_version = _effective("pokemon-y", resource)
        source_archive = source_path.read_bytes()
        if source_archive != y_path.read_bytes() or source_version != y_version:
            raise ValueError(f"X/Y effective sources differ for {resource}")
        pack, compressed_member, is_compressed = _member_pack(source_archive, member_key)
        texture = next((item for item in parse_texture_pack(pack) if item["name"] == filename), None)
        if texture is None:
            raise ValueError(f"Source texture not found: {resource}:{member_key}:{filename}")
        width, height, fmt, rgba = decode_bclim(texture["data"])
        if fmt not in (8, 9):
            raise ValueError(f"Unexpected source texture format {fmt} for {filename}")
        output_png = editing_root / f"{filename}.png"
        write_png(output_png, width, height, rgba)
        rows.append({"resource": resource, "member": f"{member_key[0]}/{member_key[1]}",
                     "pack_order": texture["order"], "internal_filename": filename,
                     "png": f"{filename}.png", "width": width, "height": height, "bclim_format": fmt,
                     "source_version": source_version, "source_archive_sha256": sha256(source_archive),
                     "source_compressed_member_sha256": sha256(compressed_member),
                     "source_bclim_sha256": sha256(texture["data"]),
                     "source_png_sha256": sha256(output_png.read_bytes()),
                     "source_alpha_transparent_pixels": sum(rgba[i] == 0 for i in range(3, len(rgba), 4)),
                     "member_lz11_compressed": is_compressed})
    manifest = {"milestone": "3I", "set": "canonical-24", "assets": rows,
                "warning": "Game-derived PNGs are local working files; do not commit or redistribute."}
    editing_root.mkdir(parents=True, exist_ok=True)
    (editing_root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                                  encoding="utf-8", newline="\n")
    return manifest


def _verify_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    assets = manifest.get("assets")
    if manifest.get("set") != "canonical-24" or not isinstance(assets, list) or len(assets) != 24:
        raise ValueError("Editing manifest is not the canonical 24-image set")
    names = [str(item["png"]) for item in assets]
    if set(names) != EXPECTED_PNGS or len(names) != len(set(names)):
        raise ValueError("Editing manifest image filenames do not match the 24 canonical targets")
    return assets  # type: ignore[return-value]


def build_images(*, editing_root: Path = EDITING, output_root: Path = OUTPUT,
                 dry_run: bool = False) -> dict[str, object]:
    manifest_path = editing_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assets = _verify_manifest(manifest)
    replacements_by_resource: dict[str, dict[str, bytes]] = {resource: {} for resource in RESOURCE_TARGETS}
    proof_by_resource: dict[str, list[dict[str, object]]] = {resource: [] for resource in RESOURCE_TARGETS}
    for item in assets:
        resource = str(item["resource"])
        filename = str(item["internal_filename"])
        if resource not in RESOURCE_TARGETS or filename not in RESOURCE_TARGETS[resource]:
            raise ValueError(f"Manifest resource mapping is not allowlisted: {resource}:{filename}")
        source_path, version = _effective("pokemon-x", resource)
        source_archive = source_path.read_bytes()
        if version != item["source_version"] or sha256(source_archive) != item["source_archive_sha256"]:
            raise ValueError(f"Source resource changed since extraction: {resource}")
        pack, _, _ = _member_pack(source_archive, tuple(map(int, str(item["member"]).split("/"))))
        texture = next((part for part in parse_texture_pack(pack) if part["name"] == filename), None)
        if texture is None or sha256(texture["data"]) != item["source_bclim_sha256"]:
            raise ValueError(f"Source texture changed since extraction: {resource}:{filename}")
        png_path = editing_root / str(item["png"])
        width, height, rgba = read_png_rgba(png_path)
        if (width, height) != (item["width"], item["height"]):
            raise ValueError(f"Edited PNG dimensions changed for {filename}: {width}x{height}")
        transparent = sum(rgba[i] == 0 for i in range(3, len(rgba), 4))
        alpha_opaque = sum(rgba[i] == 255 for i in range(3, len(rgba), 4))
        if not transparent or not alpha_opaque:
            raise ValueError(f"PNG alpha/transparency was flattened or erased: {filename}")
        if dry_run and sha256(png_path.read_bytes()) != item["source_png_sha256"]:
            raise ValueError(f"Dry-run requires untouched original PNG: {filename}")
        encoded = encode_bclim(rgba, width, height, texture["data"])
        dw, dh, fmt, decoded = decode_bclim(encoded)
        if (dw, dh, fmt) != (width, height, item["bclim_format"]):
            raise ValueError(f"BCLIM metadata changed for {filename}")
        channel_errors = [abs(a - b) for a, b in zip(rgba, decoded)]
        max_error = max(channel_errors, default=0)
        if max_error > (9 if fmt == 8 else 0):
            raise ValueError(f"PNG/BCLIM decoded pixel mismatch for {filename}: max channel delta {max_error}")
        if dry_run and decoded != decode_bclim(texture["data"])[3]:
            raise ValueError(f"Original-image dry-run changed decoded pixels: {filename}")
        replacements_by_resource[resource][filename] = encoded
        proof_by_resource[resource].append({"filename": filename, "png_sha256": sha256(png_path.read_bytes()),
                                            "output_bclim_sha256": sha256(encoded),
                                            "source_bclim_sha256": item["source_bclim_sha256"],
                                            "byte_identical_bclim": encoded == texture["data"],
                                            "decoded_pixel_sha256": sha256(decoded),
                                            "transparent_pixels": transparent,
                                            "opaque_pixels": alpha_opaque, "max_channel_delta": max_error,
                                            "pack_order": item["pack_order"]})

    result: dict[str, object] = {"milestone": "3I", "build_state": "original_image_dry_run" if dry_run else "uninstalled_image_candidate",
                                "installed": False, "runtime_tested": False, "original_assets_modified": False,
                                "games": {}, "dry_run": dry_run}
    all_game_results: dict[str, object] = {}
    backup_manifest_path = output_root / "candidate-backup-manifest.json"
    backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8")) if backup_manifest_path.exists() else {"backups": {}}
    for game, title_id in TITLE_IDS.items():
        game_results = []
        for resource in RESOURCE_TARGETS:
            source_path, version = _effective(game, resource)
            source_archive = source_path.read_bytes()
            if sha256(source_archive) != next(row["source_archive_sha256"] for row in assets if row["resource"] == resource):
                raise ValueError(f"X/Y resource source mismatch at build time: {game}/{resource}")
            member_key = RESOURCE_TARGETS[resource][next(iter(RESOURCE_TARGETS[resource]))]
            pack, _, _ = _member_pack(source_archive, member_key)
            patched_pack = replace_texture_pack(pack, replacements_by_resource[resource])
            for original in parse_texture_pack(pack):
                if original["name"] not in replacements_by_resource[resource]:
                    rebuilt = next(item for item in parse_texture_pack(patched_pack) if item["name"] == original["name"])
                    if rebuilt["data"] != original["data"]:
                        raise ValueError(f"Unrelated texture changed in {resource}: {original['name']}")
            archive_output, archive_proof = replace_archive_member(source_archive, member_key, patched_pack)
            destination = output_root / game / "romfs" / Path(*resource.split("/"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                backup = destination.with_suffix(destination.suffix + ".bak")
                if not backup.exists():
                    shutil.copyfile(destination, backup)
                    backup_key = destination.relative_to(output_root).as_posix()
                    backup_manifest["backups"][backup_key] = sha256(backup.read_bytes())
                else:
                    backup_key = destination.relative_to(output_root).as_posix()
                    if backup_key not in backup_manifest["backups"] or sha256(backup.read_bytes()) != backup_manifest["backups"][backup_key]:
                        raise ValueError(f"Candidate backup hash is missing or invalid: {backup}")
            destination.write_bytes(archive_output)
            game_results.append({"resource": resource, "source_version": version,
                                 "source_path": source_path.relative_to(ROOT).as_posix(),
                                 "layeredfs_title_id": title_id,
                                 "output_path": destination.relative_to(output_root).as_posix(),
                                 "textures": proof_by_resource[resource], **archive_proof})
        all_game_results[game] = {"title_id": title_id, "resources": game_results}
    result["games"] = all_game_results
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "manifest.json").write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                                 encoding="utf-8", newline="\n")
    if backup_manifest["backups"]:
        backup_manifest_path.write_text(json.dumps(backup_manifest, sort_keys=True, indent=2) + "\n",
                                        encoding="utf-8", newline="\n")
    return result


def restore_candidate(output_root: Path = OUTPUT) -> list[str]:
    restored = []
    backup_manifest_path = output_root / "candidate-backup-manifest.json"
    backup_manifest = json.loads(backup_manifest_path.read_text(encoding="utf-8")) if backup_manifest_path.exists() else {"backups": {}}
    for candidate in output_root.glob("*/romfs/a/*/*/*"):
        backup = candidate.with_suffix(candidate.suffix + ".bak")
        if backup.is_file():
            relative = candidate.relative_to(output_root).as_posix()
            expected_hash = backup_manifest.get("backups", {}).get(relative)
            if not expected_hash or sha256(backup.read_bytes()) != expected_hash:
                raise ValueError(f"Candidate backup hash mismatch; refusing rollback: {backup}")
            if candidate.is_file():
                candidate.unlink()
            backup.replace(candidate)
            restored.append(candidate.relative_to(output_root).as_posix())
        elif candidate.is_file():
            candidate.unlink()
            restored.append(candidate.relative_to(output_root).as_posix() + " (removed generated candidate)")
    manifest = output_root / "manifest.json"
    if manifest.exists():
        manifest.unlink()
    if backup_manifest_path.exists():
        backup_manifest_path.unlink()
    return restored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--init-editing-workspace", action="store_true")
    modes.add_argument("--backup-editing-workspace", action="store_true")
    modes.add_argument("--restore-editing-backup", type=Path)
    modes.add_argument("--dry-run", action="store_true", help="reinsert untouched original PNGs and verify byte/pixel identity")
    modes.add_argument("--build-candidate", action="store_true", help="build an uninstalled candidate from current edited PNGs")
    modes.add_argument("--rollback-candidate", action="store_true", help="restore/remove only generated candidate outputs")
    args = parser.parse_args()
    if args.init_editing_workspace:
        result = initialize_editing_workspace()
    elif args.backup_editing_workspace:
        result = {"backup": backup_workspace(EDITING, BACKUPS, EXPECTED_PNGS).relative_to(ROOT).as_posix()}
    elif args.restore_editing_backup:
        target = args.restore_editing_backup.resolve(strict=True)
        if ROOT.resolve() not in target.parents:
            parser.error("backup must be under the project root")
        restore_workspace(EDITING, target, EXPECTED_PNGS)
        result = {"restored": target.relative_to(ROOT).as_posix()}
    elif args.rollback_candidate:
        result = {"rolled_back": restore_candidate(OUTPUT)}
    else:
        output = ROOT / "build/milestone-3i/dry-run" if args.dry_run else OUTPUT
        result = build_images(output_root=output, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
