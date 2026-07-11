"""Renderers: turn an intensity grid into pixels — on screen or in a file.

The terminal renderer emits ANSI truecolour escape codes. The PNG renderer is
optional and lazily imports Pillow only when actually used, so the core CLI has
zero third-party dependencies.
"""

from __future__ import annotations

import sys
from typing import List, Optional, TextIO

from . import colors
from .patterns import Grid

# Unicode block glyphs ordered from "empty" to "full"; a cell is drawn as a
# block whose shade reflects intensity when glyph mode is "blocks".
_SHADE_BLOCKS = " ░▒▓█"


def _sample_map(grid: Grid, color_map: colors.ColorMapFn):
    """Pre-compute an RGB value for every cell of ``grid``."""
    out: List[List[colors.RGB]] = []
    for row in grid:
        out.append([color_map(v) for v in row])
    return out


def render_terminal(
    grid: Grid,
    color_map: Optional[colors.ColorMapFn] = None,
    glyph: str = "blocks",
    out: Optional[TextIO] = None,
) -> str:
    """Render ``grid`` to an ANSI-coloured string and write it to ``out``.

    ``glyph`` is one of ``"blocks"`` (shaded Unicode block) or ``"ascii"``
    (``. : + * #`` ramp). Returns the rendered string so callers can also
    capture it for tests.
    """
    color_map = color_map or colors.get_color_map("ember")
    stream = out or sys.stdout
    lines: List[str] = []
    rgb_grid = _sample_map(grid, color_map)

    if glyph == "ascii":
        ramp = " .:-=+*#%@"
        for y, row in enumerate(grid):
            line = ""
            for x, v in enumerate(row):
                idx = min(len(ramp) - 1, int(v * (len(ramp) - 1)))
                ch = ramp[idx]
                line += colors.ansi_truecolor(rgb_grid[y][x]) + ch
            lines.append(line + colors.RESET)
    elif glyph == "blocks":
        for y, row in enumerate(grid):
            line = ""
            for x, v in enumerate(row):
                bidx = min(len(_SHADE_BLOCKS) - 1, int(round(v * (len(_SHADE_BLOCKS) - 1))))
                line += colors.ansi_truecolor(rgb_grid[y][x], bg=True) + _SHADE_BLOCKS[bidx]
            lines.append(line + colors.RESET)
    else:
        raise ValueError(f"unknown glyph mode {glyph!r}; expected 'blocks' or 'ascii'")

    text = "\n".join(lines)
    stream.write(text + "\n")
    return text


def render_png(
    grid: Grid,
    path: str,
    color_map: Optional[colors.ColorMapFn] = None,
    scale: int = 1,
) -> str:
    """Render ``grid`` to a PNG file at ``path`` using Pillow.

    ``scale`` multiplies each cell into an ``scale x scale`` block of pixels, so
    e.g. ``scale=20`` turns a 40x12 grid into an 800x240 image. Raises
    ``ImportError`` if Pillow is not installed.
    """
    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - exercised only without Pillow
        raise ImportError(
            "PNG export requires Pillow. Install with `pip install Pillow` "
            "or run `crest export` after adding it to your environment."
        ) from exc

    color_map = color_map or colors.get_color_map("ember")
    width = max((len(r) for r in grid), default=0)
    height = len(grid)
    scale = max(1, int(scale))
    img = Image.new("RGB", (width * scale, height * scale))
    px = img.load()
    for y, row in enumerate(grid):
        for x, v in enumerate(row):
            r, g, b = color_map(v)
            for dy in range(scale):
                for dx in range(scale):
                    px[x * scale + dx, y * scale + dy] = (r, g, b)
    img.save(path)
    return path
