import heapq
from typing import List, Dict, Set, Tuple

from .events import Event
from .world import WorldState
from .validator import TransitionValidator
from .replay import EventRecorder
from .allocator import ResourceAllocator
from agentgym.eval.metrics import compute_task_success_rate, compute_average_completion_time


class Simulator:
    def __init__(self, world: WorldState, enable_replay: bool = True):
        self.world = world
        self._queue: List[Event] = []
        self._seq = 0
        self.validator = TransitionValidator()
        self.recorder = EventRecorder() if enable_replay else None

        tool_requirements = {
            tid: t.get("requirements", []) for tid, t in self.world.tools.items()
        }
        tool_rate_limits = {
            tid: float(t.get("rate_limit_per_sec", 0.0))
            for tid, t in self.world.tools.items()
            if float(t.get("rate_limit_per_sec", 0.0)) > 0
        }
        resource_config = self.world.resources or {
            "api_search": 5,
            "compute_slot": 2,
            "db_lock": 2,
        }
        self.allocator = ResourceAllocator(
            resource_config=resource_config,
            tool_requirements=tool_requirements,
            tool_rate_limits=tool_rate_limits,
            backpressure_policy=self.world.backpressure_policy,
        )
        self._held_resources: Dict[str, List[str]] = {}
        self._retry_count_by_request: Dict[str, int] = {}
        self._tool_call_seen: Set[Tuple[str, str]] = set()

    def schedule(self, sim_time: float, priority: int, event_type: str, actor_id: str, correlation_id: str, payload=None):
        if payload is None:
            payload = {}
        self._seq += 1
        evt = Event(
            sim_time=sim_time,
            priority=priority,
            seq_id=self._seq,
            event_type=event_type,
            actor_id=actor_id,
            correlation_id=correlation_id,
            payload=payload,
        )
        heapq.heappush(self._queue, evt)

    def run(self, max_events: int = 1000):
        self.world.status = "running"
        processed = 0
        while self._queue and processed < max_events:
            evt = heapq.heappop(self._queue)
            self.world.current_time = evt.sim_time
            ok, msg = self.validator.validate_event(evt.event_type, evt.payload)
            if not ok:
                raise ValueError(f"event validation failed: {msg}")
            if self.recorder:
                self.recorder.record({
                    "sim_time": evt.sim_time,
                    "priority": evt.priority,
                    "seq_id": evt.seq_id,
                    "event_type": evt.event_type,
                    "actor_id": evt.actor_id,
                    "correlation_id": evt.correlation_id,
                    "payload": evt.payload,
                })
            self._handle(evt)
            processed += 1
        if not self._queue:
            self.world.status = "done"
        ok, msg = self.validator.finalize()
        if not ok:
            raise ValueError(f"final validation failed: {msg}")

        self.world.metrics["events_processed"] = float(processed)
        self.world.metrics["task_success_rate"] = compute_task_success_rate(self.world.tasks)
        self.world.metrics["average_completion_time"] = compute_average_completion_time(self.world.tasks)
        self.world.metrics["retry_count"] = float(sum(self._retry_count_by_request.values()))
        return processed

    def _retry_delay(self, req_id: str) -> float:
        c = self._retry_count_by_request.get(req_id, 0)
        if self.world.retry_mode == "exp":
            d = self.world.retry_base_delay * (2 ** c)
            return min(d, self.world.retry_max_delay)
        return self.world.retry_base_delay

    def _handle(self, evt: Event):
        if evt.event_type == "task_created":
            task_id = evt.payload["task_id"]
            self.world.tasks[task_id] = {
                "status": "pending",
                "created_at": evt.sim_time,
            }
            return

        if evt.event_type == "tool_requested":
            tool_id = evt.payload["tool_id"]
            req_id = evt.payload["tool_request_id"]
            task_id = evt.payload.get("task_id", "")
            key = (task_id, tool_id)
            if key in self._tool_call_seen:
                self.world.metrics["duplicate_tool_calls"] += 1
            else:
                self._tool_call_seen.add(key)

            ok, held, tag = self.allocator.allocate(tool_id, now=evt.sim_time)
            if ok:
                self._held_resources[req_id] = held
                self.schedule(evt.sim_time, 1, "tool_started", evt.actor_id, evt.correlation_id, evt.payload)
                latency = float(self.world.tools[tool_id].get("latency", 1.0))
                self.schedule(evt.sim_time + latency, 1, "tool_finished", evt.actor_id, evt.correlation_id, evt.payload)
            else:
                if tag.startswith("retry:") or tag.startswith("wait:"):
                    self._retry_count_by_request[req_id] = self._retry_count_by_request.get(req_id, 0) + 1
                    delay = self._retry_delay(req_id)
                    self.schedule(evt.sim_time + delay, 2, "retry_scheduled", evt.actor_id, evt.correlation_id, evt.payload)
                else:
                    self.schedule(evt.sim_time, 2, "tool_failed", evt.actor_id, evt.correlation_id, {**evt.payload, "reason": tag})
            return

        if evt.event_type == "retry_scheduled":
            self.schedule(evt.sim_time, 1, "tool_requested", evt.actor_id, evt.correlation_id, evt.payload)
            return

        if evt.event_type == "tool_finished":
            req_id = evt.payload["tool_request_id"]
            held = self._held_resources.pop(req_id, [])
            self.allocator.release(held)
            task_id = evt.payload.get("task_id")
            if task_id and task_id in self.world.tasks:
                self.schedule(evt.sim_time, 1, "task_completed", evt.actor_id, evt.correlation_id, {"task_id": task_id})
            return

        if evt.event_type == "task_completed":
            task_id = evt.payload["task_id"]
            if task_id in self.world.tasks:
                self.world.tasks[task_id]["status"] = "done"
                self.world.tasks[task_id]["completed_at"] = evt.sim_time
            return

        if evt.event_type == "memory_write":
            mem_id = evt.payload["memory_id"]
            self.world.memory_store[mem_id] = {
                "value": evt.payload.get("value"),
                "owner": evt.actor_id,
                "updated_at": evt.sim_time,
            }
            self.world.metrics["memory_write_count"] += 1
            return

        if evt.event_type == "memory_read":
            self.world.metrics["memory_read_count"] += 1
            return

        if evt.event_type == "memory_invalidate":
            mem_id = evt.payload.get("memory_id")
            if mem_id in self.world.memory_store:
                del self.world.memory_store[mem_id]
            return
