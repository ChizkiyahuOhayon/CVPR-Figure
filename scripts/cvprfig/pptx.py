"""Native PowerPoint (.pptx) writer.

The reference corpus was drawn in PowerPoint -- the residual SimSun/Calibri
font references in the published PDFs give it away -- so a .pptx export puts
the figure back in the tool the community actually edits in.  PowerPoint
shapes also paste straight into Visio as native shapes, which makes this the
most forgiving route onto a Visio canvas.

Every module is a real DrawingML shape with its own geometry, fill, outline
and text body; raster panels are embedded as pictures.
"""

import os
import zipfile
import xml.sax.saxutils as sx

from . import edges as edgemod, layout as L, shapes as SH, style, text as T

ESC = sx.escape
EMU = 12700.0          # EMU per point
A = "http://schemas.openxmlformats.org/drawingml/2006/main"


def e(v):
    return str(int(round(float(v) * EMU)))


def hx(c):
    return (c or "#000000").lstrip("#").upper()


class Deck(object):
    def __init__(self, fig):
        self.fig = fig
        fig.render()
        self.W, self.H = fig._viewbox
        self.shapes = []
        self.media = []          # (name, bytes)
        self.rels = []           # (rId, target)
        self.next_id = 2

    def sid(self):
        i = self.next_id
        self.next_id += 1
        return i

    def add_rel(self, target):
        rid = "rId%d" % (len(self.rels) + 2)
        self.rels.append((rid, target))
        return rid

    # ------------------------------------------------------------- pieces
    def _xfrm(self, x, y, w, h, rot=0):
        r = ' rot="%d"' % int(rot * 60000) if rot else ""
        return ('<a:xfrm%s><a:off x="%s" y="%s"/><a:ext cx="%s" cy="%s"/></a:xfrm>'
                % (r, e(x), e(y), e(max(w, 0.1)), e(max(h, 0.1))))

    def _fill(self, fill):
        if not fill or fill == "none":
            return "<a:noFill/>"
        return '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % hx(fill)

    def _ln(self, color, lw, dash=None, head=None, tail=None):
        if not color or color == "none" or not lw:
            return '<a:ln><a:noFill/></a:ln>'
        parts = ['<a:ln w="%s" cap="flat">' % e(lw),
                 '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>' % hx(color)]
        if dash:
            parts.append('<a:prstDash val="dash"/>')
        parts.append('<a:miter lim="800000"/>')
        if head:
            parts.append('<a:headEnd type="triangle" w="med" len="med"/>')
        if tail:
            parts.append('<a:tailEnd type="triangle" w="med" len="med"/>')
        parts.append('</a:ln>')
        return "".join(parts)

    def _txt(self, label, tstyle, anchor="ctr", wrap="none"):
        """Body text for a shape.  ``vert`` turns the whole text block, which
        is how PowerPoint renders a rotated label in a tall thin module."""
        if not label:
            return ('<p:txBody><a:bodyPr rtlCol="0" anchor="%s" wrap="none"'
                    ' lIns="0" tIns="0" rIns="0" bIns="0"/><a:lstStyle/>'
                    '<a:p><a:endParaRPr lang="en-US"/></a:p></p:txBody>' % anchor)
        ts = tstyle or {}
        vert = ts.get("vert", "")
        font = ts.get("font", "Times New Roman")
        sz = str(int(round(ts.get("size", 7.0) * 100)))
        col = hx(ts.get("color", "#000000"))
        b = ' b="1"' if ts.get("bold") else ""
        i = ' i="1"' if ts.get("italic") else ""
        algn = ts.get("align", "ctr")
        paras = []
        for line in str(label).split("\n"):
            runs = []
            for chars, rb, ri, script in T.parse_runs(line, ts.get("bold", False),
                                                      ts.get("italic", False)):
                if not chars:
                    continue
                base = ' baseline="%d"' % (30000 if script > 0 else -25000) if script else ""
                runs.append('<a:r><a:rPr lang="en-US" sz="%s"%s%s%s dirty="0">'
                            '<a:solidFill><a:srgbClr val="%s"/></a:solidFill>'
                            '<a:latin typeface="%s"/><a:cs typeface="%s"/></a:rPr>'
                            '<a:t>%s</a:t></a:r>'
                            % (sz, ' b="1"' if rb else "", ' i="1"' if ri else "",
                               base, col, font, font, ESC(chars)))
            if not runs:
                runs.append('<a:endParaRPr lang="en-US" sz="%s"/>' % sz)
            paras.append('<a:pPr algn="%s"/>%s' % (algn, "".join(runs)))
        body = "".join("<a:p>%s</a:p>" % p for p in paras)
        return ('<p:txBody><a:bodyPr rtlCol="0" anchor="%s" wrap="%s"%s lIns="0" tIns="0"'
                ' rIns="0" bIns="0"><a:spAutoFit/></a:bodyPr><a:lstStyle/>%s</p:txBody>'
                % (anchor, wrap, ' vert="%s"' % vert if vert else "", body))

    # ------------------------------------------------------------- shapes
    def sp(self, name, x, y, w, h, geom, fill, line, lw, dash=None, label=None,
           tstyle=None, rot=0):
        i = self.sid()
        self.shapes.append(
            '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s %d"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr>%s%s%s%s</p:spPr>%s</p:sp>'
            % (i, name, i, self._xfrm(x, y, w, h, rot), geom, self._fill(fill),
               self._ln(line, lw, dash), self._txt(label, tstyle)))
        return i

    def rect(self, x, y, w, h, fill, line, lw, dash=None, label=None, tstyle=None,
             rounded=True, name="Module"):
        if rounded and h > 0:
            adj = min(0.5, style.GEOM["corner"] / max(min(w, h), 1.0))
            geom = ('<a:prstGeom prst="roundRect"><a:avLst>'
                    '<a:gd name="adj" fmla="val %d"/></a:avLst></a:prstGeom>'
                    % int(adj * 100000))
        else:
            geom = '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        return self.sp(name, x, y, w, h, geom, fill, line, lw, dash, label, tstyle)

    def ellipse(self, x, y, w, h, fill, line, lw, label=None, tstyle=None, name="Oval"):
        return self.sp(name, x, y, w, h,
                       '<a:prstGeom prst="ellipse"><a:avLst/></a:prstGeom>',
                       fill, line, lw, None, label, tstyle)

    def polygon(self, points, fill, line, lw, dash=None, label=None, tstyle=None,
                closed=True, name="Shape"):
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
        w = max(x1 - x0, 0.01); h = max(y1 - y0, 0.01)
        cw, ch = e(w), e(h)
        path = ['<a:path w="%s" h="%s">' % (cw, ch)]
        for k, (px, py) in enumerate(points):
            tag = "moveTo" if k == 0 else "lnTo"
            path.append('<a:%s><a:pt x="%s" y="%s"/></a:%s>'
                        % (tag, e(px - x0), e(py - y0), tag))
        if closed:
            path.append("<a:close/>")
        path.append("</a:path>")
        geom = ('<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
                '<a:rect l="0" t="0" r="r" b="b"/><a:pathLst>%s</a:pathLst></a:custGeom>'
                % "".join(path))
        return self.sp(name, x0, y0, w, h, geom, fill, line, lw, dash, label, tstyle)

    def polyline(self, points, color, lw, dash=None, arrow_end=True, arrow_start=False,
                 name="Flow"):
        xs = [p[0] for p in points]; ys = [p[1] for p in points]
        x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
        w = max(x1 - x0, 0.01); h = max(y1 - y0, 0.01)
        path = ['<a:path w="%s" h="%s" fill="none">' % (e(w), e(h))]
        for k, (px, py) in enumerate(points):
            tag = "moveTo" if k == 0 else "lnTo"
            path.append('<a:%s><a:pt x="%s" y="%s"/></a:%s>'
                        % (tag, e(px - x0), e(py - y0), tag))
        path.append("</a:path>")
        geom = ('<a:custGeom><a:avLst/><a:gdLst/><a:ahLst/><a:cxnLst/>'
                '<a:rect l="0" t="0" r="r" b="b"/><a:pathLst>%s</a:pathLst></a:custGeom>'
                % "".join(path))
        i = self.sid()
        self.shapes.append(
            '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s %d"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            '<p:spPr>%s%s<a:noFill/>%s</p:spPr>%s</p:sp>'
            % (i, name, i, self._xfrm(x0, y0, w, h), geom,
               self._ln(color, lw, dash, arrow_start, arrow_end), self._txt(None, None)))
        return i

    def textbox(self, x, y, w, h, label, tstyle, name="Label"):
        i = self.sid()
        self.shapes.append(
            '<p:sp><p:nvSpPr><p:cNvPr id="%d" name="%s %d"/>'
            '<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            '<p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/></p:spPr>%s</p:sp>'
            % (i, name, i, self._xfrm(x, y, w, h), self._txt(label, tstyle, "ctr")))
        return i

    def picture(self, x, y, w, h, path):
        with open(path, "rb") as fh:
            blob = fh.read()
        ext = path.rsplit(".", 1)[-1].lower()
        ext = "png" if ext not in ("png", "jpg", "jpeg", "gif") else ext
        name = "image%d.%s" % (len(self.media) + 1, ext)
        self.media.append((name, blob))
        rid = self.add_rel("../media/" + name)
        i = self.sid()
        self.shapes.append(
            '<p:pic><p:nvPicPr><p:cNvPr id="%d" name="Panel %d"/>'
            '<p:cNvPicPr><a:picLocks noChangeAspect="0"/></p:cNvPicPr><p:nvPr/></p:nvPicPr>'
            '<p:blipFill><a:blip r:embed="%s"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>'
            '<p:spPr>%s<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:ln w="%s"><a:solidFill><a:srgbClr val="000000"/></a:solidFill></a:ln>'
            '</p:spPr></p:pic>'
            % (i, i, rid, self._xfrm(x, y, w, h), e(style.STROKE["hairline"])))
        return i


# ------------------------------------------------------------------ emit
def _tstyle(spec, fig, over=None):
    d = {"font": "Times New Roman" if spec.get("_font", fig.font) == "times" else "Arial",
         "size": spec.get("_tsize", 7.0),
         "bold": bool(spec.get("_bold")), "italic": bool(spec.get("_italic")),
         "color": style.resolve_color(spec.get("text_color"), style.INK, ink=True)}
    rot = spec.get("rotate")
    if rot in (90, -90, 270):
        d["vert"] = "vert270" if rot == 90 else "vert"
    if over:
        d.update(over)
    return d


def _emit_node(d, it, fig):
    s = it.spec
    shape = s.get("shape", "box")
    fill, stroke, tc = SH.node_colors(s)
    lw = style.stroke_width(s.get("lw"), style.STROKE["box"])
    dash = bool(s.get("dash"))
    x, y, w, h = it.x, it.y, it.w, it.h
    if s.get("caption"):
        h -= s["_cap_h"] + float(s.get("caption_gap", 3.0))
    ts = _tstyle(s, fig)
    label = s.get("text") or None

    if shape in ("box", "roundbox"):
        d.rect(x, y, w, h, fill, stroke, lw, dash, label, ts, True)
    elif shape in ("sharpbox", "rect", "bar"):
        d.rect(x, y, w, h, fill, stroke, lw, dash, label, ts, False)
    elif shape in ("trapezoid", "encoder", "invtrapezoid", "decoder", "chevron",
                   "parallelogram", "hexagon", "plane"):
        from .vsdx import _poly_points
        d.polygon(_poly_points(shape, s, x, y, w, h), fill, stroke, lw, dash, label, ts)
    elif shape in ("circle", "ellipse"):
        d.ellipse(x, y, w, h, fill, stroke, lw, label, ts)
    elif shape in ("circleop", "op"):
        dd = min(w, h); cx, cy = x + w / 2.0, y + h / 2.0
        d.ellipse(cx - dd / 2, cy - dd / 2, dd, dd, "#FFFFFF", stroke, lw)
        k = dd * 0.28
        sym = s.get("op", s.get("text", "+"))
        if sym in ("+", "add", "sum", "oplus"):
            d.polyline([(cx - k, cy), (cx + k, cy)], stroke, lw, None, False, False, "OpBar")
            d.polyline([(cx, cy - k), (cx, cy + k)], stroke, lw, None, False, False, "OpBar")
        elif sym in ("x", "*", "mul", "otimes"):
            j = k * 0.72
            d.polyline([(cx - j, cy - j), (cx + j, cy + j)], stroke, lw, None, False, False, "OpBar")
            d.polyline([(cx - j, cy + j), (cx + j, cy - j)], stroke, lw, None, False, False, "OpBar")
        else:
            d.textbox(cx - dd / 2, cy - dd / 2, dd, dd, sym, _tstyle(s, fig, {"size": dd * 0.6}))
    elif shape in ("slab", "slabstack"):
        dep = style.GEOM["slab_depth"]
        cnt = int(s.get("n", 1)); cw = float(s.get("cell", 8.0)); gap = float(s.get("cellgap", 3.0))
        ch = h - dep
        colors = s.get("colors")
        for i in range(cnt):
            cx = x + i * (cw + gap); cy = y + dep
            f = fill
            if isinstance(colors, list) and colors:
                f = style.resolve_color(colors[i % len(colors)], fill)
            d.polygon([(cx, cy), (cx + dep, cy - dep), (cx + cw + dep, cy - dep), (cx + cw, cy)],
                      SH._shade(f, 1.16), stroke, lw, None, None, None, True, "SlabTop")
            d.polygon([(cx + cw, cy), (cx + cw + dep, cy - dep),
                       (cx + cw + dep, cy + ch - dep), (cx + cw, cy + ch)],
                      SH._shade(f, 0.90), stroke, lw, None, None, None, True, "SlabSide")
            d.rect(cx, cy, cw, ch, f, stroke, lw, None, None, None, False, "SlabFace")
        if s.get("text"):
            d.textbox(x, y, w, h, s["text"], ts, "SlabLabel")
    elif shape == "cube":
        dep = style.GEOM["slab_depth"] * 1.6
        side = min(w - dep, h - dep); cx, cy = x, y + dep
        d.rect(cx, cy, side, side, fill, stroke, lw, None, None, None, False, "CubeFace")
        d.polygon([(cx, cy), (cx + dep, cy - dep), (cx + side + dep, cy - dep), (cx + side, cy)],
                  SH._shade(fill, 1.16), stroke, lw, None, None, None, True, "CubeTop")
        d.polygon([(cx + side, cy), (cx + side + dep, cy - dep),
                   (cx + side + dep, cy + side - dep), (cx + side, cy + side)],
                  SH._shade(fill, 0.90), stroke, lw, None, None, None, True, "CubeSide")
    elif shape == "tokengrid":
        rows = int(s.get("rows", 4)); cols = int(s.get("cols", 1))
        cell = float(s.get("cell", 8.0)); gap = float(s.get("cellgap", 2.4))
        colors = s.get("colors")
        for i in range(rows):
            for j in range(cols):
                f = fill
                if isinstance(colors, list) and colors:
                    f = style.resolve_color(colors[(i * cols + j) % len(colors)], fill)
                d.rect(x + j * (cell + gap), y + i * (cell + gap), cell, cell,
                       f, stroke, lw, None, None, None, True, "Token")
    elif shape == "framestrip":
        mask = SH.frame_mask(s)
        cell = float(s.get("cell", 5.0)); gap = float(s.get("cellgap", 1.2))
        on = style.resolve_color(s.get("on_fill"), style.FAMILIES["steel"][4])
        off = style.resolve_color(s.get("off_fill"), style.FAMILIES["grey"][1])
        edge = style.resolve_color(s.get("cell_stroke"), "none")
        for i, bit in enumerate(mask):
            d.rect(x + i * (cell + gap), y, cell, h, on if bit else off, edge,
                   style.stroke_width(s.get("cell_lw"), style.STROKE["hairline"]), None, None, None,
                   True, "Frame")
    elif shape in ("dist", "density"):
        from .vsdx import _dist_points
        d.polygon(_dist_points(s, x, y, w, h), fill, stroke, lw, None, None, None,
                  True, "Density")
    elif shape == "brace":
        col = style.resolve_color(s.get("color"), style.INK, ink=True)
        blw = style.stroke_width(s.get("lw"), style.STROKE["hairline"] * 1.6)
        span = float(s.get("depth", 3.0))
        if s.get("dir", "right") in ("right", "left"):
            tip = x + span if s.get("dir", "right") == "right" else x
            back = x if s.get("dir", "right") == "right" else x + span
            d.polyline([(back, y), (tip, y + h * 0.12), (tip, y + h * 0.44),
                        (tip + (tip - back) * 0.6, y + h / 2.0),
                        (tip, y + h * 0.56), (tip, y + h * 0.88), (back, y + h)],
                       col, blw, None, False, False, "Brace")
        else:
            d.polyline([(x, y), (x + w * 0.12, y + span), (x + w * 0.44, y + span),
                        (x + w / 2.0, y + span * 1.6), (x + w * 0.56, y + span),
                        (x + w * 0.88, y + span), (x + w, y)],
                       col, blw, None, False, False, "Brace")
    elif shape in ("image", "photo", "imagestack"):
        src = s.get("src")
        p = os.path.join(fig.base or "", src) if src else None
        if p and os.path.exists(p):
            d.picture(x, y, w, h, p)
        else:
            d.rect(x, y, w, h, "#F2F2F2", style.FRAME_GREY, style.STROKE["hairline"], True,
                   s.get("text") or "image",
                   _tstyle(s, fig, {"size": 6.0, "color": style.MUTED_INK}), False, "ImageSlot")
    elif shape in ("text", "note", "mathlabel"):
        d.textbox(x, y, w, h, label, ts)
    elif shape == "ellipsis":
        r = float(s.get("r", 1.05)); k = int(s.get("n", 3))
        for i in range(1, k + 1):
            d.ellipse(x + w * i / (k + 1.0) - r, y + h / 2.0 - r, 2 * r, 2 * r,
                      style.INK, "none", 0, None, None, "Dot")
    elif shape == "spacer":
        return
    else:
        d.rect(x, y, w, h, fill, stroke, lw, dash, label, ts, True)

    if s.get("caption"):
        d.textbox(x, y + h + float(s.get("caption_gap", 3.0)), w, s["_cap_h"] + 1,
                  s["caption"], _tstyle(s, fig, {"size": s["_cap_size"], "bold": False,
                                                 "italic": False}), "Caption")
    if s.get("badge"):
        bs = float(s.get("badge_size", style.TYPE["annot"]["size"]))
        d.textbox(x + w - 24, y - bs - 1.5, 24, bs + 3, s["badge"],
                  _tstyle(s, fig, {"size": bs, "italic": True, "bold": False,
                                   "align": "r"}), "Badge")


def _emit_container(d, it, fig):
    s = it.spec
    frame = s.get("frame", "none")
    fill = style.resolve_color(s.get("fill"), "none")
    if frame not in (None, "none", False) or fill != "none":
        stroke = style.resolve_color(s.get("frame_color"),
                                     style.FRAME_GREY if frame in ("dashed", "region") else style.INK,
                                     ink=True)
        if frame in (None, "none", False):
            stroke = "none"
        d.rect(it.x, it.y, it.w, it.h, fill, stroke,
               style.stroke_width(s.get("frame_lw"), style.STROKE["frame"]),
               frame in ("dashed", "region", True), None, None, True, "Stage")
    title = s.get("title")
    if title:
        ts = float(s.get("title_size", style.TYPE["stage_title"]["size"]))
        tw, th, _ = T.measure(title, ts, fig.font, True, True)
        pos = s.get("title_pos", "above")
        if pos == "above":
            ty = it.y - style.GEOM["stage_title_gap"] - th
        elif pos == "below":
            ty = it.y + it.h + style.GEOM["stage_title_gap"]
        elif pos == "inside-bottom":
            ty = it.y + it.h - th - style.GEOM["stage_pad"]
        else:
            ty = it.y + 4
        d.textbox(it.x, ty, it.w, th + 2, title,
                  {"font": "Times New Roman" if fig.font == "times" else "Arial",
                   "size": ts, "bold": s.get("title_bold", True),
                   "italic": s.get("title_italic", True),
                   "color": style.resolve_color(s.get("title_color"), style.INK, ink=True),
                   "align": {"left": "l", "right": "r"}.get(s.get("title_align", "center"), "ctr")},
                  "StageTitle")
    if s.get("badge"):
        bs = float(s.get("badge_size", style.TYPE["annot"]["size"]))
        d.textbox(it.x + it.w - 26, it.y + 1.5, 24, bs + 3, s["badge"],
                  {"font": "Times New Roman", "size": bs, "italic": True,
                   "color": style.INK, "align": "r"}, "Badge")
    for c in it.children:
        if c.kind == "node":
            _emit_node(d, c, fig)
        else:
            _emit_container(d, c, fig)


def _emit_edges(d, fig):
    for ed in (fig.spec.get("edges") or []):
        a, sa = edgemod.resolve_ref(ed["from"], fig.nodes)
        c, sb = edgemod.resolve_ref(ed["to"], fig.nodes)
        if sa is None or sb is None:
            da, db = edgemod.auto_sides(a, c)
            sa = sa or da
            sb = sb or db
        pts = edgemod._dedup(edgemod._path_points(a, sa, c, sb, ed))
        color = style.resolve_color(ed.get("color"), style.INK, ink=True)
        lwk = ed.get("lw", "flow")
        lw = style.STROKE.get(lwk) if isinstance(lwk, str) else float(lwk)
        lw = lw or style.STROKE["flow"]
        arrow = ed.get("arrow", "end")
        d.polyline(pts, color, lw, bool(ed.get("dash")),
                   arrow in ("end", "both"), arrow in ("start", "both"))
        if ed.get("label"):
            mid = pts[len(pts) // 2]
            size = float(ed.get("label_size", style.TYPE["caption"]["size"]))
            tw, th, _ = T.measure(ed["label"], size, fig.font)
            d.textbox(mid[0] - tw / 2.0 - 1, mid[1] - th - 2.5, tw + 2, th + 2, ed["label"],
                      {"font": "Times New Roman" if fig.font == "times" else "Arial",
                       "size": size, "color": color}, "FlowLabel")


def _emit_notes(d, fig):
    for nt in (fig.spec.get("notes") or []):
        if not isinstance(nt, dict):
            continue
        size = float(nt.get("size", style.TYPE["annot"]["size"]))
        if nt.get("at"):
            x, y = float(nt["at"][0]), float(nt["at"][1])
        elif nt.get("near"):
            item, side = edgemod.resolve_ref(nt["near"], fig.nodes)
            x, y = item.port(side or "n")
        else:
            continue
        x += float(nt.get("dx", 0.0)); y += float(nt.get("dy", 0.0))
        tw, th, _ = T.measure(nt.get("text", ""), size, fig.font)
        d.textbox(x - tw / 2.0 - 1, y - th / 2.0 - 1, tw + 3, th + 2, nt.get("text", ""),
                  {"font": "Times New Roman" if fig.font == "times" else "Arial",
                   "size": size, "italic": nt.get("italic", True),
                   "color": style.resolve_color(nt.get("color"), style.INK, ink=True)}, "Note")


# ------------------------------------------------------------------ package
def _content_types(media):
    exts = set(n.rsplit(".", 1)[-1] for n, _ in media)
    defaults = ['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
                '<Default Extension="xml" ContentType="application/xml"/>']
    for x in sorted(exts):
        mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "gif": "image/gif"}.get(x, "image/png")
        defaults.append('<Default Extension="%s" ContentType="%s"/>' % (x, mime))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '%s'
            '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
            '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
            '<Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>'
            '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
            '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
            '</Types>' % "".join(defaults))


ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
             '</Relationships>')

PRES_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>'
             '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>'
             '</Relationships>')

MASTER_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
               '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
               '</Relationships>')

LAYOUT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
               '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
               '</Relationships>')

_EMPTY_TREE = ('<p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/>'
               '<p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/>'
               '<a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/>'
               '</a:xfrm></p:grpSpPr></p:spTree></p:cSld>')

_PML = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
        'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"')

MASTER = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<p:sldMaster %s>%s<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1"'
          ' accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5"'
          ' accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
          '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
          '</p:sldMaster>' % (_PML, _EMPTY_TREE))

LAYOUT = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<p:sldLayout %s type="blank" preserve="1">%s</p:sldLayout>' % (_PML, _EMPTY_TREE))


def _theme():
    def scheme():
        names = ["dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3",
                 "accent4", "accent5", "accent6", "hlink", "folHlink"]
        vals = ["000000", "FFFFFF", "44546A", "E7E6E6", "5B9BD5", "ED7D31",
                "A5A5A5", "FFC000", "4472C4", "70AD47", "0563C1", "954F72"]
        out = []
        for nm, v in zip(names, vals):
            if nm in ("dk1", "lt1"):
                out.append('<a:%s><a:sysClr val="%s" lastClr="%s"/></a:%s>'
                           % (nm, "windowText" if nm == "dk1" else "window", v, nm))
            else:
                out.append('<a:%s><a:srgbClr val="%s"/></a:%s>' % (nm, v, nm))
        return "".join(out)
    fmt = ('<a:fmtScheme name="Office"><a:fillStyleLst>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
           '<a:lnStyleLst>'
           '<a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
           '</a:lnStyleLst>'
           '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
           '<a:effectStyle><a:effectLst/></a:effectStyle>'
           '<a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
           '<a:bgFillStyleLst>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
           '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
           '</a:fmtScheme>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="%s" name="CVPR-Figure"><a:themeElements>'
            '<a:clrScheme name="Office">%s</a:clrScheme>'
            '<a:fontScheme name="Office"><a:majorFont><a:latin typeface="Times New Roman"/>'
            '<a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Times New Roman"/><a:ea typeface=""/>'
            '<a:cs typeface=""/></a:minorFont></a:fontScheme>%s</a:themeElements>'
            '<a:objectDefaults/><a:extraClrSchemeLst/></a:theme>' % (A, scheme(), fmt))


def write(fig, path):
    d = Deck(fig)
    for it in fig.items:
        _emit_container(d, it, fig)
    _emit_edges(d, fig)
    _emit_notes(d, fig)

    slide = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<p:sld %s><p:cSld><p:spTree>'
             '<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
             '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/>'
             '<a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
             '%s</p:spTree></p:cSld>'
             '<p:clrMapOvr><a:overrideClrMapping bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2"'
             ' accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4"'
             ' accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
             '</p:clrMapOvr></p:sld>' % (_PML, "".join(d.shapes)))

    pres = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<p:presentation %s saveSubsetFonts="1">'
            '<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
            '<p:sldIdLst><p:sldId id="256" r:id="rId2"/></p:sldIdLst>'
            '<p:sldSz cx="%s" cy="%s"/><p:notesSz cx="%s" cy="%s"/>'
            '</p:presentation>' % (_PML, e(d.W), e(d.H), e(d.H), e(d.W)))

    slide_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
                  '%s</Relationships>'
                  % "".join('<Relationship Id="%s" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="%s"/>'
                            % (rid, tgt) for rid, tgt in d.rels))

    zf = zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED)
    try:
        zf.writestr("[Content_Types].xml", _content_types(d.media))
        zf.writestr("_rels/.rels", ROOT_RELS)
        zf.writestr("ppt/presentation.xml", pres)
        zf.writestr("ppt/_rels/presentation.xml.rels", PRES_RELS)
        zf.writestr("ppt/slideMasters/slideMaster1.xml", MASTER)
        zf.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", MASTER_RELS)
        zf.writestr("ppt/slideLayouts/slideLayout1.xml", LAYOUT)
        zf.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", LAYOUT_RELS)
        zf.writestr("ppt/slides/slide1.xml", slide)
        zf.writestr("ppt/slides/_rels/slide1.xml.rels", slide_rels)
        zf.writestr("ppt/theme/theme1.xml", _theme())
        for name, blob in d.media:
            zf.writestr("ppt/media/" + name, blob)
    finally:
        zf.close()
    return {"path": path, "shapes": len(d.shapes), "media": len(d.media)}
