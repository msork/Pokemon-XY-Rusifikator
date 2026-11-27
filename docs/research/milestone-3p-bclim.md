# Milestone 3P BCLIM texture support

## Four-dataset rescan

The Linux scan visited 1,600 files and SHA-256 checked all 568 GARC archives. Identical archives shared inspection results by content hash. The before counts use the recorded 3O Linux inventory, where the decoder rejected 4,414 occurrences for format support and 18 for padded layout support. The new scanner distinguishes unsupported formats and layouts from malformed data and decode errors.

| Dataset | 3O decoded | 3O unsupported | 3O failed | 3P decoded | 3P unsupported | 3P failed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pokémon X base | 4,291 | 2,205 | 0 | 6,496 | 0 | 0 |
| Pokémon X update 1.5 | 13 | 11 | 0 | 24 | 0 | 0 |
| Pokémon Y base | 4,291 | 2,205 | 0 | 6,496 | 0 | 0 |
| Pokémon Y update 1.5 | 13 | 11 | 0 | 24 | 0 | 0 |
| **Total** | **8,608** | **4,432** | **0** | **13,040** | **0** | **0** |

Every prior decode rejection matches a newly decoded occurrence by game, version, archive, nested member, filename and raw SHA-256. Unique PNGs increased from 3,575 to 5,057. The other 9,326 scan diagnostics include 4,386 unsupported BCH containers and cases such as unaccepted texture-pack indices and LZ11 errors. The BCLIM totals cover recognized entries in the scan scope.

| ID | Format | Recovered occurrences |
| --- | --- | ---: |
| 0 | L8 | 82 |
| 2 | LA4 | 26 |
| 3 | LA8 | 248 |
| 5 | RGB565 | 398 |
| 6 | RGB8 | 62 |
| 8 | RGBA4444, small padded layout | 2 |
| 9 | RGBA8888, small padded layouts | 16 |
| 10 | ETC1 | 476 |
| 11 | ETC1A4 | 3,046 |
| 12 | L4 | 70 |
| 13 | A4 | 6 |

Format 7 also needed a correction. Of the textures previously exported as direct RGB5A1, 1,763 unique source hashes use the XY indexed RGB5A1 variant. The payload begins with palette type 2 and a color count, followed by the RGB5A1 palette and tiled indices. Textures with up to 16 colors store the first index in the high nibble. Larger palettes use byte indices. Eight unique 40 × 30 textures omit part of the clipped index plane. All eight contain every index needed for their visible rectangle. The corrected previews use the stored palette and retain its alpha.

## Layout and editing evidence

- The BCLIM mapping uses IDs 0 through 13. The little-endian footer records visible dimensions and payload size. Direct texels and palette indices use row-major 8 × 8 tiles with Morton ordering inside each tile. Direct formats take a minimum 8 × 8 power-of-two storage rectangle. Observed compact RGBA8888 rectangles can also align each dimension to eight. The decoder accepts a layout only when the payload length matches. [png2bclim reader and writer](https://github.com/kwsch/png2bclim/blob/master/png2bclim/BCLIM.cs) · [pk3DS GPLv3 license](https://github.com/kwsch/pk3DS/blob/master/LICENSE.md)
- ETC1 uses one RGB word per 4 × 4 block. ETC1A4 places the little-endian alpha word before it, with column-major alpha nibbles. Four blocks form each 8 × 8 tile. The visible rectangle is cropped from storage. Payload sizes confirm 1,205 unique textures using the minimum 16-pixel power-of-two rule, including a 2 × 21 ETC1 texture stored at 16 × 32, and another 25 ETC1A4 hashes that require an 8-pixel minimum. [Azahar PICA texture layout](https://github.com/azahar-emu/azahar/blob/master/src/video_core/texture/texture_decode.cpp)
- RGB channel order, bit replication, implicit alpha, low-nibble-first L4/A4 and the two ETC1 block modes were checked against licensed references. Alpha-only samples use PICA's zero-RGB convention. A8 and HILO8 have synthetic coverage because neither format appeared in the scan. The project codec is an original Python implementation with no imported reference source. [Azahar channel packing](https://github.com/azahar-emu/azahar/blob/master/src/common/color.h) · [Khronos ETC1 specification](https://registry.khronos.org/OpenGL/extensions/OES/OES_compressed_ETC1_RGB8_texture.txt) · [Apache-licensed Android ETC1 reference](https://android.googlesource.com/platform/frameworks/native/+/refs/heads/main/opengl/libs/ETC1/etc1.cpp)
- Template-based edits return the original bytes for identical RGBA data, including ETC blocks, duplicate palette indices, clipped texels and the footer. Changed indexed pixels must use an existing palette entry. ETC RGB edits can change selectors within the original block's color codebook, and ETC1A4 can also store exact 4-bit alpha changes. The encoder rejects pixels that require new ETC bases or modifier tables. New encoder paths require an exact RGBA round trip. The existing RGBA4444 API retains its documented quantization behavior, and the artwork proposal workflow still checks the result pixel-for-pixel.

## Offline OCR and pilot disposition

The OCR inventory uses the existing Tesseract preprocessing and confidence gate, deduplicated by raw SHA-256. It includes all 1,482 newly decoded PNGs and 1,763 corrected format 7 previews. Tesseract returned 99 single high-confidence Latin lines, 475 results requiring OCR review, and 2,671 images with no extracted line. All 99 high-confidence results came from the newly decoded cohort. A high-confidence Latin line is evidence for review. Language and terminology still require context. The report is `build/offline-textures/runs/905c7a074809779e0e1440fa0201abcd56645cc0f00ef9850ee0d113fbc8f25b.json`. No translation model was used for the inventory.

The pilot selects its original ten textures by source fingerprint across scanner inventories. The same nine items remain held, with byte-identical before and after PNGs. The start prompt remains the only draft proposal. IDs below refer to the original 3O inventory.

| Rejection | Held textures | Evidence |
| --- | --- | --- |
| No OCR line | T000264, T003077, T003101, T003430 | Communication button, HUD bar, status icon and cleared badge produced no line |
| OCR confidence and line structure | T003423 | The score banner produced several fragments and the only fragment above threshold was one letter |
| Nonuniform artwork at the text boundary | T003394, T003397 | DRAW and WIN passed OCR and the lettering touches artwork |
| Conflicting glossary entries | T003475 | POKEDEX matched more than one normalized glossary entry |
| Language ambiguity | T003563 | FIN on the end card needs language identification |

The scan retained all 48 existing translation exclusions. The three original manually edited textures remain protected by source hash, and the previous discovery and pilot outputs remain available locally.

## Reproduction and runtime

Use the dependencies and local Tesseract paths in the [3O Linux setup](../testing/linux-offline-artwork.md). The OCR-only mode uses Pillow, Tesseract and the English traineddata. Its baseline is the separate 3O manifest and its referenced PNGs.

```sh
build/offline-deps/venv/bin/python scripts/scan_milestone3n_artwork.py \
  --output build/milestone-3p/inventory
LD_LIBRARY_PATH="$PWD/build/offline-deps/ocr/usr/lib64" \
  build/offline-deps/venv/bin/python scripts/localize_textures.py \
  --manifest build/milestone-3p/inventory/texture-manifest.json \
  --ocr-new-since build/offline-textures/inventory/texture-manifest.json \
  --tesseract build/offline-deps/ocr/usr/bin/tesseract \
  --tessdata build/offline-deps/tessdata --jobs 8
python3 -m unittest discover -s tests -v
```

Local evidence is under `build/milestone-3p/`, including the per-occurrence baseline reconciliation and the new JSON and CSV manifests. The regression suite passed 108 tests, including synthetic channel, tiling, alpha, ETC, palette, padding and malformed-input fixtures and the existing 24 byte-exact artwork round trips. An additional corpus check encoded each exported ETC PNG against its source template and recovered the original bytes for all 170 ETC1 and 1,060 ETC1A4 hashes.

On Solus 4.9 the installed AppImage is `/home/maxim/azaharplus.AppImage` and its existing log identifies `cf90688 | AzaharPlus-cf9068844-dirty`. The data directory is `/home/maxim/.local/share/azaharplus-emu` and the observed LayeredFS root is `load/mods` below it. The Pokémon X title directory `0004000000055D00` and Pokémon Y title directory `0004000000055E00` are both absent. Linux runtime validation remains pending independently for X and Y. Historical Windows deployment and rollback records remain in `docs/testing/`.

The two divergent remote commits, `cf4bae8` and `cd36738`, added and removed the empty `test` file. Their net tree matches the common ancestor. Merge `10d02bd` retained both histories with the exact 3O tree. All 101 baseline tests passed before that merge was pushed to git.gay.
