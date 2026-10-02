#!/usr/bin/env python3
"""Actualiza la sección "Private Work" de los README con una lista OPT-IN de repositorios privados.

Nada se publica por defecto: solo aparecen los repos que tú escribes en featured.json, con el título y la
descripción públicos que tú redactas (sin nombres de cliente salvo que lo pidas). Los repos privados se
muestran con la etiqueta "Private repository" y SIN enlace, porque para los demás darían 404.

Con un token (GH_TOKEN / METRICS_TOKEN) verifica que cada repo exista y avisa si su visibilidad no coincide.

Uso:
  python privacity/update_private_repos.py            # escribe los README
  python privacity/update_private_repos.py --check    # no escribe; falla si algo está desactualizado
  python privacity/update_private_repos.py --no-verify  # sin llamadas a la API de GitHub
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
API = "https://api.github.com"
START = "<!-- PRIVATE-REPOS:START -->"
END = "<!-- PRIVATE-REPOS:END -->"

TEXTS = {
    "en": {
        "readme": "README.md",
        "heading": "Private Work",
        "intro": "Selected work from private repositories. The code is not public; titles and descriptions are written for this page.",
        "cols": ("Project", "Description", "Stack", "Status"),
        "private": "Private repository",
        "public": "Public repository",
        "updated": "updated",
        "client": "Client",
        "months": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
    },
    "es": {
        "readme": "README.es.md",
        "heading": "Trabajo Privado",
        "intro": "Trabajo seleccionado de repositorios privados. El código no es público; los títulos y descripciones están escritos para esta página.",
        "cols": ("Proyecto", "Descripción", "Stack", "Estado"),
        "private": "Repositorio privado",
        "public": "Repositorio público",
        "updated": "actualizado",
        "client": "Cliente",
        "months": ["ene.", "feb.", "mar.", "abr.", "may.", "jun.", "jul.", "ago.", "sep.", "oct.", "nov.", "dic."],
    },
}


class Problem(Exception):
    """Error de configuración o de verificación: se corrige en featured.json."""


# --------------------------------------------------------------------------- GitHub
def gh(path: str, token: str) -> tuple[int, dict]:
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "privacity-readme-updater",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        return err.code, {}


def verify(entry: dict, token: str) -> dict:
    """Consulta la API. Devuelve la visibilidad real y la fecha del último push."""
    repo = entry["repo"]
    status, data = gh(f"/repos/{repo}", token)
    if status in (401, 403):
        raise Problem(f"{repo}: el token no es válido o no tiene permiso (HTTP {status}).")
    if status == 404:
        raise Problem(f"{repo}: no existe o el token no tiene acceso. Revisa el nombre (owner/name) y el alcance del token.")
    if status != 200:
        raise Problem(f"{repo}: respuesta inesperada de GitHub (HTTP {status}).")

    real_private = bool(data["private"])
    declared = entry.get("private")
    if declared is not None and bool(declared) != real_private:
        side = "PRIVADO" if real_private else "PÚBLICO"
        print(f"AVISO {repo}: en featured.json dice private={declared}, pero en GitHub es {side}. Se usa el valor real.")
    return {"private": real_private, "pushed_at": data.get("pushed_at"), "archived": data.get("archived", False)}


# --------------------------------------------------------------------------- validación
def validate(entry: dict, blocked: list[str]) -> None:
    repo = entry.get("repo", "")
    if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise Problem(f"repo inválido: {repo!r}. Usa el formato owner/name.")
    for lang in TEXTS:
        if not entry.get("title", {}).get(lang):
            raise Problem(f"{repo}: falta title.{lang}")
        if not entry.get("description", {}).get(lang):
            raise Problem(f"{repo}: falta description.{lang}")

    visible = " ".join(
        [*entry["title"].values(), *entry["description"].values(), *entry.get("stack", []), entry.get("url", "")]
    ).lower()
    for term in blocked:
        if term.lower() in visible:
            raise Problem(f"{repo}: el texto público contiene el término bloqueado {term!r}. Quítalo o sácalo de blocked_terms.")


# --------------------------------------------------------------------------- render
def cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def fmt_date(iso: str, lang: str) -> str:
    d = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    return f'{TEXTS[lang]["months"][d.month - 1]} {d.year}'


def status_cell(entry: dict, info: dict | None, lang: str) -> str:
    t = TEXTS[lang]
    private = info["private"] if info else bool(entry.get("private", True))
    if private:
        badge = f'![{t["private"]}](https://img.shields.io/badge/-{t["private"].replace(" ", "%20")}-555555?style=flat-square&logo=github&logoColor=white)'
    else:
        badge = f'![{t["public"]}](https://img.shields.io/badge/-{t["public"].replace(" ", "%20")}-2ea44f?style=flat-square&logo=github&logoColor=white)'
    out = badge
    if info and info.get("pushed_at") and entry.get("show_updated", True):
        out += f' {t["updated"]} {fmt_date(info["pushed_at"], lang)}'
    return out


def title_cell(entry: dict, info: dict | None, lang: str) -> str:
    title = cell(entry["title"][lang])
    private = info["private"] if info else bool(entry.get("private", True))
    # Un repo privado nunca se enlaza (daría 404). Si hay una URL pública (sitio en vivo), se usa esa.
    link = entry.get("url") or (None if private else f'https://github.com/{entry["repo"]}')
    if link:
        return f"[**{title}**]({link})"
    return f"**{title}**"


def build_block(entries: list[dict], infos: dict[str, dict | None], lang: str) -> str:
    if not entries:
        return ""  # sin repos elegidos: la sección no aparece
    t = TEXTS[lang]
    rows = []
    for e in entries:
        desc = cell(e["description"][lang])
        if e.get("show_client") and e.get("client"):
            desc += f' ({t["client"]}: {cell(e["client"])})'
        stack = " ".join(f"`{cell(s)}`" for s in e.get("stack", []))
        rows.append(f'| {title_cell(e, infos[e["repo"]], lang)} | {desc} | {stack} | {status_cell(e, infos[e["repo"]], lang)} |')
    head = f'| {t["cols"][0]} | {t["cols"][1]} | {t["cols"][2]} | {t["cols"][3]} |\n| :--- | :--- | :--- | :--- |'
    return f'## {t["heading"]}\n\n{t["intro"]}\n\n{head}\n' + "\n".join(rows) + "\n\n---\n"


def replace_section(text: str, block: str, readme: str) -> str:
    if START not in text or END not in text:
        raise Problem(
            f"{readme}: faltan los marcadores. Añade estas dos líneas donde quieras la sección:\n  {START}\n  {END}"
        )
    eol = "\r\n" if "\r\n" in text else "\n"
    inner = eol + (block.replace("\n", eol) if block else "")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    return pattern.sub(lambda _m: f"{START}{inner}{END}", text, count=1)


# --------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "featured.json")
    ap.add_argument("--root", type=Path, default=REPO, help="carpeta donde están README.md y README.es.md")
    ap.add_argument("--check", action="store_true", help="no escribe: sale con error si algún README está desactualizado")
    ap.add_argument("--no-verify", action="store_true", help="no consulta la API de GitHub")
    args = ap.parse_args()

    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        entries: list[dict] = config.get("repos", [])
        blocked: list[str] = config.get("blocked_terms", [])
        seen: set[str] = set()
        for e in entries:
            validate(e, blocked)
            if e["repo"].lower() in seen:
                raise Problem(f'{e["repo"]}: está repetido en featured.json')
            seen.add(e["repo"].lower())

        token = os.environ.get("GH_TOKEN") or os.environ.get("METRICS_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
        infos: dict[str, dict | None] = {}
        for e in entries:
            if args.no_verify or not token:
                if entries and not args.no_verify:
                    print(f'AVISO {e["repo"]}: sin token, no se verificó la visibilidad (se usa "private" de featured.json).')
                infos[e["repo"]] = None
            else:
                infos[e["repo"]] = verify(e, token)

        changed = False
        for lang, t in TEXTS.items():
            path = args.root / t["readme"]
            raw = path.read_bytes().decode("utf-8")
            new = replace_section(raw, build_block(entries, infos, lang), t["readme"])
            if new != raw:
                changed = True
                if args.check:
                    print(f'DESACTUALIZADO {t["readme"]}')
                else:
                    path.write_bytes(new.encode("utf-8"))
                    print(f'OK {t["readme"]} actualizado ({len(entries)} repo(s))')
            else:
                print(f'OK {t["readme"]} sin cambios')
        return 1 if (changed and args.check) else 0
    except Problem as err:
        print(f"ERROR {err}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
