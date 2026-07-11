# crest

**Generative terminal-art CLI** — render animated parametric patterns directly
in your terminal using ANSI truecolour, with optional PNG export.

`crest` is dependency-free at its core (Python standard library only) and
produces flowing wave/plasma/mandala art in a few keystrokes. It is built in
the same spirit as the rest of the tools in this folder: small, well-tested,
cross-platform, and easy to read.

---

## Features

- **5 parametric patterns** — `wave`, `plasma`, `gradient`, `mandala`, `ripple`
- **8 colour maps** — `mono`, `ember`, `fire`, `ocean`, `viridis`, `rainbow`, `ice`, `matrix`
- **2 glyph styles** — shaded Unicode blocks (`blocks`) or an ASCII ramp (`ascii`)
- **Live animation** — `animate` loops the pattern in place
- **PNG export** — `export` saves a frame (optional, needs Pillow)
- **Zero core dependencies** — runs on any Python 3.8+ install
- **30 tests** covering patterns, colour maps, renderers, and the CLI

---

## Quick start

```bash
# From PyPI (core has no dependencies; add [png] for image export)
pip install crest-art
pip install crest-art[png]   # + Pillow for PNG export

# Or, from the project root for local development:
cd crest
pip install -e .            # core only
pip install -e ".[png]"     # + Pillow for PNG export

# List what's available
python3 -m crest.cli list

# Print a static frame
python3 -m crest.cli render -p wave -c ember

# Animate it (Ctrl+C to stop)
python3 -m crest.cli animate -p plasma -c rainbow

# Matrix-style screensaver (hacker aesthetic)
python3 -m crest.cli animate -p plasma -c matrix -s 0.08 -d 0.05

# Save a frame to PNG (requires Pillow)
python3 -m crest.cli export -p mandala -c fire -o mandala.png
```

Once installed, the `crest` command is also available directly:

```bash
crest render -p ripple -c ocean -g ascii
```

### Guided wizard

New to `crest`? Just run `crest` with **no arguments** to drop straight into
the interactive wizard. It walks you through presets, patterns, colour maps,
glyph styles, and **static vs. animated** view, shows a live preview, and prints
the exact `crest` command so you can reuse it later:

```bash
crest            # no args -> wizard
crest wizard     # explicit
```

### Shell integration

The venv keeps your system clean. To avoid typing the venv path, **source** the
fish helper — it is a function definition, not an executable script, so do not
run it directly (`./crest.fish` fails with "interpreter directive"). Source it
once (or add it to `~/.config/fish/config.fish`):

```fish
source /path/to/crest/crest.fish
crest list
```

Or run the launchers directly (they bootstrap the venv on first use):

```bash
./run.fish list
./run.sh list
```

---

## Matrix Colour Map

A green colour map inspired by classic terminal aesthetics. Use it with any pattern:

```bash
# Static frame
crest render -p wave -c matrix

# Different patterns
crest render -p ripple -c matrix
crest render -p mandala -c matrix
crest render -p plasma -c matrix
```

---

## Warp terminal

`crest` works great in [Warp](https://www.warp.dev):

- **Static frames** render perfectly — use `crest render` (or `export` to PNG):
  ```bash
  crest render -p plasma -c matrix
  ```
- **Live animation** (`crest animate`) is best enjoyed in a classic terminal
  emulator. Warp's UI capture model doesn't handle per-frame full-screen
  redraws cleanly, so animations may look choppy there. For a still in Warp,
  render a single frame or export a PNG.

---

## Usage

```
crest {render|animate|export|list|wizard} [options]
```

### Shared options

| Flag | Default | Description |
|------|---------|-------------|
| `-p, --pattern` | `wave` | Pattern name |
| `-c, --color` | `ember` | Colour map name |
| `-g, --glyph` | `blocks` | `blocks` or `ascii` |
| `-w, --width` | terminal | Width in cells |
| `-H, --height` | terminal - 2 | Height in cells |

### Command-specific options

- `render` / `export`: `-t, --time FLOAT` — animation phase offset
- `animate`: `-t` (start phase), `-s, --speed FLOAT` (phase/frame), `-d, --delay FLOAT` (seconds/frame)
- `export`: `-o, --output PATH` — PNG path (default `crest.png`); `-s, --scale INT` — pixel scale per cell (e.g. `20` → each cell becomes 20×20 px)

### Examples

```bash
# Tiny static frame, deterministic
crest render -p mandala -c rainbow -g ascii -w 40 -H 12

# Slow ocean ripple animation
crest animate -p ripple -c ocean -s 0.08 -d 0.08

# Grab one frame of the plasma at a specific phase
crest export -p plasma -c viridis -t 2.0 -o plasma.png
```

---

## How it works

1. **Patterns** (`crest/patterns.py`) generate a 2D grid of float intensities in
   `[0.0, 1.0]`. Each generator is a pure function of `(width, height, time)`,
   so animation is just advancing `time`.
2. **Colour maps** (`crest/colors.py`) turn each intensity into an `(r, g, b)`
   triple. Several named ramps are provided and easy to extend.
3. **Renderers** (`crest/render.py`) map the coloured grid to output — ANSI
   escapes for the terminal, or a PNG via Pillow (lazy import, so the core
   stays dependency-free).
4. The **CLI** (`crest/cli.py`) wires argparse subcommands to the layers above.

---

## Development

```bash
pip install -e ".[png]" pytest
python3 -m pytest -q
python3 -m crest.cli --version
```

Project layout:

```
crest/
├── crest/
│   ├── __init__.py   # public API + version
│   ├── patterns.py    # parametric generators
│   ├── colors.py      # colour maps + ANSI helpers
│   ├── render.py      # terminal & PNG renderers
│   ├── cli.py         # argparse interface
│   └── wizard.py      # interactive setup
├── tests/
│   └── test_crest.py  # 30 tests
├── matrix-screensaver.sh
├── matrix-screensaver.fish
├── pyproject.toml
├── requirements.txt
├── LICENSE            # MIT
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).
