# Operating stance

## The problem this skill exists to solve

Machine-made framework figures fail in a recognisable way. They are not ugly;
they are *generic*. The tells, in the order reviewers notice them:

| Tell | What it looks like | What a real figure does |
|---|---|---|
| Decorative colour | Every box a different saturated hue, rainbow gradients | 3–5 pale tints, each meaning one thing |
| Depth effects | Drop shadows, bevels, glow, glassmorphism | Flat fills, one hairline outline |
| Even spacing everywhere | A perfect grid of identical rounded rectangles | Uneven, because the content is uneven |
| Prose in boxes | "This module aggregates multi-scale features" | "Feature Aggregation" |
| Free-floating arrows | Curves that start and end near, not on, a port | Orthogonal runs on port normals |
| No data | Pure abstraction, no picture of the actual output | Real crops of inputs and results, embedded |
| Icons | Gears, brains, clouds, robots, emoji | Tensors as slabs, encoders as trapezoids |
| A caption that repeats the picture | "Figure 1: The pipeline of our method." | A claim the figure demonstrates |

Every one of these is a *default* that has to be actively overridden. This
skill overrides them in the engine so they cannot come back by accident.

## Non-negotiables

1. **Design at final size.** All type sizes in a spec are in final rendered
   points on the printed page. 6.5–8 pt is the working range; below 5.0 pt the
   renderer refuses to stay silent. Never draw large and shrink.
2. **Colour carries meaning or it is grey.** A hue is spent on a semantic role
   — the contribution, a data stream, a stage — and that role keeps the same
   hue in every figure of the paper. Decoration gets `grey`.
3. **Fills are pale, ink is black.** Module fills come from the pale/light/soft
   end of a tint ladder. Outlines are black hairlines. Saturated tints appear
   only on arrows and coloured label text that must be traced back to an entity.
4. **One shape vocabulary.** Box, trapezoid, slab, token grid, cube, chevron,
   operator circle, image panel. Do not invent shapes.
5. **Arrows leave and enter along port normals** and turn at right angles. No
   free curves, no arrowheads landing on a corner.
6. **Labels are noun phrases**, ≤ 6 words, sentence case, no terminal period.
7. **Ground the abstraction.** A method figure that shows no real input crop
   and no real output crop is a block diagram, not a paper figure. Leave
   `image` slots for them and fill them with actual data.
8. **The figure must survive greyscale and 100% print.** No information may
   live only in hue; no stroke thinner than 0.3 pt.

## Default behaviour when the request is vague

- Assume the reader is a reviewer skimming at 100% zoom on a laptop.
- Assume the figure will be printed in black and white by at least one reviewer.
- Prefer one figure that answers one question over one figure that shows
  everything.
- If the method has a loop, show the loop once with a `×N` badge; do not unroll
  it unless unrolling *is* the contribution.
- When the user has an existing figure they like, match its colour roles rather
  than its exact geometry.

## What this skill will not do

- It will not fabricate quantitative results, ablation numbers, or output
  crops. Image slots stay as labelled placeholders until the user supplies real
  renders.
- It will not draw a figure claiming a mechanism the user has not described.
- It is not a chart tool. Bar charts, curves and tables belong in matplotlib.
