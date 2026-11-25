# Linux migration and offline texture pilot

## Local AzaharPlus profile

Solus 4.9 has an executable at `/home/maxim/azaharplus.AppImage`. The desktop launcher references that file. Existing emulator logs identify `cf90688 | AzaharPlus-cf9068844-dirty`, and the Qt configuration lists the game library at `/home/maxim/Games/3DS Games` and updates at `/home/maxim/Games/3DS Games/update`. Both X/Y game images and update packages were present there. The repository has all four extracted X/Y base and update 1.5 RomFS trees under `workspace/`.

| Item | Observed location |
| --- | --- |
| Qt configuration | `/home/maxim/.config/azaharplus-emu/qt-config.ini` |
| Emulator data | `/home/maxim/.local/share/azaharplus-emu` |
| LayeredFS root | `/home/maxim/.local/share/azaharplus-emu/load/mods` |
| SDMC and NAND trees | `sdmc/` and `nand/` under the emulator data directory |

The existing Linux logs show LayeredFS activity for title `000400000011C500` (Alpha Sapphire). The Linux mod directories for Pokémon X (`0004000000055D00`) and Pokémon Y (`0004000000055E00`) were both absent. X and Y Linux runtime validation are each pending. The read-only audit is in `build/offline-textures/linux-profile.json`.

Installers resolve the Linux XDG data location and require its existing `load/mods` directory. Set `AZAHARPLUS_DATA_DIR` to a verified absolute emulator data directory for a custom or portable profile. An unchanged Windows setup continues to use its AppData path. For a future verified installation, use a new `--record-root` under `build/` with the same installer and record root for rollback. The 3K installer accepts `--prior-record` for the verified 3G text installation. The 3L and 3M image installers accept `--text-record` for the corresponding verified 3K text installation. Historical Windows rollback manifests retain their original absolute paths and remain bound to that deployment. The offline artwork command only generates review files.

## Local tooling

Use Python 3.14 on the tested host. The Python requirements are pinned in `requirements-offline-artwork.txt`. Obtain Tesseract and its English traineddata from a trusted distribution or the official Tesseract project. Use a locally installed Cyrillic TrueType font. The pilot used DejaVu Serif Bold, discovered with `fc-match -f '%{file}\\n' 'DejaVu Serif:style=Bold'`. Create a virtual environment and provision the pinned wheels before the offline run. [Tesseract English data](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0) · [CTranslate2](https://github.com/OpenNMT/CTranslate2)

Obtain the English-to-Russian Argos 1.9 package from the official catalog. Extract its `metadata.json`, `sentencepiece.model`, and `model/` into a local directory. The pipeline runs CTranslate2 with SentencePiece directly using these local files. The pilot Argos archive SHA-256 was `591d743ae103752b88ffc38785c50421320f4eff93c8967e0d3d2e14d4e27811`. The English traineddata SHA-256 was `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2`. [Argos model catalog](https://github.com/argosopentech/argospm-index/blob/main/index.json) · [Argos package format](https://github.com/argosopentech/argos-translate/blob/master/argostranslate/package.py)

The pilot used official Solus Tesseract 5.5.4 and its local shared libraries extracted to the ignored build directory. For this checkout, the exact command is:

```sh
LD_LIBRARY_PATH="$PWD/build/offline-deps/ocr/usr/lib64" \
  build/offline-deps/venv/bin/python scripts/localize_textures.py --pilot \
  --tesseract build/offline-deps/ocr/usr/bin/tesseract \
  --tessdata build/offline-deps/tessdata \
  --model build/offline-deps/translate-en_ru-1_9 \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf
```

On a system with Tesseract on PATH, use the virtual environment's Python with the local traineddata, model, and font paths. The scanner and localizer can run independently. Generate a fresh inventory under `build/offline-textures/inventory/` with `python3 scripts/scan_milestone3n_artwork.py`. Pass its manifest to the localizer with `--manifest`. The fixed pilot IDs match both the original 3N manifest and the verified Linux rescan. The tool accepts repeated `--asset` IDs for smaller review sets and `--batch` for the manifest queue after pilot review.

Each run writes a content-addressed report under `build/offline-textures/runs/`. Completed texture entries are published to the SHA-256 cache as whole directories and reused on restart with matching PNG, model, glossary, font, executable, language data, and pipeline inputs. The pipeline verifies that cache preview hashes still match on reuse. A source texture appearing in multiple places shares one result and retains all occurrence records. The three edits under the original 3N `done/` and the 3I/3M exclusions are protected across duplicates. For additional manual edit directories, pass `--protect` with the source hash retained in the scanner-export filename.

Only single-line, high-confidence OCR with verifiable source bytes and supported pixel layouts is considered for automated rendering. A high Tesseract score does not establish the texture's language or contextual meaning. The compositor handles flat colors, simple outlines, single-color alpha sprites, and near-grayscale palettes on uniformly colored artwork. It leaves complex artwork for manual work. Glyph coverage can change only within the inferred lettering region for transparent text sprites. The 3I BCLIM encoder must reproduce the proposal pixel-for-pixel. Held items get an unchanged after-preview and a reason. Rendering produces local PNGs and hashes for review.

## Ten-texture pilot

The sample crosses keyboard or communication UI, the start screen, HUD, status, battle results, a score banner, Pokédex, and an end card. Each texture has recorded X/Y occurrences and the pilot ran OCR once per source hash.

| Texture | Result |
| --- | --- |
| T000264 | No OCR line on the communication button |
| T002718 | Start prompt proposal from the glossary |
| T003077 | No OCR line on the HUD bar |
| T003101 | No OCR line on the status icon |
| T003394 | Model translated DRAW. Nonuniform artwork requires manual masking |
| T003397 | Model translated WIN. Nonuniform artwork requires manual masking |
| T003423 | Score banner OCR was unreliable |
| T003430 | No high-confidence OCR on the cleared badge |
| T003475 | Pokédex wordmark matched conflicting normalized glossary entries |
| T003563 | End-card OCR detected a word with ambiguous language |

The start-prompt preview retained all 800 × 480 pixels' alpha and used only original palette colors. Its 3,576 changed pixels are bounded by x=294–677 and y=407–420, inclusive. The preview remains a draft because the generic serif font differs from the original display lettering. No batch processing, candidate installation, or emulator launch took place.

## Unsupported formats

The scanner reports every rejected BCLIM decode and recognizes BCH headers at the start of inspected files and decompressed GARC members. It records dataset, archive, member and SHA-256. A BCH header is evidence of an unsupported container. Its embedded images and formats require a parser. The Linux scan visited 1,600 files and reproduced all 8,608 decoded occurrences and 3,575 unique BCLIM hashes from 3N. It found 4,386 BCH headers, with 2,193 in each base game and none in the scanned update containers. The 4,432 BCLIM failures comprised formats 0 (82), 2 (26), 3 (248), 5 (398), 6 (62), 10 (476), 11 (3,046), 12 (70), and 13 (6), plus 18 unsupported padded layouts in formats 8 and 9. The inventory at `build/offline-textures/inventory/unsupported-formats.json` groups decode failures by format and preserves individual locations. Oversized sources and unrecognized containers remain visible in the scan report.

## Regression and publication

The regression suite uses recorded Windows installation metadata and verifies the corresponding local candidate bytes. Installer mutation tests use temporary profiles. Record path lookups for a live installation still require the matching active profile.

The command `python3 -m unittest discover -s tests -v` passed 101 tests on Solus 4.9. A separate protection check skipped all three 3N manual edits and a known 3I translation. The repeated pilot reused its cache and reproduced the same report. The existing branch had two local test-file commits and the SSH remote had two different test-file commits. Both pairs have the same net tree. Publication requires reconciling the divergent history under the repository's remote-history rule.
