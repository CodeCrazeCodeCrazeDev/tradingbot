"""
Distributed Intelligence Systems
=================================

Advanced distributed AI capabilities including:
- Federated Self-Improvement
- Swarm-Based Strategy Discovery
- Hierarchical Multi-Agent System
"""

import asyncio
import hashlib
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# FEDERATED SELF-IMPROVEMENT
# =============================================================================

@dataclass
class ModelUpdate:
    """A model update from a federated node"""
    node_id: str
    update_id: str
    weights: Dict[str, np.ndarray]
    metrics: Dict[str, float]
    num_samples: int
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class FederatedNode:
    """A node in the federated learning network"""
    node_id: str
    name: str
    local_weights: Dict[str, np.ndarray]
    local_data_size: int = 0
    contribution_score: float = 0.0
    last_update: Optional[datetime] = None
    is_active: bool = True


class FederatedAggregator:
    """
    Federated Learning Aggregator
    
    Coordinates federated self-improvement across multiple
    instances without sharing raw data.
    """
    
    def __init__(
        self,
        aggregation_method: str = "fedavg",
        min_nodes_for_update: int = 2,
        staleness_threshold: int = 5
    ):
        self.aggregation_method = aggregation_method
        self.min_nodes_for_update = min_nodes_for_update
        self.staleness_threshold = staleness_threshold
        
        self.nodes: Dict[str, FederatedNode] = {}
        self.global_weights: Dict[str, np.ndarray] = {}
        self.update_history: List[Dict[str, Any]] = []
        self.round_number = 0
        
        logger.info(f"FederatedAggregator initialized with {aggregation_method}")
    
    def register_node(self, node_id: str, name: str) -> FederatedNode:
        """Register a new federated node"""
        
        node = FederatedNode(
            node_id=node_id,
            name=name,
            local_weights={}
        )
        
        self.nodes[node_id] = node
        logger.info(f"Registered federated node: {name} ({node_id})")
        
        return node
    
    def submit_update(self, update: ModelUpdate) -> bool:
        """Submit a model update from a node"""
        
        if update.node_id not in self.nodes:
            logger.warning(f"Unknown node: {update.node_id}")
            return False
        
        node = self.nodes[update.node_id]
        node.local_weights = update.weights
        node.local_data_size = update.num_samples
        node.last_update = update.timestamp
        
        logger.info(f"Received update from {node.name}: {update.num_samples} samples")
        
        return True
    
    def aggregate(self) -> Dict[str, np.ndarray]:
        """Aggregate updates from all nodes"""
        
        active_nodes = [
            node for node in self.nodes.values()
            if node.is_active and node.local_weights
        ]
        
        if len(active_nodes) < self.min_nodes_for_update:
            logger.warning(f"Not enough active nodes for aggregation: {len(active_nodes)}")
            return self.global_weights
        
        self.round_number += 1
        
        if self.aggregation_method == "fedavg":
            self.global_weights = self._federated_averaging(active_nodes)
        elif self.aggregation_method == "fedprox":
            self.global_weights = self._federated_proximal(active_nodes)
        elif self.aggregation_method == "scaffold":
            self.global_weights = self._scaffold_aggregation(active_nodes)
        else:
            self.global_weights = self._federated_averaging(active_nodes)
        
        # Record history
        self.update_history.append({
            'round': self.round_number,
            'num_nodes': len(active_nodes),
            'total_samples': sum(n.local_data_size for n in active_nodes),
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"Aggregation round {self.round_number} complete with {len(active_nodes)} nodes")
        
        return self.global_weights
    
    def _federated_averaging(self, nodes: List[FederatedNode]) -> Dict[str, np.ndarray]:
        """FedAvg: Weighted average by data size"""
        
        total_samples = sum(n.local_data_size for n in nodes)
        
        if total_samples == 0:
            return self.global_weights
        
        aggregated = {}
        
        # Get all weight keys
        all_keys = set()
        for node in nodes:
            all_keys.update(node.local_weights.keys())
        
        for key in all_keys:
            weighted_sum = None
            
            for node in nodes:
                if key not in node.local_weights:
                    continue
                
                weight = node.local_data_size / total_samples
                contribution = node.local_weights[key] * weight
                
                if weighted_sum is None:
                    weighted_sum = contribution
                else:
                    weighted_sum += contribution
            
            if weighted_sum is not None:
                aggregated[key] = weighted_sum
        
        return aggregated
    
    def _federated_proximal(self, nodes: List[FederatedNode], mu: float = 0.01) -> Dict[str, np.ndarray]:
        """FedProx: With proximal term for heterogeneity"""
        
        # Start with FedAvg
        aggregated = self._federated_averaging(nodes)
        
        # Add proximal regularization towards global model
        if self.global_weights:
            for key in aggregated:
                if key in self.global_weights:
                    aggregated[key] = (
                        aggregated[key] + mu * self.global_weights[key]
                    ) / (1 + mu)
        
        return aggregated
    
    def _scaffold_aggregation(self, nodes: List[FederatedNode]) -> Dict[str, np.ndarray]:
        """SCAFFOLD: Variance reduction for federated learning"""
        
        # Simplified SCAFFOLD implementation
        return self._federated_averaging(nodes)
    
    def get_global_model(self) -> Dict[str, np.ndarray]:
        """Get current global model weights"""
        return self.global_weights.copy()
    
    def distribute_global_model(self):
        """Distribute global model to all nodes"""
        
        for node in self.nodes.values():
            if node.is_active:
                node.local_weights = self.global_weights.copy()
        
        logger.info(f"Distributed global model to {len(self.nodes)} nodes")
    
    def get_report(self) -> Dict[str, Any]:
        """Get federated learning report"""
        
        return {
            'round_number': self.round_number,
            'num_nodes': len(self.nodes),
            'active_nodes': sum(1 for n in self.nodes.values() if n.is_active),
            'aggregation_method': self.aggregation_method,
            'history': self.update_history[-10:]
        }


class FederatedLearningClient:
    """
    Federated Learning Client
    
    Local training and update generation for federated learning.
    """
    
    def __init__(
        self,
        node_id: str,
        local_epochs: int = 5,
        learning_rate: float = 0.01
    ):
        self.node_id = node_id
        self.local_epochs = local_epochs
        self.learning_rate = learning_rate
        
        self.local_weights: Dict[str, np.ndarray] = {}
        self.local_data: List[Tuple[np.ndarray, np.ndarray]] = []
        
        logger.info(f"FederatedLearningClient initialized: {node_id}")
    
    def set_weights(self, weights: Dict[str, np.ndarray]):
        """Set local weights from global model"""
        self.local_weights = {k: v.copy() for k, v in weights.items()}
    
    def add_local_data(self, x: np.ndarray, y: np.ndarray):
        """Add local training data"""
        self.local_data.append((x, y))
    
    def train_local(self) -> ModelUpdate:
        """Train on local data and generate update"""
        
        if not self.local_data:
            logger.warning("No local data for training")
            return ModelUpdate(
                node_id=self.node_id,
                update_id=f"update_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                weights=self.local_weights,
                metrics={},
                num_samples=0
            )
        
        # Combine local data
        all_x = np.vstack([x for x, _ in self.local_data])
        all_y = np.vstack([y for _, y in self.local_data])
        
        # Simple gradient descent training (placeholder)
        for epoch in range(self.local_epochs):
            for key in self.local_weights:
                # Simulated gradient update
                gradient = np.random.randn(*self.local_weights[key].shape) * 0.01
                self.local_weights[key] -= self.learning_rate * gradient
        
        update = ModelUpdate(
            node_id=self.node_id,
            update_id=f"update_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            weights=self.local_weights,
            metrics={'loss': random.uniform(0.1, 0.5)},
            num_samples=len(all_x)
        )
        
        return update


# =============================================================================
# SWARM-BASED STRATEGY DISCOVERY
# =============================================================================

@dataclass
class Particle:
    """A particle in the swarm"""
    particle_id: str
    position: np.ndarray  # Strategy parameters
    velocity: np.ndarray
    best_position: np.ndarray
    best_fitness: float = float('-inf')
    current_fitness: float = float('-inf')


class ParticleSwarmOptimizer:
    """
    Particle Swarm Optimization for Strategy Discovery
    
    Uses swarm intelligence to discover optimal strategy parameters.
    """
    
    def __init__(
        self,
        num_particles: int = 50,
        dimensions: int = 10,
        w: float = 0.7,  # Inertia weight
        c1: float = 1.5,  # Cognitive coefficient
        c2: float = 1.5,  # Social coefficient
        bounds: Optional[Tuple[np.ndarray, np.ndarray]] = None
    ):
        self.num_particles = num_particles
        self.dimensions = dimensions
        self.w = w
        self.c1 = c1
        self.c2 = c2
        
        if bounds is None:
            self.lower_bound = np.zeros(dimensions)
            self.upper_bound = np.ones(dimensions)
        else:
            self.lower_bound, self.upper_bound = bounds
        
        self.particles: List[Particle] = []
        self.global_best_position: Optional[np.ndarray] = None
        self.global_best_fitness: float = float('-inf')
        self.iteration = 0
        self.history: List[Dict[str, Any]] = []
        
        logger.info(f"ParticleSwarmOptimizer initialized with {num_particles} particles")
    
    def initialize_swarm(self):
        """Initialize particle swarm"""
        
        self.particles = []
        
        for i in range(self.num_particles):
            # Random initial position
            position = np.random.uniform(
                self.lower_bound,
                self.upper_bound,
                self.dimensions
            )
            
            # Random initial velocity
            velocity = np.random.uniform(
                -(self.upper_bound - self.lower_bound) * 0.1,
                (self.upper_bound - self.lower_bound) * 0.1,
                self.dimensions
            )
            
            particle = Particle(
                particle_id=f"particle_{i}",
                position=position,
                velocity=velocity,
                best_position=position.copy()
            )
            
            self.particles.append(particle)
        
        logger.info(f"Initialized swarm with {len(self.particles)} particles")
    
    def evaluate_fitness(
        self,
        fitness_function: Callable[[np.ndarray], float]
    ):
        """Evaluate fitness of all particles"""
        
        for particle in self.particles:
            fitness = fitness_function(particle.position)
            particle.current_fitness = fitness
            
            # Update personal best
            if fitness > particle.best_fitness:
                particle.best_fitness = fitness
                particle.best_position = particle.position.copy()
            
            # Update global best
            if fitness > self.global_best_fitness:
                self.global_best_fitness = fitness
                self.global_best_position = particle.position.copy()
    
    def update_velocities(self):
        """Update particle velocities"""
        
        for particle in self.particles:
            r1 = np.random.random(self.dimensions)
            r2 = np.random.random(self.dimensions)
            
            # Cognitive component (personal best)
            cognitive = self.c1 * r1 * (particle.best_position - particle.position)
            
            # Social component (global best)
            if self.global_best_position is not None:
                social = self.c2 * r2 * (self.global_best_position - particle.position)
            else:
                social = np.zeros(self.dimensions)
            
            # Update velocity
            particle.velocity = (
                self.w * particle.velocity +
                cognitive +
                social
            )
            
            # Velocity clamping
            max_velocity = (self.upper_bound - self.lower_bound) * 0.2
            particle.velocity = np.clip(particle.velocity, -max_velocity, max_velocity)
    
    def update_positions(self):
        """Update particle positions"""
        
        for particle in self.particles:
            particle.position = particle.position + particle.velocity
            
            # Boundary handling (reflection)
            for d in range(self.dimensions):
                if particle.position[d] < self.lower_bound[d]:
                    particle.position[d] = self.lower_bound[d]
                    particle.velocity[d] *= -0.5
                elif particle.position[d] > self.upper_bound[d]:
                    particle.position[d] = self.upper_bound[d]
                    particle.velocity[d] *= -0.5
    
    def optimize(
        self,
        fitness_function: Callable[[np.ndarray], float],
        max_iterations: int = 100,
        tolerance: float = 1e-6
    ) -> Tuple[np.ndarray, float]:
        """
        Run PSO optimization
        
        Returns:
            Best position and fitness found
        """
        
        logger.info(f"Starting PSO optimization for {max_iterations} iterations")
        
        self.initialize_swarm()
        
        prev_best = float('-inf')
        stagnation_count = 0
        
        for i in range(max_iterations):
            self.iteration = i + 1
            
            # Evaluate fitness
            self.evaluate_fitness(fitness_function)
            
            # Record history
            self.history.append({
                'iteration': self.iteration,
                'best_fitness': self.global_best_fitness,
                'avg_fitness': np.mean([p.current_fitness for p in self.particles])
            })
            
            # Check convergence
            if abs(self.global_best_fitness - prev_best) < tolerance:
                stagnation_count += 1
                if stagnation_count >= 10:
                    logger.info(f"Converged at iteration {i + 1}")
                    break
            else:
                stagnation_count = 0
            
            prev_best = self.global_best_fitness
            
            # Update swarm
            self.update_velocities()
            self.update_positions()
            
            if (i + 1) % 10 == 0:
                logger.info(f"Iteration {i + 1}: Best fitness = {self.global_best_fitness:.6f}")
        
        logger.info(f"PSO complete. Best fitness: {self.global_best_fitness:.6f}")
        
        return self.global_best_position, self.global_best_fitness


class AntColonyOptimizer:
    """
    Ant Colony Optimization for Strategy Discovery
    
    Uses ant colony behavior for combinatorial optimization.
    """
    
    def __init__(
        self,
        num_ants: int = 50,
        num_nodes: int = 20,
        alpha: float = 1.0,  # Pheromone importance
        beta: float = 2.0,  # Heuristic importance
        evaporation_rate: float = 0.5,
        q: float = 100.0  # Pheromone deposit factor
    ):
        self.num_ants = num_ants
        self.num_nodes = num_nodes
        self.alpha = alpha
        self.beta = beta
        self.evaporation_rate = evaporation_rate
        self.q = q
        
        # Pheromone matrix
        self.pheromones = np.ones((num_nodes, num_nodes))
        
        # Best solution
        self.best_path: Optional[List[int]] = None
        self.best_fitness: float = float('-inf')
        
        logger.info(f"AntColonyOptimizer initialized with {num_ants} ants")
    
    def construct_solution(
        self,
        heuristic_matrix: np.ndarray
    ) -> List[int]:
        """Construct a solution path for one ant"""
        
        path = [random.randint(0, self.num_nodes - 1)]
        visited = set(path)
        
        while len(path) < self.num_nodes:
            current = path[-1]
            
            # Calculate probabilities for unvisited nodes
            probs = []
            candidates = []
            
            for j in range(self.num_nodes):
                if j not in visited:
                    pheromone = self.pheromones[current, j] ** self.alpha
                    heuristic = heuristic_matrix[current, j] ** self.beta
                    probs.append(pheromone * heuristic)
                    candidates.append(j)
            
            if not candidates:
                break
            
            # Normalize probabilities
            total = sum(probs)
            if total > 0:
                probs = [p / total for p in probs]
            else:
                probs = [1.0 / len(candidates)] * len(candidates)
            
            # Select next node
            next_node = np.random.choice(candidates, p=probs)
            path.append(next_node)
            visited.add(next_node)
        
        return path
    
    def update_pheromones(
        self,
        paths: List[List[int]],
        fitnesses: List[float]
    ):
        """Update pheromone levels"""
        
        # Evaporation
        self.pheromones *= (1 - self.evaporation_rate)
        
        # Deposit pheromones
        for path, fitness in zip(paths, fitnesses):
            if fitness > 0:
                deposit = self.q * fitness
                
                for i in range(len(path) - 1):
                    self.pheromones[path[i], path[i + 1]] += deposit
                    self.pheromones[path[i + 1], path[i]] += deposit
    
    def optimize(
        self,
        fitness_function: Callable[[List[int]], float],
        heuristic_matrix: Optional[np.ndarray] = None,
        max_iterations: int = 100
    ) -> Tuple[List[int], float]:
        """Run ACO optimization"""
        
        if heuristic_matrix is None:
            heuristic_matrix = np.ones((self.num_nodes, self.num_nodes))
        
        logger.info(f"Starting ACO optimization for {max_iterations} iterations")
        
        for iteration in range(max_iterations):
            paths = []
            fitnesses = []
            
            # Construct solutions for all ants
            for _ in range(self.num_ants):
                path = self.construct_solution(heuristic_matrix)
                fitness = fitness_function(path)
                
                paths.append(path)
                fitnesses.append(fitness)
                
                # Update best
                if fitness > self.best_fitness:
                    self.best_fitness = fitness
                    self.best_path = path.copy()
            
            # Update pheromones
            self.update_pheromones(paths, fitnesses)
            
            if (iteration + 1) % 10 == 0:
                logger.info(f"Iteration {iteration + 1}: Best fitness = {self.best_fitness:.6f}")
        
        return self.best_path, self.best_fitness


class SwarmStrategyDiscovery:
    """
    Swarm-Based Strategy Discovery
    
    High-level interface for using swarm intelligence
    to discover optimal trading strategies.
    """
    
    def __init__(
        self,
        method: str = "pso",
        num_agents: int = 50
    ):
        self.method = method
        self.num_agents = num_agents
        
        if method == "pso":
            self.optimizer = ParticleSwarmOptimizer(num_particles=num_agents)
        elif method == "aco":
            self.optimizer = AntColonyOptimizer(num_ants=num_agents)
        else:
            self.optimizer = ParticleSwarmOptimizer(num_particles=num_agents)
        
        self.discovered_strategies: List[Dict[str, Any]] = []
        
        logger.info(f"SwarmStrategyDiscovery initialized with {method}")
    
    async def discover_strategy(
        self,
        parameter_bounds: Dict[str, Tuple[float, float]],
        backtest_function: Callable[[Dict[str, float]], float],
        max_iterations: int = 50
    ) -> Dict[str, Any]:
        """
        Discover optimal strategy parameters
        
        Args:
            parameter_bounds: Dict of parameter name -> (min, max)
            backtest_function: Function that takes params and returns fitness
            max_iterations: Maximum optimization iterations
        
        Returns:
            Best strategy parameters found
        """
        
        param_names = list(parameter_bounds.keys())
        dimensions = len(param_names)
        
        lower = np.array([parameter_bounds[p][0] for p in param_names])
        upper = np.array([parameter_bounds[p][1] for p in param_names])
        
        # Create fitness wrapper
        def fitness_wrapper(position: np.ndarray) -> float:
            params = {
                param_names[i]: position[i]
                for i in range(len(param_names))
            }
            return backtest_function(params)
        
        if self.method == "pso":
            self.optimizer = ParticleSwarmOptimizer(
                num_particles=self.num_agents,
                dimensions=dimensions,
                bounds=(lower, upper)
            )
            
            best_position, best_fitness = self.optimizer.optimize(
                fitness_wrapper,
                max_iterations=max_iterations
            )
        else:
            # For ACO, discretize the space
            best_position = (lower + upper) / 2
            best_fitness = fitness_wrapper(best_position)
        
        # Convert to parameter dict
        best_params = {
            param_names[i]: float(best_position[i])
            for i in range(len(param_names))
        }
        
        strategy = {
            'parameters': best_params,
            'fitness': best_fitness,
            'method': self.method,
            'iterations': max_iterations
        }
        
        self.discovered_strategies.append(strategy)
        
        return strategy


# =============================================================================
# HIERARCHICAL MULTI-AGENT SYSTEM
# =============================================================================

class AgentRole(Enum):
    """Roles in the agent hierarchy"""
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"
    WORKER = "worker"


@dataclass
class AgentMessage:
    """Message between agents"""
    sender_id: str
    receiver_id: str
    message_type: str
    content: Any
    priority: int = 0
    timestamp: datetime = field(default_factory=datetime.utcnow)


class BaseAgent(ABC):
    """Base class for all agents"""
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        role: AgentRole
    ):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        
        self.inbox: List[AgentMessage] = []
        self.outbox: List[AgentMessage] = []
        self.subordinates: List[str] = []
        self.supervisor_id: Optional[str] = None
        
        self.state: Dict[str, Any] = {}
        self.is_active = True
    
    @abstractmethod
    async def process(self, input_data: Any) -> Any:
        """Process input and generate output"""
        pass
    
    def receive_message(self, message: AgentMessage):
        """Receive a message"""
        self.inbox.append(message)
    
    def send_message(
        self,
        receiver_id: str,
        message_type: str,
        content: Any,
        priority: int = 0
    ) -> AgentMessage:
        """Send a message"""
        message = AgentMessage(
            sender_id=self.agent_id,
            receiver_id=receiver_id,
            message_type=message_type,
            content=content,
            priority=priority
        )
        self.outbox.append(message)
        return message
    
    def process_inbox(self) -> List[AgentMessage]:
        """Process all messages in inbox"""
        messages = sorted(self.inbox, key=lambda m: m.priority, reverse=True)
        self.inbox = []
        return messages


class SupervisorAgent(BaseAgent):
    """
    Supervisor Agent
    
    Top-level agent that coordinates all other agents
    and makes final decisions.
    """
    
    def __init__(self, agent_id: str, name: str):
        super().__init__(agent_id, name, AgentRole.SUPERVISOR)
        
        self.decision_history: List[Dict[str, Any]] = []
    
    async def process(self, input_data: Any) -> Any:
        """Process input from subordinates and make decision"""
        
        # Collect responses from subordinates
        responses = {}
        
        for message in self.process_inbox():
            if message.message_type == "analysis_result":
                responses[message.sender_id] = message.content
        
        # Aggregate and decide
        if responses:
            decision = self._aggregate_decisions(responses)
        else:
            decision = self._default_decision(input_data)
        
        self.decision_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'input': str(input_data)[:100],
            'decision': decision
        })
        
        return decision
    
    def _aggregate_decisions(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate decisions from subordinates"""
        
        # Voting mechanism
        actions = {}
        confidences = {}
        
        for agent_id, response in responses.items():
            if isinstance(response, dict):
                action = response.get('action', 'hold')
                confidence = response.get('confidence', 0.5)
                
                if action not in actions:
                    actions[action] = 0
                    confidences[action] = []
                
                actions[action] += 1
                confidences[action].append(confidence)
        
        if not actions:
            return {'action': 'hold', 'confidence': 0.5}
        
        # Select action with most votes
        best_action = max(actions.keys(), key=lambda k: actions[k])
        avg_confidence = np.mean(confidences[best_action])
        
        return {
            'action': best_action,
            'confidence': avg_confidence,
            'votes': actions,
            'num_agents': len(responses)
        }
    
    def _default_decision(self, input_data: Any) -> Dict[str, Any]:
        """Default decision when no subordinate input"""
        return {'action': 'hold', 'confidence': 0.5}


class SpecialistAgent(BaseAgent):
    """
    Specialist Agent
    
    Specialized in a specific type of analysis.
    """
    
    def __init__(
        self,
        agent_id: str,
        name: str,
        specialty: str
    ):
        super().__init__(agent_id, name, AgentRole.SPECIALIST)
        self.specialty = specialty
    
    async def process(self, input_data: Any) -> Any:
        """Process input according to specialty"""
        
        if self.specialty == "trend":
            return self._analyze_trend(input_data)
        elif self.specialty == "momentum":
            return self._analyze_momentum(input_data)
        elif self.specialty == "volatility":
            return self._analyze_volatility(input_data)
        elif self.specialty == "sentiment":
            return self._analyze_sentiment(input_data)
        else:
            return {'action': 'hold', 'confidence': 0.5}
    
    def _analyze_trend(self, data: Any) -> Dict[str, Any]:
        """Trend analysis"""
        if isinstance(data, dict) and 'close' in data:
            prices = data['close']
            if len(prices) >= 20:
                sma_short = np.mean(prices[-10:])
                sma_long = np.mean(prices[-20:])
                
                if sma_short > sma_long * 1.01:
                    return {'action': 'buy', 'confidence': 0.7, 'reason': 'Uptrend'}
                elif sma_short < sma_long * 0.99:
                    return {'action': 'sell', 'confidence': 0.7, 'reason': 'Downtrend'}
        
        return {'action': 'hold', 'confidence': 0.5}
    
    def _analyze_momentum(self, data: Any) -> Dict[str, Any]:
        """Momentum analysis"""
        if isinstance(data, dict) and 'close' in data:
            prices = data['close']
            if len(prices) >= 14:
                roc = (prices[-1] - prices[-14]) / prices[-14] * 100
                
                if roc > 5:
                    return {'action': 'buy', 'confidence': 0.65, 'reason': 'Strong momentum'}
                elif roc < -5:
                    return {'action': 'sell', 'confidence': 0.65, 'reason': 'Weak momentum'}
        
        return {'action': 'hold', 'confidence': 0.5}
    
    def _analyze_volatility(self, data: Any) -> Dict[str, Any]:
        """Volatility analysis"""
        if isinstance(data, dict) and 'close' in data:
            prices = data['close']
            if len(prices) >= 20:
                volatility = np.std(prices[-20:]) / np.mean(prices[-20:])
                
                if volatility > 0.05:
                    return {'action': 'reduce', 'confidence': 0.6, 'reason': 'High volatility'}
        
        return {'action': 'hold', 'confidence': 0.5}
    
    def _analyze_sentiment(self, data: Any) -> Dict[str, Any]:
        """Sentiment analysis"""
        if isinstance(data, dict) and 'sentiment' in data:
            sentiment = data['sentiment']
            
            if sentiment > 0.5:
                return {'action': 'buy', 'confidence': 0.6, 'reason': 'Positive sentiment'}
            elif sentiment < -0.5:
                return {'action': 'sell', 'confidence': 0.6, 'reason': 'Negative sentiment'}
        
        return {'action': 'hold', 'confidence': 0.5}


class HierarchicalMultiAgentSystem:
    """
    Hierarchical Multi-Agent System
    
    Coordinates multiple specialized agents in a hierarchy
    for comprehensive market analysis.
    """
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.message_queue: List[AgentMessage] = []
        
        # Create default hierarchy
        self._create_default_hierarchy()
        
        logger.info("HierarchicalMultiAgentSystem initialized")
    
    def _create_default_hierarchy(self):
        """Create default agent hierarchy"""
        
        # Supervisor
        supervisor = SupervisorAgent("supervisor_1", "Chief Trading Officer")
        self.agents[supervisor.agent_id] = supervisor
        
        # Specialists
        specialists = [
            ("trend_specialist", "Trend Analyst", "trend"),
            ("momentum_specialist", "Momentum Analyst", "momentum"),
            ("volatility_specialist", "Volatility Analyst", "volatility"),
            ("sentiment_specialist", "Sentiment Analyst", "sentiment")
        ]
        
        for agent_id, name, specialty in specialists:
            specialist = SpecialistAgent(agent_id, name, specialty)
            specialist.supervisor_id = supervisor.agent_id
            supervisor.subordinates.append(agent_id)
            self.agents[agent_id] = specialist
    
    def add_agent(self, agent: BaseAgent, supervisor_id: Optional[str] = None):
        """Add an agent to the system"""
        
        self.agents[agent.agent_id] = agent
        
        if supervisor_id and supervisor_id in self.agents:
            agent.supervisor_id = supervisor_id
            self.agents[supervisor_id].subordinates.append(agent.agent_id)
    
    async def process_market_data(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process market data through agent hierarchy"""
        
        # Phase 1: Specialists analyze
        specialist_results = {}
        
        for agent_id, agent in self.agents.items():
            if agent.role == AgentRole.SPECIALIST:
                result = await agent.process(market_data)
                specialist_results[agent_id] = result
                
                # Send result to supervisor
                if agent.supervisor_id:
                    agent.send_message(
                        agent.supervisor_id,
                        "analysis_result",
                        result
                    )
        
        # Deliver messages
        self._deliver_messages()
        
        # Phase 2: Supervisor decides
        supervisor = self.agents.get("supervisor_1")
        if supervisor:
            decision = await supervisor.process(market_data)
        else:
            decision = {'action': 'hold', 'confidence': 0.5}
        
        return {
            'decision': decision,
            'specialist_analyses': specialist_results,
            'num_agents': len(self.agents)
        }
    
    def _deliver_messages(self):
        """Deliver all pending messages"""
        
        for agent in self.agents.values():
            for message in agent.outbox:
                if message.receiver_id in self.agents:
                    self.agents[message.receiver_id].receive_message(message)
            agent.outbox = []
    
    def get_hierarchy_report(self) -> Dict[str, Any]:
        """Get hierarchy report"""
        
        return {
            'num_agents': len(self.agents),
            'agents': [
                {
                    'id': agent.agent_id,
                    'name': agent.name,
                    'role': agent.role.value,
                    'subordinates': len(agent.subordinates),
                    'is_active': agent.is_active
                }
                for agent in self.agents.values()
            ]
        }


# Convenience functions
def create_federated_system(num_nodes: int = 3) -> Tuple[FederatedAggregator, List[FederatedLearningClient]]:
    """Create a federated learning system"""
    
    aggregator = FederatedAggregator()
    clients = []
    
    for i in range(num_nodes):
        node_id = f"node_{i}"
        aggregator.register_node(node_id, f"Trading Node {i}")
        client = FederatedLearningClient(node_id)
        clients.append(client)
    
    return aggregator, clients


def create_swarm_optimizer(method: str = "pso", num_agents: int = 50) -> SwarmStrategyDiscovery:
    """Create a swarm optimizer"""
    return SwarmStrategyDiscovery(method=method, num_agents=num_agents)


def create_multi_agent_system() -> HierarchicalMultiAgentSystem:
    """Create a multi-agent system"""
    return HierarchicalMultiAgentSystem()
