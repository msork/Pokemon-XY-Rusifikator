# Milestone 3A: Cyrillic Coverage and Layout Validation

Date: 2026-11-19. Generated test resources remain under ignored `build/`; source assets remain read-only. The current test installation is recorded below.

## Confirmed runtime baseline

The project owner confirmed that both Pokémon X and Pokémon Y display `Привет!` correctly on the initial language-selection screen in AzaharPlus 2126.2-A with update 1.5 active and the LayeredFS patch installed. This verifies those five Cyrillic letters plus `!` in both games.

## Static CFNT and CWDH findings

The base font archive `a/1/8/5` contains ten CFNT members. The corrected CMAP reader treats `codeEnd` as inclusive, consistent with libctru's codepoint lookup. The ten candidate game fonts still contain no mappings in U+0400-U+052F, including Ё (U+0401) and ё (U+0451). The glyph-test content has 69 distinct codepoints absent from the union of these CFNT maps: the 66 Russian alphabet characters, plus the numero sign (U+2116), ruble sign (U+20BD), and mathematical minus (U+2212). The other selected punctuation and test symbols map in at least one candidate font.

CFNT CWDH records store left bearing, glyph bitmap width, and character advance. The tooling now resolves CMAP codepoints to glyph indices and reads CWDH advances. For `Use the +Control Pad to select a language.` the two Latin fonts (members 0/0 and 1/0) sum to 536 font advance units; member 2/0 sums to 238. Those are font units, not measured AzaharPlus screen pixels. The precise font chosen for each language-screen element and the fallback font's advances are unknown. Russian lines have no complete game-CFNT advance because their glyphs are unmapped; their actual runtime width must be observed.

The three large CFNT members set alternate glyph indices 31, 31, and 27 for unmapped codepoints (with CWDH advances 17, 17, and 6). The small variants use alternate index 12 (advance 10). Under libctru-style lookup, these are the single alternate glyphs returned for unmapped characters; they cannot explain the user's observation of distinct, correctly rendered letters in `Привет!`. This supports the inference that AzaharPlus or another active game font path supplies additional Cyrillic glyphs. The exact fallback mechanism is not identified.

References: [libctru CMAP lookup and alternate-character behavior](https://github.com/devkitPro/libctru/blob/master/libctru/source/font.c#L558-L638) and [CWDH character advance use](https://github.com/devkitPro/libctru/blob/master/libctru/source/font.c#L642-L704). The project parser is independently implemented; these references document the inclusive CMAP lookup and advance semantics.

The successful `Привет!` runtime result despite the static CMAP gaps demonstrates that the runtime provides a fallback glyph path or another font source for those characters. It does not prove that every Russian glyph or special mark uses the same fallback or correct advances. Additional CFNT modification is not currently justified; first compare the new runtime matrix. If only particular glyphs fail, identify the exact active font and fallback behavior before planning a CFNT atlas/CMAP/CWDH edit.

## Test patch content and integrity

`python scripts/build_render_validation.py` builds two clearly named variants for each game from update 1.5 `a/0/7/4`, GARC member 85/0, message 1, the help panel visible on the language-selection screen:

| Variant | Purpose | Max explicit span | X/Y archive SHA-256 | Size |
|---|---|---:|---|---:|
| `glyph-coverage` | Upper/lower Russian alphabets, Ё/ё, punctuation, digits, math/special symbols, and mixed Latin/numbers | 39 codepoints | `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c` | 2,388,612 |
| `long-text` | Deliberately long Russian lines for horizontal wrapping and vertical overflow observation | 103 codepoints | `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61` | 2,389,076 |

The update archive source hash is `ed8a7a8e69e24ffb4d55c8ff6912457dbd4b4fb8825f30b1511563ab91ba0881`. X and Y source data are shared, so their files have identical hashes, but outputs are placed in separate title-specific directories:

- `build/milestone-3a/glyph-coverage/pokemon-x/0004000000055D00/romfs/a/0/7/4`
- `build/milestone-3a/glyph-coverage/pokemon-y/0004000000055E00/romfs/a/0/7/4`
- `build/milestone-3a/long-text/pokemon-x/0004000000055D00/romfs/a/0/7/4`
- `build/milestone-3a/long-text/pokemon-y/0004000000055E00/romfs/a/0/7/4`

Both variants preserve the source message's nine control-token events, including both `FF00` format controls, and preserve all 150 unrelated GARC members byte-for-byte. The output TextFile is reparsed; requested characters must survive serialization. Each message stays within the 16-bit TextFile record size. The builder writes only under `build/` and records per-span codepoint lengths, static unmapped glyphs, font advances where available, and archive hashes in `build/milestone-3a/render-validation-report.json`.

The glyph test's longest span is shorter than the source's longest explicit English span (39 versus 43 codepoints). Its visible pixel fit still depends on fallback metrics. The long-text variant's 103-codepoint span is intentionally 2.4 times the source's longest explicit line to reveal wrapping, clipping, and overflow behavior. Character count is only a coarse bound; it is not a pixel-width guarantee.

## Automated validation

The validation helpers report missing CMAP mappings and enforce configured BMP/UTF-16-unit and explicit-line codepoint limits. They deliberately distinguish static CFNT coverage from runtime fallback. The TextFile serializer continues to enforce the actual 16-bit message word limit and exact control/placeholder sequence preservation. CFNT advance calculations are reported only for fully mapped strings; missing fallback metrics are left unknown, not guessed.

`python -m unittest discover -s tests -v`: 17 tests passed, including inclusive CMAP bounds, CWDH advance and alternate-glyph lookup, full alphabet fixture coverage, unmapped-glyph reporting, text unit/line constraints, and replacement-message control preservation. `python scripts/build_render_validation.py` built four valid archives with the hashes above. No full translation extraction or bulk translation has begun.

## Glyph-coverage installation record

On 2026-11-19 the verified glyph-coverage files were installed only at:

- X: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4`
- Y: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4`

Both installed files are 2,388,612 bytes with SHA-256 `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c`. The previous Russian probes are backed up in ignored `build/milestone-3a/install-backups/20261119T185929Z/` as `pokemon-x-a074.before-glyph-test` and `pokemon-y-a074.before-glyph-test`; each backup hash is `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa`.

AzaharPlus was not launched during installation. The glyph target was the initial language-selection screen's large right-side help/information panel. The test replaces that panel's instructions; it does not replace the language buttons, `Play Pokémon X/Y in` header, or bottom-right version label.

To restore the previous Russian probes, close AzaharPlus and run this from the project root:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-3a\install-backups\20261119T185929Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-glyph-test') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-glyph-test') -Destination $yTarget -Force
```

This restores only the two test archive files. The original glyph test install and rollback sequence is retained in [the AzaharPlus Milestone 3A test plan](../testing/azaharplus.md).

## Owner-confirmed glyph results

The owner tested the glyph-coverage variant in both games and confirmed all 33 uppercase and all 33 lowercase Russian letters render, including Ё/ё. Record Pokémon X and Pokémon Y separately as **alphabet coverage passed**. The punctuation row crowds into the red `Цифры:` label in both screenshots. Symbol spacing and full layout remain unverified; this crowding does not mean the alphabet glyphs failed.

## Long-text installation record and rollback

After reporting the glyph results, the owner installed the long-text variant for the next test. At that stage, both targets were the same `a/0/7/4` files under the X/Y base Title ID folders listed above. Installed hash: `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61`; size: 2,389,076 bytes. The glyph-coverage files were backed up at `build/milestone-3a/install-backups/20261119T190332Z/` as `pokemon-x-a074.before-long-text` and `pokemon-y-a074.before-long-text`; each backup hash is `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c`. This installation was later superseded by the controlled 350-word test below.

AzaharPlus was not launched during this replacement. To restore the glyph-coverage variant, close AzaharPlus and run from the project root:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-3a\install-backups\20261119T190332Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-long-text') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-long-text') -Destination $yTarget -Force
```

The long-text variant targets message 1 in member 85/0 of update 1.5 `a/0/7/4`, visible in the same right-side information panel. The owner later reported that this variant made the panel blank in both games; see the investigation below. Do not begin bulk translation yet.

## Controlled record-350 installation and rollback

On 2026-11-19, the regenerated matrix's `record-350-words` variant was installed for the next owner runtime check. Before replacement, both installed files matched the expected long-text archive hash `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61`. The previous files were backed up under ignored `build/milestone-3a/install-backups/20261119T191931Z/`:

- `pokemon-x-a074.before-record-350-words`
- `pokemon-y-a074.before-record-350-words`

Each backup is 2,389,076 bytes and hashes to `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61`.

The installed X and Y files are each 2,388,724 bytes and hash to `c9e9914f04f57cd2e4f38d2ef5ab6eaa0983f7fe0a11d1dbc59dc9ece9c39e20`. They replace only these LayeredFS targets:

- X: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4`
- Y: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4`

The generated archives were checked against `matrix-report.json`; each target has GARC member 85/0, message ID 1, 350 UTF-16 words, and the exact nine raw control events from the update source. All 150 unrelated members are unchanged. AzaharPlus was not launched. To restore the prior long-text files, close AzaharPlus and run from the project root:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-3a\install-backups\20261119T191931Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-record-350-words') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-record-350-words') -Destination $yTarget -Force
```

After copying, verify both target hashes equal the long-text backup hash above. The project has not tested this variant at runtime; owner testing in X and Y is pending.

## Long-text blank-panel investigation

The project owner later tested the installed `long-text` variant in Pokémon X and Pokémon Y with update 1.5 active. In both games, the right-side information panel was completely blank while the language buttons and version label remained visible. This is an owner-reported runtime failure; the project did not launch AzaharPlus during this investigation. The previously confirmed `glyph-coverage` variant rendered Russian in both games.

The two generated archives were compared at `a/0/7/4`, GARC member 85/0, message 1:

| Property | Confirmed glyph variant | Blank-panel long variant |
|---|---:|---:|
| Archive SHA-256 | `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c` | `092ee4b69a085867f2547f780ff13af19826d70ab3a8b0963bd834fa01f8ab61` |
| Archive size | 2,388,612 bytes | 2,389,076 bytes |
| Target TextFile member size | 2,752 bytes | 3,216 bytes |
| Message 1 offset / reserved field | 468 / 4 | 468 / 4 |
| Message 1 record length | 295 words | 527 words |
| Visible replacement characters | 211 | 443 |
| Longest explicit span | 39 characters | 103 characters |
| Control events / encoded control words | 9 / 15 | 9 / 15 |

The message IDs, target offset, reserved field, and raw control-event sequence are identical. Both include the same newline events and the two `0x0010`/`0xFF00` variables with their original arguments. The changed ciphertext is expected because the message contents and word count changed; the message encryption starts from the same per-message key. The TextFile section size and subsequent message offsets are recomputed, and the target record grows by exactly 232 words (464 bytes). All 150 non-target GARC members remain byte-identical in each build. No encoding, compression, GARC membership, or control-format difference was found that explains the runtime result.

This comparison does **not** prove a text-length limit. The 527-word record is below the TextFile format's 16-bit per-record length capacity, but that storage bound does not establish the game's runtime renderer's buffer or layout limit. The public [pkNX TextFile implementation](https://github.com/kwsch/pkNX/blob/master/pkNX.Structures/Text/TextFile.cs#L57-L100) independently models per-line lengths as 16-bit values and the same Gen VI word encryption; it documents the container-level representation, not Pokémon X/Y's runtime UI limits. No public game-engine source or authoritative screen-specific maximum has been identified. The cause remains unresolved among total record size, line width, cumulative rendered lines, fallback-font metrics, or an additional engine-specific condition.

The comparison also prompted a serializer audit: `0x0000` appears as an argument inside the second `0xFF00` control sequence, as well as at the true end of the record. Current test generation preserves the raw control sequence and appends the source suffix, and round-trip checks prove the output remains parseable. The new matrix validator compares the complete raw control tuples (including arguments), rather than relying only on the human-readable token summary. This shared serialization behavior is present in both the known-working glyph artifact and the failed long artifact, so it does not by itself explain their different owner-reported result.

### Reproducible controlled matrix

Run `python scripts/build_text_length_matrix.py` to recreate ignored outputs under `build/milestone-3a/length-matrix/` and `matrix-report.json`. Every variant is built independently for X and Y from the same update 1.5 source, uses the same ten printable spans and exact raw control sequence as the known-working glyph variant, preserves the other 150 GARC members, reparses the rebuilt GARC/TextFile, and checks every other TextFile message's decoded/encrypted words, reserved field, and padding. X/Y outputs are separate, although the verified inputs currently produce identical hashes.

The total-record axis uses 295, 350, 400, 450, 480, 500, 512, and 527 decoded words. The first variant is the known glyph-coverage baseline and is expected to reproduce hash `f05cbd20...791c`. Later variants append only the same Russian `я` filler, distributed across existing nonempty spans; all line breaks and control positions remain fixed. The 512/527 pair tests around a plausible but unverified boundary. A second axis independently extends only the first span to 43, 58, 75, and 103 characters while all other spans and controls remain fixed. Each output has its own variant directory and hash in the generated report.

**Recommended first runtime test:** install and check `record-350-words` in X and Y separately, with update 1.5 enabled. It adds 55 Russian characters to the known-working 295-word baseline while retaining the identical formatting, and its longest span is 46 characters. If it renders, proceed in order through 400, 450, 480, 500, 512, and 527 words, changing only the test archive between runs. If a total-record variant fails, test the line-width axis separately to see whether one long explicit span reproduces the blank panel at a much smaller total record size. Record the panel state and visible lines per game. Do not launch or install any of these variants as part of this investigation, and do not begin bulk translation yet.

## Next work after runtime confirmation

Record glyph-by-glyph results separately for X and Y, and note visual substitution, line wrapping, clipping, missing glyphs, and overflow. If coverage and layout are acceptable, proceed to a translation data pipeline: stable per-member message IDs, shared X/Y records with contextual overrides, source hashes, exact control-token metadata, glossary/translation-memory checks, and untranslated/draft/reviewed/validated/tested states. Keep translation drafts in project-authored files and do not send copyrighted source strings to external services without explicit approval. Do not start bulk translation until the glyph and text-layout report is complete.
