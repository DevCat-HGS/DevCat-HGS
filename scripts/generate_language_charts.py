"""Genera las gráficas de lenguajes del perfil a partir de la API de GitHub.

Se miden dos cosas distintas porque responden a preguntas distintas:
  - Volumen de código: bytes por lenguaje, indica dónde está el peso del trabajo.
  - Amplitud de uso: en cuántos repositorios aparece, indica qué se usa a diario.

El conteo de bytes de GitHub incluye artefactos de compilación y proyectos
duplicados, por lo que SKIPPED_REPOS y IGNORED_LANGUAGES los descartan.
"""

import json
import os
import sys
import urllib.error
import urllib.request

USER = "DevCat-HGS"
API = "https://api.github.com"
OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "profile")

# GameDB commitea su carpeta build/, donde qrc_resources.cpp (13 MB generados por
# Qt) representaría por sí solo la mitad del perfil. UnityCW, GameExp y
# RespaldoGame son copias del mismo proyecto Unity que CashWin.
SKIPPED_REPOS = {"GameDB", "UnityCW", "GameExp", "RespaldoGame"}

# Lenguajes que produce el motor o el sistema de build, no escritos a mano.
IGNORED_LANGUAGES = {
    "ShaderLab", "HLSL", "CMake", "Makefile", "QMake",
    "Batchfile", "Objective-C", "Objective-C++",
}

COLORS = {
    "C#": "#178600", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Vue": "#41b883", "Dart": "#00b4ab", "Python": "#3572a5",
    "CSS": "#663399", "HTML": "#e34c26", "Kotlin": "#a97bff",
    "C++": "#f34b7d", "C": "#555555", "Astro": "#ff5a03",
    "Swift": "#f05138", "PHP": "#4f5d95", "Shell": "#89e051",
    "Dockerfile": "#384d54", "MDX": "#fcb32c", "SCSS": "#c6538c",
    "Java": "#b07219", "Go": "#00add8", "Rust": "#dea584",
    "Jupyter Notebook": "#da5b0b", "Svelte": "#ff3e00",
}
FALLBACK_COLOR = "#8b949e"

TOP_N = 8
BAR_W = 200
ROW_H = 26
PANEL_W = 430
PAD = 22


def request(path, token):
    req = urllib.request.Request(API + path)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-chart-generator")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp), resp.headers.get("Link", "")


def paginate(path, token):
    repos, page = [], 1
    while True:
        batch, link = request(path + str(page), token)
        repos.extend(batch)
        if 'rel="next"' not in link:
            return repos
        page += 1


def fetch_repos(token):
    """Incluye repositorios privados si el token lo permite.

    El GITHUB_TOKEN de Actions está limitado al repositorio actual y no puede
    consultar /user/repos, así que en ese caso se usa el listado público.
    """
    public = "/users/%s/repos?per_page=100&type=owner&page=" % USER
    if token:
        try:
            repos = paginate(
                "/user/repos?per_page=100&affiliation=owner&visibility=all&page=",
                token,
            )
        except urllib.error.HTTPError as err:
            if err.code not in (401, 403):
                raise
            print("Sin acceso a repos privados; se usa el listado público.")
            repos = paginate(public, token)
    else:
        repos = paginate(public, None)
    return [r for r in repos if not r["fork"] and r["name"] not in SKIPPED_REPOS]


def collect(token):
    by_bytes, by_repo_count = {}, {}
    for repo in fetch_repos(token):
        try:
            langs, _ = request("/repos/%s/languages" % repo["full_name"], token)
        except urllib.error.HTTPError:
            continue
        for name, size in langs.items():
            if name in IGNORED_LANGUAGES:
                continue
            by_bytes[name] = by_bytes.get(name, 0) + size
            by_repo_count[name] = by_repo_count.get(name, 0) + 1
    return by_bytes, by_repo_count


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def panel(title, rows, total, suffix, x_offset):
    """Dibuja un panel de barras horizontales. rows es [(nombre, valor)]."""
    top = max(v for _, v in rows) if rows else 1
    parts = [
        '<text x="%d" y="%d" class="title">%s</text>'
        % (x_offset + PAD, PAD + 14, esc(title))
    ]
    for i, (name, value) in enumerate(rows):
        y = PAD + 42 + i * ROW_H
        width = max(3, round(BAR_W * value / top))
        color = COLORS.get(name, FALLBACK_COLOR)
        if suffix == "%":
            label = "%.1f%%" % (value / total * 100)
        else:
            label = "%d repos" % value
        parts.append(
            '<text x="%d" y="%d" class="lang">%s</text>'
            '<rect x="%d" y="%d" width="%d" height="9" rx="4.5" class="track"/>'
            '<rect x="%d" y="%d" width="%d" height="9" rx="4.5" fill="%s"/>'
            '<text x="%d" y="%d" class="value">%s</text>'
            % (
                x_offset + PAD, y + 9, esc(name),
                x_offset + PAD + 96, y + 1, BAR_W, 
                x_offset + PAD + 96, y + 1, width, color,
                x_offset + PAD + 96 + BAR_W + 10, y + 9, label,
            )
        )
    return "\n  ".join(parts)


def render(by_bytes, by_repo_count):
    total_bytes = sum(by_bytes.values())
    top_bytes = sorted(by_bytes.items(), key=lambda kv: -kv[1])[:TOP_N]
    top_count = sorted(by_repo_count.items(), key=lambda kv: -kv[1])[:TOP_N]

    height = PAD * 2 + 42 + ROW_H * TOP_N
    width = PANEL_W * 2

    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Lenguajes de programación utilizados">
  <style>
    .title {{ font: 600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #24292f; }}
    .lang  {{ font: 400 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; fill: #24292f; }}
    .value {{ font: 400 11px ui-monospace, SFMono-Regular, Consolas, monospace; fill: #57606a; }}
    .track {{ fill: #d0d7de; opacity: .45; }}
    .card  {{ fill: #ffffff; stroke: #d0d7de; }}
    @media (prefers-color-scheme: dark) {{
      .title, .lang {{ fill: #e6edf3; }}
      .value {{ fill: #8b949e; }}
      .track {{ fill: #30363d; opacity: 1; }}
      .card  {{ fill: #0d1117; stroke: #30363d; }}
    }}
  </style>
  <rect x="0.5" y="0.5" width="{wm}" height="{hm}" rx="6" class="card"/>
  {left}
  {right}
</svg>
""".format(
        w=width, h=height, wm=width - 1, hm=height - 1,
        left=panel("Volumen de código", top_bytes, total_bytes, "%", 0),
        right=panel("Amplitud de uso", top_count, 0, "repos", PANEL_W),
    )


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    by_bytes, by_repo_count = collect(token)
    if not by_bytes:
        sys.exit("No se obtuvieron datos de lenguajes.")
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, "languages.svg")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(render(by_bytes, by_repo_count))
    print("Generado %s (%d lenguajes)" % (path, len(by_bytes)))


if __name__ == "__main__":
    main()
