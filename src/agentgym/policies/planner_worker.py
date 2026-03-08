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

    def plan_memory_cycle(self, num_tasks: int, num_agents: int = 5):
        writes = []
        reads = []
        invalidations = []
        for i in range(min(4, num_tasks)):
            mem_id = f"shared:hint:t{i}"
            task_id = f"t{i}"
            writes.append({
                "actor_id": "agent_0",
                "memory_id": mem_id,
                "value": {"preferred_tool": "database" if i % 2 == 0 else "search"},
                "at": 0.01 + i * 0.03,
                "ttl": 2.0,
                "confidence": 0.8,
            })
            reads.append({
                "actor_id": f"agent_{(i % (num_agents - 1)) + 1}",
                "memory_id": mem_id,
                "task_id": task_id,
                "at": 0.06 + i * 0.03,
                "min_confidence": 0.65,
                "on_hit": {"tool_id": "database" if i % 2 == 0 else "search", "tool_request_id": f"mem_hit_pw_{i}"},
                "on_miss": {"tool_id": "compute", "tool_request_id": f"mem_miss_pw_{i}"},
            })
        return {"writes": writes, "reads": reads, "invalidations": invalidations}

    def world_overrides(self):
        return {"backpressure_policy": "wait", "retry_mode": "fixed"}
