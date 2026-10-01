"""Command-line interface for crest.

Subcommands:
  render    print a single static frame of a pattern to the terminal
  animate   play a looping animation in the terminal
  export    save a static frame to a PNG (requires Pillow)
  list      show available patterns and colour maps

Shared options control size, pattern, colour map, and glyph style.
"""

from __future__ import annotations

import argparse
import math
import shutil
import sys
import time
from typing import List, Optional

# ``__version__`` is defined once, in ``crest/__init__.py``. Importing it here
# keeps ``crest --version`` in step with the package (and keeps the historical
# ``crest.cli.__version__`` name working for callers that import it).
from . import __version__, colors, patterns, render, wizard

# Glyph modes understood by the terminal renderer.
GLYPH_MODES = ("blocks", "ascii")
# Bounds that guard against pathological allocations — the DoS class
# SECURITY.md explicitly keeps in scope. A phase beyond ±1e9 has no visual
# meaning and can overflow the float range inside the generators
# (e.g. ``time * 2.0`` in ripple).
MAX_PHASE = 1e9
MAX_CELLS_PER_AXIS = 4096
MAX_TOTAL_CELLS = 1_000_000


def _phase_float(text: str) -> float:
    """argparse type for ``--time`` / ``--speed``: finite float, |value| <= 1e9."""
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid float value: {text!r}")
    if not math.isfinite(value) or abs(value) > MAX_PHASE:
        raise argparse.ArgumentTypeError(
            f"expected a finite number with |value| <= {MAX_PHASE:g}, got {text!r}"
        )
    return value


def _non_negative_float(text: str) -> float:
    """argparse type for ``--delay``: finite float >= 0."""
    value = _phase_float(text)
    if value < 0.0:
        raise argparse.ArgumentTypeError(f"expected a non-negative number, got {text!r}")
    return value


def _scale_int(text: str) -> int:
    """argparse type for ``--scale``: integer in [1, render.MAX_PNG_SCALE]."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer value: {text!r}")
    if not 1 <= value <= render.MAX_PNG_SCALE:
        raise argparse.ArgumentTypeError(
            f"expected an integer in [1, {render.MAX_PNG_SCALE}], got {text!r}"
        )
    return value



def _terminal_size(default_cols: int = 80, default_rows: int = 40):
    """Return ``(cols, rows)`` from the terminal, falling back to defaults."""
    size = shutil.get_terminal_size(fallback=(default_cols, default_rows))
    return size.columns, size.lines


def _add_common(parser: argparse.ArgumentParser) -> None:
    """Attach options shared by every command that renders a pattern."""
    parser.add_argument("-p", "--pattern", default="wave", help="pattern name (default: wave)")
    parser.add_argument(
        "-c", "--color", default="ember", dest="color",
        help="colour map name (default: ember)",
    )
    parser.add_argument(
        "-g", "--glyph", default="blocks", choices=GLYPH_MODES,
        help="glyph style: blocks or ascii (default: blocks)",
    )
    parser.add_argument(
        "-w", "--width", type=int, default=None,
        help="output width in cells (default: terminal width)",
    )
    parser.add_argument(
        "-H", "--height", type=int, default=None,
        help="output height in cells (default: terminal height - 2)",
    )


def resolve_size(width, height):
    """Resolve optional ``(width, height)`` cell counts into a concrete size.

    ``None`` (or a falsy value) falls back to the terminal; results are
    clamped to at least one cell and capped by :data:`MAX_CELLS_PER_AXIS` /
    :data:`MAX_TOTAL_CELLS` so one command line cannot request a pathological
    allocation. Exits with status 2 and a clean message when over the cap.
    """
    cols, rows = _terminal_size()
    w = width if width else cols
    h = height if height else max(1, rows - 2)
    w, h = max(1, w), max(1, h)
    if w > MAX_CELLS_PER_AXIS or h > MAX_CELLS_PER_AXIS or w * h > MAX_TOTAL_CELLS:
        print(
            f"error: requested {w}x{h} cells is too large "
            f"(max {MAX_CELLS_PER_AXIS} per axis, {MAX_TOTAL_CELLS} cells total)",
            file=sys.stderr,
        )
        sys.exit(2)
    return w, h


def _resolve_size(args: argparse.Namespace):
    return resolve_size(args.width, args.height)


def _resolve_color(args: argparse.Namespace) -> colors.ColorMapFn:
    try:
        return colors.get_color_map(args.color)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)


def cmd_render(args: argparse.Namespace) -> int:
    try:
        pat = patterns.get_pattern(args.pattern)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    color = _resolve_color(args)
    width, height = _resolve_size(args)
    grid = pat.render(width, height, time=args.time)
    render.render_terminal(grid, color_map=color, glyph=args.glyph)
    return 0


def cmd_animate(args: argparse.Namespace) -> int:
    try:
        pat = patterns.get_pattern(args.pattern)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    color = _resolve_color(args)
    width, height = _resolve_size(args)
    try:
        while True:
            args.time += args.speed
            grid = pat.render(width, height, time=args.time)
            # Carriage-return + cursor-up to redraw in place.
            sys.stdout.write("\x1b[2J\x1b[H")
            render.render_terminal(grid, color_map=color, glyph=args.glyph)
            time.sleep(args.delay)
    except KeyboardInterrupt:
        print("\nstopped.")
        return 0


def cmd_export(args: argparse.Namespace) -> int:
    try:
        pat = patterns.get_pattern(args.pattern)
    except KeyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    color = _resolve_color(args)
    width, height = _resolve_size(args)
    grid = pat.render(width, height, time=args.time)
    try:
        path = render.render_png(grid, args.output, color_map=color, scale=args.scale)
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(3)
    except ValueError as exc:
        # Size/scale guards inside render_png.
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(2)
    except OSError as exc:
        print(f"error: cannot write {args.output}: {exc}", file=sys.stderr)
        sys.exit(2)
    print(f"wrote {path} ({width}x{height})")
    return 0


def cmd_wizard(args: argparse.Namespace) -> int:
    return wizard.run_wizard()


def cmd_list(args: argparse.Namespace) -> int:
    print("patterns:")
    for name in patterns.list_patterns():
        print(f"  - {name}")
    print("\ncolour maps:")
    for name in colors.list_color_maps():
        print(f"  - {name}")
    print("\nglyph modes:")
    for name in GLYPH_MODES:
        print(f"  - {name}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="crest",
        description="Generative terminal-art CLI — render animated parametric patterns.",
    )
    parser.add_argument("--version", action="version", version=f"crest {__version__}")
    sub = parser.add_subparsers(dest="command", required=False)

    p_render = sub.add_parser("render", help="print a single static frame")
    _add_common(p_render)
    p_render.add_argument("-t", "--time", type=_phase_float, default=0.0, help="animation phase offset")
    p_render.set_defaults(func=cmd_render)

    p_anim = sub.add_parser("animate", help="play a looping animation")
    _add_common(p_anim)
    p_anim.add_argument("-t", "--time", type=_phase_float, default=0.0, help="starting phase")
    p_anim.add_argument("-s", "--speed", type=_phase_float, default=0.15, help="phase increment per frame")
    p_anim.add_argument("-d", "--delay", type=_non_negative_float, default=0.05, help="seconds to wait between frames")
    p_anim.set_defaults(func=cmd_animate)

    p_export = sub.add_parser("export", help="save a frame to a PNG (needs Pillow)")
    _add_common(p_export)
    p_export.add_argument("-t", "--time", type=_phase_float, default=0.0, help="animation phase offset")
    p_export.add_argument("-o", "--output", default="crest.png", help="output PNG path")
    p_export.add_argument(
        "-s", "--scale", type=_scale_int, default=1, dest="scale",
        help=f"pixel scale per cell, 1-{render.MAX_PNG_SCALE} (e.g. 20 -> each cell becomes 20x20 px)",
    )
    p_export.set_defaults(func=cmd_export)

    p_list = sub.add_parser("list", help="list patterns, colour maps, glyphs")
    p_list.set_defaults(func=cmd_list)

    p_wiz = sub.add_parser("wizard", help="interactive guided setup")
    p_wiz.set_defaults(func=cmd_wizard)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    # No subcommand -> drop the user straight into the guided wizard.
    if not getattr(args, "command", None):
        return wizard.run_wizard()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
