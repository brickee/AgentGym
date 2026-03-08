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

## 2026-03-08 (Autopilot sprint — metric split + memory benchmark)
- Split retry/duplicate signal into separate runtime metrics:
  - `protocol_retry_count`
  - `semantic_duplicate_work_count`
- Preserved compatibility aliases:
  - `retry_count` -> protocol retries
  - `duplicate_tool_calls` -> semantic duplicate work
- Added deterministic memory benchmark scenario (`memory_cycle`) with write/read/invalidate lifecycle coverage.
- Expanded benchmark output columns to include split metrics + memory counters.
- Updated benchmark summary script for scenario-aware aggregation.
- Added targeted tests (`tests/test_metrics_split_and_memory.py`) for:
  - retry vs semantic duplicate separation
  - memory counter + invalidate behavior
- Generated sprint artifact report: `artifacts/sprint_report_20260308.md`.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`
- `PYTHONPATH=src python3 -m pytest -q` failed: `No module named pytest` (environment blocker)

### Self-review
- Split metric semantics now avoid counting retries as duplicate work (resolves prior confound).
- Memory workload currently validates event plumbing only; richer task-coupled memory scenarios remain for next pass.

## 2026-03-08 (Autopilot sprint — semantic overlap + communication metrics)
- Added dedicated `semantic_overlap` benchmark scenario using deterministic policy-provided duplicate-intent plans.
- Expanded policy realism (deterministic task/tool mixes + explicit communication plans) while keeping reproducibility.
- Added runtime `send_message` event handling with event-level metrics:
  - `communication_event_count`
  - `communication_cost`
- Wired communication metrics into benchmark CSV output and markdown summary aggregation.
- Hardened task completion scheduling to avoid duplicate terminal events when multiple tools complete for one task.
- Added tests (`tests/test_policy_signal_and_comm.py`) for:
  - policy-distinguishable semantic duplicate-work signal
  - event-level communication metric accounting
- Updated README quickstart/status/metric notes for new scenarios and communication counters.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`
- `PYTHONPATH=src python3 -m pytest -q` failed: `No module named pytest` (environment blocker)

## 2026-03-08 (Autopilot sprint — memory semantics coupled to task outcomes)
- Replaced standalone memory-cycle events with policy-driven, task-coupled memory workloads.
- Added memory runtime semantics:
  - TTL (`expires_at`)
  - confidence threshold filtering (`min_confidence`)
  - stale/low-confidence miss tracking
- Extended `memory_read` to branch into deterministic tool request paths (`on_hit` vs `on_miss`), directly affecting task runtime outcomes.
- Added policy-specific memory-cycle plans across independent/planner-worker/shared-memory baselines.
- Expanded benchmark outputs and summary aggregation with memory quality counters:
  - `memory_hit_count`, `memory_miss_count`, `memory_stale_read_count`, `memory_low_confidence_read_count`
- Added/updated tests for memory hit/miss path execution and stale-read accounting.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

## 2026-03-08 (Autopilot sprint — scenario delta reporting)
- Extended `scripts/summarize_benchmark.py` with comparative delta sections:
  - policy deltas vs independent within each scenario
  - scenario deltas vs baseline within each policy
- Kept output deterministic and CSV-driven (no hidden state), while preserving existing aggregate table.
- Regenerated `artifacts/benchmark_v0_summary.md` with deltas to support faster policy/scenario sensitivity reads.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`
