from .base import BasePolicy, ToolRequestPlan, MessagePlan


class PlannerWorkerPolicy(BasePolicy):
    name = "planner_worker"

    def plan_requests(self, num_tasks: int, num_agents: int = 5):
        # Coordinated planner assigns staggered tasks with mostly search/database.
        plans = []
        for i in range(num_tasks):
            tool = "compute" if i % 5 == 0 else ("database" if i % 2 == 0 else "search")
            plans.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"tr{i}",
                    agent_id=f"agent_{i % num_agents}",
                    tool_id=tool,
                    start_at=0.1 + i * 0.075,
                )
            )
        return plans

    def plan_semantic_duplicates(self, num_tasks: int, num_agents: int = 5):
        # Planner occasionally causes one overlap near handoff boundaries.
        dups = []
        for i in range(0, num_tasks, 9):
            dups.append(
                ToolRequestPlan(
                    task_id=f"t{i}",
                    tool_request_id=f"dup_pw_{i}",
                    agent_id=f"agent_{(i + 1) % num_agents}",
                    tool_id="search",
                    start_at=0.14 + i * 0.004,
                )
            )
        return dups

    def plan_messages(self, num_tasks: int, num_agents: int = 5):
        # Planner-heavy communication.
        msgs = []
        planner = "agent_0"
        for i in range(num_tasks):
            worker = f"agent_{(i % (num_agents - 1)) + 1}"
            msgs.append(
                MessagePlan(
                    sender_id=planner,
                    recipient_id=worker,
                    message_id=f"msg_pw_assign_{i}",
                    sent_at=0.03 + i * 0.01,
                    content=f"do-task-{i}",
                )
            )
            msgs.append(
                MessagePlan(
                    sender_id=worker,
                    recipient_id=planner,
                    message_id=f"msg_pw_report_{i}",
                    sent_at=0.035 + i * 0.01,
                    content="ack",
                )
            )
        return msgs

    def world_overrides(self):
        return {"backpressure_policy": "wait", "retry_mode": "fixed"}
