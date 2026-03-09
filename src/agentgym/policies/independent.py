from .base import BasePolicy, ToolRequestPlan, MessagePlan


class IndependentPolicy(BasePolicy):
    name = "independent"

    def plan_requests(self, num_tasks: int, num_agents: int = 5):
        # Uncoordinated workers: bursty starts and heavier compute/database usage.
        plans = []
        tools = ["search", "compute", "database"]
        for i in range(num_tasks):
            plans.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"tr{i}",
                    agent_id=f"agent_{i % num_agents}",
                    tool_id=tools[(2 * i + 1) % len(tools)],
                    start_at=0.1 + (i % 4) * 0.01,
                )
            )
        return plans

    def plan_semantic_duplicates(self, num_tasks: int, num_agents: int = 5):
        # Independent workers often re-do same intent with a new request ID.
        dups = []
        for i in range(0, num_tasks, 3):
            dups.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"dup_ind_{i}",
                    agent_id=f"agent_{(i + 2) % num_agents}",
                    tool_id="search" if i % 2 == 0 else "compute",
                    start_at=0.15 + (i % 4) * 0.012,
                )
            )
        return dups

    def plan_messages(self, num_tasks: int, num_agents: int = 5):
        msgs = []
        for i in range(max(1, num_tasks // 2)):
            sender = f"agent_{i % num_agents}"
            recipient = f"agent_{(i + 1) % num_agents}"
            msgs.append(
                MessagePlan(
                    sender_id=sender,
                    recipient_id=recipient,
                    message_id=f"msg_ind_{i}",
                    sent_at=0.05 + i * 0.013,
                    content="status?",
                )
            )
        return msgs

    def plan_memory_cycle(self, num_tasks: int, num_agents: int = 5, min_confidence: float | None = None):
        writes = []
        reads = []
        invalidations = []
        for i in range(min(4, num_tasks)):
            mem_id = f"shared:hint:t{i}"
            task_id = f"t{i}"
            # Independent team writes sparse, lower-confidence hints.
            writes.append({
                "actor_id": f"agent_{i % num_agents}",
                "memory_id": mem_id,
                "value": {"preferred_tool": "search"},
                "at": 0.02 + i * 0.04,
                "ttl": 0.03 if i % 2 == 0 else 1.5,
                "confidence": 0.45 if i % 2 == 0 else 0.7,
            })
            reads.append({
                "actor_id": f"agent_{(i + 1) % num_agents}",
                "memory_id": mem_id,
                "task_id": task_id,
                "at": 0.08 + i * 0.04,
                "min_confidence": min_confidence if min_confidence is not None else 0.6,
                "on_hit": {"tool_id": "search", "tool_request_id": f"mem_hit_ind_{i}"},
                "on_miss": {"tool_id": "compute", "tool_request_id": f"mem_miss_ind_{i}"},
            })
            if i == 1:
                invalidations.append({"actor_id": "agent_0", "memory_id": mem_id, "at": 0.095})
        return {"writes": writes, "reads": reads, "invalidations": invalidations}

    def world_overrides(self):
        return {"backpressure_policy": "retry", "retry_mode": "fixed"}
