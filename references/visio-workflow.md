# Editing the output: Visio, PowerPoint, Illustrator

The SVG is the source of truth; everything else is generated from the same
laid-out geometry, so the shapes are native in each target rather than a
picture wrapped in a container.

```
python3 scripts/render.py spec.yaml -o out/overview -f svg,pdf,vsdx,pptx
```

| Format | Written by | Editable as |
|---|---|---|
| `.svg` | bundled | Illustrator, Inkscape, Figma, Affinity, browsers |
| `.pdf` | LibreOffice / Inkscape / rsvg / cairosvg, whichever is installed | LaTeX `\includegraphics`, Illustrator |
| `.png` | same, at `--dpi` (default 600) | slides, rebuttal images |
| `.emf` | LibreOffice / Inkscape | Word and Visio import, ungroups to shapes |
| `.vsdx` | bundled | **Visio, natively — no ungroup step** |
| `.pptx` | bundled | **PowerPoint, natively; pastes into Visio as shapes** |

Only `.svg`, `.vsdx` and `.pptx` need no external tool at all.

## Visio

Open `out/overview.vsdx`. Every module is a real Visio shape with its own
geometry, fill, line and character sections:

- click a box → the Format Shape pane shows the fill as `#FFE699`;
- drag a vertex → the geometry rows update, no ungroup needed;
- edit text in place → it keeps 7 pt Times New Roman;
- arrows are polylines with `EndArrow=4` (solid triangle), so you can drag
  their waypoints.

The page is sized to the figure plus a 0.35 in margin, in inches, with the
origin at the bottom-left — Visio's own convention.

**Raster panels.** `image` nodes export to `.vsdx` as labelled placeholder
rectangles rather than embedded bitmaps; the render report lists the source
files it skipped. Insert the real crops with *Insert → Pictures* and drop them
onto the placeholders. Use `.pptx` instead if you want the images embedded for
you.

**Round-trip.** Nothing reads a `.vsdx` back into a spec. Treat the spec as the
master while the structure is still moving, and switch to editing the `.vsdx`
only once the layout is settled.

## PowerPoint

Open `out/overview.pptx`. The slide is exactly the figure size, so what you see
is the printed size. Images are embedded. This is the closest match to how the
reference papers were actually produced.

To move a PowerPoint figure into Visio: select all on the slide, copy, and
paste into a Visio page — Office pastes as native shapes, not as a picture.

To get back to a PDF for LaTeX after hand-editing: *File → Export → PDF*, then
crop with `pdfcrop`, or select all → *Save as Picture* → PDF.

## A Visio-only workflow

If you would rather not touch YAML at all:

1. `python3 scripts/make_stencil.py -o templates/stencil -f vsdx`
2. Open `templates/stencil.vsdx` and keep it in a second window. It holds every
   shape in the vocabulary, pre-styled in every semantic role, the full tint
   ladder with hex values, and the line-weight set.
3. Copy modules out of it into your own page. They arrive with the house fill,
   outline, corner radius and 7 pt Times label already applied.

Visio's stencil format (`.vssx`) has no schema that can be written safely
without Visio itself, which is why the palette ships as an ordinary drawing.
In practice the workflow is identical.

## LaTeX

Always include the PDF, never the PNG:

```latex
\begin{figure*}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/overview.pdf}
  \caption{...}
  \label{fig:overview}
\end{figure*}
```

The canvas is already the venue's `\linewidth`, so `width=\linewidth` renders
the figure at 100% and the type sizes in the spec are the type sizes on the
page. If you scale it down in LaTeX, everything shrinks with it — re-render
with a smaller `width` instead.

## Fonts

The SVG names `Times New Roman, Nimbus Roman, Liberation Serif, Times, serif`
so it degrades sensibly on machines without the Microsoft fonts. Converters
substitute at their own discretion; if exact metrics matter, convert with
Inkscape (`--export-text-to-path`) or check the PDF with
`pdffonts out/overview.pdf`.
