# NEXT TODO

## Immediate (next session)
1. Wire replay analytics outputs into benchmark summary tables (not just helper functions) with per-scenario decomposition excerpts.
2. Add deterministic `resource_contention` scenario coverage and include it in scenario delta tables.
3. Add invariant regression tests for replay precheck + validator edge cases (`non-monotonic sim_time`, terminal-after-terminal, uncreated-task tool request).

## Quality tasks
- Add migration note and deprecation warnings timeline for legacy aliases (`retry_count`, `duplicate_tool_calls`).
- Expand communication effectiveness reporting with policy ranking and confidence over seeds.
- Enable pytest in runtime image so CI checks can run full suite locally.
