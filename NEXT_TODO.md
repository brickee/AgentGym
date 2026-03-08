# NEXT TODO

## Immediate (next session)
1. Add dependency bootstrap (`pytest` + minimal dev extras) and a single CI command running smoke + unit checks.
2. Add confidence-threshold sweeps to memory_cycle to quantify quality-vs-latency tradeoff.
3. Add deterministic communication stress scenario (broadcast vs point-to-point) for governance policy comparisons.

## Quality tasks
- Add strict schema/versioning for benchmark CSV columns to avoid downstream parser drift.
- Plan migration timeline for legacy aliases (`retry_count`, `duplicate_tool_calls`).
- Add a deterministic communication stress scenario (broadcast vs point-to-point) for governance policy comparisons.
