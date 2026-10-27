"""Heuristic QA: measure wrapped text height with Calibri metrics vs. each shape's height,
and flag shapes that extend beyond the slide."""
import sys

from PIL import ImageFont
from pptx import Presentation

FONTS = {False: "C:/Windows/Fonts/calibri.ttf", True: "C:/Windows/Fonts/calibrib.ttf"}
_cache = {}


def font(size, bold):
    k = (round(size * 4), bold)
    if k not in _cache:
        _cache[k] = ImageFont.truetype(FONTS[bold], int(size * 4))  # 4x for precision
    return _cache[k]


def width_pt(text, size, bold):
    return font(size, bold).getlength(text) / 4.0


def para_lines(runs, max_w):
    """runs: list of (text, size, bold). Greedy word wrap; returns (lines, max_size)."""
    words, size = [], 14
    for t, sz, b in runs:
        size = max(size, sz) if words else sz
        for w in t.split(" "):
            words.append((w, sz, b))
    lines, cur = 1, 0.0
    for w, sz, b in words:
        ww = width_pt(w + " ", sz, b)
        if cur + ww > max_w + 0.5 and cur > 0:
            lines += 1
            cur = ww
        else:
            cur += ww
    return lines, max(sz for _, sz, _ in words) if words else 14


def main(path):
    prs = Presentation(path)
    SW, SH = prs.slide_width, prs.slide_height
    problems = 0
    for n, slide in enumerate(prs.slides, 1):
        for sh in slide.shapes:
            if sh.left is not None and (sh.left < 0 or sh.top < 0 or sh.left + sh.width > SW + 10 or sh.top + sh.height > SH + 10):
                print(f"slide {n}: '{sh.name}' extends beyond slide")
                problems += 1
            if not sh.has_text_frame or not sh.text_frame.text.strip():
                continue
            tf = sh.text_frame
            ml = (tf.margin_left or 0) / 12700
            mr = (tf.margin_right or 0) / 12700
            mt = (tf.margin_top or 0) / 12700
            mb = (tf.margin_bottom or 0) / 12700
            avail_w = sh.width / 12700 - ml - mr
            total_h = mt + mb
            for p in tf.paragraphs:
                runs = []
                for r in p.runs:
                    sz = r.font.size.pt if r.font.size else 18
                    runs.append((r.text, sz, bool(r.font.bold)))
                if not runs:
                    total_h += 14 * 1.2
                    continue
                indent = 0.25 * 72 if p._p.pPr is not None and p._p.pPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}buChar") is not None else 0
                lines, sz = para_lines(runs, avail_w - indent)
                after = 0
                if p._p.pPr is not None:
                    spc = p._p.pPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}spcAft")
                    if spc is not None and len(spc):
                        after = float(spc[0].get("val")) / 100
                total_h += lines * sz * 1.2 + after
            avail_h = sh.height / 12700
            if total_h > avail_h + 3:
                txt = tf.text.strip().replace("\n", " ")[:50]
                print(f"slide {n}: OVERFLOW need {total_h:.0f}pt > {avail_h:.0f}pt  [{txt}]")
                problems += 1
    print("fit problems:", problems)


main(sys.argv[1])
