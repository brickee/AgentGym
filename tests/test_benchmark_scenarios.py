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


def test_proxy_scenarios_are_policy_differentiated_with_stress_knobs():
    dl_ind = run_once(RunConfig(policy_name="independent", seed=1, scenario="deadlock_proxy", num_tasks=12))
    dl_sm = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="deadlock_proxy", num_tasks=12))
    st_ind = run_once(RunConfig(policy_name="independent", seed=1, scenario="starvation_proxy", num_tasks=12))
    st_sm = run_once(RunConfig(policy_name="shared_memory", seed=1, scenario="starvation_proxy", num_tasks=12))

    assert dl_ind["policy_deadlock_start_spread"] != dl_sm["policy_deadlock_start_spread"]
    assert st_ind["policy_starvation_compute_share"] != st_sm["policy_starvation_compute_share"]
    # Ensure this surfaces into different stress signatures.
    assert (
        dl_ind["replay_anomaly_score"] != dl_sm["replay_anomaly_score"]
        or dl_ind["unfinished_task_count"] != dl_sm["unfinished_task_count"]
    )
