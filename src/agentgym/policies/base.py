from dataclasses import dataclass
from typing import List, Dict


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


class BasePolicy:
    name: str = "base"

    def plan_requests(self, num_tasks: int, num_agents: int = 5) -> List[ToolRequestPlan]:
        raise NotImplementedError

    def plan_semantic_duplicates(self, num_tasks: int, num_agents: int = 5) -> List[ToolRequestPlan]:
        return []

    def plan_messages(self, num_tasks: int, num_agents: int = 5) -> List[MessagePlan]:
        return []

    def world_overrides(self) -> Dict:
        return {}
