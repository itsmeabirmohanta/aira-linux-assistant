#!/bin/bash
# Backward-compatibility wrapper for ARIA background execution
SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
exec "$SCRIPT_DIR/run_aria.sh" "$@"
