#!/usr/bin/env bash

# Resolve directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Launch inside terminal (e.g. konsole)
if command -v konsole >/dev/null 2>&1; then
    konsole -e "$SCRIPT_DIR/run.sh"
elif command -v x-terminal-emulator >/dev/null 2>&1; then
    x-terminal-emulator -e "$SCRIPT_DIR/run.sh"
else
    "$SCRIPT_DIR/run.sh"
fi
