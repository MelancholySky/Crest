"""Colour maps that turn a scalar intensity in ``[0, 1]`` into an ``(r, g, b)``.

A colour map is just a callable ``float -> (r, g, b)`` where each channel is a
``0..255`` integer. Renderers sample the map at every grid cell to decide what
to draw. Several named maps are provided so users can restyle the same pattern
without touching generator code.
"""

from __future__ import annotations

import math
from typing import Callable, Dict, List, Sequence, Tuple

RGB = Tuple[int, int, int]
ColorMapFn = Callable[[float], RGB]


def _clamp_byte(v: int) -> int:
    """Clamp an integer into the ``0..255`` byte range."""
    return 0 if v < 0 else (255 if v > 255 else v)


def _hsv_to_rgb(h: float, s: float, v: float) -> RGB:
    """Convert HSV (all channels ``0..1``) to an ``(r, g, b)`` byte triple."""
    h = h - math.floor(h)  # wrap hue into [0, 1)
    h *= 6.0
    i = int(h)
    f = h - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    r, g, b = {
        0: (v, t, p),
        1: (q, v, p),
        2: (p, v, t),
        3: (p, q, v),
        4: (t, p, v),
        5: (v, p, q),
    }[i % 6]
    return (_clamp_byte(round(r * 255)), _clamp_byte(round(g * 255)), _clamp_byte(round(b * 255)))


def _make_gradient(stops: Sequence[Tuple[float, RGB]]) -> ColorMapFn:
    """Build a colour map by linearly interpolating between ``(pos, rgb)`` stops."""
    ordered = sorted(stops, key=lambda s: s[0])

    def fn(t: float) -> RGB:
        t = 0.0 if t < 0.0 else (1.0 if t > 1.0 else t)
        for i in range(len(ordered) - 1):
            p0, c0 = ordered[i]
            p1, c1 = ordered[i + 1]
            if p0 <= t <= p1:
                span = (p1 - p0) or 1.0
                f = (t - p0) / span
                return (
                    _clamp_byte(round(c0[0] + (c1[0] - c0[0]) * f)),
                    _clamp_byte(round(c0[1] + (c1[1] - c0[1]) * f)),
                    _clamp_byte(round(c0[2] + (c1[2] - c0[2]) * f)),
                )
        return ordered[-1][1]

    return fn


# --- Built-in colour maps -------------------------------------------------

_MONO = _make_gradient([(0.0, (0, 0, 0)), (1.0, (255, 255, 255))])

# Amber/orange ramp echoing the Wave/CV brand palette.
_EMBER = _make_gradient(
    [(0.0, (8, 4, 0)), (0.4, (120, 40, 0)), (0.7, (245, 133, 63)), (1.0, (255, 255, 235))]
)

_FIRE = _make_gradient(
    [(0.0, (0, 0, 0)), (0.3, (120, 10, 0)), (0.6, (240, 80, 0)), (0.85, (255, 200, 40)), (1.0, (255, 255, 230))]
)

_OCEAN = _make_gradient(
    [(0.0, (2, 6, 30)), (0.4, (10, 60, 120)), (0.7, (20, 150, 170)), (1.0, (180, 240, 250))]
)

_VIRIDIS = _make_gradient(
    [(0.0, (68, 1, 84)), (0.25, (59, 82, 139)), (0.5, (33, 145, 140)), (0.75, (94, 201, 98)), (1.0, (253, 231, 37))]
)


def _rainbow(t: float) -> RGB:
    return _hsv_to_rgb(t, 0.85, 1.0)


def _ice(t: float) -> RGB:
    return _hsv_to_rgb(0.55 + 0.1 * t, 0.5, 0.4 + 0.6 * t)


_MATRIX = _make_gradient(
    [(0.0, (0, 20, 0)), (0.2, (0, 80, 0)), (0.5, (0, 180, 0)), (0.8, (0, 255, 0)), (1.0, (150, 255, 100))]
)


_COLOR_MAPS: Dict[str, ColorMapFn] = {
    "mono": _MONO,
    "ember": _EMBER,
    "fire": _FIRE,
    "ocean": _OCEAN,
    "viridis": _VIRIDIS,
    "rainbow": _rainbow,
    "ice": _ice,
    "matrix": _MATRIX,
}


def list_color_maps() -> List[str]:
    """Return the names of all registered colour maps."""
    return list(_COLOR_MAPS.keys())


def get_color_map(name: str) -> ColorMapFn:
    """Return a colour map callable by name, raising ``KeyError`` if unknown."""
    if name not in _COLOR_MAPS:
        raise KeyError(
            f"unknown colour map {name!r}; available: {', '.join(list_color_maps())}"
        )
    return _COLOR_MAPS[name]


# --- ANSI truecolour helpers ----------------------------------------------

RESET = "\x1b[0m"


def ansi_truecolor(rgb: RGB, bg: bool = False) -> str:
    """Return an ANSI 24-bit colour escape sequence for ``rgb``.

    ``bg=True`` emits a background colour sequence instead of foreground.
    """
    r, g, b = rgb
    prefix = 48 if bg else 38
    return f"\x1b[{prefix};2;{r};{g};{b}m"
