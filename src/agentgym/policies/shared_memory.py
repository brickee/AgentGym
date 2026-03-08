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

    def world_overrides(self):
        return {"backpressure_policy": "retry", "retry_mode": "exp", "retry_base_delay": 0.5}
