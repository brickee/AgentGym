from agentgym.core.events import Event


def test_event_ordering_by_time_priority_seq():
    e1 = Event(sim_time=1.0, priority=1, seq_id=2, event_type="x", actor_id="a", correlation_id="c")
    e2 = Event(sim_time=1.0, priority=0, seq_id=3, event_type="x", actor_id="a", correlation_id="c")
    e3 = Event(sim_time=0.5, priority=9, seq_id=1, event_type="x", actor_id="a", correlation_id="c")
    assert sorted([e1, e2, e3]) == [e3, e2, e1]
