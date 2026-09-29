"""
Swarm Intelligence - Emergent Collective Behavior System
=========================================================

Implements swarm-based AI where multiple simple agents
collectively exhibit intelligent behavior through:
- Ant Colony Optimization (ACO) for path finding
- Particle Swarm Optimization (PSO) for parameter tuning
- Bee Colony algorithms for resource allocation
- Flocking behavior for trend following
- Stigmergy for indirect communication

The swarm can self-organize, adapt, and solve complex
trading problems through emergent collective intelligence.
"""

import asyncio
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import copy

logger = logging.getLogger(__name__)


class SwarmRole(Enum):
    """Roles within the swarm"""
    SCOUT = "scout"           # Explores new opportunities
    WORKER = "worker"         # Executes known strategies
    SOLDIER = "soldier"       # Defends against losses
    QUEEN = "queen"           # Coordinates and reproduces
    DRONE = "drone"           # Supports other agents


class AgentState(Enum):
    """State of a swarm agent"""
    IDLE = "idle"
    EXPLORING = "exploring"
    EXPLOITING = "exploiting"
    COMMUNICATING = "communicating"
    RESTING = "resting"
    DEAD = "dead"


@dataclass
class Position:
    """Position in solution space"""
    dimensions: List[float]
    fitness: float = 0.0
    
    def distance_to(self, other: 'Position') -> float:
        """Calculate Euclidean distance to another position"""
        if len(self.dimensions) != len(other.dimensions):
            return float('inf')
        return math.sqrt(sum((a - b) ** 2 for a, b in zip(self.dimensions, other.dimensions)))
    
    def copy(self) -> 'Position':
        return Position(dimensions=self.dimensions.copy(), fitness=self.fitness)


@dataclass
class Pheromone:
    """Pheromone trail for stigmergic communication"""
    pheromone_id: str
    position: Position
    intensity: float
    pheromone_type: str  # "food", "danger", "opportunity"
    deposited_at: datetime = field(default_factory=datetime.utcnow)
    decay_rate: float = 0.1
    
    def decay(self, time_delta_seconds: float) -> None:
        """Decay pheromone intensity over time"""
        decay_factor = math.exp(-self.decay_rate * time_delta_seconds / 3600)
        self.intensity *= decay_factor
    
    def is_active(self) -> bool:
        """Check if pheromone is still active"""
        return self.intensity > 0.01


@dataclass
class SwarmMessage:
    """Message for swarm communication"""
    sender_id: str
    message_type: str  # "opportunity", "danger", "resource", "status"
    content: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: int = 1
    ttl: int = 10  # Time to live in iterations


class SwarmAgent(ABC):
    """Base class for swarm agents"""
    
    def __init__(self, agent_id: str, role: SwarmRole, config: Optional[Dict[str, Any]] = None):
        self.agent_id = agent_id
        self.role = role
        self.config = config or {}
        
        self.state = AgentState.IDLE
        self.position: Optional[Position] = None
        self.velocity: List[float] = []
        self.personal_best: Optional[Position] = None
        self.energy: float = 100.0
        self.age: int = 0
        self.messages: List[SwarmMessage] = []
        
        self.memory: List[Position] = []  # Visited positions
        self.max_memory = 100
    
    @abstractmethod
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive the environment"""
        pass
    
    @abstractmethod
    def decide(self, perception: Dict[str, Any]) -> str:
        """Decide on action based on perception"""
        pass
    
    @abstractmethod
    def act(self, action: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action in environment"""
        pass
    
    def update_personal_best(self) -> None:
        """Update personal best position"""
        if self.position:
            if self.personal_best is None or self.position.fitness > self.personal_best.fitness:
                self.personal_best = self.position.copy()
    
    def remember(self, position: Position) -> None:
        """Remember a visited position"""
        self.memory.append(position.copy())
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)
    
    def consume_energy(self, amount: float) -> None:
        """Consume energy for actions"""
        self.energy = max(0, self.energy - amount)
        if self.energy <= 0:
            self.state = AgentState.DEAD
    
    def rest(self, amount: float) -> None:
        """Recover energy"""
        self.energy = min(100, self.energy + amount)
    
    def receive_message(self, message: SwarmMessage) -> None:
        """Receive a message from another agent"""
        self.messages.append(message)
    
    def send_message(self, message_type: str, content: Dict[str, Any], priority: int = 1) -> SwarmMessage:
        """Create a message to send"""
        return SwarmMessage(
            sender_id=self.agent_id,
            message_type=message_type,
            content=content,
            priority=priority,
        )


class ParticleAgent(SwarmAgent):
    """Particle Swarm Optimization agent"""
    
    def __init__(self, agent_id: str, dimensions: int, bounds: List[Tuple[float, float]], config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, SwarmRole.WORKER, config)
        
        self.dimensions = dimensions
        self.bounds = bounds
        
        # PSO parameters
        self.inertia = self.config.get('inertia', 0.7)
        self.cognitive = self.config.get('cognitive', 1.5)
        self.social = self.config.get('social', 1.5)
        
        # Initialize random position and velocity
        self.position = Position(
            dimensions=[random.uniform(b[0], b[1]) for b in bounds]
        )
        self.velocity = [random.uniform(-1, 1) * (b[1] - b[0]) * 0.1 for b in bounds]
        self.personal_best = self.position.copy()
    
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive global best and neighbors"""
        return {
            'global_best': environment.get('global_best'),
            'neighbors': environment.get('neighbors', []),
            'fitness_landscape': environment.get('fitness_landscape'),
        }
    
    def decide(self, perception: Dict[str, Any]) -> str:
        """Decide movement direction"""
        if self.energy < 10:
            return "rest"
        return "move"
    
    def act(self, action: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Execute PSO movement"""
        if action == "rest":
            self.rest(20)
            return {'action': 'rest', 'position': self.position}
        
        global_best = environment.get('global_best')
        
        # Update velocity
        for i in range(self.dimensions):
            r1, r2 = random.random(), random.random()
            
            cognitive_component = self.cognitive * r1 * (self.personal_best.dimensions[i] - self.position.dimensions[i])
            social_component = 0
            if global_best:
                social_component = self.social * r2 * (global_best.dimensions[i] - self.position.dimensions[i])
            
            self.velocity[i] = self.inertia * self.velocity[i] + cognitive_component + social_component
            
            # Clamp velocity
            max_vel = (self.bounds[i][1] - self.bounds[i][0]) * 0.2
            self.velocity[i] = max(-max_vel, min(max_vel, self.velocity[i]))
        
        # Update position
        for i in range(self.dimensions):
            self.position.dimensions[i] += self.velocity[i]
            # Clamp to bounds
            self.position.dimensions[i] = max(self.bounds[i][0], min(self.bounds[i][1], self.position.dimensions[i]))
        
        self.consume_energy(1)
        self.age += 1
        
        return {'action': 'move', 'position': self.position}


class AntAgent(SwarmAgent):
    """Ant Colony Optimization agent"""
    
    def __init__(self, agent_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, SwarmRole.SCOUT, config)
        
        self.pheromone_sensitivity = self.config.get('pheromone_sensitivity', 1.0)
        self.exploration_rate = self.config.get('exploration_rate', 0.2)
        self.carrying_food = False
        self.path: List[Position] = []
    
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive pheromone trails and food sources"""
        return {
            'pheromones': environment.get('pheromones', []),
            'food_sources': environment.get('food_sources', []),
            'nest_position': environment.get('nest_position'),
        }
    
    def decide(self, perception: Dict[str, Any]) -> str:
        """Decide based on pheromone trails"""
        if self.carrying_food:
            return "return_to_nest"
        
        if random.random() < self.exploration_rate:
            return "explore"
        
        pheromones = perception.get('pheromones', [])
        if pheromones:
            return "follow_pheromone"
        
        return "explore"
    
    def act(self, action: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ant behavior"""
        result = {'action': action}
        
        if action == "explore":
            # Random walk
            if self.position:
                new_dims = [d + random.gauss(0, 0.1) for d in self.position.dimensions]
                self.position = Position(dimensions=new_dims)
            self.path.append(self.position.copy() if self.position else Position([0, 0]))
            self.consume_energy(0.5)
        
        elif action == "follow_pheromone":
            pheromones = environment.get('pheromones', [])
            if pheromones and self.position:
                # Move towards strongest pheromone
                best_pheromone = max(pheromones, key=lambda p: p.intensity)
                direction = [
                    best_pheromone.position.dimensions[i] - self.position.dimensions[i]
                    for i in range(len(self.position.dimensions))
                ]
                magnitude = math.sqrt(sum(d ** 2 for d in direction))
                if magnitude > 0:
                    step_size = 0.1
                    new_dims = [
                        self.position.dimensions[i] + direction[i] / magnitude * step_size
                        for i in range(len(self.position.dimensions))
                    ]
                    self.position = Position(dimensions=new_dims)
            self.path.append(self.position.copy() if self.position else Position([0, 0]))
            self.consume_energy(0.3)
        
        elif action == "return_to_nest":
            nest = environment.get('nest_position')
            if nest and self.position:
                # Move towards nest
                direction = [nest.dimensions[i] - self.position.dimensions[i] for i in range(len(self.position.dimensions))]
                magnitude = math.sqrt(sum(d ** 2 for d in direction))
                if magnitude > 0.1:
                    step_size = 0.15
                    new_dims = [
                        self.position.dimensions[i] + direction[i] / magnitude * step_size
                        for i in range(len(self.position.dimensions))
                    ]
                    self.position = Position(dimensions=new_dims)
                else:
                    # Reached nest
                    self.carrying_food = False
                    result['deposited_food'] = True
            self.consume_energy(0.4)
        
        self.age += 1
        result['position'] = self.position
        return result
    
    def deposit_pheromone(self, pheromone_type: str, intensity: float) -> Pheromone:
        """Deposit pheromone at current position"""
        return Pheromone(
            pheromone_id=f"pher_{self.agent_id}_{datetime.utcnow().strftime('%H%M%S%f')}",
            position=self.position.copy() if self.position else Position([0, 0]),
            intensity=intensity,
            pheromone_type=pheromone_type,
        )


class BeeAgent(SwarmAgent):
    """Bee Colony Optimization agent"""
    
    def __init__(self, agent_id: str, bee_type: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(agent_id, SwarmRole.SCOUT if bee_type == "scout" else SwarmRole.WORKER, config)
        
        self.bee_type = bee_type  # "scout", "employed", "onlooker"
        self.food_source: Optional[Position] = None
        self.trial_count = 0
        self.max_trials = self.config.get('max_trials', 10)
    
    def perceive(self, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Perceive food sources and waggle dances"""
        return {
            'food_sources': environment.get('food_sources', []),
            'waggle_dances': environment.get('waggle_dances', []),
            'hive_position': environment.get('hive_position'),
        }
    
    def decide(self, perception: Dict[str, Any]) -> str:
        """Decide based on bee type and perception"""
        if self.bee_type == "scout":
            return "explore"
        elif self.bee_type == "employed":
            if self.food_source and self.trial_count < self.max_trials:
                return "exploit"
            return "abandon"
        else:  # onlooker
            waggle_dances = perception.get('waggle_dances', [])
            if waggle_dances:
                return "follow_dance"
            return "wait"
    
    def act(self, action: str, environment: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bee behavior"""
        result = {'action': action}
        
        if action == "explore":
            # Random search for new food source
            if self.position:
                new_dims = [d + random.gauss(0, 0.5) for d in self.position.dimensions]
                self.position = Position(dimensions=new_dims)
            self.consume_energy(1)
        
        elif action == "exploit":
            # Local search around food source
            if self.food_source:
                perturbation = [random.gauss(0, 0.1) for _ in self.food_source.dimensions]
                new_dims = [self.food_source.dimensions[i] + perturbation[i] for i in range(len(self.food_source.dimensions))]
                new_pos = Position(dimensions=new_dims)
                
                # Greedy selection
                if new_pos.fitness > self.food_source.fitness:
                    self.food_source = new_pos
                    self.trial_count = 0
                else:
                    self.trial_count += 1
            self.consume_energy(0.5)
        
        elif action == "abandon":
            self.food_source = None
            self.trial_count = 0
            self.bee_type = "scout"
            result['abandoned'] = True
        
        elif action == "follow_dance":
            waggle_dances = environment.get('waggle_dances', [])
            if waggle_dances:
                # Probabilistic selection based on fitness
                total_fitness = sum(d['fitness'] for d in waggle_dances)
                if total_fitness > 0:
                    r = random.random() * total_fitness
                    cumsum = 0
                    for dance in waggle_dances:
                        cumsum += dance['fitness']
                        if cumsum >= r:
                            self.food_source = dance['position'].copy()
                            self.bee_type = "employed"
                            break
            self.consume_energy(0.2)
        
        self.age += 1
        result['position'] = self.position
        return result
    
    def waggle_dance(self) -> Dict[str, Any]:
        """Perform waggle dance to communicate food source"""
        if self.food_source:
            return {
                'dancer_id': self.agent_id,
                'position': self.food_source.copy(),
                'fitness': self.food_source.fitness,
            }
        return {}


class SwarmIntelligence:
    """
    Swarm Intelligence Coordinator
    
    Manages multiple swarm algorithms and agents for
    collective problem solving in trading.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.agents: Dict[str, SwarmAgent] = {}
        self.pheromones: List[Pheromone] = []
        self.global_best: Optional[Position] = None
        
        self.iteration = 0
        self.max_iterations = self.config.get('max_iterations', 1000)
        
        # Environment
        self.bounds = self.config.get('bounds', [(0, 1)] * 10)
        self.dimensions = len(self.bounds)
        
        # Statistics
        self.fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        
        logger.info("SwarmIntelligence initialized")
    
    def add_particle_swarm(self, num_particles: int = 30) -> None:
        """Add PSO agents to the swarm"""
        for i in range(num_particles):
            agent = ParticleAgent(
                agent_id=f"particle_{i}",
                dimensions=self.dimensions,
                bounds=self.bounds,
                config=self.config,
            )
            self.agents[agent.agent_id] = agent
        
        logger.info(f"Added {num_particles} particle agents")
    
    def add_ant_colony(self, num_ants: int = 20) -> None:
        """Add ACO agents to the swarm"""
        for i in range(num_ants):
            agent = AntAgent(
                agent_id=f"ant_{i}",
                config=self.config,
            )
            # Initialize position
            agent.position = Position(
                dimensions=[random.uniform(b[0], b[1]) for b in self.bounds]
            )
            self.agents[agent.agent_id] = agent
        
        logger.info(f"Added {num_ants} ant agents")
    
    def add_bee_colony(self, num_scouts: int = 5, num_employed: int = 15, num_onlookers: int = 10) -> None:
        """Add ABC agents to the swarm"""
        for i in range(num_scouts):
            agent = BeeAgent(f"bee_scout_{i}", "scout", self.config)
            agent.position = Position(dimensions=[random.uniform(b[0], b[1]) for b in self.bounds])
            self.agents[agent.agent_id] = agent
        
        for i in range(num_employed):
            agent = BeeAgent(f"bee_employed_{i}", "employed", self.config)
            agent.position = Position(dimensions=[random.uniform(b[0], b[1]) for b in self.bounds])
            agent.food_source = agent.position.copy()
            self.agents[agent.agent_id] = agent
        
        for i in range(num_onlookers):
            agent = BeeAgent(f"bee_onlooker_{i}", "onlooker", self.config)
            agent.position = Position(dimensions=[random.uniform(b[0], b[1]) for b in self.bounds])
            self.agents[agent.agent_id] = agent
        
        logger.info(f"Added bee colony: {num_scouts} scouts, {num_employed} employed, {num_onlookers} onlookers")
    
    def evaluate_fitness(self, fitness_func: Callable[[Position], float]) -> None:
        """Evaluate fitness for all agents"""
        for agent in self.agents.values():
            if agent.position:
                agent.position.fitness = fitness_func(agent.position)
                agent.update_personal_best()
                
                # Update global best
                if self.global_best is None or agent.position.fitness > self.global_best.fitness:
                    self.global_best = agent.position.copy()
    
    def decay_pheromones(self, time_delta: float = 1.0) -> None:
        """Decay all pheromones"""
        for pheromone in self.pheromones:
            pheromone.decay(time_delta)
        
        # Remove inactive pheromones
        self.pheromones = [p for p in self.pheromones if p.is_active()]
    
    def step(self, fitness_func: Callable[[Position], float]) -> Dict[str, Any]:
        """Execute one iteration of the swarm"""
        # Build environment
        environment = {
            'global_best': self.global_best,
            'pheromones': self.pheromones,
            'bounds': self.bounds,
            'nest_position': Position(dimensions=[0.5] * self.dimensions),
            'hive_position': Position(dimensions=[0.5] * self.dimensions),
            'waggle_dances': [],
        }
        
        # Collect waggle dances from bees
        for agent in self.agents.values():
            if isinstance(agent, BeeAgent) and agent.bee_type == "employed":
                dance = agent.waggle_dance()
                if dance:
                    environment['waggle_dances'].append(dance)
        
        # Execute agent behaviors
        results = []
        for agent in self.agents.values():
            if agent.state == AgentState.DEAD:
                continue
            
            perception = agent.perceive(environment)
            action = agent.decide(perception)
            result = agent.act(action, environment)
            results.append(result)
            
            # Ants deposit pheromones
            if isinstance(agent, AntAgent) and agent.position:
                if agent.carrying_food:
                    pheromone = agent.deposit_pheromone("food", 1.0)
                    self.pheromones.append(pheromone)
        
        # Evaluate fitness
        self.evaluate_fitness(fitness_func)
        
        # Decay pheromones
        self.decay_pheromones()
        
        # Update statistics
        if self.global_best:
            self.fitness_history.append(self.global_best.fitness)
        
        diversity = self._calculate_diversity()
        self.diversity_history.append(diversity)
        
        self.iteration += 1
        
        return {
            'iteration': self.iteration,
            'global_best_fitness': self.global_best.fitness if self.global_best else 0,
            'active_agents': len([a for a in self.agents.values() if a.state != AgentState.DEAD]),
            'pheromone_count': len(self.pheromones),
            'diversity': diversity,
        }
    
    def _calculate_diversity(self) -> float:
        """Calculate population diversity"""
        positions = [a.position for a in self.agents.values() if a.position]
        if len(positions) < 2:
            return 0.0
        
        # Average pairwise distance
        total_distance = 0
        count = 0
        for i, p1 in enumerate(positions):
            for p2 in positions[i + 1:]:
                total_distance += p1.distance_to(p2)
                count += 1
        
        return total_distance / count if count > 0 else 0.0
    
    async def optimize(self, fitness_func: Callable[[Position], float], max_iterations: Optional[int] = None) -> Position:
        """Run optimization until convergence or max iterations"""
        max_iter = max_iterations or self.max_iterations
        
        for _ in range(max_iter):
            result = self.step(fitness_func)
            
            # Check convergence
            if len(self.fitness_history) > 50:
                recent = self.fitness_history[-50:]
                if max(recent) - min(recent) < 0.001:
                    logger.info(f"Converged at iteration {self.iteration}")
                    break
            
            await asyncio.sleep(0)  # Yield control
        
        return self.global_best
    
    def get_best_solution(self) -> Optional[Position]:
        """Get the best solution found"""
        return self.global_best
    
    def get_report(self) -> Dict[str, Any]:
        """Get swarm status report"""
        agent_types = {}
        for agent in self.agents.values():
            agent_type = type(agent).__name__
            agent_types[agent_type] = agent_types.get(agent_type, 0) + 1
        
        return {
            'iteration': self.iteration,
            'total_agents': len(self.agents),
            'agent_types': agent_types,
            'active_agents': len([a for a in self.agents.values() if a.state != AgentState.DEAD]),
            'pheromone_count': len(self.pheromones),
            'global_best_fitness': self.global_best.fitness if self.global_best else None,
            'global_best_position': self.global_best.dimensions if self.global_best else None,
            'diversity': self.diversity_history[-1] if self.diversity_history else 0,
            'fitness_history': self.fitness_history[-20:],
        }


# Factory function
def create_swarm_intelligence(
    swarm_type: str = "hybrid",
    dimensions: int = 10,
    bounds: Optional[List[Tuple[float, float]]] = None,
    config: Optional[Dict[str, Any]] = None
) -> SwarmIntelligence:
    """Create and initialize swarm intelligence"""
    config = config or {}
    config['bounds'] = bounds or [(0, 1)] * dimensions
    
    swarm = SwarmIntelligence(config)
    
    if swarm_type == "pso":
        swarm.add_particle_swarm(30)
    elif swarm_type == "aco":
        swarm.add_ant_colony(20)
    elif swarm_type == "abc":
        swarm.add_bee_colony(5, 15, 10)
    elif swarm_type == "hybrid":
        swarm.add_particle_swarm(15)
        swarm.add_ant_colony(10)
        swarm.add_bee_colony(3, 8, 5)
    
    return swarm
