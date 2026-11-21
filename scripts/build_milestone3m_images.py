#!/usr/bin/env python3
"""Deterministically rebuild the 24 edited textures into separate X/Y image candidates."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_milestone3i_textures import (EDITING, RESOURCE_TARGETS, _member_pack,
                                               build_images, validate_editing_workspace)
from scripts.extract_milestone3h_textures import write_png
from src.extraction.garc import GARC
from src.rebuilding.textures import decode_bclim, parse_texture_pack, sha256

OUTPUT = ROOT / "build/milestone-3m/candidate"
PREVIEWS = ROOT / "build/milestone-3m/decoded-previews"
EXPECTED_PNG_SET = 24


def _png_hashes(editing: Path) -> dict[str, str]:
    return {path.name: sha256(path.read_bytes()) for path in sorted(editing.glob("*.png"))}


def _resource_hashes(report: dict) -> dict[tuple[str, str], str]:
    return {(game, row["resource"]): row["output_sha256"]
            for game, data in report["games"].items() for row in data["resources"]}


def _export_previews(candidate_root: Path, preview_root: Path, game: str,
                     resource: str, archive_path: Path) -> list[dict[str, object]]:
    archive_bytes = archive_path.read_bytes()
    archive = GARC.parse(archive_bytes)
    member = next(row for row in archive.members if (row.entry_id, row.subfile_id) == (0, 2))
    pack, _compressed, _was_compressed = _member_pack(archive_bytes, (0, 2))
    textures = parse_texture_pack(pack)
    expected_names = set(RESOURCE_TARGETS[resource])
    output = []
    for texture in textures:
        if texture["name"] not in expected_names:
            continue
        width, height, fmt, rgba = decode_bclim(texture["data"])
        name = str(texture["name"])
        png_path = preview_root / game / Path(*resource.split("/")) / f"{name}.png"
        write_png(png_path, width, height, rgba)
        output.append({"game": game, "resource": resource, "member": "0/2", "internal_filename": name,
                       "dimensions": [width, height], "bclim_format": fmt,
                       "png_path": png_path.relative_to(ROOT).as_posix(),
                       "png_sha256": sha256(png_path.read_bytes()),
                       "garc_member_sha256": sha256(member.data)})
    if {str(row["internal_filename"]) for row in output} != expected_names:
        raise ValueError(f"Unexpected decoded texture count for {game}/{resource}: {len(output)}")
    return output


def build(editing_root: Path = EDITING, output_root: Path = OUTPUT,
          preview_root: Path = PREVIEWS) -> dict[str, object]:
    validation = validate_editing_workspace(editing_root)
    if validation["assets_validated"] != EXPECTED_PNG_SET:
        raise ValueError("Canonical 24-PNG workspace did not validate completely")
    source_png_hashes = _png_hashes(editing_root)
    if len(source_png_hashes) != EXPECTED_PNG_SET:
        raise ValueError(f"Expected 24 source PNGs, found {len(source_png_hashes)}")
    manifest_data = (editing_root / "manifest.json").read_bytes()

    with tempfile.TemporaryDirectory(prefix="pokemon_xy_m3m_repro_") as temp:
        first_root = Path(temp) / "first"
        second_root = Path(temp) / "second"
        first = build_images(editing_root=editing_root, output_root=first_root)
        second = build_images(editing_root=editing_root, output_root=second_root)
        first_hashes, second_hashes = _resource_hashes(first), _resource_hashes(second)
        if first_hashes != second_hashes:
            raise ValueError("Independent rebuilds did not produce identical archive hashes")
        if len(first_hashes) != 4:
            raise ValueError("Expected four deterministic X/Y archive outputs")

    final = build_images(editing_root=editing_root, output_root=output_root)
    if _resource_hashes(final) != first_hashes:
        raise ValueError("Final candidate differs from deterministic proof builds")
    if _png_hashes(editing_root) != source_png_hashes:
        raise RuntimeError("Canonical PNG workspace changed during image build")
    if (editing_root / "manifest.json").read_bytes() != manifest_data:
        raise RuntimeError("Canonical image manifest changed during image build")

    previews = []
    for game, game_data in final["games"].items():
        for resource_row in game_data["resources"]:
            resource = resource_row["resource"]
            archive_path = output_root / game / "romfs" / Path(*resource.split("/"))
            previews.extend(_export_previews(output_root, preview_root, game, resource, archive_path))

    result = {"milestone": "3M", "build_state": "uninstalled_integrated_24_texture_candidate",
              "installed": False, "runtime_tested": False, "original_assets_modified": False,
              "source_workspace": editing_root.relative_to(ROOT).as_posix(),
              "source_manifest_sha256": sha256(manifest_data), "source_pngs": source_png_hashes,
              "source_png_count": len(source_png_hashes), "workspace_validation": validation,
              "deterministic_rebuilds": 3, "deterministic_hashes_match": True,
              "resource_scope": ["a/2/4/0", "a/2/3/9"], "games": final["games"],
              "decoded_preview_count": len(previews), "decoded_previews": previews,
              "preview_scope": "Only the 24 owner-edited textures are decoded to previews; unrelated textures in the same texture packs are preserved and not decoded by this builder."}
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "milestone-3m-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    result = build()
    print(json.dumps({"milestone": result["milestone"], "candidate": OUTPUT.relative_to(ROOT).as_posix(),
                      "deterministic_rebuilds": result["deterministic_rebuilds"],
                      "archive_hashes": {game: {row["resource"]: row["output_sha256"]
                                                 for row in data["resources"]}
                                         for game, data in result["games"].items()},
                      "decoded_preview_count": result["decoded_preview_count"],
                      "installed": False, "runtime_tested": False}, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
