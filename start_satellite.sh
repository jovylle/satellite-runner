#!/usr/bin/env bash
set -euo pipefail

# Go to repo root
cd "$(dirname "$0")"

# Run the Python module inside venv
exec venv/bin/python -m satellite_runner.main \
  >> "$HOME/.satellite-runner.log" 2>&1
