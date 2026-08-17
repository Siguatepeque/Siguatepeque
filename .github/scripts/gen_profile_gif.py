#!/usr/bin/env python3
"""unixporn-grade terminal GIF for the profile README (gifos/github-readme-terminal).

Design: a r/unixporn "rice" screenshot, animated.
  - faux window chrome (traffic lights, "zsh — 96x28")
  - 6-color panes banner + decode/scramble title reveal (gifos effect)
  - neofetch: ASCII logo left, specs right, 2x8 color-block dump (the signature)
  - live repo list from the GitHub API (fallback offline)
  - scrot footer, plays once and settles on the final frame

Font: vendored Cascadia Mono TTF (assets/CascadiaMono.ttf) so box-drawing,
block and powerline glyphs render. Deterministic (seeded RNG).
Writes ~/.config/gifos/ TOMLs before importing gifos (config read at import).
Output: ./output.gif in repo root (CWD must be repo root).
"""
import os
import pathlib
import random

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
os.chdir(REPO_ROOT)

# ---- write gifos configs before import (import reads them) -----------------
cfgdir = pathlib.Path.home() / ".config" / "gifos"
cfgdir.mkdir(parents=True, exist_ok=True)

(cfgdir / "gifos_settings.toml").write_text(
    """[general]
debug = false
cursor = "▮"
show_cursor = true
blink_cursor = true
user_name = "siguatepeque"
fps = 16
color_scheme = "hn"

[files]
frame_base_name = "frame_"
frame_folder_name = "frames"
output_gif_name = "output"
""",
    encoding="utf-8",
)

(cfgdir / "ansi_escape_colors.toml").write_text(
    """[hn]
    [hn.default_colors]
    fg = "#c9d1d9"
    bg = "#010409"

    [hn.normal_colors]
    black = "#161b22"
    red = "#f85149"
    green = "#7ee787"
    yellow = "#d29922"
    blue = "#58a6ff"
    magenta = "#bc8cff"
    cyan = "#39c5cf"
    white = "#c9d1d9"

    [hn.bright_colors]
    black = "#30363d"
    red = "#ff7b72"
    green = "#7ee787"
    yellow = "#e3b341"
    blue = "#79c0ff"
    magenta = "#d2a8ff"
    cyan = "#56d4dd"
    white = "#f0f6fc"
""",
    encoding="utf-8",
)

random.seed(7)

import gifos.gifos as _gifos_mod
from gifos.effects.text_scramble_effect import text_scramble_effect_lines
from PIL import Image

# capture a COPY of every rendered frame (the lib mutates/returns the same
# object) and bypass its ffmpeg-based gen_gif (broken quoting on Windows).
_frames: list = []


def _patched_gen_frame(self, frame=None):
    if frame is None:  # fresh frame
        frame = Image.new(
            "RGB", (self._Terminal__width, self._Terminal__height), self._Terminal__bg_color
        )
        self._Terminal__col_in_row = {_ + 1: 1 for _ in range(self.num_rows)}
        self.cursor_to_box(1, 1)
        return frame
    self._Terminal__frame_count += 1
    _frames.append(frame.copy())
    return frame


_gifos_mod.Terminal._Terminal__gen_frame = _patched_gen_frame
_gifos_mod.Terminal.gen_gif = lambda self: None  # no-op

from gifos.gifos import Terminal  # noqa: E402  (config must exist first)

G = "\\x1b[92m"   # bright green
Y = "\\x1b[93m"   # bright yellow
R = "\\x1b[91m"   # bright red
C = "\\x1b[96m"   # bright cyan
M = "\\x1b[95m"   # bright magenta
B = "\\x1b[94m"   # bright blue
g = "\\x1b[32m"   # green
r = "\\x1b[31m"   # red
y = "\\x1b[33m"   # yellow
b = "\\x1b[34m"   # blue
m = "\\x1b[35m"   # magenta
c = "\\x1b[36m"   # cyan
D = "\\x1b[90m"   # dim
W = "\\x1b[0m"    # reset

FONT = str(REPO_ROOT / "assets" / "CascadiaMono.ttf")
# 960x600, pad 18 -> font 18: width 960/12 = 80 cols; rows (600-36)/(18+5) = 24
t = Terminal(width=960, height=600, xpad=18, ypad=18, font_file=FONT, font_size=18, line_spacing=5)
t.set_fps(16)
t.set_prompt(f"{G}siguatepeque{W}@{Y}github{W} {B}❯{W} ")

SPEED = 1  # frames per typed char

# ── window chrome ────────────────────────────────────────────────────────────
t.gen_text(f"{r}●{W} {y}●{W} {g}●{W}   {D}zsh — siguatepeque@github — 80x24{W}", 1)
t.gen_text(f"{D}{'─' * 79}{W}", 2)
t.clone_frame(12)

# ── panes banner + decode/scramble title ─────────────────────────────────────
PANES = (
    f"{r}██████{W}{y}██████{W}{g}██████{W}{c}██████{W}{b}██████{W}{m}██████{W}"
)
t.gen_text(PANES, 4)
t.gen_text(f"{D}{'─' * 36}{W}", 5)

title_lines = text_scramble_effect_lines(
    "S I G U A T E P E Q U E", multiplier=3, only_upper=True, include_special=False
)
t.gen_text([f"{G}{line}{W}" for line in title_lines], 6)
t.gen_text(f"{C}future biomedical eng · larping on github{W}", 7)
t.gen_text(f"{D}honduras · 20 · hEDS · some computer stuff, some medical stuff{W}", 8)
t.clone_frame(16)

# ── neofetch ─────────────────────────────────────────────────────────────────
t.scroll_up(11)
t.gen_prompt(1)
t.gen_typing_text("neofetch --ascii_distro siguatepeque", 1, contin=True, speed=SPEED)

LOGO = [
    f"{G}       ▄▄▄▄       {W}",
    f"{G}     ▄█░░░░█▄     {W}",
    f"{G}    █░░▄▄░░░█    {W}",
    f"{G}    █░█▀▀█░░█    {W}",
    f"{G}    █░█▄▄█░░█    {W}",
    f"{G}    █░░░░░░░█    {W}",
    f"{G}     ▀█▄▄▄█▀     {W}",
    f"{G}       ▀▀▀▀       {W}",
]
INFO = [
    f"{G}siguatepeque{W}@{C}github{W}",
    f"{D}──────────────────────────{W}",
    f"{Y}os{W}       github.hn {D}(arch, mentally){W}",
    f"{Y}host{W}     honduras · sps/siguatepeque",
    f"{Y}kernel{W}   hEDS-1.0 {D}(running on vibes){W}",
    f"{Y}uptime{W}   20 years",
    f"{Y}shell{W}    zsh + cope",
    f"{Y}de{W}       biomedicine {D}(wip){W}",
    f"{Y}wm{W}       git push --force-with-lease",
    f"{Y}editor{W}   whatever the AI uses",
]
ROW0 = 3
for i, line in enumerate(LOGO):
    t.gen_text(line, ROW0 + i)
for i, line in enumerate(INFO):
    t.gen_text(line, ROW0 + i, col_num=24, contin=True)

# color-block dump: normal + bright rows (the rice signature), below the logo
blocks_norm = "".join(f"\\x1b[{30+i}m███{W}" for i in range(8))
blocks_bright = "".join(f"\\x1b[{90+i}m███{W}" for i in range(8))
t.gen_text(blocks_norm, ROW0 + 12, col_num=3, contin=True)
t.gen_text(blocks_bright, ROW0 + 13, col_num=3, contin=True)
t.clone_frame(22)

# ── pfetch-style one-liner ───────────────────────────────────────────────────
t.scroll_up(15)
t.gen_prompt(1)
t.gen_typing_text("pfetch", 1, contin=True, speed=SPEED)
t.gen_text([
    f"     {C}◆{W}  os     {G}github dot hn{W}",
    f"  {M}◆{W}   {Y}◆{W}  wm     {G}commit --amend{W}",
    f"     {R}◆{W}  shell  {G}zsh, pure prompt{W}",
], 2, count=2)
t.clone_frame(14)

# ── live repo list ───────────────────────────────────────────────────────────
t.scroll_up(8)
t.gen_prompt(1)
t.gen_typing_text("gh repo list --limit 4", 1, contin=True, speed=SPEED)

_repos = [
    "heds-biomarker-discovery",
    "girlfriend-day-emily",
    "detector-caidas",
    "luna-cycle-tracker (private)",
]
try:
    import json as _json
    import urllib.request as _u

    _req = _u.Request(
        "https://api.github.com/users/Siguatepeque/repos?per_page=100&sort=pushed&direction=desc",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "profile-gif"},
    )
    if os.environ.get("GITHUB_TOKEN"):
        _req.add_header("Authorization", f"Bearer {os.environ['GITHUB_TOKEN']}")
    with _u.urlopen(_req, timeout=20) as _r:
        _all = [
            x["name"] + (" (private)" if x.get("private") else "")
            for x in _json.loads(_r.read().decode())
            if not x.get("fork") and x["name"] != "Siguatepeque"
        ]
    if _all:
        _repos = _all[:4]
except Exception:
    pass  # offline CI: fall back to last-known list

_tree_lines = []
for _i, _name in enumerate(_repos):
    _branch = "├──" if _i < len(_repos) - 1 else "╰──"
    _tree_lines.append(f"{D}{_branch}{W} {C}{_name}{W}")
_tree_lines.append("")
t.gen_text(_tree_lines, 2, count=2)
t.clone_frame(14)

# ── scrot footer + exit ──────────────────────────────────────────────────────
t.scroll_up(8)
t.gen_prompt(1)
t.gen_typing_text("scrot ~/rice.png && exit", 1, contin=True, speed=SPEED)
t.gen_text(f"{D}saved 960x600 · thanks for stopping by · stay hydrated{W}", 2, count=4)
t.gen_text(f"{Y}connection closed.{W}", 3, count=5)
t.clone_frame(44)

# ── assemble: play once, settle on last frame ────────────────────────────────
fps = 16
duration_ms = max(2, round(1000 / fps))
pal = [f.convert("P", palette=Image.ADAPTIVE, colors=32) for f in _frames]
pal[0].save(
    "output.gif",
    save_all=True,
    append_images=pal[1:],
    duration=duration_ms,
    loop=1,
    optimize=False,
    disposal=2,
)
size = os.path.getsize("output.gif")
print(f"output.gif: {len(pal)} frames, {size} bytes, ~{len(pal)/fps:.1f}s, loop=1")
