#!/usr/bin/env bash
set -euo pipefail

PYTHONPATH=src python3 scripts/smoke_check.py

LOCAL_PYTEST_PATH=".local-pydeps"
ensure_pytest() {
  if PYTHONPATH="src:${LOCAL_PYTEST_PATH}" python3 -c "import pytest" >/dev/null 2>&1; then
    return 0
  fi

  if ! command -v pip3 >/dev/null 2>&1; then
    return 1
  fi

  mkdir -p "${LOCAL_PYTEST_PATH}"
  if pip3 install --disable-pip-version-check --target "${LOCAL_PYTEST_PATH}" pytest >/dev/null 2>&1; then
    return 0
  fi

  return 1
}

if ensure_pytest; then
  PYTHONPATH="src:${LOCAL_PYTEST_PATH}" python3 -m pytest -q
else
  echo "CI_NOTE pytest unavailable; skipping unit tests (smoke/benchmark-only flow remains intact)"
fi
