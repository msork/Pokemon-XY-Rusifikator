#!/usr/bin/env python3
"""Build disposable X/Y Russian TextFile test patches under ignored build/."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.extraction.garc import GARC  # noqa: E402
from src.extraction.messages import MessageError, TextFile  # noqa: E402

TITLE_IDS = {"pokemon-x": "0004000000055D00", "pokemon-y": "0004000000055E00"}
RESOURCE = "a/0/7/4"
TARGET_MEMBER = (35, 0)
TARGET_MESSAGE_ID = 22
RUSSIAN_POC = "\u041f\u0440\u0438\u0432\u0435\u0442!"
EXPECTED_UPDATE_MESSAGE = "Ver. 1.5"
BUILD_ROOT = (ROOT / "build/milestone-2b").resolve()


def contained(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def build_one(game: str) -> dict[str, object]:
    source = ROOT / "workspace" / game / "update-1.5" / RESOURCE
    if not contained(source, ROOT / "workspace") or not source.is_file():
        raise FileNotFoundError(f"Expected update 1.5 source archive is missing: {source}")
    raw = source.read_bytes()
    archive = GARC.parse(raw)
    members = {(member.entry_id, member.subfile_id): member.data for member in archive.members}
    if TARGET_MEMBER not in members:
        raise MessageError(f"Target GARC member {TARGET_MEMBER} is absent in {game}")
    text_file = TextFile.parse(members[TARGET_MEMBER])
    if len(text_file.lines) <= TARGET_MESSAGE_ID:
        raise MessageError(f"Target message ID {TARGET_MESSAGE_ID} is absent in {game}")
    target = text_file.lines[TARGET_MESSAGE_ID]
    if target.display_text != EXPECTED_UPDATE_MESSAGE or target.tokens:
        raise MessageError(f"Update-only version marker does not match expected plain message in {game}")

    edited_text = text_file.rebuild({TARGET_MESSAGE_ID: RUSSIAN_POC})
    edited = GARC.parse(raw).rebuild({TARGET_MEMBER: edited_text})
    rebuilt_archive = GARC.parse(edited)
    rebuilt_members = {(member.entry_id, member.subfile_id): member.data for member in rebuilt_archive.members}
    for key, original in members.items():
        if key != TARGET_MEMBER and rebuilt_members[key] != original:
            raise MessageError(f"Unrelated GARC member changed during POC repack: {game}/{key}")
    rebuilt_text = TextFile.parse(rebuilt_members[TARGET_MEMBER])
    if rebuilt_text.lines[TARGET_MESSAGE_ID].display_text != RUSSIAN_POC:
        raise MessageError(f"Russian POC did not survive GARC rebuild for {game}")

    output = BUILD_ROOT / game / TITLE_IDS[game] / "romfs" / Path(*RESOURCE.split("/"))
    if not contained(output, BUILD_ROOT):
        raise RuntimeError(f"Refusing output outside build root: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(edited)
    return {
        "game": game,
        "base_title_id": TITLE_IDS[game],
        "romfs_resource": RESOURCE,
        "source_version": "update-1.5",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "output_sha256": hashlib.sha256(edited).hexdigest(),
        "output_size": len(edited),
        "target_entry_id": TARGET_MEMBER[0],
        "target_subfile_id": TARGET_MEMBER[1],
        "target_message_id": TARGET_MESSAGE_ID,
        "translation": RUSSIAN_POC,
        "unchanged_other_members": len(members) - 1,
        "output": output.relative_to(ROOT).as_posix(),
        "install_performed": False,
    }


def main() -> int:
    results = [build_one(game) for game in TITLE_IDS]
    BUILD_ROOT.mkdir(parents=True, exist_ok=True)
    report = BUILD_ROOT / "poc-report.json"
    report.write_text(json.dumps(results, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8", newline="\n")
    print(json.dumps(results, ensure_ascii=True, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
