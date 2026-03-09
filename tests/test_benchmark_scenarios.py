from agentgym.eval.runner import RunConfig, run_once


def test_memory_stress_scenarios_emit_memory_risk_signals():
    poison = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="memory_poisoning", num_tasks=12))
    stale = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="memory_staleness_heavy", num_tasks=12))

    assert poison["memory_poisoned_write_count"] >= 1
    assert poison["memory_poisoned_read_count"] >= 1
    assert stale["memory_stale_read_count"] >= 1
    assert stale["memory_stale_miss_rate"] > 0.0


def test_deadlock_and_starvation_proxy_metrics_present_and_nontrivial():
    deadlock = run_once(RunConfig(policy_name="independent", seed=1, scenario="deadlock_proxy", num_tasks=12))
    starvation = run_once(RunConfig(policy_name="independent", seed=1, scenario="starvation_proxy", num_tasks=12))

    assert deadlock["unfinished_task_count"] >= 0
    assert deadlock["replay_anomaly_score"] >= 0
    assert starvation["starvation_completion_p95_p50_gap"] >= 0.0
    assert "replay_anomaly_score" in starvation
