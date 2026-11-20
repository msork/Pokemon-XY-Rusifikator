# Milestone 3L: Original FIGHT Texture Review

## Decision and safety state

The owner rejected the Milestone 3K Russian button lettering for poor form, alignment, and styling. Its image was rolled back; both X/Y `a/2/4/0` LayeredFS paths were originally absent and were removed again. The four Milestone 3K text archives remain installed at their verified hashes. The rejected PNG/archive outputs and their generator/installer code were removed. No replacement lettering has been made, and no image should be installed or regenerated until the owner approves a proposed design.

The canonical 24-PNG set was not edited. The original `fight_text.bclim.png` SHA-256 remains `c3317a191a48b540b0e3b87e35baed574d4d47f0bf4171c5beeb0d95280646b9`.

## Original reference files

Run this read-only source exporter to reproduce the references and their hash manifest:

```powershell
python scripts/prepare_milestone3l_fight_reference.py
```

Generated files are under ignored `build/milestone-3l/artwork-review/`:

- `fight_text-original-80x50.png` is a byte-identical copy of the canonical source.
- `fight_text-nearest-8x-640x400.png` expands every source pixel into an exact 8 by 8 block, without interpolation.
- `original-fight-style-reference.svg` displays both views over a checkerboard so the transparent edges and pale background are visible.
- `manifest.json` records SHA-256 hashes, dimensions, pixel replication verification, and source color/alpha measurements.

Evidence from the original RGBA PNG:

- Canvas: 80 by 50 pixels, RGBA8.
- Nonzero-alpha footprint: x=4..77, y=15..35.
- Red ink/edge footprint by measured red-color mask: x=8..75, y=18..32. This is a measured pixel range, not an asserted font bounding box.
- Transparent pixels: 2,669 of 4,000; fully opaque pixels: 280.
- The backing pixels use RGB 255,238,238 with varying alpha. The most frequent visible ink colors include RGB 119,0,0 (61 pixels), 170,0,0 (34), 68,0,0 (30), and 187,34,34 (26). Other sampled red/brown and pale-red edge colors are listed in the generated manifest.
- The word is uppercase, narrow sans-serif lettering, centered horizontally and vertically in the small texture. The enlargement shows antialiased red letter faces with a darker red/brown edge and a subtle offset shadow/edge treatment. The pink-white backing is translucent and rounded by its alpha boundary; it is part of the artwork and must remain intact.

The coordinates and color counts above are computed from pixel data. The visual description of the font and edge treatment is an inspection of the native and nearest-neighbor previews; no original font filename or source font has been identified. The raster does not prove which font family or drawing filter created it.

## Russian lettering style specification for a future proposal

This is a design brief only; it does not generate art:

1. Preserve the 80 by 50 RGBA canvas, source alpha, pale backing, and all pixels outside the lettering edit mask.
2. Keep the label horizontally centered and within the measured original ink area (approximately 68 by 15 pixels). The glyphs should read clearly at native size, not only when enlarged.
3. Match the original condensed uppercase sans-serif weight, red face, dark red/brown edge, antialiasing, and subtle shadow. Sample the 8x reference rather than substituting a block/pixel font.
4. Retain the original pink-white translucent backing and rounded alpha silhouette. Do not redraw, recolor, flatten, or resize it.
5. Check that the intended Russian equivalent fits the available width and height before adding any pixels. The Russian word choice itself should be reviewed separately from the artwork.

## Safe lettering-replacement workflow after approval

1. Copy the canonical source to a new ignored working directory, record its SHA-256, and leave `build/milestone-3i/editing/` untouched.
2. Work from the native source and the 8x reference. Establish an explicit lettering mask that includes the existing antialias and shadow pixels but excludes the translucent backing.
3. Remove/rebuild only within that mask. Compare decoded RGBA pixels against the original and fail validation if any pixel outside the approved mask changes. Keep canvas dimensions and alpha channel unchanged.
4. Export a native 80 by 50 RGBA8 PNG and an 8x nearest-neighbor preview. Review both at native and enlarged scales for centering, edge weight, colors, and background continuity.
5. After artwork review, encode only `fight_text.bclim` in pack member `0/2` of `a/2/4/0`. Verify the other 10 textures and six unrelated GARC members are unchanged, then make separate X/Y candidates with hashes.
6. Keep any future image patch separate from text archives. Back up the two exact mod targets, record absent paths, and make image rollback independent of the text rollback.

This workflow is documented for a later approved design. Do not create replacement lettering or install an image patch before owner approval.
