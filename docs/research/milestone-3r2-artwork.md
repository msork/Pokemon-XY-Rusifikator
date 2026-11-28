# Milestone 3R2 offline artwork quality

## Evaluation

The original [30-texture benchmark](milestone-3r-benchmark.json) kept its labels and scoring rubric. The [12-texture holdout](milestone-3r2-holdout.json) was annotated before running 3R2 and has disjoint source hashes. It contains ten English assets and two language controls. Both sets use the same conditional translation and preview gates. The three protected benchmark assets are read-only OCR controls and are excluded from the translatable denominator.

| Measure | 3R baseline | 3R2 Tesseract only | 3R2 Tesseract + PaddleOCR CPU | 3R2 holdout |
| --- | ---: | ---: | ---: | ---: |
| Exact English transcription of English assets | 18/28 (64.3%) | 19/28 (67.9%) | **28/28 (100%)** | 8/10 (80%) |
| English assets with strong OCR confirmation | 11/28 | 11/28 | 19/28 | 7/10 |
| Strong English false positives on language controls | 0/2 | 0/2 | 0/2 | 0/2 |
| Translation matches among attempts | 14/16 (87.5%) | 17/17 (100%) | **25/25 (100%)** | 3/8 (37.5%) |
| Passed all gates among translatable assets | 2/25 (8%) | 4/25 (16%) | **4/25 (16%)** | 0/10 (0%) |

Exact transcription allows a review-only reading and normalizes case, accents, punctuation and letter/number spacing. Confirmed OCR still requires two agreeing passes. Repeated Paddle crops count as one pass. Translation accuracy uses the fixed human rubric and excludes assets with no proposal. The holdout's longer congratulatory wording conveys the intended meaning but missed the fixed rubric. Other holdout results exposed domain terminology errors, including the disease label, an abbreviation and a badly read Pokédex heading. These results keep the project below the 80% acceptance target and show that the main benchmark scores do not generalize to the holdout.

The main benchmark produced seven drafts, with mean soft-alpha drift of 0.043 across those lines. The 3R value was 0.260 over six drafts. The two ETC1A4 start prompts now pass automatic gates. Pokédex still exceeds the soft-alpha limit. The renderer kept the exact outside-mask RGBA and compression limits. Side-by-side inspection still shows that native stroke weight differs in the start prompts and that the DRAW replacement is more upright than the source. These four passing previews remain review material. Local sheets under `build/milestone-3r2/comparisons/` show the source, 3R draft, 3R2 draft and verified after-preview.

## Audit of all 28 3R non-passing cases

The first column uses the IDs recorded in the original benchmark. The two earlier passing previews remain passing. The first blocker is the enforced gate at which each run stopped.

| ID | Exact 3R blocker | 3R2 outcome |
| --- | --- | --- |
| T000230 | Manual Internet artwork is protected | Read-only OCR confirms Internet |
| T000262 | Manual PLAY artwork is protected | Read-only PaddleOCR reads PLAY |
| T000263 | Manual DECORATE artwork is protected | Read-only OCR confirms DECORATE |
| T000264 | No OCR line on SWITCH | Exact Paddle reading lacks independent agreement |
| T003077 | OCR confused the tiny EXP label with the attached meter | Exact reading lacks independent agreement |
| T003099 | FAINTED's colored translucent badge crossed the sampled background | Backing alpha remains ambiguous |
| T003101 | PARALYSIS was below minimum OCR confidence | Tight crops recover the word, without independent agreement |
| T003102 | ASLEEP yielded a low-confidence fragment | Exact Paddle reading lacks independent agreement |
| T003103 | FROZEN was read with border characters | Exact crop hypothesis remains in conflict |
| T003104 | BURNED's backing and glyph alpha could not be separated | Backing alpha remains ambiguous |
| T003105 | POISONED lacked two agreeing passes | OCR agrees, the badge backing still cannot be recovered |
| T003260 | MEGA EVOLUTION was transcribed but lacked agreement | Both lines confirmed, observed edges disagree with the background model |
| T003262 | The illustrated SHIFT button yielded no reliable text | Exact Paddle reading lacks independent agreement |
| T003395 | The gradient LOSE wordmark lacked OCR agreement | Confirmed OCR and isolated sprite, but Russian lettering loses too much native height |
| T003397 | The WIN contour extended into the sampled crop edges | Text confirmed, the inferred mask is too dense or reaches a boundary |
| T003423 | OCR read fragments of the HIGH SCORE ribbon | Exact reading lacks independent agreement |
| T003424 | No reliable OCR line on RESULTS | Exact OCR, ribbon artwork crosses the reconstructed backing |
| T003430 | No reliable OCR line on CLEARED | Exact reading lacks independent agreement |
| T003467 | TYPE 1 had a spurious boundary mark and lacked agreement | TYPE1 normalizes to TYPE 1, the translucent badge backing remains ambiguous |
| T003471 | ALL lacked agreement and the model returned an inflected phrase | Confirmed OCR and contextual glossary match, but backing remains ambiguous |
| T003475 | The Cyrillic Pokédex preview exceeded soft-alpha limits | Improved glow, but residual soft-alpha drift still exceeds the limit |
| T003479 | COMPARE mask and OCR bounds disagreed and the model returned an infinitive | Glossary and mask verified, Russian OCR does not confirm every decoded line |
| T003563 | FIN is an ambiguous non-English control | Language gate still holds it |
| T003786 | German start prompt is a negative control | Language gate still holds it |
| T003794 | ETC1A4 PUSH START BUTTON was too solid after rendering | Source-opacity fitting and all gates pass |
| T003799 | ETC1A4 PRESS START was too solid after rendering | Source-opacity fitting and all gates pass |
| T004707 | ATTACK's new colors could not preserve protected ETC1 samples | Exact protected-pixel compression still fails |
| T004708 | SPEED's inferred foreground reached its artwork boundary or was too dense | Mask gate still holds it |

## Implementation and preservation

- Tesseract and PaddleOCR read original, isolated color, compact, and rotated windows. Spatial consensus prefers a complete baseline over repeated fragments and keeps competing readings available for review. Only unambiguous letter/number segmentation is normalized. Recognizer observations are cached separately from rendering.
- The fitter compares normalized ink templates derived from all 24 manual battle references and records the three closest applicable shapes. Native-height and shape gates remain in force. Controlled horizontal fit has a minimum scale of 0.88. No reference pixels are copied into a draft.
- Background checks use exact row edges and, for a linear gradient, additional edge samples and unchanged support between glyphs. Non-sprite alpha is preserved. Detached glyph art must have a clear perimeter and every separate alpha component must intersect the OCR region. The renderer transfers measured representable alpha ranks to a soft, bounded fringe and reuses sampled gradients, shadow direction, and outline color. A mask PNG is stored and fingerprinted with each draft.
- Russian spelling is checked locally with Hunspell. Project UI terms and a small explicit name/abbreviation list stay valid, and other misses go to review. Contextual glossary entries for comparison UI and Shift augment the existing entries without overwriting them. Russian OCR readback stays mandatory on the decoded result. The fallback model still requires linguistic review even when spelled correctly.
- Independent verification checked the 24 manual reference hashes, the before/after SHA-256 of held and protected previews, and every outside-mask pixel of the four passing previews. Source assets, the 107 selected 3N images, manual edits, saves, translations, and rollback records were preserved. No preview was installed.

## Local runtime and reproduction

PaddleOCR 3.3.1 with PaddlePaddle 3.2.2 ran the official English and Cyrillic PP-OCRv5 mobile models under isolated Python 3.12.16. The host's Python 3.14 package index had no PaddlePaddle wheel. The English and Cyrillic model archive SHA-256 values were respectively `e595b4cf2ffad19fbb5a61ba345d63939577a3ab8717b6e5995642590c9101b4` and `ef0c66f19ebe6849daf9aa7485e9253d2a8d851e165e208bf08ba68a620ae645`. All benchmark inference was local. [PaddleOCR model downloads and API](https://www.paddleocr.ai/v3.3.1/en/version3.x/module_usage/text_recognition.html) · [LibreOffice Russian Hunspell dictionary](https://github.com/LibreOffice/dictionaries/tree/master/ru_RU)

On Solus 4.9, the RTX 5070 Laptop GPU reported compute capability 12.0 and driver 620.70.06 when queried on the host. CUDA is hidden during a standard restricted tool run. The measured CTranslate2 fallback benchmark used 20 batches of eight prompts after three warm-ups. CPU median and p95 were 422.912 and 474.708 ms. CUDA median and p95 were 43.844 and 47.772 ms. Both produced identical translations on those eight prompts. [CTranslate2 CUDA requirements](https://opennmt.net/CTranslate2/installation.html)

The official CUDA 12.9 PaddlePaddle 3.2.2 wheel also ran locally. Its package-index endpoint timed out, so the matching Python 3.12 wheel was installed directly from the official CDN in a separate build directory. On the same nine English line crops after one warm-up per crop, 45 measured recognitions gave a CPU median/p95 of 22.391/36.525 ms and GPU median/p95 of 6.937/8.954 ms. The timed path includes crop preprocessing and recognition. Each backend recognized the PUSH START BUTTON label rotated 90° and reported a 270° corrective pass, with corroboration from Tesseract. One ambiguous COMPARE crop differed between raw CPU and GPU recognizer strings. The full 30-texture GPU run used both CUDA OCR models and GPU CTranslate2, and reproduced every CPU decision, reason and before/after PNG fingerprint. Its 21.45-second wall time includes cached Tesseract work and should be read separately from the device-only comparison. [Official CUDA wheel index](https://www.paddlepaddle.org.cn/packages/stable/cu129/paddlepaddle-gpu/)

Use the [3R command and setup](milestone-3r-artwork.md) with the isolated Python 3.12 environment. Add the following options to enable the same inference path. For the independent set, substitute `--holdout docs/research/milestone-3r2-holdout.json` for the benchmark argument.

```sh
--paddle-model build/milestone-3r2/en_PP-OCRv5_mobile_rec_infer \
--paddle-name en_PP-OCRv5_mobile_rec \
--paddle-rus-model build/milestone-3r2/cyrillic_PP-OCRv5_mobile_rec_infer \
--spell-dictionary build/milestone-3r2/ru_RU \
--match-font /usr/share/fonts/opentype/urw-base35/NimbusSansNarrow-Bold.otf
```

Set `PADDLE_PDX_CACHE_HOME` and `XDG_CACHE_HOME` to a directory under `build/`. A warm benchmark rerun took 0.43 seconds and reproduced the report hash. The cold CPU combined run took 38.88 seconds. The Tesseract-only run reused the Tesseract stage cache and took 3.16 seconds, so its wall time is a cache result. Full reports are under `build/offline-textures/runs/`. The combined GPU report is `134786a9860d18d0728fbb741bd5af4baa718ad22b78c5897de10d3f703bdd1c.json`. The combined-CPU benchmark is `d12dbd58bd1488ec9e9c2e8a56803b862d1e2c673f55e9288b354645be061ab7.json`, Tesseract-only is `1d8a787141f7d750931d8a1a0e5bb78037f25dbc614b4b2586584a0524143f2a.json`, and the combined holdout is `3fbffbc6598b055982590d76529077e56a9d386489bbd8558d438add1d0b5f39.json`.

All 133 regression tests passed. The installed Linux AppImage remains `/home/maxim/azaharplus.AppImage`, recorded build `cf90688 | AzaharPlus-cf9068844-dirty`. The data directory is `/home/maxim/.local/share/azaharplus-emu` and its LayeredFS root is `load/mods` below that directory. Runtime validation remains pending separately for Pokémon X and Y.
