# House style, and where every number came from

This is not a taste document. Every constant in `scripts/cvprfig/style.py` was
measured out of the vector content of published figures, using PyMuPDF to read
fill colours, stroke widths, font names and glyph sizes directly from the PDFs.

## The corpus

| Paper | Venue | Figure measured |
|---|---|---|
| SparseWorld: A Flexible, Adaptive and Efficient 4D Occupancy World Model | AAAI 2026 submission (arXiv 2510.17482) | `overview.pdf`, `comparation.pdf` |
| GaussianWorld: Gaussian World Model for Streaming 3D Occupancy Prediction | CVPR 2025 (arXiv 2412.10373) | `framework.pdf`, `teaser.pdf` |
| EmbodiedOcc: Embodied 3D Occupancy Prediction | (arXiv 2412.04380) | `Main_new.pdf`, `teaser_v4.pdf` |
| StreamVGGT: Streaming Visual Geometry Transformer | (arXiv 2507.11539) | `framework.pdf`, `teaser_v2.pdf` |
| TPVFormer: Tri-Perspective View for 3D Semantic Occupancy | CVPR 2023 (arXiv 2302.07817) | `framework.pdf`, `teaser.pdf` |

## The single most useful finding

**These figures are PowerPoint files.** The fill colours are exactly the
Microsoft Office theme tint ladder, and the embedded font tables still carry
`SimSun`, `SimHei` and `Calibri` alongside `TimesNewRomanPSMT` — the residue of
a Chinese-locale PowerPoint install.

That matters for two reasons. First, if you want output that reads as
hand-made, use the colours the authors actually clicked; a "nicer" palette
reads as foreign immediately. Second, it explains why the `.pptx` export in
this skill is not a convenience feature — it puts the figure back in the tool
the community edits in.

Observed fills, by frequency across the corpus:

```
#92CDDC #C2E2EB #B7DDE8 #DBEEF3 #EBF5F8   Office Accent5 (aqua) at 40/60/80% lighter
#C5E0B4 #EBF1DF #C0D39A #E9EFDC           Accent3 / green at 40/60/80% lighter
#FFF2CC #FFE699 #FFD965 #FFC000 #BF9000   gold, lighter 80/60/40 and darker 25/50
#F8CBAD #FBE5D6 #ED7D31 #EA700D #C55A11   orange, same ladder
#D3C9DE #EEEAF2 #CCC2D9 #B4A7D6           Accent4 / purple
#F2DCDA #FFBFBF #C0504D #B1001C           Accent2 / rose
#F2F2F2 #E4E4E4 #D8D8D8 #BFBFBF #A5A5A5 #7F7F7F #595959   the Office grey ladder
```

Strokes are overwhelmingly `#000000` (1191 occurrences against 20 for the next
colour). Saturated colour appears on **arrows and label text**, not on outlines.

## Typography

| Property | Measured | Encoded as |
|---|---|---|
| Label font | `TimesNewRomanPSMT`, `HelveticaNeue`, `Arial-BoldMT` | `font: times` \| `helvetica` |
| Stage titles | bold italic serif, or bold sans | `TYPE["stage_title"]` = 7.8 pt bold italic |
| Label size on the page | 6.2 – 7.6 pt | `TYPE["node"]` = 7.0 pt |
| Sub/superscripts | ~0.72 × base | `SCRIPT_SCALE` |

Worked example: SparseWorld's `overview.pdf` has a native canvas of
934.08 × 434.76 pt and is included at `\linewidth` in a two-column AAAI paper,
i.e. 504 pt. The scale factor is 504 / 934.08 = **0.540**. Its 14 pt labels
therefore print at **7.6 pt**, and its 1.5 pt strokes at **0.81 pt**.

This is why the engine lays out in final points: the number in the spec is the
number on the page, with no mental arithmetic.

## Geometry

| Property | Measured | Encoded |
|---|---|---|
| Module box height | 21–28 pt native → 11–15 pt final | text + 2 × 4.2 pt |
| Horizontal text padding | box width − text width = 14 pt final | `node_padx` = 7.0 pt |
| Corner radius | small, ~2–3 pt final | `corner` = 2.6 pt |
| Module outline | 1.5 pt native → 0.81 pt final | `STROKE["flow"]` = 0.80 |
| Box outline | 1.25 pt native → 0.67 pt final | `STROKE["box"]` = 0.65 |
| Image hairline | 0.24–0.5 pt native | `STROKE["hairline"]` = 0.30 |
| Stage container | grey dashed, ~3.2/2.2 dash | `DASH["frame"]` |

The padding constant is worth checking yourself: `Temporal-Spatial MHSA` set in
7 pt Times measures 71.0 pt; the published box is 85 pt wide at final size.
85 − 71 = 14 = 2 × 7.0. The engine reproduces the box to within a rounding error.

## Recurring idioms

- **Stage columns.** Grey dashed rounded container per pipeline phase, with a
  bold italic serif title *above* the container, not inside it.
- **Tinted region inside a stage.** The repeated block gets a pale wash plus a
  dashed border in the *saturated* version of the same hue, and a `×L` badge in
  the top-right.
- **Colour-matched flow.** Arrows inside a stage take that stage's deep tint;
  arrows between stages are black. Label text for an entity is set in the same
  colour as that entity's arrow — that is the legend, done inline.
- **Extruded slabs** for query/token banks: front face plus a top and side face
  at 1.16 × and 0.90 × the fill lightness. Never a gradient.
- **Trapezoids** for encoders and decoders, narrow end pointing the way the
  dimensionality goes.
- **Chevrons** for memory reads and writes.
- **Real crops everywhere**: surround-view camera images, occupancy renders,
  point clouds, depth maps — embedded at hairline-outlined rectangles.
- **Loop and count badges** in italic: `×L`, `×N`, `×f`, set at 6.4 pt.

## What the corpus never does

No gradients. No drop shadows. No glow. No 3-D bevels. No icons of gears or
brains. No more than two type families in one figure. No text below ~6 pt. No
colour that is not either a pale Office tint, a saturated Office tint on an
arrow, or black.
