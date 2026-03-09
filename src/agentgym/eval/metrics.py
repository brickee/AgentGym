def compute_task_success_rate(tasks: dict) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks.values() if t.get("status") == "done")
    return done / len(tasks)


def compute_average_completion_time(tasks: dict) -> float:
    times = []
    for t in tasks.values():
        if t.get("status") == "done" and t.get("completed_at") is not None:
            times.append(float(t["completed_at"]) - float(t.get("created_at", 0.0)))
    if not times:
        return 0.0
    return sum(times) / len(times)


def compute_normalized_metrics(metrics: dict, num_tasks: int) -> dict:
    """Compute per-task and per-success normalized metrics.

    Returns dict with normalized communication and protocol metrics.
    """
    success_rate = float(metrics.get("task_success_rate", 0.0))
    successful_tasks = max(1, round(success_rate * num_tasks))
    safe_tasks = max(1, num_tasks)

    comm_cost = float(metrics.get("communication_cost", 0.0))
    comm_events = float(metrics.get("communication_event_count", 0.0))
    retries = float(metrics.get("protocol_retry_count", 0.0))
    duplicates = float(metrics.get("semantic_duplicate_work_count", 0.0))

    return {
        "comm_cost_per_task": round(comm_cost / safe_tasks, 4),
        "comm_cost_per_success": round(comm_cost / successful_tasks, 4),
        "comm_events_per_task": round(comm_events / safe_tasks, 4),
        "retries_per_task": round(retries / safe_tasks, 4),
        "duplicates_per_task": round(duplicates / safe_tasks, 4),
        "comm_effectiveness": round(
            (success_rate * safe_tasks) / max(1.0, comm_cost) * 100, 4
        ) if comm_cost > 0 else 0.0,
    }
