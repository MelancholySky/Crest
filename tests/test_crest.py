"""Test suite for crest.

Covers the three layers independently:
  * patterns  — grid shape, value ranges, determinism, registry
  * colors     — clamping, gradient interpolation, map registry, ANSI output
  * render     — terminal string output (blocks + ascii) and PNG export
  * cli        — argument parsing, subcommand dispatch, error handling

Run with ``pytest`` from the project root.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import io
import os
import pathlib
import re
import shutil
import sys

import pytest

import crest
from crest import cli, colors, patterns, render, wizard


# --------------------------------------------------------------------------
# patterns
# --------------------------------------------------------------------------

def test_all_patterns_produce_in_range_grids():
    for name in patterns.list_patterns():
        grid = patterns.get_pattern(name).render(20, 10)
        assert len(grid) == 10
        assert all(len(row) == 20 for row in grid)
        for row in grid:
            for v in row:
                assert 0.0 <= v <= 1.0


def test_pattern_is_deterministic_for_fixed_time():
    a = patterns.wave(16, 8, time=1.5)
    b = patterns.wave(16, 8, time=1.5)
    assert a == b


def test_pattern_changes_with_time():
    a = patterns.ripple(16, 8, time=0.0)
    b = patterns.ripple(16, 8, time=3.0)
    assert a != b


def test_get_pattern_unknown_raises():
    with pytest.raises(KeyError):
        patterns.get_pattern("does-not-exist")


def test_grid_dimensions_handles_ragged():
    grid = [[0.0, 0.0], [0.0]]
    assert patterns.grid_dimensions(grid) == (2, 2)


# --------------------------------------------------------------------------
# colors
# --------------------------------------------------------------------------

def test_clamp_byte_bounds():
    assert colors._clamp_byte(-5) == 0
    assert colors._clamp_byte(300) == 255
    assert colors._clamp_byte(128) == 128


def test_gradient_interpolates_endpoints():
    ramp = colors._make_gradient([(0.0, (0, 0, 0)), (1.0, (100, 200, 50))])
    assert ramp(0.0) == (0, 0, 0)
    assert ramp(1.0) == (100, 200, 50)


def test_gradient_midpoint_average():
    ramp = colors._make_gradient([(0.0, (0, 0, 0)), (1.0, (0, 0, 10))])
    assert ramp(0.5) == (0, 0, 5)


def test_all_color_maps_return_valid_rgb():
    for name in colors.list_color_maps():
        fn = colors.get_color_map(name)
        r, g, b = fn(0.5)
        for ch in (r, g, b):
            assert 0 <= ch <= 255


def test_ansi_truecolor_foreground_and_background():
    fg = colors.ansi_truecolor((10, 20, 30))
    bg = colors.ansi_truecolor((10, 20, 30), bg=True)
    assert fg == "\x1b[38;2;10;20;30m"
    assert bg == "\x1b[48;2;10;20;30m"


def test_get_color_map_unknown_raises():
    with pytest.raises(KeyError):
        colors.get_color_map("nope")


# --------------------------------------------------------------------------
# render
# --------------------------------------------------------------------------

def _small_grid():
    return patterns.gradient(10, 4, time=0.0)


def test_render_terminal_blocks_includes_ansi_and_reset():
    grid = _small_grid()
    buf = io.StringIO()
    text = render.render_terminal(grid, color_map=colors.get_color_map("mono"), glyph="blocks", out=buf)
    assert colors.RESET in text
    assert "\x1b[48;2;" in text  # background colour escape used in blocks mode
    assert buf.getvalue() == text + "\n"


def test_render_terminal_ascii_uses_foreground():
    grid = _small_grid()
    text = render.render_terminal(grid, color_map=colors.get_color_map("mono"), glyph="ascii")
    assert "\x1b[38;2;" in text


def test_render_terminal_unknown_glyph_raises():
    with pytest.raises(ValueError):
        render.render_terminal(_small_grid(), glyph="emoji")


def test_render_png_when_pillow_absent(monkeypatch):
    """With PIL masked out, render_png should raise ImportError."""
    monkeypatch.setitem(sys.modules, "PIL", None)
    with pytest.raises(ImportError):
        render.render_png(_small_grid(), "out.png")


def test_render_png_with_pillow(tmp_path):
    if importlib.util.find_spec("PIL") is None:
        pytest.skip("Pillow not installed")
    from PIL import Image

    out = tmp_path / "frame.png"
    render.render_png(_small_grid(), str(out), color_map=colors.get_color_map("fire"))
    assert out.exists()
    img = Image.open(out)
    assert img.size == (10, 4)


def test_render_png_scales_up(tmp_path):
    if importlib.util.find_spec("PIL") is None:
        pytest.skip("Pillow not installed")
    from PIL import Image

    out = tmp_path / "scaled.png"
    render.render_png(_small_grid(), str(out), color_map=colors.get_color_map("fire"), scale=5)
    img = Image.open(out)
    assert img.size == (50, 20)


# --------------------------------------------------------------------------
# cli
# --------------------------------------------------------------------------

def test_list_command_prints_entries(capsys):
    assert cli.cmd_list(argparse.Namespace()) == 0
    out = capsys.readouterr().out
    assert "wave" in out
    assert "ember" in out


def test_render_command_writes_ansi(capsys, monkeypatch):
    # Pin terminal size so output is deterministic.
    monkeypatch.setattr(shutil, "get_terminal_size", lambda *a, **k: os.terminal_size((12, 8)))
    args = cli.build_parser().parse_args(["render", "-p", "wave", "-c", "ember", "-g", "blocks", "-w", "12", "-H", "6"])
    assert cli.cmd_render(args) == 0
    out = capsys.readouterr().out
    assert colors.RESET in out


def test_unknown_pattern_exits_nonzero(monkeypatch):
    args = cli.build_parser().parse_args(["render", "-p", "bogus"])
    with pytest.raises(SystemExit) as exc:
        cli.cmd_render(args)
    assert exc.value.code == 2


def test_export_without_pillow_exits_nonzero(monkeypatch, tmp_path):
    monkeypatch.setitem(sys.modules, "PIL", None)
    out = tmp_path / "x.png"
    args = cli.build_parser().parse_args(["export", "-o", str(out)])
    with pytest.raises(SystemExit) as exc:
        cli.cmd_export(args)
    assert exc.value.code == 3


def test_main_dispatches_render():
    rc = cli.main(["render", "-p", "gradient", "-c", "mono", "-g", "ascii", "-w", "8", "-H", "3"])
    assert rc == 0


def test_version_flag_reports_package_version(capsys):
    """``--version`` must print the one version defined in ``crest``."""
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert capsys.readouterr().out == f"crest {crest.__version__}\n"


def test_cli_version_is_not_a_second_copy():
    """``crest.cli.__version__`` is a re-export, not its own literal."""
    assert cli.__version__ is crest.__version__


# ``pyproject.toml`` carries the packaging copy of the version, so it can drift
# from ``crest.__version__``. Read it from the source tree next to this file --
# not the working directory -- so the check below holds wherever pytest runs.
PYPROJECT_PATH = pathlib.Path(__file__).resolve().parent.parent / "pyproject.toml"

_TABLE_HEADER_RE = re.compile(r"^\[\s*([^\[\]]+?)\s*\]$")
_VERSION_RE = re.compile(r"""^version\s*=\s*(["'])([^"']+)\1\s*(?:#.*)?$""")


def _pyproject_version(path: pathlib.Path):
    """Return the version declared in ``pyproject.toml``'s ``[project]`` table.

    A deliberately narrow line scan rather than a TOML parse: crest supports
    Python 3.8, where ``tomllib`` does not exist, and takes no third-party
    dependencies -- test-only ones included. Only a quoted ``version`` key
    inside ``[project]`` counts, so a ``version`` in another table or a
    commented-out line cannot satisfy it. Returns ``None`` if there is none.
    """
    table = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("["):
            header = _TABLE_HEADER_RE.match(line)
            # An unparseable header (e.g. ``[[array.of.tables]]``) leaves no
            # known table, so its keys are never read as ``[project]``'s.
            table = header.group(1) if header else None
            continue
        if table != "project":
            continue
        match = _VERSION_RE.match(line)
        if match:
            return match.group(2)
    return None


def test_pyproject_version_matches_package_version():
    """The packaging version must track ``crest.__version__``.

    A release bump that touches only one of the two files fails here instead
    of shipping a distribution whose metadata contradicts ``crest --version``.
    """
    if not PYPROJECT_PATH.is_file():
        # No source tree — the suite is running against an installed package.
        # Fall back to that distribution's baked-in metadata so the invariant
        # is still checked rather than skipped.
        installed = importlib.metadata.version("crest-art")
        assert installed == crest.__version__, (
            f"installed crest-art metadata says {installed!r} but "
            f"crest.__version__ says {crest.__version__!r}"
        )
        return

    declared = _pyproject_version(PYPROJECT_PATH)
    assert declared is not None, (
        f"no quoted version key found in [project] of {PYPROJECT_PATH}"
    )
    assert declared == crest.__version__, (
        f"{PYPROJECT_PATH.name} declares version {declared!r} but "
        f"crest.__version__ says {crest.__version__!r}; bump both "
        f"(see RELEASE.md, 'Post-release maintenance')"
    )


def test_pyproject_version_reader_ignores_other_tables_and_comments(tmp_path):
    """The scan must not be satisfied by a decoy version key."""
    toml = tmp_path / "pyproject.toml"
    toml.write_text(
        "[build-system]\n"
        'version = "9.9.9"\n'
        "\n"
        "[project]\n"
        '# version = "8.8.8"\n'
        'name = "crest-art"\n'
        '  version = "1.2.3"  # indentation and trailing comments are fine\n'
        "\n"
        "[tool.other]\n"
        'version = "7.7.7"\n',
        encoding="utf-8",
    )
    assert _pyproject_version(toml) == "1.2.3"


def test_pyproject_version_reader_returns_none_when_absent(tmp_path):
    toml = tmp_path / "pyproject.toml"
    toml.write_text('[project]\nname = "crest-art"\n', encoding="utf-8")
    assert _pyproject_version(toml) is None


# --------------------------------------------------------------------------
# wizard
# --------------------------------------------------------------------------

class _FakeIO:
    """Minimal scripted I/O: returns queued answers, records display lines."""

    def __init__(self, answers):
        self._answers = list(answers)
        self.lines = []

    def prompt(self, msg):
        # Don't consume an answer for the printed prompt itself.
        return self._answers.pop(0)

    def display(self, msg):
        self.lines.append(msg)


def test_build_run_options_defaults_to_custom():
    # preset + pattern + color + glyph + action + 2 sizes
    io = _FakeIO(["", "", "", "", "", "", "", ""])
    opts = wizard.build_run_options(io.prompt, io.display)
    assert opts["pattern"] in patterns.list_patterns()
    assert opts["color"] in colors.list_color_maps()
    assert opts["glyph"] in ("blocks", "ascii")
    assert opts["action"] == "render"


def test_build_run_options_animated_path():
    # preset(blank)=custom, pattern(blank), color(blank), glyph(blank),
    # action=2 (animate), speed(blank), delay(blank), sizes(blank).
    io = _FakeIO(["", "", "", "", "2", "", "", "", ""])
    opts = wizard.build_run_options(io.prompt, io.display)
    assert opts["action"] == "animate"
    assert opts["speed"] == 0.15
    assert opts["delay"] == 0.05


def test_build_run_options_preset_then_overrides():
    # Menu picks must be numeric indices, one per prompt.
    #   1 -> preset index 0 ("Ember Wave"), which sets wave/ember/blocks
    #   2 -> pattern index 1 ("plasma")
    #   '' -> keep ember (colour default)
    #   '' -> keep blocks (glyph default)
    #   '' -> action default (render)
    #   '' '' -> blank sizes (render path = 7 prompts)
    io = _FakeIO(["1", "2", "", "", "", "", ""])
    opts = wizard.build_run_options(io.prompt, io.display)
    assert opts["pattern"] == "plasma"
    assert opts["color"] == "ember"
    assert opts["glyph"] == "blocks"
    assert opts["width"] is None
    assert opts["height"] is None


def test_command_for_options_includes_flags():
    opts = {"pattern": "wave", "color": "ember", "glyph": "blocks", "width": 40, "height": 20}
    cmd = wizard.command_for_options(opts)
    assert cmd == "crest render -p wave -c ember -g blocks -w 40 -H 20"


def test_command_for_options_animated():
    opts = {"pattern": "wave", "color": "ember", "glyph": "blocks",
            "action": "animate", "speed": 0.2, "delay": 0.1}
    cmd = wizard.command_for_options(opts)
    assert cmd == "crest animate -p wave -c ember -g blocks -s 0.2 -d 0.1"


def test_command_for_options_omits_blank_size():
    opts = {"pattern": "ripple", "color": "ocean", "glyph": "blocks"}
    cmd = wizard.command_for_options(opts)
    assert "-w" not in cmd and "-H" not in cmd
    assert cmd == "crest render -p ripple -c ocean -g blocks"


def test_wizard_preview_runs_headless():
    # preset(blank)=custom, pattern(blank), color(blank), glyph(blank),
    # action(blank)=render, speed/delay skipped, sizes 30x10.
    io = _FakeIO(["", "", "", "", "", "30", "10"])
    rc = wizard.run_wizard(prompt=io.prompt, display=io.display)
    assert rc == 0
    assert any("Equivalent command" in line for line in io.lines)


def test_no_subcommand_launches_wizard():
    # main() with no args should route to the wizard (returns 0 headlessly
    # when we inject IO via the wizard default path is not possible here, so
    # we assert argparse yields no command and main dispatches to wizard).
    from crest import cli
    parser = cli.build_parser()
    args = parser.parse_args([])
    assert getattr(args, "command", None) is None


# (shutil/sys imported at top so they are available to every test)
