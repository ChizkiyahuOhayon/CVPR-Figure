# After the hand-over: auditing the files that actually ship

`validate.py` audits the spec. But the files that end up in the paper are
usually not the ones the engine wrote: the PPTX is opened in WPS or
PowerPoint, boxes are nudged, an arrow is deleted, a label is retyped, and the
PDF in the paper is exported from that edited PPTX. Every failure seen in
practice happened in those two steps:

| Seen in a real submission | Where it happened |
|---|---|
| two arrowheads drawn at 45° | WPS, after bends were re-dragged |
| 20 subscripts silently flattened ("z1:4") | copy-paste between tools |
| a legend entry for an arrow that had been deleted | hand edit |
| a 4000 ppi crop exported at 298 ppi JPEG | LibreOffice default PDF export |
| type shrunk to 5.9 pt | hand edit, then the figure scaled into the column |

So the audit continues after the hand-over.

## Rule: once the PPTX is edited, it is the only source

From the moment a person edits the PPTX, the spec no longer describes the
figure. **Export the paper PDF from the PPTX. Do not re-run `render.py` on the
spec** — it would overwrite the edits. If the structure must change, change
the spec, re-render, and redo the hand edits deliberately.

## The loop

```bash
# 1. audit the edited PPTX at the width it will print
python3 scripts/audit_pptx.py figures/fig2.pptx --width 496.8 --spec figures/src/fig2.yaml

# 2. export losslessly (LibreOffice by default; --via keynote on a Mac)
python3 scripts/export_pptx.py figures/fig2.pptx -o figures/fig2.pdf --width 496.8

# 3. audit the PDF that LaTeX will include (export_pptx.py runs this itself)
python3 scripts/audit_pdf.py figures/fig2.pdf --width 496.8
```

Widths: CVPR/ICCV double 496.8, single 237.1; AAAI 504.0 / 238.5; ICML
487.8 / 234.9; NeurIPS/ICLR 397.5. Pass the width the figure is *included*
at; if LaTeX uses `width=0.8\linewidth`, pass 0.8 × the column.

## What `audit_pptx.py` checks

Works on any PPTX — this engine's, FigGenie's, or one drawn by hand.

| Code | Level | What it means, and the fix |
|---|---|---|
| `short-final-segment` | error | a bent arrow's last run is under two WPS arrowheads; WPS draws the head at 45°. Lengthen the last run (move the bend away from the target) or make the arrow straight |
| `short-final-segment` | warning | under two PowerPoint-size heads; may tilt in PowerPoint |
| `unglued-arrow` | warning | an arrow end touches a module without being glued; moving the module leaves it behind. Re-attach it to a connection point |
| `freeform-arrow` | note | arrows drawn as freeform shapes cannot follow a moved module at all |
| `glue-broken` | warning | an arrow glued to a shape that was deleted |
| `text-too-small` / `text-small` | error / warning | type under 6.0 / 6.5 pt at the printed width |
| `lost-subscript` | error | with `--spec` or `--ref fig.svg`: a sub/superscript the source has and the PPTX does not. Without a reference: runs such as `z1:4`, `d1` that look like flattened subscripts |
| `legend-orphan` | error | a legend swatch whose line style or fill nothing else in the figure uses |
| `image-low-ppi` / `image-soft` | error / warning | an embedded picture under 300 / 600 ppi at its printed size |
| `raster-effect` | warning | shadow, glow or soft edge; LibreOffice rasterises them at 96–350 ppi |
| `no-background` | warning | Keynote renders a slide with no background on black |
| `off-slide` | warning | content past the slide edge is cropped on export |
| `mixed-fonts` | warning | more than two text families |
| `arrowhead-size` | note | the head length each application will draw for this file |

## What `audit_pdf.py` checks

| Code | Level | What it means |
|---|---|---|
| `text-too-small` | error | glyph runs under 6.0 pt (scripts under 4.5 pt) |
| `image-low-ppi` / `image-soft` | error / warning | under 300 / 600 ppi |
| `image-jpeg` | warning | an image stored as JPEG/JPEG 2000 — re-export losslessly |
| `font-not-embedded` | error | the venue checker rejects this |
| `type3-font` | warning | bitmap fonts with visible glyphs |
| `page-is-raster` | error | the whole figure is one picture |

## Hand-editing without breaking it

- **Move modules, not arrow ends.** Arrows from v3 are glued connectors;
  drag the module and its arrows follow. Arrows with three or more bends are
  freeform (the render report lists them) and must be moved by hand.
- **Keep a bend away from the target.** The last run after a bend must be at
  least ~10 pt (2.5 arrowheads) or WPS mis-aims the head.
- **Change type size in the spec, not in the PPTX.** Text boxes are
  `wrap="none"` with auto-fit, so a label enlarged by hand grows out of its
  module. Use `figure: {type_scale: 1.1}` and re-render.
- **Deleting an element? Delete its legend entry.** The legend is one group
  with one sub-group per entry, so the swatch and its text go together; then
  re-centre the group.
- **Subscripts:** in WPS/PowerPoint use Format → Font → Subscript (baseline
  −25 %). Typing "z1:4" flat is what `lost-subscript` catches.
- **No effects.** Shadows and glows are rasterised by LibreOffice on export.

## Exporting from an application by hand

| Application | Setting |
|---|---|
| LibreOffice | use `export_pptx.py`; the default PDF filter downsamples to 300 dpi JPEG |
| WPS (macOS) | Export to PDF, picture quality **highest**; still stores JPEG — check with `audit_pdf.py` |
| Keynote | Export → PDF, Image Quality **Best** (or `export_pptx.py --via keynote`) |
| PowerPoint | Save As PDF, Options → uncheck "Bitmap text when fonts may not be embedded", Optimize for **Standard** |

See [app-compatibility.md](app-compatibility.md) for what each application
does differently.
