# Milestone 3R offline artwork localization

## Workflow

The existing `scripts/localize_textures.py` command runs enhanced review for an explicit asset selection or the annotated 30-texture benchmark. The legacy pilot still uses its original gates. Its ten reasons, OCR records and before/after PNG fingerprints matched the recorded 3O pilot in a regression rerun.

- Tesseract combines black and white alpha composites, contrast and color-isolated ink passes, alpha silhouettes, upscaling, and right-angle rotations. It maps all boxes back to native image coordinates and groups agreeing readings by region. Color isolation can retain stacked lines as a group. The language gate uses glossary and UI vocabulary evidence, competing OCR hypotheses, and locale or foreign-language markers. Single-pass text remains review evidence.
- The translator checks the project glossary and [artwork terminology](../../glossary/artwork-terms.json) first, with context derived from the asset role. It sends a stacked label as one phrase to retain context and fits whole words back to the detected line slots. Argos/CTranslate2 supplies a local fallback, which requires linguistic review even if encoding and Russian OCR pass.
- The renderer infers an ink mask from transparent backgrounds or matching row-edge samples. It reconstructs only the masked background and holds crops whose ink cannot be separated from artwork. It measures native letter size, alignment, tracking, contour, and slant against the candidate Cyrillic fonts and all 24 owner-edited battle references. Matching references contribute measured stroke occupancy. The renderer samples a foreground gradient and reproduces identifiable outlines and directional shadows. Detached transparent glyph sprites can redistribute coverage only within the recovered lettering footprint. Nonlettering RGBA and dimensions are preserved.
- A proposal is decoded again before validation. RGBA4444 and RGBA8888 require exact decoded equality with the rendered draft. The ETC compressor first tries the original selector codebook. It can also search individual and differential base colors and modifiers for changed 4 × 4 blocks. Unchanged blocks and footer bytes are retained. Protected and unchanged pixels must decode exactly. ETC1A4 alpha must be exact, and changed RGB is capped at a per-channel maximum error of 12 and RMS of 5. A block that cannot satisfy the constraints is held. [Khronos ETC1 specification](https://registry.khronos.org/OpenGL/extensions/OES/OES_compressed_ETC1_RGB8_texture.txt)
- Russian OCR runs on the decoded lettering at multiple preprocessing settings. Each line requires agreement from two passes, confidence of at least 75, and the same text after case and punctuation normalization. The gate also checks the shape score, width, slant, dominant color coverage, and soft-alpha drift. A held texture keeps its unchanged after-preview and can include a separate renderer draft for review.
- The existing SHA-256 cache resumes completed textures, commits complete per-texture directories, and verifies all cached preview fingerprints before reusing them. Its inputs include source image, source role, font order and hashes, the reference set, glossary/model, backend, and both OCR language models.

## Local benchmark

The [benchmark labels](milestone-3r-benchmark.json) were recorded by reading the source PNGs before scoring. They were used only to score the results. The set contains 28 English labels and two text-bearing negative controls, an ambiguous end card and a German start prompt. It includes all ten previous pilot textures, a stacked battle label, status badges, decorative artwork, and five ETC1A4 assets. Three already-manually-edited source hashes receive read-only OCR as protection controls. All 107 selected 3N assets were mapped by source fingerprint, and 25 of them occur in the benchmark. The remaining selected assets were inventoried without OCR, translation, or rendering.

| Measure | Result |
| --- | ---: |
| Strong English classifications among English assets | 11/28 |
| English assets without strong classification | 17/28 |
| Exact English transcriptions, including review-only reads | 18/28 |
| False positives among the non-English/ambiguous controls | 0/2 |
| Incorrect transcriptions among confirmed English classifications | 0/11 |
| Proposed translations matching the label rubric | 14/16 |
| Rendered drafts | 6/30 |
| Drafts whose decoded lettering passed Russian OCR | 5/6 |
| Passed all automatic preview checks | 2/30 (6.7%) |
| Protected assets carried through as read-only controls | 3/30 |

The two translation mismatches were the isolated ALL control and the infinitive returned for COMPARE. They stayed in review. The enhanced passes transcribed the stacked MEGA EVOLUTION label and translated the phrase in context. Its competing hypotheses kept it outside automatic rendering. Small status icons and lettering embedded in decorative ribbons remain inconsistent. A sample of two negative controls gives limited evidence about false positives across the inventory.

### Visual review

Across the six rendered lines, the mean shape/height/density score was 0.779 and mean dominant palette coverage was 0.982. The mean width fit was 0.935. Mean soft-alpha drift was 0.260, with the two ETC1A4 prompts and Pokédex exceeding the 0.18 limit. These metrics describe the rendered subset of the benchmark and complement the side-by-side review.

| Source | Visual assessment |
| --- | --- |
| 3N T002718 start prompt | Centered Cyrillic retains the row background and serif appearance. It uses less horizontal space than the English label. Passed the gates. |
| 3N T003394 DRAW | The draft restores a green gradient, dark outline, and slanted fill. The Cyrillic has heavier strokes and a simpler silhouette. Passed the gates. |
| 3N T003475 Pokédex | The source has a diffuse cyan glow and distinct spacing. The Cyrillic draft has a harder contour. Held by the visual gate. |
| 3Q T003794 and T003799 ETC1A4 start prompts | Both survived decode and Russian OCR. The draft edges were too solid compared with the source soft alpha. Both stayed in review. |
| 3Q T004707 ATTACK | The draft recovered a gold face and dark edge, but changed RGB could not be represented within the exact protected-pixel constraints. Held at compression. |

Passing the checks means the offline PNG preview met the automated thresholds. The reference workflow still requires visual and linguistic review before any future installation. No source archives, emulator files or saves were edited. The 24 owner references, the selected and completed 3N images, existing translations, and rollback records were read-only.

## Reproduce and verify

Use the [Linux tooling setup](../testing/linux-offline-artwork.md) with the official Russian Tesseract fast model in the same local tessdata directory as English. The Russian model used here has SHA-256 `e16e5e036cce1d9ec2b00063cf8b54472625b9e14d893a169e2b0dedeb4df225`. [Tesseract Russian traineddata](https://github.com/tesseract-ocr/tessdata_fast/blob/4.1.0/rus.traineddata)

```sh
LD_LIBRARY_PATH="$PWD/build/offline-deps/ocr/usr/lib64" \
  build/offline-deps/venv/bin/python scripts/localize_textures.py \
  --benchmark docs/research/milestone-3r-benchmark.json \
  --manifest build/milestone-3q/inventory/texture-manifest.json \
  --tesseract build/offline-deps/ocr/usr/bin/tesseract \
  --tessdata build/offline-deps/tessdata \
  --model build/offline-deps/translate-en_ru-1_9 \
  --font /usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf \
  --match-font /usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf \
  --match-font /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf \
  --match-font /usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-BoldOblique.ttf

python3 -m unittest discover -s tests -v
```

The optional PaddleOCR 3 recognition backend uses an already-provisioned local model via `--paddle-model`, with matching `--paddle-name` and optional `--paddle-device gpu`. It contributes observations for Tesseract-proposed regions. The benchmark used only Tesseract and CPU CTranslate2. PaddleOCR was unavailable locally and its adapter is covered with a synthetic model response. `--device cuda` selects CTranslate2 GPU inference when available. The host reported zero CUDA devices, so real GPU runs and Paddle inference remain unverified. [PaddleOCR local recognition API](https://www.paddleocr.ai/v3.3.1/en/version3.x/module_usage/text_recognition.html) · [CTranslate2 device API](https://opennmt.net/CTranslate2/python/ctranslate2.Translator.html)

The content-addressed benchmark report is `build/offline-textures/runs/043645015407ec24a4375ff4b499a9ae16d9ef60802b3aaa803400e826703004.json`. A cache rerun reproduced that file. The local visual review sheet is `build/milestone-3r/visual-review.png`. All 126 regression tests passed on Solus 4.9. The synthetic tests include OCR geometry and locale checks, layered style recovery, exact unaffected pixels, and ETC1/ETC1A4 endpoint changes and alpha round trips. Runtime validation remains pending separately for Pokémon X and Y. The installed AppImage is `/home/maxim/azaharplus.AppImage`, with recorded build `cf90688 | AzaharPlus-cf9068844-dirty` and LayeredFS root `/home/maxim/.local/share/azaharplus-emu/load/mods`.
