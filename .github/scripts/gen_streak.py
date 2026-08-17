#!/usr/bin/env python3
"""Self-contained streak SVG card.

Fetches the per-day contribution calendar from GitHub (the same data that
powers the public profile page), computes current + longest streaks, and
renders a minimal dark card matching the profile palette. Written into the
repo by the scheduled workflow, so it is hosted by GitHub itself - no
third-party stats service involved.

Output: ./profile/streak.svg relative to the repo root.
"""
import datetime as dt
import pathlib
import os
import re
import sys
import urllib.request

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
os.chdir(REPO_ROOT)

USER = "Siguatepeque"


def esc(s):
    return (
        s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def fetch_contributions():
    """Return {date:%Y-%m-%d: count} parsed from the public contributions page.

    The per-day cells carry data-date (no year repeat, one per day) and each is
    paired, in document order, with a <tool-tip> whose text is either
    'No contributions on <Month> <Day>th.' or 'N contributions on <Month> <Day>th.'
    Year is resolved by pairing the two ordered lists.
    """
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "streak-card-generator"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    dates = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', html)
    tips = re.findall(r"<tool-tip[^>]*>(.*?)</tool-tip>", html, re.S)
    if not dates or len(tips) != len(dates):
        raise RuntimeError(f"unexpected markup: {len(dates)} dates, {len(tips)} tooltips")
    days = {}
    for date, tip in zip(dates, tips):
        m = re.search(r"No contributions", tip)
        if m:
            days[date] = 0
            continue
        m = re.search(r"(\d+)\s+contribution", tip)
        days[date] = int(m.group(1)) if m else 0
    return days


def compute_streaks(days):
    """Current streak (ending today or yesterday) and longest streak, in days."""
    today = dt.date.today().isoformat()
    active = {d for d, c in days.items() if c > 0}
    if not active:
        return 0, 0
    cur = 0
    d = dt.date.today()
    if d.isoformat() not in active:
        d -= dt.timedelta(days=1)
    while d.isoformat() in active:
        cur += 1
        d -= dt.timedelta(days=1)
    longest = 0
    run = 0
    prev = None
    for date in sorted(active):
        if prev is not None and (dt.date.fromisoformat(date) - dt.date.fromisoformat(prev)).days == 1:
            run += 1
        else:
            run = 1
        longest = max(longest, run)
        prev = date
    return cur, longest


def main():
    try:
        days = fetch_contributions()
        cur, longest = compute_streaks(days)
    except Exception as e:
        svg = (
            '<svg width="440" height="100" viewBox="0 0 440 100" '
            'xmlns="http://www.w3.org/2000/svg" role="img">'
            "<title>streak</title>"
            '<rect width="440" height="100" rx="6" fill="#010409"/>'
            '<text x="20" y="30" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            'font-size="16" font-weight="600" fill="#7ee787">streak</text>'
            '<text x="20" y="60" font-family="Segoe UI, Ubuntu, Sans-Serif" '
            'font-size="12" fill="#8b949e">unavailable: {}</text>'
            "</svg>".format(esc(str(e))[:60])
        )
        pathlib.Path("profile").mkdir(exist_ok=True)
        pathlib.Path("profile/streak.svg").write_text(svg, encoding="utf-8")
        print(f"error card written: {str(e)[:80]}")
        sys.exit(1)

    days_total = len(days)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    svg = (
        '<svg width="440" height="100" viewBox="0 0 440 100" '
        'xmlns="http://www.w3.org/2000/svg" role="img" '
        'aria-label="github streak">'
        "<title>streak</title>"
        '<rect width="440" height="100" rx="6" fill="#010409"/>'
        '<text x="20" y="30" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        'font-size="16" font-weight="600" fill="#7ee787">streak</text>'
        f'<text x="20" y="62" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        f'font-size="26" font-weight="700" fill="#c9d1d9">{cur}'
        f'<tspan font-size="13" fill="#8b949e"> days</tspan></text>'
        f'<text x="150" y="62" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        f'font-size="13" fill="#8b949e">longest: {longest} days</text>'
        f'<text x="20" y="86" font-family="Segoe UI, Ubuntu, Sans-Serif" '
        f'font-size="10" fill="#484f58">{days_total} days of history tracked</text>'
        "</svg>"
    )
    pathlib.Path("profile").mkdir(exist_ok=True)
    pathlib.Path("profile/streak.svg").write_text(svg, encoding="utf-8")
    print(f"streak.svg written: current={cur}d longest={longest}d ({days_total} active days)")


if __name__ == "__main__":
    main()