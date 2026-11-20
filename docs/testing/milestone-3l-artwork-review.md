# Milestone 3L Owner Artwork Review

The rejected Russian lettering has been removed from the test mod paths and generated candidate outputs. No replacement artwork exists. Review the original texture only:

```text
build/milestone-3l/artwork-review/fight_text-original-80x50.png
build/milestone-3l/artwork-review/fight_text-nearest-8x-640x400.png
build/milestone-3l/artwork-review/original-fight-style-reference.svg
build/milestone-3l/artwork-review/manifest.json
```

Recreate these read-only references with:

```powershell
python scripts/prepare_milestone3l_fight_reference.py
```

The native PNG is byte-identical to `build/milestone-3i/editing/fight_text.bclim.png`. The 8x PNG is a pixel-exact nearest-neighbor enlargement. Open the SVG in a browser to compare native and enlarged source against a transparency checkerboard.

The style measurements and future mask-based editing requirements are in [the original texture research](../research/milestone-3l-original-fight-style.md). No runtime test is needed for these reference files. The game remains on the original FIGHT texture; the 227 text records remain installed. No replacement lettering may be generated or installed before owner approval.
