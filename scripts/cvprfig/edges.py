"""Edge routing.

Real pipeline figures use three routing patterns and essentially nothing else:
a straight shot between facing ports, an orthogonal dog-leg when the ports are
offset, and a bus that leaves a node sideways, runs parallel to the flow and
re-enters (the classic residual / skip connection).  Anything more elaborate
reads as auto-generated, so the router deliberately stops here.
"""

from . import style, svg
from .svg import fmt

SIDE_VEC = {"n": (0, -1), "s": (0, 1), "e": (1, 0), "w": (-1, 0), "c": (0, 0)}


def resolve_ref(ref, nodes):
    """``"id"`` or ``"id.side"`` -> (item, side or None)."""
    if isinstance(ref, (list, tuple)):
        return None, None
    ref = str(ref)
    side = None
    if "." in ref:
        head, tail = ref.rsplit(".", 1)
        if tail.lower() in ("n", "s", "e", "w", "c", "nw", "ne", "sw", "se"):
            ref, side = head, tail.lower()
    item = nodes.get(ref)
    if item is None:
        raise KeyError("edge references unknown node id %r" % ref)
    return item, side


def auto_sides(a, b):
    dx = b.cx - a.cx
    dy = b.cy - a.cy
    ax_overlap = min(a.x + a.w, b.x + b.w) - max(a.x, b.x)
    ay_overlap = min(a.y + a.h, b.y + b.h) - max(a.y, b.y)
    if abs(dx) >= abs(dy) or (ay_overlap > 0 and abs(dx) > 2):
        return ("e", "w") if dx >= 0 else ("w", "e")
    return ("s", "n") if dy >= 0 else ("n", "s")


def _ortho(p0, sa, p1, sb, stub, mid):
    """Standard orthogonal connector: leave along the port normal, turn at
    most twice, arrive along the target port normal."""
    vx, vy = SIDE_VEC.get(sa, (0, 0))
    wx, wy = SIDE_VEC.get(sb, (0, 0))
    a = (p0[0] + vx * stub, p0[1] + vy * stub)
    b = (p1[0] + wx * stub, p1[1] + wy * stub)
    h_out, h_in = bool(vx), bool(wx)
    if h_out and h_in:
        mx = a[0] + (b[0] - a[0]) * mid
        pts = [p0, a, (mx, a[1]), (mx, b[1]), b, p1]
    elif not h_out and not h_in:
        my = a[1] + (b[1] - a[1]) * mid
        pts = [p0, a, (a[0], my), (b[0], my), b, p1]
    elif h_out:
        pts = [p0, a, (b[0], a[1]), b, p1]
    else:
        pts = [p0, a, (a[0], b[1]), b, p1]
    return pts


def _path_points(a, sa, b, sb, e):
    p0 = a.port(sa)
    p1 = b.port(sb)
    route = e.get("route", "auto")
    stub = float(e.get("stub", style.GEOM["port_stub"]))
    mid = float(e.get("mid", 0.5))

    if e.get("via"):
        pts = [p0]
        for v in e["via"]:
            if isinstance(v, (list, tuple)) and len(v) == 2:
                pts.append((float(v[0]), float(v[1])))
        pts.append(p1)
        return pts

    if route == "straight":
        return [p0, p1]

    # already facing each other on one axis -- a single straight run reads best
    if route == "auto":
        vx, vy = SIDE_VEC.get(sa, (0, 0))
        wx, wy = SIDE_VEC.get(sb, (0, 0))
        aligned_x = abs(p0[0] - p1[0]) < 0.4 and vy and wy and vy == -wy
        aligned_y = abs(p0[1] - p1[1]) < 0.4 and vx and wx and vx == -wx
        if aligned_x or aligned_y:
            return [p0, p1]

    if route in ("bus", "loop"):
        bend = float(e.get("bend", 12.0))
        vx, vy = SIDE_VEC.get(sa, (1, 0))
        wx, wy = SIDE_VEC.get(sb, (-1, 0))
        m0 = (p0[0] + vx * bend, p0[1] + vy * bend)
        m1 = (p1[0] + wx * bend, p1[1] + wy * bend)
        if vx:
            return [p0, m0, (m0[0], m1[1]), m1, p1]
        return [p0, m0, (m1[0], m0[1]), m1, p1]

    if route == "hv":
        va = (p0[0] + SIDE_VEC.get(sa, (1, 0))[0] * stub,
              p0[1] + SIDE_VEC.get(sa, (1, 0))[1] * stub)
        vb = (p1[0] + SIDE_VEC.get(sb, (-1, 0))[0] * stub,
              p1[1] + SIDE_VEC.get(sb, (-1, 0))[1] * stub)
        return [p0, va, (vb[0], va[1]), vb, p1]
    if route == "vh":
        va = (p0[0] + SIDE_VEC.get(sa, (0, 1))[0] * stub,
              p0[1] + SIDE_VEC.get(sa, (0, 1))[1] * stub)
        vb = (p1[0] + SIDE_VEC.get(sb, (0, -1))[0] * stub,
              p1[1] + SIDE_VEC.get(sb, (0, -1))[1] * stub)
        return [p0, va, (va[0], vb[1]), vb, p1]

    return _ortho(p0, sa, p1, sb, stub, mid)


def _dedup(pts):
    """Drop repeated points, then collapse collinear runs."""
    out = [pts[0]]
    for p in pts[1:]:
        if abs(p[0] - out[-1][0]) > 0.05 or abs(p[1] - out[-1][1]) > 0.05:
            out.append(p)
    if len(out) < 3:
        return out
    slim = [out[0]]
    for i in range(1, len(out) - 1):
        ax, ay = slim[-1]
        bx, by = out[i]
        cx, cy = out[i + 1]
        cross = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
        if abs(cross) > 0.05:
            slim.append(out[i])
    slim.append(out[-1])
    return slim


def draw(cv, e, nodes, ctx):
    a, sa = resolve_ref(e["from"], nodes)
    b, sb = resolve_ref(e["to"], nodes)
    if sa is None or sb is None:
        da, db = auto_sides(a, b)
        sa = sa or da
        sb = sb or db

    color = style.resolve_color(e.get("color"), style.INK, ink=True)
    lwk = e.get("lw", "flow")
    lw = style.STROKE.get(lwk, None) if isinstance(lwk, str) else float(lwk)
    if lw is None:
        lw = float(lwk)
    dash = e.get("dash")
    if dash is True:
        dash = style.DASH["flow"]
    elif isinstance(dash, str):
        dash = style.DASH.get(dash, dash)

    pts = _dedup(_path_points(a, sa, b, sb, e))
    arrow = e.get("arrow", "end")
    marker_end = marker_start = ""
    kind = e.get("head", "tri")
    if arrow in ("end", "both"):
        marker_end = " marker-end='url(#%s)'" % cv.marker(color, lw, kind)
    if arrow in ("start", "both"):
        marker_start = " marker-start='url(#%s)'" % cv.marker(color, lw, kind)

    d = "M" + " L".join("%s,%s" % (fmt(x), fmt(y)) for x, y in pts)
    cv.add("<path d='%s' fill='none' stroke='%s' stroke-width='%s' stroke-linejoin='miter'"
           " stroke-linecap='butt'%s%s%s/>"
           % (d, color, fmt(lw), " stroke-dasharray='%s'" % dash if dash else "",
              marker_start, marker_end))

    if e.get("label"):
        _label(cv, e, pts, color, ctx)


def _label(cv, e, pts, color, ctx):
    t = float(e.get("label_pos", 0.5))
    segs = []
    total = 0.0
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        L = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
        segs.append((L, pts[i], pts[i + 1]))
        total += L
    target = total * t
    acc = 0.0
    px, py, horiz = pts[0][0], pts[0][1], True
    for L, p, q in segs:
        if acc + L >= target or L == segs[-1][0]:
            r = 0 if L == 0 else (target - acc) / L
            px = p[0] + (q[0] - p[0]) * r
            py = p[1] + (q[1] - p[1]) * r
            horiz = abs(q[0] - p[0]) >= abs(q[1] - p[1])
            break
        acc += L
    size = float(e.get("label_size", style.TYPE["caption"]["size"]))
    dx = float(e.get("label_dx", 0.0))
    dy = float(e.get("label_dy", -(size * 0.62) if horiz else 0.0))
    anchor = e.get("label_anchor", "middle" if horiz else "start")
    if not horiz and not e.get("label_dx"):
        dx = size * 0.5
    tc = style.resolve_color(e.get("label_color"),
                             color if e.get("label_color_match", True) else style.INK, ink=True)
    if e.get("label_bg", True):
        pass
    svg.draw_text(cv, px + dx, py + dy, e["label"], size,
                  e.get("label_font", ctx["font"]), e.get("label_bold", False),
                  e.get("label_italic", False), tc, anchor, "middle")
