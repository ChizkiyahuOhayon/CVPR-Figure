# Changelog

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
