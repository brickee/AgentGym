from agentgym.core.events import Event
from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world


def main():
    e1 = Event(sim_time=1.0, priority=1, seq_id=2, event_type="x", actor_id="a", correlation_id="c")
    e2 = Event(sim_time=1.0, priority=0, seq_id=3, event_type="x", actor_id="a", correlation_id="c")
    e3 = Event(sim_time=0.5, priority=9, seq_id=1, event_type="x", actor_id="a", correlation_id="c")
    assert sorted([e1, e2, e3]) == [e3, e2, e1], "event ordering failed"

    world = make_mvp_world()
    sim = Simulator(world)
    sim.schedule(0.0, 0, "task_created", "system", "run1", {"task_id": "t1"})
    sim.schedule(1.0, 0, "task_completed", "agent_0", "run1", {"task_id": "t1"})
    processed = sim.run()
    assert processed == 2, "processed count mismatch"
    assert world.tasks["t1"]["status"] == "done", "task completion failed"
    print("SMOKE_CHECK_OK")


if __name__ == "__main__":
    main()
