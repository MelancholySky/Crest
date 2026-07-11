#!/usr/bin/env bash
# crest launcher — bootstraps a venv on first run, then runs the CLI.
# Usage: ./run.sh [args...]   (no args launches the wizard)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$DIR/.venv"

if [ ! -d "$VENV" ]; then
    echo "First run: creating virtual environment in $VENV"
    python3 -m venv "$VENV"
    "$VENV/bin/pip" install -e . --quiet
fi

exec "$VENV/bin/crest" "$@"
