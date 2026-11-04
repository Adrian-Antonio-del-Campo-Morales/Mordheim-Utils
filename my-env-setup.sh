#!/usr/bin/env bash
# Activate the virtual environment of the checkout this shell is in.
# HFI may inline this content in a worktree shell, so the checkout is found
# from the working directory, never from this file's path.  Every worktree
# needs its own .venv (create it with: python3 tools/setup_worktree.py); a
# venv from another checkout would import that checkout's packages and native
# extension, so none is used as a fallback.
__mordheim_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [ -n "${VIRTUAL_ENV:-}" ] && [ "$VIRTUAL_ENV" != "$__mordheim_root/.venv" ]; then
    # Drop a venv inherited from another checkout before anything else.
    PATH="$(printf '%s' "$PATH" | tr ':' '\n' | grep -vxF "$VIRTUAL_ENV/bin" | paste -sd: -)"
    unset VIRTUAL_ENV PYTHONHOME
fi
if [ -f "$__mordheim_root/.venv/bin/activate" ]; then
    # shellcheck disable=SC1091
    source "$__mordheim_root/.venv/bin/activate"
else
    echo "WARNING: $__mordheim_root has no .venv; run: python3 tools/setup_worktree.py" >&2
fi
unset __mordheim_root
