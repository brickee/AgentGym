from agentgym.core.world import WorldState


def make_mvp_world(seed: int = 42) -> WorldState:
    world = WorldState(seed=seed, backpressure_policy="retry")
    for i in range(5):
        world.agents[f"agent_{i}"] = {"role": "worker", "busy_until": 0.0}
    world.tools = {
        "search": {"latency": 2.0, "capacity": 5, "requirements": ["api_search"], "rate_limit_per_sec": 2.0},
        "compute": {"latency": 10.0, "capacity": 2, "requirements": ["compute_slot"], "rate_limit_per_sec": 1.0},
        "database": {"latency": 3.0, "capacity": 3, "requirements": ["db_lock"], "rate_limit_per_sec": 2.0},
    }
    world.resources = {
        "api_search": 2,
        "compute_slot": 1,
        "db_lock": 1,
    }
    return world
