"""House style for top-tier CV/ML conference pipeline figures.

Every constant here is a measurement, not a preference.  The corpus is 349
figure PDFs from the arXiv sources of 46 papers by three groups whose figures
this project is trying to sound like -- Tsinghua MARS, Wenzhao Zheng's group,
and Megvii -- plus the CVPR/ICCV/ICLR/AAAI sample used for v1.  Provenance and
the exact numbers are in references/corpus-report.md.

Two findings drive almost everything below.

1.  Not one figure in the corpus is drawn in TikZ.  All 292 are external
    PDF/PNG artwork placed with \\includegraphics, and the giveaway fonts
    (Calibri, Cambria Math, Segoe Print) say the tool was PowerPoint, Visio or
    diagrams.net.  So the palette is the Office/draw.io colour picker, and
    matching it is the difference between "drawn by a person" and "generated".

2.  The corpus uses colour freely inside boxes but hardly ever on their
    outlines.  Excluding the page backdrop, the median diagram has 87% of its
    filled box area in a saturated family -- so "keep it mostly grey" would be
    wrong advice.  What is consistent is the *number* of families (median 5,
    75th percentile 9) and the outlines: 45% of stroke length in the corpus is
    pure black and most of the rest is the grey ladder, with family-tinted
    outlines a clear minority.  Hence ``outline: ink`` is the default here.
"""

from . import palettes

# --------------------------------------------------------------------------
# Palette.  Backed by palettes.py, which holds the measured hex values.
# ``FAMILIES`` is kept as a plain dict of ladders for backwards compatibility
# with v1 specs and with code that indexes it directly.
# --------------------------------------------------------------------------
SYSTEM = "office"                      # office | drawio  (see palettes.py)

FAMILIES = dict(palettes.OFFICE)
FAMILIES["steel"] = FAMILIES["navy"]   # v1 alias
FAMILIES["rose"] = FAMILIES["red"]     # v1 alias
TINT_INDEX = {name: i for i, name in enumerate(palettes.RUNGS)}

INK = "#000000"          # 45% of stroke length in the corpus is pure black
MUTED_INK = "#595959"    # secondary captions, axis-style annotation
FRAME_GREY = "#A6A6A6"   # dashed stage containers
SOFT_FRAME = "#BFBFBF"
PAPER = "#FFFFFF"
SIGNAL = dict(palettes.SIGNAL)

# Semantic roles.  Keeping roles stable across every figure in a paper is the
# single strongest signal of a hand-crafted figure set.  Defaults favour the
# blue/green/orange triad, which carries 72% of the coloured area in the
# corpus; the rarer families are there for figures that genuinely need them.
ROLES = {
    "input":      ("grey",   "light"),
    "backbone":   ("navy",   "light"),
    "encoder":    ("green",  "light"),
    "decoder":    ("purple", "light"),
    "attention":  ("blue",   "soft"),
    "core":       ("gold",   "light"),      # the paper's contribution
    "temporal":   ("orange", "light"),
    "memory":     ("red",    "light"),
    "loss":       ("red",    "soft"),
    "output":     ("blue",   "light"),
    "baseline":   ("grey",   "light"),
    "ours":       ("gold",   "light"),
    "aux":        ("teal",   "light"),
    "frozen":     ("blue",   "pale"),
    "trainable":  ("orange", "pale"),
    "neutral":    ("grey",   "pale"),
}

# --------------------------------------------------------------------------
# Typography.  Sizes are in *final rendered points* -- the renderer scales the
# canvas so that these land verbatim on the printed page.
#
# Measured on 185 figures whose \\includegraphics width could be resolved, so
# the canvas-to-column scale factor is known (median 0.385).  The rendered
# glyph distribution is median 6.0 pt, quartiles 4.5 and 7.5 pt; the median
# per-figure *smallest* glyph is 5.4 pt.  So published practice runs a body
# tier around 6.5-7 pt with annotation dipping to 5.  Anything under 5 pt is
# in the bottom 29% and is where reviewers start complaining.
# --------------------------------------------------------------------------
FONT_STACKS = {
    "times":     "Times New Roman, Nimbus Roman, Liberation Serif, Times, serif",
    "helvetica": "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif",
    "arial":     "Arial, Liberation Sans, Helvetica, sans-serif",
}
# Serif is the corpus default: Times/Nimbus Roman/CMR carry 71% of characters
# in the diagram set, against 15% for Arial/Helvetica/Calibri.  Figures match
# the body font of the paper they sit in.
DEFAULT_FONT = "times"

TYPE = {
    "stage_title": {"size": 7.8, "weight": "bold", "style": "italic"},
    "panel_title": {"size": 7.6, "weight": "bold", "style": "normal"},
    "node":        {"size": 7.0, "weight": "normal", "style": "normal"},
    "node_strong": {"size": 7.0, "weight": "bold", "style": "normal"},
    "caption":     {"size": 6.5, "weight": "normal", "style": "normal"},
    "annot":       {"size": 6.0, "weight": "normal", "style": "italic"},
    "math":        {"size": 6.8, "weight": "normal", "style": "italic"},
    "tiny":        {"size": 5.4, "weight": "normal", "style": "normal"},
}
MIN_RENDERED_PT = 5.0     # p29 of the corpus; below this the auditor errors
WARN_RENDERED_PT = 5.6    # below this it warns

# --------------------------------------------------------------------------
# Strokes, in final rendered points.  v1 guessed these roughly 2x too heavy.
# Rendered-width modes in the corpus, after applying each figure's own scale
# factor: 0.19 pt (13%), 0.36 pt (24%), 0.45 pt (8%), 0.80 pt (5%), with a
# hairline shelf at 0.17-0.20.  Fine lines are the norm; a 1 pt outline is a
# deliberate shout.
# --------------------------------------------------------------------------
STROKE = {
    "hairline": 0.19,
    "thin":     0.28,
    "box":      0.36,
    "flow":     0.45,
    "frame":    0.36,
    "emphasis": 0.80,
    "shout":    1.10,
}
DASH = {
    "frame":   "3.2,2.2",
    "region":  "2.6,1.8",
    "flow":    "3.0,2.0",
    "thin":    "1.6,1.4",
    "dot":     "0.8,1.4",
}

# Geometry, in final rendered points unless noted.
GEOM = {
    "corner":        2.6,    # module box corner radius
    "frame_corner":  5.0,    # dashed stage container radius
    "node_padx":     7.0,    # horizontal text padding inside a box
    "node_pady":     4.2,    # vertical text padding
    "line_gap":      1.18,   # multiline leading multiplier
    "gap_x":         16.0,   # default horizontal gap between siblings
    "gap_y":         9.0,    # default vertical gap between siblings
    "stage_gap":     14.0,   # gap between stage containers
    "stage_pad":     8.0,    # padding inside a stage container
    "stage_title_gap": 4.0,  # gap between stage title baseline and container
    "arrow_len":     4.6,    # arrowhead length
    "arrow_wid":     3.2,    # arrowhead width
    "slab_depth":    3.6,    # 3D extrusion depth for tensor slabs
    "iso_dx":        3.2,    # isometric offset, x
    "iso_dy":        2.4,    # isometric offset, y
    "port_stub":     5.0,    # minimum straight run leaving a port
    "marker":        6.0,    # flame / snowflake marker box
}

# Column widths of the major venues, in points, at 100% \linewidth.
VENUE_WIDTH = {
    "cvpr":    {"single": 237.1, "double": 496.8},
    "iccv":    {"single": 237.1, "double": 496.8},
    "eccv":    {"single": 347.1, "double": 347.1},   # single-column LNCS
    "neurips": {"single": 397.5, "double": 397.5},
    "iclr":    {"single": 397.5, "double": 397.5},
    "icml":    {"single": 234.9, "double": 487.8},
    "aaai":    {"single": 238.5, "double": 504.0},
    "acl":     {"single": 219.1, "double": 455.2},
    "icra":    {"single": 252.0, "double": 516.0},   # ieeeconf
    "iros":    {"single": 252.0, "double": 516.0},
    "siggraph":{"single": 244.0, "double": 516.0},
    "generic": {"single": 240.0, "double": 500.0},
}

# Aspect ratios the corpus actually ships, width/height of the artwork.
# Median 1.82; 10th/90th percentile 0.96 and 3.35.  A double-column framework
# figure clusters near 3.0, a single-column module detail near 1.2.
ASPECT = {"teaser": 1.6, "framework": 2.6, "module": 1.3, "panel": 1.8}


def stroke_width(value, default=None):
    """Accept a number or one of the named weights (hairline/box/flow/...)."""
    if value is None:
        return default
    if isinstance(value, str):
        if value in STROKE:
            return STROKE[value]
        try:
            return float(value)
        except ValueError:
            return default
    return float(value)


def _fam_tint(role):
    return ROLES.get(role, ROLES["neutral"])


def fill_for(role, tint=None, system=None):
    fam, default = _fam_tint(role)
    return palettes.pick(fam, tint or default, system or SYSTEM)


def stroke_for(role, tint="strong", system=None):
    """Outline colour matched to the fill family."""
    fam, _ = _fam_tint(role)
    sys_ = system or SYSTEM
    if sys_ == "drawio":
        return palettes.outline(fam, "drawio")
    return palettes.pick(fam, tint, sys_)


def accent_for(role, system=None):
    """Saturated colour for arrows and text that must read as 'this entity'."""
    fam, _ = _fam_tint(role)
    return palettes.pick(fam, "deep", system or SYSTEM)


def resolve_color(value, default=None, ink=False, system=None):
    """Accept '#rrggbb', 'family.tint', 'family', a role name or a signal name.

    ``ink=True`` is used for strokes, arrows and coloured label text: a bare
    role or family name then resolves to the saturated end of that family
    instead of the pale fill, which is what published figures do when they
    colour a data path after the module it comes from.
    """
    if value is None:
        return default
    v = str(value).strip()
    if v.startswith("#"):
        return v.upper()
    if v in ("none", "None", "transparent"):
        return "none"
    sys_ = system or SYSTEM
    if "." in v:
        fam, tint = v.split(".", 1)
        if fam in FAMILIES and tint in TINT_INDEX:
            return FAMILIES[fam][TINT_INDEX[tint]]
        if fam in ("office", "drawio") and tint in FAMILIES:
            return palettes.pick(tint, "light", fam)
    if v in FAMILIES:
        return FAMILIES[v][TINT_INDEX["deep" if ink else "light"]]
    if v in ROLES:
        return accent_for(v, sys_) if ink else fill_for(v, None, sys_)
    if v in SIGNAL:
        return SIGNAL[v]
    named = {"ink": INK, "muted": MUTED_INK, "frame": FRAME_GREY,
             "softframe": SOFT_FRAME, "paper": PAPER,
             "white": "#FFFFFF", "black": "#000000", "darkred": "#B1001C"}
    if v in named:
        return named[v]
    return v
