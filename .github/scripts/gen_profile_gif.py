#!/usr/bin/env python3
"""Generate the terminal boot GIF for the profile README (gifos / github-readme-terminal).

Deterministic: fixed speeds + seeded RNG so CI regen produces byte-identical output.
Writes ~/.config/gifos/ TOMLs before importing gifos (config picked up at import time).
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
fps = 24
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

# capture every rendered frame (they are chained in memory) and bypass the
# ffmpeg-based gen_gif (its quoting breaks on Windows cmd; PIL is deterministic
# and has zero external deps)
_frames: list = []


def _patched_gen_frame(self, frame=None):
    """Same chaining as the original, but snapshot a COPY of each state and
    skip the per-frame PNG writes (they were only for ffmpeg's benefit)."""
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
W = "\\x1b[0m"    # reset

HOLD = 9      # frames of stillness after a block
TAIL = 18     # final hold
SPEED = 2     # typing speed (frames per char)

t = Terminal(width=360, height=240, xpad=6, ypad=6)
t.set_fps(24)
t.set_prompt(f"{G}siguatepeque{W}@{Y}github{W}:~$ ")

# -- $ whoami ---------------------------------------------------------------
t.gen_prompt(1)
t.gen_typing_text("whoami", 1, contin=True, speed=SPEED)
t.gen_text(f"{G}siguatepeque{W}", 2, count=3)

# -- $ neofetch --------------------------------------------------------------
t.gen_prompt(3)
t.gen_typing_text("neofetch", 3, contin=True, speed=SPEED)
t.gen_text([
    "  user      " + G + "siguatepeque" + W,
    "  location  honduras",
    "  age       20",
    "  condition hEDS",
    "  bio       some computer stuff,",
    "            some medical stuff",
    "",
    '  "' + G + "future biomedical eng," + W,
    "   larping on github" + '"',
], 4)
t.clone_frame(HOLD)

# -- $ ls projects/ ----------------------------------------------------------
t.scroll_up(12)
t.gen_prompt(1)
t.gen_typing_text("ls projects/", 1, contin=True, speed=SPEED)
t.gen_text([
    "  " + G + "heds-biomarker-discovery" + W + "   [" + Y + "python" + W + "]",
    "  " + G + "detector-caidas" + W + "            [" + Y + "js" + W + "]",
    "  " + G + "girlfriend-day-emily" + W + "       [" + Y + "js" + W + "]",
], 2)
t.clone_frame(HOLD)

# -- $ exit ------------------------------------------------------------------
t.scroll_up(5)
t.gen_prompt(1)
t.gen_typing_text("exit", 1, contin=True, speed=SPEED)
t.gen_text(f"{Y}connection closed.{W}", 2, count=4)
t.clone_frame(TAIL)

fps = 24
duration_ms = max(2, round(1000 / fps))
pal = [f.convert("P", palette=Image.ADAPTIVE, colors=16) for f in _frames]
pal[0].save(
    "output.gif",
    save_all=True,
    append_images=pal[1:],
    duration=duration_ms,
    loop=0,
    optimize=False,
    disposal=2,
)
size = os.path.getsize("output.gif")
print(f"output.gif generated: {len(pal)} frames, {size} bytes, ~{len(pal)/fps:.1f}s")