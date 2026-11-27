# Milestone 3Q BCH texture discovery

## Scope and evidence

The scan reopened all four extracted RomFS datasets on Linux, verified archive SHA-256 and reused results for byte-identical GARC archives. It looked for BCH at the start of standalone files and direct or nested GARC members after the existing bounded LZ11 decode. Member locations are sequences of GARC entry and subfile IDs. The BCH container hash covers the decoded member bytes. Each raw surface offset is relative to those bytes.

All 4,386 candidates recorded by 3P matched the new scan by dataset, archive, member and raw container SHA-256. No headers were found in the two update datasets. The 2,118 unique containers all use backward and forward compatibility 7 with converter revision 38669. The scanner also checked 24 occurrences of the bare `BCH` byte sequence in non-GARC source files. Twenty-two lacked the NUL in the actual signature. The other two occur at the same byte offset in the X/Y copies of an AAC file. Their supposed contents offset exceeds the remaining file length. They are false signatures.

| Dataset | Valid BCH occurrences | Texture entries | Exported surface occurrences | BCH issues |
| --- | ---: | ---: | ---: | ---: |
| Pokémon X base | 2,193 | 2,168 | 2,278 | 0 |
| Pokémon X update 1.5 | 0 | 0 | 0 | 0 |
| Pokémon Y base | 2,193 | 2,168 | 2,278 | 0 |
| Pokémon Y update 1.5 | 0 | 0 | 0 | 0 |
| **Total** | **4,386** | **4,336** | **4,556** | **0** |

The 4,556 surface occurrences comprise 4,292 2D textures and 264 faces from 44 cubemap occurrences. There are 2,160 texture entries across the unique containers and 1,620 distinct PNGs. The 13,040 BCLIM occurrences and their 48 translation exclusions match 3P. The scan still records 4,940 non-BCH diagnostics, including unaccepted texture-pack signatures and LZ11 decode errors.

## Header, relocations and resource types

The XY parser checks the five file sections and the relocation tail. It validates the source field of all 273,569 relocation entries across unique containers, checks target bounds, rejects overlapping source fields and keeps the relocation table read-only. String relocations address their source byte-wise. The other observed source offsets are in words. One scene dictionary uses the end of contents for its empty pointer list. That one-past-end pointer is accepted only for an empty dictionary slot. Command relocations resolve disk byte offsets into raw data, without applying the VRAM address encoding used at runtime.

The contents directory separates textures from models, materials, shaders, LUTs, lights, animations and scenes. The parser bounds the pointer and name tables and resolves each texture descriptor through its relocation. Models, materials and animations are inventoried by their top-level dictionary counts. Across source occurrences the directory lists 1,226 models, 2,436 materials, 288 skeletal animations, 344 material animations and 76 visibility animations. Their internal rendering and animation data remain outside this extractor. Of the unique containers, 1,146 contain just textures, 394 contain textures alongside other resources, and 578 contain no textures.

| Evidence | Reference |
| --- | --- |
| BCH header and directories | [SPICA header](https://github.com/gdkchan/SPICA/blob/master/SPICA/Formats/CtrH3D/H3DHeader.cs) · [SPICA resource directory](https://github.com/gdkchan/SPICA/blob/master/SPICA/Formats/CtrH3D/H3D.cs) |
| Relocation fields and sections | [SPICA relocator](https://github.com/gdkchan/SPICA/blob/master/SPICA/Formats/CtrH3D/H3DRelocator.cs) · [SPICA section types](https://github.com/gdkchan/SPICA/blob/master/SPICA/Formats/CtrH3D/H3DSection.cs) |
| PICA packet layout and cubemap addresses | [SPICA packet reader](https://github.com/gdkchan/SPICA/blob/master/SPICA/PICA/PICACommandReader.cs) · [SPICA texture descriptor](https://github.com/gdkchan/SPICA/blob/master/SPICA/Formats/CtrH3D/Texture/H3DTexture.cs) · [Azahar texture registers](https://github.com/azahar-emu/azahar/blob/master/src/video_core/pica/regs_texturing.h) |
| PNG orientation and mip storage | [SPICA direct texture converter](https://github.com/gdkchan/SPICA/blob/master/SPICA/PICA/Converters/TextureConverter.cs) · [SPICA ETC converter](https://github.com/gdkchan/SPICA/blob/master/SPICA/PICA/Converters/TextureCompression.cs) · [citro3d texture storage](https://github.com/devkitPro/citro3d/blob/master/source/texture.c) |

The project uses these references for format facts and implements independent Python code. SPICA is released under the Unlicense. Azahar's reference header is GPLv2-or-later. No third-party source is copied into this repository. [SPICA license](https://github.com/gdkchan/SPICA/blob/master/LICENSE.txt)

## PICA surface extraction

The reader cross-checks the descriptor's format against PICA registers and validates dimensions, command word counts and texture relocation flags. Alternate texture units must point to the same surface with the same format and dimensions. For cubemaps the six addresses map to +X, −X, +Y, −Y, +Z, −Z. Each face gets its own PNG and source record. The existing BCLIM pixel decoder is reused through a raw tiled-plane entry point with the PICA format IDs translated explicitly. BCH's bottom-up convention is converted to PNG row order for both direct and ETC data.

All observed descriptors declare one mip level. The manifest keeps the declared count and each exported level's index, dimensions, format, start and byte length. Contiguous whole-tile mip chains with matching PICA LOD fields are covered by synthetic tests. Smaller-than-tile mip levels, other converter versions and unrecognized command or relocation variants remain unsupported. HILO8 has shared synthetic decoder coverage and did not occur in the BCH corpus. Cubemap faces are exported independently. Seam and runtime sampling behavior remain unverified.

`bch-containers.json` records per-hash validation, section sizes, relocation counts, dictionary counts and per-source locations. `bch-texture-manifest.json` includes the name and dictionary index, cubemap face, mip level, absolute location within the decoded BCH, payload SHA-256, archive SHA-256 and GARC member path. PNGs under `bch-png/` are deduplicated by the PICA format, dimensions and exact payload bytes. The OCR report retains these source mappings. A separate pass reopened all 2,118 unique containers and checked the mapped spans, raw payload hashes and every pixel of all 1,620 PNGs.

## Replacement investigation

The in-memory API can replace a same-size encoded payload for a single-surface texture in a fully parsed texture-only BCH. It verifies the candidate by decoding it and checks that no other surface overlaps the byte range and that every raw-data reference belongs to a known texture. The original bytes are returned for unchanged content. Synthetic tests check a changed payload, unrelated byte identity, relocation stability and rejection of aliases, cubemaps and model-bearing containers. All 1,181 eligible texture entries in unique texture-only containers returned the original bytes on a no-op. A changed RGBA8 payload was checked in memory against one base occurrence per game at `a/0/8/9`, member `89/0`. Each change affected one decoded channel and preserved all bytes outside the target. This API has no installer or archive rewrite workflow. Changed mip chains and model-bearing containers need additional reference and runtime evidence.

## Reproduce locally

Use the [Linux tooling setup](../testing/linux-offline-artwork.md). The BCH option runs the scanner with a fresh inspection of each distinct archive and uses the existing per-run SHA-256 cache. The command writes BCH results alongside the separate BCLIM inventory in a dedicated generated directory.

```sh
build/offline-deps/venv/bin/python scripts/scan_milestone3n_artwork.py --bch \
  --output build/milestone-3q/inventory
LD_LIBRARY_PATH="$PWD/build/offline-deps/ocr/usr/lib64" \
  build/offline-deps/venv/bin/python scripts/localize_textures.py \
  --manifest build/milestone-3q/inventory/bch-texture-manifest.json \
  --ocr-new-since build/milestone-3p/inventory/texture-manifest.json \
  --tesseract build/offline-deps/ocr/usr/bin/tesseract \
  --tessdata build/offline-deps/tessdata --jobs 8
python3 -m unittest discover -s tests -v
```

All 116 regression tests passed on Solus 4.9, including eight synthetic BCH tests.

The OCR invocation uses the existing two-background Tesseract pass and confidence gate. The run inventoried all 1,620 PNGs and retained all 4,556 source mappings. It found two single high-confidence Latin lines, 429 results requiring OCR review and 1,189 with no extracted line. A repeat from the cache produced the same report, `build/offline-textures/runs/9ed3f009e3d529d06e2c1ef9b77753e6ff1bdbf5d96d09f7eafc5c3578fc23bb.json`. OCR is evidence for manual review. BCH textures remain outside the BCLIM translation-proposal path.

The installed Linux runtime is `/home/maxim/azaharplus.AppImage` with recorded build `cf90688 | AzaharPlus-cf9068844-dirty`. Its data directory is `/home/maxim/.local/share/azaharplus-emu` and its observed LayeredFS root is `load/mods` beneath that directory. Pokémon X and Pokémon Y runtime validation each remain pending. Previous Windows rollback records remain available.
