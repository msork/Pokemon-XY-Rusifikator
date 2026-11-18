# Milestone 1 Research Log

Date: 2026-11-18

## Local inventory

SHA-256 manifests were generated for all four trees at `reports/pokemon-x-base.jsonl`, `reports/pokemon-y-base.jsonl`, `reports/pokemon-x-update-1.5.jsonl`, and `reports/pokemon-y-update-1.5.jsonl`. Reports are local and ignored by Git.

| Dataset | Files | Bytes |
|---|---:|---:|
| X base | 653 | 1,783,776,455 |
| Y base | 653 | 1,783,776,439 |
| X update 1.5 | 147 | 28,575,664 |
| Y update 1.5 | 147 | 28,575,648 |

Combined size is 3,624,704,206 bytes. Sampled extensionless resources under `a/` start with `43 52 41 47` (`CRAG`, byte-reversed GARC magic) and consistent GARC-like header fields. This is signature evidence, not a completed structural parse. The trees also contain `.cro` modules, `btl_ai.garc`, `static.crs`, shaders, and audio.

The Project Pokémon community file map identifies likely English text archives at `a/0/7/4` and `a/0/8/2`, script text in other `a/0/8/*` resources, and font resources around `a/1/8/5`; all those paths exist. These mappings are discovery leads, not an authoritative format specification. No archive has yet been unpacked, no message contents have been validated, and no individual font member has been identified.

## X/Y byte comparison

Base comparison: 625 identical paths, 28 differing paths, zero path-only entries. Update comparison: 109 identical, 38 differing, zero path-only entries. Differences prove byte variation only; their semantic purpose has not yet been determined.

## Base versus update path comparison

For each game, all 147 update paths also exist in base, 27 have identical bytes, and 120 differ; there are 506 base-only paths and no update-only paths. This means update 1.5 supplies same-path overrides for 120 resources. It does not prove which side Azahar selects at runtime. Comparing identified candidate archives shows the `a/0/7/*` and `a/1/8/*` families vary between base and update, so effective text and font assets must be resolved against the installed update rather than assumed from base.

## Research sources and provisional conclusions

- Citra's official game-modding guide documents per-title mod directories under `load/mods/<Title ID>` and the `romfs` replacement folder: <https://citra.azahar-emu.org/help/feature/game-modding/>. This supports the expected base title ID layout as a working hypothesis; the target MSYS2 installation remains unverified.
- Azahar's `LayeredFS` source documents same-path RomFS replacements and patched files: <https://github.com/azahar-emu/azahar/blob/master/src/core/file_sys/layered_fs.cpp>. This confirms replacement semantics at the RomFS overlay layer, but not which base/update RomFS tree the user's installed build supplies; that remains open pending inspection of the local build and runtime logs.
- pk3DS is a Gen VI-capable project and includes Gen 6 structures, but complete text extraction/rebuild coverage is not established: <https://github.com/kwsch/pk3DS>.
- Project Pokémon's X/Y file map assigns `a/0/7/4` to English text, `a/0/8/2` to English script text, and `a/1/8/5` to fonts: <https://projectpokemon.org/home/docs/gen-6/xy-file-system-r89/>. Treat as a community reference and validate against actual contents.
- Kuriimu-family support and the exact X/Y message format have not yet been validated against these files. No parser is selected.
- A secondary encoding reference reports rasterized fonts and system-font fallback in Gen VI, but this does not prove Russian renders in X/Y: <https://bulbapedia.bulbagarden.net/wiki/Character_encoding_(Generation_V%E2%80%93present)>.

## Decisions

Use a local Python read-only inventory tool. Do not select a message parser or edit game assets until samples are signature-inspected and a compatible implementation is verified. Keep base and update resources separate until update precedence is verified.

## Open questions

- Which archive members under the candidate `a/` resources contain messages and font data?
- Which resources differ semantically across X/Y and base/update?
- What exact Azahar version and MSYS2 user directory does the target PC use?
- Does installed update 1.5 replace text/font resources, and how does this build resolve LayeredFS against installed updates?
