from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ResourceUnit:
    total_units: int
    used_units: int = 0


class ResourceAllocator:
    """Minimal resource allocator that maps tool requests to shared resources."""

    def __init__(self, resource_config: Dict[str, int], tool_requirements: Dict[str, List[str]]):
        self.resources: Dict[str, ResourceUnit] = {
            rid: ResourceUnit(total_units=units) for rid, units in resource_config.items()
        }
        self.tool_requirements = tool_requirements

    def can_allocate(self, tool_id: str) -> bool:
        for rid in self.tool_requirements.get(tool_id, []):
            r = self.resources[rid]
            if r.used_units >= r.total_units:
                return False
        return True

    def allocate(self, tool_id: str) -> Tuple[bool, List[str]]:
        reqs = self.tool_requirements.get(tool_id, [])
        if not self.can_allocate(tool_id):
            return False, []
        for rid in reqs:
            self.resources[rid].used_units += 1
        return True, reqs

    def release(self, resource_ids: List[str]) -> None:
        for rid in resource_ids:
            r = self.resources[rid]
            if r.used_units > 0:
                r.used_units -= 1
