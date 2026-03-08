import csv
from dataclasses import dataclass
from pathlib import Path
from typing import List

from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world


@dataclass
class RunConfig:
    policy_name: str
    seed: int


def run_once(cfg: RunConfig):
    world = make_mvp_world(seed=cfg.seed)
    # lightweight policy effects at environment level (placeholder)
    if cfg.policy_name == "independent":
        world.backpressure_policy = "retry"
    elif cfg.policy_name == "planner_worker":
        world.backpressure_policy = "wait"
    elif cfg.policy_name == "shared_memory":
        world.backpressure_policy = "retry"
        world.retry_mode = "exp"

    sim = Simulator(world, enable_replay=False)
    for i in range(5):
        task_id = f"t{i}"
        req_id = f"tr{i}"
        sim.schedule(0.0 + i * 0.01, 0, "task_created", "system", "bench", {"task_id": task_id})
        sim.schedule(0.1 + i * 0.01, 0, "tool_requested", f"agent_{i%5}", "bench", {
            "task_id": task_id,
            "tool_request_id": req_id,
            "tool_id": "search" if i % 2 == 0 else "compute",
        })

    processed = sim.run(max_events=2000)
    return {
        "policy": cfg.policy_name,
        "seed": cfg.seed,
        "events_processed": int(processed),
        "task_success_rate": world.metrics["task_success_rate"],
        "retry_count": int(world.metrics["retry_count"]),
        "sim_end_time": world.current_time,
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
