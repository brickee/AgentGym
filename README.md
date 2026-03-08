# AgentGym

A discrete-event simulator for multi-agent coordination under shared resource contention.

## Goal
AgentGym studies how multi-agent systems coordinate when tools are rate-limited, resources are scarce, memory is shared, and events are asynchronous.

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

## Status
Bootstrapping the MVP architecture.
