# AgentGym Sprint Report — 2026-03-08

## Scope completed
1. Split duplicate metrics into:
   - `protocol_retry_count` (retry loops on same request ID)
   - `semantic_duplicate_work_count` (distinct request IDs targeting same `(task_id, tool_id)` intent)
2. Added benchmark memory scenario coverage (`memory_cycle`) with deterministic `memory_write` / `memory_read` / `memory_invalidate` events.
3. Regenerated benchmark + markdown summary artifacts.
4. Added focused tests for metric split and memory counters.

## Validation runs
- `PYTHONPATH=src python3 scripts/smoke_check.py` ✅
- `PYTHONPATH=src python3 scripts/run_benchmark.py` ✅
- `python3 scripts/summarize_benchmark.py` ✅
- `PYTHONPATH=src python3 -m pytest -q` ❌ (`No module named pytest` in this environment)

## Key findings
- Protocol retries preserve prior behavior trends:
  - independent: `165`
  - planner_worker: `85`
  - shared_memory: `32`
- Semantic duplicates are now separated from retries and currently `0` in the default policy plans.
- Memory scenario increments event count by +3/run and reports `avg_mem_w/r/i = 1.00/1.00/1.00` for each policy, while leaving completion latency and retry counts unchanged.

## Metric deltas vs prior combined metric snapshot
Prior snapshot (combined duplicate metric):
- independent: `duplicate_intent_count=10`
- planner_worker: `duplicate_intent_count=1`
- shared_memory: `duplicate_intent_count=4`

Now (split):
- `protocol_retry_count`: 165 / 85 / 32
- `semantic_duplicate_work_count`: 0 / 0 / 0

Interpretation: previous duplicate signal was dominated by protocol retries; split removes this confound.

## Next risks
- Benchmark currently does not include a semantic-duplicate workload; that metric can remain zero in normal runs and should be explicitly stress-tested.
- No pytest available in runtime; CI/local dev env should install test dependencies to avoid drift between smoke and unit checks.
- `duplicate_tool_calls` remains as compatibility alias; downstream consumers should migrate to split metrics before alias removal.
