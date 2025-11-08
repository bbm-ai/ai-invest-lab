#!/usr/bin/env bash
set -euo pipefail

# Activate venv
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

# Run once (manual)
python -m src.master_agent
