# Releasing crest

This guide covers packaging and publishing a **crest** release to GitHub and
PyPI. The package is built and verified in step 1; the remaining steps
distribute it.

## Prerequisites

- Python 3.8+ and `pip`
- A [PyPI](https://pypi.org) account (for upload) and a GitHub repo at
  `https://github.com/melancholysky/crest`
- Build tooling: `pip install build twine`

Commands below use a `$VERSION` shell variable as a placeholder for the
release version. Set it once in your shell before running them:

```bash
VERSION=0.1.0   # replace with the version you are releasing
```

## 1. Build the distribution

The wheel and source distribution are produced with:

```bash
python -m build
```

Outputs land in `dist/`:

- `crest_art-$VERSION-py3-none-any.whl` (universal wheel)
- `crest_art-$VERSION.tar.gz` (source distribution)

Verify the package metadata before publishing:

```bash
twine check dist/*
```

## 2. Publish to PyPI

Manual upload with twine:

```bash
# Optional: test on PyPI staging first
twine upload --repository testpypi dist/crest_art-$VERSION*

# Production
twine upload dist/crest_art-$VERSION*
```

Alternatively, automate via GitHub Actions (recommended for future releases).
Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  push:
    tags:
      - 'v*'

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install build tools
        run: pip install build twine
      - name: Build distributions
        run: python -m build
      - name: Publish to PyPI
        run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
```

## 3. Create a GitHub release

1. Go to https://github.com/melancholysky/crest/releases
2. Click "Draft a new release"
3. Tag: `v$VERSION`
4. Title: `crest v$VERSION`
5. Description (the v0.1.0 announcement below is a working example — update
   the "What's New" list from `CHANGELOG.md` for each release):

   ```markdown
   **Generative terminal-art CLI** — First release!

   ## What's New
   - 5 parametric patterns: wave, plasma, gradient, mandala, ripple
   - 8 colour maps: mono, ember, fire, ocean, viridis, rainbow, ice, matrix
   - 2 glyph styles: Unicode blocks and ASCII ramp
   - Live animation with smooth phase interpolation
   - PNG export (optional, with Pillow)
   - Interactive wizard for guided discovery
   - Zero core dependencies
   - 30 tests

   ## Installation
       pip install crest-art          # Core (no dependencies)
       pip install crest-art[png]     # With PNG export

   > Note: the PyPI package is `crest-art` (the name `crest` was already
   > taken on PyPI), but the installed command is still just `crest`.

   ## Quick Start
       crest                          # Interactive wizard
       crest render -p wave -c ember  # Static frame
       crest animate -p plasma        # Live animation
   ```
6. Optionally attach `dist/crest_art-$VERSION-py3-none-any.whl` and
   `dist/crest_art-$VERSION.tar.gz`
7. Publish

## 4. Verify installation

From PyPI (fresh environment):

```bash
python3 -m venv /tmp/crest_test
source /tmp/crest_test/bin/activate
pip install crest-art
crest --version
crest list
crest render -p mandala -c rainbow -g ascii -w 40 -H 12
```

From the built wheel — verifies the exact artifact produced in step 1, works
before publishing, and does not depend on GitHub release assets:

```bash
python3 -m venv /tmp/crest_wheel_test
source /tmp/crest_wheel_test/bin/activate
pip install "dist/crest_art-$VERSION-py3-none-any.whl"
crest --version
```

If you attached the distributions to the GitHub release (optional step in
section 3), you can instead download the wheel from the release page and
`pip install` that file.

## Package facts

- **Name**: `crest-art` (PyPI distribution; the importable module and `crest` command are unchanged)
- **Version**: `0.1.0`
- **License**: MIT
- **Entry point**: `crest = "crest.cli:main"`
- **Build backend**: setuptools
- **Python**: 3.8–3.14
- **Core dependencies**: none (Pillow optional, via `[png]`)
- **Repository**: https://github.com/melancholysky/crest
- **PyPI**: https://pypi.org/project/crest-art/

## Publishing to PyPI

The built distributions are in `dist/` and have passed `twine check`.
You need a PyPI API token (https://pypi.org/manage/account/token/).
**Never paste the token into chat or commit it.**

### Option A — GitHub Actions (recommended for future releases)

1. In the GitHub repo: **Settings → Secrets and variables → Actions →
   New repository secret**.
   - Name: `PYPI_API_TOKEN`
   - Value: your PyPI token (`pypi-AgEI...`)
2. Ensure `.github/workflows/publish.yml` is in the repo (it ships in this
   folder).
3. Push the `v$VERSION` tag — the workflow builds and uploads automatically:
   ```bash
   git tag -a "v$VERSION" -m "Release v$VERSION"
   git push origin "v$VERSION"
   ```

### Option B — Manual upload (fastest for a one-off release)

Run from this folder, feeding the token via an environment variable so it
never lands in shell history:

```bash
export PYPI_API_TOKEN="pypi-AgEI...your-token-here"
twine upload --username __token__ --password "$PYPI_API_TOKEN" dist/crest_art-$VERSION*
unset PYPI_API_TOKEN
```

## AUR package (Arch / CachyOS)

An AUR `PKGBUILD` lives in `aur/` (and is excluded from the PyPI sdist).
It builds from the PyPI sdist, so **publish to PyPI first**.

1. After PyPI publish, compute the sdist checksum:
   ```bash
   cd aur
   # either download the sdist and run:
   sha256sum crest_art-$VERSION.tar.gz
   # or let pkgconf fill it in:
   updpkgsums
   ```
2. Replace `sha256sums=('SKIP')` with the real hash.
3. Verify it builds locally:
   ```bash
   cd aur && makepkg -si
   ```
4. Submit to the AUR (create the `crest-art` package, upload `PKGBUILD` +
   `.SRCINFO` generated by `makepkg --printsrcinfo > .SRCINFO`).

## Pre-release checklist

- [x] Code tested (30/30 tests passing)
- [x] Version consistent in `__init__.py` and `pyproject.toml`
- [x] `CHANGELOG.md` created
- [x] `.gitignore` configured
- [x] `README.md` complete with examples
- [x] `pyproject.toml` carries PyPI metadata
- [x] Distributions built (wheel + sdist)
- [x] `twine check` passes
- [x] Published to PyPI
- [x] GitHub release created

## Post-release maintenance

- Monitor download stats at https://pypi.org/project/crest-art/
- Respond to GitHub issues and pull requests
- For bug fixes or features: bump the version in `__init__.py` and
  `pyproject.toml`, add `CHANGELOG.md` notes, rebuild, and re-upload.

## Credits

- **hy3** — development and the core idea behind crest.
- **Melancholy Sky** — project author and maintainer.
