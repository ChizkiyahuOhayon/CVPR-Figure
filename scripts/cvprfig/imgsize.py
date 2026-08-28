"""Pixel dimensions of PNG / JPEG / GIF, with no dependencies.

Needed so an ``image:`` node can inherit the real aspect ratio of the photo
it points at.  Getting this wrong is the loudest tell in a generated figure:
squashed input frames.
"""

import struct


def size(path):
    """Return (width, height) in pixels, or None if the format is unknown."""
    try:
        with open(path, "rb") as fh:
            head = fh.read(26)
            if head[:8] == b"\x89PNG\r\n\x1a\n" and head[12:16] == b"IHDR":
                return struct.unpack(">II", head[16:24])
            if head[:3] == b"GIF":
                w, h = struct.unpack("<HH", head[6:10])
                return w, h
            if head[:2] == b"\xff\xd8":
                return _jpeg(fh)
            if head[:4] == b"%PDF":
                return _pdf(path)
    except Exception:
        return None
    return None


def _jpeg(fh):
    fh.seek(2)
    while True:
        b = fh.read(1)
        while b and b != b"\xff":
            b = fh.read(1)
        while b == b"\xff":
            b = fh.read(1)
        if not b:
            return None
        marker = b[0]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        ln = struct.unpack(">H", fh.read(2))[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            fh.read(1)
            h, w = struct.unpack(">HH", fh.read(4))
            return w, h
        fh.seek(ln - 2, 1)


def _pdf(path):
    """MediaBox of the first page, in points, for vector assets."""
    import re
    with open(path, "rb") as fh:
        blob = fh.read(400000)
    m = re.search(rb"/MediaBox\s*\[\s*([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)\s+([\d.+-]+)", blob)
    if not m:
        return None
    x0, y0, x1, y1 = (float(v) for v in m.groups())
    return abs(x1 - x0), abs(y1 - y0)


def aspect(path, default=1.33):
    wh = size(path)
    if not wh or not wh[1]:
        return default
    return wh[0] / float(wh[1])
