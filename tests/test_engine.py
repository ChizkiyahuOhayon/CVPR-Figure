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
from cvprfig import layout as L                                      # noqa: E402
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
    for _case in ('a: "Rocket \\U0001F680"', 'a: "\\u03bc x \\u00d7"',
                  'a: "line\\nbreak"', 'a: "tab\\there"', "a: 'it''s'",
                  'a: "quote \\" end"'):
        _py = real.safe_load(_case)["a"]
        miniyaml._pyyaml = None
        try:
            _mini = miniyaml.load(_case)["a"]
        finally:
            miniyaml._pyyaml = real
        check(_py == _mini, "escape parity for %s" % _case)
    y = miniyaml.load("a: off\nb: no\nc: true\nd: false\n")
    check(y["a"] == "off" and y["b"] == "no", "on/off/yes/no stay strings, so they work as ids")
    check(y["c"] is True and y["d"] is False, "true/false stay boolean")

section("parser equivalence")
if real is not None:
    for _name in ("pipeline-4stage", "teaser-comparison", "attention-tokens",
                  "streaming-worldmodel", "module-detail", "dual-branch",
                  "gated-module", "blindspot-teaser", "study-overview",
                  "factorial-2x2", "taxonomy",
             # v2, from the corpus scan
             "framework-with-io", "surroundview-pipeline", "trainable-frozen",
             "teacher-student", "wrapped-pipeline"):
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
check(style.resolve_color("core") == "#FFF2CC", "role -> pale fill")
check(style.resolve_color("core", ink=True) == "#BF9000", "role -> saturated ink")
check(style.resolve_color("gold.soft") == "#FFE699", "family.tint")
check(style.resolve_color("#abcdef") == "#ABCDEF", "hex passes through, normalised")

# -------------------------------------------------------------- templates
section("templates render and export")
TEMPLATES = ("pipeline-4stage", "teaser-comparison", "attention-tokens",
             "streaming-worldmodel", "module-detail", "dual-branch",
             "gated-module", "blindspot-teaser", "study-overview",
             "factorial-2x2", "taxonomy",
             # v2, from the corpus scan
             "framework-with-io", "surroundview-pipeline", "trainable-frozen",
             "teacher-student", "wrapped-pipeline")

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
check("stroke-width='0.8'" in _lw.tostring(), "a named weight reaches the SVG")

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
check("text-too-small" in codes, "catches sub-5 pt type")
check("inconsistent-role" in codes, "catches one concept drawn in two colours")
check("off-palette" in codes, "catches off-palette fills")
check("emoji" in codes, "catches emoji")
check(rep.counts()["error"] > 0, "reports errors on a bad figure")

for name in TEMPLATES:
    _, rep = V.audit(os.path.join(ROOT, "templates", name + ".yaml"))
    check(rep.counts()["error"] == 0, "%s passes the auditor with no errors" % name)



# ============================================================ v2: shapes
section("v2 shape vocabulary")
_v2 = Figure(miniyaml.load("""
figure: {id: v2, venue: cvpr, width: double}
layout: row
panels:
  - id: p
    body:
      - row:
          gap: 8
          align: center
          body:
            - {id: cam, shape: cameraring, cell: 24}
            - {id: vox, shape: voxelgrid, grid: 3, side: 28, role: core}
            - {id: fm, shape: planestack, n: 4, w: 20, h: 26, role: attention}
            - {id: gs, shape: gaussians, n: 6, w: 46, h: 28, seed: 3}
            - {id: mt, shape: marker, kind: trainable, d: 8}
            - {id: mf, shape: marker, kind: frozen, d: 8}
            - {id: ig, shape: imagegrid, rows: 2, cols: 3, cell: 20}
            - {id: ln, shape: lane, text: "flow", w: 54, h: 16}
"""))
_svg = _v2.tostring()
check("<ellipse" in _svg, "gaussians emit ellipses")
check(_svg.count("<path") >= 2, "markers emit vector paths, not emoji")
for _sid in ("cam", "vox", "fm", "gs", "mt", "mf", "ig", "ln"):
    check(_sid in {i.id for i in L.walk(_v2.items)}, "%s is laid out" % _sid)
_, _rep = V.audit({"figure": {"id": "v2", "venue": "cvpr", "width": "double"},
                   "panels": [{"id": "p", "body": [{"id": "m", "shape": "marker",
                                                    "kind": "trainable", "d": 8}]}]})
check(_rep.counts()["error"] == 0, "a vector marker does not trip the emoji check")

section("v2 markup escaping")
check(T.parse_runs(r"kernel\_size")[0][0] == "kernel_size", "backslash escapes _")
check(T.parse_runs(r"a\*b")[0][0] == "a*b", "backslash escapes *")
check(T.parse_runs("x_i")[1][3] == -1, "unescaped _ still subscripts")

section("v2 image sizing")
import tempfile as _tf, struct as _st, zlib as _zl
def _png(path, w, h):
    def chunk(t, d):
        return (_st.pack(">I", len(d)) + t + d
                + _st.pack(">I", _zl.crc32(t + d) & 0xFFFFFFFF))
    ihdr = _st.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    raw = b"".join(b"\x00" + b"\x00\x00\x00" * w for _ in range(h))
    open(path, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
                           + chunk(b"IDAT", _zl.compress(raw)) + chunk(b"IEND", b""))
_tmp = _tf.mkdtemp()
_p = os.path.join(_tmp, "wide.png")
_png(_p, 64, 16)
from cvprfig import imgsize as _IS
check(_IS.size(_p) == (64, 16), "png header is read")
check(abs(_IS.aspect(_p) - 4.0) < 1e-6, "aspect comes from the file")
_fig = Figure(miniyaml.load("""
figure: {id: im, venue: cvpr, width: double}
layout: row
panels: [{id: p, body: [{id: pic, shape: image, w: 80, src: wide.png}]}]
"""), base=_tmp)
_pic = {i.id: i for i in L.walk(_fig.items)}["pic"]
check(abs(_pic.h - 20.0) < 0.5, "height follows the real aspect (80/4 = 20)")
check("data:image/png;base64" in _fig.tostring(), "the raster is embedded, not linked")

# ============================================================ v2: code2fig
section("v2 code to figure")
from cvprfig.code2fig import torchscan as _TS, mmconfig as _MC, emit as _EM
_src = os.path.join(_tmp, "m.py")
_MODEL_SRC = "\n".join([
    "import torch.nn as nn",
    "class Net(nn.Module):",
    "    def __init__(self):",
    "        self.backbone = nn.Conv2d(3, 64)",
    "        self.neck = nn.Sequential(nn.Conv2d(64, 128), nn.ReLU())",
    "        self.ctx_head = nn.Linear(128, 10)",
    "        self.depth_head = nn.Linear(128, 1)",
    "        self.dropout = nn.Dropout(0.1)",
    "        self.loss = nn.CrossEntropyLoss()",
    "    def forward(self, x):",
    "        f = self.backbone(x)",
    "        f = self.neck(f)",
    "        a = self.ctx_head(f)",
    "        b = self.depth_head(f)",
    "        return a, b",
])
open(_src, "w").write(_MODEL_SRC)
_g, _name, _all = _TS.build([_src])
_ids = {n.id for n in _g.nodes}
check(_name == "Net", "picks the model class")
check("backbone" in _ids and "neck" in _ids, "submodules become nodes")
check("ctx_head" in _ids and "depth_head" in _ids, "both branches survive")
check("dropout" not in _ids, "plumbing modules are pruned")
check("loss" not in _ids, "loss is dropped unless asked for")
check(_g.get("backbone").role == "backbone", "role inferred from the name")
check(("backbone", "neck", None) in _g.edges, "dataflow edge recovered from forward")
check(len(_g.topo_layers()) >= 3, "the graph layers left to right")

_cfg = os.path.join(_tmp, "cfg.py")
_CFG_SRC = "\n".join([
    "model = dict(",
    "    type='Detector',",
    "    img_backbone=dict(type='ResNet', depth=50, out_channels=256),",
    "    img_neck=dict(type='FPN', in_channels=256, out_channels=128),",
    "    bbox_head=dict(type='Head', num_classes=10),",
    "    train_cfg=dict(lr=0.1))",
])
open(_cfg, "w").write(_CFG_SRC)
_g2, _n2 = _MC.build(_cfg)
_ids2 = {n.id for n in _g2.nodes}
check(_n2 == "Detector", "config type is the title")
check({"img_backbone", "img_neck", "bbox_head"} <= _ids2, "config stages become nodes")
check("train_cfg" not in _ids2, "train_cfg is skipped")
check("depth 50" in (_g2.get("img_backbone").note or ""), "channel counts are captured")

_spec, _note = _EM.fit(_g2, venue="cvpr", width="double")
check(Figure(_spec).fit_scale >= 0.94, "the emitted draft fits its column")
_, _r2 = V.audit(_spec)
check(_r2.counts()["error"] == 0, "the emitted draft passes the auditor")

section("v2 recalibrated constants")
check(style.MIN_RENDERED_PT == 5.0, "type floor is the corpus 29th percentile")
check(style.STROKE["box"] == 0.36, "box stroke is the corpus mode")
check(style.FAMILIES["blue"][1] == "#DEEBF7", "blue.light is Office Accent 5 Lighter 80%")
from cvprfig import palettes as _P
check(_P.DRAWIO["green"] == ("#D5E8D4", "#82B366"), "draw.io pairs are kept whole")
check(len(_P.TAB10) == 10, "tab10 is available for plot panels")

print("\n%s  (%d failure%s)" % ("FAILED" if FAILED else "ALL PASSED",
                                len(FAILED), "" if len(FAILED) == 1 else "s"))
sys.exit(1 if FAILED else 0)
