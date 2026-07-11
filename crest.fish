# crest fish function — puts `crest` on your PATH without typing the venv path.
#
# IMPORTANT: this is a function DEFINITION, not an executable script. It has no
# shebang on purpose, so running it directly (e.g. `./crest.fish`) fails with
# "fish scripts require an interpreter directive". You MUST source it:
#
#   source /path/to/crest/crest.fish
#
# or add that line to your ~/.config/fish/config.fish.

# Resolve the project root from this file's own location so the helper works
# no matter where the repo is cloned.
set -l CREST_DIR (dirname (status filename))

function crest --wraps=$CREST_DIR/.venv/bin/crest --description "crest generative terminal-art CLI"
    $CREST_DIR/.venv/bin/crest $argv
end
