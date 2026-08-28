r"""Text measurement and light inline markup.

Supports the small amount of markup real conference figures need:
  ``*italic*``, ``**bold**``, ``_sub_``, ``^sup^`` and ``\n`` line breaks.
  A backslash escapes the next character: ``kernel\_size`` prints literally.
Measurement uses the baked Adobe Core-14 advance widths, so a box sized here
is correct in the exported PDF without a font query at run time.
"""

import re
from ._metrics import WIDTHS

_FALLBACK = 500  # ems/1000 for glyphs outside Latin-1 (CJK, arrows, math)
# Advance widths for the handful of non-Latin-1 glyphs figure labels actually
# use.  Without these the fallback overestimates and labels look gappy.
_EXTRA = {
    "\u00d7": 564, "\u2212": 564, "\u00b1": 564, "\u2264": 549, "\u2265": 549,
    "\u2248": 549, "\u2192": 987, "\u2190": 987, "\u2194": 1042, "\u21d2": 987,
    "\u2295": 768, "\u2297": 768, "\u2299": 768, "\u2211": 713, "\u222b": 274,
    "\u2026": 1000, "\u00b7": 250, "\u2022": 460, "\u2013": 500, "\u2014": 1000,
    "\u2018": 333, "\u2019": 333, "\u201c": 444, "\u201d": 444, "\u00b0": 400,
    "\u03b1": 500, "\u03b2": 500, "\u03b3": 411, "\u03b4": 494, "\u03b5": 439,
    "\u03b8": 521, "\u03bb": 549, "\u03bc": 576, "\u03c0": 549, "\u03c3": 603,
    "\u03c4": 439, "\u03c6": 521, "\u03c8": 686, "\u03c9": 686, "\u0394": 612,
}


def _key(family, bold, italic):
    if family == "helvetica":
        if bold and italic:
            return "helvetica-boldoblique"
        if bold:
            return "helvetica-bold"
        if italic:
            return "helvetica-oblique"
        return "helvetica"
    if bold and italic:
        return "times-bolditalic"
    if bold:
        return "times-bold"
    if italic:
        return "times-italic"
    return "times"


def glyph_width(ch, family="times", bold=False, italic=False):
    table = WIDTHS[_key(family, bold, italic)]
    code = ord(ch)
    if code in table:
        return table[code]
    if ch in _EXTRA:
        return _EXTRA[ch]
    if code > 0x2E80:          # CJK and friends are full-width
        return 1000
    return _FALLBACK


TOKEN_RE = re.compile(r"(\*\*|\*|_\{|\^\{|\}|_|\^)")


def parse_runs(text, bold=False, italic=False):
    r"""Split inline markup into styled runs.

    Returns a list of ``(chars, bold, italic, script)`` where ``script`` is
    ``0`` for baseline, ``-1`` subscript, ``+1`` superscript.

    A backslash escapes the next character, so ``kernel\_size`` is a literal
    underscore rather than a subscript.  Code-derived labels are full of
    identifiers and need this; so does any spec that wants to print an
    asterisk.
    """
    runs, buf = [], []
    b, i, script = bold, italic, 0
    pending_close = []
    j = 0
    def flush():
        if buf:
            runs.append(("".join(buf), b, i, script))
            del buf[:]
    while j < len(text):
        if text[j] == "\\" and j + 1 < len(text):
            buf.append(text[j + 1]); j += 2; continue
        if text.startswith("**", j):
            flush(); b = not b; j += 2; continue
        if text[j] == "*":
            flush(); i = not i; j += 1; continue
        if text.startswith("_{", j) or text.startswith("^{", j):
            flush(); script = -1 if text[j] == "_" else 1
            pending_close.append("brace"); j += 2; continue
        if text[j] == "}" and pending_close:
            flush(); pending_close.pop(); script = 0; j += 1; continue
        if text[j] in "_^" and j + 1 < len(text):
            flush(); script = -1 if text[j] == "_" else 1
            buf.append(text[j + 1]); flush(); script = 0; j += 2; continue
        buf.append(text[j]); j += 1
    flush()
    return runs or [("", b, i, 0)]


SCRIPT_SCALE = 0.72
SCRIPT_RISE = 0.32
SCRIPT_DROP = 0.16


def line_width(line, size, family="times", bold=False, italic=False):
    total = 0.0
    for chars, b, i, script in parse_runs(line, bold, italic):
        s = size * (SCRIPT_SCALE if script else 1.0)
        for ch in chars:
            total += glyph_width(ch, family, b, i) * s / 1000.0
    return total


def measure(text, size, family="times", bold=False, italic=False, leading=1.18):
    """Return ``(width, height, lines)`` in points for a multi-line label."""
    lines = str(text).split("\n") if text else [""]
    w = max((line_width(ln, size, family, bold, italic) for ln in lines), default=0.0)
    h = size * leading * len(lines) if len(lines) > 1 else size
    return w, h, lines


def wrap(text, max_width, size, family="times", bold=False, italic=False):
    """Greedy word wrap, honouring explicit newlines already in ``text``."""
    out = []
    for para in str(text).split("\n"):
        words, cur = para.split(), ""
        for word in words:
            trial = (cur + " " + word).strip()
            if cur and line_width(trial, size, family, bold, italic) > max_width:
                out.append(cur)
                cur = word
            else:
                cur = trial
        out.append(cur)
    return "\n".join(out)
