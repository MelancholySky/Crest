# release/ — upload-ready copy

This `release/` folder is a complete, self-contained copy of the **crest**
project, prepared for publishing to GitHub. Upload its contents as the
repository (the full codebase + docs + scripts).

## What's inside
- `crest/` — full source (all modules)
- `tests/` — test suite (30 tests)
- `pyproject.toml`, `requirements.txt` — packaging
- `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `AGENTS.md`,
  `RELEASE.md`, `IDLE_SCREENSAVER.md` — documentation
- `run.fish`, `run.sh`, `crest.fish`, `matrix-screensaver.*`, `idle-screensaver.py`
  — launch/screensaver helpers
- `dist/` — prebuilt package (`crest-0.1.0-py3-none-any.whl`, `crest-0.1.0.tar.gz`)

## Publishing steps
1. Create the GitHub repo `melancholysky/crest` and upload this folder's
   contents as the initial commit.
2. Tag the release `v0.1.0`.
3. On the GitHub **Releases** page, draft a new release from `v0.1.0` and
   attach `dist/crest-0.1.0-py3-none-any.whl` and `dist/crest-0.1.0.tar.gz`
   as **release assets** (the repo's `.gitignore` excludes `dist/`, so the
   built files are not committed to the tree — attach them manually there).

## Rebuilding the package
If you need fresh artifacts, build from a **temporary copy** of this folder
(not inside it), so the build process does not write `*.egg-info`/`build/`
into the upload copy:

```bash
cp -r release /tmp/crest-build
cd /tmp/crest-build
python -m build        # produces dist/crest-0.1.0-*.whl and .tar.gz
twine check dist/*     # validate metadata before upload
# then copy the new dist/ files back into release/dist/
```

This folder mirrors the project root minus local dev artifacts
(`.venv`, `.pytest_cache`, `*.egg-info`, `build/`, `__pycache__`).
