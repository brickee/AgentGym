# NEXT TODO

## Immediate (next session)
1. Add a dedicated semantic-duplicate benchmark scenario (distinct request IDs for same task/tool intent) so `semantic_duplicate_work_count` is exercised in benchmark tables.
2. Couple memory workload to task outcomes (cache hit/miss patterns affecting tool choice/latency), not just standalone memory events.
3. Add dependency bootstrap (`pytest` + minimal dev extras) and a single CI command that runs smoke + unit checks.

## Quality tasks
- Add per-scenario delta table generator (baseline vs memory/semantic scenarios).
- Add strict schema/versioning for benchmark CSV columns to avoid downstream parser drift.
- Plan migration timeline for legacy aliases (`retry_count`, `duplicate_tool_calls`).
