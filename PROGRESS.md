# PROGRESS LOG

## 2026-03-08
- Initialized project planning artifacts.
- Disabled daily papers push cron.
- Added daily progress-report cron at 17:00 UTC.
- Defined milestone roadmap (M0→M3).

### Decisions
- Keep MVP scope tight: DES + shared resource contention + 3 baselines.
- Use concise daily reporting format for continuity.

### Blockers
- Local test environment does not include pytest; temporary smoke checks run via `PYTHONPATH=src python3 scripts/smoke_check.py`.
- Need to add CI/test runner convention in next iteration.

## 2026-03-08 (Day 1 — iteration 1)
- Added `event_schema.yaml` and `world_state_schema.yaml`.
- Implemented minimal simulator core (`Event`, `WorldState`, `Simulator`).
- Added MVP world builder and baseline policy stub.
- Added smoke checks and validated run path.
- Wrote self-review notes for scaling/abstraction/reproducibility risks.

### Decisions
- Keep deterministic event ordering contract explicit: `(time, priority, seq_id)`.
- Prioritize transition validation + allocator abstraction in Day 2.

## 2026-03-08 (Day 1 — iteration 2)
- Added runtime `TransitionValidator` for tool lifecycle/task terminal/resource-balance checks.
- Added `ResourceAllocator` abstraction to decouple tool intent from resource accounting.
- Added replay recorder (`EventRecorder`) with JSONL artifact export.
- Expanded smoke checks and passed: `PYTHONPATH=src python3 scripts/smoke_check.py`.

### Decisions
- Fail fast on invalid event transitions (raise immediately) to prevent silent corruption.
- Keep replay format JSONL for cheap append + easy downstream analytics.

## 2026-03-08 (Next phase kickoff)
- Updated positioning to organization-level simulator in `README.md` and `PLAN.md`.
- Implemented token-bucket-based per-tool rate-limit support in allocator.
- Added backpressure policy responses: `wait`, `drop`, `retry`.
- Extended smoke check to cover rate-limited retry behavior.

### Decisions
- Keep backpressure policy in allocator first (single source), later expose to scenario config.
- Use explicit reject tags (`wait:*`, `retry:*`, `dropped:*`) for deterministic downstream event mapping.

## 2026-03-08 (Next phase iteration 2)
- Integrated allocator into simulator event flow (`tool_requested` -> allocate -> `tool_started`/`retry_scheduled`/`tool_failed`).
- Added automatic scheduling of `tool_finished` based on tool latency.
- Added resource release on `tool_finished` and auto `task_completed` scheduling.
- Added world-level `backpressure_policy` and resource config wiring.
- Re-ran end-to-end smoke: `SMOKE_CHECK_OK`.

### Decisions
- Keep retry delay fixed (1.0s) for now to preserve deterministic behavior; parameterize later.
- Let simulator own lifecycle scheduling so policy layer can stay simpler and pluggable.

## 2026-03-08 (Next phase iteration 3)
- Added configurable retry strategy in world config: `retry_mode` (`fixed`/`exp`), base/max delay.
- Added lightweight benchmark runner: 3 policies × 3 seeds -> `artifacts/benchmark_v0.csv`.
- Added quickstart benchmark command in README.
- Found and fixed validator bug in retry loop (`retry_scheduled -> tool_requested` transition).
- Re-ran benchmark after fix: `BENCHMARK_OK`.

### Decisions
- Keep validator strict but retry-aware; retries must loop through explicit state transitions.
- Keep runner simple first (scenario-level policy knobs), then swap in real policy logic next.

## 2026-03-08 (Next phase iteration 4)
- Replaced placeholder baselines with concrete policy planners:
  - `IndependentPolicy`
  - `PlannerWorkerPolicy`
  - `SharedMemoryPolicy`
- Runner now uses policy-generated request plans instead of hardcoded event patterns.
- Added average completion time metric and duplicate-intent signal.
- Wired task completion timestamps (`completed_at`) into simulator metrics.
- Re-ran smoke + benchmark successfully.

### Validation snapshot
- independent: retry_count=165, avg_completion_time=19.8545, duplicate_intent_count=10
- planner_worker: retry_count=85, avg_completion_time=12.2845, duplicate_intent_count=1
- shared_memory: retry_count=32, avg_completion_time=12.9528, duplicate_intent_count=4

### Decisions
- Keep policy behavior explicit and deterministic (no RNG in baseline logic yet).
- Use planner/intent level duplicate metric now; replace later with event-log-level duplicate-work metric.

## 2026-03-08 (Next phase iteration 5)
- Added runtime memory hooks to simulator: `memory_write`, `memory_read`, `memory_invalidate`.
- Upgraded duplicate metric from planner-intent approximation to runtime event-level (`duplicate_tool_calls`).
- Added benchmark summary generator: `scripts/summarize_benchmark.py` -> `artifacts/benchmark_v0_summary.md`.
- Added artifact hygiene in `.gitignore` to prevent generated files polluting commits.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

### Design note
- Current duplicate metric counts repeated `(task_id, tool_id)` requests including retry loops; next iteration should split into:
  - protocol-level retries
  - semantically duplicate work (distinct request IDs)
