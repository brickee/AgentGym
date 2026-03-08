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
