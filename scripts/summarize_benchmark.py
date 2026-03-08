import csv
from collections import defaultdict
from pathlib import Path

CSV_PATH = Path("artifacts/benchmark_v0.csv")
OUT_MD = Path("artifacts/benchmark_v0_summary.md")


def main():
    agg = defaultdict(lambda: {"n": 0, "events": 0.0, "lat": 0.0, "retry": 0.0, "dup": 0.0})
    with CSV_PATH.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            p = row["policy"]
            agg[p]["n"] += 1
            agg[p]["events"] += float(row["events_processed"])
            agg[p]["lat"] += float(row["avg_completion_time"])
            agg[p]["retry"] += float(row["retry_count"])
            agg[p]["dup"] += float(row["duplicate_tool_calls"])

    lines = ["# Benchmark v0 Summary", "", "| policy | avg_events | avg_completion_time | avg_retry | avg_duplicate_calls |", "|---|---:|---:|---:|---:|"]
    for p, v in sorted(agg.items()):
        n = v["n"]
        lines.append(f"| {p} | {v['events']/n:.2f} | {v['lat']/n:.4f} | {v['retry']/n:.2f} | {v['dup']/n:.2f} |")

    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"SUMMARY_OK {OUT_MD}")


if __name__ == "__main__":
    main()
