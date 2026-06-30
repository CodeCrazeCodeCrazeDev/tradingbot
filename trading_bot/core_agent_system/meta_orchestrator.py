"""
Meta-Orchestrator - Self-Scaffolding Research Architecture
Enhanced with basic strategy evolution.
"""

import logging
import uuid
import random
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
        default_id = "standard_analysis_v1"
        nodes = {
            "start": WorkflowNode("start", WorkflowNodeType.DECOMPOSE, {"depth": 1}, ["end"]),
            "end": WorkflowNode("end", WorkflowNodeType.CONCLUDE, {})
        }
        self.policies[default_id] = WorkflowPolicy(
            default_id, "Standard Analysis", "Standard sequential analysis workflow",
            nodes, "start"
        )
        # Force initial success rate to allow selection
        self.policies[default_id].performance_metrics["success_rate"] = 0.5

    def add_policy(self, policy: WorkflowPolicy):
        self.policies[policy.policy_id] = policy

    def get_best_policy_for_task(self, task_type: str) -> Optional[WorkflowPolicy]:
        """Select best policy based on historical performance"""
        if not self.policies:
            return None
        # Heuristic: return the one with highest success_rate
        return max(self.policies.values(), key=lambda p: p.performance_metrics["success_rate"])

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
    Enhanced with strategy evolution (Self-Scaffolding).
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

            try:
                node_result = await self._execute_node(node, task, context, core_system)
            except Exception as e:
                logger.error(f"Error executing node {node.node_id}: {e}")
                node_result = {"success": False, "error": str(e)}

            execution_trace[-1]["result"] = node_result

            if not node_result.get("success", False):
                if node.node_type != WorkflowNodeType.RETRY:
                    success = False
                    break

            if node.next_nodes:
                current_node_id = node.next_nodes[0]
            else:
                break

        # 3. Record and Learn
        metrics = {"success": success, "steps": len(execution_trace)}
        self.memory.record_execution(policy.policy_id, execution_trace, metrics)

        # Update policy metrics
        policy.usage_count += 1
        alpha = 0.1
        policy.performance_metrics["success_rate"] = (
            (1-alpha) * policy.performance_metrics["success_rate"] + alpha * (1.0 if success else 0.0)
        )

        # Periodic Evolution
        if policy.usage_count % 5 == 0:
            self.evolve_strategies()

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
            result = await system.coordination_core.execute_task(
                task_name=f"Decomposition: {task[:20]}",
                task_type=TaskType.PLANNING,
                description=task,
                priority=TaskPriority.MEDIUM,
                metadata=context
            )
            return result

        elif node.node_type == WorkflowNodeType.SELECT_AGENT:
            role_name = node.config.get("role")
            if role_name:
                from .agent_registry import AgentRole
                try:
                    role = AgentRole(role_name.lower())
                    agents = system.agent_registry.get_agents_by_role(role)
                    return {"success": len(agents) > 0, "agents": [a.agent_id for a in agents]}
                except ValueError:
                    return {"success": False, "error": f"Invalid role: {role_name}"}
            return {"success": False, "error": "No role specified"}

        elif node.node_type == WorkflowNodeType.CALL_TOOL:
            tool_name = node.config.get("tool")
            tool_params = node.config.get("parameters", {})
            if tool_name:
                tool = await system.tool_registry.get_tool(tool_name)
                if tool:
                    result = await tool.execute(tool_params)
                    return result
            return {"success": False, "error": f"Tool {tool_name} not found"}

        elif node.node_type == WorkflowNodeType.VERIFY:
            is_compliant, violations = await system.coordination_core.governance.check_compliance(
                agent_id="meta_orchestrator",
                action={"type": "workflow_step", "node": node.node_id},
                context=context
            )
            return {"success": is_compliant, "violations": violations}

        elif node.node_type == WorkflowNodeType.CONCLUDE:
            return {"success": True, "concluded": True}

        return {"success": False, "error": f"Unknown node type {node.node_type}"}

    def evolve_strategies(self):
        """Self-scaffolding: Create new workflow variations based on performance memory"""
        logger.info("Meta-Orchestrator: Evolving orchestration strategies...")

        # Select a parent policy to mutate
        parent_id = random.choice(list(self.strategy_library.policies.keys()))
        parent = self.strategy_library.policies[parent_id]

        # Create variation
        variation_id = f"evolved_{uuid.uuid4().hex[:6]}"
        new_nodes = {k: WorkflowNode(v.node_id, v.node_type, v.config.copy(), v.next_nodes.copy())
                     for k, v in parent.nodes.items()}

        # Simple mutation: Insert a verification step if not present
        if "verify" not in new_nodes and "start" in new_nodes:
            new_nodes["verify"] = WorkflowNode("verify", WorkflowNodeType.VERIFY, {"threshold": 0.8}, ["end"])
            new_nodes["start"].next_nodes = ["verify"]

        new_policy = WorkflowPolicy(
            variation_id, f"Evolved {parent.name}", f"Evolved variation of {parent_id}",
            new_nodes, parent.start_node
        )
        # Give it a baseline success rate to be competitive
        new_policy.performance_metrics["success_rate"] = parent.performance_metrics["success_rate"] * 0.95

        self.strategy_library.add_policy(new_policy)
        logger.info(f"New strategy scaffolded: {variation_id}")
