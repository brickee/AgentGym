# Multi-Agent Coordination Simulator — PLAN

## North Star
Build a discrete-event multi-agent **organization simulator** for shared tools/resources, where contention, collaboration, and team governance are first-class, with clear MVP metrics and training hooks (RL/GEPA/MARTI).

## Milestones

### M0 — Project Foundation (Day 0-1)
- [ ] Repo scaffolding (src/tests/config/docs)
- [ ] Event schema v0
- [ ] World state schema v0
- [ ] Metric schema v0
- [ ] Deterministic seed + replay policy

### M1 — MVP Simulator Core (Day 2-4)
- [ ] DES event queue + clock progression
- [ ] Tool/resource allocator (latency, queue, rate limit)
- [ ] Basic world (5 agents, 20 tasks, 3 tools)
- [ ] Action API: request_tool/wait/send_message/complete_task

### M2 — Baseline Agents + Eval (Day 4-6)
- [ ] Independent baseline
- [ ] Planner-worker baseline
- [ ] Shared-memory baseline (minimal)
- [ ] Metrics pipeline + experiment runner

### M3 — Research Extensions (Week 2+)
- [ ] Shared tool ecosystem (dependency/failure/cost)
- [ ] Memory as first-class resource (private/shared/team)
- [ ] Organization layer (hierarchy/market/decentralized team policies)
- [ ] RL/GEPA/MARTI interfaces
- [ ] Benchmark packaging

## Current Phase Focus (2026-03-09)
- M2 hardening pass in progress: replay analytics decomposition, communication metric normalization, and stricter invariant checks.
- Benchmark schema moved to v1.1 to include normalized communication columns.

## Weekly Operating Rules
1. Each day must end with PROGRESS + NEXT_TODO updates.
2. No feature merge without metric impact or test coverage.
3. Prioritize deterministic reproducibility over extra complexity.
