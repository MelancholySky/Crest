#!/usr/bin/env bash
# Green-themed screensaver using crest
# Run with: ./matrix-screensaver.sh
# Press Ctrl+C to exit

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

# Ensure the project's venv exists (bootstrapped on first run),
# then drive the installed `crest` executable so we never depend on
# CWD or a system-wide `crest` install.
if [ ! -d "$VENV" ]; then
    echo "First run: creating virtual environment in $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -e "$DIR" --quiet
fi

# Colors for output
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}=== crest Screensaver ===${NC}"
echo "Press Ctrl+C to exit"
echo ""

# Run the matrix animation
# Pattern options: wave, plasma, ripple, gradient, mandala
# Adjust -s (speed) and -d (delay) for different effects

"$VENV/bin/crest" animate \
  --pattern plasma \
  --color matrix \
  --glyph blocks \
  --speed 0.08 \
  --delay 0.05
