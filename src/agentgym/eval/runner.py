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


def _schedule_memory_workload(sim: Simulator, scenario: str):
    if scenario != "memory_cycle":
        return

    # Deterministic memory workload to cover write/read/invalidate lifecycle.
    sim.schedule(0.02, 0, "memory_write", "agent_0", "bench_memory", {
        "memory_id": "shared:plan:t0",
        "value": {"owner": "agent_0", "hint": "use-search-first"},
    })
    sim.schedule(0.03, 0, "memory_read", "agent_1", "bench_memory", {
        "memory_id": "shared:plan:t0",
    })
    sim.schedule(0.04, 0, "memory_invalidate", "agent_2", "bench_memory", {
        "memory_id": "shared:plan:t0",
    })


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
    _schedule_memory_workload(sim, cfg.scenario)
    _schedule_message_workload(sim, policy, cfg, len(world.agents))

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
