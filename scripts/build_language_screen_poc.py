#!/usr/bin/env python3
"""Build disposable language-selection-screen LayeredFS probes under build/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.garc import GARC, GARCError  # noqa: E402
from src.extraction.lz11 import decompress  # noqa: E402
from src.extraction.messages import MessageError, TextFile  # noqa: E402

TITLE_IDS = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCE = "a/0/7/4"
TARGET_MEMBER = (85, 0)
TARGET_MESSAGE_ID = 25
EXPECTED_SOURCE = "Ver. 1.5"
VARIANTS = {"ascii-control": "ASCII 2C", "russian": "\u041f\u0440\u0438\u0432\u0435\u0442!"}
BUILD_ROOT = (ROOT / "build/milestone-2c").resolve()


def contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def replace_message_archive(
    raw: bytes,
    member_key: tuple[int, int],
    message_id: int,
    expected_source: str,
    replacement: str,
) -> bytes:
    """Replace one plain message in a disposable GARC and verify its rebuild."""
    archive = GARC.parse(raw)
    members = {(member.entry_id, member.subfile_id): member.data for member in archive.members}
    if member_key not in members:
        raise MessageError(f"Target GARC member {member_key} is absent")
    member_data = members[member_key]
    was_compressed = member_data[:1] == b"\x11"
    text_data = decompress(member_data) if was_compressed else member_data
    text = TextFile.parse(text_data)
    if message_id >= len(text.lines):
        raise MessageError(f"Target message ID {message_id} is absent")
    target = text.lines[message_id]
    if target.display_text != expected_source or target.tokens:
        raise MessageError(f"Target source does not match expected plain string: {target.display_text!r}")

    rebuilt_text = text.rebuild({message_id: replacement})
    # Preserve the source member's storage mode. The selected language-screen
    # member is uncompressed, but this helper remains safe for compressed input.
    if was_compressed:
        raise MessageError("Compressed TextFile replacement is unsupported by this probe")
    rebuilt_archive_data = archive.rebuild({member_key: rebuilt_text})
    rebuilt_archive = GARC.parse(rebuilt_archive_data)
    rebuilt_members = {(member.entry_id, member.subfile_id): member.data for member in rebuilt_archive.members}
    if set(rebuilt_members) != set(members):
        raise GARCError("GARC member set changed during probe rebuild")
    for key, original in members.items():
        if key != member_key and rebuilt_members[key] != original:
            raise GARCError(f"Unrelated GARC member changed during rebuild: {key}")
    check = TextFile.parse(rebuilt_members[member_key])
    if check.lines[message_id].display_text != replacement:
        raise MessageError("Replacement did not survive archive rebuild")
    if check.lines[message_id].message_id != message_id:
        raise MessageError("Replacement message ID changed during archive rebuild")
    return rebuilt_archive_data


def build_one(game: str, variant: str, replacement: str) -> dict[str, object]:
    source = ROOT / "workspace" / game / "update-1.5" / Path(*RESOURCE.split("/"))
    if not contained(source, ROOT / "workspace") or not source.is_file():
        raise FileNotFoundError(f"Expected update 1.5 source archive is missing: {source}")
    raw = source.read_bytes()
    archive = GARC.parse(raw)
    members = {(member.entry_id, member.subfile_id): member.data for member in archive.members}
    if TARGET_MEMBER not in members:
        raise MessageError(f"Target GARC member {TARGET_MEMBER} is absent in {game}")
    source_text = members[TARGET_MEMBER]
    if source_text[:1] == b"\x11":
        source_text = decompress(source_text)
    source_file = TextFile.parse(source_text)
    if len(source_file.lines) <= TARGET_MESSAGE_ID:
        raise MessageError(f"Update-only target message {TARGET_MESSAGE_ID} is absent in {game}")
    if source_file.lines[TARGET_MESSAGE_ID].display_text != EXPECTED_SOURCE:
        raise MessageError(f"Unexpected visible version label in {game}")

    edited = replace_message_archive(raw, TARGET_MEMBER, TARGET_MESSAGE_ID, EXPECTED_SOURCE, replacement)
    out = BUILD_ROOT / variant / game / TITLE_IDS[game] / "romfs" / Path(*RESOURCE.split("/"))
    if not contained(out, BUILD_ROOT):
        raise RuntimeError(f"Refusing output outside build root: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(edited)
    return {
        "game": game,
        "variant": variant,
        "base_title_id": TITLE_IDS[game],
        "source_version": "update-1.5",
        "romfs_resource": RESOURCE,
        "target_member": list(TARGET_MEMBER),
        "target_message_id": TARGET_MESSAGE_ID,
        "expected_source": EXPECTED_SOURCE,
        "replacement": replacement,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": hashlib.sha256(edited).hexdigest(),
        "output_size": len(edited),
        "unchanged_other_members": len(members) - 1,
        "output": out.relative_to(ROOT).as_posix(),
        "install_performed": False,
    }


def main() -> int:
    results = [build_one(game, variant, replacement) for variant, replacement in VARIANTS.items() for game in TITLE_IDS]
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    (BUILD_ROOT / "language-screen-poc-report.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8", newline="\n"
    )
    print(json.dumps(results, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
