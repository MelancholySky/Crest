# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.1] - 2026-10-01

### Fixed
- `crest.fish`: calling the `crest` fish function after `source` failed with
  "The expanded command was empty" — the function looked up a variable local
  to the sourced file, which dies as soon as `source` returns. The venv
  binary path is now snapshotted into the function at definition time
  (`--inherit-variable`) and made absolute, so the helper also survives a
  later `cd` or a relative-path `source`.
- Idle screensaver (`idle-screensaver.py`): idle detection read the wrong
  `who -u` column — the PID field, never the IDLE time — so idle time was
  always 0 and the screensaver could never launch. It now parses the real
  IDLE column across the current user's sessions (`.` → active, `old` →
  24h+) and rejects `--idle-time` values below 1 second with a clean error.
- `run.sh` / `run.fish` bootstrapped with `pip install -e .`, which resolves
  against the caller's working directory — a first run from outside the repo
  left a broken half-installed venv. They now install the repo path
  explicitly, matching `matrix-screensaver.sh`.
- Non-finite or out-of-range numeric options (`--time nan`, `--speed inf`,
  `--delay -1`, phases past ±1e9) crashed with raw tracebacks; they are now
  rejected at parse time with clean usage errors.
- `crest export` to an unwritable or missing path now reports
  `error: cannot write ...` instead of a raw traceback.
- The wizard exits cleanly with "Cancelled." on Ctrl+D or Ctrl+C at any
  prompt instead of an `EOFError`/`KeyboardInterrupt` traceback.
- The wizard's live preview honours `0` for speed, delay, and size exactly
  like the "Equivalent command" it prints, instead of silently substituting
  defaults behind the command's back.
- The wizard's numeric prompts reject non-finite floats and dimensions over
  the cap, re-prompting instead of passing them through.
- `aur/PKGBUILD`: added the missing `python-setuptools` makedepend so
  clean-chroot builds work; corrected the `updpkgsums` attribution
  (pacman-contrib).
- RELEASE.md: replaced the drifted embedded publish-workflow example
  (floating action tags) with a pointer to the shipped workflow, corrected
  the version-carrier list (PKGBUILD / .SRCINFO also carry the version), and
  added the missing AUR version-bump step.

### Security
- User-supplied dimensions are now capped — `--width`/`--height` at 4096
  per axis and 1,000,000 total cells, export `--scale` at 1–512 with a
  64-megapixel image ceiling — so one mistyped command can no longer request
  a machine-freezing allocation. This closes the in-scope item from
  SECURITY.md ("Denial of service through pathological --width / --height
  values").

## [0.1.0] - 2026-07-11

### Added
- Initial release of **crest**: a generative terminal-art CLI
- **5 parametric patterns**: wave, plasma, gradient, mandala, ripple
- **8 colour maps**: mono, ember, fire, ocean, viridis, rainbow, ice, matrix
- **2 glyph styles**: Unicode blocks (shaded) and ASCII ramp
- **Live animation** with `animate` command
- **PNG export** via `export` command (optional Pillow dependency)
- **Interactive wizard** for guided setup and discovery
- **Zero core dependencies** — runs on any Python 3.8+ install
- Comprehensive test suite (36 tests)
- Shell integration helpers (fish and sh launchers)
- Full CLI documentation and usage examples

### Features
- Pure parametric generators (deterministic, no side effects)
- Modular architecture: patterns, colours, renderers, CLI
- ANSI truecolour terminal rendering
- Lazy-loaded optional dependencies (Pillow for PNG)
- Cross-platform support
- Terminal auto-detection for dimensions
