#!/usr/bin/env python3
"""Audit a PPTX as it will be printed -- after a person has edited it.

    python3 audit_pptx.py fig.pptx [--width 496.8] [--spec spec.yaml | --ref fig.svg]
                          [--json] [--strict]

``validate.py`` audits the spec.  But once a figure has been handed over as a
PPTX and moved around in WPS or PowerPoint, the spec no longer describes what
ships: arrows have been re-dragged, subscripts lost in a copy-paste, legend
entries orphaned, type resized.  This reads the PPTX itself (any PPTX -- this
engine's, FigGenie's, or one drawn by hand) and checks:

  short-final-segment   a bent arrow whose last run is too short for WPS to aim
                        the head (it draws it at 45 degrees)
  unglued-arrow         an arrow touching a module without being glued to it,
                        so moving the module leaves the arrow behind
  text-too-small        any run under 6.0 pt at the final printed width
  lost-subscript        a sub/superscript that the spec (or the source SVG) has
                        and the PPTX no longer does; without a reference, runs
                        such as "z1:4" that look like a flattened subscript
  legend-orphan         a legend entry whose line style or swatch the figure
                        no longer uses
  image-low-ppi         an embedded picture under 300 ppi (warning under 600)
  raster-effect         shadow / glow / soft edge: LibreOffice rasterises these
                        at 96-350 ppi on export
  no-background         no slide background -- Keynote renders it black

Once a PPTX has been edited by hand it is the only source of the figure.
Export the paper PDF from it (export_pptx.py) and never regenerate it from
the spec, which would overwrite the edits.

Exit code 1 when an error is reported (or a warning, with --strict).
"""

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cvprfig import ooxml, style, text as T                        # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


class Report(object):
    def __init__(self):
        self.rows = []

    def add(self, level, code, msg, where=None):
        self.rows.append({"level": level, "code": code, "message": msg, "where": where})

    def counts(self):
        c = {"error": 0, "warning": 0, "note": 0}
        for r in self.rows:
            c[r["level"]] += 1
        return c


def _label(sh):
    t = ooxml.text_of(sh).replace("\n", " ").strip()
    return "%s%s" % (sh["name"] or sh["tag"], (" %r" % t[:30]) if t else "")


def _seglen(p, q):
    return ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5


def _heads(sh):
    """Head length (pt) per application for this line's arrowhead(s)."""
    ln = sh["line"]
    out = {}
    for end in ("head", "tail"):
        h = ln[end]
        if not h:
            continue
        preset = (h[1] if h[1] in ("sm", "med", "lg") else "med",
                  h[2] if h[2] in ("sm", "med", "lg") else "med")
        out[end] = {app: style.head_size(ln["w"], preset, app)[0]
                    for app in ("office", "wps", "keynote")}
    return out


# ------------------------------------------------------------------ checks
def check_arrows(slide, scale, rep):
    boxes = [sh for sh in slide.shapes if not sh.get("open_line")
             and sh["box"][2] > 3 and sh["box"][3] > 3]
    by_id = {sh["id"]: sh for sh in slide.shapes}
    unglued, freeform = [], []
    for sh in ooxml.lines_with_heads(slide):
        pts = sh["paths"][0][0] if sh["paths"] else []
        if len(pts) < 2:
            continue
        heads = _heads(sh)
        for end, hs in heads.items():
            if len(pts) < 3:
                continue          # a straight arrow cannot be mis-aimed
            seg = _seglen(pts[-2], pts[-1]) if end == "tail" else _seglen(pts[1], pts[0])
            if seg < 2.0 * hs["wps"]:
                rep.add("error", "short-final-segment",
                        "%s: the run after the last bend is %.1f pt, under two arrowheads "
                        "(%.1f pt in WPS); WPS draws this head at 45 degrees"
                        % (_label(sh), seg, 2 * hs["wps"]), sh["name"])
            elif seg < 2.0 * hs["office"]:
                rep.add("warning", "short-final-segment",
                        "%s: the run after the last bend is %.1f pt; PowerPoint draws this "
                        "head %.1f pt long and may tilt it" % (_label(sh), seg, hs["office"]),
                        sh["name"])
        # glue
        for which, p, cxn in (("start", pts[0], sh["st"]), ("end", pts[-1], sh["end"])):
            if cxn:
                if cxn[0] not in by_id:
                    rep.add("warning", "glue-broken",
                            "%s is glued at its %s to shape id %s, which no longer exists"
                            % (_label(sh), which, cxn[0]), sh["name"])
                continue
            touch = [b for b in boxes if _on_edge(p, b["box"])]
            if touch:
                unglued.append("%s (%s, at %s)" % (_label(sh), which, _label(touch[0])))
        if sh["tag"] != "cxnSp":
            freeform.append(_label(sh))
    if unglued:
        rep.add("warning", "unglued-arrow",
                "%d arrow end(s) touch a module without being glued to it, so moving the "
                "module leaves them behind: %s" % (len(unglued), "; ".join(unglued[:6])))
    if freeform:
        rep.add("note", "freeform-arrow",
                "%d arrow(s) are freeform shapes, not connectors; they cannot follow a moved "
                "module (%s)" % (len(freeform), "; ".join(freeform[:5])))


def _on_edge(p, box, tol=1.2):
    x, y, w, h = box
    inside_x = x - tol <= p[0] <= x + w + tol
    inside_y = y - tol <= p[1] <= y + h + tol
    if not (inside_x and inside_y):
        return False
    return (min(abs(p[0] - x), abs(p[0] - x - w)) <= tol or
            min(abs(p[1] - y), abs(p[1] - y - h)) <= tol)


def check_text(slide, scale, rep):
    sizes = []
    small = []
    fonts = {}
    for sh in slide.shapes:
        for r in sh.get("runs", []):
            if r.get("br") or not r["text"].strip():
                continue
            sz = r["size"] or 18.0          # PowerPoint's default
            eff = sz * scale * (0.67 if r["baseline"] else 1.0)
            sizes.append(eff)
            if r["font"]:
                fonts[r["font"]] = fonts.get(r["font"], 0) + len(r["text"])
            lim_e = style.MIN_RENDERED_PT * (0.67 if r["baseline"] else 1.0)
            lim_w = style.WARN_RENDERED_PT * (0.67 if r["baseline"] else 1.0)
            if eff < lim_e:
                small.append(("error", eff, sh, r))
            elif eff < lim_w:
                small.append(("warning", eff, sh, r))
    # one finding per shape, at its smallest base-line run
    per = {}
    for level, eff, sh, r in small:
        k = id(sh)
        if r["baseline"]:
            eff = eff / 0.67           # report in base-line terms
        cur = per.get(k)
        if cur is None or eff < cur[1]:
            per[k] = (level if cur is None or level == "error" else cur[0], eff, sh)
        elif level == "error":
            per[k] = ("error", cur[1], sh)
    errs = sorted((v for v in per.values() if v[0] == "error"), key=lambda v: v[1])
    warns = sorted((v for v in per.values() if v[0] != "error"), key=lambda v: v[1])
    for level, eff, sh in errs:
        rep.add("error", "text-too-small", "%s prints at %.1f pt (floor %.1f pt)"
                % (_label(sh), eff, style.MIN_RENDERED_PT), sh["name"])
    if warns:
        rep.add("warning", "text-small",
                "%d text shape(s) print between %.1f and %.1f pt (warning below %.1f pt): %s"
                % (len(warns), warns[0][1], warns[-1][1], style.WARN_RENDERED_PT,
                   "; ".join(_label(sh) for _, _, sh in warns[:8])
                   + (" ..." if len(warns) > 8 else "")))
    latin = [f for f in fonts if not re.search(r"Symbol|Math|Wingding|Dings", f, re.I)]
    if len(latin) > 2:
        rep.add("warning", "mixed-fonts",
                "%d text fonts in one figure: %s" % (len(latin), ", ".join(sorted(latin))))
    if sizes:
        sizes.sort()
        rep.add("note", "type-summary",
                "printed type: min %.1f, median %.1f, max %.1f pt over %d runs; fonts %s"
                % (sizes[0], sizes[len(sizes) // 2], sizes[-1], len(sizes),
                   ", ".join("%s" % f for f in sorted(fonts, key=fonts.get, reverse=True)[:3])))


# A flattened subscript: one letter (accent allowed) followed by digits,
# an index range, or a primed index -- z1:4, O5:10, d1, x_t written as xt is
# undetectable and needs --spec or --ref.
FLAT = re.compile(r"(?<![A-Za-z0-9])([A-Za-zÀ-ɏḀ-ỿ][̀-ͯ]?)"
                  r"(\d+(?::\d+)?)(?![A-Za-z0-9])")


def _expected_scripts(ref):
    """(base letter, script text, sign) for every sub/superscript the source has."""
    out = []
    if ref.lower().endswith(".svg"):
        import xml.etree.ElementTree as ET
        tree = ET.parse(ref)
        for el in tree.iter():
            tag = el.tag.split("}")[-1]
            if tag != "tspan":
                continue
            bs = el.get("baseline-shift") or ""
            style_ = el.get("style") or ""
            m = re.search(r"baseline-shift:\s*([^;]+)", style_)
            bs = bs or (m.group(1) if m else "")
            if not bs:
                continue
            sign = 1 if (bs.startswith("super") or (bs[:1].isdigit() and not bs.startswith("-"))) else -1
            if (el.text or "").strip():
                out.append(("", el.text.strip(), sign))
        return out
    from cvprfig import load_path, Figure
    spec = load_path(ref)
    fig = Figure(spec, base=os.path.dirname(os.path.abspath(ref)))
    from validate import text_elements
    for _, txt, _, _ in text_elements(fig):
        runs = T.parse_runs(txt)
        for k, (chars, b, i, sc) in enumerate(runs):
            if sc:
                base = runs[k - 1][0][-1:] if k else ""
                out.append((base, chars.strip(), 1 if sc > 0 else -1))
    return out


def check_scripts(slide, ref, rep):
    have = {}
    flat = []
    for sh in slide.shapes:
        # Adjacent runs on the base line print as one word, so "z" + "1:4"
        # that lost its baseline reads as "z1:4" just like a merged run.
        plain_text, chunks = [], []
        for r in sh.get("runs", []):
            if r.get("br") or r["baseline"]:
                if plain_text:
                    chunks.append("".join(plain_text))
                    plain_text = []
                if r["baseline"] and not r.get("br"):
                    key = (r["text"].strip(), 1 if r["baseline"] > 0 else -1)
                    have[key] = have.get(key, 0) + 1
                continue
            plain_text.append(r["text"])
        if plain_text:
            chunks.append("".join(plain_text))
        for chunk in chunks:
            for m in FLAT.finditer(chunk):
                flat.append((m.group(0), sh))
    if ref:
        want = _expected_scripts(ref)
        need = {}
        for base, txt, sign in want:
            need[(txt, sign)] = need.get((txt, sign), 0) + 1
        missing = []
        for key, n in need.items():
            got = have.get(key, 0)
            if got < n:
                missing.extend([key] * (n - got))
        if missing:
            rep.add("error", "lost-subscript",
                    "%d sub/superscript(s) in %s are plain text in the PPTX: %s"
                    % (len(missing), os.path.basename(ref),
                       ", ".join(("_" if s < 0 else "^") + t for t, s in missing[:12])))
    if flat:
        rep.add("error" if not ref else "warning", "lost-subscript",
                "%d run(s) look like flattened subscripts (%s); set them as subscripts "
                "(baseline -25000) or write them as $z_{1:4}$ in the spec"
                % (len(flat), ", ".join(sorted(set(t for t, _ in flat))[:12])))


def check_legend(slide, rep):
    """Find legend swatches -- a short horizontal line or a small filled box
    with a text label immediately to its right -- and check that the figure
    still uses each swatch's style somewhere else."""
    texts = [sh for sh in slide.shapes if ooxml.text_of(sh).strip()]
    lines = [sh for sh in slide.shapes if sh.get("open_line") and sh["paths"]
             and not sh["line"]["none"]]
    swatches = []
    for sh in lines + [s for s in slide.shapes if not s.get("open_line")]:
        x, y, w, h = sh["box"]
        is_line = sh.get("open_line")
        if is_line:
            pts = sh["paths"][0][0]
            if len(pts) != 2 or abs(pts[0][1] - pts[1][1]) > 0.3 or not (5 <= w <= 30):
                continue
        else:
            if not (4 <= w <= 18 and 2 <= h <= 10) or sh["fill"] in (None, "none"):
                continue
            if ooxml.text_of(sh).strip():
                continue
        ymid = y + h / 2.0
        for t in texts:
            tx, ty, tw, th = t["box"]
            if 0 <= tx - (x + w) <= 9 and abs(ty + th / 2.0 - ymid) <= 3.5 and tw < 200:
                swatches.append((sh, t))
                break
    in_group = [sw for sw in swatches if any("legend" in g.lower() for g in sw[0]["groups"])]
    if in_group:
        swatches = in_group           # the engine's (or a careful author's) legend group
    else:
        # A swatch floats: a line touching a module is an arrow, not a key.
        boxes = [b for b in slide.shapes if not b.get("open_line") and b["box"][2] > 3
                 and b["box"][3] > 3 and not ooxml.text_of(b).strip()]
        free = []
        for sh, t in swatches:
            if sh.get("open_line"):
                pts = sh["paths"][0][0]
                if any(_on_edge(p, b["box"], 0.8) for p in (pts[0], pts[-1]) for b in boxes
                       if b is not sh):
                    continue
            free.append((sh, t))
        # ... and a legend has entries stacked in a column or set in a row
        swatches = [(sh, t) for sh, t in free
                    if any(o is not sh and (abs(o["box"][0] - sh["box"][0]) < 1.0 or
                                            abs(o["box"][1] + o["box"][3] / 2.0
                                                - sh["box"][1] - sh["box"][3] / 2.0) < 1.0)
                           for o, _ in free)]
    if not swatches:
        return
    sw_ids = set(id(s) for s, _ in swatches)
    for sh, t in swatches:
        label = ooxml.text_of(t).strip()
        if sh.get("open_line"):
            key = (sh["line"]["color"], bool(sh["line"]["dash"]))
            used = [o for o in lines if id(o) not in sw_ids and
                    (o["line"]["color"], bool(o["line"]["dash"])) == key]
            if not used:
                rep.add("error", "legend-orphan",
                        "legend entry %r shows a %s %s line that no other line in the figure "
                        "uses -- the element it explained was deleted"
                        % (label, "dashed" if key[1] else "solid", key[0]), sh["name"])
        else:
            used = [o for o in slide.shapes if id(o) not in sw_ids and o.get("fill") == sh["fill"]
                    and o is not sh and o["box"][2] * o["box"][3] > sh["box"][2] * sh["box"][3]]
            if not used:
                rep.add("error", "legend-orphan",
                        "legend entry %r shows fill %s, which no module uses any more"
                        % (label, sh["fill"]), sh["name"])


def check_images(slide, scale, rep):
    for sh in slide.shapes:
        if sh["tag"] != "pic" or not sh.get("px"):
            continue
        l, t_, r, b = sh["crop"]
        px_w = sh["px"][0] * max(0.01, 1 - l - r)
        inches = sh["box"][2] * scale / 72.0
        if inches <= 0:
            continue
        ppi = px_w / inches
        if ppi < 300:
            rep.add("error", "image-low-ppi",
                    "%s (%s) is %.0f px across %.2f in -> %.0f ppi; it will print blurred"
                    % (sh["name"], os.path.basename(sh["media"]), px_w, inches, ppi), sh["name"])
        elif ppi < 600:
            rep.add("warning", "image-soft",
                    "%s (%s) prints at %.0f ppi (< 600)"
                    % (sh["name"], os.path.basename(sh["media"]), ppi), sh["name"])
        if sh.get("media_ext") in ("jpg", "jpeg"):
            rep.add("note", "jpeg-image",
                    "%s is a JPEG; occupancy renders and masks keep sharper edges as PNG"
                    % sh["name"], sh["name"])


def check_effects(slide, rep):
    eff = [sh for sh in slide.shapes if sh.get("effects")]
    if eff:
        kinds = sorted(set(k for sh in eff for k in sh["effects"]))
        rep.add("warning", "raster-effect",
                "%d shape(s) carry effects (%s); LibreOffice rasterises these at 96-350 ppi "
                "when exporting PDF, and they read as slide decoration: %s"
                % (len(eff), ", ".join(kinds), ", ".join(sh["name"] for sh in eff[:5])))


def check_canvas(slide, rep):
    W, H = slide.size
    if not slide.has_bg:
        rep.add("warning", "no-background",
                "the slide has no background fill; Keynote draws such slides on black")
    out = [sh for sh in slide.shapes if sh["box"][0] < -1 or sh["box"][1] < -1
           or sh["box"][0] + sh["box"][2] > W + 1 or sh["box"][1] + sh["box"][3] > H + 1]
    if out:
        rep.add("warning", "off-slide",
                "%d shape(s) extend past the slide and will be cropped on export: %s"
                % (len(out), ", ".join(_label(sh) for sh in out[:4])))


def check_head_sizes(slide, rep):
    seen = {}
    for sh in ooxml.lines_with_heads(slide):
        for end, hs in _heads(sh).items():
            h = sh["line"][end]
            key = (round(sh["line"]["w"], 2), h[1], h[2])
            seen[key] = hs
    if seen:
        parts = ["%.2f pt %s/%s: LibreOffice/PowerPoint %.1f, WPS %.1f, Keynote %.1f pt"
                 % (k[0], k[1], k[2], v["office"], v["wps"], v["keynote"])
                 for k, v in sorted(seen.items())[:4]]
        rep.add("note", "arrowhead-size",
                "arrowhead length per application -- " + "; ".join(parts))


def audit(path, width=None, ref=None):
    slide = ooxml.read(path)
    W = slide.size[0]
    rep = Report()
    if width is None and ref and not ref.lower().endswith(".svg"):
        from cvprfig import load_path, Figure
        fig = Figure(load_path(ref), base=os.path.dirname(os.path.abspath(ref)))
        width = fig.target
    if width is None:
        width = W
        rep.add("note", "width-assumed",
                "no --width given; assuming the slide prints at its own width (%.1f pt)" % W)
    scale = width / W if W else 1.0
    check_arrows(slide, scale, rep)
    check_text(slide, scale, rep)
    check_scripts(slide, ref, rep)
    check_legend(slide, rep)
    check_images(slide, scale, rep)
    check_effects(slide, rep)
    check_canvas(slide, rep)
    check_head_sizes(slide, rep)
    meta = {"slide_pt": [round(slide.size[0], 1), round(slide.size[1], 1)],
            "print_width_pt": round(width, 1), "scale": round(scale, 4),
            "shapes": len(slide.shapes)}
    return rep, meta


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx")
    ap.add_argument("--width", type=float,
                    help="printed width in pt (CVPR double column 496.8, single 237.1)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--spec", help="the cvpr-figure spec the PPTX came from")
    g.add_argument("--ref", help="a source SVG (e.g. FigGenie's) to compare subscripts with")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="fail on warnings too")
    args = ap.parse_args(argv)
    rep, meta = audit(args.pptx, args.width, args.spec or args.ref)
    c = rep.counts()
    if args.json:
        print(json.dumps({"counts": c, "findings": rep.rows, "meta": meta}, indent=2))
    else:
        icon = {"error": "FAIL", "warning": "WARN", "note": "note"}
        order = {"error": 0, "warning": 1, "note": 2}
        for r in sorted(rep.rows, key=lambda r: order[r["level"]]):
            print("%-4s %-20s %s" % (icon[r["level"]], r["code"], r["message"]))
        print("\n%d error(s), %d warning(s), %d note(s) | slide %.0f x %.0f pt printed at "
              "%.1f pt (x%.3f)" % (c["error"], c["warning"], c["note"], meta["slide_pt"][0],
                                   meta["slide_pt"][1], meta["print_width_pt"], meta["scale"]))
    if c["error"] or (args.strict and c["warning"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
