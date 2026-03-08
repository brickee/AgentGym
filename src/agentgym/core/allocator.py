from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ResourceUnit:
    total_units: int
    used_units: int = 0


@dataclass
class TokenBucket:
    rate_per_sec: float
    capacity: float
    tokens: float
    last_refill_time: float = 0.0

    def refill(self, now: float) -> None:
        elapsed = max(0.0, now - self.last_refill_time)
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate_per_sec)
        self.last_refill_time = now

    def consume(self, amount: float, now: float) -> bool:
        self.refill(now)
        if self.tokens >= amount:
            self.tokens -= amount
            return True
        return False


class ResourceAllocator:
    """Resource allocator with capacity + rate limit + backpressure policy.

    backpressure_policy:
      - wait: caller should retry later
      - drop: immediate rejection
      - retry: rejection with retry hint
    """

    def __init__(
        self,
        resource_config: Dict[str, int],
        tool_requirements: Dict[str, List[str]],
        tool_rate_limits: Dict[str, float] | None = None,
        backpressure_policy: str = "wait",
    ):
        self.resources: Dict[str, ResourceUnit] = {
            rid: ResourceUnit(total_units=units) for rid, units in resource_config.items()
        }
        self.tool_requirements = tool_requirements
        self.backpressure_policy = backpressure_policy
        self.tool_buckets: Dict[str, TokenBucket] = {}
        tool_rate_limits = tool_rate_limits or {}
        for tool_id, rps in tool_rate_limits.items():
            cap = max(1.0, rps)
            self.tool_buckets[tool_id] = TokenBucket(rate_per_sec=rps, capacity=cap, tokens=cap)

    def can_allocate(self, tool_id: str) -> bool:
        for rid in self.tool_requirements.get(tool_id, []):
            r = self.resources[rid]
            if r.used_units >= r.total_units:
                return False
        return True

    def _rate_limit_ok(self, tool_id: str, now: float) -> bool:
        bucket = self.tool_buckets.get(tool_id)
        if bucket is None:
            return True
        return bucket.consume(1.0, now)

    def allocate(self, tool_id: str, now: float = 0.0) -> Tuple[bool, List[str], str]:
        reqs = self.tool_requirements.get(tool_id, [])
        if not self._rate_limit_ok(tool_id, now):
            return self._reject(reason="rate_limited")
        if not self.can_allocate(tool_id):
            return self._reject(reason="capacity_blocked")

        for rid in reqs:
            self.resources[rid].used_units += 1
        return True, reqs, "allocated"

    def _reject(self, reason: str) -> Tuple[bool, List[str], str]:
        if self.backpressure_policy == "drop":
            return False, [], f"dropped:{reason}"
        if self.backpressure_policy == "retry":
            return False, [], f"retry:{reason}"
        return False, [], f"wait:{reason}"

    def release(self, resource_ids: List[str]) -> None:
        for rid in resource_ids:
            r = self.resources[rid]
            if r.used_units > 0:
                r.used_units -= 1
