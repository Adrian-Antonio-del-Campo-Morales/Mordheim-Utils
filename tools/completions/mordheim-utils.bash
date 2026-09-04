# Tab completion for tools/mordheim-utils.py (bash and Git Bash).
#
# Source it once per shell, e.g. from ~/.bashrc:
#   source /path/to/tools/completions/mordheim-utils.bash
#
# After sourcing, `mordheim-utils` runs the launcher and Tab completes:
#   mordheim-utils <TAB>                 -> subcommand names
#   mordheim-utils benchmark --deep <TAB> -> options / choice values
# Direct launcher paths also complete when they are the first word
# (tools/mordheim-utils.py, ./tools/mordheim-utils.py).

_mordheim_utils_root() {
    # Directory of the completion script: <root>/tools/completions/mordheim-utils.bash
    local source_dir
    source_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    cd "$source_dir/../.." && pwd
}

_mordheim_utils_complete() {
    local launcher root
    root="$(_mordheim_utils_root)"
    launcher="$root/tools/mordheim-utils.py"

    # Find the launcher token (function name or script path) and complete the
    # words that follow it, so `python tools/mordheim-utils.py ...` also works.
    local words_start=0
    local index word
    for index in "${!COMP_WORDS[@]}"; do
        word="${COMP_WORDS[index]}"
        if [[ "$word" == *mordheim-utils.py || "$word" == mordheim-utils ]]; then
            words_start=$((index + 1))
            break
        fi
    done

    local -a args
    args=("${COMP_WORDS[@]:words_start}")
    local output
    output="$(python "$launcher" _complete "${args[@]}" 2>/dev/null)"
    COMPREPLY=()
    while IFS= read -r candidate; do
        [[ -n "$candidate" ]] && COMPREPLY+=("$candidate")
    done <<< "$output"
}

# Convenience wrapper so the completion is bound to a stable first word.
if ! declare -F mordheim-utils >/dev/null 2>&1; then
    _MU_SCRIPT_ROOT="$(_mordheim_utils_root)"
    mordheim-utils() { python "$_MU_SCRIPT_ROOT/tools/mordheim-utils.py" "$@"; }
    unset _MU_SCRIPT_ROOT
fi

complete -F _mordheim_utils_complete mordheim-utils
complete -F _mordheim_utils_complete tools/mordheim-utils.py
complete -F _mordheim_utils_complete ./tools/mordheim-utils.py
