import heapq
from typing import List

from .events import Event
from .world import WorldState


class Simulator:
    def __init__(self, world: WorldState):
        self.world = world
        self._queue: List[Event] = []
        self._seq = 0

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
            self._handle(evt)
            processed += 1
        if not self._queue:
            self.world.status = "done"
        return processed

    def _handle(self, evt: Event):
        if evt.event_type == "task_created":
            task_id = evt.payload["task_id"]
            self.world.tasks[task_id] = {
                "status": "pending",
                "created_at": evt.sim_time,
            }
        elif evt.event_type == "task_completed":
            task_id = evt.payload["task_id"]
            if task_id in self.world.tasks:
                self.world.tasks[task_id]["status"] = "done"
