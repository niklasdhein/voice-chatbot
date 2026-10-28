#!/usr/bin/env bash
set -e

# Navigate to project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment if present
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

python3 main.py
