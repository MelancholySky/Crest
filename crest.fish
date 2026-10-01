# crest fish function — puts `crest` on your PATH without typing the venv path.
#
# IMPORTANT: this is a function DEFINITION, not an executable script. It has no
# shebang on purpose, so running it directly (e.g. `./crest.fish`) fails with
# "fish scripts require an interpreter directive". You MUST source it:
#
#   source /path/to/crest/crest.fish
#
# or add that line to your ~/.config/fish/config.fish.

# Resolve the venv binary from this file's own location so the helper works
# no matter where the repo is cloned. `realpath` makes the path absolute, so
# the definition-time snapshot below survives a later `cd` or a relative
# `source` path.
set -l crest_bin (realpath (dirname (status filename)))/.venv/bin/crest

# The function body runs at *call* time — long after `source` has finished
# and this file's local variables are gone. Looking up $crest_bin then would
# expand to nothing ("The expanded command was empty"), so `--inherit-variable`
# (-V) snapshots the value into the function's own scope at definition time.
function crest --wraps=$crest_bin -V crest_bin --description "crest generative terminal-art CLI"
    $crest_bin $argv
end
