"""
Workflow Genome - Evolutionary Orchestration Policies

Allows the evolution of Meta-Orchestrator workflow graphs using
genetic algorithms.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from enum import Enum
import random

class WorkflowNodeType(Enum):
    DECOMPOSE = "decompose"
    SELECT_AGENT = "select_agent"
    CALL_TOOL = "call_tool"
    VERIFY = "verify"
    RETRY = "retry"
    CONCLUDE = "conclude"

@dataclass
class NodeGene:
    """Genetic representation of a Workflow Node"""
    node_id: str
    node_type: WorkflowNodeType
    config: Dict[str, Any]
    next_nodes: List[str] = field(default_factory=list)

@dataclass
class WorkflowGenome:
    """Genetic representation of a Workflow Policy"""
    genome_id: str
    nodes: Dict[str, NodeGene]
    start_node: str
    fitness: float = 0.0

class WorkflowSearchSpace:
    """Defines the search space for evolving workflows"""

    def __init__(self):
        self.node_types = list(WorkflowNodeType)
        self.roles = ["planner", "executor", "researcher", "evaluator", "optimizer", "safety"]
        self.tools = ["market_data", "trade_executor", "risk_calculator", "portfolio"]

    def create_random_genome(self, num_nodes: int = 3) -> WorkflowGenome:
        """Create a random workflow genome"""
        genome_id = str(uuid.uuid4())[:8]
        nodes = {}

        node_ids = [f"node_{i}" for i in range(num_nodes)]

        for i, node_id in enumerate(node_ids):
            node_type = random.choice(self.node_types)
            config = self._generate_random_config(node_type)

            # Connect to next node
            next_nodes = []
            if i < num_nodes - 1:
                next_nodes.append(node_ids[i+1])

            nodes[node_id] = NodeGene(node_id, node_type, config, next_nodes)

        # Ensure last node is CONCLUDE
        nodes[node_ids[-1]].node_type = WorkflowNodeType.CONCLUDE
        nodes[node_ids[-1]].next_nodes = []

        return WorkflowGenome(genome_id, nodes, node_ids[0])

    def _generate_random_config(self, node_type: WorkflowNodeType) -> Dict[str, Any]:
        if node_type == WorkflowNodeType.SELECT_AGENT:
            return {"role": random.choice(self.roles)}
        elif node_type == WorkflowNodeType.CALL_TOOL:
            return {"tool": random.choice(self.tools), "parameters": {}}
        elif node_type == WorkflowNodeType.DECOMPOSE:
            return {"depth": random.randint(1, 2)}
        elif node_type == WorkflowNodeType.VERIFY:
            return {"threshold": random.uniform(0.5, 0.9)}
        return {}

    def mutate(self, genome: WorkflowGenome) -> WorkflowGenome:
        """Mutate a workflow genome"""
        new_genome = WorkflowGenome(
            str(uuid.uuid4())[:8],
            {nid: NodeGene(n.node_id, n.node_type, n.config.copy(), n.next_nodes.copy())
             for nid, n in genome.nodes.items()},
            genome.start_node
        )

        # Select random node to mutate (excluding conclude if it's the only one)
        node_id = random.choice(list(new_genome.nodes.keys()))
        node = new_genome.nodes[node_id]

        mutation_type = random.choice(["type", "config"])

        if mutation_type == "type" and node.node_type != WorkflowNodeType.CONCLUDE:
            node.node_type = random.choice([t for t in self.node_types if t != WorkflowNodeType.CONCLUDE])
            node.config = self._generate_random_config(node.node_type)
        else:
            # Mutate config
            if node.node_type == WorkflowNodeType.SELECT_AGENT:
                node.config["role"] = random.choice(self.roles)
            elif node.node_type == WorkflowNodeType.VERIFY:
                node.config["threshold"] = min(0.99, max(0.01, node.config.get("threshold", 0.7) + random.uniform(-0.1, 0.1)))

        return new_genome
