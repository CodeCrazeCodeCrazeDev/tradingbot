"""
Experiment Database - ASI-Evolve Persistent Memory
==============================================

Persistent storage of all experiments with structured metadata.
Supports multiple sampling policies: UCB1, greedy, random, MAP-Elites.

Based on ASI-Evolve paper: "stores the outcome of each evolution round and supplies the sampled nodes that form the Researcher's context"
"""

import asyncio
import logging
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class ExperimentStatus(Enum):
    """Experiment lifecycle status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ANALYZED = "analyzed"


@dataclass
class ExperimentNode:
    """Single experiment node in database"""
    id: str
    timestamp: datetime
    motivation: str
    program: str  # Generated code/experiment
    results: Dict[str, Any]  # Structured evaluation metrics
    analysis: Optional[str] = None  # Analyzer insights
    score: float  # Primary fitness score
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_id: Optional[str] = None  # For evolutionary tracking
    generation_method: str = "llm_conditional"  # How this was generated
    validation_stats: Dict[str, Any] = field(default_factory=dict)  # Validation gate results
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'motivation': self.motivation,
            'program': self.program,
            'results': self.results,
            'analysis': self.analysis,
            'score': self.score,
            'metadata': self.metadata,
            'parent_id': self.parent_id,
            'generation_method': self.generation_method,
            'validation_stats': self.validation_stats,
        }


class ExperimentDatabase:
    """
    ASI-Evolve Experiment Database with sampling policies.
    
    Maintains complete history of all experiments for context sampling.
    """
    
    def __init__(self):
        self.nodes: Dict[str, ExperimentNode] = {}
        self.sampling_algorithm = "ucb1"  # Default sampling policy
        logger.info("Experiment Database initialized")
    
    def add_node(self, node: ExperimentNode):
        """Add experiment node to database"""
        self.nodes[node.id] = node
        logger.info(f"Added experiment node: {node.id}")
    
    def sample_nodes(self, sample_n: int = 5, algorithm: str = "ucb1") -> List[ExperimentNode]:
        """Sample nodes using specified algorithm"""
        if not self.nodes:
            return []
        
        available_nodes = list(self.nodes.values())
        
        if algorithm == "ucb1":
            # Upper Confidence Bound sampling
            scored_nodes = []
            for node in available_nodes:
                # UCB1 score: avg_score + exploration_bonus / sqrt(visits)
                visits = sum(1 for n in self.nodes.values() if n.parent_id == node.id)
                exploration_bonus = 1.0 / np.sqrt(visits + 1)
                confidence = node.score + exploration_bonus
                scored_nodes.append((confidence, node))
            
            scored_nodes.sort(key=lambda x: x[0], reverse=True)
            return [node for _, node in scored_nodes[:sample_n]]
        
        elif algorithm == "greedy":
            # Select top performing nodes
            sorted_nodes = sorted(available_nodes, key=lambda n: n.score, reverse=True)
            return sorted_nodes[:sample_n]
        
        elif algorithm == "random":
            # Random sampling
            import random
            return random.sample(available_nodes, min(sample_n, len(available_nodes)))
        
        elif algorithm == "map_elites":
            # MAP-Elites island sampling
            # Simple implementation: divide by score ranges
            high_score = max([n.score for n in available_nodes]) if available_nodes else 0
            low_score = min([n.score for n in available_nodes]) if available_nodes else 0
            
            elite_nodes = [n for n in available_nodes if n.score >= (high_score + low_score) / 2]
            return random.sample(elite_nodes, min(sample_n, len(elite_nodes)))
        
        else:
            # Default to random
            return self.sample_nodes(sample_n, "random")
    
    def get_node(self, node_id: str) -> Optional[ExperimentNode]:
        """Get node by ID"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[ExperimentNode]:
        """Get all nodes"""
        return list(self.nodes.values())
    
    def get_nodes_by_score_range(self, min_score: float, max_score: float) -> List[ExperimentNode]:
        """Get nodes within score range"""
        return [n for n in self.nodes.values() if min_score <= n.score <= max_score]
    
    def update_node_score(self, node_id: str, new_score: float):
        """Update node score"""
        if node_id in self.nodes:
            self.nodes[node_id].score = new_score
            logger.info(f"Updated node {node_id} score to {new_score}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics"""
        if not self.nodes:
            return {'total_nodes': 0, 'avg_score': 0.0, 'sampling_algorithm': self.sampling_algorithm}
        
        scores = [n.score for n in self.nodes.values()]
        total_nodes = len(self.nodes)
        avg_score = sum(scores) / total_nodes if total_nodes > 0 else 0.0
        
        return {
            'total_nodes': total_nodes,
            'avg_score': avg_score,
            'sampling_algorithm': self.sampling_algorithm,
            'score_distribution': {
                'min': min(scores) if scores else 0.0,
                'max': max(scores) if scores else 0.0,
                'median': sorted(scores)[len(scores)//2] if scores else 0.0,
            }
        }
