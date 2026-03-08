from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world


def test_simulator_smoke_run():
    world = make_mvp_world()
    sim = Simulator(world)
    sim.schedule(0.0, 0, "task_created", "system", "run1", {"task_id": "t1"})
    sim.schedule(1.0, 0, "task_completed", "agent_0", "run1", {"task_id": "t1"})
    processed = sim.run()
    assert processed == 2
    assert world.tasks["t1"]["status"] == "done"
