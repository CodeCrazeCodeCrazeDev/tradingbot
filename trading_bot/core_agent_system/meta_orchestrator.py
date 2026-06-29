"""
Meta-Orchestrator - Self-Scaffolding Research Architecture

The Meta-Orchestrator learns to construct its own orchestration framework
by optimizing workflow policies: task decomposition, agent selection,
tool selection, and execution order.

It does NOT modify source code; instead, it manages a "Strategy Library"
of optimized workflow graphs.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class WorkflowNodeType(Enum):
    DECOMPOSE = "decompose"
    SELECT_AGENT = "select_agent"
    CALL_TOOL = "call_tool"
    VERIFY = "verify"
    RETRY = "retry"
    CONCLUDE = "conclude"

@dataclass
class WorkflowNode:
    """A node in a learned workflow graph"""
    node_id: str
    node_type: WorkflowNodeType
    config: Dict[str, Any]
    next_nodes: List[str] = field(default_factory=list)
    condition: Optional[str] = None

@dataclass
class WorkflowPolicy:
    """A learned orchestration strategy (Workflow Graph)"""
    policy_id: str
    name: str
    description: str
    nodes: Dict[str, WorkflowNode]
    start_node: str
    performance_metrics: Dict[str, float] = field(default_factory=lambda: {
        "success_rate": 0.0,
        "avg_duration": 0.0,
        "resource_efficiency": 0.0
    })
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)

class StrategyLibrary:
    """Repository of optimized Workflow Policies"""
    def __init__(self):
        self.policies: Dict[str, WorkflowPolicy] = {}
        self._load_default_policies()

    def _load_default_policies(self):
        """Seed the library with initial human-designed strategies"""

        # 1. Standard Analysis Workflow
        analysis_id = "standard_analysis_v1"
        analysis_nodes = {
            "decompose": WorkflowNode("decompose", WorkflowNodeType.DECOMPOSE, {"depth": 1}, ["end"]),
            "end": WorkflowNode("end", WorkflowNodeType.CONCLUDE, {})
        }
        self.policies[analysis_id] = WorkflowPolicy(
            analysis_id, "Standard Analysis", "Standard sequential analysis workflow using Coordination Core",
            analysis_nodes, "decompose",
            performance_metrics={"success_rate": 0.8, "avg_duration": 10.0, "resource_efficiency": 0.7}
        )

        # 2. Research & Discovery Workflow
        research_id = "research_discovery_v1"
        research_nodes = {
            "select_researcher": WorkflowNode("select_researcher", WorkflowNodeType.SELECT_AGENT, {"role": "researcher"}, ["research_task"]),
            "research_task": WorkflowNode("research_task", WorkflowNodeType.DECOMPOSE, {"type": "research"}, ["verify"]),
            "verify": WorkflowNode("verify", WorkflowNodeType.VERIFY, {"threshold": 0.8}, ["end"]),
            "end": WorkflowNode("end", WorkflowNodeType.CONCLUDE, {})
        }
        self.policies[research_id] = WorkflowPolicy(
            research_id, "Research & Discovery", "Deep research workflow for new market patterns",
            research_nodes, "select_researcher",
            performance_metrics={"success_rate": 0.7, "avg_duration": 30.0, "resource_efficiency": 0.6}
        )

        # 3. High-Confidence Execution Workflow
        execution_id = "safe_execution_v1"
        exec_nodes = {
            "safety_check": WorkflowNode("safety_check", WorkflowNodeType.VERIFY, {"threshold": 0.9}, ["select_executor"]),
            "select_executor": WorkflowNode("select_executor", WorkflowNodeType.SELECT_AGENT, {"role": "executor"}, ["execute"]),
            "execute": WorkflowNode("execute", WorkflowNodeType.DECOMPOSE, {"type": "execution"}, ["verify_outcome"]),
            "verify_outcome": WorkflowNode("verify_outcome", WorkflowNodeType.VERIFY, {"threshold": 0.7}, ["end"]),
            "end": WorkflowNode("end", WorkflowNodeType.CONCLUDE, {})
        }
        self.policies[execution_id] = WorkflowPolicy(
            execution_id, "Safe Execution", "Execution workflow with pre-safety and post-verification",
            exec_nodes, "safety_check",
            performance_metrics={"success_rate": 0.95, "avg_duration": 5.0, "resource_efficiency": 0.9}
        )

        # 4. Adaptive Recovery Workflow
        recovery_id = "adaptive_recovery_v1"
        recovery_nodes = {
            "analyze_failure": WorkflowNode("analyze_failure", WorkflowNodeType.DECOMPOSE, {"type": "analysis"}, ["select_optimizer"]),
            "select_optimizer": WorkflowNode("select_optimizer", WorkflowNodeType.SELECT_AGENT, {"role": "optimizer"}, ["propose_fix"]),
            "propose_fix": WorkflowNode("propose_fix", WorkflowNodeType.DECOMPOSE, {"type": "planning"}, ["end"]),
            "end": WorkflowNode("end", WorkflowNodeType.CONCLUDE, {})
        }
        self.policies[recovery_id] = WorkflowPolicy(
            recovery_id, "Adaptive Recovery", "Workflow for recovering from system or strategy failures",
            recovery_nodes, "analyze_failure",
            performance_metrics={"success_rate": 0.6, "avg_duration": 15.0, "resource_efficiency": 0.5}
        )

    def add_policy(self, policy: WorkflowPolicy):
        self.policies[policy.policy_id] = policy

    def get_best_policy_for_task(self, task: str) -> Optional[WorkflowPolicy]:
        """Select best policy based on task context and historical performance"""
        if not self.policies:
            return None

        task_lower = task.lower()

        # 1. Keyword-based matching for specific domains
        candidate_ids = []
        if any(kw in task_lower for kw in ["execute", "trade", "buy", "sell", "order"]):
            candidate_ids.append("safe_execution_v1")
        if any(kw in task_lower for kw in ["research", "discover", "pattern", "alpha"]):
            candidate_ids.append("research_discovery_v1")
        if any(kw in task_lower for kw in ["recover", "fix", "fail", "error", "optimize"]):
            candidate_ids.append("adaptive_recovery_v1")
        if any(kw in task_lower for kw in ["analyze", "plan", "forecast", "predict"]):
            candidate_ids.append("standard_analysis_v1")

        # 2. Filter candidates
        candidates = [self.policies[pid] for pid in candidate_ids if pid in self.policies]

        # 3. Fallback to all policies if no specific domain matched
        if not candidates:
            candidates = list(self.policies.values())

        # 4. Select best by performance within candidates
        return max(candidates, key=lambda p: p.performance_metrics["success_rate"])

class WorkflowMemory:
    """Episodic memory for workflow executions"""
    def __init__(self):
        self.executions: List[Dict[str, Any]] = []

    def record_execution(self, policy_id: str, trace: List[Dict[str, Any]], metrics: Dict[str, float]):
        self.executions.append({
            "policy_id": policy_id,
            "trace": trace,
            "metrics": metrics,
            "timestamp": datetime.now()
        })

class ExperimentTracker:
    """Tracks variations of workflows to enable improvement"""
    def __init__(self):
        self.experiments: Dict[str, Any] = {}

    def log_variation(self, parent_policy_id: str, variation_id: str, change: str):
        self.experiments[variation_id] = {
            "parent": parent_policy_id,
            "change": change,
            "results": []
        }

class MetaOrchestrator:
    """
    Meta-Orchestrator

    The high-level controller that manages how the system organizes itself.
    It utilizes the StrategyLibrary and WorkflowMemory to optimize execution.
    """
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.strategy_library = StrategyLibrary()
        self.memory = WorkflowMemory()
        self.experiment_tracker = ExperimentTracker()

        # Policy for choosing strategies
        self.orchestration_policy = {
            "exploration_rate": self.config.get("exploration_rate", 0.2),
            "optimization_target": "success_rate"
        }

    async def execute_task(self, task: str, context: Dict[str, Any], core_system: Any) -> Dict[str, Any]:
        """
        Execute a task by selecting or generating a workflow policy.
        """
        # 1. Select Strategy
        policy = self.strategy_library.get_best_policy_for_task(task)

        # 2. Execute Workflow
        logger.info(f"Meta-Orchestrator using policy: {policy.name}")

        execution_trace = []
        current_node_id = policy.start_node
        success = True

        while current_node_id in policy.nodes:
            node = policy.nodes[current_node_id]
            execution_trace.append({"node": node.node_id, "type": node.node_type.value})

            # Dispatch to core system components
            try:
                node_result = await self._execute_node(node, task, context, core_system)
            except Exception as e:
                logger.error(f"Error executing node {node.node_id}: {e}")
                node_result = {"success": False, "error": str(e)}

            execution_trace[-1]["result"] = node_result

            if not node_result.get("success", False):
                if node.node_type != WorkflowNodeType.RETRY:
                    success = False
                    # Don't break here if we want to allow partial success or fallback
                    # For now, break as per original logic
                    break

            # Determine next node
            if node.next_nodes:
                current_node_id = node.next_nodes[0] # Simplified logic
            else:
                break

        # 3. Record and Learn
        metrics = {"success": success, "steps": len(execution_trace)}
        self.memory.record_execution(policy.policy_id, execution_trace, metrics)

        # Update policy metrics (simple moving average)
        policy.usage_count += 1
        alpha = 0.1
        policy.performance_metrics["success_rate"] = (
            (1-alpha) * policy.performance_metrics["success_rate"] + alpha * (1.0 if success else 0.0)
        )

        return {
            "success": success,
            "policy_id": policy.policy_id,
            "trace": execution_trace,
            "metrics": metrics
        }

    async def _execute_node(self, node: WorkflowNode, task: str, context: Dict[str, Any], system: Any) -> Dict[str, Any]:
        """Map workflow node to system execution"""
        from .coordination_core import TaskType, TaskPriority

        if node.node_type == WorkflowNodeType.DECOMPOSE:
            # Delegate to SelfCoordinatingCore
            # Check if coordination_core is already executing to avoid nested wait
            result = await system.coordination_core.execute_task(
                task_name=f"Decomposition: {task[:20]}",
                task_type=TaskType.PLANNING,
                description=task,
                priority=TaskPriority.MEDIUM,
                metadata=context
            )
            return result

        elif node.node_type == WorkflowNodeType.SELECT_AGENT:
            # Delegate to AgentRegistry via system
            role_name = node.config.get("role")
            if role_name:
                # Find the enum member by name
                from .agent_registry import AgentRole
                try:
                    role = AgentRole(role_name.lower())
                    agents = system.agent_registry.get_agents_by_role(role)
                    return {"success": len(agents) > 0, "agents": [a.agent_id for a in agents]}
                except ValueError:
                    return {"success": False, "error": f"Invalid role: {role_name}"}
            return {"success": False, "error": "No role specified"}

        elif node.node_type == WorkflowNodeType.CALL_TOOL:
            # Delegate to ToolRegistry via system
            tool_name = node.config.get("tool")
            tool_params = node.config.get("parameters", {})
            if tool_name:
                tool = await system.tool_registry.get_tool(tool_name)
                if tool:
                    result = await tool.execute(tool_params)
                    return result
            return {"success": False, "error": f"Tool {tool_name} not found"}

        elif node.node_type == WorkflowNodeType.VERIFY:
            # Delegate to GovernanceSystem
            # Merge context into action to allow governance to inspect parameters
            check_action = {"type": "workflow_step", "node": node.node_id}
            check_action.update(context)

            is_compliant, violations = await system.coordination_core.governance.check_compliance(
                agent_id="meta_orchestrator",
                action=check_action,
                context=context
            )
            return {"success": is_compliant, "violations": violations}

        elif node.node_type == WorkflowNodeType.CONCLUDE:
            return {"success": True, "concluded": True}

        return {"success": False, "error": f"Unknown node type {node.node_type}"}

    def evolve_strategies(self):
        """Self-scaffolding: Create new workflow variations based on performance memory"""
        # This is where the model "learns to construct its own framework"
        # In a real implementation, this would use the PolicyNetwork to propose
        # new WorkflowNode configurations.
        logger.info("Evolving orchestration strategies...")
        pass
