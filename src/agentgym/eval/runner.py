import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from agentgym.core.simulator import Simulator
from agentgym.core.replay import replay_duplicate_decomposition, replay_invariant_precheck, replay_event_distribution
from agentgym.envs.mvp_world import make_mvp_world
from agentgym.eval.metrics import compute_normalized_metrics
from agentgym.policies.independent import IndependentPolicy
from agentgym.policies.planner_worker import PlannerWorkerPolicy
from agentgym.policies.shared_memory import SharedMemoryPolicy


POLICIES = {
    "independent": IndependentPolicy,
    "planner_worker": PlannerWorkerPolicy,
    "shared_memory": SharedMemoryPolicy,
}

MEMORY_CONFIDENCE_SWEEP = [0.5, 0.7, 0.9]

BENCHMARK_SCHEMA_VERSION = "1.5"
BENCHMARK_COLUMNS = [
    "schema_version",
    "scenario",
    "policy",
    "seed",
    "tasks",
    "events_processed",
    "task_success_rate",
    "avg_completion_time",
    "protocol_retry_count",
    "semantic_duplicate_work_count",
    "communication_event_count",
    "communication_cost",
    "comm_cost_per_task",
    "comm_cost_per_success",
    "comm_events_per_task",
    "retries_per_task",
    "duplicates_per_task",
    "comm_effectiveness",
    "replay_violation_count",
    "replay_duplicate_task_count",
    "replay_top_duplicate_agent_count",
    "replay_retry_scheduled_count",
    "replay_tool_failed_count",
    "replay_anomaly_score",
    "unfinished_task_count",
    "starvation_completion_p95_p50_gap",
    "policy_deadlock_start_spread",
    "policy_starvation_compute_share",
    "retry_count",
    "duplicate_tool_calls",
    "memory_write_count",
    "memory_read_count",
    "memory_invalidate_count",
    "memory_hit_count",
    "memory_miss_count",
    "memory_stale_read_count",
    "memory_low_confidence_read_count",
    "memory_poisoned_write_count",
    "memory_poisoned_read_count",
    "memory_stale_miss_rate",
    "memory_poison_exposure_rate",
    "sim_end_time",
]


@dataclass
class RunConfig:
    policy_name: str
    seed: int
    scenario: str = "baseline"
    num_tasks: int = 12


def _memory_threshold_for_scenario(scenario: str) -> float | None:
    prefix = "memory_cycle@thr_"
    if scenario.startswith(prefix):
        return float(scenario[len(prefix):])
    if scenario == "memory_cycle":
        return None
    return None


def _policy_stress_knobs(policy_name: str, scenario: str) -> dict:
    defaults = {
        "deadlock_start_spread": 0.0,
        "starvation_compute_share": 1.0,
        "deadlock_delay": 1.0,
        "starvation_retry_max_delay": 6.0,
    }
    profiles = {
        "independent": {
            "deadlock_start_spread": 0.0,
            "starvation_compute_share": 1.0,
            "deadlock_delay": 1.2,
            "starvation_retry_max_delay": 6.0,
        },
        "planner_worker": {
            "deadlock_start_spread": 0.003,
            "starvation_compute_share": 0.85,
            "deadlock_delay": 0.8,
            "starvation_retry_max_delay": 4.5,
        },
        "shared_memory": {
            "deadlock_start_spread": 0.006,
            "starvation_compute_share": 0.65,
            "deadlock_delay": 0.6,
            "starvation_retry_max_delay": 3.5,
        },
    }
    out = dict(defaults)
    out.update(profiles.get(policy_name, {}))
    return out


def _scenario_memory_workload(policy, scenario: str, cfg: RunConfig, num_agents: int) -> dict:
    threshold = _memory_threshold_for_scenario(scenario)
    base = policy.plan_memory_cycle(
        num_tasks=cfg.num_tasks,
        num_agents=num_agents,
        min_confidence=threshold,
    )

    if scenario in {"memory_cycle", "memory_poisoning", "memory_staleness_heavy"} or threshold is not None:
        pass
    else:
        return {"writes": [], "reads": [], "invalidations": []}

    if scenario == "memory_poisoning":
        poisoned_writes = []
        poisoned_reads = []
        for i, w in enumerate(base.get("writes", [])):
            w2 = dict(w)
            if i % 3 == 0:
                # Realistic poisoning: minority of writes, high confidence, moderate TTL.
                w2["poisoned"] = True
                w2["confidence"] = 0.88
                w2["ttl"] = max(2.0, float(w2.get("ttl", 1.0)))
                w2["value"] = {"preferred_tool": "compute", "tag": "poisoned"}
            poisoned_writes.append(w2)

        for i, r in enumerate(base.get("reads", [])):
            r2 = dict(r)
            if i % 3 == 0:
                # Poisoned hits tilt toward expensive path; misses recover to safer path.
                r2["on_hit"] = {"tool_id": "compute", "tool_request_id": f"poison_hit_{cfg.policy_name}_{i}"}
                r2["on_miss"] = {"tool_id": "search", "tool_request_id": f"poison_miss_{cfg.policy_name}_{i}"}
                r2["min_confidence"] = 0.82
            poisoned_reads.append(r2)

        base["writes"] = poisoned_writes
        base["reads"] = poisoned_reads

    if scenario == "memory_staleness_heavy":
        stale_writes = []
        stale_reads = []
        for i, w in enumerate(base.get("writes", [])):
            w2 = dict(w)
            # Keep some chance of freshness while still stressing stale-path handling.
            w2["ttl"] = 0.045 + (i * 0.008)
            stale_writes.append(w2)

        for i, r in enumerate(base.get("reads", [])):
            r2 = dict(r)
            r2["at"] = max(float(r2.get("at", 0.1)), 0.11 + i * 0.03)
            r2["on_miss"] = {"tool_id": "compute", "tool_request_id": f"stale_miss_{cfg.policy_name}_{i}"}
            stale_reads.append(r2)

        base["writes"] = stale_writes
        base["reads"] = stale_reads

    return base


def _schedule_memory_workload(sim: Simulator, scenario: str, policy, cfg: RunConfig):
    workload = _scenario_memory_workload(policy, scenario, cfg, len(sim.world.agents))
    coupled_tasks = set()

    for w in workload.get("writes", []):
        sim.schedule(w["at"], 0, "memory_write", w["actor_id"], "bench_memory", {
            "memory_id": w["memory_id"],
            "value": w.get("value", {}),
            "ttl": w.get("ttl"),
            "confidence": w.get("confidence", 1.0),
            "poisoned": w.get("poisoned", False),
        })

    for r in workload.get("reads", []):
        coupled_tasks.add(r["task_id"])
        sim.schedule(0.0, 0, "task_created", "system", "bench_memory", {"task_id": r["task_id"]})
        sim.schedule(r["at"], 0, "memory_read", r["actor_id"], "bench_memory", {
            "memory_id": r["memory_id"],
            "task_id": r["task_id"],
            "on_hit": r["on_hit"],
            "on_miss": r["on_miss"],
            "min_confidence": r.get("min_confidence", 0.5),
        })

    for inv in workload.get("invalidations", []):
        sim.schedule(inv["at"], 0, "memory_invalidate", inv["actor_id"], "bench_memory", {
            "memory_id": inv["memory_id"],
        })

    return coupled_tasks


def _schedule_message_workload(sim: Simulator, policy, cfg: RunConfig, num_agents: int):
    mode = None
    if cfg.scenario == "comm_stress_broadcast":
        mode = "broadcast"
    elif cfg.scenario == "comm_stress_p2p":
        mode = "p2p"

    for idx, msg in enumerate(policy.plan_messages(num_tasks=cfg.num_tasks, num_agents=num_agents)):
        payload = {
            "message_id": msg.message_id,
            "recipient_id": msg.recipient_id,
            "content": msg.content,
        }
        sent_at = msg.sent_at

        if mode == "broadcast":
            payload["recipient_id"] = None
            payload["recipient_ids"] = [f"agent_{i}" for i in range(num_agents) if f"agent_{i}" != msg.sender_id]
            payload["message_id"] = f"{msg.message_id}_b"
            sent_at = msg.sent_at + (idx * 0.0001)
        elif mode == "p2p":
            payload["message_id"] = f"{msg.message_id}_p"
            sent_at = msg.sent_at + (idx * 0.0001)

        sim.schedule(sent_at, 0, "send_message", msg.sender_id, "bench_msg", payload)


def _apply_scenario_world_overrides(world, scenario: str, knobs: dict):
    if scenario == "resource_contention":
        world.resources = {
            "api_search": 1,
            "compute_slot": 1,
            "db_lock": 1,
        }
        world.retry_base_delay = 0.5
        world.retry_mode = "exp"

    if scenario == "deadlock_proxy":
        # Proxy for circular wait: a near-serialized world with drop-on-pressure.
        world.resources = {
            "api_search": 1,
            "compute_slot": 1,
            "db_lock": 1,
        }
        world.backpressure_policy = "drop"
        world.retry_mode = "fixed"
        world.retry_base_delay = float(knobs.get("deadlock_delay", 1.0))

    if scenario == "starvation_proxy":
        # Proxy for starvation: one slow constrained lane + aggressive retries.
        world.resources = {
            "api_search": 1,
            "compute_slot": 1,
            "db_lock": 1,
        }
        world.backpressure_policy = "retry"
        world.retry_mode = "exp"
        world.retry_base_delay = 0.2
        world.retry_max_delay = float(knobs.get("starvation_retry_max_delay", 6.0))


def _apply_scenario_plan_overrides(cfg: RunConfig, plans, knobs: dict):
    if cfg.scenario == "deadlock_proxy":
        # Deterministic policy-specific contention shape to preserve diagnostics while differentiating policy behavior.
        spread = float(knobs.get("deadlock_start_spread", 0.0))
        out = []
        for i, p in enumerate(plans):
            if cfg.policy_name == "independent":
                tool = "database"
            elif cfg.policy_name == "planner_worker":
                tool = "database" if i % 2 == 0 else "search"
            else:
                tool = "database" if i % 3 == 0 else "search"
            out.append(type(p)(
                task_id=p.task_id,
                tool_request_id=f"dl_{cfg.policy_name}_{i}",
                agent_id=p.agent_id,
                tool_id=tool,
                start_at=0.1 + (i * spread),
            ))
        return out

    if cfg.scenario == "starvation_proxy":
        # Deterministic policy-specific burst profiles under constrained compute.
        compute_share = float(knobs.get("starvation_compute_share", 1.0))
        spread = max(0.0001, float(knobs.get("deadlock_start_spread", 0.0)) * 1.5)
        out = []
        for i, p in enumerate(plans):
            quota = int(round((i + 1) * compute_share))
            use_compute = (quota > int(round(i * compute_share)))
            if cfg.policy_name == "independent":
                start_at = 0.05 if i == 0 else 0.051
            else:
                start_at = 0.05 + (i * spread)
            out.append(type(p)(
                task_id=p.task_id,
                tool_request_id=f"st_{cfg.policy_name}_{i}",
                agent_id=p.agent_id,
                tool_id="compute" if use_compute else "search",
                start_at=start_at,
            ))
        return out

    return plans


def run_once(cfg: RunConfig) -> Dict:
    world = make_mvp_world(seed=cfg.seed)

    policy = POLICIES[cfg.policy_name]()
    for k, v in policy.world_overrides().items():
        setattr(world, k, v)
    stress_knobs = _policy_stress_knobs(cfg.policy_name, cfg.scenario)
    _apply_scenario_world_overrides(world, cfg.scenario, stress_knobs)

    plans = policy.plan_requests(num_tasks=cfg.num_tasks, num_agents=len(world.agents))
    if cfg.scenario == "semantic_overlap":
        plans.extend(policy.plan_semantic_duplicates(num_tasks=cfg.num_tasks, num_agents=len(world.agents)))
    plans = _apply_scenario_plan_overrides(cfg, plans, stress_knobs)

    sim = Simulator(world, enable_replay=True)
    coupled_tasks = _schedule_memory_workload(sim, cfg.scenario, policy, cfg)
    _schedule_message_workload(sim, policy, cfg, len(world.agents))

    if coupled_tasks:
        plans = [p for p in plans if p.task_id not in coupled_tasks]

    created_tasks = set()
    for plan in plans:
        if plan.task_id not in created_tasks:
            created_tasks.add(plan.task_id)
            sim.schedule(0.0, 0, "task_created", "system", "bench", {"task_id": plan.task_id})
        sim.schedule(plan.start_at, 0, "tool_requested", plan.agent_id, "bench", {
            "task_id": plan.task_id,
            "tool_request_id": plan.tool_request_id,
            "tool_id": plan.tool_id,
        })

    processed = sim.run(max_events=5000)
    events = sim.recorder.events if sim.recorder else []
    replay_violations = replay_invariant_precheck(events)
    replay_dups = replay_duplicate_decomposition(events)
    replay_dist = replay_event_distribution(events)
    top_dup_agent = max(replay_dups["by_agent"].values()) if replay_dups["by_agent"] else 0
    replay_retry_scheduled_count = int(replay_dist.get("retry_scheduled", 0))
    replay_tool_failed_count = int(replay_dist.get("tool_failed", 0))
    norm = compute_normalized_metrics(world.metrics, cfg.num_tasks)

    memory_reads = max(1, int(world.metrics["memory_read_count"]))
    memory_hits = max(1, int(world.metrics["memory_hit_count"]))

    completions = sorted([
        float(t.get("completed_at", t.get("created_at", 0.0))) - float(t.get("created_at", 0.0))
        for t in world.tasks.values()
        if t.get("status") == "done"
    ])
    if completions:
        p50_idx = int(0.5 * (len(completions) - 1))
        p95_idx = int(0.95 * (len(completions) - 1))
        starvation_gap = round(completions[p95_idx] - completions[p50_idx], 4)
    else:
        starvation_gap = 0.0

    unfinished_task_count = int(sum(1 for t in world.tasks.values() if t.get("status") != "done"))
    replay_anomaly_score = int(
        len(replay_violations)
        + sum(replay_dups["by_task"].values())
        + top_dup_agent
        + (replay_retry_scheduled_count // 5)
        + replay_tool_failed_count
    )

    return {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "scenario": cfg.scenario,
        "policy": cfg.policy_name,
        "seed": cfg.seed,
        "tasks": cfg.num_tasks,
        "events_processed": int(processed),
        "task_success_rate": world.metrics["task_success_rate"],
        "avg_completion_time": round(world.metrics["average_completion_time"], 4),
        "protocol_retry_count": int(world.metrics["protocol_retry_count"]),
        "semantic_duplicate_work_count": int(world.metrics["semantic_duplicate_work_count"]),
        "communication_event_count": int(world.metrics["communication_event_count"]),
        "communication_cost": round(world.metrics["communication_cost"], 3),
        "comm_cost_per_task": norm["comm_cost_per_task"],
        "comm_cost_per_success": norm["comm_cost_per_success"],
        "comm_events_per_task": norm["comm_events_per_task"],
        "retries_per_task": norm["retries_per_task"],
        "duplicates_per_task": norm["duplicates_per_task"],
        "comm_effectiveness": norm["comm_effectiveness"],
        "replay_violation_count": int(len(replay_violations)),
        "replay_duplicate_task_count": int(sum(replay_dups["by_task"].values())),
        "replay_top_duplicate_agent_count": int(top_dup_agent),
        "replay_retry_scheduled_count": int(replay_retry_scheduled_count),
        "replay_tool_failed_count": int(replay_tool_failed_count),
        "replay_anomaly_score": int(replay_anomaly_score),
        "unfinished_task_count": int(unfinished_task_count),
        "starvation_completion_p95_p50_gap": float(starvation_gap),
        "policy_deadlock_start_spread": float(stress_knobs["deadlock_start_spread"]),
        "policy_starvation_compute_share": float(stress_knobs["starvation_compute_share"]),
        "retry_count": int(world.metrics["retry_count"]),
        "duplicate_tool_calls": int(world.metrics["duplicate_tool_calls"]),
        "memory_write_count": int(world.metrics["memory_write_count"]),
        "memory_read_count": int(world.metrics["memory_read_count"]),
        "memory_invalidate_count": int(world.metrics["memory_invalidate_count"]),
        "memory_hit_count": int(world.metrics["memory_hit_count"]),
        "memory_miss_count": int(world.metrics["memory_miss_count"]),
        "memory_stale_read_count": int(world.metrics["memory_stale_read_count"]),
        "memory_low_confidence_read_count": int(world.metrics["memory_low_confidence_read_count"]),
        "memory_poisoned_write_count": int(world.metrics["memory_poisoned_write_count"]),
        "memory_poisoned_read_count": int(world.metrics["memory_poisoned_read_count"]),
        "memory_stale_miss_rate": round(float(world.metrics["memory_stale_read_count"]) / memory_reads, 4),
        "memory_poison_exposure_rate": round(float(world.metrics["memory_poisoned_read_count"]) / memory_hits, 4),
        "sim_end_time": round(world.current_time, 4),
    }


def run_benchmark(out_csv: str = "artifacts/benchmark_v0.csv"):
    rows: List[dict] = []
    scenarios = [
        "baseline",
        "semantic_overlap",
        "memory_cycle",
        "memory_poisoning",
        "memory_staleness_heavy",
        "comm_stress_p2p",
        "comm_stress_broadcast",
        "resource_contention",
        "deadlock_proxy",
        "starvation_proxy",
    ] + [f"memory_cycle@thr_{thr:.2f}" for thr in MEMORY_CONFIDENCE_SWEEP]
    for scenario in scenarios:
        for policy in ["independent", "planner_worker", "shared_memory"]:
            for seed in [1, 2, 3]:
                rows.append(run_once(RunConfig(policy_name=policy, seed=seed, scenario=scenario)))

    p = Path(out_csv)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=BENCHMARK_COLUMNS)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k) for k in BENCHMARK_COLUMNS})
    return str(p)
