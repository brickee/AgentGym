# NEXT TODO

## Immediate (next session)
1. Add scenario-specific recommendation confidence (seed variance bands + tie-break details) in summary output.
2. Add a mixed stress scenario combining memory poisoning + communication broadcast to stress cross-axis failure modes.
3. Add explicit benchmark regression checks in CI for memory robustness rates (upper bounds by policy).

## Quality tasks
- Expand communication effectiveness reporting with policy ranking and confidence intervals over seeds.
- Enable pytest in runtime image so direct `PYTHONPATH=src python3 -m pytest -q` works without fallback path.
- Add CI assertion that replay violation totals must remain zero across all benchmark rows.
