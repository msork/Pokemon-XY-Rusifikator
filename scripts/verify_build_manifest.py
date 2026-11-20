#!/usr/bin/env python3
"""Verify candidate output hashes, build proofs, and repeat-build determinism."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def flatten(manifest: dict) -> dict[tuple[str, str], dict]:
    result = {}
    for game, record in manifest["games"].items():
        for resource in record["resources"]:
            key = (game, resource["resource"])
            if key in result:
                raise ValueError(f"Duplicate manifest resource: {key}")
            result[key] = resource
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--repeat-manifest", type=Path)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    rows = flatten(manifest)
    repeat = flatten(json.loads(args.repeat_manifest.read_text(encoding="utf-8"))) if args.repeat_manifest else None
    root = args.manifest.resolve().parent
    errors = []
    output = []
    for (game, resource), proof in sorted(rows.items()):
        path = (root / game / "romfs" / Path(*resource.split("/"))).resolve()
        if root not in path.parents:
            errors.append(f"output path escapes candidate root: {path}")
            continue
        if not path.is_file():
            errors.append(f"missing output archive: {path}")
            continue
        digest = file_sha256(path)
        if digest != proof["output_sha256"]:
            errors.append(f"output hash differs from manifest: {game}/{resource}")
        if int(proof["modified_members"]) + int(proof["unrelated_members_verified_unchanged"]) != int(proof["garc_members"]):
            errors.append(f"GARC member accounting mismatch: {game}/{resource}")
        if proof["source_version"] != ("update-1.5" if resource == "a/0/7/4" else "base"):
            errors.append(f"unexpected effective resource version: {game}/{resource}")
        if repeat is not None:
            if (game, resource) not in repeat or repeat[(game, resource)]["output_sha256"] != digest:
                errors.append(f"repeat build is not byte-deterministic: {game}/{resource}")
        output.append({"game": game, "resource": resource, "effective_version": proof["source_version"],
                       "output_sha256": digest, "messages_applied": proof["messages_applied"],
                       "members_unchanged": proof["unrelated_members_verified_unchanged"],
                       "untranslated_messages_unchanged": proof["untranslated_messages_verified_unchanged"]})
    if repeat is not None and set(repeat) != set(rows):
        errors.append("candidate and repeat manifest resource sets differ")
    report = {"result": "FAIL" if errors else "PASS", "resources_verified": len(output), "errors": errors, "resources": output}
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
