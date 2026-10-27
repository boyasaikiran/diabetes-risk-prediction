"""Small WordprocessingML generator used to add the report body to the university template.

Everything here emits raw XML strings so the template's styles, cover page and certificate are preserved.
"""
from __future__ import annotations

import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
TEXT_W = 9404  # twips: 12240 - 2*1418
FONT = "Times New Roman"
BODY_SZ = 24  # 12 pt
LINE = 280  # ~1.17 line spacing


def esc(t: str) -> str:
    return escape(t, {'"': "&quot;"})


# ---------------------------------------------------------------- inline runs
def rpr(b=False, i=False, sz=None, font=None, hl=False, sup=False, sub=False, color=None, caps=False) -> str:
    x = ""
    if font:
        x += f'<w:rFonts w:ascii="{font}" w:hAnsi="{font}" w:cs="{font}" w:eastAsia="{font}"/>'
    if b:
        x += "<w:b/><w:bCs/>"
    if i:
        x += "<w:i/><w:iCs/>"
    if caps:
        x += "<w:caps/>"
    if color:
        x += f'<w:color w:val="{color}"/>'
    if sz:
        x += f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>'
    if hl:
        x += '<w:highlight w:val="yellow"/>'
    if sup:
        x += '<w:vertAlign w:val="superscript"/>'
    if sub:
        x += '<w:vertAlign w:val="subscript"/>'
    return f"<w:rPr>{x}</w:rPr>" if x else ""


def run(text: str, **kw) -> str:
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{esc(text)}</w:t></w:r>'


_TOKEN = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+`|\[\[.+?\]\]|\^\{.+?\}|_\{.+?\})")


def inline(text: str, sz=None, b=False, i=False) -> str:
    """Mini-markup: **bold**, *italic*, `code`, [[placeholder]], ^{sup}, _{sub}."""
    out = []
    for part in _TOKEN.split(text):
        if not part:
            continue
        if part.startswith("**"):
            out.append(run(part[2:-2], b=True, i=i, sz=sz))
        elif part.startswith("`"):
            out.append(run(part[1:-1], font="Courier New", sz=(sz or BODY_SZ) - 2, b=b))
        elif part.startswith("[["):
            out.append(run("[" + part[2:-2] + "]", b=b, i=i, sz=sz, hl=True))
        elif part.startswith("^{"):
            out.append(run(part[2:-1], sup=True, b=b, i=i, sz=sz))
        elif part.startswith("_{"):
            out.append(run(part[2:-1], sub=True, b=b, i=i, sz=sz))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append(run(part[1:-1], i=True, b=b, sz=sz))
        else:
            out.append(run(part, b=b, i=i, sz=sz))
    return "".join(out)


# ---------------------------------------------------------------- paragraphs
def para(inner: str, jc="both", before=0, after=120, line=LINE, keep_next=False, page_break_before=False,
         ind_left=0, ind_hanging=0, ind_first=0, style=None, outline=None, num=None, shade=None, keep_lines=False,
         tabs=None, border=False) -> str:
    p = ""
    if style:
        p += f'<w:pStyle w:val="{style}"/>'
    if keep_next:
        p += "<w:keepNext/>"
    if keep_lines:
        p += "<w:keepLines/>"
    if page_break_before:
        p += "<w:pageBreakBefore/>"
    if num:
        p += f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>'
    if border:
        p += '<w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="BBBBBB"/><w:left w:val="single" w:sz="4" w:space="4" w:color="BBBBBB"/><w:bottom w:val="single" w:sz="4" w:space="4" w:color="BBBBBB"/><w:right w:val="single" w:sz="4" w:space="4" w:color="BBBBBB"/></w:pBdr>'
    if shade:
        p += f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>'
    if tabs:
        p += "<w:tabs>" + "".join(f'<w:tab w:val="{k}" w:pos="{v}"/>' for k, v in tabs) + "</w:tabs>"
    p += f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>'
    if ind_left or ind_hanging or ind_first:
        p += f'<w:ind w:left="{ind_left}"' + (f' w:hanging="{ind_hanging}"' if ind_hanging else "") + (f' w:firstLine="{ind_first}"' if ind_first else "") + "/>"
    p += f'<w:jc w:val="{jc}"/>'
    if outline is not None:
        p += f'<w:outlineLvl w:val="{outline}"/>'
    return f"<w:p><w:pPr>{p}</w:pPr>{inner}</w:p>"


def body_p(text: str) -> str:
    return para(inline(text, sz=BODY_SZ), jc="both")


def chapter_heading(num: int, title: str) -> str:
    return (para(run(f"CHAPTER {num}", b=True, sz=28), jc="center", before=0, after=60, page_break_before=True, keep_next=True)
            + para(run(title, b=True, sz=32), jc="center", after=240, keep_next=True, style="Heading1", outline=0,
                   ).replace('<w:pStyle w:val="Heading1"/>', '<w:pStyle w:val="Heading1"/>'))


def h2(num: str, title: str) -> str:
    return para(run(f"{num}  {title}", b=True, sz=28), jc="left", before=240, after=120, keep_next=True, style="Heading2", outline=1)


def h3(text: str) -> str:
    return para(run(text, b=True, sz=24), jc="left", before=160, after=80, keep_next=True, outline=2)


def bullets(items: list[str], numid: int) -> str:
    return "".join(para(inline(t, sz=BODY_SZ), jc="both", after=60, num=numid, ind_left=567, ind_hanging=283) for t in items)


def code_block(text: str) -> str:
    out = []
    lines = text.rstrip("\n").split("\n")
    for k, ln in enumerate(lines):
        out.append(para(run(ln if ln else " ", font="Courier New", sz=18), jc="left", before=0, after=0, line=240,
                        shade="F2F2F2", ind_left=120, keep_lines=True, keep_next=k < len(lines) - 1))
    out.append(para("", after=60, line=240))
    return "".join(out)


def caption(label: str, text: str, above=False) -> str:
    inner = run(label + " ", b=True, sz=22) + inline(text, sz=22, i=True)
    return para(inner, jc="center", before=60 if not above else 160, after=160 if not above else 60, line=252, keep_next=above)


# ---------------------------------------------------------------- tables
def table(header: list[str], rows: list[list[str]], widths: list[int], sz=20, aligns: list[str] | None = None,
          header_fill="DCE6F1", first_col_bold=False) -> str:
    assert sum(widths) <= TEXT_W + 5, (sum(widths), header)
    aligns = aligns or ["left"] * len(header)
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    border = '<w:top w:val="single" w:sz="4" w:color="7F7F7F"/><w:left w:val="single" w:sz="4" w:color="7F7F7F"/><w:bottom w:val="single" w:sz="4" w:color="7F7F7F"/><w:right w:val="single" w:sz="4" w:color="7F7F7F"/><w:insideH w:val="single" w:sz="4" w:color="7F7F7F"/><w:insideV w:val="single" w:sz="4" w:color="7F7F7F"/>'
    x = f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:jc w:val="center"/><w:tblBorders>{border}</w:tblBorders><w:tblLayout w:type="fixed"/><w:tblCellMar><w:top w:w="40" w:type="dxa"/><w:left w:w="80" w:type="dxa"/><w:bottom w:w="40" w:type="dxa"/><w:right w:w="80" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>{grid}</w:tblGrid>'

    keep = len(rows) <= 12

    def cell(text, w, fill=None, bold=False, jc="left", kn=False):
        shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ""
        paras = "".join(para(inline(seg, sz=sz, b=bold), jc=jc, before=0, after=0, line=240, keep_next=kn) for seg in str(text).split("\n"))
        return f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}<w:vAlign w:val="center"/></w:tcPr>{paras}</w:tc>'

    x += '<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>' + "".join(cell(h, w, header_fill, True, "center", keep) for h, w in zip(header, widths, strict=True)) + "</w:tr>"
    for ri, r in enumerate(rows):
        kn = keep and ri < len(rows) - 1
        x += "<w:tr><w:trPr><w:cantSplit/></w:trPr>" + "".join(
            cell(c, w, None, first_col_bold and k == 0, aligns[k], kn) for k, (c, w) in enumerate(zip(r, widths, strict=True))) + "</w:tr>"
    return x + "</w:tbl>" + para("", after=60, line=240)


# ---------------------------------------------------------------- figures
class Media:
    def __init__(self, first_rid: int = 100):
        self.items: list[tuple[str, Path]] = []  # (rId, path)
        self.next = first_rid
        self.docpr = 500

    def add(self, path: Path) -> str:
        rid = f"rId{self.next}"
        self.next += 1
        self.items.append((rid, path))
        return rid


def figure(media: Media, path: Path, width_in: float, alt: str) -> str:
    rid = media.add(path)
    with Image.open(path) as im:
        w, h = im.size
    cx = int(width_in * 914400)
    cy = int(cx * h / w)
    media.docpr += 1
    d = media.docpr
    drawing = (
        f'<w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing">'
        f'<wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{d}" name="Figure {d}" descr="{esc(alt)}"/>'
        f'<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
        f'<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{d}" name="{esc(path.name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
        f'</a:graphicData></a:graphic></wp:inline></w:drawing>'
    )
    return para(f"<w:r>{drawing}</w:r>", jc="center", before=120, after=0, line=240, keep_next=True)


# ---------------------------------------------------------------- equations (OMML)
M = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'


def mr(t: str, plain=False) -> str:
    plain = plain or bool(re.search(r"[A-Za-z]{2,}", t))
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if plain else ""
    return f"<m:r>{sty}<m:t xml:space=\"preserve\">{esc(t)}</m:t></m:r>"


def mfrac(n: str, d: str) -> str:
    return f"<m:f><m:num>{n}</m:num><m:den>{d}</m:den></m:f>"


def msub(b: str, s: str) -> str:
    return f"<m:sSub><m:e>{b}</m:e><m:sub>{s}</m:sub></m:sSub>"


def msup(b: str, s: str) -> str:
    return f"<m:sSup><m:e>{b}</m:e><m:sup>{s}</m:sup></m:sSup>"


def mparen(inner: str) -> str:
    return f"<m:d><m:dPr><m:begChr m:val=\"(\"/><m:endChr m:val=\")\"/></m:dPr><m:e>{inner}</m:e></m:d>"


def msum(lo: str, hi: str, inner: str) -> str:
    return (f"<m:nary><m:naryPr><m:chr m:val=\"∑\"/><m:limLoc m:val=\"undOvr\"/></m:naryPr><m:sub>{lo}</m:sub><m:sup>{hi}</m:sup><m:e>{inner}</m:e></m:nary>")


def equation(label: str, omml: str) -> str:
    """Centered equation with right-aligned number, e.g. (3.1)."""
    inner = (f'<w:r><w:tab/></w:r><m:oMath {M}>{omml}</m:oMath><w:r><w:tab/></w:r>' + run(f"({label})", sz=BODY_SZ))
    return para(inner, jc="left", before=60, after=100, tabs=[("center", TEXT_W // 2), ("right", TEXT_W)], keep_lines=True)
