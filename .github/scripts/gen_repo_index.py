#!/usr/bin/env python3
"""Auto-discover public repos and render an interactive repo-index SVG.

No project is hardcoded: repos come from the GitHub REST API at CI time
(GITHUB_TOKEN provided by the workflow). Layout: one terminal-styled row per
repo, newest-pushed first, capped at MAX_ROWS. Each row's name is a clickable
link in the SVG (GitHub's README sanitizer keeps <a> inside SVG images).

Output: ./profile/repo-index.svg relative to repo root.
"""
import datetime as dt
import json
import os
import pathlib
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
os.chdir(REPO_ROOT)

USER = "Siguatepeque"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_ROWS = 8

LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "Jupyter Notebook": "#DA5B0B", "HTML": "#e34c26", "CSS": "#563d7c",
    "Rust": "#dea584", "Go": "#00ADD8", "C++": "#f34b7d", "C": "#555555",
    "Shell": "#89e051", "Java": "#b07219", "Lua": "#000080",
}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "profile-card-generator")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def trunc(s, n):
    s = (s or "").strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def main():
    try:
        repos = api(f"/users/{USER}/repos?per_page=100&sort=pushed&direction=desc")
        repos = [r for r in repos if not r.get("fork") and r["name"] != USER]
        repos.sort(key=lambda r: r.get("pushed_at") or "", reverse=True)
        repos = repos[:MAX_ROWS]
    except Exception as e:  # honest failure card, never fabricate
        repos = None
        err = str(e)

    W = 720
    ROW_H = 46
    HEAD = 64
    PAD = 18
    H = HEAD + (len(repos) if repos else 1) * ROW_H + PAD * 2 + 18
    MONO = "ui-monospace,SFMono-Regular,Consolas,'Cascadia Mono',monospace"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">',
        '<title id="t">Live repository index</title>',
        '<desc id="d">Auto-generated list of public repositories, newest activity first.</desc>',
        f'<rect width="{W}" height="{H}" rx="10" fill="#010409" stroke="#30363d"/>',
        # window chrome
        f'<circle cx="{PAD+8}" cy="24" r="5" fill="#f85149"/>',
        f'<circle cx="{PAD+24}" cy="24" r="5" fill="#d29922"/>',
        f'<circle cx="{PAD+40}" cy="24" r="5" fill="#7ee787"/>',
        f'<text x="{PAD+62}" y="29" font-family="{MONO}" font-size="13" fill="#7ee787">$ ls -la --sort=activity</text>',
        f'<line x1="{PAD}" y1="42" x2="{W-PAD}" y2="42" stroke="#21262d"/>',
        f'<text x="{PAD}" y="58" font-family="{MONO}" font-size="11" fill="#8b949e">name</text>',
        f'<text x="{W-PAD}" y="58" text-anchor="end" font-family="{MONO}" font-size="11" fill="#8b949e">lang · ★ · pushed</text>',
    ]

    y = HEAD + PAD - 6
    if not repos:
        parts.append(
            f'<text x="{PAD}" y="{y}" font-family="{MONO}" font-size="13" fill="#f85149">index unavailable: {esc(err)[:80]}</text>'
        )
    else:
        for r in repos:
            name = r["name"]
            url = r["html_url"]
            lang = r.get("language") or "-"
            desc = trunc(r.get("description"), 74)
            stars = r.get("stargazers_count", 0)
            pushed = (r.get("pushed_at") or "")[:10]
            lc = LANG_COLORS.get(lang, "#8b949e")
            parts += [
                f'<a href="{esc(url)}" target="_blank">',
                f'  <rect x="{PAD-6}" y="{y-16}" width="{W-2*PAD+12}" height="{ROW_H-4}" rx="6" fill="#0d1117" opacity="0.55"/>',
                f'  <text x="{PAD}" y="{y+2}" font-family="{MONO}" font-size="14" fill="#58a6ff">{esc(name)}</text>',
                f'  <text x="{PAD}" y="{y+19}" font-family="{MONO}" font-size="11" fill="#8b949e">{esc(desc)}</text>',
                f'</a>',
                f'<circle cx="{W-PAD-150}" cy="{y-2}" r="5" fill="{lc}"/>',
                f'<text x="{W-PAD-138}" y="{y+2}" font-family="{MONO}" font-size="12" fill="#c9d1d9">{esc(lang)}</text>',
                f'<text x="{W-PAD}" y="{y+2}" text-anchor="end" font-family="{MONO}" font-size="12" fill="#d29922">★{stars} <tspan fill="#8b949e">{pushed}</tspan></text>',
            ]
            y += ROW_H

    parts.append(
        f'<text x="{W/2}" y="{H-10}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="#484f58">rebuilt daily by github actions · no projects hardcoded</text>'
    )
    parts.append("</svg>")

    out = REPO_ROOT / "profile" / "repo-index.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(parts), encoding="utf-8")
    print(f"repo-index.svg written: {len(repos) if repos else 0} repos")


if __name__ == "__main__":
    main()
