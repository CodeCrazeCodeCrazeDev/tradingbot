"""
Code Genetics - DNA-like Code Evolution System
===============================================

Treats code as genetic material that can:
- Mutate (small random changes)
- Crossover (combine best parts of two strategies)
- Express (compile and run)
- Replicate (create copies with variations)
- Evolve (natural selection based on fitness)

This enables the AI to evolve its own trading strategies
through genetic programming principles.
"""

import ast
import copy
import hashlib
import logging
import random
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import json

logger = logging.getLogger(__name__)


class GeneType(Enum):
    """Types of genetic code units"""
    PARAMETER = "parameter"           # Numeric parameters
    CONDITION = "condition"           # Boolean conditions
    INDICATOR = "indicator"           # Technical indicators
    SIGNAL_LOGIC = "signal_logic"     # Signal generation logic
    RISK_RULE = "risk_rule"           # Risk management rules
    EXIT_RULE = "exit_rule"           # Exit conditions
    FILTER = "filter"                 # Trade filters
    TIMING = "timing"                 # Timing logic


class MutationType(Enum):
    """Types of mutations"""
    POINT = "point"                   # Single value change
    INSERTION = "insertion"           # Add new gene
    DELETION = "deletion"             # Remove gene
    DUPLICATION = "duplication"       # Copy gene
    INVERSION = "inversion"           # Reverse order
    TRANSPOSITION = "transposition"   # Move gene location


@dataclass
class Gene:
    """A single unit of genetic code"""
    gene_id: str
    gene_type: GeneType
    name: str
    value: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mutation_rate: float = 0.1
    is_dominant: bool = False
    expression_weight: float = 1.0
    
    def mutate(self) -> 'Gene':
        """Create a mutated copy of this gene"""
        new_gene = copy.deepcopy(self)
        new_gene.gene_id = f"{self.gene_id}_mut_{random.randint(1000, 9999)}"
        
        if isinstance(self.value, (int, float)):
            # Numeric mutation
            if self.min_value is not None and self.max_value is not None:
                range_size = self.max_value - self.min_value
                mutation = random.gauss(0, range_size * 0.1)
                new_gene.value = max(self.min_value, min(self.max_value, self.value + mutation))
            else:
                new_gene.value = self.value * random.uniform(0.8, 1.2)
        
        elif isinstance(self.value, bool):
            # Boolean mutation - flip with probability
            if random.random() < self.mutation_rate:
                new_gene.value = not self.value
        
        elif isinstance(self.value, str):
            # String mutation - character changes
            if len(self.value) > 0 and random.random() < self.mutation_rate:
                chars = list(self.value)
                idx = random.randint(0, len(chars) - 1)
                chars[idx] = chr(ord(chars[idx]) + random.randint(-5, 5))
                new_gene.value = ''.join(chars)
        
        elif isinstance(self.value, list):
            # List mutation - add/remove/modify elements
            new_gene.value = copy.deepcopy(self.value)
            if len(new_gene.value) > 0:
                action = random.choice(['add', 'remove', 'modify'])
                if action == 'add' and len(new_gene.value) < 10:
                    new_gene.value.append(random.choice(self.value))
                elif action == 'remove' and len(new_gene.value) > 1:
                    new_gene.value.pop(random.randint(0, len(new_gene.value) - 1))
                elif action == 'modify':
                    idx = random.randint(0, len(new_gene.value) - 1)
                    if isinstance(new_gene.value[idx], (int, float)):
                        new_gene.value[idx] *= random.uniform(0.8, 1.2)
        
        return new_gene
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'gene_id': self.gene_id,
            'gene_type': self.gene_type.value,
            'name': self.name,
            'value': self.value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'mutation_rate': self.mutation_rate,
            'is_dominant': self.is_dominant,
            'expression_weight': self.expression_weight,
        }


@dataclass
class Chromosome:
    """A collection of genes that form a complete strategy"""
    chromosome_id: str
    genes: List[Gene]
    generation: int = 0
    fitness: float = 0.0
    parent_ids: List[str] = field(default_factory=list)
    birth_timestamp: datetime = field(default_factory=datetime.utcnow)
    mutations_applied: int = 0
    
    def get_gene(self, name: str) -> Optional[Gene]:
        """Get gene by name"""
        for gene in self.genes:
            if gene.name == name:
                return gene
        return None
    
    def get_genes_by_type(self, gene_type: GeneType) -> List[Gene]:
        """Get all genes of a specific type"""
        return [g for g in self.genes if g.gene_type == gene_type]
    
    def mutate(self, mutation_rate: float = 0.1) -> 'Chromosome':
        """Create a mutated copy of this chromosome"""
        new_chromosome = Chromosome(
            chromosome_id=f"chr_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            genes=[],
            generation=self.generation + 1,
            parent_ids=[self.chromosome_id],
        )
        
        for gene in self.genes:
            if random.random() < mutation_rate:
                new_chromosome.genes.append(gene.mutate())
                new_chromosome.mutations_applied += 1
            else:
                new_chromosome.genes.append(copy.deepcopy(gene))
        
        return new_chromosome
    
    def crossover(self, other: 'Chromosome') -> Tuple['Chromosome', 'Chromosome']:
        """Perform crossover with another chromosome"""
        # Single-point crossover
        if len(self.genes) < 2 or len(other.genes) < 2:
            return self.mutate(), other.mutate()
        
        crossover_point = random.randint(1, min(len(self.genes), len(other.genes)) - 1)
        
        child1_genes = self.genes[:crossover_point] + other.genes[crossover_point:]
        child2_genes = other.genes[:crossover_point] + self.genes[crossover_point:]
        
        child1 = Chromosome(
            chromosome_id=f"chr_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            genes=[copy.deepcopy(g) for g in child1_genes],
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.chromosome_id, other.chromosome_id],
        )
        
        child2 = Chromosome(
            chromosome_id=f"chr_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}",
            genes=[copy.deepcopy(g) for g in child2_genes],
            generation=max(self.generation, other.generation) + 1,
            parent_ids=[self.chromosome_id, other.chromosome_id],
        )
        
        return child1, child2
    
    def express(self) -> Dict[str, Any]:
        """Express the chromosome as a strategy configuration"""
        config = {}
        
        for gene in self.genes:
            if gene.gene_type == GeneType.PARAMETER:
                config[gene.name] = gene.value
            elif gene.gene_type == GeneType.CONDITION:
                config.setdefault('conditions', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.INDICATOR:
                config.setdefault('indicators', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.SIGNAL_LOGIC:
                config.setdefault('signals', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.RISK_RULE:
                config.setdefault('risk', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.EXIT_RULE:
                config.setdefault('exits', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.FILTER:
                config.setdefault('filters', {})[gene.name] = gene.value
            elif gene.gene_type == GeneType.TIMING:
                config.setdefault('timing', {})[gene.name] = gene.value
        
        return config
    
    def get_dna_hash(self) -> str:
        """Get unique hash of this chromosome's DNA"""
        dna_string = json.dumps([g.to_dict() for g in self.genes], sort_keys=True)
        return hashlib.sha256(dna_string.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'chromosome_id': self.chromosome_id,
            'genes': [g.to_dict() for g in self.genes],
            'generation': self.generation,
            'fitness': self.fitness,
            'parent_ids': self.parent_ids,
            'birth_timestamp': self.birth_timestamp.isoformat(),
            'mutations_applied': self.mutations_applied,
            'dna_hash': self.get_dna_hash(),
        }


class GenePool:
    """
    Gene Pool - Collection of chromosomes for evolution
    
    Manages:
    - Population of chromosomes
    - Selection pressure
    - Breeding and mutation
    - Fitness tracking
    - Speciation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        self.population: List[Chromosome] = []
        self.hall_of_fame: List[Chromosome] = []  # Best ever
        self.species: Dict[str, List[Chromosome]] = {}
        
        self.population_size = self.config.get('population_size', 50)
        self.elite_size = self.config.get('elite_size', 5)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.crossover_rate = self.config.get('crossover_rate', 0.7)
        
        self.generation = 0
        self.best_fitness_history: List[float] = []
        
        logger.info("GenePool initialized")
    
    def initialize_population(self, template_genes: List[Gene]) -> None:
        """Initialize population with random variations of template"""
        self.population = []
        
        for i in range(self.population_size):
            chromosome = Chromosome(
                chromosome_id=f"chr_gen0_{i}_{random.randint(1000, 9999)}",
                genes=[],
                generation=0,
            )
            
            for gene in template_genes:
                # Create variation of each gene
                new_gene = gene.mutate() if i > 0 else copy.deepcopy(gene)
                chromosome.genes.append(new_gene)
            
            self.population.append(chromosome)
        
        logger.info(f"Initialized population with {len(self.population)} chromosomes")
    
    def evaluate_fitness(self, fitness_func: Callable[[Chromosome], float]) -> None:
        """Evaluate fitness of all chromosomes"""
        for chromosome in self.population:
            chromosome.fitness = fitness_func(chromosome)
        
        # Sort by fitness
        self.population.sort(key=lambda c: c.fitness, reverse=True)
        
        # Update hall of fame
        for chromosome in self.population[:self.elite_size]:
            if not self.hall_of_fame or chromosome.fitness > self.hall_of_fame[0].fitness:
                self.hall_of_fame.insert(0, copy.deepcopy(chromosome))
                self.hall_of_fame = self.hall_of_fame[:10]  # Keep top 10 ever
        
        # Track best fitness
        if self.population:
            self.best_fitness_history.append(self.population[0].fitness)
    
    def select_parents(self) -> Tuple[Chromosome, Chromosome]:
        """Select two parents using tournament selection"""
        tournament_size = min(5, len(self.population))
        
        def tournament():
            contestants = random.sample(self.population, tournament_size)
            return max(contestants, key=lambda c: c.fitness)
        
        return tournament(), tournament()
    
    def evolve(self) -> None:
        """Evolve the population to the next generation"""
        new_population = []
        
        # Elitism - keep best chromosomes
        elite = self.population[:self.elite_size]
        new_population.extend([copy.deepcopy(c) for c in elite])
        
        # Generate rest of population
        while len(new_population) < self.population_size:
            parent1, parent2 = self.select_parents()
            
            if random.random() < self.crossover_rate:
                child1, child2 = parent1.crossover(parent2)
            else:
                child1 = parent1.mutate(self.mutation_rate)
                child2 = parent2.mutate(self.mutation_rate)
            
            # Additional mutation
            if random.random() < self.mutation_rate:
                child1 = child1.mutate(self.mutation_rate)
            if random.random() < self.mutation_rate:
                child2 = child2.mutate(self.mutation_rate)
            
            new_population.append(child1)
            if len(new_population) < self.population_size:
                new_population.append(child2)
        
        self.population = new_population
        self.generation += 1
        
        logger.info(f"Evolved to generation {self.generation}")
    
    def speciate(self) -> None:
        """Group chromosomes into species based on genetic similarity"""
        self.species = {}
        
        for chromosome in self.population:
            dna_hash = chromosome.get_dna_hash()
            species_key = dna_hash[:4]  # First 4 chars as species identifier
            
            if species_key not in self.species:
                self.species[species_key] = []
            self.species[species_key].append(chromosome)
        
        logger.info(f"Population divided into {len(self.species)} species")
    
    def get_best_chromosome(self) -> Optional[Chromosome]:
        """Get the best chromosome in current population"""
        if not self.population:
            return None
        return max(self.population, key=lambda c: c.fitness)
    
    def get_diversity_score(self) -> float:
        """Calculate genetic diversity of population"""
        if len(self.population) < 2:
            return 0.0
        
        unique_hashes = set(c.get_dna_hash() for c in self.population)
        return len(unique_hashes) / len(self.population)
    
    def get_report(self) -> Dict[str, Any]:
        """Get gene pool status report"""
        return {
            'generation': self.generation,
            'population_size': len(self.population),
            'species_count': len(self.species),
            'diversity_score': self.get_diversity_score(),
            'best_fitness': self.population[0].fitness if self.population else 0,
            'avg_fitness': sum(c.fitness for c in self.population) / len(self.population) if self.population else 0,
            'hall_of_fame_size': len(self.hall_of_fame),
            'fitness_history': self.best_fitness_history[-10:],
        }


class CodeGenetics:
    """
    Code Genetics Engine
    
    Main interface for genetic code evolution.
    Creates, evolves, and manages genetic trading strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.gene_pool = GenePool(config)
        
        # Template genes for trading strategies
        self.template_genes = self._create_template_genes()
        
        logger.info("CodeGenetics engine initialized")
    
    def _create_template_genes(self) -> List[Gene]:
        """Create template genes for trading strategies"""
        return [
            # Parameters
            Gene("gene_rsi_period", GeneType.PARAMETER, "rsi_period", 14, 5, 50, 0.15),
            Gene("gene_rsi_overbought", GeneType.PARAMETER, "rsi_overbought", 70, 60, 90, 0.1),
            Gene("gene_rsi_oversold", GeneType.PARAMETER, "rsi_oversold", 30, 10, 40, 0.1),
            Gene("gene_ma_fast", GeneType.PARAMETER, "ma_fast_period", 10, 5, 50, 0.15),
            Gene("gene_ma_slow", GeneType.PARAMETER, "ma_slow_period", 50, 20, 200, 0.15),
            Gene("gene_atr_period", GeneType.PARAMETER, "atr_period", 14, 5, 30, 0.1),
            Gene("gene_atr_multiplier", GeneType.PARAMETER, "atr_multiplier", 2.0, 1.0, 5.0, 0.15),
            
            # Risk rules
            Gene("gene_risk_per_trade", GeneType.RISK_RULE, "risk_per_trade", 0.02, 0.005, 0.05, 0.1),
            Gene("gene_max_positions", GeneType.RISK_RULE, "max_positions", 3, 1, 10, 0.1),
            Gene("gene_max_drawdown", GeneType.RISK_RULE, "max_drawdown", 0.15, 0.05, 0.30, 0.1),
            
            # Exit rules
            Gene("gene_take_profit_atr", GeneType.EXIT_RULE, "take_profit_atr", 3.0, 1.0, 6.0, 0.15),
            Gene("gene_stop_loss_atr", GeneType.EXIT_RULE, "stop_loss_atr", 2.0, 0.5, 4.0, 0.15),
            Gene("gene_trailing_stop", GeneType.EXIT_RULE, "trailing_stop_enabled", True, None, None, 0.2),
            
            # Filters
            Gene("gene_min_volume", GeneType.FILTER, "min_volume_percentile", 50, 0, 100, 0.1),
            Gene("gene_trend_filter", GeneType.FILTER, "require_trend_alignment", True, None, None, 0.2),
            
            # Timing
            Gene("gene_trade_hours", GeneType.TIMING, "allowed_hours", [8, 9, 10, 11, 12, 13, 14, 15, 16], None, None, 0.1),
            Gene("gene_avoid_news", GeneType.TIMING, "avoid_high_impact_news", True, None, None, 0.1),
            
            # Indicators
            Gene("gene_use_macd", GeneType.INDICATOR, "use_macd", True, None, None, 0.15),
            Gene("gene_use_bollinger", GeneType.INDICATOR, "use_bollinger", True, None, None, 0.15),
            Gene("gene_use_volume", GeneType.INDICATOR, "use_volume_analysis", True, None, None, 0.15),
            
            # Signal logic
            Gene("gene_signal_threshold", GeneType.SIGNAL_LOGIC, "min_signal_strength", 0.6, 0.3, 0.9, 0.1),
            Gene("gene_confirmation_count", GeneType.SIGNAL_LOGIC, "required_confirmations", 2, 1, 5, 0.15),
        ]
    
    def initialize(self) -> None:
        """Initialize the genetic system"""
        self.gene_pool.initialize_population(self.template_genes)
    
    def evolve_generation(self, fitness_func: Callable[[Chromosome], float]) -> Dict[str, Any]:
        """Evolve one generation"""
        # Evaluate fitness
        self.gene_pool.evaluate_fitness(fitness_func)
        
        # Speciate
        self.gene_pool.speciate()
        
        # Evolve
        self.gene_pool.evolve()
        
        return self.gene_pool.get_report()
    
    def get_best_strategy(self) -> Optional[Dict[str, Any]]:
        """Get the best evolved strategy configuration"""
        best = self.gene_pool.get_best_chromosome()
        if best:
            return best.express()
        return None
    
    def inject_gene(self, gene: Gene) -> None:
        """Inject a new gene into the population"""
        for chromosome in self.gene_pool.population:
            if random.random() < 0.3:  # 30% chance to receive gene
                chromosome.genes.append(copy.deepcopy(gene))
        
        logger.info(f"Injected gene {gene.name} into population")
    
    def export_dna(self, chromosome: Chromosome) -> str:
        """Export chromosome as DNA string"""
        return json.dumps(chromosome.to_dict(), indent=2)
    
    def import_dna(self, dna_string: str) -> Chromosome:
        """Import chromosome from DNA string"""
        data = json.loads(dna_string)
        
        genes = []
        for g_data in data['genes']:
            gene = Gene(
                gene_id=g_data['gene_id'],
                gene_type=GeneType(g_data['gene_type']),
                name=g_data['name'],
                value=g_data['value'],
                min_value=g_data.get('min_value'),
                max_value=g_data.get('max_value'),
                mutation_rate=g_data.get('mutation_rate', 0.1),
                is_dominant=g_data.get('is_dominant', False),
                expression_weight=g_data.get('expression_weight', 1.0),
            )
            genes.append(gene)
        
        return Chromosome(
            chromosome_id=data['chromosome_id'],
            genes=genes,
            generation=data['generation'],
            fitness=data['fitness'],
            parent_ids=data['parent_ids'],
        )


# Factory function
def create_code_genetics(config: Optional[Dict[str, Any]] = None) -> CodeGenetics:
    """Create and initialize code genetics engine"""
    engine = CodeGenetics(config)
    engine.initialize()
    return engine
