from .base import BasePolicy, ToolRequestPlan


class PlannerWorkerPolicy(BasePolicy):
    name = "planner_worker"

    def plan_requests(self, num_tasks: int, num_agents: int = 5):
        # Coordinated: staggered queue and search-first pattern.
        plans = []
        for i in range(num_tasks):
            plans.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"tr{i}",
                    agent_id=f"agent_{i % num_agents}",
                    tool_id="search" if i % 3 else "compute",
                    start_at=0.1 + i * 0.08,
                )
            )
        return plans

    def world_overrides(self):
        return {"backpressure_policy": "wait", "retry_mode": "fixed"}
