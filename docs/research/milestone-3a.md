# Milestone 3A: Cyrillic Coverage and Layout Validation

Date: 2026-11-19. Generated test resources remain under ignored `build/`; source assets remain read-only. The current test installation is recorded below.

## Confirmed runtime baseline

The project owner confirmed that both Pokémon X and Pokémon Y display `Привет!` correctly on the initial language-selection screen in AzaharPlus 2126.2-A with update 1.5 active and the LayeredFS patch installed. This verifies those five Cyrillic letters plus `!` in both games. It does not establish complete Cyrillic coverage, Ё/ё support, special-character support, or line layout. The glyph-coverage variant has since been installed, but has not been launched.

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

## Glyph-coverage installation record and rollback

On 2026-11-19 the verified glyph-coverage files were installed only at:

- X: `%APPDATA%\AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4`
- Y: `%APPDATA%\AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4`

Both installed files are 2,388,612 bytes with SHA-256 `f05cbd20ebdc2beb1d438d6b82a6ff61ccdd183ee41b12b208ced7be0d1e791c`. The previous Russian probes are backed up in ignored `build/milestone-3a/install-backups/20261119T185929Z/` as `pokemon-x-a074.before-glyph-test` and `pokemon-y-a074.before-glyph-test`; each backup hash is `d2fbd6bebd5b7764b2e4ec2077d7f3ed7cbc343dc60bf3b1b73933db24c572fa`.

AzaharPlus was not launched during installation. Inspect the initial language-selection screen's large help/information panel (the panel on the right in the supplied screenshot). The glyph test replaces that panel's instructions; it does not replace the language buttons, `Play Pokémon X/Y in` header, or bottom-right version label. Test X and Y separately with update 1.5 enabled. The long-text variant is not installed.

To restore the previous Russian probes, close AzaharPlus and run this from the project root:

```powershell
$backup = Join-Path (Get-Location) 'build\milestone-3a\install-backups\20261119T185929Z'
$xTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055D00\romfs\a\0\7\4'
$yTarget = Join-Path $env:APPDATA 'AzaharPlus\load\mods\0004000000055E00\romfs\a\0\7\4'
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-x-a074.before-glyph-test') -Destination $xTarget -Force
Copy-Item -LiteralPath (Join-Path $backup 'pokemon-y-a074.before-glyph-test') -Destination $yTarget -Force
```

This restores only the two test archive files. The exact test sequence, character checklist, and long-text variant instructions are in [the AzaharPlus Milestone 3A test plan](../testing/azaharplus.md). Never install both variants at once.

## Next work after runtime confirmation

Record glyph-by-glyph results separately for X and Y, and note visual substitution, line wrapping, clipping, missing glyphs, and overflow. If coverage and layout are acceptable, proceed to a translation data pipeline: stable per-member message IDs, shared X/Y records with contextual overrides, source hashes, exact control-token metadata, glossary/translation-memory checks, and untranslated/draft/reviewed/validated/tested states. Keep translation drafts in project-authored files and do not send copyrighted source strings to external services without explicit approval. Do not start bulk translation until the glyph and text-layout report is complete.
