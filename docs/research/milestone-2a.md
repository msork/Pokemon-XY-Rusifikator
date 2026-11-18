# Milestone 2A: GARC, TextFile, CFNT Findings

Date: 2026-11-18. All inspections read from `workspace/`; extracted members and reports are generated under ignored `build/milestone-2a/`.

## Candidate archive findings

| Resource | Dataset availability | X base/update size | Y base/update size | Parsed structure |
|---|---|---:|---:|---|
| `a/0/7/4` (English text) | Base and update 1.5 | 2,388,420 / 2,388,484 | 2,388,420 / 2,388,484 | GARC v4; 151 entries/members; all 151 members are Gen VI TextFile |
| `a/0/8/2` (English script text) | Base only | 1,306,204 / absent | 1,306,204 / absent | GARC v4; 424 entries/members; all members are Gen VI TextFile |
| `a/1/8/5` (fonts) | Base only | 3,301,724 / absent | 3,301,724 / absent | GARC v4; 4 entries, 10 present members; each member is CFNT |

Archive SHA-256 fingerprints:

| Resource/version | SHA-256 |
|---|---|
| `a/0/7/4` base (X and Y) | `18c12ccb9baf48c9a33e46b77b372c3124a64ad84dae0c03ee50229650a26760` |
| `a/0/7/4` update 1.5 (X and Y) | `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881` |
| `a/0/8/2` base (X and Y) | `16b9a70f11fd6ac5779a577a16e457b793028be612d279dab28d1abf59349999` |
| `a/1/8/5` base (X and Y) | `b0d0b65a44cc5a0217f857cb339dd49021a1a8b5c231ca43ada1e283ba96fba6` |

No candidate member was LZ11-compressed. GARC header evidence is signature `CRAG`, BOM `FE FF`, version field `0x0400`, and four chunks. The three tested archives parsed strictly, and no-change rebuilds compared byte-for-byte equal to all source archives. Raw extracted members are not committed.

The English-text member messages use little-endian 16-bit code units encrypted by the Gen VI rolling XOR key. The parser preserves encrypted and decoded words, per-member ID, source-member hash, whole TextFile hash, decoded display text, and control tokens. TextFile headers have one section, a zero initial key, section offset `0x10`, and a length field describing bytes after that offset. All candidate TextFile members parsed without malformed text-like members. Parsed message-line counts:

| Dataset | `a/0/7/4` | `a/0/8/2` |
|---|---:|---:|
| X base | 27,605 | 7,607 |
| X update 1.5 | 27,607 | not present |
| Y base | 27,605 | 7,607 |
| Y update 1.5 | 27,607 | not present |

The parser retains line indexes even for empty messages. The inspected English text archive includes newline, variable/control, clear/return, remapped-character, and private-use tokens. A small English sample is generated locally in `build/milestone-2a/<game>/<version>/a_0_7_4/english-sample.jsonl`; it is deliberately excluded from Git.

## X/Y and update differences

Base `a/0/7/4` X/Y archives are byte-identical by archive hash. Update `a/0/7/4` X/Y archives are also byte-identical by archive hash. Base `a/0/8/2` and `a/1/8/5` are byte-identical between X and Y. The update `a/0/7/4` archive is 64 bytes larger than base. For each game, member-level comparison shows four of 151 base/update text members differ; the remaining entries match. Exact base/update effective-resource selection at runtime remains unverified.

The updates contain neither `a/0/8/2` nor `a/1/8/5`, so these candidates resolve to base files by path availability if the emulator merges update RomFS with base RomFS in the expected way. This is a static inference only, pending an X/Y test on the target emulator.

## Font evidence

The ten font members in X and Y are identical by SHA-256. They have `CFNT` signature and little-endian byte-order marker. The map tables structurally decode to Latin, kana, Hangul, full-width forms, and punctuation ranges. Across all ten members, no mapped codepoint falls in U+0400–U+052F; U+0401 Ё and U+0451 ё are both absent. This establishes that the existing candidate game fonts do not provide Cyrillic mappings. It does not establish whether AzaharPlus can supply missing glyphs through a system-font fallback or other rendering feature. No font was modified, and no Cyrillic runtime rendering test has been performed.

Mapped-codepoint counts by font member are 3,302, 2,846, 2,830, and 31 for each of the seven small variants. The seven variants have some differences in their codepoint sets; all are missing Cyrillic.

## Tooling research and licensing

- `pk3DS` contains Gen VI GARC and TextFile implementations and is GPL-3.0. Its source was used as a format reference; no pk3DS source code was copied into this repository. The local parser has been checked against actual X/Y data and round-trip byte equality. Sources: https://github.com/kwsch/pk3DS and its GPL-3.0 license.
- `3DSkit` includes BFFNT/CFNT character-map parsing code. It is GPL-3.0 and has broader dependencies for image extraction; this project uses only the documented block-level structure as a reference and does not import its code. Source: https://github.com/Tyulis/3DSkit.
- `kwsch/GARC-Unpack` and `kwsch/xytext` were not selected because their archived repositories do not provide a clear license for reuse and this milestone required strict, evidence-backed coverage.
- Kuriimu-family support was not selected because exact X/Y TextFile read/write behavior for these resources has not been demonstrated by a specific plugin/source implementation in this investigation.

## AzaharPlus target and local evidence

Primary target is AzaharPlus 2126.2-A at `C:\Users\maxim\Games\azaharplus-2126.2-A-windows`. Local user data is `C:\Users\maxim\AppData\Roaming\AzaharPlus`, containing `config`, `load`, `nand`, `sdmc`, `log`, `states`, and other profile directories. Existing title mod folders and prior log replacement entries show per-title LayeredFS RomFS replacements are used by this local fork for other installed games. Expected X/Y mod roots are `load/mods/0004000000055D00/romfs/` and `load/mods/0004000000055E00/romfs/`.

The local profile has no X/Y installed title/update evidence and its latest log contains no X/Y boot. Therefore the following remain unverified: X/Y-specific LayeredFS replacement, update 1.5 versus base precedence in the running fork, and the claimed Cyrillic/system-font behavior in these games. No runtime test was performed.

The official AzaharPlus 2126.2-A release notes describe compatibility with game files and list its fork-specific changes, but do not claim Cyrillic rendering or a Cyrillic fallback feature. Therefore the reported emulator capability is not verified by project documentation and requires the X/Y runtime test described below. Source: https://github.com/AzaharPlus/AzaharPlus/releases/tag/AZAHAR_PLUS_2126_2_A.

References: AzaharPlus project and release information: https://github.com/AzaharPlus/AzaharPlus. The upstream Azahar project documents title-ID mod folders and LayeredFS; fork inheritance is not treated as proof of X/Y behavior: https://github.com/azahar-emu/azahar and https://citra.azahar-emu.org/help/feature/game-modding/.

## Next milestone

Add editable JSONL/CSV export and a structure-preserving TextFile writer. Verify message archive extraction/rebuild on every candidate and add a replacement fixture that checks encrypted-line encoding, table bounds, and control tokens. With the user launching X and Y under AzaharPlus 2126.2-A with update 1.5 installed, record a minimal harmless text-rendering test and LayeredFS log evidence before starting bulk translation. If system fallback cannot render Ё/ё and Cyrillic, research a compatible CFNT extension path before translation.
