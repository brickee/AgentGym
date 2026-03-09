from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world


def test_split_retry_vs_semantic_duplicate_metrics():
    world = make_mvp_world()
    sim = Simulator(world, enable_replay=False)

    sim.schedule(0.0, 0, "task_created", "system", "run", {"task_id": "t1"})
    # First request for intent (t1, search)
    sim.schedule(0.1, 0, "tool_requested", "agent_0", "run", {
        "task_id": "t1", "tool_request_id": "req_a", "tool_id": "search"
    })
    # Distinct request id for same intent should count as semantic duplicate.
    sim.schedule(0.12, 0, "tool_requested", "agent_1", "run", {
        "task_id": "t1", "tool_request_id": "req_b", "tool_id": "search"
    })

    sim.run(max_events=1000)

    assert world.metrics["semantic_duplicate_work_count"] == 1.0
    assert world.metrics["duplicate_tool_calls"] == 1.0  # compatibility alias
    assert world.metrics["protocol_retry_count"] >= 0.0
    assert world.metrics["retry_count"] == world.metrics["protocol_retry_count"]


def test_memory_event_counters_and_invalidation():
    world = make_mvp_world()
    sim = Simulator(world, enable_replay=False)

    sim.schedule(0.0, 0, "memory_write", "agent_0", "m", {"memory_id": "k1", "value": {"x": 1}})
    sim.schedule(0.1, 0, "memory_read", "agent_1", "m", {"memory_id": "k1"})
    sim.schedule(0.2, 0, "memory_invalidate", "agent_2", "m", {"memory_id": "k1"})

    sim.run(max_events=20)

    assert world.metrics["memory_write_count"] == 1.0
    assert world.metrics["memory_read_count"] == 1.0
    assert world.metrics["memory_invalidate_count"] == 1.0
    assert world.metrics["memory_hit_count"] == 1.0
    assert world.metrics["memory_miss_count"] == 0.0
    assert "k1" not in world.memory_store


def test_memory_read_drives_hit_vs_miss_tool_paths():
    world = make_mvp_world()
    sim = Simulator(world, enable_replay=False)

    sim.schedule(0.0, 0, "task_created", "system", "m", {"task_id": "t_hit"})
    sim.schedule(0.0, 0, "task_created", "system", "m", {"task_id": "t_miss"})

    sim.schedule(0.0, 0, "memory_write", "agent_0", "m", {
        "memory_id": "hint:hit",
        "value": {"preferred_tool": "search"},
        "ttl": 1.0,
        "confidence": 0.9,
        "poisoned": True,
    })
    sim.schedule(0.1, 0, "memory_read", "agent_1", "m", {
        "memory_id": "hint:hit",
        "task_id": "t_hit",
        "min_confidence": 0.6,
        "on_hit": {"tool_id": "search", "tool_request_id": "hit_req"},
        "on_miss": {"tool_id": "compute", "tool_request_id": "hit_fallback"},
    })

    sim.schedule(0.0, 0, "memory_write", "agent_0", "m", {
        "memory_id": "hint:stale",
        "value": {"preferred_tool": "search"},
        "ttl": 0.01,
        "confidence": 0.9,
    })
    sim.schedule(0.1, 0, "memory_read", "agent_2", "m", {
        "memory_id": "hint:stale",
        "task_id": "t_miss",
        "min_confidence": 0.6,
        "on_hit": {"tool_id": "search", "tool_request_id": "stale_req"},
        "on_miss": {"tool_id": "compute", "tool_request_id": "miss_req"},
    })

    sim.run(max_events=200)

    assert world.tasks["t_hit"]["status"] == "done"
    assert world.tasks["t_miss"]["status"] == "done"
    assert world.metrics["memory_hit_count"] == 1.0
    assert world.metrics["memory_miss_count"] == 1.0
    assert world.metrics["memory_stale_read_count"] == 1.0
    assert world.metrics["memory_poisoned_write_count"] == 1.0
    assert world.metrics["memory_poisoned_read_count"] == 1.0
