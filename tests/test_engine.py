#!/usr/bin/env python3
"""Self-contained regression tests.  Run: python3 tests/test_engine.py"""

import os
import sys
import zipfile
import xml.dom.minidom as minidom

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from cvprfig import Figure, load_path, miniyaml, style, text as T   # noqa: E402
from cvprfig import edges as edgemod                                 # noqa: E402
from cvprfig import vsdx as vsdx_writer, pptx as pptx_writer         # noqa: E402

FAILED = []


def check(cond, msg):
    if cond:
        print("  ok   %s" % msg)
    else:
        print("  FAIL %s" % msg)
        FAILED.append(msg)


def section(name):
    print("\n== %s" % name)


# ---------------------------------------------------------------- metrics
section("text metrics")
w, h, lines = T.measure("Temporal-Spatial MHSA", 7.0)
check(abs(w - 70.97) < 0.1, "measured width matches the published box (71.0 pt)")
check(len(lines) == 1, "single line")
check(T.measure("a\nb", 7.0)[1] > 7.0, "multiline is taller than one line")
runs = T.parse_runs("Q^{t} **b** *i*")
check(any(r[3] > 0 for r in runs), "superscript parsed")
check(any(r[1] for r in runs), "bold parsed")
check(any(r[2] for r in runs), "italic parsed")
check(T.glyph_width("×", "times") == 564, "multiplication sign has a real width")

# ----------------------------------------------------------------- yaml
section("yaml fallback parser")
doc = """
figure: {id: t, venue: cvpr}
panels:
  - id: p
    title: "A"
    body:
      - {id: a, text: X}
      - row: [{id: b, text: Y}]
edges:
  - from: a
    to: b
"""
real = miniyaml._pyyaml
try:
    miniyaml._pyyaml = None
    d = miniyaml.load(doc)
finally:
    miniyaml._pyyaml = real
check(d["figure"]["id"] == "t", "nested inline mapping")
check(d["panels"][0]["body"][1]["row"][0]["id"] == "b", "nested flow sequence")
check(d["edges"][0]["from"] == "a", "block mapping inside a sequence")
if real is not None:
    y = miniyaml.load("a: off\nb: no\nc: true\nd: false\n")
    check(y["a"] == "off" and y["b"] == "no", "on/off/yes/no stay strings, so they work as ids")
    check(y["c"] is True and y["d"] is False, "true/false stay boolean")

section("parser equivalence")
if real is not None:
    for _name in ("pipeline-4stage", "teaser-comparison", "attention-tokens",
                  "streaming-worldmodel", "module-detail", "dual-branch",
                  "gated-module", "blindspot-teaser", "study-overview",
                  "factorial-2x2", "taxonomy"):
        _p = os.path.join(ROOT, "templates", _name + ".yaml")
        _src = open(_p, encoding="utf-8").read()
        _a = Figure(miniyaml.load(_src), base=os.path.join(ROOT, "templates")).tostring()
        miniyaml._pyyaml = None
        try:
            _b = Figure(miniyaml.load(_src), base=os.path.join(ROOT, "templates")).tostring()
        finally:
            miniyaml._pyyaml = real
        check(_a == _b, "%s renders identically with and without PyYAML" % _name)

# ---------------------------------------------------------------- layout
section("layout")
spec = {
    "figure": {"id": "t", "venue": "cvpr", "width": "double"},
    "panels": [{"id": "p", "frame": "dashed", "body": [
        {"id": "short", "text": "A"},
        {"id": "long", "text": "A much longer module label"},
    ]}],
}
fig = Figure(spec)
check(abs(fig.nodes["short"].w - fig.nodes["long"].w) < 0.01,
      "siblings in a column snap to a common width")
check(fig.nodes["short"].cx == fig.nodes["long"].cx, "and stay centred on one axis")

spec2 = {"figure": {"id": "t"}, "panels": [{"id": "p", "row": [
    {"id": "plain", "shape": "sharpbox", "w": 20, "h": 15},
    {"id": "capped", "shape": "sharpbox", "w": 20, "h": 15, "caption": "T"},
]}]}
f2 = Figure(spec2)
box_plain = f2.nodes["plain"].h - f2.nodes["plain"].cap
box_capped = f2.nodes["capped"].h - f2.nodes["capped"].cap
check(abs(box_plain - box_capped) < 0.01,
      "a caption does not change the box height under uniform snapping")

# --------------------------------------------------------------- routing
section("edge routing")
import types
a = types.SimpleNamespace(port=lambda s: (100.0, 50.0))
b = types.SimpleNamespace(port=lambda s: (40.0, 90.0))
pts = edgemod._dedup(edgemod._path_points(a, "s", b, "n", {}))
check(abs(pts[0][0] - pts[1][0]) < 0.01, "leaves a south port travelling straight down")
check(abs(pts[-1][0] - pts[-2][0]) < 0.01, "arrives at a north port travelling straight down")
pts = edgemod._dedup(edgemod._path_points(a, "e", b, "w", {}))
check(abs(pts[0][1] - pts[1][1]) < 0.01, "leaves an east port travelling horizontally")
straight = edgemod._dedup(edgemod._path_points(
    types.SimpleNamespace(port=lambda s: (0.0, 0.0)),
    "e",
    types.SimpleNamespace(port=lambda s: (50.0, 0.0)), "w", {}))
check(len(straight) == 2, "aligned facing ports give one straight run")

# ---------------------------------------------------------------- colour
section("colour resolution")
check(style.resolve_color("core") == "#FFE699", "role -> pale fill")
check(style.resolve_color("core", ink=True) == "#BF9000", "role -> saturated ink")
check(style.resolve_color("gold.soft") == "#FFE699", "family.tint")
check(style.resolve_color("#abcdef") == "#ABCDEF", "hex passes through, normalised")

# -------------------------------------------------------------- templates
section("templates render and export")
TEMPLATES = ("pipeline-4stage", "teaser-comparison", "attention-tokens",
             "streaming-worldmodel", "module-detail", "dual-branch",
             "gated-module", "blindspot-teaser", "study-overview",
             "factorial-2x2", "taxonomy")

for name in TEMPLATES:
    path = os.path.join(ROOT, "templates", name + ".yaml")
    fig = Figure(load_path(path), base=os.path.join(ROOT, "templates"))
    svg = fig.tostring()
    check(svg.startswith("<svg") and svg.rstrip().endswith("</svg>"), "%s renders SVG" % name)
    minidom.parseString(svg)
    check(fig.scale >= 0.85, "%s fits the column within 15%% (scale %.2f)" % (name, fig.scale))
    eff = style.TYPE["node"]["size"] * fig.scale
    check(eff >= style.MIN_RENDERED_PT, "%s type stays legible (%.1f pt)" % (name, eff))

out = os.path.join(HERE, "_out")
os.makedirs(out, exist_ok=True)

section("new shapes")
_shapes = {"figure": {"id": "sh", "venue": "cvpr", "width": "single"},
           "panels": [{"id": "p", "body": [
               {"id": "fs", "shape": "framestrip", "pattern": "..####..##", "cell": 5},
               {"id": "dg", "shape": "dist", "kind": "gauss", "w": 40, "h": 20},
               {"id": "dl", "shape": "dist", "kind": "laplace", "w": 40, "h": 20},
               {"id": "db", "shape": "dist", "kind": "bimodal", "w": 40, "h": 20},
               {"id": "br", "shape": "brace", "h": 24}]}]}
_f = Figure(_shapes)
_svg = _f.tostring()
minidom.parseString(_svg)
check(abs(_f.nodes["fs"].w - (10 * 5 + 9 * 1.2)) < 0.01,
      "framestrip width follows its pattern length")
check("<path" in _svg, "density glyph emits a path")
for _w, _ext in ((vsdx_writer, "vsdx"), (pptx_writer, "pptx")):
    _p = os.path.join(out, "shapes." + _ext)
    _w.write(_f, _p)
    _z = zipfile.ZipFile(_p)
    for _n in _z.namelist():
        if _n.endswith((".xml", ".rels")):
            minidom.parseString(_z.read(_n))
    check(True, "new shapes survive the %s writer" % _ext)

section("named stroke weights")
check(style.stroke_width("emphasis") == style.STROKE["emphasis"], "name resolves")
check(style.stroke_width(1.7) == 1.7, "number passes through")
check(style.stroke_width(None, 0.65) == 0.65, "default applies")
_lw = Figure({"figure": {"id": "lw"}, "panels": [{"id": "p", "body": [
    {"id": "a", "text": "x", "lw": "emphasis"}]}]})
check("stroke-width='1.1'" in _lw.tostring(), "a named weight reaches the SVG")

section("container body forms")
_forms = Figure({"figure": {"id": "cf"}, "panels": [{"id": "p", "body": [
    {"group": {"id": "g", "frame": "region",
               "row": {"gap": 5, "body": [
                   {"group": {"id": "inner", "body": [{"id": "leaf", "text": "L"}]}},
                   {"id": "sib", "text": "S"}]}}}]}]})
_forms.tostring()
check("inner" in _forms.nodes and "leaf" in _forms.nodes,
      "a group nested inside a row-with-options is addressable")

# ------------------------------------------------------------- containers
section("vsdx and pptx packaging")
fig = Figure(load_path(os.path.join(ROOT, "templates", "pipeline-4stage.yaml")),
             base=os.path.join(ROOT, "templates"))

vp = os.path.join(out, "t.vsdx")
info = vsdx_writer.write(fig, vp)
z = zipfile.ZipFile(vp)
for n in z.namelist():
    minidom.parseString(z.read(n))
check("visio/pages/page1.xml" in z.namelist(), "vsdx has a page part")
check("[Content_Types].xml" in z.namelist(), "vsdx has content types")
check(z.read("visio/pages/page1.xml").decode().count("<Shape ") > 100,
      "vsdx carries native shapes (%d)" % z.read("visio/pages/page1.xml").decode().count("<Shape "))
check(info["shapes"] > 100, "writer reports the shape count")

pp = os.path.join(out, "t.pptx")
info = pptx_writer.write(fig, pp)
z = zipfile.ZipFile(pp)
for n in z.namelist():
    if n.endswith(".xml") or n.endswith(".rels"):
        minidom.parseString(z.read(n))
check("ppt/slides/slide1.xml" in z.namelist(), "pptx has a slide")
check("ppt/theme/theme1.xml" in z.namelist(), "pptx has a theme")
slide = z.read("ppt/slides/slide1.xml").decode()
check(slide.count("<p:sp>") > 100, "pptx carries native shapes (%d)" % slide.count("<p:sp>"))

# --------------------------------------------------------------- auditor
section("auditor")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import validate as V   # noqa: E402

bad = os.path.join(out, "bad.yaml")
with open(bad, "w") as fh:
    fh.write("""
figure: {id: bad, venue: cvpr, width: double}
panels:
  - id: p
    body:
      - row: [{id: a, text: "Encoder", fill: "#FF00FF", size: 4.0},
              {id: b, text: "Encoder", fill: "#FFD965"},
              {id: c, text: "Rocket \\U0001F680"}]
edges: [{from: a, to: b}]
""")
_, rep = V.audit(bad)
codes = set(r["code"] for r in rep.rows)
check("text-too-small" in codes, "catches sub-5.5 pt type")
check("inconsistent-role" in codes, "catches one concept drawn in two colours")
check("off-palette" in codes, "catches off-palette fills")
check("emoji" in codes, "catches emoji")
check(rep.counts()["error"] > 0, "reports errors on a bad figure")

for name in TEMPLATES:
    _, rep = V.audit(os.path.join(ROOT, "templates", name + ".yaml"))
    check(rep.counts()["error"] == 0, "%s passes the auditor with no errors" % name)

print("\n%s  (%d failure%s)" % ("FAILED" if FAILED else "ALL PASSED",
                                len(FAILED), "" if len(FAILED) == 1 else "s"))
sys.exit(1 if FAILED else 0)
