"""
Idea #6: Neural Architecture Evolution
=======================================
Self-evolving neural network topologies that adapt architecture based on market conditions.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import logging
import copy

logger = logging.getLogger(__name__)


class MutationType(Enum):
    ADD_NODE = "add_node"
    REMOVE_NODE = "remove_node"
    ADD_CONNECTION = "add_connection"
    REMOVE_CONNECTION = "remove_connection"
    CHANGE_ACTIVATION = "change_activation"
    CHANGE_WEIGHT = "change_weight"
    ADD_LAYER = "add_layer"
    REMOVE_LAYER = "remove_layer"


class ActivationType(Enum):
    RELU = "relu"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    LEAKY_RELU = "leaky_relu"
    ELU = "elu"
    SWISH = "swish"
    GELU = "gelu"


@dataclass
class Gene:
    gene_id: int
    gene_type: str
    innovation_number: int
    enabled: bool = True
    
    
@dataclass
class NodeGene(Gene):
    layer: int = 0
    activation: ActivationType = ActivationType.RELU
    bias: float = 0.0


@dataclass
class ConnectionGene(Gene):
    source_node: int = 0
    target_node: int = 0
    weight: float = 1.0


@dataclass
class Genome:
    genome_id: str
    node_genes: List[NodeGene] = field(default_factory=list)
    connection_genes: List[ConnectionGene] = field(default_factory=list)
    fitness: float = 0.0
    species_id: Optional[int] = None
    generation: int = 0
    
    def copy(self) -> 'Genome':
        return Genome(
            genome_id=f"{self.genome_id}_copy",
            node_genes=[copy.deepcopy(n) for n in self.node_genes],
            connection_genes=[copy.deepcopy(c) for c in self.connection_genes],
            fitness=0.0,
            species_id=self.species_id,
            generation=self.generation + 1
        )


@dataclass
class Species:
    species_id: int
    representative: Genome
    members: List[Genome] = field(default_factory=list)
    best_fitness: float = 0.0
    stagnation_counter: int = 0
    

class NEATEvolver:
    """NEAT (NeuroEvolution of Augmenting Topologies) implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.innovation_counter = 0
        self.innovation_history: Dict[Tuple[int, int], int] = {}
        self.species: List[Species] = []
        self.population: List[Genome] = []
        
    def get_innovation_number(self, source: int, target: int) -> int:
        key = (source, target)
        if key not in self.innovation_history:
            self.innovation_history[key] = self.innovation_counter
            self.innovation_counter += 1
        return self.innovation_history[key]
    
    def create_minimal_genome(self, genome_id: str, num_inputs: int, num_outputs: int) -> Genome:
        nodes = []
        connections = []
        
        for i in range(num_inputs):
            nodes.append(NodeGene(
                gene_id=i,
                gene_type="input",
                innovation_number=i,
                layer=0,
                activation=ActivationType.RELU
            ))
        
        for i in range(num_outputs):
            nodes.append(NodeGene(
                gene_id=num_inputs + i,
                gene_type="output",
                innovation_number=num_inputs + i,
                layer=1,
                activation=ActivationType.TANH
            ))
        
        for i in range(num_inputs):
            for j in range(num_outputs):
                innovation = self.get_innovation_number(i, num_inputs + j)
                connections.append(ConnectionGene(
                    gene_id=innovation,
                    gene_type="connection",
                    innovation_number=innovation,
                    source_node=i,
                    target_node=num_inputs + j,
                    weight=np.random.randn() * 0.5
                ))
        
        return Genome(genome_id=genome_id, node_genes=nodes, connection_genes=connections)
    
    def mutate(self, genome: Genome) -> Genome:
        mutated = genome.copy()
        
        mutation_rates = self.config.get("mutation_rates", {
            "weight": 0.8,
            "add_node": 0.03,
            "add_connection": 0.05,
            "remove_connection": 0.02,
            "change_activation": 0.1
        })
        
        if np.random.random() < mutation_rates.get("weight", 0.8):
            for conn in mutated.connection_genes:
                if np.random.random() < 0.9:
                    conn.weight += np.random.randn() * 0.1
                else:
                    conn.weight = np.random.randn() * 0.5
        
        if np.random.random() < mutation_rates.get("add_node", 0.03):
            self._mutate_add_node(mutated)
        
        if np.random.random() < mutation_rates.get("add_connection", 0.05):
            self._mutate_add_connection(mutated)
        
        if np.random.random() < mutation_rates.get("change_activation", 0.1):
            hidden_nodes = [n for n in mutated.node_genes if n.gene_type == "hidden"]
            if hidden_nodes:
                node = np.random.choice(hidden_nodes)
                node.activation = np.random.choice(list(ActivationType))
        
        return mutated
    
    def _mutate_add_node(self, genome: Genome):
        enabled_connections = [c for c in genome.connection_genes if c.enabled]
        if not enabled_connections:
            return
        
        conn = np.random.choice(enabled_connections)
        conn.enabled = False
        
        new_node_id = max(n.gene_id for n in genome.node_genes) + 1
        new_node = NodeGene(
            gene_id=new_node_id,
            gene_type="hidden",
            innovation_number=self.innovation_counter,
            layer=(genome.node_genes[conn.source_node].layer + 
                   genome.node_genes[conn.target_node].layer) // 2,
            activation=np.random.choice(list(ActivationType))
        )
        self.innovation_counter += 1
        genome.node_genes.append(new_node)
        
        inn1 = self.get_innovation_number(conn.source_node, new_node_id)
        genome.connection_genes.append(ConnectionGene(
            gene_id=inn1,
            gene_type="connection",
            innovation_number=inn1,
            source_node=conn.source_node,
            target_node=new_node_id,
            weight=1.0
        ))
        
        inn2 = self.get_innovation_number(new_node_id, conn.target_node)
        genome.connection_genes.append(ConnectionGene(
            gene_id=inn2,
            gene_type="connection",
            innovation_number=inn2,
            source_node=new_node_id,
            target_node=conn.target_node,
            weight=conn.weight
        ))
    
    def _mutate_add_connection(self, genome: Genome):
        existing = {(c.source_node, c.target_node) for c in genome.connection_genes}
        
        possible = []
        for n1 in genome.node_genes:
            for n2 in genome.node_genes:
                if n1.gene_id != n2.gene_id and n1.layer < n2.layer:
                    if (n1.gene_id, n2.gene_id) not in existing:
                        possible.append((n1.gene_id, n2.gene_id))
        
        if possible:
            source, target = possible[np.random.randint(len(possible))]
            innovation = self.get_innovation_number(source, target)
            genome.connection_genes.append(ConnectionGene(
                gene_id=innovation,
                gene_type="connection",
                innovation_number=innovation,
                source_node=source,
                target_node=target,
                weight=np.random.randn() * 0.5
            ))
    
    def crossover(self, parent1: Genome, parent2: Genome) -> Genome:
        if parent1.fitness > parent2.fitness:
            fitter, weaker = parent1, parent2
        else:
            fitter, weaker = parent2, parent1
        
        child = fitter.copy()
        child.genome_id = f"child_{np.random.randint(1000000)}"
        
        weaker_innovations = {c.innovation_number: c for c in weaker.connection_genes}
        
        for i, conn in enumerate(child.connection_genes):
            if conn.innovation_number in weaker_innovations:
                if np.random.random() < 0.5:
                    child.connection_genes[i].weight = weaker_innovations[conn.innovation_number].weight
        
        return child
    
    def compute_compatibility(self, genome1: Genome, genome2: Genome) -> float:
        c1, c2, c3 = 1.0, 1.0, 0.4
        
        innovations1 = {c.innovation_number for c in genome1.connection_genes}
        innovations2 = {c.innovation_number for c in genome2.connection_genes}
        
        matching = innovations1 & innovations2
        disjoint = len((innovations1 - innovations2) | (innovations2 - innovations1))
        excess = 0
        
        if matching:
            weights1 = {c.innovation_number: c.weight for c in genome1.connection_genes}
            weights2 = {c.innovation_number: c.weight for c in genome2.connection_genes}
            weight_diff = np.mean([abs(weights1[i] - weights2[i]) for i in matching])
        else:
            weight_diff = 0
        
        n = max(len(genome1.connection_genes), len(genome2.connection_genes), 1)
        
        return (c1 * excess / n) + (c2 * disjoint / n) + (c3 * weight_diff)
    
    def speciate(self, population: List[Genome], threshold: float = 3.0):
        for genome in population:
            genome.species_id = None
        
        for species in self.species:
            species.members.clear()
        
        for genome in population:
            placed = False
            for species in self.species:
                if self.compute_compatibility(genome, species.representative) < threshold:
                    species.members.append(genome)
                    genome.species_id = species.species_id
                    placed = True
                    break
            
            if not placed:
                new_species = Species(
                    species_id=len(self.species),
                    representative=genome,
                    members=[genome]
                )
                genome.species_id = new_species.species_id
                self.species.append(new_species)
        
        self.species = [s for s in self.species if s.members]
        
        for species in self.species:
            species.representative = np.random.choice(species.members)


class NeuralArchitectureEvolver:
    """
    Neural Architecture Evolution system for trading.
    Automatically evolves network architectures based on market performance.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.neat = NEATEvolver(self.config)
        self.population_size = self.config.get("population_size", 100)
        self.num_inputs = self.config.get("num_inputs", 64)
        self.num_outputs = self.config.get("num_outputs", 3)
        self.generation = 0
        self.best_genome: Optional[Genome] = None
        self.fitness_history: List[float] = []
        self.initialized = False
        self.metrics = {
            "generations": 0,
            "best_fitness": 0.0,
            "avg_fitness": 0.0,
            "num_species": 0,
            "avg_complexity": 0.0
        }
        
    async def initialize(self):
        """Initialize the evolution system."""
        logger.info("Initializing Neural Architecture Evolver")
        
        self.neat.population = [
            self.neat.create_minimal_genome(f"genome_{i}", self.num_inputs, self.num_outputs)
            for i in range(self.population_size)
        ]
        
        self.neat.speciate(self.neat.population)
        self.initialized = True
        
    async def evaluate_population(self, fitness_function: Callable[[Genome], float]) -> List[Genome]:
        """Evaluate fitness of all genomes."""
        if not self.initialized:
            await self.initialize()
        
        for genome in self.neat.population:
            genome.fitness = fitness_function(genome)
        
        self.neat.population.sort(key=lambda g: g.fitness, reverse=True)
        self.best_genome = self.neat.population[0]
        
        self.metrics["best_fitness"] = self.best_genome.fitness
        self.metrics["avg_fitness"] = np.mean([g.fitness for g in self.neat.population])
        self.fitness_history.append(self.best_genome.fitness)
        
        return self.neat.population
    
    async def evolve_generation(self) -> Dict[str, Any]:
        """Evolve to the next generation."""
        if not self.initialized:
            await self.initialize()
        
        new_population = []
        
        if self.best_genome:
            new_population.append(self.best_genome.copy())
        
        total_fitness = sum(max(0, g.fitness) for g in self.neat.population)
        
        while len(new_population) < self.population_size:
            if np.random.random() < 0.75 and len(self.neat.species) > 0:
                species = np.random.choice(self.neat.species)
                if len(species.members) >= 2:
                    parent1, parent2 = np.random.choice(species.members, 2, replace=False)
                    child = self.neat.crossover(parent1, parent2)
                else:
                    child = species.members[0].copy()
            else:
                if total_fitness > 0:
                    probs = [max(0, g.fitness) / total_fitness for g in self.neat.population]
                    parent = np.random.choice(self.neat.population, p=probs)
                else:
                    parent = np.random.choice(self.neat.population)
                child = parent.copy()
            
            child = self.neat.mutate(child)
            new_population.append(child)
        
        self.neat.population = new_population[:self.population_size]
        self.neat.speciate(self.neat.population)
        
        self.generation += 1
        self.metrics["generations"] = self.generation
        self.metrics["num_species"] = len(self.neat.species)
        self.metrics["avg_complexity"] = np.mean([
            len(g.node_genes) + len(g.connection_genes) 
            for g in self.neat.population
        ])
        
        return {
            "generation": self.generation,
            "best_fitness": self.metrics["best_fitness"],
            "avg_fitness": self.metrics["avg_fitness"],
            "num_species": self.metrics["num_species"],
            "avg_complexity": self.metrics["avg_complexity"]
        }
    
    def genome_to_network(self, genome: Genome) -> Dict[str, Any]:
        """Convert genome to executable network representation."""
        layers = {}
        for node in genome.node_genes:
            if node.layer not in layers:
                layers[node.layer] = []
            layers[node.layer].append(node)
        
        connections = {}
        for conn in genome.connection_genes:
            if conn.enabled:
                if conn.target_node not in connections:
                    connections[conn.target_node] = []
                connections[conn.target_node].append({
                    "source": conn.source_node,
                    "weight": conn.weight
                })
        
        return {
            "layers": {k: [n.gene_id for n in v] for k, v in layers.items()},
            "connections": connections,
            "activations": {n.gene_id: n.activation.value for n in genome.node_genes},
            "biases": {n.gene_id: n.bias for n in genome.node_genes}
        }
    
    async def forward_pass(self, genome: Genome, inputs: np.ndarray) -> np.ndarray:
        """Execute forward pass through evolved network."""
        network = self.genome_to_network(genome)
        
        node_values = {}
        input_nodes = [n for n in genome.node_genes if n.gene_type == "input"]
        for i, node in enumerate(input_nodes):
            if i < len(inputs):
                node_values[node.gene_id] = inputs[i]
        
        sorted_layers = sorted(network["layers"].keys())
        
        for layer in sorted_layers[1:]:
            for node_id in network["layers"][layer]:
                total = network["biases"].get(node_id, 0)
                
                if node_id in network["connections"]:
                    for conn in network["connections"][node_id]:
                        source_val = node_values.get(conn["source"], 0)
                        total += source_val * conn["weight"]
                
                activation = network["activations"].get(node_id, "tanh")
                if activation == "relu":
                    node_values[node_id] = max(0, total)
                elif activation == "tanh":
                    node_values[node_id] = np.tanh(total)
                elif activation == "sigmoid":
                    node_values[node_id] = 1 / (1 + np.exp(-np.clip(total, -500, 500)))
                else:
                    node_values[node_id] = np.tanh(total)
        
        output_nodes = [n for n in genome.node_genes if n.gene_type == "output"]
        outputs = [node_values.get(n.gene_id, 0) for n in output_nodes]
        
        return np.array(outputs)
    
    async def adapt_to_market(self, market_data: np.ndarray, 
                               labels: np.ndarray,
                               generations: int = 50) -> Genome:
        """Evolve architecture specifically for current market conditions."""
        def fitness_fn(genome: Genome) -> float:
            try:
                total_error = 0
                for i in range(min(100, len(market_data))):
                    output = asyncio.get_event_loop().run_until_complete(
                        self.forward_pass(genome, market_data[i])
                    )
                    error = np.mean((output - labels[i]) ** 2)
                    total_error += error
                return 1.0 / (1.0 + total_error)
            except:
                return 0.0
        
        for _ in range(generations):
            await self.evaluate_population(fitness_fn)
            await self.evolve_generation()
        
        return self.best_genome
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get evolution metrics."""
        return {
            **self.metrics,
            "population_size": len(self.neat.population),
            "fitness_history_length": len(self.fitness_history)
        }
    
    async def shutdown(self):
        """Shutdown the evolution system."""
        self.neat.population.clear()
        self.neat.species.clear()
        self.initialized = False
        logger.info("Neural Architecture Evolver shutdown complete")
