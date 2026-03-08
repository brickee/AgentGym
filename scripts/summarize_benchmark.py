import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("artifacts/benchmark_v0.csv")
OUT_MD = Path("artifacts/benchmark_v0_summary.md")


def main():
    agg = defaultdict(lambda: {
        "n": 0,
        "events": 0.0,
        "lat": 0.0,
        "protocol_retry": 0.0,
        "semantic_dup": 0.0,
        "mem_w": 0.0,
        "mem_r": 0.0,
        "mem_i": 0.0,
    })

    with CSV_PATH.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            k = (row["scenario"], row["policy"])
            agg[k]["n"] += 1
            agg[k]["events"] += float(row["events_processed"])
            agg[k]["lat"] += float(row["avg_completion_time"])
            agg[k]["protocol_retry"] += float(row["protocol_retry_count"])
            agg[k]["semantic_dup"] += float(row["semantic_duplicate_work_count"])
            agg[k]["mem_w"] += float(row.get("memory_write_count", 0.0))
            agg[k]["mem_r"] += float(row.get("memory_read_count", 0.0))
            agg[k]["mem_i"] += float(row.get("memory_invalidate_count", 0.0))

    lines = [
        "# Benchmark v0 Summary",
        "",
        "| scenario | policy | avg_events | avg_completion_time | avg_protocol_retries | avg_semantic_duplicates | avg_mem_w/r/i |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for (scenario, policy), v in sorted(agg.items()):
        n = v["n"]
        lines.append(
            f"| {scenario} | {policy} | {v['events']/n:.2f} | {v['lat']/n:.4f} | {v['protocol_retry']/n:.2f} | {v['semantic_dup']/n:.2f} | {v['mem_w']/n:.2f}/{v['mem_r']/n:.2f}/{v['mem_i']/n:.2f} |"
        )

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"SUMMARY_OK {OUT_MD}")


if __name__ == "__main__":
    main()
