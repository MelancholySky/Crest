"""Parametric pattern generators.

Every generator returns a 2D :class:`list` of ``float`` in the range
``[0.0, 1.0]`` (an "intensity grid"), where ``grid[y][x]`` is the value at
column ``x`` and row ``y``. Consuming layers (renderers) are responsible for
mapping those intensities to colour and glyphs.

All generators are deterministic for a given ``(width, height, time, **opts)``
tuple, which keeps tests reproducible and lets animations advance via the
``time`` parameter.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Tuple

# A grid is row-major: grid[row][col], values in [0.0, 1.0].
Grid = List[List[float]]

PatternFn = Callable[..., Grid]


def _clamp(v: float) -> float:
    """Clamp a value into the canonical ``[0.0, 1.0]`` range."""
    return 0.0 if v < 0.0 else (1.0 if v > 1.0 else v)


def _blank(width: int, height: int) -> Grid:
    """Allocate a zero-filled grid of the requested size."""
    return [[0.0] * width for _ in range(height)]


def wave(width: int, height: int, time: float = 0.0, **_opts) -> Grid:
    """Interfering sine waves — the visual motif behind crest.

    Two diagonally travelling waves are summed and normalised. The ``time``
    parameter scrolls the pattern for animation.
    """
    grid = _blank(width, height)
    fx = 2.0 * math.pi / max(width, 1)
    fy = 2.0 * math.pi / max(height, 1)
    for y in range(height):
        for x in range(width):
            a = math.sin(x * fx * 3.0 + time)
            b = math.sin((x + y) * fy * 2.0 - time * 1.3)
            v = (a + b) / 2.0
            grid[y][x] = _clamp((v + 1.0) / 2.0)
    return grid


def plasma(width: int, height: int, time: float = 0.0, **_opts) -> Grid:
    """Classic plasma: summed phase-shifted sinusoids in both axes.

    Produces smooth flowing colour fields; great for the rainbow colour map.
    """
    grid = _blank(width, height)
    for y in range(height):
        for x in range(width):
            v = (
                math.sin(x * 0.10 + time)
                + math.sin(y * 0.13 - time * 0.7)
                + math.sin((x + y) * 0.07 + time * 1.1)
                + math.sin(math.hypot(x - width / 2, y - height / 2) * 0.09 - time)
            )
            grid[y][x] = _clamp((v + 4.0) / 8.0)
    return grid


def gradient(width: int, height: int, time: float = 0.0, **_opts) -> Grid:
    """A simple diagonal gradient that rotates with ``time``.

    Useful as a sanity-check pattern and for testing the renderer.
    """
    grid = _blank(width, height)
    angle = time * 0.5
    ca, sa = math.cos(angle), math.sin(angle)
    for y in range(height):
        for x in range(width):
            # Project (x, y) onto the rotating diagonal then normalise.
            proj = (x * ca + y * sa) / max(math.hypot(width, height), 1.0)
            grid[y][x] = _clamp(proj)
    return grid


def mandala(width: int, height: int, time: float = 0.0, **_opts) -> Grid:
    """Radial kaleidoscope built from polar symmetry.

    Six-fold rotational symmetry plus a pulsing radius gives a flower-like
    pattern that animates by breathing in and out.
    """
    grid = _blank(width, height)
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    max_r = max(cx, cy, 1.0)
    petals = 6
    pulse = 1.0 + 0.25 * math.sin(time * 1.5)
    for y in range(height):
        for x in range(width):
            dx, dy = x - cx, y - cy
            r = math.hypot(dx, dy) / max_r
            theta = math.atan2(dy, dx)
            v = math.sin(petals * theta + r * 10.0 - time) * math.cos(r * math.pi * pulse)
            grid[y][x] = _clamp((v + 1.0) / 2.0)
    return grid


def ripple(width: int, height: int, time: float = 0.0, **_opts) -> Grid:
    """Concentric ripples emanating from the centre, expanding with ``time``."""
    grid = _blank(width, height)
    cx, cy = (width - 1) / 2.0, (height - 1) / 2.0
    max_r = max(cx, cy, 1.0)
    for y in range(height):
        for x in range(width):
            r = math.hypot(x - cx, y - cy) / max_r
            v = math.sin(r * 18.0 - time * 2.0)
            grid[y][x] = _clamp((v + 1.0) / 2.0)
    return grid


# Registry of available patterns. Order matters: it is the order shown by
# ``crest list`` and the order used for any numeric selection in future UI.
_PATTERNS: Dict[str, PatternFn] = {
    "wave": wave,
    "plasma": plasma,
    "gradient": gradient,
    "mandala": mandala,
    "ripple": ripple,
}


class Pattern:
    """Lightweight descriptor for a registered pattern generator."""

    def __init__(self, name: str, fn: PatternFn):
        self.name = name
        self._fn = fn

    def render(self, width: int, height: int, time: float = 0.0, **opts) -> Grid:
        return self._fn(width, height, time, **opts)

    def __call__(self, width: int, height: int, time: float = 0.0, **opts) -> Grid:
        return self.render(width, height, time, **opts)


def list_patterns() -> List[str]:
    """Return the names of all registered patterns."""
    return list(_PATTERNS.keys())


def get_pattern(name: str) -> Pattern:
    """Return a :class:`Pattern` by name, or raise ``KeyError`` if unknown."""
    if name not in _PATTERNS:
        raise KeyError(
            f"unknown pattern {name!r}; available: {', '.join(list_patterns())}"
        )
    return Pattern(name, _PATTERNS[name])


def grid_dimensions(grid: Grid) -> Tuple[int, int]:
    """Return ``(width, height)`` for a grid, guarding against ragged input."""
    height = len(grid)
    width = max((len(row) for row in grid), default=0)
    return width, height
