#!/usr/bin/env python3
"""Generate the terminal boot GIF for the profile README (gifos / github-readme-terminal).

Widescreen (640x264, ~2.4:1) so it reads as a terminal window, ~10s at 14 fps,
plays ONCE and settles on the final frame. Sequence: boot banner + progress bar,
whoami, neofetch, cat future.txt, exit. Deterministic (seeded RNG, fixed speeds)
so CI regeneration is byte-identical.

Writes ~/.config/gifos/ TOMLs before importing gifos (config read at import time).
Output: ./output.gif in the repo root (CWD must be repo root).
"""
import os
import pathlib
import random
import sys

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
R = "\\x1b[91m"   # bright red
D = "\\x1b[90m"   # bright black (dim)
W = "\\x1b[0m"    # reset

t = Terminal(width=640, height=264, xpad=14, ypad=12)
t.set_fps(14)
t.set_prompt(f"{G}siguatepeque{W}@{Y}github{W}:~$ ")

SPEED = 3  # typing speed: frames per char

# -- boot ---------------------------------------------------------------------
t.gen_text(f"{D}booting siguatepeque@github ...{W}", 1)
t.gen_text(f"[{G}#################{W}------------------] 50%", 2)
t.gen_text(f"{D}kernel: hEDS 1.0 (running on vibes){W}", 3)
t.gen_text(f"{D}mounting /home/siguatepeque ... {G}done{W}", 4)
t.gen_text(f"{D}starting network services ... {G}done{W}", 5)
t.clone_frame(12)

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
    f"{G}~~~~~~{W}        siguatepeque@github",
    f"{G}~    ~{W}        -------------------",
    f"{G}~~~~~~{W}        os:     honduras",
    "                age:    20",
    "                cond:   hEDS",
    "                bio:    some computer stuff,",
    "                        some medical stuff",
    "",
], 4)
t.clone_frame(18)

# -- $ cat future.txt ---------------------------------------------------------
t.scroll_up(10)
t.gen_prompt(1)
t.gen_typing_text("cat future.txt", 1, contin=True, speed=SPEED)
t.gen_text([
    f"{G}future biomedical eng,{W}",
    f"{G}larping on github{W}",
], 2, count=2)
t.clone_frame(14)

# -- $ exit -------------------------------------------------------------------
t.scroll_up(5)
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