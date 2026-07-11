#!/usr/bin/fish
# crest launcher — bootstraps a venv on first run, then runs the CLI.
# Usage: ./run.fish [args...]   (no args launches the wizard)
set -l DIR (dirname (status filename))
set -l VENV $DIR/.venv

if not test -d $VENV
    echo "First run: creating virtual environment in $VENV"
    python3 -m venv $VENV
    $VENV/bin/pip install -e . --quiet
end

$VENV/bin/crest $argv
