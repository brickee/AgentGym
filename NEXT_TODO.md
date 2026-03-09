# NEXT TODO

## Immediate (next session)
1. Add recommendation confidence intervals over seeds for replay/liveness metrics (`replay_anomaly_score`, `unfinished_task_count`, starvation gap) and surface CI in summary.
2. Add CI benchmark guardrails with hard thresholds for anomaly counters in non-proxy scenarios (should stay near zero outside stress tests).
3. Tune robustness scoring weights with explicit policy goals (latency-first vs reliability-first presets).

## Quality tasks
- Add per-scenario markdown callouts for “safe operating region” of memory confidence thresholds.
- Add compact benchmark regression fixture (small seeds/tasks) for faster CI precheck.
- Consider a mixed stress case (`memory_poisoning + comm_stress_broadcast`) with explicit failure-budget targets.
