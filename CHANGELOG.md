# Changelog

## 2.0.0

Re-derived the whole house style from a much larger corpus, and added a path
from source code to a figure.

### The corpus

46 papers with complete arXiv sources from Tsinghua MARS, Wenzhao Zheng's group
and Megvii: 292 figure environments, 298 tables, 349 figure PDFs read with
PyMuPDF. Full numbers and method in
[`references/corpus-report.md`](references/corpus-report.md).

### Added

- `scripts/from_code.py` — draft a spec from a PyTorch `nn.Module` source tree
  or an mmengine/mmdet `model = dict(...)` config. Neither reader imports or
  executes anything; both parse with `ast`. Recovers submodules, dataflow from
  `forward`, parallel branches, residual joins and `×N` repeats; prunes
  norm/dropout plumbing; infers roles from names; colours parallel branches
  apart when role inference finds nothing.
- A **column-fitting ladder** in the emitter: a draft wider than its column is
  reshaped — captions dropped, names abbreviated, peripheral boxes shed, and
  only as a last resort folded into two bands — instead of being silently
  downscaled into 5 pt type. Each concession is reported.
- `cvprfig/palettes.py` — the three measured colour systems (Office theme,
  diagrams.net stock pairs, matplotlib `tab10`) kept whole rather than blended.
- `cvprfig/imgsize.py` — PNG/JPEG/GIF/PDF dimensions with no dependencies, so
  an `image` node inherits the real aspect ratio of the file it points at.
- Shapes: `voxelgrid`, `planestack`, `gaussians`, `cameraring`, `imagegrid`,
  `lane`, and `marker` — the flame/snowflake trainable/frozen convention as
  **vector paths**, not pasted emoji.
- Templates: `framework-with-io`, `surroundview-pipeline`, `trainable-frozen`,
  `teacher-student`, `wrapped-pipeline`.
- Auditor check `no-real-content` / `empty-image-slot`: 57% of framework
  diagrams in the corpus embed rasters, two thirds with inputs at the far left
  and predictions at the far right.
- Backslash escaping in the inline markup, so `kernel\_size` prints literally.
  Generated labels use it; hand-written specs now can too.
- `Figure.fit_scale`, available after layout without rendering.
- `validate.audit()` accepts a spec dict as well as a path.

### Changed — recalibrations, with the measurement

- **Stroke weights were about 2× too heavy.** Rendered-width modes in the
  corpus are 0.19 / 0.36 / 0.45 / 0.80 pt. `STROKE` moved from
  0.30/0.65/0.80/1.10 to 0.19/0.28/0.36/0.45/0.80.
- **Type floor.** `MIN_RENDERED_PT` 5.5 → 5.0, with a new 5.6 pt warning tier.
  The corpus puts 29% of glyphs below 5.0 pt and its median per-figure smallest
  glyph at 5.4, so 5.5 as a hard floor rejected half the reference set.
- **Palette.** Families now come from `palettes.py`; `blue` is the Office Blue
  Accent 5 ladder (`#DEEBF7 …`), `navy` is Accent 1, and `steel`/`rose` are
  kept as aliases so v1 specs still load. Role defaults shifted toward the
  blue/green/orange triad, which carries 72% of coloured area in the corpus.
- `MAX_HUE_FAMILIES` 5 → 6 (corpus median is 5, 75th percentile 9).
- `role: core` now resolves to `gold.light` rather than `gold.soft`.

### Removed

- A **colour-balance check** that would have warned when most of a figure's
  filled area was saturated. The "84% of fill area is neutral" number behind it
  counted the page-sized white backdrop as a fill. Measured the way an auditor
  measures — coloured share of *box* fill area — the corpus median is 87%
  coloured, so the check would have fired on nearly every published figure. The
  reasoning is recorded under "Rules that were tested and cut" in the corpus
  report so it does not get reintroduced from intuition.


All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] — 2026-08-22

### Added
- Six archetypes, taking the catalogue from five to eleven. Four of them cover
  analysis, evaluation and position papers, which have no architecture to draw
  but do have an argument: `blindspot-teaser`, `study-overview`,
  `factorial-2x2`, `taxonomy`. Two more cover common architecture patterns:
  `dual-branch` (teacher–student, contrastive, EMA) and `gated-module`
  (adapters, LoRA, FiLM, calibration heads).
- Shapes `framestrip` (observation windows, masks, missingness topologies),
  `dist` (a density glyph that says "a distribution" without faking data), and
  a proper curly `brace`. All three are supported by the SVG, `.vsdx` and
  `.pptx` writers.
- TIFF export.
- `same_label_ok` on a node, to silence the one-concept-one-colour audit where
  two identically named things are deliberately contrasted.

### Fixed
- **High-resolution raster export.** `--dpi` was silently ignored: LibreOffice's
  PNG filter emits a 96 dpi screenshot whatever you ask for, so a 600 dpi
  request produced a 317 px image. Rasters are now always taken from the PDF
  with a rasteriser that honours a density flag, and `render.py` verifies the
  produced pixel count against `--dpi` and warns when a converter cuts the
  corner.
- Named stroke weights (`lw: emphasis`) crashed on nodes and frames; they
  worked only on edges.
- A `group` nested inside a `row: {gap: …, body: […]}` lost its children.
  Every container body now accepts both the plain-list and the inline-options
  form.
- The auditor treated bare text labels as obstacles when checking whether an
  edge crosses a module, producing false positives for lines passing between
  two centred labels.

## [1.0.0] — 2026-08-22

### Added
- Initial release: the layout engine, the measured house style, five
  archetypes, the SVG / PDF / PNG / EMF / `.vsdx` / `.pptx` writers, the
  auditor, the Visio and PowerPoint module stencil, and the reference set.
