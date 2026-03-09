import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


class EventRecorder:
    def __init__(self):
        self.events: List[Dict] = []

    def record(self, event_dict: Dict) -> None:
        self.events.append(event_dict)

    def dump_jsonl(self, path: str) -> None:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("w", encoding="utf-8") as f:
            for e in self.events:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")


def load_jsonl(path: str) -> List[Dict]:
    p = Path(path)
    out: List[Dict] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            out.append(json.loads(line))
    return out


def replay_event_distribution(events: List[Dict]) -> Dict[str, int]:
    """Count events by event_type."""
    dist: Dict[str, int] = defaultdict(int)
    for e in events:
        dist[e.get("event_type", "unknown")] += 1
    return dict(sorted(dist.items()))


def replay_duplicate_decomposition(events: List[Dict]) -> Dict[str, Dict]:
    """Decompose duplicate-work signals by agent and task.

    Returns dict with:
      - by_agent: {agent_id: count} of semantic duplicate tool requests
      - by_task: {task_id: count} of semantic duplicate tool requests
      - intent_map: {(task_id, tool_id): [request_ids]}
    """
    intent_map: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    seen_req_ids: set = set()

    for e in events:
        if e.get("event_type") != "tool_requested":
            continue
        payload = e.get("payload", {})
        req_id = payload.get("tool_request_id", "")
        task_id = payload.get("task_id", "")
        tool_id = payload.get("tool_id", "")
        if req_id and req_id not in seen_req_ids:
            seen_req_ids.add(req_id)
            intent_map[(task_id, tool_id)].append(req_id)

    by_agent: Dict[str, int] = defaultdict(int)
    by_task: Dict[str, int] = defaultdict(int)

    # For intents with >1 distinct request_id, each extra is a duplicate
    dup_req_ids: set = set()
    for (task_id, tool_id), req_ids in intent_map.items():
        if len(req_ids) > 1:
            for rid in req_ids[1:]:
                dup_req_ids.add(rid)
                by_task[task_id] = by_task.get(task_id, 0) + 1

    # Map duplicate request_ids back to actors
    for e in events:
        if e.get("event_type") != "tool_requested":
            continue
        payload = e.get("payload", {})
        req_id = payload.get("tool_request_id", "")
        if req_id in dup_req_ids:
            actor = e.get("actor_id", "unknown")
            by_agent[actor] = by_agent.get(actor, 0) + 1

    return {
        "by_agent": dict(by_agent),
        "by_task": dict(by_task),
        "intent_map": {f"{k[0]}:{k[1]}": v for k, v in intent_map.items()},
    }


def replay_invariant_precheck(events: List[Dict]) -> List[str]:
    """Run lightweight invariant checks on a replay trace.

    Returns list of violation strings (empty = clean).
    """
    violations: List[str] = []

    # Check 1: tool lifecycle ordering
    tool_last: Dict[str, str] = {}
    ALLOWED_NEXT = {
        "tool_requested": {"tool_started", "tool_failed", "retry_scheduled"},
        "tool_started": {"tool_finished", "tool_failed", "task_failed"},
        "retry_scheduled": {"tool_requested", "tool_failed"},
    }
    TERMINAL = {"tool_finished", "tool_failed", "task_failed"}
    tool_events = {"tool_requested", "tool_started", "tool_finished", "tool_failed", "retry_scheduled", "task_failed"}

    # Check 2: task_created before tool_requested referencing task
    created_tasks: set = set()
    # Check 3: duplicate task_created
    # Check 4: monotonic sim_time
    last_time = -1.0

    for e in events:
        etype = e.get("event_type", "")
        payload = e.get("payload", {})
        sim_time = float(e.get("sim_time", 0.0))

        if sim_time < last_time:
            violations.append(f"non-monotonic sim_time: {last_time} -> {sim_time}")
        last_time = sim_time

        if etype == "task_created":
            tid = payload.get("task_id", "")
            if tid in created_tasks:
                violations.append(f"duplicate task_created: {tid}")
            created_tasks.add(tid)

        if etype == "tool_requested":
            tid = payload.get("task_id", "")
            if tid and tid not in created_tasks:
                violations.append(f"tool_requested for uncreated task: {tid}")

        req_id = payload.get("tool_request_id")
        if req_id and etype in tool_events:
            prev = tool_last.get(req_id)
            if prev is None:
                if etype != "tool_requested":
                    violations.append(f"tool {req_id} starts at {etype}, expected tool_requested")
            elif prev in TERMINAL:
                violations.append(f"tool {req_id} event {etype} after terminal {prev}")
            else:
                allowed = ALLOWED_NEXT.get(prev, set())
                if etype not in allowed:
                    violations.append(f"tool {req_id}: invalid {prev} -> {etype}")
            tool_last[req_id] = etype

    return violations
