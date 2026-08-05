# crest

**Generative terminal-art CLI** — render animated parametric patterns directly
in your terminal using ANSI truecolour, with optional PNG export.

![crest preview](preview.png)

Dependency-free at its core: Python standard library only, no install footprint
beyond the package itself. Pillow is optional and only needed for PNG export.

```bash
pip install crest-art
crest
```

---

## Install

```bash
pip install crest-art          # core, no dependencies
pip install "crest-art[png]"   # + Pillow for PNG export
```

> The PyPI package is **`crest-art`** — the name `crest` was already taken.
> The installed command is still `crest`.

Arch users: a PKGBUILD is available in [`aur/`](aur/).

## Quick start

Run `crest` with no arguments to open the interactive wizard. It walks you
through patterns, colour maps, glyph styles, and static vs. animated output,
shows a live preview, and prints the command it built so you can reuse it.

```bash
crest                                   # wizard
crest list                              # show all patterns and colour maps
crest render -p wave -c ember           # one static frame
crest animate -p plasma -c rainbow      # animate in place (Ctrl+C to stop)
crest export -p mandala -c fire -o out.png
```

Matrix-style screensaver:

```bash
crest animate -p plasma -c matrix -s 0.08 -d 0.05
```

---

## What's available

- **5 patterns** — `wave`, `plasma`, `gradient`, `mandala`, `ripple`
- **8 colour maps** — `mono`, `ember`, `fire`, `ocean`, `viridis`, `rainbow`, `ice`, `matrix`
- **2 glyph styles** — shaded Unicode blocks (`blocks`) or an ASCII ramp (`ascii`)

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
| `-w, --width` | terminal width | Width in cells |
| `-H, --height` | terminal height − 2 | Height in cells |

### Per-command options

| Command | Flag | Description |
|---------|------|-------------|
| `render`, `export` | `-t, --time FLOAT` | Animation phase offset |
| `animate` | `-t, --time FLOAT` | Starting phase |
| `animate` | `-s, --speed FLOAT` | Phase advance per frame |
| `animate` | `-d, --delay FLOAT` | Seconds per frame |
| `export` | `-o, --output PATH` | PNG path (default `crest.png`) |
| `export` | `-s, --scale INT` | Pixels per cell (`20` → 20×20 px per cell) |

### Examples

```bash
# Small deterministic frame
crest render -p mandala -c rainbow -g ascii -w 40 -H 12

# Slow ocean ripple
crest animate -p ripple -c ocean -s 0.08 -d 0.08

# One plasma frame at a specific phase
crest export -p plasma -c viridis -t 2.0 -o plasma.png
```

---

## Terminal notes

Requires a terminal with ANSI truecolour support — most modern emulators
qualify. Output degrades gracefully in narrower terminals; use `-w` and `-H`
to override the detected size.

**Warp:** static frames render correctly, but `animate` may look choppy —
Warp's UI capture model doesn't handle per-frame full-screen redraws cleanly.
Use `render` or `export` there, and save `animate` for a classic emulator.

---

## Running from source

Clone and install in editable mode:

```bash
git clone https://github.com/MelancholySky/Crest
cd Crest
pip install -e ".[png]"
```

Or use the bundled launchers, which bootstrap a venv on first run:

```bash
./run.fish list
./run.sh list
```

Fish users can source the helper function instead of typing the venv path.
It defines a function rather than being an executable script, so source it —
running `./crest.fish` directly fails with an interpreter directive error.

```fish
source /path/to/Crest/crest.fish
crest list
```

---

## How it works

1. **Patterns** (`crest/patterns.py`) produce a 2D grid of float intensities in
   `[0.0, 1.0]`. Each generator is a pure function of `(width, height, time)`,
   so animating is just advancing `time`.
2. **Colour maps** (`crest/colors.py`) turn each intensity into an `(r, g, b)`
   triple. The named ramps are plain data and easy to extend.
3. **Renderers** (`crest/render.py`) map the coloured grid to output — ANSI
   escapes for the terminal, or a PNG via Pillow. Pillow is imported lazily so
   the core stays dependency-free.
4. **CLI** (`crest/cli.py`) wires argparse subcommands to the layers above.

Because patterns are pure functions of time, any frame is reproducible from
its parameters — the same command always renders the same output.

```
Crest/
├── crest/
│   ├── __init__.py    # public API + version
│   ├── patterns.py    # parametric generators
│   ├── colors.py      # colour maps + ANSI helpers
│   ├── render.py      # terminal & PNG renderers
│   ├── cli.py         # argparse interface
│   └── wizard.py      # interactive setup
├── tests/
│   └── test_crest.py  # 30 tests
├── aur/               # PKGBUILD
├── pyproject.toml
└── LICENSE
```

## Development

```bash
pip install -e ".[png]" pytest
python3 -m pytest -q
crest --version
```

30 tests cover patterns, colour maps, renderers, and the CLI. Contributions
are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## Security

Found a vulnerability? Please report it privately rather than opening an issue.
See [SECURITY.md](SECURITY.md).

---

## Credits

Core idea by **hy3**. Built and maintained by **Melancholy Sky**.

MIT licensed — see [LICENSE](LICENSE).
