from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class WorldState:
    current_time: float = 0.0
    seed: int = 42
    status: str = "idle"
    agents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=lambda: {
        "task_success_rate": 0.0,
        "average_completion_time": 0.0,
        "resource_utilization": 0.0,
        "duplicate_tool_calls": 0.0,
        "communication_cost": 0.0,
    })
