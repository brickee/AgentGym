import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("artifacts/benchmark_v0.csv")
OUT_MD = Path("artifacts/benchmark_v0_summary.md")
REQUIRED_COLUMNS = {
    "schema_version",
    "scenario",
    "policy",
    "seed",
    "tasks",
    "events_processed",
    "task_success_rate",
    "avg_completion_time",
    "protocol_retry_count",
    "semantic_duplicate_work_count",
    "communication_event_count",
    "communication_cost",
    "comm_cost_per_task",
    "comm_cost_per_success",
    "comm_events_per_task",
    "retries_per_task",
    "duplicates_per_task",
    "comm_effectiveness",
    "replay_violation_count",
    "replay_duplicate_task_count",
    "replay_top_duplicate_agent_count",
    "replay_retry_scheduled_count",
    "replay_tool_failed_count",
    "replay_anomaly_score",
    "unfinished_task_count",
    "starvation_completion_p95_p50_gap",
    "retry_count",
    "duplicate_tool_calls",
    "memory_write_count",
    "memory_read_count",
    "memory_invalidate_count",
    "memory_hit_count",
    "memory_miss_count",
    "memory_stale_read_count",
    "memory_low_confidence_read_count",
    "memory_poisoned_write_count",
    "memory_poisoned_read_count",
    "memory_stale_miss_rate",
    "memory_poison_exposure_rate",
    "sim_end_time",
}


def _means(v):
    n = max(1, int(v["n"]))
    return {
        "events": v["events"] / n,
        "lat": v["lat"] / n,
        "protocol_retry": v["protocol_retry"] / n,
        "semantic_dup": v["semantic_dup"] / n,
        "comm_events": v["comm_events"] / n,
        "comm_cost": v["comm_cost"] / n,
        "mem_w": v["mem_w"] / n,
        "mem_r": v["mem_r"] / n,
        "mem_i": v["mem_i"] / n,
        "mem_hit": v["mem_hit"] / n,
        "mem_miss": v["mem_miss"] / n,
        "mem_stale": v["mem_stale"] / n,
        "mem_low_conf": v["mem_low_conf"] / n,
        "mem_poison_w": v["mem_poison_w"] / n,
        "mem_poison_r": v["mem_poison_r"] / n,
        "mem_stale_rate": v["mem_stale_rate"] / n,
        "mem_poison_exposure": v["mem_poison_exposure"] / n,
        "comm_cost_per_task": v["comm_cost_per_task"] / n,
        "comm_cost_per_success": v["comm_cost_per_success"] / n,
        "comm_events_per_task": v["comm_events_per_task"] / n,
        "retries_per_task": v["retries_per_task"] / n,
        "duplicates_per_task": v["duplicates_per_task"] / n,
        "comm_effectiveness": v["comm_effectiveness"] / n,
        "replay_viol": v["replay_viol"] / n,
        "replay_dup_task": v["replay_dup_task"] / n,
        "replay_top_dup_agent": v["replay_top_dup_agent"] / n,
        "replay_retry_sched": v["replay_retry_sched"] / n,
        "replay_tool_failed": v["replay_tool_failed"] / n,
        "replay_anomaly": v["replay_anomaly"] / n,
        "unfinished_tasks": v["unfinished_tasks"] / n,
        "starvation_gap": v["starvation_gap"] / n,
    }


def _memory_threshold(scenario: str) -> float | None:
    prefix = "memory_cycle@thr_"
    if scenario.startswith(prefix):
        return float(scenario[len(prefix):])
    return None


def _recommend_policy(mean_by_key, scenario: str, policies: list[str]):
    candidates = []
    for p in policies:
        m = mean_by_key[(scenario, p)]
        risk_penalty = 0.0
        if m["mem_stale_rate"] > 0.3:
            risk_penalty += 3.0
        if m["mem_poison_exposure"] > 0.2:
            risk_penalty += 3.0
        anomaly_penalty = 0.15 * m["replay_anomaly"] + 0.6 * m["unfinished_tasks"] + 0.12 * m["starvation_gap"]
        score = (
            m["lat"]
            + 0.08 * m["protocol_retry"]
            + 0.12 * m["semantic_dup"]
            + 0.03 * m["comm_cost"]
            + anomaly_penalty
            + risk_penalty
        )
        flags = []
        if m["comm_cost_per_task"] > 5.0:
            flags.append("high_comm_cost")
        if m["retries_per_task"] > 2.0:
            flags.append("high_retry_pressure")
        if m["mem_stale_rate"] > 0.3:
            flags.append("stale_memory_risk")
        if m["mem_poison_exposure"] > 0.2:
            flags.append("poisoning_risk")
        if m["replay_anomaly"] > 3.0:
            flags.append("replay_anomaly_risk")
        if m["unfinished_tasks"] > 0.0:
            flags.append("unfinished_task_risk")
        if m["starvation_gap"] > 6.0:
            flags.append("starvation_tail_risk")
        candidates.append((score, p, flags))

    candidates.sort(key=lambda x: x[0])
    _, best_policy, flags = candidates[0]
    return best_policy, (", ".join(flags) if flags else "none")


def main():
    agg = defaultdict(lambda: {
        "n": 0,
        "events": 0.0,
        "lat": 0.0,
        "protocol_retry": 0.0,
        "semantic_dup": 0.0,
        "comm_events": 0.0,
        "comm_cost": 0.0,
        "mem_w": 0.0,
        "mem_r": 0.0,
        "mem_i": 0.0,
        "mem_hit": 0.0,
        "mem_miss": 0.0,
        "mem_stale": 0.0,
        "mem_low_conf": 0.0,
        "mem_poison_w": 0.0,
        "mem_poison_r": 0.0,
        "mem_stale_rate": 0.0,
        "mem_poison_exposure": 0.0,
        "comm_cost_per_task": 0.0,
        "comm_cost_per_success": 0.0,
        "comm_events_per_task": 0.0,
        "retries_per_task": 0.0,
        "duplicates_per_task": 0.0,
        "comm_effectiveness": 0.0,
        "replay_viol": 0.0,
        "replay_dup_task": 0.0,
        "replay_top_dup_agent": 0.0,
        "replay_retry_sched": 0.0,
        "replay_tool_failed": 0.0,
        "replay_anomaly": 0.0,
        "unfinished_tasks": 0.0,
        "starvation_gap": 0.0,
    })

    schema_versions = set()
    with CSV_PATH.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = set(reader.fieldnames or [])
        missing = sorted(REQUIRED_COLUMNS - header)
        if missing:
            raise ValueError(f"benchmark schema missing columns: {missing}")
        for row in reader:
            schema_versions.add(str(row.get("schema_version", "")))
            k = (row["scenario"], row["policy"])
            agg[k]["n"] += 1
            agg[k]["events"] += float(row["events_processed"])
            agg[k]["lat"] += float(row["avg_completion_time"])
            agg[k]["protocol_retry"] += float(row["protocol_retry_count"])
            agg[k]["semantic_dup"] += float(row["semantic_duplicate_work_count"])
            agg[k]["comm_events"] += float(row.get("communication_event_count", 0.0))
            agg[k]["comm_cost"] += float(row.get("communication_cost", 0.0))
            agg[k]["mem_w"] += float(row.get("memory_write_count", 0.0))
            agg[k]["mem_r"] += float(row.get("memory_read_count", 0.0))
            agg[k]["mem_i"] += float(row.get("memory_invalidate_count", 0.0))
            agg[k]["mem_hit"] += float(row.get("memory_hit_count", 0.0))
            agg[k]["mem_miss"] += float(row.get("memory_miss_count", 0.0))
            agg[k]["mem_stale"] += float(row.get("memory_stale_read_count", 0.0))
            agg[k]["mem_low_conf"] += float(row.get("memory_low_confidence_read_count", 0.0))
            agg[k]["mem_poison_w"] += float(row.get("memory_poisoned_write_count", 0.0))
            agg[k]["mem_poison_r"] += float(row.get("memory_poisoned_read_count", 0.0))
            agg[k]["mem_stale_rate"] += float(row.get("memory_stale_miss_rate", 0.0))
            agg[k]["mem_poison_exposure"] += float(row.get("memory_poison_exposure_rate", 0.0))
            agg[k]["comm_cost_per_task"] += float(row.get("comm_cost_per_task", 0.0))
            agg[k]["comm_cost_per_success"] += float(row.get("comm_cost_per_success", 0.0))
            agg[k]["comm_events_per_task"] += float(row.get("comm_events_per_task", 0.0))
            agg[k]["retries_per_task"] += float(row.get("retries_per_task", 0.0))
            agg[k]["duplicates_per_task"] += float(row.get("duplicates_per_task", 0.0))
            agg[k]["comm_effectiveness"] += float(row.get("comm_effectiveness", 0.0))
            agg[k]["replay_viol"] += float(row.get("replay_violation_count", 0.0))
            agg[k]["replay_dup_task"] += float(row.get("replay_duplicate_task_count", 0.0))
            agg[k]["replay_top_dup_agent"] += float(row.get("replay_top_duplicate_agent_count", 0.0))
            agg[k]["replay_retry_sched"] += float(row.get("replay_retry_scheduled_count", 0.0))
            agg[k]["replay_tool_failed"] += float(row.get("replay_tool_failed_count", 0.0))
            agg[k]["replay_anomaly"] += float(row.get("replay_anomaly_score", 0.0))
            agg[k]["unfinished_tasks"] += float(row.get("unfinished_task_count", 0.0))
            agg[k]["starvation_gap"] += float(row.get("starvation_completion_p95_p50_gap", 0.0))

    mean_by_key = {k: _means(v) for k, v in agg.items()}
    scenarios = sorted({k[0] for k in agg})
    policies = sorted({k[1] for k in agg})

    lines = [
        "# Benchmark v0 Summary",
        "",
        f"Schema versions: {', '.join(sorted(v for v in schema_versions if v))}",
        "",
        "| scenario | policy | avg_events | avg_completion_time | avg_protocol_retries | avg_semantic_duplicates | avg_comm_events | avg_comm_cost | avg_mem_w/r/i | avg_mem_hit/miss/stale/low_conf | avg_mem_poison_w/r |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in scenarios:
        for policy in policies:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['events']:.2f} | {m['lat']:.4f} | {m['protocol_retry']:.2f} | {m['semantic_dup']:.2f} | {m['comm_events']:.2f} | {m['comm_cost']:.2f} | {m['mem_w']:.2f}/{m['mem_r']:.2f}/{m['mem_i']:.2f} | {m['mem_hit']:.2f}/{m['mem_miss']:.2f}/{m['mem_stale']:.2f}/{m['mem_low_conf']:.2f} | {m['mem_poison_w']:.2f}/{m['mem_poison_r']:.2f} |"
            )

    lines.extend([
        "",
        "## Concise recommendation by scenario",
        "",
        "| scenario | recommended_policy | tradeoff_flags |",
        "|---|---|---|",
    ])
    for scenario in scenarios:
        rec, flags = _recommend_policy(mean_by_key, scenario, policies)
        lines.append(f"| {scenario} | {rec} | {flags} |")

    lines.extend([
        "",
        "## Policy deltas vs independent (within each scenario)",
        "",
        "| scenario | policy | Δcompletion_time | Δprotocol_retries | Δsemantic_duplicates |",
        "|---|---|---:|---:|---:|",
    ])
    for scenario in scenarios:
        base = mean_by_key[(scenario, "independent")]
        for policy in [p for p in policies if p != "independent"]:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['lat'] - base['lat']:+.4f} | {m['protocol_retry'] - base['protocol_retry']:+.2f} | {m['semantic_dup'] - base['semantic_dup']:+.2f} |"
            )

    lines.extend([
        "",
        "## Scenario deltas vs baseline (within each policy)",
        "",
        "| policy | scenario | Δcompletion_time | Δprotocol_retries | Δsemantic_duplicates |",
        "|---|---|---:|---:|---:|",
    ])
    non_baseline = [s for s in scenarios if s != "baseline"]
    for policy in policies:
        base = mean_by_key[("baseline", policy)]
        for scenario in non_baseline:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {policy} | {scenario} | {m['lat'] - base['lat']:+.4f} | {m['protocol_retry'] - base['protocol_retry']:+.2f} | {m['semantic_dup'] - base['semantic_dup']:+.2f} |"
            )

    lines.extend([
        "",
        "## Memory confidence-threshold tradeoff (memory_cycle sweeps)",
        "",
        "| policy | threshold | avg_completion_time | avg_protocol_retries | avg_mem_hit | avg_mem_miss | avg_mem_low_conf |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for policy in policies:
        threshold_scenarios = sorted(
            [s for s in scenarios if _memory_threshold(s) is not None],
            key=lambda s: _memory_threshold(s),
        )
        for scenario in threshold_scenarios:
            thr = _memory_threshold(scenario)
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {policy} | {thr:.2f} | {m['lat']:.4f} | {m['protocol_retry']:.2f} | {m['mem_hit']:.2f} | {m['mem_miss']:.2f} | {m['mem_low_conf']:.2f} |"
            )

    lines.extend([
        "",
        "## Memory robustness (poisoning/staleness)",
        "",
        "| scenario | policy | stale_miss_rate | poison_exposure_rate | poisoned_writes | poisoned_reads |",
        "|---|---|---:|---:|---:|---:|",
    ])
    for scenario in [s for s in scenarios if s in {"memory_poisoning", "memory_staleness_heavy", "memory_cycle"} or _memory_threshold(s) is not None]:
        for policy in policies:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['mem_stale_rate']:.4f} | {m['mem_poison_exposure']:.4f} | {m['mem_poison_w']:.2f} | {m['mem_poison_r']:.2f} |"
            )

    lines.extend([
        "",
        "## Normalized communication metrics",
        "",
        "| scenario | policy | comm_cost/task | comm_cost/success | comm_events/task | retries/task | duplicates/task | comm_effectiveness |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for scenario in scenarios:
        for policy in policies:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['comm_cost_per_task']:.4f} | {m['comm_cost_per_success']:.4f} | {m['comm_events_per_task']:.4f} | {m['retries_per_task']:.4f} | {m['duplicates_per_task']:.4f} | {m['comm_effectiveness']:.4f} |"
            )

    lines.extend([
        "",
        "## Replay invariant + duplicate decomposition",
        "",
        "| scenario | policy | replay_violations | replay_duplicate_tasks | replay_top_duplicate_agent | replay_retry_scheduled | replay_tool_failed | replay_anomaly_score | unfinished_tasks | starvation_p95_p50_gap |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for scenario in scenarios:
        for policy in policies:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['replay_viol']:.2f} | {m['replay_dup_task']:.2f} | {m['replay_top_dup_agent']:.2f} | {m['replay_retry_sched']:.2f} | {m['replay_tool_failed']:.2f} | {m['replay_anomaly']:.2f} | {m['unfinished_tasks']:.2f} | {m['starvation_gap']:.2f} |"
            )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"SUMMARY_OK {OUT_MD}")


if __name__ == "__main__":
    main()
