from agentgym.core.validator import TransitionValidator
from agentgym.core.allocator import ResourceAllocator


def test_validator_tool_lifecycle():
    v = TransitionValidator()
    ok, _ = v.validate_event("tool_requested", {"tool_request_id": "x1"})
    assert ok
    ok, _ = v.validate_event("tool_started", {"tool_request_id": "x1"})
    assert ok
    ok, _ = v.validate_event("tool_finished", {"tool_request_id": "x1"})
    assert ok


def test_allocator_basic_contention():
    a = ResourceAllocator({"r1": 1}, {"search": ["r1"]})
    ok, _, _ = a.allocate("search", now=0.0)
    assert ok
    ok2, _, tag = a.allocate("search", now=0.0)
    assert (not ok2) and tag.startswith("wait:")


def test_allocator_rate_limit_retry_policy():
    a = ResourceAllocator(
        {"r1": 1},
        {"search": ["r1"]},
        tool_rate_limits={"search": 1.0},
        backpressure_policy="retry",
    )
    ok, held, _ = a.allocate("search", now=0.0)
    assert ok
    a.release(held)
    ok2, _, tag = a.allocate("search", now=0.0)
    assert (not ok2) and tag.startswith("retry:rate_limited")
