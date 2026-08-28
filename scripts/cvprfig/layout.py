"""Box-model layout solver.

The spec author states *semantics* (which modules live in which stage, in what
order); this module decides the geometry.  Two properties matter for making
output look hand-drawn rather than generated:

  * siblings in a vertical stack are snapped to a common width, and siblings in
    a horizontal run to a common height -- published figures are almost always
    on such a grid;
  * everything is placed on a shared point grid, so nothing is off by a
    fraction of a point.

Coordinates are SVG-style: x right, y down, units are final rendered points.
"""

from . import style, text as T

ROW_KINDS = ("row", "hstack")
COL_KINDS = ("col", "stack", "vstack")
BOXY = ("box", "roundbox", "sharpbox", "trapezoid", "invtrapezoid", "chevron",
        "parallelogram", "hexagon", "circle", "ellipse")


class Item(object):
    __slots__ = ("id", "kind", "spec", "children", "x", "y", "w", "h",
                 "parent", "depth", "is_leaf", "cap")

    def __init__(self, kind, spec, children=None):
        self.kind = kind
        self.spec = spec
        self.id = spec.get("id")
        self.children = children or []
        self.x = self.y = 0.0
        self.w = self.h = 0.0
        self.cap = 0.0
        self.parent = None
        self.depth = 0
        self.is_leaf = not self.children and kind == "node"

    # geometry helpers -----------------------------------------------------
    @property
    def cx(self):
        return self.x + self.w / 2.0

    @property
    def cy(self):
        return self.y + self.h / 2.0

    def port(self, side):
        side = (side or "c").lower()
        table = {
            "n": (self.cx, self.y), "s": (self.cx, self.y + self.h),
            "w": (self.x, self.cy), "e": (self.x + self.w, self.cy),
            "c": (self.cx, self.cy),
            "nw": (self.x, self.y), "ne": (self.x + self.w, self.y),
            "sw": (self.x, self.y + self.h), "se": (self.x + self.w, self.y + self.h),
            "nn": (self.cx, self.y), "ss": (self.cx, self.y + self.h),
        }
        return table.get(side, table["c"])

    def __repr__(self):
        return "<%s %s %.1f,%.1f %.1fx%.1f>" % (self.kind, self.id, self.x, self.y, self.w, self.h)


# ------------------------------------------------------------------ build
def build_tree(body, defaults, ctx, depth=0):
    """Turn nested spec dicts into Items."""
    items = []
    for raw in (body or []):
        items.append(build_item(raw, defaults, ctx, depth))
    return items


def build_item(raw, defaults, ctx, depth=0):
    if raw is None:
        raw = {}
    if isinstance(raw, str):
        raw = {"text": raw}
    if not isinstance(raw, dict):
        raise ValueError("layout item must be a mapping, got %r" % (raw,))

    for kinds, kind in ((ROW_KINDS, "row"), (COL_KINDS, "col")):
        for key in kinds:
            if key in raw:
                spec = dict(raw)
                body = _unwrap(spec.pop(key), spec, key)
                item = Item(kind, spec, build_tree(body, defaults, ctx, depth + 1))
                _finish_container(item, depth)
                return item
    if "group" in raw:
        spec = dict(raw["group"] or {})
        kind = "col"
        body = None
        for key in ("body", "stack", "col", "row", "items"):
            if key in spec:
                body = _unwrap(spec.pop(key), spec, key)
                kind = "row" if key == "row" else "col"
                break
        spec.setdefault("frame", "region")
        item = Item(kind, spec, build_tree(body or [], defaults, ctx, depth + 1))
        _finish_container(item, depth)
        return item
    if "body" in raw:
        spec = dict(raw)
        body = _unwrap(spec.pop("body"), spec, "body")
        kind = "row" if spec.pop("arrange", "col") == "row" else "col"
        item = Item(kind, spec, build_tree(body, defaults, ctx, depth + 1))
        _finish_container(item, depth)
        return item

    merged = dict(defaults.get("node", {}))
    merged.update(raw)
    item = Item("node", merged)
    item.depth = depth
    return item


def _unwrap(body, spec, key):
    """Accept either a plain list of children or ``{gap: 6, body: [...]}``.

    The inline-options form is much easier to write for one-off containers, so
    both spellings are allowed everywhere a container body is expected.
    """
    if isinstance(body, dict):
        inner = dict(body)
        out = (inner.pop("body", None) or inner.pop("items", None)
               or inner.pop(key, None) or [])
        spec.update(inner)
        return out
    return body or []


def _finish_container(item, depth):
    item.depth = depth
    for c in item.children:
        c.parent = item


# --------------------------------------------------------------- measuring
def measure_node(item, ctx):
    s = item.spec
    shape = s.get("shape", "box")
    font = s.get("font", ctx["font"])
    tkey = s.get("type", "node_strong" if s.get("strong") else "node")
    ts = dict(style.TYPE.get(tkey, style.TYPE["node"]))
    if s.get("size"):
        ts["size"] = float(s["size"])
    size = ts["size"]
    bold = s.get("bold", ts["weight"] == "bold")
    italic = s.get("italic", ts["style"] == "italic")

    label = s.get("text", "")
    maxw = s.get("wrap")
    if maxw:
        label = T.wrap(label, float(maxw), size, font, bold, italic)
        s["text"] = label
    tw, th, lines = T.measure(label, size, font, bold, italic, style.GEOM["line_gap"])
    s["_lines"] = lines
    s["_tsize"] = size
    s["_bold"] = bold
    s["_italic"] = italic
    s["_font"] = font

    padx = float(s.get("padx", style.GEOM["node_padx"]))
    pady = float(s.get("pady", style.GEOM["node_pady"]))

    if shape in ("text", "note", "mathlabel"):
        padx = float(s.get("padx", 0.0)); pady = float(s.get("pady", 0.0))
        w, h = tw + 2 * padx, th + 2 * pady
    elif shape == "tokengrid":
        cols = int(s.get("cols", 1)); rows = int(s.get("rows", 4))
        cell = float(s.get("cell", 8.0)); gap = float(s.get("cellgap", 2.4))
        w = cols * cell + (cols - 1) * gap
        h = rows * cell + (rows - 1) * gap
    elif shape in ("slab", "slabstack"):
        n = int(s.get("n", 1))
        cw = float(s.get("cell", 8.0)); ch = float(s.get("cellh", 30.0))
        gap = float(s.get("cellgap", 3.0)); dep = style.GEOM["slab_depth"]
        w = n * cw + (n - 1) * gap + dep
        h = ch + dep
    elif shape == "cube":
        side = float(s.get("side", 34.0))
        w = h = side + style.GEOM["slab_depth"] * 1.6
    elif shape in ("circleop", "op"):
        d = float(s.get("d", 10.0)); w = h = d
    elif shape in ("image", "imagestack", "photo"):
        # When a real asset is attached, let it set the aspect ratio.  A
        # squashed input frame is the loudest tell in a generated figure.
        asp = _src_aspect(s, ctx)
        if s.get("w") and not s.get("h"):
            w = float(s["w"]); h = w / asp
        elif s.get("h") and not s.get("w"):
            h = float(s["h"]); w = h * asp
        elif not s.get("w") and not s.get("h"):
            h = 38.0; w = h * asp
        else:
            w = float(s["w"]); h = float(s["h"])
    elif shape in ("imagegrid",):
        rows = int(s.get("rows", 1)); cols = int(s.get("cols", 3))
        gap = float(s.get("cellgap", 1.8))
        asp = _src_aspect(s, ctx)
        cw = float(s.get("cell", 34.0))
        w = cols * cw + (cols - 1) * gap
        h = rows * (cw / asp) + (rows - 1) * gap
    elif shape in ("cameraring", "surroundview"):
        gap = float(s.get("cellgap", 1.6))
        asp = _src_aspect(s, ctx, 1.6)
        cw = float(s.get("cell", 30.0))
        w = 3 * cw + 2 * gap
        h = 2 * (cw / asp) + gap
    elif shape in ("voxelgrid", "voxel"):
        side = float(s.get("side", 34.0))
        w = h = side + float(s.get("depth", style.GEOM["slab_depth"] * 1.7))
    elif shape in ("planestack", "featmaps"):
        n = int(s.get("n", 4))
        w = float(s.get("w", 26.0)) + (n - 1) * float(s.get("offset", 3.0))
        h = float(s.get("h", 34.0)) + (n - 1) * float(s.get("offset_y", 1.6))
    elif shape == "gaussians":
        w = float(s.get("w", 60.0)); h = float(s.get("h", 40.0))
    elif shape == "marker":
        d = float(s.get("d", style.GEOM["marker"])); w = h = d
    elif shape == "lane":
        w = float(s.get("w", max(tw + 2 * padx + 14.0, 60.0)))
        h = float(s.get("h", max(th + 2 * pady, 16.0)))
    elif shape in ("framestrip",):
        from .shapes import frame_mask
        mask = frame_mask(s)
        cell = float(s.get("cell", 5.0)); gap = float(s.get("cellgap", 1.2))
        w = len(mask) * cell + max(0, len(mask) - 1) * gap
        h = float(s.get("h", 13.0))
    elif shape in ("dist", "density"):
        w = float(s.get("w", 46.0)); h = float(s.get("h", 22.0))
    elif shape == "brace":
        if s.get("dir", "right") in ("right", "left"):
            w = float(s.get("depth", 3.0)); h = float(s.get("h", 30.0))
        else:
            w = float(s.get("w", 40.0)); h = float(s.get("depth", 3.0))
    elif shape == "ellipsis":
        w = float(s.get("w", 14.0)); h = float(s.get("h", 7.0))
    elif shape == "spacer":
        w = float(s.get("w", 10.0)); h = float(s.get("h", 10.0))
    elif shape in ("trapezoid", "invtrapezoid"):
        w = tw + 2 * padx + float(s.get("slantpad", 9.0))
        h = th + 2 * pady + float(s.get("hpad", 8.0))
    elif shape == "chevron":
        w = tw + 2 * padx + float(s.get("point", 7.0))
        h = th + 2 * pady
    elif shape in ("circle", "ellipse"):
        w = tw + 2.2 * padx; h = max(th + 2.2 * pady, w * 0.6)
    else:
        w = tw + 2 * padx
        h = th + 2 * pady

    if s.get("rotate") in (90, -90, 270):
        w, h = h, w

    item.w = max(float(s.get("w", w)), float(s.get("minw", 0)))
    item.h = max(float(s.get("h", h)), float(s.get("minh", 0)))
    # A caption hangs below the shape.  It counts towards the parent's
    # footprint but must not be swept into a uniform-height snap, or captioned
    # and uncaptioned siblings end up with different box heights.
    item.cap = 0.0
    cap = s.get("caption")
    if cap:
        cs = float(s.get("caption_size", style.TYPE["caption"]["size"]))
        cw, ch, clines = T.measure(cap, cs, font, False, s.get("caption_italic", False))
        s["_cap_lines"] = clines
        s["_cap_size"] = cs
        s["_cap_h"] = ch
        item.cap = ch + float(s.get("caption_gap", 3.0))
        item.h += item.cap
        item.w = max(item.w, cw)


def _src_aspect(s, ctx, default=1.33):
    """Aspect of the first attached asset, falling back to a sane default."""
    if s.get("aspect"):
        return float(s["aspect"])
    src = s.get("src") or (s.get("srcs") or [None])[0]
    if not src:
        return default
    import os
    from . import imgsize
    p = os.path.join(ctx.get("base", ""), src) if ctx.get("base") else src
    if not os.path.exists(p):
        return default
    return imgsize.aspect(p, default)


def measure(item, ctx):
    if item.kind == "node":
        measure_node(item, ctx)
        return
    for c in item.children:
        measure(c, ctx)

    s = item.spec
    pad = _pad(s, item)
    gap = float(s.get("gap", style.GEOM["gap_x" if item.kind == "row" else "gap_y"]))
    uniform = s.get("uniform", True)

    if item.kind == "row":
        if uniform:
            hs = [c.h - c.cap for c in item.children if _snappable(c)]
            if hs:
                top = max(hs)
                for c in item.children:
                    if _snappable(c) and c.spec.get("h") is None:
                        c.h = top + c.cap
        inner_w = sum(c.w for c in item.children) + gap * max(0, len(item.children) - 1)
        inner_h = max([c.h for c in item.children] or [0])
    else:
        if uniform:
            ws = [c.w for c in item.children if _snappable(c)]
            if ws:
                wide = max(ws)
                for c in item.children:
                    if _snappable(c) and c.spec.get("w") is None:
                        c.w = wide
        inner_w = max([c.w for c in item.children] or [0])
        inner_h = sum(c.h for c in item.children) + gap * max(0, len(item.children) - 1)

    title_h = _title_height(s, ctx)
    if s.get("title") and s.get("title_pos") == "inside-bottom":
        # the title sits inside the frame, so it eats bottom padding, not top
        pad = (pad[0], pad[1], pad[2] + title_h, pad[3])
        title_h = 0.0
    item.w = max(inner_w + pad[1] + pad[3], float(s.get("minw", 0)))
    item.h = max(inner_h + pad[0] + pad[2], float(s.get("minh", 0)))
    item.h += title_h
    if s.get("w"):
        item.w = float(s["w"])
    if s.get("h"):
        item.h = float(s["h"])
    s["_pad"] = pad
    s["_gap"] = gap
    s["_title_h"] = title_h


def _snappable(c):
    """Whether a sibling participates in the common-width / common-height snap.

    Module boxes do -- a stack of boxes at different widths is the clearest
    tell of a generated figure.  Containers and free-form marks do not: a
    nested stage should keep its own intrinsic size.
    """
    if c.kind != "node":
        return c.spec.get("snap", False)
    return c.spec.get("snap", c.spec.get("shape", "box") in BOXY)


def _pad(s, item):
    """(top, right, bottom, left)."""
    if s.get("frame") in (None, "none", False) and not s.get("fill"):
        base = float(s.get("pad", 0.0))
    else:
        base = float(s.get("pad", style.GEOM["stage_pad"]))
    p = [base] * 4
    for i, k in enumerate(("padt", "padr", "padb", "padl")):
        if s.get(k) is not None:
            p[i] = float(s[k])
    return p


def _title_height(s, ctx):
    if not s.get("title"):
        return 0.0
    pos = s.get("title_pos", "above")
    ts = style.TYPE["stage_title"]["size"]
    if pos in ("above", "below"):
        return 0.0  # lives outside the frame; handled by the parent band
    return ts * 1.05 + float(s.get("title_gap", 4.0))


# ---------------------------------------------------------------- placing
def place(item, x, y, ctx):
    item.x, item.y = round(x, 3), round(y, 3)
    if item.kind == "node":
        return
    s = item.spec
    pad = s.get("_pad", (0, 0, 0, 0))
    gap = s.get("_gap", 0.0)
    title_h = s.get("_title_h", 0.0)
    align = s.get("align", "center")

    ix = x + pad[3]
    iy = y + pad[0] + title_h
    iw = item.w - pad[1] - pad[3]
    ih = item.h - pad[0] - pad[2] - title_h

    if item.kind == "row":
        total = sum(c.w for c in item.children) + gap * max(0, len(item.children) - 1)
        justify = s.get("justify", "center")
        cx = ix + _offset(justify, iw, total)
        for c in item.children:
            cy = iy + _offset(align, ih, c.h)
            if c.spec.get("align") in ("start", "top"):
                cy = iy
            elif c.spec.get("align") in ("end", "bottom"):
                cy = iy + ih - c.h
            place(c, cx + float(c.spec.get("dx", 0)), cy + float(c.spec.get("dy", 0)), ctx)
            cx += c.w + gap
    else:
        total = sum(c.h for c in item.children) + gap * max(0, len(item.children) - 1)
        justify = s.get("justify", "center")
        cy = iy + _offset(justify, ih, total)
        for c in item.children:
            cx = ix + _offset(align, iw, c.w)
            if c.spec.get("align") in ("start", "left"):
                cx = ix
            elif c.spec.get("align") in ("end", "right"):
                cx = ix + iw - c.w
            place(c, cx + float(c.spec.get("dx", 0)), cy + float(c.spec.get("dy", 0)), ctx)
            cy += c.h + gap


def _offset(mode, avail, used):
    if mode in ("start", "left", "top"):
        return 0.0
    if mode in ("end", "right", "bottom"):
        return avail - used
    return (avail - used) / 2.0


def walk(items):
    for it in items:
        yield it
        for sub in walk(it.children):
            yield sub


def index(items):
    out = {}
    for it in walk(items):
        if it.id:
            out[it.id] = it
    return out
