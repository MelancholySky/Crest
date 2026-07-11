"""Interactive wizard for crest.

The wizard walks an end user through choosing a pattern, colour map, glyph
style, and size, then either previews it live or shows the equivalent
``crest`` command so they can reproduce it later. The whole thing is built
around small injectable ``prompt`` / ``display`` callables so the flow is
fully testable without a real terminal (see ``build_run_options`` and
``command_for_options``).

Design notes (mirrors the Wave project's "guided + presets + copy CLI command"
philosophy):
  * A few curated **presets** give instant good-looking starting points.
  * Choices are presented as numbered menus with sensible defaults.
  * The final step offers a live preview AND the exact command string, so the
    user learns the CLI as they go.
"""

from __future__ import annotations

import sys
import time
from typing import Callable, Dict, List, Optional, TextIO

from . import colors, patterns, render

# A small palette of curated starting points. Each maps directly to CLI flags.
PRESETS: Dict[str, Dict[str, str]] = {
    "Ember Wave": {"pattern": "wave", "color": "ember", "glyph": "blocks"},
    "Rainbow Mandala": {"pattern": "mandala", "color": "rainbow", "glyph": "ascii"},
    "Ocean Ripple": {"pattern": "ripple", "color": "ocean", "glyph": "blocks"},
    "Fire Plasma": {"pattern": "plasma", "color": "fire", "glyph": "blocks"},
    "Viridis Gradient": {"pattern": "gradient", "color": "viridis", "glyph": "ascii"},
    "Ice Mono": {"pattern": "wave", "color": "ice", "glyph": "ascii"},
}

# The options a completed wizard run produces.
RunOptions = Dict[str, object]


def _ask_menu(
    title: str,
    choices: List[str],
    default_index: int,
    prompt: Callable[[str], str],
    display: Callable[[str], None],
) -> int:
    """Show a numbered menu and return the chosen index (0-based).

    ``prompt`` returns the user's raw line; ``display`` writes output. An empty
    line accepts the ``default_index``; invalid input re-prompts.
    """
    display(f"\n{title}")
    for i, choice in enumerate(choices, start=1):
        marker = ">" if i - 1 == default_index else " "
        display(f"  {marker} {i}. {choice}")
    while True:
        raw = prompt("Select [enter for default]: ").strip()
        if raw == "":
            return default_index
        if raw.isdigit() and 1 <= int(raw) <= len(choices):
            return int(raw) - 1
        display("  Please enter a number in the list, or press enter for the default.")


def _pick_from_registry(
    title: str,
    names: List[str],
    default_name: str,
    prompt: Callable[[str], str],
    display: Callable[[str], None],
) -> str:
    idx = _ask_menu(title, names, names.index(default_name), prompt, display)
    return names[idx]


def build_run_options(prompt, display) -> RunOptions:
    """Drive the guided flow and return the chosen :data:`RunOptions`.

    ``prompt`` / ``display`` are injected so this is testable headlessly.
    """
    display("=" * 56)
    display("  crest — generative terminal-art wizard")
    display("=" * 56)
    display("Build a pattern step by step, then preview it or copy the command.")

    # Step 0: optional preset.
    preset_names = list(PRESETS.keys())
    preset_idx = _ask_menu(
        "Start from a preset (or build from scratch):",
        preset_names + ["Custom (build from scratch)"],
        len(preset_names),  # default: build custom
        prompt,
        display,
    )
    if preset_idx < len(preset_names):
        opts: RunOptions = dict(PRESETS[preset_names[preset_idx]])
        display(f"\nLoaded preset: {preset_names[preset_idx]}")
    else:
        opts = {"pattern": "wave", "color": "ember", "glyph": "blocks"}

    # Step 1: pattern.
    opts["pattern"] = _pick_from_registry(
        "Pattern:", patterns.list_patterns(), str(opts.get("pattern", "wave")),
        prompt, display,
    )
    # Step 2: colour map.
    opts["color"] = _pick_from_registry(
        "Colour map:", colors.list_color_maps(), str(opts.get("color", "ember")),
        prompt, display,
    )
    # Step 3: glyph.
    glyphs = ["blocks", "ascii"]
    opts["glyph"] = _pick_from_registry(
        "Glyph style:", glyphs, str(opts.get("glyph", "blocks")),
        prompt, display,
    )
    # Step 4: static or animated view.
    action_idx = _ask_menu(
        "View as:", ["Static (single frame)", "Animated (live motion)"], 0,
        prompt, display,
    )
    opts["action"] = "animate" if action_idx == 1 else "render"
    if opts["action"] == "animate":
        opts["speed"] = _ask_float(
            "Animation speed — phase per frame (blank = 0.15):", 0.15, prompt, display
        )
        opts["delay"] = _ask_float(
            "Frame delay in seconds (blank = 0.05):", 0.05, prompt, display
        )
    # Step 5: size.
    opts["width"] = _ask_int(
        "Width in cells (blank = terminal width):", None, prompt, display
    )
    opts["height"] = _ask_int(
        "Height in cells (blank = terminal height - 2):", None, prompt, display
    )
    return opts


def _ask_int(
    title: str,
    default: Optional[int],
    prompt: Callable[[str], str],
    display: Callable[[str], None],
) -> Optional[int]:
    """Prompt for an optional integer; blank returns ``default``."""
    while True:
        raw = prompt(f"{title} ").strip()
        if raw == "":
            return default
        if raw.isdigit():
            return int(raw)
        display("  Please enter a number, or leave blank.")


def _ask_float(
    title: str,
    default: float,
    prompt: Callable[[str], str],
    display: Callable[[str], None],
) -> float:
    """Prompt for an optional float; blank returns ``default``."""
    while True:
        raw = prompt(f"{title} ").strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            display("  Please enter a number, or leave blank.")


def command_for_options(opts: RunOptions) -> str:
    """Return the ``crest`` command string equivalent to ``opts``."""
    verb = "animate" if opts.get("action") == "animate" else "render"
    parts = ["crest", verb]
    parts += ["-p", str(opts.get("pattern", "wave"))]
    parts += ["-c", str(opts.get("color", "ember"))]
    parts += ["-g", str(opts.get("glyph", "blocks"))]
    if opts.get("width") is not None:
        parts += ["-w", str(opts["width"])]
    if opts.get("height") is not None:
        parts += ["-H", str(opts["height"])]
    if verb == "animate":
        if opts.get("speed") is not None:
            parts += ["-s", str(opts["speed"])]
        if opts.get("delay") is not None:
            parts += ["-d", str(opts["delay"])]
    return " ".join(parts)


def run_wizard(
    prompt: Optional[Callable[[str], str]] = None,
    display: Optional[Callable[[str], None]] = None,
    animate: bool = False,
) -> int:
    """Run the wizard end-to-end against the real terminal by default.

    ``prompt`` and ``display`` can be injected for testing. When finished, the
    user may preview the pattern live or just copy the command.
    """
    prompt = prompt or (lambda msg: input(msg))
    stream: TextIO = sys.stdout
    display = display or (lambda msg: stream.write(msg + "\n"))

    opts = build_run_options(prompt, display)

    color_fn = colors.get_color_map(str(opts["color"]))
    width = int(opts.get("width") or 80)
    height = int(opts.get("height") or 24)
    pat = patterns.get_pattern(str(opts["pattern"]))

    if opts.get("action") == "animate":
        # Play the animation live, then show the reusable command.
        speed = float(opts.get("speed") or 0.15)
        delay = float(opts.get("delay") or 0.05)
        display("\nPlaying animation — press Ctrl+C to stop.\n")
        try:
            t = 0.0
            while True:
                grid = pat.render(width, height, time=t)
                stream.write("\x1b[2J\x1b[H")
                render.render_terminal(grid, color_map=color_fn, glyph=str(opts["glyph"]))
                time.sleep(delay)
                t += speed
        except KeyboardInterrupt:
            display("\nStopped.")
    else:
        display("\n" + "-" * 56)
        display("Preview:")
        display("-" * 56)
        grid = pat.render(width, height)
        render.render_terminal(grid, color_map=color_fn, glyph=str(opts["glyph"]))
        display("")

    display("Equivalent command (copy & reuse anytime):")
    display(f"  {command_for_options(opts)}")
    return 0
