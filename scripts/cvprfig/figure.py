"""Spec -> laid-out figure -> SVG.

Design contract: the layout is computed directly in *final rendered points*,
so a 7 pt label in the spec is a 7 pt label on the printed page.  The canvas
width defaults to the target venue's column width, and slack is distributed
into the gaps between stages rather than by stretching the modules.
"""

import os

from . import edges as edgemod
from . import layout as L
from . import shapes, style, svg
from .svg import fmt


class Figure(object):
    def __init__(self, spec, base=None):
        self.spec = spec or {}
        self.base = base
        self.warnings = []
        self.meta = {}
        self._build()

    # ------------------------------------------------------------- build
    def _build(self):
        f = self.spec.get("figure") or {}
        venue = str(f.get("venue", "cvpr")).lower()
        widths = style.VENUE_WIDTH.get(venue, style.VENUE_WIDTH["generic"])
        w = f.get("width", "double")
        if isinstance(w, str):
            target = widths.get(w, widths["double"])
        else:
            target = float(w)
        self.target = target * float(f.get("width_frac", 1.0))
        self.font = f.get("font", "times")
        self.pad = float(f.get("pad", 2.0))
        # Extra room reserved outside the panel band -- used when a legend or a
        # key sits beside the first stage title, as page-1 teasers usually do.
        self.pad_top = self.pad + float(f.get("pad_top", 0.0))
        self.pad_bottom = self.pad + float(f.get("pad_bottom", 0.0))
        ctx = {"font": self.font, "base": self.base, "venue": venue}
        self.ctx = ctx

        defaults = self.spec.get("defaults") or {}
        panels = self.spec.get("panels")
        if panels is None:
            body = self.spec.get("body") or self.spec.get("nodes") or []
            panels = [{"id": "_root", "frame": "none", "body": body}]

        arrange = str(self.spec.get("layout", "row")).lower()
        self.items = [L.build_item(_as_container(p), defaults, ctx, 1) for p in panels]
        for it in self.items:
            L.measure(it, ctx)

        # title band above the panel row
        # Room above the first row for stage titles, which are drawn outside
        # the frame they belong to.  This has to look *inside* the top-level
        # items as well as at them: a banded layout (see code2fig) wraps titled
        # groups in an untitled band, and reserving nothing then clips every
        # title on the top row.
        self.title_band = max((_above_title_h(it) for it in self.items), default=0.0)
        self.bottom_band = 0.0
        for it in self.items:
            if it.spec.get("title") and it.spec.get("title_pos") == "below":
                ts = float(it.spec.get("title_size", style.TYPE["stage_title"]["size"]))
                self.bottom_band = max(self.bottom_band, ts + style.GEOM["stage_title_gap"])

        gap = float(self.spec.get("gap", style.GEOM["stage_gap"]))
        if arrange == "col":
            self._stack_col(gap)
        elif arrange == "grid":
            self._stack_grid(gap, int(self.spec.get("cols", 2)))
        else:
            self._stack_row(gap)

        self.nodes = L.index(self.items)
        self._apply_absolute()

    def _stack_row(self, gap):
        nat = sum(i.w for i in self.items) + gap * max(0, len(self.items) - 1)
        inner = self.target - 2 * self.pad
        slack = inner - nat
        n = max(1, len(self.items) - 1)
        if slack > 0 and len(self.items) > 1 and self.spec.get("fit", "fill") == "fill":
            gap += slack / n
            slack = 0.0
        x = self.pad + (max(slack, 0.0) / 2.0 if len(self.items) == 1 else 0.0)
        y = self.pad_top + self.title_band
        top = max((i.h for i in self.items), default=0.0)
        for it in self.items:
            va = it.spec.get("valign", "top")
            oy = 0.0 if va == "top" else (top - it.h if va == "bottom" else (top - it.h) / 2.0)
            L.place(it, x, y + oy, self.ctx)
            x += it.w + gap
        self.natural_w = max(self.pad * 2 + nat, x - gap + self.pad)
        self.natural_h = (self.pad_top + self.pad_bottom + self.title_band + top
                          + self.bottom_band)

    def _stack_col(self, gap):
        y = self.pad_top + self.title_band
        wide = max((i.w for i in self.items), default=0.0)
        inner = max(self.target - 2 * self.pad, wide)
        for it in self.items:
            ha = it.spec.get("halign", "center")
            ox = 0.0 if ha == "left" else (inner - it.w if ha == "right" else (inner - it.w) / 2.0)
            L.place(it, self.pad + ox, y, self.ctx)
            y += it.h + gap + (self.title_band if it is not self.items[-1] and self.title_band else 0)
        self.natural_w = self.pad * 2 + inner
        self.natural_h = y - gap + self.pad_bottom + self.bottom_band

    def _stack_grid(self, gap, cols):
        # rows of equal-width columns; each row gets its own title band
        rows = [self.items[i:i + cols] for i in range(0, len(self.items), cols)]
        colw = [0.0] * cols
        for r in rows:
            for j, it in enumerate(r):
                colw[j] = max(colw[j], it.w)
        y = self.pad_top + self.title_band
        for r in rows:
            x = self.pad
            rh = max(i.h for i in r)
            for j, it in enumerate(r):
                L.place(it, x + (colw[j] - it.w) / 2.0, y, self.ctx)
                x += colw[j] + gap
            y += rh + gap + self.title_band
        self.natural_w = self.pad * 2 + sum(colw) + gap * (cols - 1)
        self.natural_h = y - gap + self.pad_bottom

    def _apply_absolute(self):
        """Nodes may pin themselves with ``at: [x, y]`` in canvas coordinates."""
        for it in L.walk(self.items):
            at = it.spec.get("at")
            if isinstance(at, (list, tuple)) and len(at) == 2:
                dx = float(at[0]) - it.x
                dy = float(at[1]) - it.y
                for sub in L.walk([it]):
                    sub.x += dx
                    sub.y += dy

    @property
    def fit_scale(self):
        """Downscale the export will apply, known right after layout.

        Available without rendering so a caller can reshape a draft before
        committing to it -- see code2fig.emit.fit.
        """
        nat_w = max(self.natural_w, self.target)
        return self.target / nat_w if nat_w > self.target + 0.01 else 1.0

    # ------------------------------------------------------------ render
    def render(self):
        """Draw the figure once and cache it; every exporter shares the result."""
        if getattr(self, "_canvas", None) is not None:
            return self._canvas
        nat_w = max(self.natural_w, self.target)
        nat_h = self.natural_h
        f = self.spec.get("figure") or {}
        if f.get("height"):
            nat_h = max(nat_h, float(f["height"]))

        cv = svg.Canvas(nat_w, nat_h, style.resolve_color(f.get("bg"), "#FFFFFF"))
        self.scale = self.target / nat_w if nat_w > self.target + 0.01 else 1.0

        for it in self.items:
            self._draw_container(cv, it)

        for e in (self.spec.get("edges") or []):
            edgemod.draw(cv, e, self.nodes, self.ctx)

        for n in (self.spec.get("notes") or []):
            self._draw_note(cv, n)

        legend = self.spec.get("legend")
        if legend:
            self._draw_legend(cv, legend, nat_w, nat_h)

        cv.width = self.target
        cv.height = nat_h * self.scale
        self._viewbox = (nat_w, nat_h)
        self.meta = {
            "canvas_pt": [round(self.target, 2), round(nat_h * self.scale, 2)],
            "natural_pt": [round(nat_w, 2), round(nat_h, 2)],
            "scale": round(self.scale, 4),
            "node_count": sum(1 for i in L.walk(self.items) if i.kind == "node"),
            "edge_count": len(self.spec.get("edges") or []),
        }
        self._canvas = cv
        if self.scale < 0.999:
            eff = style.TYPE["node"]["size"] * self.scale
            self.warnings.append(
                "Layout is %.1f pt wide but the target column is %.1f pt, so the figure is "
                "scaled to %.0f%%; body labels render at ~%.1f pt."
                % (nat_w, self.target, self.scale * 100, eff))
            if eff < style.MIN_RENDERED_PT:
                self.warnings.append(
                    "Effective label size %.1f pt is below the %.1f pt legibility floor -- "
                    "split the figure or shorten labels." % (eff, style.MIN_RENDERED_PT))
        return cv

    def tostring(self):
        cv = self.render()
        head = ("<svg xmlns='http://www.w3.org/2000/svg' "
                "xmlns:xlink='http://www.w3.org/1999/xlink' version='1.1' "
                "width='%spt' height='%spt' viewBox='0 0 %s %s'>"
                % (fmt(cv.width), fmt(cv.height), fmt(self._viewbox[0]), fmt(self._viewbox[1])))
        parts = [head]
        if cv.defs:
            parts.append("<defs>%s</defs>" % "".join(cv.defs))
        if cv.bg and cv.bg != "none":
            parts.append("<rect x='0' y='0' width='%s' height='%s' fill='%s'/>"
                         % (fmt(self._viewbox[0]), fmt(self._viewbox[1]), cv.bg))
        parts.extend(cv.body)
        parts.append("</svg>")
        return "\n".join(parts)

    # ----------------------------------------------------------- drawing
    def _draw_container(self, cv, it):
        s = it.spec
        frame = s.get("frame", "none")
        fill = style.resolve_color(s.get("fill"), "none")
        if frame not in (None, "none", False) or fill != "none":
            stroke = style.resolve_color(s.get("frame_color"),
                                         style.FRAME_GREY if frame == "dashed" else style.INK)
            if frame in (None, "none", False):
                stroke = "none"
            dash = None
            if frame in ("dashed", True):
                dash = style.DASH["frame"]
            elif frame == "region":
                dash = style.DASH["region"]
                stroke = style.resolve_color(s.get("frame_color"), style.FRAME_GREY)
            lw = style.stroke_width(s.get("frame_lw"), style.STROKE["frame"])
            r = float(s.get("corner", style.GEOM["frame_corner"]))
            svg.rect(cv, it.x, it.y, it.w, it.h, r, fill, stroke, lw, dash,
                     s.get("frame_opacity"))

        title = s.get("title")
        if title:
            pos = s.get("title_pos", "above")
            ts = float(s.get("title_size", style.TYPE["stage_title"]["size"]))
            tc = style.resolve_color(s.get("title_color"), style.INK, ink=True)
            bold = s.get("title_bold", style.TYPE["stage_title"]["weight"] == "bold")
            ital = s.get("title_italic", style.TYPE["stage_title"]["style"] == "italic")
            ha = s.get("title_align", "center")
            tx = {"left": it.x + 2.0, "right": it.x + it.w - 2.0}.get(ha, it.x + it.w / 2.0)
            anch = {"left": "start", "right": "end"}.get(ha, "middle")
            nl = len(str(title).split("\n"))
            if pos == "above":
                ty = it.y - style.GEOM["stage_title_gap"] - ts * (nl - 0.5) * 1.18
                svg.draw_text(cv, tx, ty, title, ts, self.font, bold, ital, tc, anch, "middle")
            elif pos == "below":
                svg.draw_text(cv, tx, it.y + it.h + style.GEOM["stage_title_gap"] + ts * 0.5,
                              title, ts, self.font, bold, ital, tc, anch, "middle")
            elif pos == "inside-bottom":
                svg.draw_text(cv, tx, it.y + it.h - style.GEOM["stage_pad"] - ts * 0.5,
                              title, ts, self.font, bold, ital, tc, anch, "middle")
            else:  # inside-top
                svg.draw_text(cv, tx, it.y + s.get("_pad", (6, 0, 0, 0))[0] + ts * 0.5,
                              title, ts, self.font, bold, ital, tc, anch, "middle")

        if s.get("badge"):
            bs = float(s.get("badge_size", style.TYPE["annot"]["size"]))
            svg.draw_text(cv, it.x + it.w - 3.0, it.y + bs * 0.9, s["badge"], bs,
                          self.font, False, True,
                          style.resolve_color(s.get("badge_color"), style.INK), "end", "middle")

        for c in it.children:
            if c.kind == "node":
                shapes.draw(cv, c, self.ctx)
            else:
                self._draw_container(cv, c)

    def _draw_note(self, cv, n):
        if not isinstance(n, dict):
            return
        size = float(n.get("size", style.TYPE["annot"]["size"]))
        color = style.resolve_color(n.get("color"), style.INK, ink=True)
        anchor = n.get("anchor", "middle")
        x = y = None
        if n.get("at"):
            x, y = float(n["at"][0]), float(n["at"][1])
        elif n.get("near"):
            item, side = edgemod.resolve_ref(n["near"], self.nodes)
            x, y = item.port(side or "n")
        if x is None:
            return
        x += float(n.get("dx", 0.0))
        y += float(n.get("dy", 0.0))
        svg.draw_text(cv, x, y, n.get("text", ""), size, n.get("font", self.font),
                      n.get("bold", False), n.get("italic", style.TYPE["annot"]["style"] == "italic"),
                      color, anchor, "middle", n.get("rotate", 0))

    def _draw_legend(self, cv, lg, w, h):
        items = lg.get("items") or []
        size = float(lg.get("size", style.TYPE["caption"]["size"]))
        gap = float(lg.get("gap", 3.2))
        sw = float(lg.get("swatch", 13.0))
        pad = float(lg.get("pad", 3.0))
        vertical = lg.get("dir", "col") == "col"
        rows = []
        for e in items:
            lab = e.get("text", "")
            from . import text as T
            tw = T.line_width(lab, size, self.font, False, False)
            rows.append((e, tw))
        bw = max((sw + 3.0 + t for _, t in rows), default=0.0)
        bh = len(rows) * (size + gap) - gap
        if not vertical:
            bw = sum(sw + 3.0 + t for _, t in rows) + gap * (len(rows) - 1)
            bh = size
        pos = lg.get("at")
        if pos:
            x0, y0 = float(pos[0]), float(pos[1])
        else:
            corner = lg.get("corner", "ne")
            x0 = w - bw - pad - 4 if "e" in corner else pad + 4
            y0 = pad + 4 if "n" in corner else h - bh - pad - 4
        if lg.get("box", False):
            svg.rect(cv, x0 - pad, y0 - pad, bw + 2 * pad, bh + 2 * pad, 2.0,
                     "#FFFFFF", style.FRAME_GREY, style.STROKE["hairline"])
        cx, cy = x0, y0
        for e, tw in rows:
            col = style.resolve_color(e.get("color"), style.INK, ink=True)
            kind = e.get("kind", "line")
            ymid = cy + size / 2.0
            if kind in ("line", "arrow", "dashed"):
                dash = style.DASH["flow"] if (kind == "dashed" or e.get("dash")) else None
                lw = float(e.get("lw", style.STROKE["flow"]))
                mk = " marker-end='url(#%s)'" % cv.marker(col, lw) if kind != "line" or e.get("arrow", True) else ""
                cv.add("<path d='M%s,%s L%s,%s' fill='none' stroke='%s' stroke-width='%s'%s%s/>"
                       % (fmt(cx), fmt(ymid), fmt(cx + sw), fmt(ymid), col, fmt(lw),
                          " stroke-dasharray='%s'" % dash if dash else "", mk))
            else:
                svg.rect(cv, cx, cy + size * 0.1, sw, size * 0.8, 1.2,
                         style.resolve_color(e.get("fill"), col), style.INK, style.STROKE["hairline"])
            svg.draw_text(cv, cx + sw + 3.0, ymid, e.get("text", ""), size, self.font,
                          False, False, style.resolve_color(e.get("text_color"), style.INK),
                          "start", "middle")
            if vertical:
                cy += size + gap
            else:
                cx += sw + 3.0 + tw + gap


def _above_title_h(item, depth=0):
    """Height an "above" title needs, for this container or any it holds.

    Deliberately conservative: it does not check whether the titled container
    actually sits at the top edge, because titles are measured before anything
    is placed.  Over-reserving costs a few points of white space; under-
    reserving clips text off the canvas.
    """
    h = 0.0
    s = getattr(item, "spec", None) or {}
    if s.get("title") and s.get("title_pos", "above") == "above":
        ts = float(s.get("title_size", style.TYPE["stage_title"]["size"]))
        nlines = len(str(s["title"]).split("\n"))
        h = ts * (1.0 + 0.18 * (nlines - 1)) * nlines + style.GEOM["stage_title_gap"]
    if depth < 3:
        for c in getattr(item, "children", None) or ():
            h = max(h, _above_title_h(c, depth + 1))
    return h


def _as_container(p):
    if not isinstance(p, dict):
        return {"body": []}
    p = dict(p)
    if "body" not in p and "row" not in p and "col" not in p and "stack" not in p:
        p["body"] = []
    return p
