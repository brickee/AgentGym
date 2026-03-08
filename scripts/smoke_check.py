from pathlib import Path

from agentgym.core.events import Event
from agentgym.core.simulator import Simulator
from agentgym.core.allocator import ResourceAllocator
from agentgym.core.replay import load_jsonl
from agentgym.envs.mvp_world import make_mvp_world


def main():
    e1 = Event(sim_time=1.0, priority=1, seq_id=2, event_type="x", actor_id="a", correlation_id="c")
    e2 = Event(sim_time=1.0, priority=0, seq_id=3, event_type="x", actor_id="a", correlation_id="c")
    e3 = Event(sim_time=0.5, priority=9, seq_id=1, event_type="x", actor_id="a", correlation_id="c")
    assert sorted([e1, e2, e3]) == [e3, e2, e1], "event ordering failed"

    allocator = ResourceAllocator(
        resource_config={"api_search": 1, "compute_slot": 1, "db_lock": 1},
        tool_requirements={"search": ["api_search"], "compute": ["compute_slot"]},
    )
    ok, resources, tag = allocator.allocate("search", now=0.0)
    assert ok and resources == ["api_search"] and tag == "allocated", "allocator failed on first allocation"
    ok2, _, tag2 = allocator.allocate("search", now=0.0)
    assert (not ok2) and tag2.startswith("wait:"), "allocator should enforce capacity"
    allocator.release(resources)

    world = make_mvp_world()
    sim = Simulator(world, enable_replay=True)
    sim.schedule(0.0, 0, "task_created", "system", "run1", {"task_id": "t1"})
    sim.schedule(0.1, 0, "tool_requested", "agent_0", "run1", {
        "task_id": "t1", "tool_request_id": "tr1", "tool_id": "search"
    })
    processed = sim.run()
    assert processed >= 4, "simulator did not process expected lifecycle events"
    assert world.tasks["t1"]["status"] == "done", "task completion failed"

    out = Path("artifacts/replay_run1.jsonl")
    sim.recorder.dump_jsonl(str(out))
    replay = load_jsonl(str(out))
    assert any(e["event_type"] == "tool_started" for e in replay), "missing tool_started in replay"
    assert any(e["event_type"] == "tool_finished" for e in replay), "missing tool_finished in replay"

    print("SMOKE_CHECK_OK")


if __name__ == "__main__":
    main()
