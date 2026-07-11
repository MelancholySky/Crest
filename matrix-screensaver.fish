#!/usr/bin/env fish
# Green-themed screensaver using crest
# Run with: ./matrix-screensaver.fish
# Press Ctrl+C to exit

set -l DIR (dirname (status filename))
set -l VENV $DIR/.venv

# Ensure the project's venv exists (bootstrapped on first run),
# then drive the installed `crest` executable so we never depend on
# CWD or a system-wide `crest` install.
if not test -d $VENV
    echo "First run: creating virtual environment in $VENV"
    python3 -m venv $VENV
    $VENV/bin/pip install -e $DIR --quiet
end

# NOTE: fish's `echo` does not expand backslash escapes, so assigning
# "\033[0;32m" to a variable emits the literal string, not a colour code.
# Use `set_color` for real terminal colour.
set_color green
echo "=== crest Screensaver ==="
set_color normal
echo "Press Ctrl+C to exit"
echo ""

# Launch the matrix animation via the project venv.
# Pattern options: wave, plasma, ripple, gradient, mandala
# Adjust -s (speed) and -d (delay) for different effects.
$VENV/bin/crest animate \
  --pattern plasma \
  --color matrix \
  --glyph blocks \
  --speed 0.08 \
  --delay 0.05
