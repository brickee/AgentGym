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
- Core metrics: success rate, completion time, resource utilization, duplicate work, communication cost

## Project Management
- `PLAN.md` — roadmap and milestones
- `PROGRESS.md` — daily progress log
- `NEXT_TODO.md` — next actionable tasks

## Quickstart
```bash
PYTHONPATH=src python3 scripts/smoke_check.py
PYTHONPATH=src python3 scripts/run_benchmark.py
```

## Status
Bootstrapping the MVP architecture.
