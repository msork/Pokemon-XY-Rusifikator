# Milestone 3R3 hybrid local artwork review

## Benchmark audit

The 30-texture benchmark was used to develop the 3R2 OCR passes, regions and glossary choices. Its 28/28 transcription and 25/25 translation scores measure performance on familiar examples. The 3R2 holdout reached 8/10 exact transcriptions, 3/8 rubric matches among translation attempts and 0/10 automatic previews. Counting unattempted translations, the holdout matched 3/10. OCR confirmation and exact transcription are distinct measures. A readable but uncertain line can earn transcription credit while remaining in review.

| 3R2 holdout cases | Observed blocker |
| --- | --- |
| T003478, NATIONAL POKÉDEX | OCR produced `NATIONAL POKEDEY`. Argos translated the error as a manicure term. |
| T003481, APPEARANCE/CRY | Classical OCR did not confirm either compound label as a usable line. |
| T003100, POKÉRUS | The transcription normalized correctly, but the translation was `ПОКЕР` and the recovered lettering mask reached a boundary. |
| T003125, K.O. | The transcription normalized correctly, but OCR agreement was weak and the Russian result merely transliterated the letters. |
| T004709, SP. DEF | English transcription was correct. The untranslated Latin result failed the Russian character gate. |
| T003391 and T003469, NEW and COLOR | The crop could not separate backing alpha from the artwork. |
| T003470, SHAPE | The recovered lettering touched a boundary or exceeded the density limit. |
| T003480, HABITAT | OCR included punctuation, the Russian words lacked a space and the fitted Cyrillic lost too much height. |
| T003568, congratulations | The translation conveyed the source meaning but fell outside the fixed rubric. The illustrated background or backing alpha could not be recovered. |
| T003564 and T003453 | Classical OCR correctly excluded both controls. |

All three label files are checked by SHA-256 when evaluating. The 3R3 holdout contains 11 English assets and two non-English controls with source fingerprints disjoint from the prior sets. The labels came from visual inspection of source PNGs before any 3R3 candidate inference on those textures. Some asset families recur, such as Pokédex titles and stat meters. The holdout tests new textures from the same four datasets and does not establish generalization to another game. The earlier holdout was used for candidate selection and is now development evidence. [3R labels](milestone-3r-benchmark.json) · [3R2 labels](milestone-3r2-holdout.json) · [3R3 labels](milestone-3r3-holdout.json)

## Models and hardware

The Linux host reported an NVIDIA GeForce RTX 5070 Laptop GPU with 8,151 MiB VRAM, compute capability 12.0 and driver 620.70.06. Vulkan ran llama.cpp b12819, and the existing CUDA 12.9 libraries ran Paddle and ONNX Runtime 1.23.2. The host had no `nvcc`. ONNX Runtime 1.32.0 attempted to load CUDA 13 libraries, so it was used for CPU calibration only. Published weights and runtime binaries were downloaded to the ignored build tree and inference used a local loopback server. [llama.cpp b12819 and MIT license](https://github.com/ggml-org/llama.cpp/releases/tag/b12819) · [ONNX Runtime CUDA requirements](https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html)

The first vision comparison used the frozen 3R benchmark at zero-based indices 0, 3–9 plus both 3R2 controls. The second used all 12 cases in the 3R2 holdout. The figures include the controls in the denominator. Both models read the two controls in each old-holdout run. OCR scoring folds case and accents and ignores ordinary punctuation, consistent with the existing benchmark. GPU memory means the maximum sampled total device memory minus its idle baseline, sampled about every 200 ms. Latencies are per-request medians with a loaded model and omit the first request in each measurement.

| Vision candidate | First subset | Prior holdout | First subset warm median | GPU delta |
| --- | ---: | ---: | ---: | ---: |
| Qwen3-VL-2B-Instruct Q4_K_M, F16 projector | 6/10 | 10/12 | 0.145 s GPU | 2,846 MiB |
| SmolVLM2-500M-Video-Instruct Q8_0 | 6/10 | 5/12 | 0.125 s GPU | 724 MiB |
| Qwen3-VL-2B Q4_K_M, CPU | 7/10 | — | 1.627 s CPU | — |

Both vision weight sources give Apache-2.0 terms. Qwen3-VL was selected as a reviewer because it read both prior classical misses, including the stylized Pokédex heading and APPEARANCE/CRY. The control errors rule out automatic language confirmation from its output. GPU and CPU produced different readings on the smaller comparison. [Qwen3-VL GGUF](https://huggingface.co/Qwen/Qwen3-VL-2B-Instruct-GGUF) · [SmolVLM2 GGUF](https://huggingface.co/ggml-org/SmolVLM2-500M-Video-Instruct-GGUF)

The translation comparison used the expected English for 3R2 cases at zero-based indices 3–9, followed by `Restore 10 HP and 5 PP` and `Check the remaining PP`. The two extra cases expected `Восстановить 10 ОЗ и 5 ОС` or `Восстанавливает 10 ОЗ и 5 ОС`, and `Проверьте оставшиеся ОС` or `Проверить оставшиеся ОС`, respectively. Models were scored against these fixed strings, ignoring case and ordinary punctuation. This comparison measures translation given the correct English. It includes a separate Argos run without glossary substitutions.

| Russian draft candidate | Exact | Warm median | GPU delta |
| --- | ---: | ---: | ---: |
| Argos en→ru 1.9, CPU | 3/9 | 0.142 s | — |
| Qwen3-1.7B Q8_0, Vulkan | 1/9 | 0.168 s | 2,276 MiB |
| Qwen3-1.7B Q8_0, CPU | 1/9 | 0.587 s | — |
| Qwen3-VL-2B Q4_K_M, Vulkan | 2/9 | 0.164 s | Included above |
| Qwen3-4B Q4_K_M, Vulkan | 4/9 | 0.237 s | 3,064 MiB |
| Qwen3-4B Q4_K_M, CPU | 5/9 | 1.057 s | — |

Qwen3-4B translated both HP/PP cases correctly and had the most reference matches, making it the optional draft model. The Vulkan run produced five mismatches. The supplemental CPU run, measured after selection, recovered SP. DEF and ran about 4.5× slower. The source glossary retains priority, and only glossary translations can pass automatic preview validation. Both Qwen text GGUF releases give Apache-2.0 terms. Argos en→ru 1.9 was the existing baseline. Its local weight metadata did not specify a separate license. [Qwen3-1.7B GGUF](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF/tree/90862c4b9d2787eaed51d12237eafdfe7c5f6077) · [Qwen3-4B GGUF](https://huggingface.co/Qwen/Qwen3-4B-GGUF/tree/bc640142c66e1fdd12af0bd68f40445458f3869b) · [Argos model index](https://github.com/argosopentech/argospm-index)

## Segmentation and background reconstruction

PP-OCRv5 mobile detection proposed regions on nine of ten English cases in the older holdout and on both controls. Its CPU median was 0.040 s per texture. Its regions split SP. DEF into fragments, missed the tiny K.O. badge and recovered neither classical OCR miss when passed through Tesseract. The detector produces polygons around text proposals. Those proposals are too broad to assign pixels to lettering. The existing native-resolution alpha and edge-derived glyph masks remain the source of edit permissions. [PaddleOCR text detection](https://www.paddleocr.ai/v3.3.1/en/version3.x/module_usage/text_detection.html) · [PaddleOCR Apache-2.0 license](https://github.com/PaddlePaddle/PaddleOCR/blob/main/LICENSE)

For inpainting, a synthetic BADGE mask occluded known 128×64 flat, gradient, checkerboard and wavy backgrounds. Scoring measured mean absolute RGB error inside the mask. With all methods, compositing preserved the source alpha and every outside-mask pixel literally. The LaMa ONNX export used a reflected 512×512 input and the native result was cropped back to the source region. The model's 39.2 s first CUDA request fell to 0.234–0.250 s after warm-up. A second CUDA run peaked about 1,193 MiB above the sampled idle baseline. Its CPU requests took about 2.1 s, while OpenCV took about 1–2 ms after its first request.

| Known background | Telea | Navier–Stokes | LaMa CPU | LaMa CUDA |
| --- | ---: | ---: | ---: | ---: |
| Flat | 0.787 | 0.000 | 4.218 | 4.217 |
| Gradient | 1.544 | 0.810 | 3.689 | 3.689 |
| Checkerboard | 14.907 | 13.963 | 18.741 | 18.739 |
| Wavy RGB | 10.153 | 10.047 | 9.007 | 9.004 |

LaMa improved the wavy case by about one channel value on average, but its worst channel error there was 41. It also made errors on a flat background. None of these alternatives qualifies to fill unknown backgrounds in an automatic preview. The verified path still uses exact edge-supported reconstruction and rejects ambiguous backing alpha or illustrated backgrounds. [LaMa upstream Apache-2.0 license](https://github.com/advimman/lama/blob/main/LICENSE) · [Carve ONNX export](https://huggingface.co/Carve/LaMa-ONNX/tree/c3c0c9e468934d62e79c329e35d82dd09ff8c444)

## Pipeline and rerun

`scripts/localize_textures.py` uses independent classical OCR for spatial evidence and Russian verification. A vision reading corroborates existing OCR, identifies competing hypotheses, or stays advisory when spatial evidence is weak. When the VLM backs an exact classical alternative, the asset goes to review. A model reading never supplies a lettering mask. Contextual Russian drafts preserve the number sequence and enforce standalone `HP→ОЗ` and `PP→ОС`. Bare stat labels are substituted directly while preserving separators. The existing deterministic Cyrillic font selection, native-size fit, alpha and color recovery, independent Russian OCR, ETC encode/decode and exact outside-mask RGBA gates remain in effect.

The optional models load one at a time on first uncached use. The caches incorporate model, projector, runtime, prompts, device and source input fingerprints. A failed inference aborts the run so completed entries can be reused when it resumes. Outputs stay under `build/`. Reuse the 3R2 local arguments and add the following options to the existing command. [3R2 command and prerequisites](milestone-3r2-artwork.md)

```bash
--holdout docs/research/milestone-3r3-holdout.json \
--llama-server build/milestone-3r3/llama/llama-b12819/llama-server \
--vision-weights build/milestone-3r3/models/qwen-vl-q4.gguf \
--vision-projector build/milestone-3r3/models/qwen-vl-mmproj.gguf \
--translation-weights build/milestone-3r3/models/qwen-4b-q4.gguf \
--ai-device Vulkan0
```

The model flags accept local files only. Use `--ai-device none` for CPU llama.cpp. To reproduce the matched classical run, omit the five optional model flags. On this host, setting `VK_DRIVER_FILES=/usr/share/vulkan/icd.d/10_nvidia.json` makes Vulkan select the verified NVIDIA adapter. The run used the 3Q manifest, English and Russian PP-OCRv5 recognition, the local Hunspell dictionary and the 3R2 font profiles.

The measured model files have these SHA-256 fingerprints.

| Local file | SHA-256 |
| --- | --- |
| `llama.tar.gz` | `37f7a0528fbf586d59e2e703eefb6fd38b9e6d144797a45a91ac4ff8973b7f0c` |
| `qwen-vl-q4.gguf` | `089d75c52f4b7ffc56ba998ffc50aae89fcafc755f9e7208aacca281dca6c2ae` |
| `qwen-vl-mmproj.gguf` | `c3d5afbef5287953acd57b4043d2269456e5761a4eaccb3b71b062996970aea5` |
| `qwen-4b-q4.gguf` | `7485fe6f11af29433bc51cab58009521f205840f5b4ae3a32fa7f92e8534fdf5` |

## End-to-end results

The classical and hybrid runs used the same source PNGs, scoring and rendering thresholds. Translation accuracy is shown both among attempts and against all translatable assets, excluding the three protected manual controls in the original benchmark. Vision evidence is scored independently of accepted English OCR lines.

| Evaluation | Exact classical text | Strong English OCR | Exact vision evidence | Exact Russian among attempts | Exact Russian across eligible assets | Automatic previews |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 3R classical | 28/28 | 19/28 | — | 25/25 | 25/25 | 4/25 |
| 3R hybrid | 28/28 | 19/28 | 23/28 | 25/25 | 25/25 | 4/25 |
| 3R2 classical | 8/10 | 7/10 | — | 3/8 | 3/10 | 0/10 |
| 3R2 hybrid | 8/10 | 7/10 | 10/10 | 4/8 | 4/10 | 0/10 |
| 3R3 classical | 7/11 | 6/11 | — | 4/7 | 4/11 | 0/11 |
| 3R3 hybrid | 7/11 | 5/11 | 11/11 | 6/9 | 6/11 | 0/11 |

The three hybrid runs had zero strong English false positives across six control assets and zero incorrect automatic previews. The VLM did read `Autres` on a fresh control. The strong-English count on the fresh holdout fell from six to five because the VLM supported the classical `Hall of Fame` alternative over the initially selected `H all of Fame`. The other three fresh transcriptions recovered only as vision evidence were `CAPS`, `lower`, and `MOUNTAIN KALOS POKÉDEX`. This sample is small and those additional readings still require localized evidence.

On the fresh holdout, CAPS, lower, Hall of Fame and TYPE 2 lacked sufficient localized OCR agreement. The Mountain title failed English transcription and spelling, and the Coastal title and SP. ATK failed Russian spelling. NEW crossed ambiguous backing alpha, and HP correctly translated to ОЗ but failed the mask boundary or density gate. CLEARED rendered but failed Russian OCR readback. Congratulations! produced a rubric-matching draft that requires linguistic review. These are the blockers behind zero automatic previews.

The seven 3R hybrid draft lines averaged 0.806 for visual score, 0.985 palette coverage and 0.043 soft-alpha drift, matching the classical run. For the two fresh drafts, these means were 0.733, 0.938 and 0.021. Classical fresh drafts averaged 0.734, 0.938 and 0.098. The samples are too small to infer a visual improvement. The hybrid congratulations draft preserves the original layout and much of its glow in the comparison, but its stroke weight and letter shape still differ.

The fresh classical run took 18.50 s and the hybrid run took 24.45 s, with CPU PaddleOCR and hardware-accelerated VLM and LLM. The rerun took 3.28 s and returned the identical report hash, `b5b91498075a808dd40b5eb0886c830e6261dd1b9b33e4411a06dd831c277e23`. Runs used shared stage caches and those times are specific to the observed cache state.

Eight contact sheets under `build/milestone-3r3/comparisons/` show the sources, classical drafts, hybrid drafts and verified results. An independent check verified native dimensions on all 55 hybrid result pairs, exact source RGBA on held previews, zero changed RGBA pixels outside the mask on the four accepted previews, and all 24 manual artwork hashes. The existing 107-item 3N selection mapped without missing entries and was used for provenance only. All 138 regression tests passed. The run was offline, and no preview was deployed. The local AzaharPlus AppImage and LayeredFS root were present, with no X or Y mod directories. Pokémon X and Pokémon Y runtime validation both remain pending. [Linux profile and title IDs](../testing/linux-offline-artwork.md)
