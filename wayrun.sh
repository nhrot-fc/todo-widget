#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PY="$PROJECT_ROOT/.venv/bin/python"

if [ -x "$VENV_PY" ]; then
  PY_EXEC="$VENV_PY"
else
  PY_EXEC="$(command -v python3 || command -v python)"
fi

export PYTHONPATH="$PROJECT_ROOT${PYTHONPATH+:$PYTHONPATH}"

cd "$PROJECT_ROOT"
exec "$PY_EXEC" main.py "$@"
