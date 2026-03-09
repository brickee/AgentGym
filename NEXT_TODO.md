# NEXT TODO

## Immediate (next session)
1. Add per-scenario markdown callouts for “safe operating region” of memory confidence thresholds.
2. Add compact benchmark regression fixture (small seeds/tasks) for faster CI precheck.
3. Add scenario-budget drift detector (warn when anomaly metrics approach guardrail ceilings by >85%).

## Quality tasks
- Consider a mixed stress case (`memory_poisoning + comm_stress_broadcast`) with explicit failure-budget targets.
- Add optional bootstrap CI mode that runs compact fixture by default and full matrix on nightly.
- Add bootstrap-resampling CI option for tighter uncertainty estimates when seed count is small.
