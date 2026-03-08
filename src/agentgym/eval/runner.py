import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world
from agentgym.policies.independent import IndependentPolicy
from agentgym.policies.planner_worker import PlannerWorkerPolicy
from agentgym.policies.shared_memory import SharedMemoryPolicy


POLICIES = {
    "independent": IndependentPolicy,
    "planner_worker": PlannerWorkerPolicy,
    "shared_memory": SharedMemoryPolicy,
}


@dataclass
class RunConfig:
    policy_name: str
    seed: int
    scenario: str = "baseline"
    num_tasks: int = 12


def _schedule_memory_workload(sim: Simulator, scenario: str, policy, cfg: RunConfig):
    if scenario != "memory_cycle":
        return set()

    workload = policy.plan_memory_cycle(num_tasks=cfg.num_tasks, num_agents=len(sim.world.agents))
    coupled_tasks = set()

    for w in workload.get("writes", []):
        sim.schedule(w["at"], 0, "memory_write", w["actor_id"], "bench_memory", {
            "memory_id": w["memory_id"],
            "value": w.get("value", {}),
            "ttl": w.get("ttl"),
            "confidence": w.get("confidence", 1.0),
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
    for msg in policy.plan_messages(num_tasks=cfg.num_tasks, num_agents=num_agents):
        sim.schedule(msg.sent_at, 0, "send_message", msg.sender_id, "bench_msg", {
            "message_id": msg.message_id,
            "recipient_id": msg.recipient_id,
            "content": msg.content,
        })


def run_once(cfg: RunConfig) -> Dict:
    world = make_mvp_world(seed=cfg.seed)

    policy = POLICIES[cfg.policy_name]()
    for k, v in policy.world_overrides().items():
        setattr(world, k, v)

    plans = policy.plan_requests(num_tasks=cfg.num_tasks, num_agents=len(world.agents))
    if cfg.scenario == "semantic_overlap":
        plans.extend(policy.plan_semantic_duplicates(num_tasks=cfg.num_tasks, num_agents=len(world.agents)))

    sim = Simulator(world, enable_replay=False)
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
    return {
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
        "retry_count": int(world.metrics["retry_count"]),
        "duplicate_tool_calls": int(world.metrics["duplicate_tool_calls"]),
        "memory_write_count": int(world.metrics["memory_write_count"]),
        "memory_read_count": int(world.metrics["memory_read_count"]),
        "memory_invalidate_count": int(world.metrics["memory_invalidate_count"]),
        "memory_hit_count": int(world.metrics["memory_hit_count"]),
        "memory_miss_count": int(world.metrics["memory_miss_count"]),
        "memory_stale_read_count": int(world.metrics["memory_stale_read_count"]),
        "memory_low_confidence_read_count": int(world.metrics["memory_low_confidence_read_count"]),
        "sim_end_time": round(world.current_time, 4),
    }


def run_benchmark(out_csv: str = "artifacts/benchmark_v0.csv"):
    rows: List[dict] = []
    for scenario in ["baseline", "semantic_overlap", "memory_cycle"]:
        for policy in ["independent", "planner_worker", "shared_memory"]:
            for seed in [1, 2, 3]:
                rows.append(run_once(RunConfig(policy_name=policy, seed=seed, scenario=scenario)))

    p = Path(out_csv)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return str(p)
