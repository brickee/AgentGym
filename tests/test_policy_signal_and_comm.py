from agentgym.eval.runner import RunConfig, run_once
from agentgym.core.simulator import Simulator
from agentgym.envs.mvp_world import make_mvp_world


def test_semantic_overlap_policy_signal_is_distinguishable():
    independent = run_once(RunConfig(policy_name="independent", seed=1, scenario="semantic_overlap"))
    planner = run_once(RunConfig(policy_name="planner_worker", seed=1, scenario="semantic_overlap"))
    shared = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="semantic_overlap"))

    assert independent["semantic_duplicate_work_count"] > planner["semantic_duplicate_work_count"]
    assert planner["semantic_duplicate_work_count"] >= shared["semantic_duplicate_work_count"]


def test_send_message_updates_event_level_comm_metrics():
    world = make_mvp_world(seed=1)
    sim = Simulator(world, enable_replay=False)

    sim.schedule(0.0, 0, "send_message", "agent_0", "m", {
        "message_id": "m1",
        "recipient_id": "agent_1",
        "content": "hello",
    })
    sim.schedule(0.1, 0, "send_message", "agent_1", "m", {
        "message_id": "m2",
        "recipient_ids": ["agent_0", "agent_2"],
        "content": "status update",
    })

    sim.run(max_events=10)

    assert world.metrics["communication_event_count"] == 2.0
    assert world.metrics["communication_cost"] > 2.0


def test_resource_contention_scenario_emits_nonzero_retry_pressure():
    contention = run_once(RunConfig(policy_name="independent", seed=1, scenario="resource_contention"))

    assert contention["protocol_retry_count"] > 0
    assert contention["retries_per_task"] > 0
    assert contention["replay_violation_count"] == 0


def test_memory_poisoning_and_staleness_scenarios_emit_robustness_metrics():
    poisoning = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="memory_poisoning"))
    staleness = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="memory_staleness_heavy"))

    assert poisoning["memory_poisoned_write_count"] > 0
    assert poisoning["memory_poisoned_read_count"] >= 0
    assert poisoning["memory_poison_exposure_rate"] >= 0.0

    assert staleness["memory_stale_read_count"] > 0
    assert staleness["memory_stale_miss_rate"] > 0.0
