#!/usr/bin/env python3
"""Genera la hoja de vida (EN y ES) en PDF a partir de cv_data.json.

Pensado para pasar filtros ATS: una sola columna, texto real (sin imágenes ni
tablas), encabezados convencionales y fechas consistentes. La fuente (Inter) va
incrustada con su mapa Unicode, así que el texto sigue siendo extraíble.

Salida:
  curriculum/output/<archivo>.pdf          fuente de verdad
  portfolio/public/cv/<archivo>.pdf        copia que descarga el portafolio
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
FONTS = ROOT / "fonts"

# --- tipografía -------------------------------------------------------------
FONT, FONT_SEMI, FONT_BOLD = "Inter", "Inter-SemiBold", "Inter-Bold"
for name, file in ((FONT, "Inter-Regular.ttf"), (FONT_SEMI, "Inter-SemiBold.ttf"), (FONT_BOLD, "Inter-Bold.ttf")):
    pdfmetrics.registerFont(TTFont(name, str(FONTS / file)))
pdfmetrics.registerFontFamily(FONT, normal=FONT, bold=FONT_BOLD, italic=FONT, boldItalic=FONT_BOLD)

# --- color: sobrio, legible también en blanco y negro ------------------------
NAVY = colors.HexColor("#1B2F55")
INK = colors.HexColor("#1F2937")
MUTED = colors.HexColor("#4B5563")
RULE = colors.HexColor("#C5CCD8")


def styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName=FONT, textColor=INK, alignment=TA_LEFT, fontSize=9.1, leading=12.3)
    return {
        "name": ParagraphStyle("name", **{**base, "fontName": FONT_BOLD, "fontSize": 25, "leading": 29, "textColor": NAVY}),
        "title": ParagraphStyle("title", **{**base, "fontSize": 11.5, "leading": 15, "textColor": MUTED}),
        "contact": ParagraphStyle("contact", **{**base, "fontSize": 8.8, "leading": 12.2, "textColor": MUTED}),
        "h": ParagraphStyle(
            "h",
            **{**base, "fontName": FONT_SEMI, "fontSize": 9.6, "leading": 12, "spaceBefore": 11, "spaceAfter": 2,
               "textColor": NAVY, "charSpace": 0.9, "keepWithNext": 1},
        ),
        "body": ParagraphStyle("body", **base),
        "meta": ParagraphStyle("meta", **{**base, "fontSize": 8.8, "leading": 11.6, "textColor": MUTED}),
        "bullet": ParagraphStyle("bullet", **{**base, "leftIndent": 11, "bulletIndent": 1, "spaceBefore": 1.2, "bulletFontName": FONT, "bulletFontSize": 9.2}),
        "small": ParagraphStyle("small", **{**base, "fontSize": 8.6, "leading": 11.4, "textColor": MUTED, "leftIndent": 11, "spaceBefore": 1}),
        "proj": ParagraphStyle("proj", **{**base, "fontName": FONT_SEMI, "fontSize": 9.8, "spaceBefore": 5, "textColor": colors.HexColor("#111827")}),
    }


class TitleLine(Flowable):
    """Cargo/título a la izquierda y fecha a la derecha, en la misma línea.

    Se dibuja como dos cadenas de texto seguidas, así el extractor del ATS las lee en orden
    natural ("cargo ... fecha"). Si no caben juntas, la fecha baja a una segunda línea.
    """

    def __init__(self, left: str, right: str = "", size: float = 10.2, space_before: float = 5):
        super().__init__()
        self.left, self.right, self.size, self.space_before = left, right, size, space_before
        self.small = 8.8

    def wrap(self, avail_w, avail_h):
        self.avail_w = avail_w
        used = stringWidth(self.left, FONT_SEMI, self.size) + stringWidth(self.right, FONT, self.small) + 14
        self.stacked = bool(self.right) and used > avail_w
        self.height = self.space_before + self.size * 1.3 + (self.small * 1.3 if self.stacked else 0)
        return avail_w, self.height

    def draw(self):
        c = self.canv
        y = self.height - self.space_before - self.size
        c.setFillColor(colors.HexColor("#111827"))
        c.setFont(FONT_SEMI, self.size)
        c.drawString(0, y, self.left)
        if self.right:
            c.setFillColor(MUTED)
            c.setFont(FONT, self.small)
            if self.stacked:
                c.drawString(0, y - self.small * 1.3, self.right)
            else:
                c.drawRightString(self.avail_w, y, self.right)


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def rich(markup: str, style: ParagraphStyle) -> Paragraph:
    """Paragraph con marcado ya escapado (negritas/enlaces)."""
    return Paragraph(markup, style)


def heading(text: str, st: dict[str, ParagraphStyle]) -> list:
    rule = HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=0, spaceAfter=3)
    rule.keepWithNext = 1
    return [p(text.upper(), st["h"]), rule]


def date_range(item: dict, labels: dict) -> str:
    if not item.get("start"):
        return item["end"] or labels["present"]
    return f'{item["start"]} - {item["end"] or labels["present"]}'


def strip_scheme(url: str) -> str:
    return url.replace("https://", "").replace("http://", "").rstrip("/")


def glue_headings(flow: list) -> list:
    """Une cada encabezado (título + línea) con el primer bloque que le sigue."""
    out: list = []
    i = 0
    while i < len(flow):
        item = flow[i]
        if isinstance(item, Paragraph) and item.style.name == "h" and i + 2 < len(flow):
            first = flow[i + 2]
            body = list(first._content) if isinstance(first, KeepTogether) else [first]  # sin KeepTogether anidados
            out.append(KeepTogether([item, flow[i + 1], *body]))
            i += 3
        else:
            out.append(item)
            i += 1
    return out


def build(data: dict, lang: str, out: Path) -> None:
    c = data[lang]
    lb = c["labels"]
    st = styles()
    doc = SimpleDocTemplate(
        str(out),
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
        title=f'{data["name"]} - {c["title"]}',
        author=data["name"],
        subject="Curriculum Vitae" if lang == "en" else "Hoja de vida",
        keywords=", ".join(["Full Stack", "JavaScript", "TypeScript", "Python", "React", "Next.js", "Node.js", "Flutter", "AWS"]),
        invariant=1,  # PDF idéntico entre ejecuciones: no genera commits por ruido
    )

    flow: list = []
    flow.append(p(data["name"], st["name"]))
    flow.append(p(c["title"], st["title"]))
    flow.append(Spacer(1, 3))

    link = 'color="#1B2F55"'
    line1 = [
        escape(c["location"]),
        f'<a href="tel:{data["phone"].replace(" ", "")}" {link}>{escape(data["phone"])}</a>',
        f'<a href="mailto:{data["email"]}" {link}>{escape(data["email"])}</a>',
    ]
    line2 = [
        f'<a href="{data["linkedin"]}" {link}>{escape(strip_scheme(data["linkedin"]))}</a>',
        f'<a href="{data["github"]}" {link}>{escape(strip_scheme(data["github"]))}</a>',
    ]
    flow.append(rich("  |  ".join(line1), st["contact"]))
    flow.append(rich("  |  ".join(line2), st["contact"]))
    if c.get("availability"):
        flow.append(rich(f'<font name="{FONT_SEMI}" color="#1B2F55">{escape(c["availability"])}</font>', st["contact"]))
    flow.append(HRFlowable(width="100%", thickness=1.4, color=NAVY, spaceBefore=6, spaceAfter=0))

    flow += heading(lb["summary"], st)
    flow.append(p(c["summary"], st["body"]))

    flow += heading(lb["experience"], st)
    for job in c["experience"]:
        block = [
            TitleLine(job["role"], date_range(job, lb)),
            p(f'{job["company"]}  |  {job["place"]}', st["meta"]),
        ]
        for b in job["bullets"]:
            block.append(Paragraph(escape(b), st["bullet"], bulletText="-"))
        block.append(p(f'{lb["stack"]}: {job["stack"]}', st["small"]))
        flow.append(KeepTogether(block))

    if c.get("education"):
        flow += heading(lb["education"], st)
        for ed in c["education"]:
            flow.append(
                KeepTogether(
                    [
                        TitleLine(ed["degree"], date_range(ed, lb)),
                        p(f'{ed["institution"]}  |  {ed.get("place", "")}', st["meta"]),
                    ]
                )
            )

    flow += heading(lb["skills"], st)
    for label, items in c["skills"]:
        flow.append(rich(f'<font name="{FONT_BOLD}" color="#1B2F55">{escape(label)}:</font> {escape(items)}', st["body"]))

    flow += heading(lb["projects"], st)
    for prj in c["projects"]:
        head = escape(prj["name"])
        if prj["client"]:
            head += f' <font name="{FONT}" size="8.8" color="#4B5563">|  {escape(lb["client"])}: {escape(prj["client"])}</font>'
        flow.append(
            KeepTogether(
                [
                    rich(head, st["proj"]),
                    p(prj["text"], st["body"]),
                    p(f'{lb["stack"]}: {prj["stack"]}', st["small"]),
                ]
            )
        )

    if c.get("certifications"):
        flow += heading(lb["certifications"], st)
        for cert in c["certifications"]:
            detail = ", ".join(x for x in (cert["issuer"], cert["date"], f'{cert["hours"]} {lb["hours"]}' if cert.get("hours") else "") if x)
            flow.append(Paragraph(escape(f'{cert["name"]} ({detail})'), st["bullet"], bulletText="-"))

    if c.get("awards"):
        flow += heading(lb["awards"], st)
        for aw in c["awards"]:
            detail = ", ".join(x for x in (aw["issuer"], aw["date"]) if x)
            flow.append(Paragraph(escape(f'{aw["name"]} ({detail})'), st["bullet"], bulletText="-"))

    doc.build(glue_headings(flow))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", type=Path, default=ROOT / "cv_data.json")
    ap.add_argument("--out", type=Path, default=ROOT / "output")
    ap.add_argument("--site-dir", type=Path, default=REPO / "portfolio" / "public" / "cv")
    ap.add_argument("--no-site-copy", action="store_true", help="no copiar los PDF al portafolio")
    args = ap.parse_args()

    data = json.loads(args.data.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)

    for lang, filename in data["files"].items():
        target = args.out / filename
        build(data, lang, target)
        print(f"OK {target}")
        if not args.no_site_copy and (REPO / "portfolio").is_dir():
            args.site_dir.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(target, args.site_dir / filename)
            print(f"OK {args.site_dir / filename}")


if __name__ == "__main__":
    main()
