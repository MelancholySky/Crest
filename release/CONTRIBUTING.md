# Contributing to crest

Thank you for your interest in contributing to **crest**!

## Project Philosophy

**crest** is designed to be small, focused, and dependency-free at its core. Contributions should uphold this spirit:

- **Zero core dependencies** — The main CLI must run on Python 3.8+ with only the standard library
- **Optional extensions** — If a feature needs a third-party library (e.g., Pillow), it must be optional and lazy-loaded
- **Deterministic, pure functions** — Patterns and generators should be pure (no side effects) and deterministic for the same inputs
- **Well-tested** — User-facing changes need test coverage
- **Clear, readable code** — Match the existing code style and tone

## How to Contribute

### Reporting Issues

- Use [GitHub Issues](https://github.com/) to report bugs or request features
- Include your Python version, OS, and steps to reproduce
- For visual/rendering issues, describe or attach screenshots/example output

### Code Changes

1. **Fork and clone** the repository
2. **Create a branch** for your change: `git checkout -b feature/your-feature-name`
3. **Make your changes**, ensuring:
   - Code follows the existing style (Python 3.8+ compatible, type hints, docstrings)
   - All tests pass: `python3 -m pytest -q`
   - New features have corresponding tests in `tests/test_crest.py`
   - No new runtime dependencies are added (use optional deps if needed)
4. **Commit with a clear message**:
   ```
   Add new feature or fix bug

   Detailed explanation if needed.

   Co-Authored-By: Oz <oz-agent@warp.dev>
   ```
5. **Push** your branch and open a Pull Request

### Adding Patterns

To add a new parametric pattern:

1. Add a generator function to `crest/patterns.py` with signature:
   ```python
   def my_pattern(width: int, height: int, time: float) -> list[list[float]]:
       """Return a 2D grid of floats in [0.0, 1.0]."""
   ```
2. Register it in `_PATTERNS` dict
3. Add tests to `tests/test_crest.py`
4. Update `README.md` to list the new pattern
5. Update `CHANGELOG.md`

### Adding Colour Maps

To add a new colour map:

1. Add a function to `crest/colors.py`:
   ```python
   def my_colormap(intensity: float) -> tuple[int, int, int]:
       """Map [0.0, 1.0] to (r, g, b) where each is [0, 255]."""
   ```
2. Register it in `_COLOR_MAPS` dict
3. Add tests
4. Update documentation

### Testing

Run the test suite:
```bash
pip install -e ".[png]" pytest
python3 -m pytest -q
python3 -m pytest -v  # verbose output
```

Tests use a `_FakeIO` harness for the wizard to avoid touching the terminal. Follow this pattern for any interactive features.

## Code Style

- **Python 3.8+** compatible
- Use `from __future__ import annotations` at the top of modules
- Include type hints on public functions
- Write docstrings for public APIs
- Match the existing tone and patterns in the codebase

## Architecture

Keep these layers separate and focused:

- **`patterns.py`** — Pure generators: `(width, height, time) → grid[float]`
- **`colors.py`** — Intensity to RGB mappings + ANSI helpers
- **`render.py`** — Terminal (ANSI) and PNG renderers
- **`cli.py`** — argparse subcommands
- **`wizard.py`** — Interactive guided setup

For details, see `AGENTS.md`.

## Questions?

Check `AGENTS.md` for architecture notes and the `README.md` for usage examples. Feel free to open an issue to discuss larger changes before investing time.

---

**Thank you for contributing to crest!** ✨
