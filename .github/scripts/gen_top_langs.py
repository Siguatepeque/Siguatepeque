#!/usr/bin/env python3
"""Self-contained top-languages SVG card.

Fetches the user's repos + language byte counts from the GitHub REST API
(token optional, via GITHUB_TOKEN env) and renders a compact dark card
matching the profile's terminal palette. No external generator service.
Output: ./profile/top-langs.svg relative to the repo root.
"""
import json
import os
import pathlib
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
os.chdir(REPO_ROOT)

USER = "Siguatepeque"
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-card-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def main():
    try:
        repos = api(f"/users/{USER}/repos?per_page=100&sort=updated")
        langs = {}
        for repo in repos:
            if repo.get("fork") or not repo.get("size"):
                continue
            name = repo["name"]
            ls = api(f"/repos/{USER}/{name}/languages")
            for lang, bytes_ in ls.items():
                langs[lang] = langs.get(lang, 0) + bytes_
        if not langs:
            raise RuntimeError("no language data available")
        total = sum(langs.values())
        top = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:5]
        shares = [(lang, b / total * 100) for lang, b in top]
        labels = " ".join(f"{lang} {p:.0f}%" for lang, p in shares)
    except Exception as e:
        # honest error card - never fabricate data
        svg = (
            '<svg width="440" height="90" viewBox="0 0 440 90" '
            'xmlns="http://www.w3.org/2000/svg" role="img">'
            f'<title>most used languages</title>'
            f'<rect width="440" height="90" rx="6" fill="#010409"/>'
            f'<text x="20" y="34" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            f'font-size="16" font-weight="600" fill="#7ee787">most used languages</text>'
            f'<text x="20" y="62" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            f'font-size="12" fill="#8b949e">unavailable: {esc(str(e))[:60]}</text>'
            f'</svg>'
        )
        pathlib.Path("profile").mkdir(exist_ok=True)
        pathlib.Path("profile/top-langs.svg").write_text(svg, encoding="utf-8")
        print(f"error card written: {svg[:120]}...")
        sys.exit(1)

    n = len(shares)
    width = 440
    height = 150
    MONO = "ui-monospace,SFMono-Regular,Consolas,'Cascadia Mono',monospace"
    LANG_C = {"Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
              "HTML": "#e34c26", "CSS": "#563d7c", "Jupyter Notebook": "#DA5B0B",
              "Rust": "#dea584", "Go": "#00ADD8", "Shell": "#89e051"}

    # stacked proportional bar
    bar_top = 56
    bar_h = 12
    bar_x = 20
    bar_w = width - 40
    x = bar_x
    segs = []
    for i, (lang, pct) in enumerate(shares):
        w = max(2.0, bar_w * pct / 100)
        color = LANG_C.get(lang, "#7ee787")
        segs.append(
            f'<rect x="{x:.1f}" y="{bar_top}" width="{w:.1f}" height="{bar_h}" '
            f'rx="2" fill="{color}"/>'
        )
        x += w

    # legend rows
    legend = []
    ly = bar_top + 34
    for lang, pct in shares:
        color = LANG_C.get(lang, "#7ee787")
        legend.append(
            f'<circle cx="26" cy="{ly-4}" r="4" fill="{color}"/>'
            f'<text x="38" y="{ly}" font-family="{MONO}" font-size="12" fill="#c9d1d9">{esc(lang)}</text>'
            f'<text x="{width-24}" y="{ly}" text-anchor="end" font-family="{MONO}" font-size="12" fill="#8b949e">{pct:.1f}%</text>'
        )
        ly += 18
    height = ly + 6

    svg = (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="most used languages">'
        "<title>most used languages</title>"
        f'<rect width="{width}" height="{height}" rx="10" fill="#010409" stroke="#30363d"/>'
        # window chrome
        '<circle cx="28" cy="24" r="5" fill="#f85149"/>'
        '<circle cx="44" cy="24" r="5" fill="#d29922"/>'
        '<circle cx="60" cy="24" r="5" fill="#7ee787"/>'
        f'<text x="80" y="28" font-family="{MONO}" font-size="13" fill="#7ee787">$ tokei --languages</text>'
        f'<line x1="20" y1="42" x2="{width-20}" y2="42" stroke="#21262d"/>'
        + "".join(segs)
        + "".join(legend)
        + "</svg>"
    )
    pathlib.Path("profile").mkdir(exist_ok=True)
    pathlib.Path("profile/top-langs.svg").write_text(svg, encoding="utf-8")
    print(f"top-langs.svg written ({len(svg)} bytes): {labels}")


if __name__ == "__main__":
    main()