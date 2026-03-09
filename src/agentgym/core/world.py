from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class WorldState:
    current_time: float = 0.0
    seed: int = 42
    status: str = "idle"
    backpressure_policy: str = "wait"
    retry_mode: str = "fixed"  # fixed | exp
    retry_base_delay: float = 1.0
    retry_max_delay: float = 8.0
    agents: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resources: Dict[str, int] = field(default_factory=dict)
    memory_store: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metrics: Dict[str, float] = field(default_factory=lambda: {
        "task_success_rate": 0.0,
        "average_completion_time": 0.0,
        "resource_utilization": 0.0,
        "duplicate_tool_calls": 0.0,  # legacy compatibility alias
        "semantic_duplicate_work_count": 0.0,
        "communication_cost": 0.0,
        "communication_event_count": 0.0,
        "events_processed": 0.0,
        "retry_count": 0.0,  # legacy compatibility alias
        "protocol_retry_count": 0.0,
        "memory_read_count": 0.0,
        "memory_write_count": 0.0,
        "memory_invalidate_count": 0.0,
        "memory_hit_count": 0.0,
        "memory_miss_count": 0.0,
        "memory_stale_read_count": 0.0,
        "memory_low_confidence_read_count": 0.0,
        "memory_poisoned_write_count": 0.0,
        "memory_poisoned_read_count": 0.0,
    })
