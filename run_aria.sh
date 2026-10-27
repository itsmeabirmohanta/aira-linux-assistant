#!/bin/bash
# Wrapper to run ARIA handling symlinks and paths cleanly
REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
cd "$SCRIPT_DIR"
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
exec "$SCRIPT_DIR/.venv/bin/python" -m aria.main "$@"
