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
    bar_h = 8
    bar_top = 48
    seg_gap = 2
    seg_w = (width - 40 - seg_gap * (n - 1)) / n
    segs = []
    opacity = [1.0, 0.78, 0.58, 0.42, 0.3]
    x = 20
    for i, (lang, pct) in enumerate(shares):
        w = seg_w * (pct / 100) * 0.9 + seg_w * 0.1  # floor so tiny shares stay visible
        segs.append(
            f'<rect x="{x:.1f}" y="{bar_top}" width="{w:.1f}" height="{bar_h}" '
            f'rx="3" fill="#7ee787" opacity="{opacity[i % len(opacity)]}"/>'
        )
        x += seg_w

    svg = (
        '<svg width="440" height="100" viewBox="0 0 440 100" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="most used languages">'
        "<title>most used languages</title>"
        '<rect width="440" height="100" rx="6" fill="#010409"/>'
        '<text x="20" y="28" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        'font-size="16" font-weight="600" fill="#7ee787">most used languages</text>'
        + "".join(segs)
        + f'<text x="20" y="{bar_top + bar_h + 18}" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        f'font-size="12" fill="#8b949e">{esc(labels)}</text>'
        "</svg>"
    )
    pathlib.Path("profile").mkdir(exist_ok=True)
    pathlib.Path("profile/top-langs.svg").write_text(svg, encoding="utf-8")
    print(f"top-langs.svg written ({len(svg)} bytes): {labels}")


if __name__ == "__main__":
    main()