# The "does this look generated?" audit

Run `python3 scripts/validate.py spec.yaml --svg out/fig.svg` first — it
mechanises everything below that can be mechanised. Then do the eye pass, which
it cannot.

## Automated (the auditor)

| Code | Level | What it catches |
|---|---|---|
| `text-too-small` | error | anything under 5.0 pt at final size (the corpus 29th percentile) |
| `text-small` | warn | 5.0-5.6 pt -- legal, but have a reason |
| `text-small` | warning | 5.5–6.0 pt |
| `label-overflow` | error | text wider than its box |
| `node-overlap` | error | two siblings occupying the same space |
| `edge-crosses-node` | warning | an arrow routed through a third module |
| `bad-edge` | error | an edge naming a node that does not exist |
| `inconsistent-role` | error | one label drawn in two different fills |
| `off-palette` | warning | a colour outside the house tint ladders |
| `too-many-hues` | warning | more than 5 colour families |
| `stroke-zoo` | warning | more than 4 distinct line weights |
| `mixed-fonts` | warning | two type families in one figure |
| `label-verbose` | warning | a label over 6 words |
| `label-period` | warning | a label ending in a full stop |
| `emoji` | error | emoji or dingbats |
| `tall-figure` | warning | over the venue height budget |
| `gradient` / `shadow` | warning | gradients or filters in the SVG |
| `unconnected` | note | a module no arrow touches |

## By eye, at 100% on paper

Print it. Actually print it, or at minimum view the PDF at 100% zoom on a
laptop. Then:

1. **Squint.** What is darkest and largest? It must be the contribution. If a
   grey baseline box wins the squint test, the emphasis is inverted.
2. **Follow one input to one output** with a finger. If you lose the thread,
   the routing is wrong, not the reader.
3. **Cover the caption.** Can you still state the claim? If not, the figure is
   decoration around text.
4. **Convert to greyscale** (`magick fig.png -colorspace Gray g.png`). Anything
   that stops being distinguishable was relying on hue alone.
5. **Read every label out loud.** Any that is a sentence gets cut to a noun
   phrase.
6. **Check the count badges.** `×L`, `×N` — do they match the equations?
7. **Look at the four corners.** Empty corners are fine; a lonely orphan
   element in one is not.
8. **Compare against the neighbouring figure in the paper.** Same fills for the
   same concepts? Same title style? Same label size?

## The nine tells, in the order reviewers notice them

1. Saturated rainbow fills instead of a pale tint ladder.
2. Drop shadows or gradients.
3. Icons — gears, brains, clouds, robots, sparkles.
4. Sentence-length text inside boxes.
5. Every box exactly the same size in a perfect grid.
6. Curved, floating arrows that miss their ports.
7. No real data anywhere in the figure.
8. Colour used decoratively, so the same hue means different things in
   different places.
9. A caption that names the figure instead of stating a claim.

## Caption template

> **Figure N.** *<Claim in one sentence, present tense.>* <One sentence naming
> the parts, in the order the eye reads them.> <Optional: what the colours
> mean, if it is not obvious.>

Good: *"Figure 2. Sparse queries adapt their sampling range to scene depth, so
distant geometry is covered without a dense grid. Multi-view images are encoded
(left), refined by L range-adaptive layers (centre, yellow), and rolled forward
f steps by the state-conditioned forecaster (right, orange)."*

Bad: *"Figure 2. Overview of the proposed framework."*
