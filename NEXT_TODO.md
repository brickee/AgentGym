# NEXT TODO

## Immediate (next session)
1. Couple memory workload to task outcomes (cache hit/miss patterns that alter tool choice or latency) instead of standalone memory events.
2. Add per-scenario delta reporting (policy-vs-policy and baseline-vs-semantic_overlap-vs-memory_cycle) in summary output.
3. Add dependency bootstrap (`pytest` + minimal dev extras) and a single CI command running smoke + unit checks.

## Quality tasks
- Add strict schema/versioning for benchmark CSV columns to avoid downstream parser drift.
- Plan migration timeline for legacy aliases (`retry_count`, `duplicate_tool_calls`).
- Add a deterministic communication stress scenario (broadcast vs point-to-point) for governance policy comparisons.
