from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(order=True)
class Event:
    sort_key: tuple = field(init=False, repr=False)
    sim_time: float
    priority: int
    seq_id: int
    event_type: str
    actor_id: str
    correlation_id: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.sort_key = (self.sim_time, self.priority, self.seq_id)
