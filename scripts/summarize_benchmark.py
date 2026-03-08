import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("artifacts/benchmark_v0.csv")
OUT_MD = Path("artifacts/benchmark_v0_summary.md")


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
    }


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
    })

    with CSV_PATH.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
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

    mean_by_key = {k: _means(v) for k, v in agg.items()}
    scenarios = sorted({k[0] for k in agg})
    policies = sorted({k[1] for k in agg})

    lines = [
        "# Benchmark v0 Summary",
        "",
        "| scenario | policy | avg_events | avg_completion_time | avg_protocol_retries | avg_semantic_duplicates | avg_comm_events | avg_comm_cost | avg_mem_w/r/i | avg_mem_hit/miss/stale |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in scenarios:
        for policy in policies:
            m = mean_by_key[(scenario, policy)]
            lines.append(
                f"| {scenario} | {policy} | {m['events']:.2f} | {m['lat']:.4f} | {m['protocol_retry']:.2f} | {m['semantic_dup']:.2f} | {m['comm_events']:.2f} | {m['comm_cost']:.2f} | {m['mem_w']:.2f}/{m['mem_r']:.2f}/{m['mem_i']:.2f} | {m['mem_hit']:.2f}/{m['mem_miss']:.2f}/{m['mem_stale']:.2f} |"
            )

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

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"SUMMARY_OK {OUT_MD}")


if __name__ == "__main__":
    main()
