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
    ok, _ = a.allocate("search")
    assert ok
    ok2, _ = a.allocate("search")
    assert not ok2
