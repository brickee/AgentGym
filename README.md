# AgentGym

A discrete-event simulator for multi-agent organization, coordination, and adaptation under shared resource contention.

## Goal
AgentGym studies not only resource contention, but also multi-agent **organization design**: team structures, delegation patterns, communication protocols, and memory-sharing strategies under realistic async constraints.

It targets three axes together:
- **Competition**: quota/slot/lock contention
- **Coordination**: task decomposition, messaging, and handoffs
- **Organization**: hierarchy vs decentralized teams, policy governance, and adaptation

## MVP Scope
- 5 agents, 20 tasks, 3 tools (`search`, `compute`, `database`)
- Discrete Event Simulation (DES)
- Shared resource contention and queueing
- Baselines: independent, planner-worker, shared-memory
- Core metrics: success rate, completion time, resource utilization, protocol retries, semantic duplicate work, communication cost

## Project Management
- `PLAN.md` — roadmap and milestones
- `PROGRESS.md` — daily progress log
- `NEXT_TODO.md` — next actionable tasks

## Quickstart
```bash
PYTHONPATH=src python3 scripts/smoke_check.py
PYTHONPATH=src python3 scripts/run_benchmark.py
python3 scripts/summarize_benchmark.py
```

## Dev bootstrap
```bash
python3 -m pip install -e '.[dev]'  # installs pytest
make ci                             # smoke + unit checks (pytest optional)
```

## Benchmark notes
- Scenarios: `baseline`, `semantic_overlap`, `memory_cycle`, plus confidence sweeps `memory_cycle@thr_0.50|0.70|0.90`
- Semantic duplicate-work is measured as distinct request IDs for the same `(task_id, tool_id)` intent.
- Memory-cycle now couples memory to runtime outcomes using hit/miss tool branching (`on_hit`/`on_miss`) with TTL + confidence semantics.
- Communication metrics are event-level runtime counters:
  - `communication_event_count`
  - `communication_cost`
- Summary report now includes policy deltas (vs independent), scenario deltas (vs baseline), and a memory confidence-threshold tradeoff table.

## Status
M1/M2 simulator + baseline evaluation active with scenario-aware duplicate-work and communication-cost metrics.
