# NEXT TODO

## Immediate (next session)
1. Diversify deadlock/starvation proxy workloads by policy (currently scenario forcing yields near-identical signatures across policies).
2. Add recommendation confidence intervals over seeds for the new replay/liveness metrics (`replay_anomaly_score`, `unfinished_task_count`, starvation gap).
3. Add CI benchmark guardrails with hard thresholds for anomaly counters in non-proxy scenarios (should stay near zero outside stress tests).

## Quality tasks
- Add per-scenario markdown callouts for “safe operating region” of memory confidence thresholds.
- Add compact benchmark regression fixture (small seeds/tasks) for faster CI precheck.
- Consider a mixed stress case (`memory_poisoning + comm_stress_broadcast`) with explicit failure-budget targets.
