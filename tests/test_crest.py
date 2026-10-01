"""Test suite for crest.

Covers the three layers independently:
  * patterns  — grid shape, value ranges, determinism, registry
  * colors     — clamping, gradient interpolation, map registry, ANSI output
  * render     — terminal string output (blocks + ascii) and PNG export
  * cli        — argument parsing, subcommand dispatch, error handling
  * docs       — the published [0.1.0] entry still lists what that release shipped

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
import subprocess
import sys
import time

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
# cli input validation & bounds
# --------------------------------------------------------------------------


def test_nonfinite_time_is_rejected():
    # `nan` / `inf` / `1e999` all parse as floats; they must die at argparse.
    for bad in ("nan", "inf", "-inf", "1e999"):
        with pytest.raises(SystemExit) as exc:
            cli.build_parser().parse_args(["render", "-t", bad])
        assert exc.value.code == 2


def test_huge_phase_is_rejected():
    # Finite but over the bound: ripple's `time * 2.0` would overflow to inf
    # and die inside math.sin.
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["render", "-p", "ripple", "-t", "1e308"])
    assert exc.value.code == 2


def test_negative_delay_is_rejected():
    # time.sleep(-1) used to escape as a raw ValueError traceback.
    with pytest.raises(SystemExit) as exc:
        cli.build_parser().parse_args(["animate", "-d", "-1"])
    assert exc.value.code == 2


def test_phase_bound_is_inclusive():
    args = cli.build_parser().parse_args(["render", "-t", "1e9"])
    assert args.time == 1e9


def test_scale_argument_is_bounded():
    for bad in ("0", "-3", "600"):
        with pytest.raises(SystemExit) as exc:
            cli.build_parser().parse_args(["export", "-s", bad])
        assert exc.value.code == 2
    assert cli.build_parser().parse_args(["export", "-s", "512"]).scale == 512


def test_resolve_size_caps(monkeypatch):
    monkeypatch.setattr(shutil, "get_terminal_size", lambda *a, **k: os.terminal_size((80, 24)))
    assert cli.resolve_size(4096, 1) == (4096, 1)  # per-axis boundary passes
    with pytest.raises(SystemExit) as exc:
        cli.resolve_size(4097, 1)  # one over the per-axis cap
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        cli.resolve_size(2000, 600)  # under the per-axis cap, but 1.2M cells
    assert exc.value.code == 2


def test_render_huge_width_exits_cleanly(capsys):
    # A mistyped dimension must produce a usage error, not an OOM attempt
    # (the DoS class SECURITY.md keeps in scope).
    with pytest.raises(SystemExit) as exc:
        cli.main(["render", "-w", "100000000"])
    assert exc.value.code == 2
    assert "too large" in capsys.readouterr().err


def test_export_unwritable_path_exits_cleanly(tmp_path):
    if importlib.util.find_spec("PIL") is None:
        pytest.skip("Pillow not installed")
    args = cli.build_parser().parse_args(
        ["export", "-o", str(tmp_path / "missing" / "x.png"), "-w", "4", "-H", "2"]
    )
    with pytest.raises(SystemExit) as exc:
        cli.cmd_export(args)
    assert exc.value.code == 2


def test_render_png_scale_cap_raises(tmp_path):
    if importlib.util.find_spec("PIL") is None:
        pytest.skip("Pillow not installed")
    with pytest.raises(ValueError):
        render.render_png(patterns.gradient(4, 2), str(tmp_path / "x.png"), scale=600)


def test_clamp_pins_nan_to_floor():
    assert patterns._clamp(float("nan")) == 0.0
    assert patterns._clamp(1e18) == 1.0
    assert patterns._clamp(-1e18) == 0.0


def test_animate_loop_runs_and_stops_cleanly(monkeypatch, capsys):
    """cmd_animate must actually run — no test invoked it before this audit."""
    delays = []

    def fake_sleep(seconds):
        delays.append(seconds)
        if len(delays) >= 3:
            raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", fake_sleep)
    args = cli.build_parser().parse_args(
        ["animate", "-p", "wave", "-w", "8", "-H", "3", "-d", "0.01"]
    )
    assert cli.cmd_animate(args) == 0
    assert delays == [0.01, 0.01, 0.01]
    out = capsys.readouterr().out
    assert out.count("\x1b[2J\x1b[H") == 3
    assert "stopped." in out


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
    # preset + pattern + color + glyph + action + 2 sizes = 7 prompts
    io = _FakeIO(["", "", "", "", "", "", ""])
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
    fake_io = _FakeIO(["", "", "", "", "", "30", "10"])
    stream = io.StringIO()
    rc = wizard.run_wizard(prompt=fake_io.prompt, display=fake_io.display, stream=stream)
    assert rc == 0
    assert any("Equivalent command" in line for line in fake_io.lines)
    # The preview frame must land in the injected stream, not leak to stdout.
    frame = stream.getvalue()
    assert len(frame.splitlines()) == 10
    assert "\x1b[48;2;" in frame


def test_no_subcommand_launches_wizard(monkeypatch):
    # main([]) must actually dispatch into the wizard — asserting the parse
    # alone overstated this before. A stub keeps the terminal out of it.
    from crest import cli

    args = cli.build_parser().parse_args([])
    assert getattr(args, "command", None) is None

    seen = {}
    monkeypatch.setattr(cli.wizard, "run_wizard", lambda *a, **k: seen.setdefault("called", 7))
    assert cli.main([]) == 7
    assert "called" in seen


def test_wizard_cancelled_on_eof():
    # Ctrl+D at the very first prompt used to escape as a raw EOFError.
    def eof_prompt(msg):
        raise EOFError

    lines = []
    assert wizard.run_wizard(prompt=eof_prompt, display=lines.append) == 0
    assert any("Cancelled" in line for line in lines)


def test_wizard_cancelled_on_interrupt_at_prompt():
    def interrupting_prompt(msg):
        raise KeyboardInterrupt

    lines = []
    assert wizard.run_wizard(prompt=interrupting_prompt, display=lines.append) == 0
    assert any("Cancelled" in line for line in lines)


def test_wizard_preview_matches_command_for_zero_speed_and_delay(monkeypatch):
    # Entering 0 must be honoured everywhere: the preview used to fall back
    # to the 0.15/0.05 defaults while the printed command said `-s 0.0 -d 0.0`,
    # so the taught command busy-looped instead of matching the preview.
    fake_io = _FakeIO(["", "", "", "", "2", "0", "0", "6", "3"])
    delays = []

    def fake_sleep(seconds):
        delays.append(seconds)
        raise KeyboardInterrupt

    monkeypatch.setattr(time, "sleep", fake_sleep)
    lines = []
    rc = wizard.run_wizard(prompt=fake_io.prompt, display=lines.append, stream=io.StringIO())
    assert rc == 0
    assert delays == [0.0]
    command = next(line for line in lines if "crest animate" in line)
    assert "-s 0.0" in command and "-d 0.0" in command
    assert "-w 6" in command and "-H 3" in command


def test_wizard_int_prompt_enforces_cap():
    # A width above the cap must re-prompt, not slip through to the renderer.
    fake_io = _FakeIO(["", "", "", "", "", "5000", "4096", "3"])
    opts = wizard.build_run_options(fake_io.prompt, fake_io.display)
    assert opts["width"] == 4096
    assert opts["height"] == 3
    assert any("up to 4096" in line for line in fake_io.lines)


def test_wizard_float_prompt_rejects_inf_and_negative_delay():
    # action=2 (animate); speed "inf" re-prompts to 0.15; delay "-1"
    # re-prompts to 0.05.
    fake_io = _FakeIO(["", "", "", "", "2", "inf", "0.15", "-1", "0.05", "", ""])
    opts = wizard.build_run_options(fake_io.prompt, fake_io.display)
    assert opts["speed"] == 0.15
    assert opts["delay"] == 0.05
    assert any("finite" in line for line in fake_io.lines)
    assert any(">= 0" in line for line in fake_io.lines)


# --------------------------------------------------------------------------
# docs
# --------------------------------------------------------------------------

_CHANGELOG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "CHANGELOG.md"
)

# The inventory lines of the ``[0.1.0]`` changelog entry, frozen as literals.
# That entry records what 0.1.0 published — these five patterns and eight
# colour maps, as registered at the ``v0.1.0`` tag — so it is history, not a
# live claim about the tree. A pattern or colour map added afterwards belongs
# in an ``[Unreleased]`` entry and must never be appended to these lines.
_V0_1_0_INVENTORY_LINES = (
    "- **5 parametric patterns**: wave, plasma, gradient, mandala, ripple",
    "- **8 colour maps**: mono, ember, fire, ocean, viridis, rainbow, ice, matrix",
)


def test_changelog_0_1_0_inventory_lines_are_intact():
    """Guard the drift that let ``[0.1.0]`` claim 7 colour maps, omitting ``matrix``.

    A whole-line literal match on purpose: the released inventory is fixed, so
    there is nothing to parse here and no version to track.
    """
    with open(_CHANGELOG, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for expected in _V0_1_0_INVENTORY_LINES:
        assert lines.count(expected) == 1, (
            "CHANGELOG.md must contain exactly one line reading:\n"
            "  {}\n"
            "It records what 0.1.0 shipped; a pattern or colour map added "
            "since then belongs in an [Unreleased] entry, not in [0.1.0]."
            .format(expected)
        )


# (shutil/sys imported at top so they are available to every test)


# --------------------------------------------------------------------------
# shell helpers
# --------------------------------------------------------------------------

_CREST_FISH = pathlib.Path(__file__).resolve().parent.parent / "crest.fish"


def _fake_repo_with_venv_crest(tmp_path):
    """A throwaway tree shaped like a checkout: crest.fish next to a
    .venv/bin/crest stub that echoes its arguments, so the fish helper can
    be exercised without depending on a real virtual environment."""
    repo = tmp_path / "repo"
    (repo / ".venv" / "bin").mkdir(parents=True)
    stub = repo / ".venv" / "bin" / "crest"
    stub.write_text("#!/bin/sh\necho \"stub $*\"\n", encoding="utf-8")
    stub.chmod(0o755)
    shutil.copy(_CREST_FISH, repo / "crest.fish")
    return repo / "crest.fish"


def test_fish_helper_runs_after_source_scope_ends(tmp_path):
    """Sourcing crest.fish must leave a ``crest`` function that still works.

    Regression guard: the function used to look up a variable local to the
    sourced file, which dies as soon as ``source`` returns, so calling
    ``crest`` afterwards failed with "The expanded command was empty". A real
    session sources the file in one command and calls ``crest`` in another;
    the ``begin; ... end`` wrapper reproduces that scope boundary.
    """
    if shutil.which("fish") is None:
        pytest.skip("fish not installed")
    crest_fish = _fake_repo_with_venv_crest(tmp_path)
    script = f'begin; source "{crest_fish}"; end; crest hello world'
    proc = subprocess.run(["fish", "-c", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "stub hello world"


def test_fish_helper_resolves_absolute_venv_path(tmp_path):
    """The helper must capture an absolute path at definition time.

    Sourcing via a relative path and then ``cd``-ing away breaks a helper
    that kept the relative path, so crest.fish must normalize through
    ``realpath`` before snapshotting.
    """
    if shutil.which("fish") is None:
        pytest.skip("fish not installed")
    crest_fish = _fake_repo_with_venv_crest(tmp_path)
    script = f'cd "{crest_fish.parent}"; begin; source ./crest.fish; end; cd /; crest hi'
    proc = subprocess.run(["fish", "-c", script], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "stub hi"


# --------------------------------------------------------------------------
# idle screensaver helper
# --------------------------------------------------------------------------

_IDLE_SAVER_PATH = pathlib.Path(__file__).resolve().parent.parent / "idle-screensaver.py"


def _load_idle_saver():
    spec = importlib.util.spec_from_file_location("idle_screensaver", _IDLE_SAVER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_who_idle_reads_the_idle_column():
    """Regression guard: parts[-1] of ``who -u`` is the PID, never the idle time.

    The samples are real lines from this machine's ``who -u`` (procps field
    order: USER LINE DATE TIME IDLE PID [COMMENT]).
    """
    saver = _load_idle_saver()
    text = (
        "sky      tty2         2026-09-29 00:22  old         2302\n"
        "sky      pts/1        2026-10-01 04:08  00:05        1135180 (:0)\n"
        "sky      pts/2        2026-10-01 04:30  .            999\n"
        "root     pts/3        2026-10-01 03:00  05:00        42\n"
    )
    # The screensaver may start only once every one of the user's sessions is
    # idle, so the most recently active session wins; other users are ignored.
    assert saver.parse_who_idle(text, "sky") == 0
    without_active = "\n".join(text.splitlines()[:2])
    assert saver.parse_who_idle(without_active, "sky") == 300
    assert saver.parse_who_idle(text, "root") == 18000
    assert saver.parse_who_idle(text, "nobody") == 0


def test_parse_who_idle_handles_old_and_malformed_lines():
    saver = _load_idle_saver()
    assert saver.parse_who_idle("sky tty2 2026-09-29 00:22 old 2302", "sky") == 86400
    assert saver.parse_who_idle("definitely not a who line", "sky") == 0
    assert saver.parse_who_idle("", "sky") == 0


def test_idle_time_flag_rejects_below_one():
    proc = subprocess.run(
        [sys.executable, str(_IDLE_SAVER_PATH), "--idle-time", "-5"],
        capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 2
    assert "error: --idle-time must be at least 1 second" in proc.stderr
