# Getting the figure into the paper at the right size

## The sizing rule

The engine lays out in **final rendered points**. `figure.venue` +
`figure.width` set the canvas to the exact column width of the venue, so:

```latex
\includegraphics[width=\linewidth]{figures/overview.pdf}
```

renders at 100%, and a `size: 7.0` label is 7.0 pt on the page.

Everything follows from that:

- Want the figure at 80% of the column? Set `width_frac: 0.8` in the spec and
  keep `width=\linewidth` in LaTeX. Do **not** write
  `width=0.8\linewidth` — that shrinks the type to 5.6 pt.
- Overflowing? The renderer scales the whole canvas down and *tells you the
  effective point size*. Under 5.5 pt it raises an error. The fix is to shorten
  labels, drop a stage, or split the figure — not to accept the shrink.

## Column widths, verified

| Venue | `\columnwidth` | `\textwidth` |
|---|---|---|
| CVPR / ICCV / WACV | 237.13 pt | 496.85 pt |
| ECCV (LNCS, single column) | 347.12 pt | 347.12 pt |
| NeurIPS | 397.48 pt | 397.48 pt |
| ICLR | 397.48 pt | 397.48 pt |
| ICML | 234.88 pt | 487.82 pt |
| AAAI | 238.49 pt | 504.00 pt |
| ACL / EMNLP | 219.08 pt | 455.24 pt |

Check yours rather than trusting the table: put
`\the\columnwidth\ \the\textwidth` in the document and compile.

## Float placement

```latex
% full width, top of page
\begin{figure*}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/overview.pdf}
  \caption{\textbf{Overview of X.} <claim>. <parts, left to right>.}
  \label{fig:overview}
\end{figure*}

% single column teaser, top of page 1
\begin{figure}[t]
  \centering
  \includegraphics[width=\linewidth]{figures/teaser.pdf}
  \caption{...}
  \label{fig:teaser}
\end{figure}
```

- Page-1 teasers go in `figure` at `[t]` and are referenced from the first
  paragraph of the introduction.
- Framework figures go in `figure*` at `[t]`, placed in the source *before* the
  method section that discusses them.
- Never `[H]`. Never `\vspace` hacks to force placement; fix the figure's
  height budget instead.

## Caption conventions

- Bold lead-in naming the figure, then the claim, then the parts.
- Define every badge (`×L`, `×N`) and every colour that carries meaning.
- Keep it under ~4 lines for a `figure`, ~5 for a `figure*`.
- Reference it as `Fig.~\ref{fig:overview}` (CVPR/ICCV style) or
  `Figure~\ref{...}` (NeurIPS/ICLR style) — follow the venue's own template.

## Making the PDF small

Embedded crops dominate the file size. Downsample before embedding:

```bash
magick input.png -resize 900x -quality 92 figures/crops/input.png
```

At 7 pt type, a crop displayed 100 pt wide needs about 900 px to stay sharp at
300 dpi in print; more is wasted bytes.

## Reproducibility

Keep the spec next to the figure and commit both:

```
figures/
  overview.pdf          <- what LaTeX includes
  overview.svg
  src/overview.yaml     <- the spec
  src/crops/*.png       <- the real data panels
```

Regenerate everything with one command:

```bash
for f in figures/src/*.yaml; do
  python3 scripts/render.py "$f" -o "figures/$(basename "${f%.yaml}")" -f svg,pdf
done
```

Camera-ready checks, in order:

1. `python3 scripts/validate.py spec.yaml --svg out/fig.svg --strict`
2. `pdffonts out/fig.pdf` — every font embedded.
3. View the compiled paper at 100% and read every label.
4. Print one page in greyscale.
