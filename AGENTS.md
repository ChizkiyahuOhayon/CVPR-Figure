# CVPR-Figure — agent entry point

Portable instructions for agents that do not read `SKILL.md` frontmatter
(Codex, Cursor, Aider, plain API loops). Behaviour is identical; `SKILL.md` is
the same document with Claude Code routing metadata.

## What this is

A deterministic layout engine plus a house style for the framework, pipeline,
teaser and module figures in CVPR / ICCV / ECCV / NeurIPS / ICLR / ICML / AAAI /
ACL papers. Output is SVG, PDF, PNG, EMF, native Visio `.vsdx` and native
PowerPoint `.pptx`.

Pure Python standard library. No install step. Python 3.8+.

## Use it when

The user asks for an architecture diagram, method overview, framework figure,
pipeline diagram, teaser or paradigm-comparison figure, attention/token
diagram, module zoom-in, or an editable Visio/PowerPoint version of any of
those. Also: 论文框架图、流程图、方法图、网络结构图、teaser 图、Visio 可编辑图.

Do **not** use it for bar charts, curves, heatmaps, scatter plots or ablation
plots — those are matplotlib work.

## The loop

```bash
# 0. OPTIONAL -- if the user has the model code, draft from it instead of from
#    a reading of it.  Nothing is imported or executed; both readers use ast.
python3 scripts/from_code.py path/to/models/ --list
python3 scripts/from_code.py path/to/models/ --model MyNet -o figures/src/overview.yaml
python3 scripts/from_code.py configs/model.py --mm -o figures/src/overview.yaml
#    The output is a first draft.  Rename boxes to the paper's names, delete
#    what the paper does not discuss, attach real crops, mark the contribution
#    `role: core`.  See references/from-code.md for the known limits.

# 1. otherwise start from the closest archetype
cp templates/pipeline-4stage.yaml figures/src/overview.yaml
#   architecture: pipeline-4stage, module-detail, attention-tokens,
#                 streaming-worldmodel, dual-branch, gated-module,
#                 teaser-comparison
#   with real data: framework-with-io, surroundview-pipeline,
#                 trainable-frozen, teacher-student, wrapped-pipeline
#   analysis:     blindspot-teaser, study-overview, factorial-2x2, taxonomy

# 2. edit the spec (see references/spec-language.md)

# 3. render
python3 scripts/render.py figures/src/overview.yaml -o figures/overview \
        -f svg,pdf,png,vsdx,pptx --dpi 600

# 4. audit, and fix every FAIL
python3 scripts/validate.py figures/src/overview.yaml --svg figures/overview.svg

# 5. look at it
#    (convert to PNG and open it; the auditor cannot judge communication)

# 6. AFTER THE USER HAND-EDITS THE PPTX -- the PPTX is now the only source
python3 scripts/audit_pptx.py figures/overview.pptx --width 496.8 --spec figures/src/overview.yaml
python3 scripts/audit_pptx.py figures/overview.pptx --width 496.8 --fix figures/overview_fixed.pptx
#    (--fix: theme shadows off, detached subscripts re-shifted; writes a copy)
python3 scripts/export_pptx.py figures/overview.pptx --width 496.8   # lossless PDF + audit_pdf
```

## Read these, in this order

| File | When |
|---|---|
| `static/core/stance.md` | always, first |
| `static/core/contract.md` | always, before writing a spec |
| `references/archetypes.md` | choosing the figure's shape |
| `references/spec-language.md` | writing the spec |
| `references/house-style.md` | colours, sizes, stroke weights, and why |
| `references/case-studies.md` | matching a specific paper's figures |
| `references/symbols-and-captions.md` | writing labels with symbols, the symbol table, the caption |
| `references/anti-ai-checklist.md` | before delivering |
| `references/after-handover.md` | the user edited the PPTX, or exported a PDF from it |
| `references/app-compatibility.md` | WPS / Keynote / LibreOffice / PowerPoint differences |
| `references/visio-workflow.md` | hand-editing the output |
| `references/latex-integration.md` | putting it in the paper |

## Hard rules

1. Never hand-write SVG or PDF coordinates. Write a spec.
2. Never generate the figure with an image model.
3. Type sizes are final printed points. Body 7.5 pt, titles 8.5 pt. Under
   6.0 pt is a failure, 6.0-6.5 pt a warning, module names never under 7.0 pt.
   To enlarge, use `figure: {type_scale: ...}`, not hand edits.
4. Colour means something or it is grey. One concept, one colour, across the
   whole paper.
5. `image` slots stay placeholders until the user supplies real crops. Never
   invent an output render or a number.
6. Every symbol in the figure is defined in a label or in the caption; write
   variables as `$...$` maths. Every legend entry is used.
7. No web-UI colours (Tailwind / Material / Bootstrap); pale Office fills,
   black outlines.
8. Run the auditor before saying the figure is done -- and again on the PPTX
   and PDF after any hand edit. Never re-render a spec over an edited PPTX.

## Environment notes

- `.svg`, `.vsdx`, `.pptx` are written by bundled code — always available.
- `.pdf` / `.png` / `.tiff` / `.emf` need one of: Inkscape, LibreOffice
  (`soffice`), `rsvg-convert`, `cairosvg`, ImageMagick. `render.py` reports
  what it used, takes rasters from the PDF, and verifies the pixel size
  against `--dpi` (600 = camera-ready, 1200 = poster).
- PyYAML is used when importable; otherwise a bundled parser handles the same
  subset. Specs may also be written as JSON.
