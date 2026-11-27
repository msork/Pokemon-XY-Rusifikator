"""Generated BCH container, surface and provenance manifests for the artwork scanner."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import struct

from scripts.extract_milestone3h_textures import write_png
from src.extraction.bch import MAGIC, PICA_FORMATS, UnsupportedBch, decode_surface, parse_bch


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _error(exc: ValueError) -> dict:
    return {"status": "unsupported" if isinstance(exc, UnsupportedBch) else "failed", "reason": str(exc)}


class BchInventory:
    def __init__(self, output: Path, root: Path):
        self.output = output
        self.root = root
        self.png_root = output / "bch-png"
        self.containers: dict[str, dict] = {}
        self.images: dict[str, dict] = {}
        self.incidental: list[dict] = []

    def inspect(self, raw: bytes) -> str:
        checksum = _sha256(raw)
        if checksum not in self.containers:
            self.containers[checksum] = self._inspect_container(raw)
        return checksum

    def _inspect_container(self, raw: bytes) -> dict:
        result = {"size": len(raw), "version": list(struct.unpack_from("<BBH", raw, 4)) if len(raw) >= 8 else None}
        try:
            container = parse_bch(raw)
        except ValueError as exc:
            return dict(result, **_error(exc))
        images = []
        issues = list(container.issues)
        for texture in container.textures:
            for surface in texture.surfaces:
                item = dict(asdict(surface), texture_index=texture.index, internal_filename=texture.name,
                            descriptor_offset=texture.descriptor_offset, mipmap_count=texture.mipmap_count,
                            format=texture.format, format_name=PICA_FORMATS[texture.format])
                payload = raw[surface.data_offset:surface.data_offset + surface.data_length]
                item["payload_sha256"] = _sha256(payload)
                try:
                    images.append(dict(item, **self._image(item, payload, surface)))
                except ValueError as exc:
                    issues.append(dict(item, **_error(exc)))
        return dict(result, status="partial" if issues else "valid", resource_counts=container.resource_counts,
                    sections={name: asdict(section) for name, section in container.sections.items()},
                    relocation_count=len(container.relocations),
                    relocation_flags=dict(Counter(f"0x{pointer.flag:02x}" for pointer in container.relocations.values())),
                    surfaces=images, issues=issues)

    def _image(self, item: dict, payload: bytes, surface) -> dict:
        signature = struct.pack("<BHH", item["format"], item["width"], item["height"])
        checksum = _sha256(b"BCH PICA surface\0" + signature + payload)
        if checksum not in self.images:
            rgba = decode_surface(payload, surface, item["format"])
            png = self.png_root / f"{checksum}.png"
            write_png(png, item["width"], item["height"], rgba)
            self.images[checksum] = {"sha256": checksum, "asset_id": f"BCH-{checksum}",
                                     "png_path": png.relative_to(self.root).as_posix()}
        return self.images[checksum]

    def record_incidental(self, raw: bytes, game: str, version: str, archive: str) -> None:
        offset = raw.find(b"BCH")
        while offset >= 0:
            if offset != 0 or not raw.startswith(MAGIC):
                exact = raw.startswith(MAGIC, offset)
                item = {"game": game, "version": version, "archive_path": archive, "offset": offset,
                        "status": "embedded_signature" if exact else "false_signature",
                        "prefix_hex": raw[offset:offset + 8].hex()}
                if exact and len(raw) - offset >= 48:
                    # A common legacy BCH header must point to contents after the header
                    # and within the remaining file. This establishes false hits without
                    # promising to parse arbitrary embedded containers.
                    contents = struct.unpack_from("<I", raw, offset + 8)[0]
                    if contents < 48 or contents >= len(raw) - offset:
                        item["status"] = "false_signature"
                        item["reason"] = "Unbounded contents offset in embedded magic match"
                self.incidental.append(item)
            offset = raw.find(b"BCH", offset + 3)

    def publish(self, occurrences: list[dict]) -> dict:
        rows = []
        by_dataset = {}
        export_counts = Counter()
        for occurrence in occurrences:
            checksum = occurrence["bch_sha256"]
            container = self.containers[checksum]
            occurrence["status"] = container["status"]
            dataset = f"{occurrence['game']}/{occurrence['version']}"
            counts = by_dataset.setdefault(dataset, Counter())
            counts["headers"] += 1
            counts[container["status"]] += 1
            for kind, count in container.get("resource_counts", {}).items():
                export_counts[kind] += count
            counts["exported_surfaces"] += len(container.get("surfaces", ()))
            counts["surface_or_texture_issues"] += len(container.get("issues", ()))
            rows.extend(dict(surface, **occurrence, source_kind="BCH", pending_translation=True)
                        for surface in container.get("surfaces", ()))
        _write_json(self.output / "bch-texture-manifest.json", rows)
        _write_json(self.output / "bch-containers.json",
                    {"containers": self.containers, "occurrences": occurrences, "incidental_magic": self.incidental})
        return {
            "header_occurrences": len(occurrences), "unique_containers": len(self.containers),
            "container_status": dict(Counter(row["status"] for row in occurrences)),
            "unique_container_status": dict(Counter(row["status"] for row in self.containers.values())),
            "resource_occurrences": dict(export_counts),
            "container_occurrences_by_dataset": by_dataset,
            "exported_surface_occurrences": len(rows), "unique_pngs": len({row["sha256"] for row in rows}),
            "incidental_magic": dict(Counter(row["status"] for row in self.incidental)),
            "manifest": (self.output / "bch-texture-manifest.json").relative_to(self.root).as_posix(),
            "containers": (self.output / "bch-containers.json").relative_to(self.root).as_posix(),
        }
