# Milestone 2B: TextFile Serialization and Russian Rendering Proof

Date: 2026-11-18. Source assets remain read-only under `workspace/`. Generated message samples and test patches are under ignored `build/`.

## Serializer and round-trip results

The TextFile writer retains the 0x10-byte header, section length field, line-table reserved values, message ID order, each line's original padding bytes, terminator suffix, and control-code words. It re-encodes decoded 16-bit words with the per-line rolling key and preserves the per-message initial-key progression. Variable-length edits update offsets and lengths while leaving every unrelated message's data and formatting intact.

`python scripts/verify_text_roundtrips.py` reads the source GARCs without extracting them in place. It byte-round-trips all 1,452 TextFile members across X/Y base and update 1.5: 125,638 source message records total. Per-game effective update coverage is 35,214 messages (27,607 from update `a/0/7/4` plus 7,607 from base `a/0/8/2`).

Safe replacements validate message IDs, BMP encoding, absence of accidental empty strings, 16-bit table length limits, and exact control-code/placeholder token sequence. Unsupported controls in plain text, non-BMP characters, invalid IDs, and changed placeholders/control codes are rejected. Sequence-of-word replacements allow intentional control-bearing edits only when the complete token signature remains identical.

Automated tests cover synthetic TextFile and GARC no-change round trips, edited TextFile serialization, edited GARC repacking, preservation of message IDs, control-code/placeholder checks, invalid encodings, and LZ11 literal decoding. No test modifies a source asset.

## Russian proof patch

`python scripts/build_russian_poc.py` writes separate X/Y LayeredFS directory trees under `build/milestone-2b/`. It uses the update 1.5 `a/0/7/4` archive, GARC member 35/0, message ID 22, and replaces its `Ver. 1.5` string with a Russian greeting whose code points are U+041F U+0440 U+0438 U+0432 U+0435 U+0442 U+0021. Its runtime use has not been identified.

Both X and Y patch files have SHA-256 `ebfa2db696d0e7b2c5bcd2b6fe20527ff395e51590b605b4250f30e8ce535cae`. Each output preserves the other 150 GARC members byte-for-byte and the archive remains the original 2,388,484-byte length. The source archive is never overwritten.

Correction from Milestone 2C: the `Ver. 1.5` message replaced here at member 35/0, ID 22 is not the label shown on the initial language-selection screen. That visible label is update-only message 25 in member 85/0 of the same archive. Therefore, the unchanged initial screen after installing this Milestone 2B patch was inconclusive about LayeredFS. See [Milestone 2C findings](milestone-2c.md) for the exact screen resource and controlled test plan.

## Font and fallback investigation

All 10 candidate CFNTs lack mappings for U+0400 through U+052F, including U+0401 and U+0451. Their CMAP tables map Latin, kana, Hangul, full-width forms, and punctuation. Subsequent user-confirmed AzaharPlus runtime testing showed `Привет!` correctly in both games despite those static map gaps. The display result demonstrates that a runtime fallback or another glyph source supplies at least the glyphs used by that test; its exact source and complete coverage are still unknown. Emulator UI support or bundled FreeType/FriBidi DLLs alone would not establish in-game support, but this specific X/Y runtime result does establish the seven tested characters for this build.

No font modification has been attempted. A CFNT change should be considered only if the full character matrix exposes missing glyphs or bad widths. Font atlas sizing, texture alignment, and actual X/Y font selection remain open.

## Update and LayeredFS evidence

AzaharPlus 2126.2-A states it is the same as Azahar 2126.2 except for its listed fork-specific changes. The matching upstream 2126.2 source normalizes update Title IDs by removing the update mask before forming the LayeredFS mod ID, and wraps the active NCCH RomFS with a LayeredFS root at `load/mods/<base-title-id>/romfs`. This supports the expected X/Y folders `0004000000055D00` and `0004000000055E00`, not the update IDs. Source references: [NCCHContainer update-ID normalization](https://github.com/azahar-emu/azahar/blob/2126.2/src/core/file_sys/ncch_container.cpp#L1736-L1746), [RomFS LayeredFS construction](https://github.com/azahar-emu/azahar/blob/2126.2/src/core/file_sys/ncch_container.cpp#L2653-L2724), and the [AzaharPlus 2126.2-A release](https://github.com/AzaharPlus/AzaharPlus/releases/tag/AZAHAR_PLUS_2126_2_A).

Local AzaharPlus logs show LayeredFS replacements for other titles, but the local profile has no X/Y boot evidence. The X/Y v1.5 data tree supplies `a/0/7/4` with 151 members and an update-only line 22; update 1.5 has 27,607 lines versus 27,605 in base. The test patch uses the base game Title ID and update archive's unique version marker to probe the active title path. The loader source establishes the mod root and overlay mechanism; only a logged X/Y run can confirm the local update is enabled and the test resource is being selected. That runtime confirmation remains pending.

## Runtime test status and next steps

No patch was installed, no game was launched, and no save data was accessed. Follow the exact copy, launch, log-capture, and removal instructions in [the AzaharPlus test plan](../testing/azaharplus.md). Test each game separately with update 1.5 enabled. Capture the untouched title screen first, then the POC screen and LayeredFS log. Report whether the Russian string renders correctly, as a fallback glyph, or as an empty/default character. Do not begin bulk translation until the Cyrillic result is known.
