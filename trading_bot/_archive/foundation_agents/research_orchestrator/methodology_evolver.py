"""
Methodology Evolver - Adaptive Research Methodology
=====================================================

Implements evolving research methodologies:
1. Method performance tracking
2. Methodology mutation and crossover
3. Meta-learning from research outcomes
4. Adaptive method selection

Based on the Foundation Agents paper (arXiv:2504.01990) research systems.
"""

import logging
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict
import random
import hashlib

logger = logging.getLogger(__name__)


class MethodCategory(Enum):
    """Categories of research methods"""
    STATISTICAL = "statistical"
    MACHINE_LEARNING = "machine_learning"
    CAUSAL_INFERENCE = "causal_inference"
    TIME_SERIES = "time_series"
    OPTIMIZATION = "optimization"
    SIMULATION = "simulation"
    ENSEMBLE = "ensemble"


class MethodStatus(Enum):
    """Status of a methodology"""
    ACTIVE = "active"
    TESTING = "testing"
    DEPRECATED = "deprecated"
    EVOLVED = "evolved"


@dataclass
class MethodComponent:
    """A component of a methodology"""
    name: str
    category: MethodCategory
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance
    success_rate: float = 0.5
    avg_effect_size: float = 0.0
    usage_count: int = 0
    
    # Constraints
    applicable_to: List[str] = field(default_factory=list)
    requires: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'category': self.category.value,
            'parameters': self.parameters,
            'success_rate': self.success_rate,
            'usage_count': self.usage_count
        }


@dataclass
class Methodology:
    """A complete research methodology"""
    method_id: str
    name: str
    description: str
    
    # Components
    components: List[MethodComponent] = field(default_factory=list)
    pipeline: List[str] = field(default_factory=list)  # Order of components
    
    # Parameters
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Performance tracking
    experiments_run: int = 0
    successes: int = 0
    failures: int = 0
    avg_p_value: float = 0.5
    avg_effect_size: float = 0.0
    
    # Evolution
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    mutations: List[str] = field(default_factory=list)
    
    # Status
    status: MethodStatus = MethodStatus.ACTIVE
    
    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def success_rate(self) -> float:
        """Calculate success rate"""
        total = self.successes + self.failures
        if total == 0:
            return 0.5
        return self.successes / total
    
    def fitness(self) -> float:
        """Calculate fitness for evolution"""
        success = self.success_rate()
        effect = min(1.0, abs(self.avg_effect_size))
        usage = min(1.0, self.experiments_run / 10)
        
        return 0.5 * success + 0.3 * effect + 0.2 * usage
    
    def to_dict(self) -> Dict:
        return {
            'method_id': self.method_id,
            'name': self.name,
            'description': self.description,
            'components': [c.to_dict() for c in self.components],
            'pipeline': self.pipeline,
            'success_rate': self.success_rate(),
            'fitness': self.fitness(),
            'generation': self.generation,
            'status': self.status.value
        }


class MethodLibrary:
    """Library of method components"""
    
    def __init__(self):
        self.components: Dict[str, MethodComponent] = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize standard method components"""
        components = [
            # Statistical methods
            MethodComponent(
                name='t_test',
                category=MethodCategory.STATISTICAL,
                parameters={'paired': False, 'two_sided': True},
                applicable_to=['continuous', 'comparison']
            ),
            MethodComponent(
                name='regression',
                category=MethodCategory.STATISTICAL,
                parameters={'type': 'ols', 'robust': True},
                applicable_to=['continuous', 'relationship']
            ),
            MethodComponent(
                name='bootstrap',
                category=MethodCategory.STATISTICAL,
                parameters={'n_iterations': 1000, 'confidence': 0.95},
                applicable_to=['any']
            ),
            
            # Machine learning methods
            MethodComponent(
                name='random_forest',
                category=MethodCategory.MACHINE_LEARNING,
                parameters={'n_estimators': 100, 'max_depth': 10},
                applicable_to=['prediction', 'classification']
            ),
            MethodComponent(
                name='gradient_boosting',
                category=MethodCategory.MACHINE_LEARNING,
                parameters={'n_estimators': 100, 'learning_rate': 0.1},
                applicable_to=['prediction', 'classification']
            ),
            MethodComponent(
                name='neural_network',
                category=MethodCategory.MACHINE_LEARNING,
                parameters={'layers': [64, 32], 'dropout': 0.2},
                applicable_to=['prediction', 'complex_patterns']
            ),
            
            # Causal inference
            MethodComponent(
                name='granger_causality',
                category=MethodCategory.CAUSAL_INFERENCE,
                parameters={'max_lag': 10},
                applicable_to=['time_series', 'causality']
            ),
            MethodComponent(
                name='propensity_matching',
                category=MethodCategory.CAUSAL_INFERENCE,
                parameters={'n_neighbors': 5},
                applicable_to=['observational', 'treatment_effect']
            ),
            MethodComponent(
                name='instrumental_variables',
                category=MethodCategory.CAUSAL_INFERENCE,
                parameters={},
                applicable_to=['endogeneity', 'causality']
            ),
            
            # Time series
            MethodComponent(
                name='arima',
                category=MethodCategory.TIME_SERIES,
                parameters={'auto': True},
                applicable_to=['time_series', 'forecasting']
            ),
            MethodComponent(
                name='var',
                category=MethodCategory.TIME_SERIES,
                parameters={'max_lag': 5},
                applicable_to=['multivariate', 'time_series']
            ),
            MethodComponent(
                name='regime_switching',
                category=MethodCategory.TIME_SERIES,
                parameters={'n_regimes': 2},
                applicable_to=['time_series', 'regime']
            ),
            
            # Optimization
            MethodComponent(
                name='grid_search',
                category=MethodCategory.OPTIMIZATION,
                parameters={'cv': 5},
                applicable_to=['hyperparameter', 'optimization']
            ),
            MethodComponent(
                name='bayesian_optimization',
                category=MethodCategory.OPTIMIZATION,
                parameters={'n_iterations': 50},
                applicable_to=['hyperparameter', 'expensive']
            ),
            
            # Simulation
            MethodComponent(
                name='monte_carlo',
                category=MethodCategory.SIMULATION,
                parameters={'n_simulations': 10000},
                applicable_to=['uncertainty', 'distribution']
            ),
            MethodComponent(
                name='backtesting',
                category=MethodCategory.SIMULATION,
                parameters={'walk_forward': True},
                applicable_to=['strategy', 'validation']
            )
        ]
        
        for comp in components:
            self.components[comp.name] = comp
    
    def get_component(self, name: str) -> Optional[MethodComponent]:
        return self.components.get(name)
    
    def get_by_category(self, category: MethodCategory) -> List[MethodComponent]:
        return [c for c in self.components.values() if c.category == category]
    
    def get_applicable(self, requirements: List[str]) -> List[MethodComponent]:
        """Get components applicable to requirements"""
        applicable = []
        for comp in self.components.values():
            if 'any' in comp.applicable_to:
                applicable.append(comp)
            elif any(req in comp.applicable_to for req in requirements):
                applicable.append(comp)
        return applicable


class MethodEvolver:
    """Evolves methodologies through genetic operations"""
    
    def __init__(self, library: MethodLibrary):
        self.library = library
        self.mutation_rate = 0.2
        self.crossover_rate = 0.7
    
    def mutate(self, methodology: Methodology) -> Methodology:
        """Mutate a methodology"""
        new_method = Methodology(
            method_id=f"mut_{methodology.method_id}_{datetime.utcnow().strftime('%H%M%S')}",
            name=f"{methodology.name} (mutated)",
            description=f"Mutation of {methodology.name}",
            components=methodology.components.copy(),
            pipeline=methodology.pipeline.copy(),
            parameters=methodology.parameters.copy(),
            generation=methodology.generation + 1,
            parent_ids=[methodology.method_id],
            status=MethodStatus.TESTING
        )
        
        mutations = []
        
        # Mutate parameters
        if random.random() < self.mutation_rate:
            for key in new_method.parameters:
                if isinstance(new_method.parameters[key], (int, float)):
                    factor = random.uniform(0.8, 1.2)
                    new_method.parameters[key] *= factor
                    mutations.append(f"param_{key}_scaled")
        
        # Add/remove component
        if random.random() < self.mutation_rate:
            if len(new_method.components) > 1 and random.random() < 0.5:
                # Remove random component
                idx = random.randint(0, len(new_method.components) - 1)
                removed = new_method.components.pop(idx)
                if removed.name in new_method.pipeline:
                    new_method.pipeline.remove(removed.name)
                mutations.append(f"removed_{removed.name}")
            else:
                # Add random component
                all_comps = list(self.library.components.values())
                new_comp = random.choice(all_comps)
                if new_comp.name not in [c.name for c in new_method.components]:
                    new_method.components.append(new_comp)
                    new_method.pipeline.append(new_comp.name)
                    mutations.append(f"added_{new_comp.name}")
        
        # Swap pipeline order
        if random.random() < self.mutation_rate and len(new_method.pipeline) > 1:
            i, j = random.sample(range(len(new_method.pipeline)), 2)
            new_method.pipeline[i], new_method.pipeline[j] = \
                new_method.pipeline[j], new_method.pipeline[i]
            mutations.append("swapped_order")
        
        new_method.mutations = mutations
        return new_method
    
    def crossover(
        self,
        parent1: Methodology,
        parent2: Methodology
    ) -> Methodology:
        """Crossover two methodologies"""
        # Combine components from both parents
        all_components = {}
        for comp in parent1.components + parent2.components:
            all_components[comp.name] = comp
        
        # Select subset
        n_components = (len(parent1.components) + len(parent2.components)) // 2
        selected_names = random.sample(
            list(all_components.keys()),
            min(n_components, len(all_components))
        )
        
        # Create pipeline (prefer parent1's order)
        pipeline = []
        for name in parent1.pipeline:
            if name in selected_names:
                pipeline.append(name)
        for name in parent2.pipeline:
            if name in selected_names and name not in pipeline:
                pipeline.append(name)
        
        # Merge parameters
        parameters = {**parent1.parameters, **parent2.parameters}
        
        child = Methodology(
            method_id=f"cross_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            name=f"Crossover of {parent1.name} and {parent2.name}",
            description=f"Crossover methodology",
            components=[all_components[n] for n in selected_names],
            pipeline=pipeline,
            parameters=parameters,
            generation=max(parent1.generation, parent2.generation) + 1,
            parent_ids=[parent1.method_id, parent2.method_id],
            status=MethodStatus.TESTING
        )
        
        return child
    
    def evolve_population(
        self,
        population: List[Methodology],
        n_offspring: int = 5
    ) -> List[Methodology]:
        """Evolve a population of methodologies"""
        # Sort by fitness
        sorted_pop = sorted(population, key=lambda m: m.fitness(), reverse=True)
        
        offspring = []
        
        # Elitism: keep top performers
        n_elite = max(1, len(population) // 5)
        for method in sorted_pop[:n_elite]:
            method.status = MethodStatus.ACTIVE
        
        # Generate offspring
        while len(offspring) < n_offspring:
            if random.random() < self.crossover_rate and len(sorted_pop) >= 2:
                # Crossover
                parents = random.sample(sorted_pop[:len(sorted_pop)//2 + 1], 2)
                child = self.crossover(parents[0], parents[1])
                offspring.append(child)
            else:
                # Mutation
                parent = random.choice(sorted_pop[:len(sorted_pop)//2 + 1])
                child = self.mutate(parent)
                offspring.append(child)
        
        return offspring


class MethodologyEvolver:
    """
    Methodology Evolver
    
    Manages the evolution and adaptation of research methodologies
    based on experimental outcomes.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.library = MethodLibrary()
        self.evolver = MethodEvolver(self.library)
        
        # Storage
        self.methodologies: Dict[str, Methodology] = {}
        self.methodology_history: List[Methodology] = []
        
        # Performance tracking
        self.performance_log: List[Dict] = []
        
        # Statistics
        self.stats = {
            'methodologies_created': 0,
            'evolutions_performed': 0,
            'best_fitness': 0.0,
            'avg_success_rate': 0.5
        }
        
        # Initialize default methodologies
        self._initialize_defaults()
        
        logger.info("Methodology Evolver initialized")
    
    def _initialize_defaults(self):
        """Initialize default methodologies"""
        defaults = [
            {
                'name': 'Standard Statistical',
                'description': 'Traditional statistical hypothesis testing',
                'components': ['regression', 't_test', 'bootstrap'],
                'parameters': {'significance_level': 0.05}
            },
            {
                'name': 'ML Prediction',
                'description': 'Machine learning based prediction',
                'components': ['random_forest', 'grid_search', 'backtesting'],
                'parameters': {'cv_folds': 5}
            },
            {
                'name': 'Causal Analysis',
                'description': 'Causal inference methodology',
                'components': ['granger_causality', 'propensity_matching', 'bootstrap'],
                'parameters': {'max_lag': 10}
            },
            {
                'name': 'Time Series Forecasting',
                'description': 'Time series analysis and forecasting',
                'components': ['arima', 'regime_switching', 'monte_carlo'],
                'parameters': {'forecast_horizon': 10}
            }
        ]
        
        for default in defaults:
            self.create_methodology(
                name=default['name'],
                description=default['description'],
                component_names=default['components'],
                parameters=default['parameters']
            )
    
    def create_methodology(
        self,
        name: str,
        description: str,
        component_names: List[str],
        parameters: Optional[Dict] = None
    ) -> Methodology:
        """Create a new methodology"""
        components = []
        for comp_name in component_names:
            comp = self.library.get_component(comp_name)
            if comp:
                components.append(comp)
        
        methodology = Methodology(
            method_id=f"meth_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{hashlib.md5(name.encode()).hexdigest()[:6]}",
            name=name,
            description=description,
            components=components,
            pipeline=component_names,
            parameters=parameters or {}
        )
        
        self.methodologies[methodology.method_id] = methodology
        self.methodology_history.append(methodology)
        self.stats['methodologies_created'] += 1
        
        logger.info(f"Created methodology: {name}")
        
        return methodology
    
    def record_outcome(
        self,
        method_id: str,
        success: bool,
        p_value: Optional[float] = None,
        effect_size: Optional[float] = None,
        metadata: Optional[Dict] = None
    ):
        """Record experiment outcome for a methodology"""
        if method_id not in self.methodologies:
            return
        
        method = self.methodologies[method_id]
        method.experiments_run += 1
        method.last_used = datetime.utcnow()
        
        if success:
            method.successes += 1
        else:
            method.failures += 1
        
        # Update averages
        if p_value is not None:
            n = method.experiments_run
            method.avg_p_value = ((n - 1) * method.avg_p_value + p_value) / n
        
        if effect_size is not None:
            n = method.experiments_run
            method.avg_effect_size = ((n - 1) * method.avg_effect_size + effect_size) / n
        
        # Log performance
        self.performance_log.append({
            'method_id': method_id,
            'success': success,
            'p_value': p_value,
            'effect_size': effect_size,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        })
        
        # Update component performance
        for comp in method.components:
            comp.usage_count += 1
            n = comp.usage_count
            comp.success_rate = ((n - 1) * comp.success_rate + (1 if success else 0)) / n
            if effect_size is not None:
                comp.avg_effect_size = ((n - 1) * comp.avg_effect_size + effect_size) / n
        
        # Update stats
        all_rates = [m.success_rate() for m in self.methodologies.values() if m.experiments_run > 0]
        if all_rates:
            self.stats['avg_success_rate'] = np.mean(all_rates)
        
        self.stats['best_fitness'] = max(
            m.fitness() for m in self.methodologies.values()
        )
    
    def evolve(self, n_offspring: int = 3) -> List[Methodology]:
        """Evolve methodologies based on performance"""
        # Get active methodologies with enough experiments
        active = [
            m for m in self.methodologies.values()
            if m.status == MethodStatus.ACTIVE and m.experiments_run >= 3
        ]
        
        if len(active) < 2:
            logger.warning("Not enough methodologies for evolution")
            return []
        
        # Evolve
        offspring = self.evolver.evolve_population(active, n_offspring)
        
        # Add offspring
        for child in offspring:
            self.methodologies[child.method_id] = child
            self.methodology_history.append(child)
        
        self.stats['evolutions_performed'] += 1
        
        logger.info(f"Evolved {len(offspring)} new methodologies")
        
        return offspring
    
    def select_methodology(
        self,
        requirements: List[str],
        prefer_tested: bool = True
    ) -> Optional[Methodology]:
        """Select best methodology for requirements"""
        candidates = []
        
        for method in self.methodologies.values():
            if method.status != MethodStatus.ACTIVE:
                continue
            
            # Check if components match requirements
            comp_applicable = any(
                req in comp.applicable_to or 'any' in comp.applicable_to
                for comp in method.components
                for req in requirements
            )
            
            if comp_applicable:
                candidates.append(method)
        
        if not candidates:
            # Return any active methodology
            candidates = [m for m in self.methodologies.values() if m.status == MethodStatus.ACTIVE]
        
        if not candidates:
            return None
        
        # Sort by fitness, preferring tested methods
        if prefer_tested:
            candidates.sort(
                key=lambda m: (m.experiments_run > 0, m.fitness()),
                reverse=True
            )
        else:
            candidates.sort(key=lambda m: m.fitness(), reverse=True)
        
        return candidates[0]
    
    def get_methodology(self, method_id: str) -> Optional[Methodology]:
        """Get methodology by ID"""
        return self.methodologies.get(method_id)
    
    def get_top_methodologies(self, n: int = 5) -> List[Methodology]:
        """Get top performing methodologies"""
        active = [m for m in self.methodologies.values() if m.status == MethodStatus.ACTIVE]
        active.sort(key=lambda m: m.fitness(), reverse=True)
        return active[:n]
    
    def deprecate_methodology(self, method_id: str, reason: str = ""):
        """Deprecate a methodology"""
        if method_id in self.methodologies:
            self.methodologies[method_id].status = MethodStatus.DEPRECATED
            self.methodologies[method_id].metadata['deprecation_reason'] = reason
            logger.info(f"Deprecated methodology: {method_id}")
    
    def get_component_performance(self) -> Dict[str, Dict]:
        """Get performance statistics for all components"""
        performance = {}
        
        for comp in self.library.components.values():
            performance[comp.name] = {
                'category': comp.category.value,
                'success_rate': comp.success_rate,
                'avg_effect_size': comp.avg_effect_size,
                'usage_count': comp.usage_count
            }
        
        return performance
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolver statistics"""
        active = [m for m in self.methodologies.values() if m.status == MethodStatus.ACTIVE]
        
        return {
            **self.stats,
            'total_methodologies': len(self.methodologies),
            'active_methodologies': len(active),
            'total_experiments': sum(m.experiments_run for m in self.methodologies.values()),
            'generations': max((m.generation for m in self.methodologies.values()), default=0),
            'top_methods': [
                {'name': m.name, 'fitness': m.fitness(), 'success_rate': m.success_rate()}
                for m in self.get_top_methodologies(3)
            ]
        }
