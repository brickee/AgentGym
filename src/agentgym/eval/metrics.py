def compute_task_success_rate(tasks: dict) -> float:
    if not tasks:
        return 0.0
    done = sum(1 for t in tasks.values() if t.get("status") == "done")
    return done / len(tasks)
