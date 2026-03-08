from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class ToolRequestPlan:
    task_id: str
    tool_request_id: str
    agent_id: str
    tool_id: str
    start_at: float


@dataclass
class MessagePlan:
    sender_id: str
    recipient_id: str
    message_id: str
    sent_at: float
    content: str


@dataclass
class MemoryWritePlan:
    actor_id: str
    memory_id: str
    value: Dict[str, Any]
    at: float
    ttl: float | None = None
    confidence: float = 1.0


@dataclass
class MemoryReadPlan:
    actor_id: str
    memory_id: str
    task_id: str
    at: float
    on_hit: Dict[str, Any]
    on_miss: Dict[str, Any]
    min_confidence: float = 0.5


class BasePolicy:
    name: str = "base"

    def plan_requests(self, num_tasks: int, num_agents: int = 5) -> List[ToolRequestPlan]:
        raise NotImplementedError

    def plan_semantic_duplicates(self, num_tasks: int, num_agents: int = 5) -> List[ToolRequestPlan]:
        return []

    def plan_messages(self, num_tasks: int, num_agents: int = 5) -> List[MessagePlan]:
        return []

    def plan_memory_cycle(self, num_tasks: int, num_agents: int = 5) -> Dict[str, List]:
        return {"writes": [], "reads": [], "invalidations": []}

    def world_overrides(self) -> Dict:
        return {}
