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

# Non-proxy anomaly guardrails: enforce stable upper-bounds in non-proxy scenarios.
PYTHONPATH=src python3 - <<'PY'
import csv
from pathlib import Path

csv_path = Path("artifacts/benchmark_v0.csv")
if not csv_path.exists():
    raise SystemExit("CI_FAIL missing artifacts/benchmark_v0.csv; run benchmark first")

scenario_limits = {
    "baseline": {"replay_anomaly_score": 18.0, "unfinished_task_count": 0.0},
    "semantic_overlap": {"replay_anomaly_score": 85.0, "unfinished_task_count": 0.0},
    "memory_cycle": {"replay_anomaly_score": 25.0, "unfinished_task_count": 0.0},
    "memory_cycle@thr_0.50": {"replay_anomaly_score": 25.0, "unfinished_task_count": 0.0},
    "memory_cycle@thr_0.70": {"replay_anomaly_score": 25.0, "unfinished_task_count": 0.0},
    "memory_cycle@thr_0.90": {"replay_anomaly_score": 35.0, "unfinished_task_count": 0.0},
    "memory_poisoning": {"replay_anomaly_score": 35.0, "unfinished_task_count": 0.0},
    "memory_staleness_heavy": {"replay_anomaly_score": 35.0, "unfinished_task_count": 0.0},
    "comm_stress_p2p": {"replay_anomaly_score": 18.0, "unfinished_task_count": 0.0},
    "comm_stress_broadcast": {"replay_anomaly_score": 18.0, "unfinished_task_count": 0.0},
    "resource_contention": {"replay_anomaly_score": 10.0, "unfinished_task_count": 0.0},
}

violations = []
with csv_path.open("r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        scenario = row.get("scenario", "")
        limits = scenario_limits.get(scenario)
        if not limits:
            continue
        for metric, limit in limits.items():
            val = float(row.get(metric, 0.0))
            if val > limit:
                violations.append((scenario, row.get("policy", ""), row.get("seed", ""), metric, val, limit))

if violations:
    print("CI_FAIL non-proxy anomaly guardrail breached")
    for v in violations[:20]:
        s, p, seed, metric, val, limit = v
        print(f"  scenario={s} policy={p} seed={seed} metric={metric} value={val:.4f} limit={limit:.4f}")
    raise SystemExit(1)

print("CI_OK non-proxy anomaly guardrails")
PY
