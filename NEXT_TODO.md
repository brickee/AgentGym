# NEXT TODO

## Immediate (next session)
1. Add explicit migration/deprecation note for compatibility aliases (`retry_count`, `duplicate_tool_calls`) in README + summary output.
2. Extend replay analytics to emit per-agent duplicate rank deltas vs independent in markdown summary.
3. Add deterministic scenario for mixed memory+communication stress (cross-axis invariants under heavy retries).

## Quality tasks
- Expand communication effectiveness reporting with policy ranking and confidence intervals over seeds.
- Enable pytest in runtime image so CI checks can run full suite locally.
- Add CI assertion that replay violation totals must remain zero across all benchmark rows.
