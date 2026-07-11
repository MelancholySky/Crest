# AGENTS.md

Guidance for AI agents (and contributors) working on **crest**.

## What this project is
A small, dependency-free Python CLI that renders generative terminal art using
ANSI truecolour, with optional PNG export. Core design goal: **zero third-party
dependencies at runtime** (Pillow is opt-in for `export` only).

## Architecture (keep these layers separate)
- `crest/patterns.py` — pure generators: `(width, height, time) -> grid[float]`.
  Values are intensities in `[0.0, 1.0]`. Deterministic for fixed inputs.
- `crest/colors.py` — intensity `[0,1] -> (r,g,b)` colour maps + ANSI helpers.
- `crest/render.py` — terminal (ANSI) and PNG renderers. PNG must lazy-import
  Pillow and raise a clear `ImportError` if missing.
- `crest/cli.py` — argparse subcommands (`render`, `animate`, `export`, `list`, `wizard`).
- `crest/wizard.py` — interactive guided setup. Keep `prompt`/`display` injectable
  and the pure helpers (`build_run_options`, `command_for_options`) free of I/O
  so they stay unit-testable headlessly.

## Rules
- Do **not** add runtime dependencies to the core. Anything needing a library
  must be optional and lazy-imported.
- Keep generators pure and deterministic — tests rely on this.
- New patterns: add a function + register it in `_PATTERNS`. New colour maps:
  add to `_COLOR_MAPS`. Update `README.md` and `crest list` output accordingly.
- All user-facing changes need tests in `tests/test_crest.py`. The wizard is
tested with a scripted `_FakeIO` harness; reuse it rather than touching a real terminal.

## Commands
```bash
pip install -e ".[png]" pytest
python3 -m pytest -q
python3 -m crest.cli --version
```

## Style
- Python 3.8+ compatible. Use `from __future__ import annotations`.
- Type hints + docstrings on public functions. Match the existing tone.
- Co-author commits with `Co-Authored-By: Oz <oz-agent@warp.dev>`.
