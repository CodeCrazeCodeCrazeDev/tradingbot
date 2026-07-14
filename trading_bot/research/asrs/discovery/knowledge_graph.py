import json
import os
from typing import Dict, Any, List, Optional

class ScientificKnowledgeGraph:
    """
    In-memory representation of the ASRS Scientific Knowledge Graph (SKG).
    Nodes are scientific entities (papers, algorithms, models, benchmarks)
    connected via qualitative relationships (IMPROVES, REPLACES, VALIDATES, etc.).
    """
    def __init__(self, persistence_path: str = "alphaalgo_data/scientific_knowledge_graph.json"):
        self.persistence_path = persistence_path
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.load()

    def load(self):
        if os.path.exists(self.persistence_path):
            try:
                with open(self.persistence_path, "r") as f:
                    data = json.load(f)
                    self.nodes = data.get("nodes", {})
                    self.edges = data.get("edges", [])
            except Exception:
                self.nodes = {}
                self.edges = []
        else:
            self._init_defaults()

    def save(self):
        os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
        with open(self.persistence_path, "w") as f:
            json.dump({"nodes": self.nodes, "edges": self.edges}, f, indent=2)

    def _init_defaults(self):
        # Build initial UCA V5 high-conviction paper spectrum
        self.add_node(
            node_id="paper:eksft_2026",
            label="EKSFT: Entropy and KL-Divergence Selective Fine-Tuning",
            category="PAPER",
            properties={
                "expected_roi": 0.25,
                "implementation_difficulty": 4.5,
                "compute_requirements": "GPU_MED",
                "target_domain": "calibration_masking",
                "verified_reproducible": True
            }
        )
        self.add_node(
            node_id="paper:discoloop_2026",
            label="DiscoLoop: Recurrent Agentic Reasoner Core",
            category="PAPER",
            properties={
                "expected_roi": 0.40,
                "implementation_difficulty": 6.5,
                "compute_requirements": "CPU_HIGH",
                "target_domain": "planning_depth",
                "verified_reproducible": True
            }
        )
        self.add_node(
            node_id="paper:sage_2026",
            label="SAGE: Self-Evolving Agentic Graph-Memory",
            category="PAPER",
            properties={
                "expected_roi": 0.35,
                "implementation_difficulty": 5.5,
                "compute_requirements": "CPU_MED",
                "target_domain": "memory_consolidation",
                "verified_reproducible": True
            }
        )
        self.add_node(
            node_id="module:hms_sage",
            label="HMS SAGE Graph Store",
            category="MODULE",
            properties={"active": True}
        )
        self.add_edge("paper:sage_2026", "module:hms_sage", "VALIDATES", {"confidence": 0.95})
        self.save()

    def add_node(self, node_id: str, label: str, category: str, properties: Dict[str, Any]):
        self.nodes[node_id] = {
            "id": node_id,
            "label": label,
            "category": category,
            "properties": properties
        }

    def add_edge(self, source_id: str, target_id: str, edge_type: str, metadata: Dict[str, Any]):
        self.edges.append({
            "source": source_id,
            "target": target_id,
            "type": edge_type,
            "metadata": metadata
        })

    def find_solutions_for_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Identify paper solutions in the graph matching an audited bottleneck domain."""
        solutions = []
        for node in self.nodes.values():
            if node.get("properties", {}).get("target_domain") == domain:
                solutions.append(node)
        return solutions
