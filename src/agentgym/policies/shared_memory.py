from .base import BasePolicy, ToolRequestPlan


class SharedMemoryPolicy(BasePolicy):
    name = "shared_memory"

    def plan_requests(self, num_tasks: int, num_agents: int = 5):
        # Shared memory reduces duplicate expensive compute calls.
        plans = []
        for i in range(num_tasks):
            tool = "compute" if i in {0, 4} else "search"
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

    def world_overrides(self):
        return {"backpressure_policy": "retry", "retry_mode": "exp", "retry_base_delay": 0.5}
