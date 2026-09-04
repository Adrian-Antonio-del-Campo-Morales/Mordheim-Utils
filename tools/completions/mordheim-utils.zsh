#compdef mordheim-utils
# Tab completion for tools/mordheim-utils.py (zsh).
#
# Source it once per shell, e.g. from ~/.zshrc:
#   source /path/to/tools/completions/mordheim-utils.zsh
#
# After sourcing, `mordheim-utils` runs the launcher and Tab completes the
# subcommand names and, for the delegated lab parsers, the options and
# choice values.

typeset -g _MU_SCRIPT_ROOT=${${(%):-%x}:A:h:h:h}

if (( ! $+functions[mordheim-utils] )); then
    mordheim-utils() { python "$_MU_SCRIPT_ROOT/tools/mordheim-utils.py" "$@" }
fi

_mordheim_utils_complete() {
    local -a completions
    local -a typed
    local word index start output
    start=0
    for ((index = 1; index <= ${#words}; index++)); do
        word="${words[index]}"
        if [[ "$word" == *mordheim-utils.py || "$word" == mordheim-utils ]]; then
            start=$index
            break
        fi
    done
    # zsh keeps the partially typed word out of $words; hand it to the
    # launcher as the final token so prefix filtering stays in one place.
    if ((start > 0 && start < CURRENT)); then
        typed=("${(@)words[$((start + 1)), $((CURRENT - 1))]}")
    fi
    typed+=("$PREFIX")

    output="$(python "$_MU_SCRIPT_ROOT/tools/mordheim-utils.py" _complete "${typed[@]}" 2>/dev/null)"
    completions=("${(@f)output}")
    compadd -- $completions
}

compdef _mordheim_utils_complete mordheim-utils
