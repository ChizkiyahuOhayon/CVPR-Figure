"""House style for top-tier CV/ML conference pipeline figures.

Every constant here was measured out of the vector content of published
CVPR/ICCV/ICLR/AAAI figures (see references/house-style.md for the audit).
The palette is the Microsoft Office theme tint ladder, because that is what
the authors of those figures actually clicked in PowerPoint/Visio -- matching
it is what makes generated output read as hand-drawn rather than synthetic.
"""

# --------------------------------------------------------------------------
# Palette.  Each family is a tint ladder: pale -> light -> mid -> strong -> deep.
# Fills come from the pale/light end, strokes and text accents from strong/deep.
# --------------------------------------------------------------------------
FAMILIES = {
    "blue":   ["#EBF5F8", "#DBEEF3", "#B7DDE8", "#92CDDC", "#4BACC6", "#31859B", "#205867"],
    "steel":  ["#EAF1FA", "#DDEBF7", "#BDD7EE", "#9DC3E6", "#5B9BD5", "#2E75B6", "#1F4E79"],
    "green":  ["#F3F7EC", "#EBF1DF", "#D7E4BD", "#C0D39A", "#9BBB59", "#76923C", "#4F6228"],
    "gold":   ["#FFF9E6", "#FFF2CC", "#FFE699", "#FFD965", "#FFC000", "#BF9000", "#7F6000"],
    "orange": ["#FDF0E6", "#FBE5D6", "#F8CBAD", "#F4B183", "#ED7D31", "#C55A11", "#833C0C"],
    "purple": ["#F5F3F8", "#EEEAF2", "#D3C9DE", "#B4A7D6", "#8064A2", "#5F497A", "#3F3151"],
    "rose":   ["#FCEFEF", "#F2DCDA", "#F5C6C4", "#EFA3A0", "#C0504D", "#953735", "#632523"],
    "teal":   ["#EAF6F3", "#D6EDE7", "#AEDCD0", "#86CAB9", "#3FA796", "#2E7D70", "#1E524A"],
    "grey":   ["#F7F7F7", "#F2F2F2", "#E4E4E4", "#D8D8D8", "#BFBFBF", "#A5A5A5", "#7F7F7F"],
}
TINT_INDEX = {"pale": 0, "light": 1, "soft": 2, "mid": 3, "strong": 4, "deep": 5, "dark": 6}

INK = "#000000"          # default text + hairline colour: real figures use pure black
MUTED_INK = "#595959"    # secondary captions, axis-style annotation
FRAME_GREY = "#A5A5A5"   # dashed stage containers
PAPER = "#FFFFFF"

# Semantic roles.  Keeping roles stable across every figure in a paper is the
# single strongest signal of a hand-crafted figure set.
ROLES = {
    "input":      ("grey",   "light"),
    "backbone":   ("steel",  "light"),
    "encoder":    ("green",  "light"),
    "decoder":    ("purple", "light"),
    "attention":  ("blue",   "soft"),
    "core":       ("gold",   "soft"),      # the paper's contribution
    "temporal":   ("orange", "light"),
    "memory":     ("rose",   "light"),
    "loss":       ("rose",   "soft"),
    "output":     ("blue",   "light"),
    "baseline":   ("grey",   "light"),
    "ours":       ("gold",   "soft"),
    "aux":        ("teal",   "light"),
    "neutral":    ("grey",   "pale"),
}

# --------------------------------------------------------------------------
# Typography.  Sizes are in *final rendered points* -- the renderer scales the
# canvas so that these land verbatim on the printed page.  Measured range in
# the reference corpus: 6.2-7.6 pt.  Below 6 pt reviewers cannot read it.
# --------------------------------------------------------------------------
FONT_STACKS = {
    "times":     "Times New Roman, Nimbus Roman, Liberation Serif, Times, serif",
    "helvetica": "Helvetica Neue, Helvetica, Arial, Liberation Sans, sans-serif",
}
TYPE = {
    "stage_title": {"size": 7.8, "weight": "bold", "style": "italic"},
    "panel_title": {"size": 7.8, "weight": "bold", "style": "normal"},
    "node":        {"size": 7.0, "weight": "normal", "style": "normal"},
    "node_strong": {"size": 7.0, "weight": "bold", "style": "normal"},
    "caption":     {"size": 6.6, "weight": "normal", "style": "normal"},
    "annot":       {"size": 6.4, "weight": "normal", "style": "italic"},
    "math":        {"size": 6.8, "weight": "normal", "style": "italic"},
    "tiny":        {"size": 5.6, "weight": "normal", "style": "normal"},
}
MIN_RENDERED_PT = 5.5

# --------------------------------------------------------------------------
# Strokes, in final rendered points.  Measured: 0.81 pt flow arrows,
# 0.67 pt box outlines, 0.27 pt hairlines.
# --------------------------------------------------------------------------
STROKE = {
    "hairline": 0.30,
    "box":      0.65,
    "flow":     0.80,
    "emphasis": 1.10,
    "frame":    0.55,
}
DASH = {
    "frame":   "3.2,2.2",
    "region":  "2.6,1.8",
    "flow":    "3.0,2.0",
    "thin":    "1.6,1.4",
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
    "port_stub":     5.0,    # minimum straight run leaving a port
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
    "siggraph":{"single": 244.0, "double": 516.0},
    "generic": {"single": 240.0, "double": 500.0},
}


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


def fill_for(role, tint=None):
    fam, default = ROLES.get(role, ROLES["neutral"])
    return FAMILIES[fam][TINT_INDEX[tint or default]]


def stroke_for(role, tint="strong"):
    """Outline colour matched to the fill family, two steps darker."""
    fam, _ = ROLES.get(role, ROLES["neutral"])
    return FAMILIES[fam][TINT_INDEX[tint]]


def accent_for(role):
    """Saturated colour for arrows and text that must read as 'this entity'."""
    fam, _ = ROLES.get(role, ROLES["neutral"])
    return FAMILIES[fam][TINT_INDEX["deep"]]


def resolve_color(value, default=None, ink=False):
    """Accept '#rrggbb', 'family.tint', 'family' or a role name.

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
    if "." in v:
        fam, tint = v.split(".", 1)
        if fam in FAMILIES and tint in TINT_INDEX:
            return FAMILIES[fam][TINT_INDEX[tint]]
    if v in FAMILIES:
        return FAMILIES[v][TINT_INDEX["deep" if ink else "light"]]
    if v in ROLES:
        return accent_for(v) if ink else fill_for(v)
    named = {"ink": INK, "muted": MUTED_INK, "frame": FRAME_GREY,
             "paper": PAPER, "white": "#FFFFFF", "black": "#000000",
             "red": "#C00000", "darkred": "#B1001C"}
    if v in named:
        return named[v]
    return v
