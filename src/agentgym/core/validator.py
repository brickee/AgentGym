from collections import defaultdict
from typing import Dict, Set, Tuple


class TransitionValidator:
    """Validate coarse event lifecycle constraints."""

    ALLOWED_NEXT = {
        "tool_requested": {"tool_started", "tool_failed", "retry_scheduled"},
        "tool_started": {"tool_finished", "tool_failed", "task_failed"},
        "retry_scheduled": {"tool_requested", "tool_failed"},
    }

    TERMINAL_TOOL = {"tool_finished", "tool_failed", "task_failed"}
    TERMINAL_TASK = {"task_completed", "task_failed"}

    def __init__(self) -> None:
        self._last_tool_event: Dict[str, str] = {}
        self._task_terminal: Dict[str, str] = {}
        self._resource_balance = defaultdict(int)
        self._created_tasks: Set[str] = set()
        self._pending_tool_requests: Set[str] = set()

    def validate_event(self, event_type: str, payload: Dict) -> Tuple[bool, str]:
        tool_req_id = payload.get("tool_request_id")
        task_id = payload.get("task_id")

        # Duplicate task_created check
        if event_type == "task_created":
            if task_id:
                if task_id in self._created_tasks:
                    return False, f"duplicate task_created: {task_id}"
                self._created_tasks.add(task_id)

        # tool_requested must reference a created task (if task_id present)
        if event_type == "tool_requested" and task_id:
            if task_id not in self._created_tasks:
                return False, f"tool_requested for uncreated task: {task_id}"

        if tool_req_id and event_type in {
            "tool_requested",
            "tool_started",
            "tool_finished",
            "tool_failed",
            "retry_scheduled",
            "task_failed",
        }:
            ok, msg = self._validate_tool_lifecycle(tool_req_id, event_type)
            if not ok:
                return False, msg
            # Track pending (non-terminal) tool requests
            if event_type == "tool_requested":
                self._pending_tool_requests.add(tool_req_id)
            if event_type in self.TERMINAL_TOOL:
                self._pending_tool_requests.discard(tool_req_id)

        if task_id and event_type in self.TERMINAL_TASK:
            if task_id in self._task_terminal:
                return False, f"task {task_id} already terminal via {self._task_terminal[task_id]}"
            self._task_terminal[task_id] = event_type

        if event_type in {"resource_acquired", "resource_released"}:
            holder = payload.get("holder_id")
            resource = payload.get("resource_id")
            if not holder or not resource:
                return False, "resource event missing holder_id/resource_id"
            key = f"{resource}:{holder}"
            if event_type == "resource_acquired":
                self._resource_balance[key] += 1
            else:
                self._resource_balance[key] -= 1
                if self._resource_balance[key] < 0:
                    return False, f"resource underflow for {key}"

        return True, "ok"

    def finalize(self) -> Tuple[bool, str]:
        leaked = [k for k, v in self._resource_balance.items() if v != 0]
        if leaked:
            return False, f"resource leak detected: {leaked}"
        return True, "ok"

    @property
    def created_tasks(self) -> Set[str]:
        return set(self._created_tasks)

    @property
    def terminal_tasks(self) -> Dict[str, str]:
        return dict(self._task_terminal)

    @property
    def pending_tool_requests(self) -> Set[str]:
        return set(self._pending_tool_requests)

    def _validate_tool_lifecycle(self, tool_req_id: str, current: str) -> Tuple[bool, str]:
        prev = self._last_tool_event.get(tool_req_id)
        if prev is None:
            if current != "tool_requested":
                return False, f"tool_request {tool_req_id} must start from tool_requested, got {current}"
            self._last_tool_event[tool_req_id] = current
            return True, "ok"

        if prev in self.TERMINAL_TOOL:
            return False, f"tool_request {tool_req_id} already terminal at {prev}"

        allowed = self.ALLOWED_NEXT.get(prev, set())
        if current not in allowed:
            return False, f"invalid transition for {tool_req_id}: {prev} -> {current}"

        self._last_tool_event[tool_req_id] = current
        return True, "ok"
