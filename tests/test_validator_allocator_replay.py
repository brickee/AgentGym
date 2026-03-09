from agentgym.core.validator import TransitionValidator
from agentgym.core.allocator import ResourceAllocator
from agentgym.core.replay import replay_invariant_precheck


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


def test_validator_pending_request_bookkeeping_and_terminal_clear():
    v = TransitionValidator()
    assert v.validate_event("task_created", {"task_id": "t1"})[0]
    assert v.validate_event("tool_requested", {"task_id": "t1", "tool_request_id": "r1"})[0]
    assert "r1" in v.pending_tool_requests

    assert v.validate_event("tool_started", {"task_id": "t1", "tool_request_id": "r1"})[0]
    assert "r1" in v.pending_tool_requests

    assert v.validate_event("tool_finished", {"task_id": "t1", "tool_request_id": "r1"})[0]
    assert "r1" not in v.pending_tool_requests


def test_validator_duplicate_task_guard_and_uncreated_tool_request_guard():
    v = TransitionValidator()
    assert v.validate_event("task_created", {"task_id": "dup"})[0]
    ok, msg = v.validate_event("task_created", {"task_id": "dup"})
    assert not ok and "duplicate task_created" in msg

    v2 = TransitionValidator()
    ok2, msg2 = v2.validate_event("tool_requested", {"task_id": "missing", "tool_request_id": "r-miss"})
    assert not ok2 and "uncreated task" in msg2


def test_replay_precheck_detects_non_monotonic_and_terminal_after_terminal():
    events = [
        {"sim_time": 0.0, "event_type": "task_created", "payload": {"task_id": "t1"}},
        {"sim_time": 0.1, "event_type": "tool_requested", "payload": {"task_id": "t1", "tool_request_id": "r1"}},
        {"sim_time": 0.2, "event_type": "tool_started", "payload": {"task_id": "t1", "tool_request_id": "r1"}},
        {"sim_time": 0.3, "event_type": "tool_finished", "payload": {"task_id": "t1", "tool_request_id": "r1"}},
        {"sim_time": 0.15, "event_type": "tool_started", "payload": {"task_id": "t1", "tool_request_id": "r1"}},
    ]

    violations = replay_invariant_precheck(events)
    assert any("non-monotonic sim_time" in v for v in violations)
    assert any("after terminal" in v for v in violations)
