---
name: cvpr-figure
description: >-
  Create, revise and audit publication-grade pipeline, framework, teaser and module
  figures for CVPR, ICCV, ECCV, NeurIPS, ICLR, ICML, AAAI and ACL papers, and export
  them as Visio-editable .vsdx, PowerPoint-editable .pptx, plus SVG/PDF/PNG/EMF for
  LaTeX. Use for architecture diagrams, method overview figures, framework figures,
  pipeline diagrams, teaser/paradigm-comparison figures, attention and token diagrams,
  module zoom-ins, and 顶会论文配图、框架图、流程图、pipeline图、方法图、teaser图、
  网络结构图、模型架构图、科研绘图、论文示意图、Visio可编辑图. Works from a paper
  section, an abstract, a method description, or source code. Drives a declarative
  spec through a deterministic layout engine whose palette, typography and geometry
  were measured out of published CVPR/ICCV/AAAI figures, then audits the result
  against a checklist of the things that make a diagram look machine-generated.
  Do not use for data plots — bar charts, curves, heatmaps, scatter and ablation
  plots belong in matplotlib/seaborn; use those for quantitative results.
---

# Conference figure making — router

The engine is deterministic: you write **what goes where in what order**, and
`scripts/cvprfig` computes geometry in final rendered points. Do not hand-write
SVG coordinates and do not draw with an image model — both produce the generic
look this skill exists to prevent.

Read fragments from disk as directed below. Do not work from memory of this file.

## 0. Is this the right skill?

| Request | Route |
|---|---|
| architecture / pipeline / framework / teaser / module / attention diagram | continue here |
| bar chart, curve, heatmap, scatter, ablation plot, radar | not this skill — matplotlib/seaborn |
| a graphical abstract for a *biomedical* journal | not this skill |
| "make my figure Visio-editable" | continue here, jump to step 5 |

## 1. Always load

1. [static/core/stance.md](static/core/stance.md) — the non-negotiables and the
   list of tells this skill exists to suppress.
2. [static/core/contract.md](static/core/contract.md) — the seven questions to
   answer before drawing.

Then read [manifest.yaml](manifest.yaml) to see which further fragment the
current job needs.

## 2. Fill in the contract — do not skip

Answer, in your reply to the user, before writing any spec:

1. the one-sentence claim the figure must make;
2. the archetype;
3. which element is the contribution;
4. the semantic colour map;
5. venue and column width;
6. which real crops will fill the `image` slots.

If the user gave a paper section or code, derive 1–4 from it and state your
reading back in two or three lines so it can be corrected cheaply. Ask a
question only when two readings would produce materially different figures.

## 3. Pick an archetype and start from its template

Load [references/archetypes.md](references/archetypes.md), then copy the
matching file out of `templates/` and edit it. Starting from a blank spec
wastes effort and loses the proportions that make the archetype work.

**Architecture papers**

| Archetype | Template |
|---|---|
| paradigm comparison, page 1 | `templates/teaser-comparison.yaml` |
| multi-stage pipeline | `templates/pipeline-4stage.yaml` |
| block zoom-in with tensor shapes | `templates/module-detail.yaml` |
| token / attention pattern | `templates/attention-tokens.yaml` |
| recurrent or streaming system | `templates/streaming-worldmodel.yaml` |
| teacher–student, contrastive, EMA | `templates/dual-branch.yaml` |
| adapter / gate / "we froze the rest" | `templates/gated-module.yaml` |

**Analysis, evaluation and position papers** — the contribution is a
measurement or a distinction, not a network:

| Archetype | Template |
|---|---|
| what the standard metric cannot see, page 1 | `templates/blindspot-teaser.yaml` |
| the shape of an empirical study | `templates/study-overview.yaml` |
| a controlled 2 × 2 counterfactual or ablation | `templates/factorial-2x2.yaml` |
| where this work sits in the field | `templates/taxonomy.yaml` |

## 4. Write the spec

Load [references/spec-language.md](references/spec-language.md) for the full
grammar. Load [references/house-style.md](references/house-style.md) when you
need a colour, a size or a stroke weight, or when the user asks *why* something
looks the way it does. Load [references/case-studies.md](references/case-studies.md)
when the user names a paper whose figures they want to match.

Working rules:

- one `id` per element, named after the concept, not the position;
- `role:` before `fill:` — reach for an explicit colour only when no role fits;
- let the engine size boxes from their text; set `w`/`h` only for images,
  slabs and deliberate emphasis;
- `image` slots stay placeholders until the user supplies real crops — never
  invent an output render;
- keep labels to noun phrases of six words or fewer.

## 5. Render

```bash
python3 scripts/render.py spec.yaml -o out/overview -f svg,pdf,png,vsdx,pptx --dpi 600
```

`svg`, `vsdx` and `pptx` need no external tool. `pdf`, `png`, `tiff` and `emf`
use whichever of Inkscape, LibreOffice, rsvg-convert, cairosvg or ImageMagick
is installed; the command reports which one it used and skips cleanly if none
is. Rasters are taken from the PDF and the produced pixel size is checked
against `--dpi`, because some converters silently emit a 96 dpi screenshot.
Use 600 dpi for camera-ready, 1200 for a poster.

Read the report. It prints the canvas size, the node and edge counts, and — if
the layout is wider than the column — the **effective point size** after
scaling. Anything under 5.5 pt is a failure, not a warning to live with.

For editing by hand afterwards, load
[references/visio-workflow.md](references/visio-workflow.md). Generate the
drag-and-drop module palette once per project with:

```bash
python3 scripts/make_stencil.py -o templates/stencil -f vsdx,pptx
```

## 6. Audit — required before delivering

```bash
python3 scripts/validate.py spec.yaml --svg out/overview.svg
```

Fix every `FAIL`. Justify or fix every `WARN`. Then do the eye pass in
[references/anti-ai-checklist.md](references/anti-ai-checklist.md): squint
test, trace one path, cover the caption, convert to greyscale.

**Look at the rendered figure.** Convert a page to PNG and actually view it —
the auditor catches geometry and palette, not whether the figure communicates.

## 7. Deliver

Load [references/latex-integration.md](references/latex-integration.md) and
hand back:

- the `\begin{figure*}` block with `width=\linewidth`;
- a caption that states the claim, not the picture;
- the spec file alongside the PDF so the figure can be regenerated;
- an explicit list of the `image` slots still holding placeholders.

## Revising an existing figure

If the user has a figure they want matched or fixed:

1. read the source PDF's vector content to recover its real palette and sizes —
   `python3 - <<'EOF'` with `fitz` (PyMuPDF), as documented at the top of
   `references/house-style.md`;
2. write a spec that reproduces the structure;
3. change only what the user asked for;
4. audit and re-render.

Never silently restyle a figure the user is happy with.
