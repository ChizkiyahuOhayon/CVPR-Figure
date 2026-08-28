#!/usr/bin/env python3
"""Audit a figure spec (and its rendered SVG) before it goes into a paper.

    python3 validate.py spec.yaml [--svg out/fig.svg] [--json] [--strict]

Two classes of check:

  LEGIBILITY / CORRECTNESS -- things a reviewer will notice: sub-6 pt text,
  labels overflowing their boxes, arrows crossing modules, a figure so tall it
  eats the page, unreachable nodes.

  HOUSE STYLE -- the things that make a figure read as machine-generated:
  off-palette colours, too many hues, the same concept drawn in two colours,
  gradients, drop shadows, five different stroke weights, sentence-long labels.

Exit code is 0 when nothing above the failure threshold is reported.
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cvprfig import Figure, load_path, layout as L, style, text as T   # noqa: E402
from cvprfig import edges as edgemod                                    # noqa: E402

PALETTE = set()
for _fam in style.FAMILIES.values():
    PALETTE.update(c.upper() for c in _fam)
PALETTE.update({"#FFFFFF", "#000000", "#C00000", "#B1001C", "#953735", "#2E75B6",
                "#1F4E79", "#7F6000", "#C55A11", "#833C0C", "#4F6228", "#5F497A",
                "#632523", "#205867", "#1E524A", "#3F3151", "#76923C", "#31859B"})

MAX_LABEL_WORDS = 6
MAX_HUE_FAMILIES = 6      # corpus median is 5 distinct families, p75 is 9
MAX_STROKE_WEIGHTS = 4


class Report(object):
    def __init__(self):
        self.rows = []

    def add(self, level, code, msg, where=None):
        self.rows.append({"level": level, "code": code, "message": msg, "where": where})

    error = lambda self, *a: self.add("error", *a)
    warn = lambda self, *a: self.add("warning", *a)
    note = lambda self, *a: self.add("note", *a)

    def counts(self):
        c = {"error": 0, "warning": 0, "note": 0}
        for r in self.rows:
            c[r["level"]] += 1
        return c


# ------------------------------------------------------------- geometry
def _boxes(fig):
    out = []
    for it in L.walk(fig.items):
        if it.kind == "node" and it.spec.get("shape", "box") != "spacer":
            out.append(it)
    return out


def check_legibility(fig, rep):
    s = fig.scale
    for it in _boxes(fig):
        size = it.spec.get("_tsize")
        if not size or not it.spec.get("text"):
            continue
        eff = size * s
        if eff < style.MIN_RENDERED_PT:
            rep.error("text-too-small",
                      "%r renders at %.1f pt (floor %.1f pt)"
                      % (it.spec["text"][:32], eff, style.MIN_RENDERED_PT), it.id)
        elif eff < style.WARN_RENDERED_PT:
            rep.warn("text-small",
                     "%r renders at %.1f pt; reviewers print at 100%%"
                     % (it.spec["text"][:32], eff), it.id)
    if s < 0.85:
        rep.warn("overscaled",
                 "layout is %.0f%% wider than the column, so everything shrinks to %.0f%%"
                 % ((1 / s - 1) * 100, s * 100))


def check_overflow(fig, rep):
    for it in _boxes(fig):
        sp = it.spec
        if not sp.get("text") or sp.get("shape") in ("text", "note", "mathlabel",
                                                     "slab", "slabstack", "image",
                                                     "photo", "imagestack"):
            continue
        if sp.get("rotate"):
            continue
        w, h, lines = T.measure(sp["text"], sp["_tsize"], sp.get("_font", "times"),
                                sp.get("_bold", False), sp.get("_italic", False),
                                style.GEOM["line_gap"])
        if w > it.w - 2.0:
            rep.error("label-overflow",
                      "label %r is %.1f pt wide inside a %.1f pt box"
                      % (sp["text"][:32], w, it.w), it.id)
        if h > it.h - 1.0:
            rep.warn("label-tall", "label %r is taller than its box" % sp["text"][:32], it.id)


def _rects_overlap(a, b, tol=0.5):
    return (a.x + a.w - tol > b.x and b.x + b.w - tol > a.x
            and a.y + a.h - tol > b.y and b.y + b.h - tol > a.y)


def check_collisions(fig, rep):
    boxes = [b for b in _boxes(fig) if b.spec.get("shape") not in ("ellipsis",)]
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            if a.parent is not b.parent:
                continue
            if _rects_overlap(a, b, 1.0):
                rep.error("node-overlap", "%s and %s overlap"
                          % (a.id or "?", b.id or "?"), a.id)


def _seg_hits_rect(p, q, it, pad=1.0):
    x0, y0, x1, y1 = it.x + pad, it.y + pad, it.x + it.w - pad, it.y + it.h - pad
    if x1 <= x0 or y1 <= y0:
        return False
    if abs(p[1] - q[1]) < 0.05:                      # horizontal
        return y0 < p[1] < y1 and min(p[0], q[0]) < x1 and max(p[0], q[0]) > x0
    if abs(p[0] - q[0]) < 0.05:                      # vertical
        return x0 < p[0] < x1 and min(p[1], q[1]) < y1 and max(p[1], q[1]) > y0
    return False


def check_edges(fig, rep):
    boxes = _boxes(fig)
    for k, ed in enumerate(fig.spec.get("edges") or []):
        try:
            a, sa = edgemod.resolve_ref(ed["from"], fig.nodes)
            b, sb = edgemod.resolve_ref(ed["to"], fig.nodes)
        except KeyError as exc:
            rep.error("bad-edge", str(exc), "edge#%d" % k)
            continue
        if sa is None or sb is None:
            da, db = edgemod.auto_sides(a, b)
            sa = sa or da
            sb = sb or db
        pts = edgemod._dedup(edgemod._path_points(a, sa, b, sb, ed))
        for i in range(len(pts) - 1):
            for it in boxes:
                if it is a or it is b:
                    continue
                # Bare labels and measured whitespace are not obstacles: their
                # bounding boxes are wide but their ink is not, so a line
                # passing between two centred labels is fine.
                if it.spec.get("shape") in ("image", "photo", "imagestack",
                                            "text", "note", "mathlabel",
                                            "spacer", "ellipsis", "brace"):
                    continue
                if _seg_hits_rect(pts[i], pts[i + 1], it):
                    rep.warn("edge-crosses-node",
                             "edge %s -> %s passes through %s"
                             % (ed["from"], ed["to"], it.id or "?"), "edge#%d" % k)
                    break


def check_reachability(fig, rep):
    ids = set(n.id for n in _boxes(fig) if n.id)
    touched = set()
    for ed in (fig.spec.get("edges") or []):
        for key in ("from", "to"):
            ref = str(ed.get(key, ""))
            touched.add(ref.rsplit(".", 1)[0] if "." in ref else ref)
    orphans = sorted(i for i in ids - touched
                     if fig.nodes[i].spec.get("shape") not in
                     ("text", "note", "mathlabel", "ellipsis", "image", "photo",
                      "imagestack", "spacer", "brace"))
    if orphans:
        rep.note("unconnected",
                 "no edge touches: %s -- intentional, or a missing arrow?"
                 % ", ".join(orphans[:8]))


def check_shape(fig, rep):
    """Page economy.  A double-column figure taller than ~0.55 of its width
    swallows most of a page; a single-column one has far more vertical room."""
    w, h = fig.meta["canvas_pt"]
    single = w < 300
    limit = 1.45 if single else 0.58
    if h > w * limit:
        rep.warn("tall-figure",
                 "%.0f x %.0f pt exceeds the %s-column height budget (%.2f x width); "
                 "it will push text off the page"
                 % (w, h, "single" if single else "double", limit))
    if h < w * 0.12:
        rep.note("thin-figure", "%.0f x %.0f pt is a very flat band" % (w, h))


# --------------------------------------------------------------- style
def check_palette(fig, rep):
    used, families = {}, set()
    for it in _boxes(fig):
        sp = it.spec
        if sp.get("shape") in ("spacer", "text", "note", "mathlabel"):
            continue
        from cvprfig.shapes import node_colors
        fill, stroke, _ = node_colors(sp)
        for col in (fill, stroke):
            if not col or col == "none":
                continue
            c = col.upper()
            used[c] = used.get(c, 0) + 1
            if c not in PALETTE:
                rep.warn("off-palette",
                         "%s uses %s, which is not in the house tint ladder" % (it.id, c),
                         it.id)
        for fam, ladder in style.FAMILIES.items():
            if fill and fill.upper() in (x.upper() for x in ladder) and fam != "grey":
                families.add(fam)
    if len(families) > MAX_HUE_FAMILIES:
        rep.warn("too-many-hues",
                 "%d colour families in one figure (%s); the reference corpus "
                 "median is 5 and its 75th percentile is 9, so past %d colour "
                 "has stopped meaning anything"
                 % (len(families), ", ".join(sorted(families)), MAX_HUE_FAMILIES))
    return used


def check_real_content(fig, rep):
    """Framework figures in this literature show real data, not just boxes.

    57% of the architecture diagrams in the reference corpus embed at least
    one raster -- median 11 of them, about a quarter of the canvas -- almost
    always inputs on the left and predictions on the right.  A pure box
    diagram is legal, but for anything pipeline-sized it is worth a nudge.
    """
    nodes = _boxes(fig)
    if len(nodes) < 6:
        return
    slots = [it for it in nodes
             if it.spec.get("shape") in ("image", "photo", "imagestack",
                                         "imagegrid", "cameraring", "surroundview")]
    if not slots:
        rep.warn("no-real-content",
                 "%d boxes and no image slot; 57%% of framework figures in the "
                 "reference corpus show real inputs and predictions alongside the "
                 "architecture (shape: image / cameraring / imagegrid)" % len(nodes))
        return
    empty = [it.id for it in slots if not it.spec.get("src") and not it.spec.get("srcs")]
    if empty:
        rep.warn("empty-image-slot",
                 "%d image slot(s) have no `src`: %s -- these export as crossed "
                 "placeholder boxes" % (len(empty), ", ".join(empty[:5])))


def check_role_consistency(fig, rep):
    """One concept, one colour.

    A node may opt out with ``same_label_ok: true`` -- but only do that when
    two identically named things are *deliberately* contrasted (an online and
    a momentum copy, say).  Usually the right fix is to name them apart.
    """
    by_label = {}
    for it in _boxes(fig):
        sp = it.spec
        txt = (sp.get("text") or "").strip()
        if not txt or sp.get("shape") in ("text", "note", "mathlabel"):
            continue
        if sp.get("same_label_ok"):
            continue
        from cvprfig.shapes import node_colors
        fill, _, _ = node_colors(sp)
        by_label.setdefault(txt, set()).add(fill)
    for txt, fills in by_label.items():
        if len(fills) > 1:
            rep.error("inconsistent-role",
                      "%r is drawn in %d different fills (%s); one concept, one colour"
                      % (txt[:32], len(fills), ", ".join(sorted(fills))))


def check_labels(fig, rep):
    for it in _boxes(fig):
        sp = it.spec
        txt = (sp.get("text") or "").strip()
        if not txt or sp.get("shape") in ("text", "note", "mathlabel"):
            continue
        plain = re.sub(r"[*_^{}]", "", txt).replace("\n", " ")
        words = [w for w in plain.split() if w]
        if len(words) > MAX_LABEL_WORDS:
            rep.warn("label-verbose",
                     "%r is %d words; module labels are noun phrases, not sentences"
                     % (plain[:40], len(words)), it.id)
        if plain.endswith("."):
            rep.warn("label-period", "%r ends in a full stop" % plain[:40], it.id)
        if plain.isupper() and len(plain) > 4:
            rep.note("label-shouting", "%r is all caps" % plain[:40], it.id)
        if re.search(r"[\U0001F300-\U0001FAFF✀-➿]", plain):
            rep.error("emoji", "%r contains an emoji or dingbat" % plain[:40], it.id)


def check_strokes(fig, rep):
    weights = set()
    for it in _boxes(fig):
        weights.add(round(style.stroke_width(it.spec.get("lw"), style.STROKE["box"]), 2))
    for ed in (fig.spec.get("edges") or []):
        weights.add(round(style.stroke_width(ed.get("lw"), style.STROKE["flow"]), 2))
    if len(weights) > MAX_STROKE_WEIGHTS:
        rep.warn("stroke-zoo",
                 "%d distinct line weights (%s); pick a hairline, a box weight and a "
                 "flow weight and stop there"
                 % (len(weights), ", ".join(str(w) for w in sorted(weights))))


def check_fonts(fig, rep):
    fams = set()
    for it in _boxes(fig):
        fams.add(it.spec.get("_font", fig.font))
    if len(fams) > 1:
        rep.warn("mixed-fonts",
                 "the figure mixes %s; match the venue body font instead"
                 % " and ".join(sorted(fams)))


SVG_TELLS = [
    (r"<linearGradient|<radialGradient|url\(#grad", "gradient",
     "gradients read as slide decoration, not as a method figure"),
    (r"feDropShadow|filter\s*=|<filter", "shadow",
     "drop shadows and filters do not survive greyscale printing"),
    (r"font-family='[^']*(Comic|Papyrus|Impact)", "novelty-font", "novelty font"),
]


def check_svg(path, rep):
    if not path or not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as fh:
        blob = fh.read()
    for pat, code, msg in SVG_TELLS:
        if re.search(pat, blob):
            rep.warn(code, msg, os.path.basename(path))
    ops = [float(m) for m in re.findall(r"opacity='([0-9.]+)'", blob)]
    faint = [o for o in ops if 0 < o < 0.35]
    if faint:
        rep.note("faint-elements",
                 "%d element(s) below 35%% opacity may vanish in print" % len(faint))


# ------------------------------------------------------------------ main
def audit(spec_path, svg_path=None, base=None):
    """Audit a spec given as a path or as an already-loaded dict."""
    if isinstance(spec_path, dict):
        spec, base = spec_path, base or os.getcwd()
    else:
        spec = load_path(spec_path)
        base = base or os.path.dirname(os.path.abspath(spec_path))
    fig = Figure(spec, base=base)
    fig.render()
    rep = Report()
    for w in fig.warnings:
        rep.warn("engine", w)
    check_legibility(fig, rep)
    check_overflow(fig, rep)
    check_collisions(fig, rep)
    check_edges(fig, rep)
    check_reachability(fig, rep)
    check_shape(fig, rep)
    check_palette(fig, rep)
    check_real_content(fig, rep)
    check_role_consistency(fig, rep)
    check_labels(fig, rep)
    check_strokes(fig, rep)
    check_fonts(fig, rep)
    check_svg(svg_path, rep)
    return fig, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec")
    ap.add_argument("--svg", help="also audit a rendered SVG for gradients/shadows")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on warnings as well as errors")
    args = ap.parse_args(argv)

    fig, rep = audit(args.spec, args.svg)
    counts = rep.counts()
    if args.json:
        print(json.dumps({"counts": counts, "findings": rep.rows, "meta": fig.meta},
                         indent=2))
    else:
        icon = {"error": "FAIL", "warning": "WARN", "note": "note"}
        for r in rep.rows:
            where = " [%s]" % r["where"] if r["where"] else ""
            print("%-4s %-20s %s%s" % (icon[r["level"]], r["code"], r["message"], where))
        m = fig.meta
        print("\n%d error(s), %d warning(s), %d note(s) | %.0f x %.0f pt | %d nodes"
              % (counts["error"], counts["warning"], counts["note"],
                 m["canvas_pt"][0], m["canvas_pt"][1], m["node_count"]))
    if counts["error"]:
        return 1
    if args.strict and counts["warning"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
