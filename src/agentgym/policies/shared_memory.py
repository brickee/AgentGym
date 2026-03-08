from .base import BasePolicy, ToolRequestPlan, MessagePlan


class SharedMemoryPolicy(BasePolicy):
    name = "shared_memory"

    def plan_requests(self, num_tasks: int, num_agents: int = 5):
        # Shared memory policy prefers search+database and limits expensive compute.
        plans = []
        for i in range(num_tasks):
            tool = "compute" if i in {0, 7} else ("database" if i % 4 == 0 else "search")
            plans.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"tr{i}",
                    agent_id=f"agent_{i % num_agents}",
                    tool_id=tool,
                    start_at=0.1 + i * 0.05,
                )
            )
        return plans

    def plan_semantic_duplicates(self, num_tasks: int, num_agents: int = 5):
        # Memory sharing suppresses duplicate intents in this baseline.
        return []

    def plan_messages(self, num_tasks: int, num_agents: int = 5):
        # Lightweight sync pings around memory writes.
        msgs = []
        for i in range(max(1, num_tasks // 4)):
            msgs.append(
                MessagePlan(
                    sender_id=f"agent_{i % num_agents}",
                    recipient_id=f"agent_{(i + 2) % num_agents}",
                    message_id=f"msg_sm_{i}",
                    sent_at=0.04 + i * 0.04,
                    content="mem-updated",
                )
            )
        return msgs

    def plan_memory_cycle(self, num_tasks: int, num_agents: int = 5):
        writes = []
        reads = []
        invalidations = []
        for i in range(min(4, num_tasks)):
            mem_id = f"shared:hint:t{i}"
            task_id = f"t{i}"
            writes.append({
                "actor_id": f"agent_{i % num_agents}",
                "memory_id": mem_id,
                "value": {"preferred_tool": "search"},
                "at": 0.005 + i * 0.025,
                "ttl": 4.0,
                "confidence": 0.95,
            })
            reads.append({
                "actor_id": f"agent_{(i + 2) % num_agents}",
                "memory_id": mem_id,
                "task_id": task_id,
                "at": 0.05 + i * 0.025,
                "min_confidence": 0.7,
                "on_hit": {"tool_id": "search", "tool_request_id": f"mem_hit_sm_{i}"},
                "on_miss": {"tool_id": "compute", "tool_request_id": f"mem_miss_sm_{i}"},
            })
            if i == 3:
                invalidations.append({"actor_id": "agent_4", "memory_id": mem_id, "at": 0.2})
        return {"writes": writes, "reads": reads, "invalidations": invalidations}

    def world_overrides(self):
        return {"backpressure_policy": "retry", "retry_mode": "exp", "retry_base_delay": 0.5}
