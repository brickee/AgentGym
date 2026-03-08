from agentgym.core.world import WorldState


def make_mvp_world(seed: int = 42) -> WorldState:
    world = WorldState(seed=seed)
    for i in range(5):
        world.agents[f"agent_{i}"] = {"role": "worker", "busy_until": 0.0}
    world.tools = {
        "search": {"latency": 2.0, "capacity": 5},
        "compute": {"latency": 10.0, "capacity": 2},
        "database": {"latency": 3.0, "capacity": 3},
    }
    return world
