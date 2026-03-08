#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 scripts/smoke_check.py

if PYTHONPATH=src python3 -c "import pytest" >/dev/null 2>&1; then
  PYTHONPATH=src python3 -m pytest -q
else
  echo "CI_NOTE pytest not installed; skipping unit tests"
fi
