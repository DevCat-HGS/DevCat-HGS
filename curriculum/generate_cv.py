#!/usr/bin/env python3
"""Genera la hoja de vida (EN y ES) en PDF a partir de cv_data.json.

Pensado para pasar filtros ATS: una sola columna, texto real (sin imágenes ni
tablas), fuente estándar, encabezados convencionales y fechas consistentes.

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
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_ITALIC = "Helvetica-Oblique"
INK = colors.HexColor("#111111")
MUTED = colors.HexColor("#444444")
RULE = colors.HexColor("#888888")


def styles() -> dict[str, ParagraphStyle]:
    base = dict(fontName=FONT, textColor=INK, alignment=TA_LEFT, fontSize=9.6, leading=12.6)
    return {
        "name": ParagraphStyle("name", **{**base, "fontName": FONT_BOLD, "fontSize": 20, "leading": 24}),
        "title": ParagraphStyle("title", **{**base, "fontSize": 11.5, "leading": 15, "textColor": MUTED}),
        "contact": ParagraphStyle("contact", **{**base, "fontSize": 9, "leading": 12, "textColor": MUTED}),
        "h": ParagraphStyle(
            "h", **{**base, "fontName": FONT_BOLD, "fontSize": 10.5, "leading": 13, "spaceBefore": 10, "spaceAfter": 2}
        ),
        "body": ParagraphStyle("body", **base),
        "role": ParagraphStyle("role", **{**base, "fontName": FONT_BOLD, "fontSize": 10.2, "spaceBefore": 4}),
        "meta": ParagraphStyle("meta", **{**base, "fontSize": 9, "textColor": MUTED}),
        "bullet": ParagraphStyle("bullet", **{**base, "leftIndent": 12, "bulletIndent": 2, "spaceBefore": 1}),
        "small": ParagraphStyle("small", **{**base, "fontSize": 9, "textColor": MUTED, "leftIndent": 12}),
    }


def p(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(escape(text), style)


def rich(markup: str, style: ParagraphStyle) -> Paragraph:
    """Paragraph con marcado ya escapado (negritas/enlaces)."""
    return Paragraph(markup, style)


def heading(text: str, st: dict[str, ParagraphStyle]) -> list:
    return [
        p(text.upper(), st["h"]),
        HRFlowable(width="100%", thickness=0.6, color=RULE, spaceBefore=0, spaceAfter=3),
    ]


def date_range(item: dict, labels: dict) -> str:
    return f'{item["start"]} - {item["end"] or labels["present"]}'


def strip_scheme(url: str) -> str:
    return url.replace("https://", "").replace("http://", "").rstrip("/")


def build(data: dict, lang: str, out: Path) -> None:
    c = data[lang]
    lb = c["labels"]
    st = styles()
    doc = SimpleDocTemplate(
        str(out),
        pagesize=LETTER,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
        title=f'{data["name"]} - {c["title"]}',
        author=data["name"],
        subject="Curriculum Vitae" if lang == "en" else "Hoja de vida",
        keywords=", ".join(["Full Stack", "React", "Next.js", "Node.js", "Flutter", "AWS", "TypeScript"]),
        invariant=1,  # PDF idéntico entre ejecuciones: no genera commits por ruido
    )

    flow: list = []
    flow.append(p(data["name"], st["name"]))
    flow.append(p(c["title"], st["title"]))

    contact = [
        escape(c["location"]),
        f'<a href="mailto:{data["email"]}" color="#444444">{escape(data["email"])}</a>',
        f'<a href="{data["linkedin"]}" color="#444444">{escape(strip_scheme(data["linkedin"]))}</a>',
        f'<a href="{data["github"]}" color="#444444">{escape(strip_scheme(data["github"]))}</a>',
    ]
    flow.append(rich("  |  ".join(contact), st["contact"]))

    flow += heading(lb["summary"], st)
    flow.append(p(c["summary"], st["body"]))

    flow += heading(lb["experience"], st)
    for job in c["experience"]:
        block = [
            p(f'{job["role"]}, {job["company"]}', st["role"]),
            p(f'{job["place"]}  |  {date_range(job, lb)}', st["meta"]),
        ]
        for b in job["bullets"]:
            block.append(Paragraph(escape(b), st["bullet"], bulletText="-"))
        block.append(p(f'{lb["stack"]}: {job["stack"]}', st["small"]))
        flow.append(KeepTogether(block))

    flow += heading(lb["skills"], st)
    for label, items in c["skills"]:
        flow.append(rich(f"<b>{escape(label)}:</b> {escape(items)}", st["body"]))

    flow += heading(lb["projects"], st)
    for prj in c["projects"]:
        head = f"<b>{escape(prj['name'])}</b>"
        if prj["client"]:
            head += f' <font name="{FONT}">| {escape(lb["client"])}: {escape(prj["client"])}</font>'
        block = [
            rich(head, st["role"]),
            p(prj["text"], st["body"]),
            p(f'{lb["stack"]}: {prj["stack"]}', st["small"]),
        ]
        flow.append(KeepTogether(block))

    if c.get("education"):
        flow += heading(lb["education"], st)
        for ed in c["education"]:
            flow.append(p(f'{ed["degree"]}, {ed["institution"]}', st["role"]))
            flow.append(p(f'{ed.get("place", "")}  |  {date_range(ed, lb)}', st["meta"]))

    flow.append(Spacer(1, 2))
    doc.build(flow)


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
