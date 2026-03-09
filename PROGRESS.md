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

## 2026-03-08 (Autopilot sprint — dev bootstrap + single CI entrypoint)
- Added optional dev dependency group in `pyproject.toml`:
  - `.[dev]` includes `pytest>=8`
- Added `scripts/ci_check.sh` as a single deterministic CI entrypoint:
  - always runs smoke
  - runs `pytest -q` if available
  - prints explicit skip note when pytest is absent
- Added `Makefile` targets (`smoke`, `benchmark`, `summary`, `ci`) for standard workflow.
- Updated README with bootstrap + `make ci` usage.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`
- `make ci` -> smoke passed, pytest gracefully skipped when unavailable

## 2026-03-08 (Autopilot sprint — benchmark schema/version guardrails)
- Added explicit benchmark schema contract in runner (`BENCHMARK_SCHEMA_VERSION`, `BENCHMARK_COLUMNS`).
- CSV writer now enforces stable column ordering instead of deriving columns from row dict order.
- Added schema validation in summary script to fail fast on missing columns.
- Summary now reports observed schema version(s) from the benchmark artifact.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

## 2026-03-08 (Autopilot sprint — memory confidence-threshold sweeps)
- Added deterministic memory threshold sweeps in benchmark runner:
  - `memory_cycle@thr_0.50`
  - `memory_cycle@thr_0.70`
  - `memory_cycle@thr_0.90`
- Extended policy memory-plan APIs to accept optional `min_confidence` override for controlled sweeps.
- Preserved reproducibility by deriving threshold from scenario string only (no RNG/stateful behavior).
- Expanded summary output to include:
  - memory low-confidence counter in aggregate table (`hit/miss/stale/low_conf`)
  - dedicated memory threshold tradeoff table (latency/retries/hit-miss-low_conf)
- Updated README benchmark notes and advanced NEXT_TODO priorities.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

## 2026-03-08 (Autopilot sprint — deterministic communication stress scenarios)
- Added deterministic communication stress scenarios for governance comparisons:
  - `comm_stress_p2p`
  - `comm_stress_broadcast`
- Runner now rewrites message payload mode deterministically per scenario:
  - p2p: point-to-point messages
  - broadcast: one-to-many via `recipient_ids`
- Reused existing communication accounting path in simulator (`communication_event_count`, `communication_cost`) to compare stress modes without changing task logic.
- Updated README scenario list and NEXT_TODO priorities.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

## 2026-03-09 (Autopilot sprint — replay analytics + normalized comm metrics + invariant hardening)
- Added replay analytics helpers in `core/replay.py`:
  - event-type distribution snapshot
  - duplicate-work decomposition by agent/task with intent map
  - lightweight replay invariant precheck
- Hardened `TransitionValidator` with stricter invariants:
  - duplicate `task_created` rejection
  - `tool_requested` must reference created task
  - pending tool-request tracking exposed for debug checks
- Added communication normalization utilities in `eval/metrics.py`:
  - per-task / per-success communication cost
  - per-task communication/retry/duplicate rates
  - aggregate communication effectiveness score
- Extended benchmark schema in runner to `1.1` and added normalized communication columns.
- Regenerated benchmark + summary artifacts after schema update.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK` (`artifacts/benchmark_v0.csv`)
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK` (`artifacts/benchmark_v0_summary.md`)

### Blockers
- `pytest` still not available in this runtime, so deeper unit-suite expansion remains constrained to smoke/benchmark gates.

## 2026-03-09 (Autopilot sprint — replay-aware benchmark artifacts + contention scenario + validator deterministic tests)
- Wired replay analytics into benchmark artifacts (`schema_version` -> `1.2`):
  - `replay_violation_count`
  - `replay_duplicate_task_count`
  - `replay_top_duplicate_agent_count`
- Activated normalized communication metrics in benchmark rows (previously schema-declared but unpopulated):
  - `comm_cost_per_task`, `comm_cost_per_success`, `comm_events_per_task`
  - `retries_per_task`, `duplicates_per_task`, `comm_effectiveness`
- Added deterministic `resource_contention` scenario with tighter shared-resource limits and exponential retry backoff.
- Extended benchmark summary report with two new sections:
  - normalized communication metrics table
  - replay invariant/decomposition table
- Added deterministic invariant tests for validator/replay edge-cases:
  - pending-request bookkeeping clears on terminal tool events
  - duplicate `task_created` and uncreated-task `tool_requested` guards
  - replay precheck catches non-monotonic `sim_time` and terminal-after-terminal lifecycle events
- Added scenario regression test asserting `resource_contention` increases retry pressure vs baseline for independent policy.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`

### Metric snapshot / deltas
- Baseline metrics remained stable for existing scenarios (example: `baseline/independent` delta: latency `+0.0000`, retries `+0.00`, semantic duplicates `+0.00`).
- New scenario `resource_contention/independent` introduced expected stress behavior:
  - avg completion time `17.0317`
  - avg protocol retries `36.00`
  - replay violations `0.00`
- Total replay violations across full benchmark matrix: `0`.

## 2026-03-09 (Autopilot sprint — local pytest path + memory poisoning/staleness robustness + recommendations)
- Added local pytest install fallback path in `scripts/ci_check.sh`:
  - attempts import from `src:.local-pydeps`
  - auto-installs pytest into `.local-pydeps` when missing
  - preserves no-deps behavior by smoke-only fallback when install/import fails
- Extended world/simulator memory metrics with poisoning counters:
  - `memory_poisoned_write_count`
  - `memory_poisoned_read_count`
- Added stronger memory robustness scenarios in benchmark runner:
  - `memory_poisoning`
  - `memory_staleness_heavy`
- Advanced benchmark schema to `1.3` and emitted robustness rates:
  - `memory_stale_miss_rate`
  - `memory_poison_exposure_rate`
- Expanded summary report with:
  - concise recommendation section (best policy by scenario)
  - tradeoff flags (`high_comm_cost`, `high_retry_pressure`, `stale_memory_risk`, `poisoning_risk`)
  - dedicated memory robustness table
- Updated tests to cover poisoning/staleness metric plumbing and scenario emissions.

### Validation
- `PYTHONPATH=src python3 scripts/smoke_check.py` -> `SMOKE_CHECK_OK`
- `PYTHONPATH=src python3 scripts/run_benchmark.py` -> `BENCHMARK_OK`
- `python3 scripts/summarize_benchmark.py` -> `SUMMARY_OK`
- `PYTHONPATH=src python3 -m pytest -q` -> still unavailable globally (`No module named pytest`)
- `./scripts/ci_check.sh` -> passed with local pytest path fallback (`15 passed`)

### Blockers
- Global environment still lacks system pytest; local fallback works, but direct `python3 -m pytest -q` remains unavailable unless local path is provided.

## 2026-03-09 (Autopilot phase — memory calibration + replay anomalies + edge proxies)
- Calibrated memory stress knobs for clearer but realistic tradeoffs:
  - `memory_poisoning`: poison only a minority of writes (`i % 3 == 0`), confidence softened to `0.88`, and hit gate set to `min_confidence=0.82`.
  - `memory_staleness_heavy`: TTL/read timings adjusted to induce high stale pressure without making every read trivially stale.
- Added deterministic edge-case benchmark scenarios:
  - `deadlock_proxy`: serialized resources + `drop` backpressure to quantify liveness collapse (`unfinished_task_count`, `tool_failed`).
  - `starvation_proxy`: serialized compute lane + aggressive exponential retries to quantify tail-latency inflation.
- Added replay-derived anomaly counters in benchmark output:
  - `replay_retry_scheduled_count`, `replay_tool_failed_count`, `replay_anomaly_score`.
- Wired new anomaly + liveness/tail counters into summary recommendation scoring and risk flags.
- Added targeted tests in `tests/test_benchmark_scenarios.py`.

### Validation (required chain)
- `PYTHONPATH=src python3 scripts/smoke_check.py` ✅
- `PYTHONPATH=src python3 scripts/run_benchmark.py` ✅
- `python3 scripts/summarize_benchmark.py` ✅
- `./scripts/ci_check.sh` ✅ (`17 passed`)

### Metric highlights (shared_memory deltas vs `memory_cycle`)
- `memory_poisoning`: poison exposure `+0.50`, avg completion `+2.00`, starvation gap `+7.53`.
- `memory_staleness_heavy`: stale miss rate `+1.00`, retries `+12`, replay anomaly `+2`, starvation gap `+39.60`.
- `deadlock_proxy`: unfinished tasks `+11`, tool_failed `+11`, replay anomaly `+6` (liveness failure signature).
- `starvation_proxy`: retries `+140`, replay anomaly `+28`, starvation gap `+48.90`, avg completion `+66.54`.

### Notes
- Proxy scenarios currently produce nearly identical stress signatures across policies due scenario-level forcing; this is intentional for deterministic liveness diagnostics but should be diversified next.
