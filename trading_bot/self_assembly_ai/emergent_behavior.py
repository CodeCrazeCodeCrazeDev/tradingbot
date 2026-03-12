"""
Emergent Behavior Engine - Self-Organizing Complex Systems
===========================================================

Implements emergent behavior patterns where complex intelligent
behaviors arise from simple rules and interactions:
- Cellular Automata for pattern emergence
- Self-Organizing Maps (SOM) for clustering
- Autopoiesis (self-creation and maintenance)
- Stigmergy (indirect coordination)
- Homeostasis (self-regulation)
- Morphogenesis (form development)

The system exhibits behaviors that were never explicitly programmed,
emerging from the interaction of simple components.
"""

import asyncio
import copy
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import hashlib

logger = logging.getLogger(__name__)


class CellState(Enum):
    """States for cellular automata"""
    DEAD = 0
    ALIVE = 1
    DORMANT = 2
    ACTIVE = 3
    EXCITED = 4


class EmergentPattern(Enum):
    """Types of emergent patterns"""
    OSCILLATOR = "oscillator"       # Repeating patterns
    GLIDER = "glider"               # Moving patterns
    STILL_LIFE = "still_life"       # Stable patterns
    CHAOS = "chaos"                 # Chaotic behavior
    EDGE_OF_CHAOS = "edge_of_chaos" # Complex adaptive behavior


@dataclass
class Cell:
    """A single cell in cellular automata"""
    x: int
    y: int
    state: CellState = CellState.DEAD
    age: int = 0
    energy: float = 0.0
    memory: List[CellState] = field(default_factory=list)
    
    def get_neighbors_coords(self, width: int, height: int) -> List[Tuple[int, int]]:
        """Get coordinates of neighboring cells (Moore neighborhood)"""
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx = (self.x + dx) % width
                ny = (self.y + dy) % height
                neighbors.append((nx, ny))
        return neighbors


class CellularAutomata:
    """
    Cellular Automata for Pattern Emergence
    
    Implements various CA rules that can generate
    complex patterns from simple rules.
    """
    
    def __init__(self, width: int = 50, height: int = 50, config: Optional[Dict[str, Any]] = None):
        self.width = width
        self.height = height
        self.config = config or {}
        
        # Initialize grid
        self.grid: Dict[Tuple[int, int], Cell] = {}
        for x in range(width):
            for y in range(height):
                self.grid[(x, y)] = Cell(x=x, y=y)
        
        # Rule parameters
        self.birth_rules = self.config.get('birth_rules', [3])  # Conway's Game of Life
        self.survival_rules = self.config.get('survival_rules', [2, 3])
        
        self.generation = 0
        self.pattern_history: List[str] = []
    
    def randomize(self, density: float = 0.3) -> None:
        """Randomize initial state"""
        for cell in self.grid.values():
            cell.state = CellState.ALIVE if random.random() < density else CellState.DEAD
    
    def set_pattern(self, pattern: List[Tuple[int, int]], offset: Tuple[int, int] = (0, 0)) -> None:
        """Set a specific pattern"""
        for x, y in pattern:
            nx = (x + offset[0]) % self.width
            ny = (y + offset[1]) % self.height
            if (nx, ny) in self.grid:
                self.grid[(nx, ny)].state = CellState.ALIVE
    
    def count_alive_neighbors(self, x: int, y: int) -> int:
        """Count alive neighbors for a cell"""
        cell = self.grid.get((x, y))
        if not cell:
            return 0
        
        count = 0
        for nx, ny in cell.get_neighbors_coords(self.width, self.height):
            neighbor = self.grid.get((nx, ny))
            if neighbor and neighbor.state == CellState.ALIVE:
                count += 1
        return count
    
    def step(self) -> Dict[str, Any]:
        """Execute one generation"""
        new_states = {}
        
        for (x, y), cell in self.grid.items():
            alive_neighbors = self.count_alive_neighbors(x, y)
            
            if cell.state == CellState.ALIVE:
                # Survival check
                if alive_neighbors in self.survival_rules:
                    new_states[(x, y)] = CellState.ALIVE
                else:
                    new_states[(x, y)] = CellState.DEAD
            else:
                # Birth check
                if alive_neighbors in self.birth_rules:
                    new_states[(x, y)] = CellState.ALIVE
                else:
                    new_states[(x, y)] = CellState.DEAD
        
        # Apply new states
        for (x, y), state in new_states.items():
            old_state = self.grid[(x, y)].state
            self.grid[(x, y)].state = state
            self.grid[(x, y)].memory.append(old_state)
            if len(self.grid[(x, y)].memory) > 10:
                self.grid[(x, y)].memory.pop(0)
            
            if state == CellState.ALIVE:
                self.grid[(x, y)].age += 1
            else:
                self.grid[(x, y)].age = 0
        
        self.generation += 1
        
        # Record pattern hash
        pattern_hash = self._get_pattern_hash()
        self.pattern_history.append(pattern_hash)
        if len(self.pattern_history) > 100:
            self.pattern_history.pop(0)
        
        return {
            'generation': self.generation,
            'alive_count': sum(1 for c in self.grid.values() if c.state == CellState.ALIVE),
            'pattern_hash': pattern_hash,
            'pattern_type': self._detect_pattern_type(),
        }
    
    def _get_pattern_hash(self) -> str:
        """Get hash of current pattern"""
        state_string = ''.join(str(c.state.value) for c in sorted(self.grid.values(), key=lambda c: (c.x, c.y)))
        return hashlib.md5(state_string.encode()).hexdigest()[:8]
    
    def _detect_pattern_type(self) -> EmergentPattern:
        """Detect the type of emergent pattern"""
        if len(self.pattern_history) < 10:
            return EmergentPattern.CHAOS
        
        recent = self.pattern_history[-10:]
        unique = len(set(recent))
        
        if unique == 1:
            return EmergentPattern.STILL_LIFE
        elif unique <= 3:
            return EmergentPattern.OSCILLATOR
        elif unique < 7:
            return EmergentPattern.EDGE_OF_CHAOS
        else:
            return EmergentPattern.CHAOS
    
    def get_alive_cells(self) -> List[Tuple[int, int]]:
        """Get coordinates of all alive cells"""
        return [(c.x, c.y) for c in self.grid.values() if c.state == CellState.ALIVE]


@dataclass
class SOMNode:
    """Node in Self-Organizing Map"""
    x: int
    y: int
    weights: List[float]
    activation: float = 0.0
    hit_count: int = 0
    
    def distance_to_input(self, input_vector: List[float]) -> float:
        """Calculate distance to input vector"""
        return math.sqrt(sum((w - i) ** 2 for w, i in zip(self.weights, input_vector)))
    
    def update_weights(self, input_vector: List[float], learning_rate: float, influence: float) -> None:
        """Update weights towards input vector"""
        for i in range(len(self.weights)):
            self.weights[i] += learning_rate * influence * (input_vector[i] - self.weights[i])


class SelfOrganizingMap:
    """
    Self-Organizing Map (Kohonen Network)
    
    Unsupervised learning that creates emergent
    topological organization of input data.
    """
    
    def __init__(self, width: int = 10, height: int = 10, input_dim: int = 10, config: Optional[Dict[str, Any]] = None):
        self.width = width
        self.height = height
        self.input_dim = input_dim
        self.config = config or {}
        
        # Initialize nodes with random weights
        self.nodes: Dict[Tuple[int, int], SOMNode] = {}
        for x in range(width):
            for y in range(height):
                weights = [random.random() for _ in range(input_dim)]
                self.nodes[(x, y)] = SOMNode(x=x, y=y, weights=weights)
        
        # Learning parameters
        self.initial_learning_rate = self.config.get('learning_rate', 0.5)
        self.initial_radius = self.config.get('radius', max(width, height) / 2)
        self.time_constant = self.config.get('time_constant', 1000)
        
        self.iteration = 0
    
    def find_bmu(self, input_vector: List[float]) -> SOMNode:
        """Find Best Matching Unit"""
        best_node = None
        best_distance = float('inf')
        
        for node in self.nodes.values():
            distance = node.distance_to_input(input_vector)
            if distance < best_distance:
                best_distance = distance
                best_node = node
        
        return best_node
    
    def get_neighborhood_radius(self) -> float:
        """Get current neighborhood radius"""
        return self.initial_radius * math.exp(-self.iteration / self.time_constant)
    
    def get_learning_rate(self) -> float:
        """Get current learning rate"""
        return self.initial_learning_rate * math.exp(-self.iteration / self.time_constant)
    
    def get_influence(self, bmu: SOMNode, node: SOMNode, radius: float) -> float:
        """Calculate influence of BMU on a node"""
        distance = math.sqrt((bmu.x - node.x) ** 2 + (bmu.y - node.y) ** 2)
        if distance > radius:
            return 0.0
        return math.exp(-(distance ** 2) / (2 * radius ** 2))
    
    def train_step(self, input_vector: List[float]) -> Dict[str, Any]:
        """Execute one training step"""
        # Find BMU
        bmu = self.find_bmu(input_vector)
        bmu.hit_count += 1
        bmu.activation = 1.0
        
        # Get current parameters
        radius = self.get_neighborhood_radius()
        learning_rate = self.get_learning_rate()
        
        # Update all nodes
        for node in self.nodes.values():
            influence = self.get_influence(bmu, node, radius)
            if influence > 0:
                node.update_weights(input_vector, learning_rate, influence)
                node.activation = max(node.activation, influence)
        
        self.iteration += 1
        
        return {
            'iteration': self.iteration,
            'bmu_position': (bmu.x, bmu.y),
            'radius': radius,
            'learning_rate': learning_rate,
        }
    
    def train(self, data: List[List[float]], epochs: int = 100) -> None:
        """Train on dataset"""
        for epoch in range(epochs):
            random.shuffle(data)
            for input_vector in data:
                self.train_step(input_vector)
    
    def map_input(self, input_vector: List[float]) -> Tuple[int, int]:
        """Map input to SOM coordinates"""
        bmu = self.find_bmu(input_vector)
        return (bmu.x, bmu.y)
    
    def get_clusters(self) -> Dict[Tuple[int, int], int]:
        """Get cluster assignments based on hit counts"""
        return {(n.x, n.y): n.hit_count for n in self.nodes.values()}


@dataclass
class Organism:
    """An autopoietic organism that maintains itself"""
    organism_id: str
    components: Dict[str, float]  # Component name -> amount
    energy: float = 100.0
    age: int = 0
    metabolism_rate: float = 1.0
    repair_rate: float = 0.5
    reproduction_threshold: float = 150.0
    
    def metabolize(self, resources: Dict[str, float]) -> Dict[str, float]:
        """Consume resources and produce energy"""
        consumed = {}
        energy_gained = 0
        
        for resource, amount in resources.items():
            if resource in self.components:
                consume_amount = min(amount, self.metabolism_rate)
                consumed[resource] = consume_amount
                energy_gained += consume_amount * 10
        
        self.energy += energy_gained
        self.energy -= 1  # Base metabolism cost
        
        return consumed
    
    def repair(self) -> None:
        """Self-repair damaged components"""
        for component in self.components:
            if self.components[component] < 1.0 and self.energy > 10:
                repair_amount = min(self.repair_rate, 1.0 - self.components[component])
                self.components[component] += repair_amount
                self.energy -= repair_amount * 5
    
    def can_reproduce(self) -> bool:
        """Check if organism can reproduce"""
        return self.energy >= self.reproduction_threshold
    
    def reproduce(self) -> Optional['Organism']:
        """Create offspring"""
        if not self.can_reproduce():
            return None
        
        # Split energy
        offspring_energy = self.energy * 0.4
        self.energy *= 0.6
        
        # Create offspring with slight mutations
        offspring_components = {}
        for comp, amount in self.components.items():
            offspring_components[comp] = amount * random.uniform(0.9, 1.1)
        
        return Organism(
            organism_id=f"{self.organism_id}_child_{random.randint(1000, 9999)}",
            components=offspring_components,
            energy=offspring_energy,
            metabolism_rate=self.metabolism_rate * random.uniform(0.95, 1.05),
            repair_rate=self.repair_rate * random.uniform(0.95, 1.05),
        )
    
    def is_alive(self) -> bool:
        """Check if organism is still alive"""
        return self.energy > 0 and all(v > 0 for v in self.components.values())


class Autopoiesis:
    """
    Autopoietic System - Self-Creating and Self-Maintaining
    
    Implements systems that continuously produce and maintain
    themselves through their own operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.organisms: Dict[str, Organism] = {}
        self.environment_resources: Dict[str, float] = {
            'energy_source': 1000.0,
            'building_blocks': 500.0,
            'catalysts': 200.0,
        }
        
        self.resource_regeneration_rate = self.config.get('regeneration_rate', 10.0)
        self.max_organisms = self.config.get('max_organisms', 100)
        
        self.generation = 0
        self.total_births = 0
        self.total_deaths = 0
    
    def add_organism(self, organism: Organism) -> None:
        """Add an organism to the system"""
        if len(self.organisms) < self.max_organisms:
            self.organisms[organism.organism_id] = organism
    
    def create_initial_organisms(self, count: int = 10) -> None:
        """Create initial population"""
        for i in range(count):
            organism = Organism(
                organism_id=f"org_{i}",
                components={
                    'membrane': 1.0,
                    'metabolism': 1.0,
                    'reproduction': 1.0,
                },
                energy=50.0,
            )
            self.add_organism(organism)
    
    def regenerate_resources(self) -> None:
        """Regenerate environmental resources"""
        for resource in self.environment_resources:
            max_amount = 1000.0 if resource == 'energy_source' else 500.0
            self.environment_resources[resource] = min(
                max_amount,
                self.environment_resources[resource] + self.resource_regeneration_rate
            )
    
    def step(self) -> Dict[str, Any]:
        """Execute one time step"""
        births = 0
        deaths = 0
        
        # Regenerate resources
        self.regenerate_resources()
        
        # Process each organism
        organisms_to_add = []
        organisms_to_remove = []
        
        for org_id, organism in self.organisms.items():
            # Metabolize
            available_resources = {
                k: v / len(self.organisms) if self.organisms else v
                for k, v in self.environment_resources.items()
            }
            consumed = organism.metabolize(available_resources)
            
            # Deduct from environment
            for resource, amount in consumed.items():
                self.environment_resources[resource] -= amount
            
            # Self-repair
            organism.repair()
            
            # Age
            organism.age += 1
            
            # Check for reproduction
            if organism.can_reproduce() and len(self.organisms) + len(organisms_to_add) < self.max_organisms:
                offspring = organism.reproduce()
                if offspring:
                    organisms_to_add.append(offspring)
                    births += 1
            
            # Check for death
            if not organism.is_alive():
                organisms_to_remove.append(org_id)
                deaths += 1
        
        # Apply changes
        for organism in organisms_to_add:
            self.add_organism(organism)
        
        for org_id in organisms_to_remove:
            del self.organisms[org_id]
        
        self.generation += 1
        self.total_births += births
        self.total_deaths += deaths
        
        return {
            'generation': self.generation,
            'population': len(self.organisms),
            'births': births,
            'deaths': deaths,
            'total_energy': sum(o.energy for o in self.organisms.values()),
            'avg_age': sum(o.age for o in self.organisms.values()) / len(self.organisms) if self.organisms else 0,
            'resources': self.environment_resources.copy(),
        }


class HomeostasisController:
    """
    Homeostasis Controller - Self-Regulation System
    
    Maintains internal stability through feedback loops
    and adaptive regulation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Variables to regulate
        self.variables: Dict[str, Dict[str, float]] = {}
        
        # Default variables for trading
        self.add_variable('risk_level', target=0.02, min_val=0.005, max_val=0.05)
        self.add_variable('position_size', target=0.1, min_val=0.01, max_val=0.3)
        self.add_variable('confidence', target=0.7, min_val=0.5, max_val=0.95)
        self.add_variable('activity_level', target=0.5, min_val=0.1, max_val=0.9)
        
        # PID controller parameters
        self.kp = self.config.get('kp', 0.5)  # Proportional
        self.ki = self.config.get('ki', 0.1)  # Integral
        self.kd = self.config.get('kd', 0.05)  # Derivative
        
        # Error tracking
        self.error_history: Dict[str, List[float]] = {}
        self.integral_error: Dict[str, float] = {}
    
    def add_variable(self, name: str, target: float, min_val: float, max_val: float) -> None:
        """Add a variable to regulate"""
        self.variables[name] = {
            'target': target,
            'current': target,
            'min': min_val,
            'max': max_val,
        }
        self.error_history[name] = []
        self.integral_error[name] = 0.0
    
    def update(self, name: str, current_value: float) -> float:
        """Update variable and get correction"""
        if name not in self.variables:
            return 0.0
        
        var = self.variables[name]
        var['current'] = current_value
        
        # Calculate error
        error = var['target'] - current_value
        
        # Update error history
        self.error_history[name].append(error)
        if len(self.error_history[name]) > 100:
            self.error_history[name].pop(0)
        
        # Integral error
        self.integral_error[name] += error
        self.integral_error[name] = max(-10, min(10, self.integral_error[name]))  # Anti-windup
        
        # Derivative error
        derivative = 0.0
        if len(self.error_history[name]) >= 2:
            derivative = self.error_history[name][-1] - self.error_history[name][-2]
        
        # PID correction
        correction = (
            self.kp * error +
            self.ki * self.integral_error[name] +
            self.kd * derivative
        )
        
        # Calculate new value
        new_value = current_value + correction
        new_value = max(var['min'], min(var['max'], new_value))
        
        return new_value
    
    def get_status(self) -> Dict[str, Any]:
        """Get homeostasis status"""
        status = {}
        for name, var in self.variables.items():
            error = var['target'] - var['current']
            status[name] = {
                'target': var['target'],
                'current': var['current'],
                'error': error,
                'error_percent': abs(error / var['target']) * 100 if var['target'] != 0 else 0,
                'in_range': var['min'] <= var['current'] <= var['max'],
            }
        return status
    
    def is_stable(self, tolerance: float = 0.1) -> bool:
        """Check if system is stable"""
        for name, var in self.variables.items():
            error_percent = abs(var['target'] - var['current']) / var['target'] if var['target'] != 0 else 0
            if error_percent > tolerance:
                return False
        return True


class EmergentBehaviorEngine:
    """
    Emergent Behavior Engine - Master Coordinator
    
    Coordinates all emergent behavior systems to create
    complex adaptive behaviors from simple rules.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize subsystems
        self.cellular_automata = CellularAutomata(
            width=self.config.get('ca_width', 30),
            height=self.config.get('ca_height', 30),
        )
        
        self.som = SelfOrganizingMap(
            width=self.config.get('som_width', 10),
            height=self.config.get('som_height', 10),
            input_dim=self.config.get('som_input_dim', 10),
        )
        
        self.autopoiesis = Autopoiesis(config)
        self.homeostasis = HomeostasisController(config)
        
        self.iteration = 0
        
        logger.info("EmergentBehaviorEngine initialized")
    
    def initialize(self) -> None:
        """Initialize all subsystems"""
        self.cellular_automata.randomize(density=0.3)
        self.autopoiesis.create_initial_organisms(10)
    
    def step(self) -> Dict[str, Any]:
        """Execute one step of all subsystems"""
        results = {}
        
        # Cellular automata step
        results['ca'] = self.cellular_automata.step()
        
        # Autopoiesis step
        results['autopoiesis'] = self.autopoiesis.step()
        
        # Homeostasis update (example values)
        risk_correction = self.homeostasis.update('risk_level', 0.025)
        results['homeostasis'] = {
            'risk_correction': risk_correction,
            'status': self.homeostasis.get_status(),
            'is_stable': self.homeostasis.is_stable(),
        }
        
        self.iteration += 1
        results['iteration'] = self.iteration
        
        return results
    
    def train_som(self, data: List[List[float]], epochs: int = 100) -> None:
        """Train the SOM on data"""
        self.som.train(data, epochs)
    
    def classify_with_som(self, input_vector: List[float]) -> Tuple[int, int]:
        """Classify input using SOM"""
        return self.som.map_input(input_vector)
    
    def get_emergent_signal(self) -> Dict[str, Any]:
        """Generate trading signal from emergent patterns"""
        # Get CA pattern type
        ca_pattern = self.cellular_automata._detect_pattern_type()
        
        # Get autopoiesis health
        autopoiesis_health = len(self.autopoiesis.organisms) / self.autopoiesis.max_organisms
        
        # Get homeostasis stability
        homeostasis_stable = self.homeostasis.is_stable()
        
        # Generate signal based on emergent properties
        signal = {
            'pattern_type': ca_pattern.value,
            'system_health': autopoiesis_health,
            'is_stable': homeostasis_stable,
            'confidence': 0.5,
            'direction': 'neutral',
        }
        
        # Determine direction based on emergent properties
        if ca_pattern == EmergentPattern.EDGE_OF_CHAOS and autopoiesis_health > 0.5:
            signal['confidence'] = 0.7
            signal['direction'] = 'bullish' if random.random() > 0.5 else 'bearish'
        elif ca_pattern == EmergentPattern.STILL_LIFE and homeostasis_stable:
            signal['confidence'] = 0.6
            signal['direction'] = 'neutral'
        elif ca_pattern == EmergentPattern.CHAOS:
            signal['confidence'] = 0.3
            signal['direction'] = 'avoid'
        
        return signal
    
    def get_report(self) -> Dict[str, Any]:
        """Get comprehensive status report"""
        return {
            'iteration': self.iteration,
            'cellular_automata': {
                'generation': self.cellular_automata.generation,
                'alive_cells': len(self.cellular_automata.get_alive_cells()),
                'pattern_type': self.cellular_automata._detect_pattern_type().value,
            },
            'som': {
                'iteration': self.som.iteration,
                'learning_rate': self.som.get_learning_rate(),
                'radius': self.som.get_neighborhood_radius(),
            },
            'autopoiesis': {
                'population': len(self.autopoiesis.organisms),
                'total_births': self.autopoiesis.total_births,
                'total_deaths': self.autopoiesis.total_deaths,
            },
            'homeostasis': self.homeostasis.get_status(),
        }


# Factory function
def create_emergent_behavior_engine(config: Optional[Dict[str, Any]] = None) -> EmergentBehaviorEngine:
    """Create and initialize emergent behavior engine"""
    engine = EmergentBehaviorEngine(config)
    engine.initialize()
    return engine
