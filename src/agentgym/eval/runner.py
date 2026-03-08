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
    num_tasks: int = 12


def _duplicate_intent_count(plans) -> int:
    # naive duplicate signal: same tool starts in near-identical time bins
    seen = {}
    dup = 0
    for p in plans:
        key = (p.tool_id, round(p.start_at, 1))
        if key in seen:
            dup += 1
        seen[key] = seen.get(key, 0) + 1
    return dup


def run_once(cfg: RunConfig) -> Dict:
    world = make_mvp_world(seed=cfg.seed)

    policy = POLICIES[cfg.policy_name]()
    for k, v in policy.world_overrides().items():
        setattr(world, k, v)

    plans = policy.plan_requests(num_tasks=cfg.num_tasks, num_agents=len(world.agents))

    sim = Simulator(world, enable_replay=False)
    for i, plan in enumerate(plans):
        sim.schedule(0.0 + i * 0.001, 0, "task_created", "system", "bench", {"task_id": plan.task_id})
        sim.schedule(plan.start_at, 0, "tool_requested", plan.agent_id, "bench", {
            "task_id": plan.task_id,
            "tool_request_id": plan.tool_request_id,
            "tool_id": plan.tool_id,
        })

    processed = sim.run(max_events=5000)
    return {
        "policy": cfg.policy_name,
        "seed": cfg.seed,
        "tasks": cfg.num_tasks,
        "events_processed": int(processed),
        "task_success_rate": world.metrics["task_success_rate"],
        "avg_completion_time": round(world.metrics["average_completion_time"], 4),
        "retry_count": int(world.metrics["retry_count"]),
        "duplicate_intent_count": _duplicate_intent_count(plans),
        "sim_end_time": round(world.current_time, 4),
    }


def run_benchmark(out_csv: str = "artifacts/benchmark_v0.csv"):
    rows: List[dict] = []
    for policy in ["independent", "planner_worker", "shared_memory"]:
        for seed in [1, 2, 3]:
            rows.append(run_once(RunConfig(policy_name=policy, seed=seed)))

    p = Path(out_csv)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    return str(p)
