"""
Knowledge and Learning Systems
==============================

Advanced knowledge and learning capabilities including:
- Knowledge Graph Construction
- Continual Learning Without Forgetting
- Active Learning for Data Efficiency
- Synthetic Data Generation
"""

import hashlib
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# KNOWLEDGE GRAPH CONSTRUCTION
# =============================================================================

class EntityType(Enum):
    """Types of entities in knowledge graph"""
    ASSET = "asset"
    SECTOR = "sector"
    INDICATOR = "indicator"
    EVENT = "event"
    PATTERN = "pattern"
    STRATEGY = "strategy"
    RISK_FACTOR = "risk_factor"
    MARKET_REGIME = "market_regime"


class RelationType(Enum):
    """Types of relationships"""
    CORRELATES_WITH = "correlates_with"
    CAUSES = "causes"
    BELONGS_TO = "belongs_to"
    INDICATES = "indicates"
    PREDICTS = "predicts"
    HEDGES = "hedges"
    SIMILAR_TO = "similar_to"
    OPPOSITE_OF = "opposite_of"


@dataclass
class Entity:
    """An entity in the knowledge graph"""
    entity_id: str
    name: str
    entity_type: EntityType
    properties: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[np.ndarray] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Relation:
    """A relationship between entities"""
    relation_id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    weight: float = 1.0
    confidence: float = 1.0
    properties: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeGraph:
    """
    Knowledge Graph Construction
    
    Builds and maintains a knowledge graph of market
    entities and their relationships.
    """
    
    def __init__(self, embedding_dim: int = 64):
        self.embedding_dim = embedding_dim
        
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, Relation] = {}
        
        # Adjacency lists for efficient traversal
        self.outgoing: Dict[str, List[str]] = defaultdict(list)
        self.incoming: Dict[str, List[str]] = defaultdict(list)
        
        # Entity embeddings for similarity
        self.entity_embeddings: Dict[str, np.ndarray] = {}
        
        logger.info("KnowledgeGraph initialized")
    
    def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        properties: Dict[str, Any] = None
    ) -> Entity:
        """Add an entity to the graph"""
        
        entity_id = hashlib.sha256(
            f"{name}:{entity_type.value}".encode()
        ).hexdigest()[:12]
        
        # Generate random embedding
        embedding = np.random.randn(self.embedding_dim)
        embedding /= np.linalg.norm(embedding)
        
        entity = Entity(
            entity_id=entity_id,
            name=name,
            entity_type=entity_type,
            properties=properties or {},
            embedding=embedding
        )
        
        self.entities[entity_id] = entity
        self.entity_embeddings[entity_id] = embedding
        
        logger.debug(f"Added entity: {name} ({entity_type.value})")
        
        return entity
    
    def add_relation(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        confidence: float = 1.0,
        properties: Dict[str, Any] = None
    ) -> Optional[Relation]:
        """Add a relationship between entities"""
        
        if source_id not in self.entities or target_id not in self.entities:
            logger.warning("Source or target entity not found")
            return None
        
        relation_id = hashlib.sha256(
            f"{source_id}:{target_id}:{relation_type.value}".encode()
        ).hexdigest()[:12]
        
        relation = Relation(
            relation_id=relation_id,
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            weight=weight,
            confidence=confidence,
            properties=properties or {}
        )
        
        self.relations[relation_id] = relation
        self.outgoing[source_id].append(relation_id)
        self.incoming[target_id].append(relation_id)
        
        return relation
    
    def get_neighbors(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None,
        direction: str = "both"
    ) -> List[Entity]:
        """Get neighboring entities"""
        
        neighbors = []
        
        if direction in ["out", "both"]:
            for rel_id in self.outgoing.get(entity_id, []):
                rel = self.relations[rel_id]
                if relation_type is None or rel.relation_type == relation_type:
                    neighbors.append(self.entities[rel.target_id])
        
        if direction in ["in", "both"]:
            for rel_id in self.incoming.get(entity_id, []):
                rel = self.relations[rel_id]
                if relation_type is None or rel.relation_type == relation_type:
                    neighbors.append(self.entities[rel.source_id])
        
        return neighbors
    
    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 5
    ) -> Optional[List[str]]:
        """Find shortest path between entities"""
        
        if source_id not in self.entities or target_id not in self.entities:
            return None
        
        # BFS
        visited = {source_id}
        queue = [(source_id, [source_id])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == target_id:
                return path
            
            if len(path) >= max_depth:
                continue
            
            for rel_id in self.outgoing.get(current, []):
                rel = self.relations[rel_id]
                if rel.target_id not in visited:
                    visited.add(rel.target_id)
                    queue.append((rel.target_id, path + [rel.target_id]))
        
        return None
    
    def find_similar_entities(
        self,
        entity_id: str,
        top_k: int = 5
    ) -> List[Tuple[Entity, float]]:
        """Find similar entities by embedding"""
        
        if entity_id not in self.entity_embeddings:
            return []
        
        query_embedding = self.entity_embeddings[entity_id]
        
        similarities = []
        for eid, embedding in self.entity_embeddings.items():
            if eid != entity_id:
                sim = np.dot(query_embedding, embedding)
                similarities.append((self.entities[eid], sim))
        
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def extract_subgraph(
        self,
        center_id: str,
        depth: int = 2
    ) -> Tuple[Dict[str, Entity], Dict[str, Relation]]:
        """Extract subgraph around an entity"""
        
        entities = {}
        relations = {}
        
        to_visit = [(center_id, 0)]
        visited = set()
        
        while to_visit:
            current_id, current_depth = to_visit.pop(0)
            
            if current_id in visited or current_depth > depth:
                continue
            
            visited.add(current_id)
            
            if current_id in self.entities:
                entities[current_id] = self.entities[current_id]
            
            # Add outgoing relations
            for rel_id in self.outgoing.get(current_id, []):
                rel = self.relations[rel_id]
                relations[rel_id] = rel
                to_visit.append((rel.target_id, current_depth + 1))
            
            # Add incoming relations
            for rel_id in self.incoming.get(current_id, []):
                rel = self.relations[rel_id]
                relations[rel_id] = rel
                to_visit.append((rel.source_id, current_depth + 1))
        
        return entities, relations
    
    def infer_relations(
        self,
        min_confidence: float = 0.5
    ) -> List[Relation]:
        """Infer new relations using graph patterns"""
        
        inferred = []
        
        # Transitivity: A->B, B->C implies A->C
        for entity_id in self.entities:
            for rel1_id in self.outgoing.get(entity_id, []):
                rel1 = self.relations[rel1_id]
                
                for rel2_id in self.outgoing.get(rel1.target_id, []):
                    rel2 = self.relations[rel2_id]
                    
                    # Check if direct relation exists
                    direct_exists = any(
                        self.relations[r].target_id == rel2.target_id
                        for r in self.outgoing.get(entity_id, [])
                    )
                    
                    if not direct_exists:
                        confidence = rel1.confidence * rel2.confidence * 0.8
                        
                        if confidence >= min_confidence:
                            new_rel = self.add_relation(
                                entity_id,
                                rel2.target_id,
                                rel1.relation_type,
                                weight=rel1.weight * rel2.weight,
                                confidence=confidence,
                                properties={"inferred": True}
                            )
                            if new_rel:
                                inferred.append(new_rel)
        
        logger.info(f"Inferred {len(inferred)} new relations")
        return inferred
    
    def query(
        self,
        entity_type: Optional[EntityType] = None,
        relation_type: Optional[RelationType] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> List[Entity]:
        """Query entities matching criteria"""
        
        results = []
        
        for entity in self.entities.values():
            if entity_type and entity.entity_type != entity_type:
                continue
            
            if properties:
                match = all(
                    entity.properties.get(k) == v
                    for k, v in properties.items()
                )
                if not match:
                    continue
            
            results.append(entity)
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get graph statistics"""
        
        return {
            'num_entities': len(self.entities),
            'num_relations': len(self.relations),
            'entity_types': {
                t.value: sum(1 for e in self.entities.values() if e.entity_type == t)
                for t in EntityType
            },
            'relation_types': {
                t.value: sum(1 for r in self.relations.values() if r.relation_type == t)
                for t in RelationType
            }
        }


# =============================================================================
# CONTINUAL LEARNING WITHOUT FORGETTING
# =============================================================================

@dataclass
class Task:
    """A learning task"""
    task_id: str
    name: str
    data: np.ndarray
    labels: np.ndarray
    importance: float = 1.0


class ElasticWeightConsolidation:
    """
    Elastic Weight Consolidation (EWC)
    
    Prevents catastrophic forgetting by protecting
    important weights from previous tasks.
    """
    
    def __init__(
        self,
        model_params: Dict[str, np.ndarray],
        lambda_ewc: float = 1000.0
    ):
        self.lambda_ewc = lambda_ewc
        
        # Store optimal parameters for each task
        self.optimal_params: Dict[str, Dict[str, np.ndarray]] = {}
        
        # Fisher information for each task
        self.fisher_info: Dict[str, Dict[str, np.ndarray]] = {}
        
        self.current_params = {k: v.copy() for k, v in model_params.items()}
        self.tasks_learned: List[str] = []
        
        logger.info("ElasticWeightConsolidation initialized")
    
    def compute_fisher_information(
        self,
        task_id: str,
        gradients: List[Dict[str, np.ndarray]]
    ):
        """Compute Fisher information matrix (diagonal approximation)"""
        
        fisher = {}
        
        for key in self.current_params:
            # Average squared gradients
            squared_grads = [g[key]**2 for g in gradients if key in g]
            
            if squared_grads:
                fisher[key] = np.mean(squared_grads, axis=0)
            else:
                fisher[key] = np.zeros_like(self.current_params[key])
        
        self.fisher_info[task_id] = fisher
        self.optimal_params[task_id] = {k: v.copy() for k, v in self.current_params.items()}
        self.tasks_learned.append(task_id)
        
        logger.info(f"Computed Fisher information for task {task_id}")
    
    def ewc_loss(self) -> float:
        """Compute EWC regularization loss"""
        
        loss = 0.0
        
        for task_id in self.tasks_learned:
            fisher = self.fisher_info[task_id]
            optimal = self.optimal_params[task_id]
            
            for key in self.current_params:
                diff = self.current_params[key] - optimal[key]
                loss += np.sum(fisher[key] * diff**2)
        
        return 0.5 * self.lambda_ewc * loss
    
    def ewc_gradient(self) -> Dict[str, np.ndarray]:
        """Compute EWC gradient for regularization"""
        
        grad = {k: np.zeros_like(v) for k, v in self.current_params.items()}
        
        for task_id in self.tasks_learned:
            fisher = self.fisher_info[task_id]
            optimal = self.optimal_params[task_id]
            
            for key in self.current_params:
                diff = self.current_params[key] - optimal[key]
                grad[key] += self.lambda_ewc * fisher[key] * diff
        
        return grad
    
    def update_params(
        self,
        task_gradient: Dict[str, np.ndarray],
        learning_rate: float = 0.01
    ):
        """Update parameters with EWC regularization"""
        
        ewc_grad = self.ewc_gradient()
        
        for key in self.current_params:
            total_grad = task_gradient.get(key, 0) + ewc_grad[key]
            self.current_params[key] -= learning_rate * total_grad


class ProgressiveNeuralNetwork:
    """
    Progressive Neural Networks
    
    Adds new columns for new tasks while keeping
    old columns frozen.
    """
    
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Columns for each task
        self.columns: List[Dict[str, np.ndarray]] = []
        
        # Lateral connections
        self.lateral_weights: List[List[np.ndarray]] = []
        
        logger.info("ProgressiveNeuralNetwork initialized")
    
    def add_column(self):
        """Add a new column for a new task"""
        
        column = {
            'W1': np.random.randn(self.input_dim, self.hidden_dim) * 0.1,
            'b1': np.zeros(self.hidden_dim),
            'W2': np.random.randn(self.hidden_dim, self.output_dim) * 0.1,
            'b2': np.zeros(self.output_dim)
        }
        
        # Lateral connections from previous columns
        laterals = []
        for _ in range(len(self.columns)):
            laterals.append(np.random.randn(self.hidden_dim, self.hidden_dim) * 0.1)
        
        self.columns.append(column)
        self.lateral_weights.append(laterals)
        
        logger.info(f"Added column {len(self.columns)}")
    
    def forward(self, x: np.ndarray, task_idx: int) -> np.ndarray:
        """Forward pass for a specific task"""
        
        if task_idx >= len(self.columns):
            raise ValueError(f"Task {task_idx} not found")
        
        # Get activations from all columns up to task_idx
        hidden_activations = []
        
        for i in range(task_idx + 1):
            col = self.columns[i]
            
            # Input to hidden
            h = x @ col['W1'] + col['b1']
            
            # Add lateral connections from previous columns
            if i > 0 and i <= task_idx:
                for j, prev_h in enumerate(hidden_activations):
                    if j < len(self.lateral_weights[i]):
                        h += prev_h @ self.lateral_weights[i][j]
            
            h = np.maximum(0, h)  # ReLU
            hidden_activations.append(h)
        
        # Output from current task column
        col = self.columns[task_idx]
        output = hidden_activations[-1] @ col['W2'] + col['b2']
        
        return output
    
    def train_task(
        self,
        task_idx: int,
        x: np.ndarray,
        y: np.ndarray,
        epochs: int = 100,
        learning_rate: float = 0.01
    ):
        """Train on a specific task"""
        
        if task_idx >= len(self.columns):
            self.add_column()
        
        col = self.columns[task_idx]
        
        for epoch in range(epochs):
            # Forward
            output = self.forward(x, task_idx)
            
            # Loss (MSE)
            loss = np.mean((output - y)**2)
            
            # Backward (simplified)
            grad_output = 2 * (output - y) / len(y)
            
            # Update only current column
            col['W2'] -= learning_rate * (self.columns[task_idx]['W1'].T @ x).T @ grad_output
            col['b2'] -= learning_rate * np.mean(grad_output, axis=0)


class ContinualLearner:
    """
    Continual Learner
    
    High-level interface for continual learning
    without catastrophic forgetting.
    """
    
    def __init__(
        self,
        method: str = "ewc",
        input_dim: int = 20,
        hidden_dim: int = 64,
        output_dim: int = 3
    ):
        self.method = method
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        
        # Initialize model parameters
        self.params = {
            'W1': np.random.randn(input_dim, hidden_dim) * 0.1,
            'b1': np.zeros(hidden_dim),
            'W2': np.random.randn(hidden_dim, output_dim) * 0.1,
            'b2': np.zeros(output_dim)
        }
        
        if method == "ewc":
            self.ewc = ElasticWeightConsolidation(self.params)
        elif method == "progressive":
            self.progressive = ProgressiveNeuralNetwork(input_dim, hidden_dim, output_dim)
        
        self.tasks_learned: List[Task] = []
        
        logger.info(f"ContinualLearner initialized with {method}")
    
    def learn_task(
        self,
        task: Task,
        epochs: int = 100,
        learning_rate: float = 0.01
    ):
        """Learn a new task without forgetting previous ones"""
        
        logger.info(f"Learning task: {task.name}")
        
        if self.method == "ewc":
            gradients = []
            
            for epoch in range(epochs):
                # Forward
                h = task.data @ self.params['W1'] + self.params['b1']
                h = np.maximum(0, h)
                output = h @ self.params['W2'] + self.params['b2']
                
                # Loss
                loss = np.mean((output - task.labels)**2)
                
                # Backward
                grad_output = 2 * (output - task.labels) / len(task.labels)
                grad_W2 = h.T @ grad_output
                grad_b2 = np.mean(grad_output, axis=0)
                
                grad_h = grad_output @ self.params['W2'].T
                grad_h = grad_h * (h > 0)
                grad_W1 = task.data.T @ grad_h
                grad_b1 = np.mean(grad_h, axis=0)
                
                task_grad = {
                    'W1': grad_W1, 'b1': grad_b1,
                    'W2': grad_W2, 'b2': grad_b2
                }
                
                gradients.append(task_grad)
                
                # Update with EWC
                self.ewc.current_params = self.params
                self.ewc.update_params(task_grad, learning_rate)
                self.params = self.ewc.current_params
            
            # Compute Fisher for this task
            self.ewc.compute_fisher_information(task.task_id, gradients[-10:])
        
        elif self.method == "progressive":
            task_idx = len(self.tasks_learned)
            self.progressive.train_task(task_idx, task.data, task.labels, epochs, learning_rate)
        
        self.tasks_learned.append(task)
        logger.info(f"Completed learning task: {task.name}")
    
    def predict(self, x: np.ndarray, task_idx: int = -1) -> np.ndarray:
        """Make predictions"""
        
        if self.method == "progressive":
            if task_idx < 0:
                task_idx = len(self.tasks_learned) - 1
            return self.progressive.forward(x, task_idx)
        else:
            h = x @ self.params['W1'] + self.params['b1']
            h = np.maximum(0, h)
            return h @ self.params['W2'] + self.params['b2']
    
    def evaluate_all_tasks(self) -> Dict[str, float]:
        """Evaluate performance on all learned tasks"""
        
        results = {}
        
        for i, task in enumerate(self.tasks_learned):
            predictions = self.predict(task.data, i)
            mse = np.mean((predictions - task.labels)**2)
            results[task.name] = mse
        
        return results


# =============================================================================
# ACTIVE LEARNING FOR DATA EFFICIENCY
# =============================================================================

class QueryStrategy(Enum):
    """Active learning query strategies"""
    UNCERTAINTY = "uncertainty"
    MARGIN = "margin"
    ENTROPY = "entropy"
    COMMITTEE = "committee"
    EXPECTED_CHANGE = "expected_change"
    DIVERSITY = "diversity"


class ActiveLearner:
    """
    Active Learning for Data Efficiency
    
    Selects most informative samples for labeling
    to minimize required training data.
    """
    
    def __init__(
        self,
        model_function: Callable[[np.ndarray], np.ndarray],
        query_strategy: QueryStrategy = QueryStrategy.UNCERTAINTY
    ):
        self.model_function = model_function
        self.query_strategy = query_strategy
        
        self.labeled_indices: Set[int] = set()
        self.query_history: List[Dict[str, Any]] = []
        
        logger.info(f"ActiveLearner initialized with {query_strategy.value}")
    
    def query(
        self,
        unlabeled_pool: np.ndarray,
        n_samples: int = 10
    ) -> List[int]:
        """Query most informative samples"""
        
        if self.query_strategy == QueryStrategy.UNCERTAINTY:
            return self._uncertainty_sampling(unlabeled_pool, n_samples)
        elif self.query_strategy == QueryStrategy.MARGIN:
            return self._margin_sampling(unlabeled_pool, n_samples)
        elif self.query_strategy == QueryStrategy.ENTROPY:
            return self._entropy_sampling(unlabeled_pool, n_samples)
        elif self.query_strategy == QueryStrategy.DIVERSITY:
            return self._diversity_sampling(unlabeled_pool, n_samples)
        else:
            return self._random_sampling(unlabeled_pool, n_samples)
    
    def _uncertainty_sampling(
        self,
        pool: np.ndarray,
        n_samples: int
    ) -> List[int]:
        """Select samples with highest prediction uncertainty"""
        
        predictions = self.model_function(pool)
        
        # Uncertainty = 1 - max probability
        if predictions.ndim > 1:
            uncertainties = 1 - np.max(predictions, axis=1)
        else:
            uncertainties = np.abs(predictions - 0.5)
        
        # Get indices of most uncertain samples
        indices = np.argsort(uncertainties)[-n_samples:]
        
        return indices.tolist()
    
    def _margin_sampling(
        self,
        pool: np.ndarray,
        n_samples: int
    ) -> List[int]:
        """Select samples with smallest margin between top predictions"""
        
        predictions = self.model_function(pool)
        
        if predictions.ndim > 1 and predictions.shape[1] > 1:
            sorted_probs = np.sort(predictions, axis=1)
            margins = sorted_probs[:, -1] - sorted_probs[:, -2]
        else:
            margins = np.abs(predictions.flatten() - 0.5)
        
        # Smallest margins = most uncertain
        indices = np.argsort(margins)[:n_samples]
        
        return indices.tolist()
    
    def _entropy_sampling(
        self,
        pool: np.ndarray,
        n_samples: int
    ) -> List[int]:
        """Select samples with highest entropy"""
        
        predictions = self.model_function(pool)
        
        if predictions.ndim > 1:
            # Clip for numerical stability
            predictions = np.clip(predictions, 1e-10, 1 - 1e-10)
            entropies = -np.sum(predictions * np.log(predictions), axis=1)
        else:
            p = np.clip(predictions.flatten(), 1e-10, 1 - 1e-10)
            entropies = -p * np.log(p) - (1-p) * np.log(1-p)
        
        indices = np.argsort(entropies)[-n_samples:]
        
        return indices.tolist()
    
    def _diversity_sampling(
        self,
        pool: np.ndarray,
        n_samples: int
    ) -> List[int]:
        """Select diverse samples using k-means++"""
        
        selected = []
        
        # Start with random sample
        first_idx = np.random.randint(len(pool))
        selected.append(first_idx)
        
        while len(selected) < n_samples:
            # Compute distances to nearest selected point
            min_distances = np.full(len(pool), np.inf)
            
            for idx in selected:
                distances = np.sum((pool - pool[idx])**2, axis=1)
                min_distances = np.minimum(min_distances, distances)
            
            # Select point with maximum distance
            probs = min_distances / min_distances.sum()
            next_idx = np.random.choice(len(pool), p=probs)
            selected.append(next_idx)
        
        return selected
    
    def _random_sampling(
        self,
        pool: np.ndarray,
        n_samples: int
    ) -> List[int]:
        """Random sampling baseline"""
        return np.random.choice(len(pool), n_samples, replace=False).tolist()
    
    def add_labeled(self, indices: List[int]):
        """Mark samples as labeled"""
        self.labeled_indices.update(indices)
        
        self.query_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'num_queried': len(indices),
            'total_labeled': len(self.labeled_indices)
        })
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get active learning statistics"""
        
        return {
            'strategy': self.query_strategy.value,
            'total_labeled': len(self.labeled_indices),
            'query_history': self.query_history[-10:]
        }


# =============================================================================
# SYNTHETIC DATA GENERATION
# =============================================================================

class SyntheticDataGenerator:
    """
    Synthetic Data Generation
    
    Generates realistic synthetic market data for
    training and augmentation.
    """
    
    def __init__(self, seed: Optional[int] = None):
        if seed:
            np.random.seed(seed)
        
        logger.info("SyntheticDataGenerator initialized")
    
    def generate_price_series(
        self,
        length: int = 1000,
        initial_price: float = 100.0,
        drift: float = 0.0001,
        volatility: float = 0.02,
        regime_changes: int = 3
    ) -> np.ndarray:
        """Generate synthetic price series with regime changes"""
        
        prices = np.zeros(length)
        prices[0] = initial_price
        
        # Regime change points
        change_points = sorted(np.random.choice(
            range(100, length - 100),
            regime_changes,
            replace=False
        ))
        change_points = [0] + list(change_points) + [length]
        
        for i in range(len(change_points) - 1):
            start = change_points[i]
            end = change_points[i + 1]
            
            # Random regime parameters
            regime_drift = drift * np.random.uniform(-2, 2)
            regime_vol = volatility * np.random.uniform(0.5, 2)
            
            for j in range(start + 1 if start > 0 else 1, end):
                returns = regime_drift + regime_vol * np.random.randn()
                prices[j] = prices[j-1] * (1 + returns)
        
        return prices
    
    def generate_ohlcv(
        self,
        length: int = 1000,
        initial_price: float = 100.0
    ) -> Dict[str, np.ndarray]:
        """Generate synthetic OHLCV data"""
        
        close = self.generate_price_series(length, initial_price)
        
        # Generate OHLC from close
        high = close * (1 + np.abs(np.random.randn(length)) * 0.01)
        low = close * (1 - np.abs(np.random.randn(length)) * 0.01)
        open_price = np.roll(close, 1)
        open_price[0] = initial_price
        
        # Ensure high >= close >= low
        high = np.maximum(high, close)
        low = np.minimum(low, close)
        
        # Generate volume
        base_volume = 1000000
        volume = base_volume * (1 + np.random.exponential(0.5, length))
        
        # Higher volume on larger moves
        price_change = np.abs(np.diff(close, prepend=close[0]))
        volume *= (1 + price_change / np.mean(price_change))
        
        return {
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }
    
    def generate_correlated_assets(
        self,
        num_assets: int = 5,
        length: int = 1000,
        correlation_matrix: Optional[np.ndarray] = None
    ) -> Dict[str, np.ndarray]:
        """Generate correlated asset returns"""
        
        if correlation_matrix is None:
            # Generate random correlation matrix
            A = np.random.randn(num_assets, num_assets)
            correlation_matrix = A @ A.T
            D = np.diag(1 / np.sqrt(np.diag(correlation_matrix)))
            correlation_matrix = D @ correlation_matrix @ D
        
        # Cholesky decomposition
        L = np.linalg.cholesky(correlation_matrix)
        
        # Generate uncorrelated returns
        uncorrelated = np.random.randn(length, num_assets) * 0.02
        
        # Apply correlation
        correlated = uncorrelated @ L.T
        
        # Convert to prices
        assets = {}
        for i in range(num_assets):
            prices = 100 * np.cumprod(1 + correlated[:, i])
            assets[f'asset_{i}'] = prices
        
        return assets
    
    def augment_data(
        self,
        data: np.ndarray,
        num_augmentations: int = 5,
        noise_level: float = 0.01
    ) -> List[np.ndarray]:
        """Augment data with variations"""
        
        augmented = []
        
        for _ in range(num_augmentations):
            # Add noise
            noisy = data + np.random.randn(*data.shape) * noise_level * np.std(data)
            
            # Random scaling
            scale = np.random.uniform(0.95, 1.05)
            scaled = noisy * scale
            
            # Random time warping (simplified)
            if len(data) > 10:
                warp_factor = np.random.uniform(0.9, 1.1)
                new_length = int(len(data) * warp_factor)
                indices = np.linspace(0, len(data) - 1, new_length).astype(int)
                warped = scaled[indices]
                
                # Resample back to original length
                final_indices = np.linspace(0, len(warped) - 1, len(data)).astype(int)
                augmented.append(warped[final_indices])
            else:
                augmented.append(scaled)
        
        return augmented
    
    def generate_labeled_data(
        self,
        num_samples: int = 1000,
        feature_dim: int = 20,
        num_classes: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Generate labeled synthetic data"""
        
        # Generate features
        features = np.random.randn(num_samples, feature_dim)
        
        # Generate labels based on feature patterns
        weights = np.random.randn(feature_dim, num_classes)
        logits = features @ weights
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits, axis=1, keepdims=True))
        probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
        
        # Sample labels
        labels = np.array([np.random.choice(num_classes, p=p) for p in probs])
        
        return features, labels


# =============================================================================
# INTEGRATED KNOWLEDGE LEARNING SYSTEM
# =============================================================================

class IntegratedKnowledgeLearningSystem:
    """
    Integrated Knowledge and Learning System
    
    Combines all knowledge and learning components.
    """
    
    def __init__(self):
        self.knowledge_graph = KnowledgeGraph()
        self.continual_learner = ContinualLearner()
        self.active_learner = None  # Initialized when model is set
        self.data_generator = SyntheticDataGenerator()
        
        logger.info("IntegratedKnowledgeLearningSystem initialized")
    
    def build_market_knowledge_graph(
        self,
        assets: List[str],
        sectors: Dict[str, List[str]],
        correlations: Dict[Tuple[str, str], float]
    ):
        """Build knowledge graph from market data"""
        
        # Add sector entities
        for sector_name in sectors:
            self.knowledge_graph.add_entity(
                sector_name,
                EntityType.SECTOR
            )
        
        # Add asset entities
        for asset in assets:
            entity = self.knowledge_graph.add_entity(
                asset,
                EntityType.ASSET
            )
            
            # Link to sector
            for sector_name, sector_assets in sectors.items():
                if asset in sector_assets:
                    sector_entity = self.knowledge_graph.query(
                        entity_type=EntityType.SECTOR,
                        properties={'name': sector_name}
                    )
                    if sector_entity:
                        self.knowledge_graph.add_relation(
                            entity.entity_id,
                            sector_entity[0].entity_id,
                            RelationType.BELONGS_TO
                        )
        
        # Add correlation relationships
        for (asset1, asset2), corr in correlations.items():
            entities1 = self.knowledge_graph.query(properties={'name': asset1})
            entities2 = self.knowledge_graph.query(properties={'name': asset2})
            
            if entities1 and entities2:
                self.knowledge_graph.add_relation(
                    entities1[0].entity_id,
                    entities2[0].entity_id,
                    RelationType.CORRELATES_WITH,
                    weight=corr
                )
        
        logger.info(f"Built knowledge graph with {len(self.knowledge_graph.entities)} entities")
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive system report"""
        
        return {
            'knowledge_graph': self.knowledge_graph.get_statistics(),
            'continual_learning': {
                'tasks_learned': len(self.continual_learner.tasks_learned),
                'method': self.continual_learner.method
            },
            'active_learning': self.active_learner.get_statistics() if self.active_learner else None
        }


# Convenience functions
def create_knowledge_learning_system() -> IntegratedKnowledgeLearningSystem:
    """Create integrated knowledge learning system"""
    return IntegratedKnowledgeLearningSystem()
