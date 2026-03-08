from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ToolRequestPlan:
    task_id: str
    tool_request_id: str
    agent_id: str
    tool_id: str
    start_at: float


class BasePolicy:
    name: str = "base"

    def plan_requests(self, num_tasks: int, num_agents: int = 5) -> List[ToolRequestPlan]:
        raise NotImplementedError

    def world_overrides(self) -> Dict:
        return {}
