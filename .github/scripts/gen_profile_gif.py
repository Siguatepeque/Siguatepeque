#!/usr/bin/env python3
"""Generate the terminal boot GIF for the profile README (gifos / github-readme-terminal).

Widescreen (640x264, ~2.4:1) so it reads as a terminal window, ~12s at 14 fps,
plays ONCE and settles on the final frame. Sequence: boot banner, whoami,
neofetch, cat larp_manifesto.txt, tree, exit. Deterministic (seeded RNG, fixed
speeds) so CI regeneration is byte-identical.

Writes ~/.config/gifos/ TOMLs before importing gifos (config read at import time).
Output: ./output.gif in the repo root (CWD must be repo root).
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
cursor = "_"
show_cursor = true
blink_cursor = true
user_name = "siguatepeque"
fps = 14
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
from PIL import Image

# capture a COPY of every rendered frame (the lib mutates and returns the same
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
C = "\\x1b[96m"   # bright cyan
M = "\\x1b[95m"   # bright magenta
D = "\\x1b[90m"   # bright black (dim)
W = "\\x1b[0m"    # reset

t = Terminal(width=640, height=264, xpad=14, ypad=12)
t.set_fps(14)
t.set_prompt(f"{G}siguatepeque{W}@{Y}github{W}:~$ ")

SPEED = 2  # typing speed: frames per char

# -- boot ---------------------------------------------------------------------
t.gen_text(f"{D}booting siguatepeque@github ...{W}", 1)
t.gen_text(f"[{G}#################{W}------------------] 50%", 2)
t.gen_text(f"{D}kernel: hEDS 1.0 (running on vibes){W}", 3)
t.gen_text(f"{D}mounting /home/siguatepeque ... {G}done{W}", 4)
t.gen_text(f"{D}loading larp modules ... {G}ok{W}", 5)
t.clone_frame(7)

# -- scroll to a clean slate --------------------------------------------------
t.scroll_up(6)

# -- $ whoami -----------------------------------------------------------------
t.gen_prompt(1)
t.gen_typing_text("whoami", 1, contin=True, speed=SPEED)
t.gen_text(f"{G}siguatepeque{W}", 2, count=3)
t.clone_frame(4)

# -- $ neofetch ---------------------------------------------------------------
t.gen_prompt(3)
t.gen_typing_text("neofetch", 3, contin=True, speed=SPEED)
t.gen_text([
    f"{G}~~~~~~{W}        {C}siguatepeque@github{W}",
    f"{G}~    ~{W}        {D}-------------------{W}",
    f"{G}~~~~~~{W}        {Y}os:{W}      honduras",
    f"                {Y}age:{W}     20",
    f"                {Y}cond:{W}    hEDS",
    f"                {Y}bio:{W}     some computer stuff,",
    f"                        some medical stuff",
    f"                {Y}status:{W}  larping as a real dev",
    "",
], 4)
t.clone_frame(10)

# -- $ cat larp_manifesto.txt -------------------------------------------------
t.scroll_up(10)
t.gen_prompt(1)
t.gen_typing_text("cat larp_manifesto.txt", 1, contin=True, speed=SPEED)
t.gen_text([
    f"{M}> fake it till you make it{W}",
    f"{M}> ship code like you belong here{W}",
    f"{M}> biomedical eng in progress{W}",
    f"{M}> the larp is the point{W}",
], 2, count=2)
t.clone_frame(10)

# -- $ tree (live repo index) -------------------------------------------------
t.scroll_up(6)
t.gen_prompt(1)
t.gen_typing_text("gh repo list --limit 4", 1, contin=True, speed=SPEED)

_repos = ["heds-biomarker-discovery", "girlfriend-day-emily", "detector-caidas", "luna-cycle-tracker (private)"]
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
        _all = [x["name"] + (" (private)" if x.get("private") else "") for x in _json.loads(_r.read().decode()) if not x.get("fork") and x["name"] != "Siguatepeque"]
    if _all:
        _repos = _all[:4]
except Exception:
    pass  # offline CI: fall back to last-known list

_pad = max(len(r) for r in _repos) + 2
t.gen_text(
    [f"{C}{name.ljust(_pad)}{W}{D}|{W}" for name in _repos] + [""],
    2, count=2,
)
t.clone_frame(10)

# -- $ exit --------------------------------------------------------------------
t.scroll_up(7)
t.gen_prompt(1)
t.gen_typing_text("exit", 1, contin=True, speed=SPEED)
t.gen_text(f"{Y}connection closed.{W}", 2, count=6)
t.clone_frame(40)

# -- assemble GIF: play once (loop=1), settle on the last frame ----------------
fps = 14
duration_ms = max(2, round(1000 / fps))
pal = [f.convert("P", palette=Image.ADAPTIVE, colors=16) for f in _frames]
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
print(f"output.gif generated: {len(pal)} frames, {size} bytes, ~{len(pal)/fps:.1f}s, loop=1")
