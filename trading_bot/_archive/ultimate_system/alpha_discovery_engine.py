"""
Alpha Discovery Engine - Autonomous Alpha Generation
=====================================================

A research-driven engine that:
1. Discovers new alpha signals through research
2. Tests and validates alpha factors
3. Combines multiple alpha sources
4. Continuously searches for market inefficiencies
5. Generates novel trading strategies
"""

import asyncio
import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from pathlib import Path
import numpy

logger = logging.getLogger(__name__)


class AlphaType(Enum):
    """Types of alpha signals"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    TREND_FOLLOWING = "trend_following"
    STATISTICAL_ARBITRAGE = "statistical_arbitrage"
    SENTIMENT = "sentiment"
    FUNDAMENTAL = "fundamental"
    TECHNICAL = "technical"
    MACHINE_LEARNING = "machine_learning"
    ALTERNATIVE_DATA = "alternative_data"
    CROSS_ASSET = "cross_asset"
    MICROSTRUCTURE = "microstructure"
    EVENT_DRIVEN = "event_driven"


class AlphaStatus(Enum):
    """Status of an alpha signal"""
    DISCOVERED = "discovered"
    TESTING = "testing"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    DEPRECATED = "deprecated"
    FAILED = "failed"


@dataclass
class AlphaSignal:
    """An alpha signal/factor"""
    alpha_id: str
    name: str
    alpha_type: AlphaType
    description: str
    
    # Signal generation
    formula: str  # Mathematical formula or code
    parameters: Dict[str, Any]
    
    # Performance metrics
    sharpe_ratio: float = 0.0
    information_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    # Validation
    backtest_start: Optional[datetime] = None
    backtest_end: Optional[datetime] = None
    out_of_sample_sharpe: float = 0.0
    
    # Status
    status: AlphaStatus = AlphaStatus.DISCOVERED
    confidence: float = 0.0
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    source: str = "research"
    
    def to_dict(self) -> Dict:
        return {
            'alpha_id': self.alpha_id,
            'name': self.name,
            'type': self.alpha_type.value,
            'description': self.description,
            'sharpe_ratio': self.sharpe_ratio,
            'status': self.status.value,
            'confidence': self.confidence
        }


@dataclass
class AlphaResearchResult:
    """Result of alpha research"""
    research_id: str
    query: str
    alphas_discovered: List[AlphaSignal]
    insights: List[str]
    sources_consulted: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class AlphaDiscoveryEngine:
    """
    Alpha Discovery Engine
    
    Capabilities:
    - Research-based alpha discovery
    - Genetic programming for alpha generation
    - Machine learning alpha mining
    - Cross-asset alpha detection
    - Alternative data alpha extraction
    - Continuous alpha validation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Alpha storage
        self.discovered_alphas: List[AlphaSignal] = []
        self.deployed_alphas: List[AlphaSignal] = []
        self.alpha_history: List[AlphaSignal] = []
        
        # Research results
        self.research_results: List[AlphaResearchResult] = []
        
        # Alpha templates (building blocks)
        self.alpha_templates = self._initialize_templates()
        
        # Genetic programming settings
        self.population_size = self.config.get('population_size', 100)
        self.generations = self.config.get('generations', 50)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        
        # Validation thresholds
        self.min_sharpe = self.config.get('min_sharpe', 1.0)
        self.min_win_rate = self.config.get('min_win_rate', 0.52)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)
        
        # Persistence
        self.storage_path = Path(self.config.get('storage_path', 'alpha_storage'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'alphas_discovered': 0,
            'alphas_validated': 0,
            'alphas_deployed': 0,
            'alphas_failed': 0,
            'research_queries': 0
        }
        
        # Load existing alphas
        self._load_alphas()
        
        logger.info("Alpha Discovery Engine initialized")
    
    def _initialize_templates(self) -> Dict[str, Dict]:
        """Initialize alpha templates"""
        return {
            # Momentum templates
            'momentum_roc': {
                'type': AlphaType.MOMENTUM,
                'formula': 'price / price.shift(period) - 1',
                'params': {'period': [5, 10, 20, 60]},
                'description': 'Rate of change momentum'
            },
            'momentum_rsi': {
                'type': AlphaType.MOMENTUM,
                'formula': 'rsi(price, period)',
                'params': {'period': [7, 14, 21]},
                'description': 'RSI-based momentum'
            },
            
            # Mean reversion templates
            'mean_rev_zscore': {
                'type': AlphaType.MEAN_REVERSION,
                'formula': '(price - price.rolling(period).mean()) / price.rolling(period).std()',
                'params': {'period': [20, 50, 100]},
                'description': 'Z-score mean reversion'
            },
            'mean_rev_bollinger': {
                'type': AlphaType.MEAN_REVERSION,
                'formula': '(price - bb_middle) / (bb_upper - bb_lower)',
                'params': {'period': [20], 'std': [2]},
                'description': 'Bollinger band mean reversion'
            },
            
            # Trend following templates
            'trend_ma_cross': {
                'type': AlphaType.TREND_FOLLOWING,
                'formula': 'sma(price, fast) - sma(price, slow)',
                'params': {'fast': [10, 20], 'slow': [50, 100, 200]},
                'description': 'Moving average crossover'
            },
            'trend_adx': {
                'type': AlphaType.TREND_FOLLOWING,
                'formula': 'adx(high, low, close, period)',
                'params': {'period': [14, 21]},
                'description': 'ADX trend strength'
            },
            
            # Microstructure templates
            'micro_volume_imbalance': {
                'type': AlphaType.MICROSTRUCTURE,
                'formula': '(buy_volume - sell_volume) / total_volume',
                'params': {'period': [5, 10]},
                'description': 'Volume imbalance'
            },
            'micro_spread': {
                'type': AlphaType.MICROSTRUCTURE,
                'formula': '(ask - bid) / mid_price',
                'params': {},
                'description': 'Bid-ask spread'
            },
            
            # Cross-asset templates
            'cross_correlation': {
                'type': AlphaType.CROSS_ASSET,
                'formula': 'correlation(asset1, asset2, period)',
                'params': {'period': [20, 60]},
                'description': 'Cross-asset correlation'
            },
            
            # ML templates
            'ml_pattern': {
                'type': AlphaType.MACHINE_LEARNING,
                'formula': 'ml_model.predict(features)',
                'params': {'model_type': ['rf', 'xgb', 'nn']},
                'description': 'ML pattern recognition'
            }
        }
    
    async def discover_alpha(
        self,
        research_query: str,
        alpha_type: Optional[AlphaType] = None,
        use_genetic: bool = True,
        use_ml: bool = True
    ) -> List[AlphaSignal]:
        """
        Discover new alpha signals
        
        Args:
            research_query: Research topic/query
            alpha_type: Specific type to focus on
            use_genetic: Use genetic programming
            use_ml: Use machine learning
            
        Returns:
            List of discovered alpha signals
        """
        logger.info(f"Discovering alpha for: {research_query}")
        self.stats['research_queries'] += 1
        
        discovered = []
        
        try:
            # 1. Template-based discovery
            template_alphas = self._discover_from_templates(research_query, alpha_type)
            discovered.extend(template_alphas)
            
            # 2. Genetic programming discovery
            if use_genetic:
                genetic_alphas = await self._genetic_discovery(research_query, alpha_type)
                discovered.extend(genetic_alphas)
            
            # 3. ML-based discovery
            if use_ml:
                ml_alphas = await self._ml_discovery(research_query, alpha_type)
                discovered.extend(ml_alphas)
            
            # 4. Validate discovered alphas
            validated = []
            for alpha in discovered:
                if await self._validate_alpha(alpha):
                    alpha.status = AlphaStatus.VALIDATED
                    validated.append(alpha)
                    self.stats['alphas_validated'] += 1
                else:
                    alpha.status = AlphaStatus.FAILED
                    self.stats['alphas_failed'] += 1
            
            # Store validated alphas
            for alpha in validated:
                self.discovered_alphas.append(alpha)
                self.stats['alphas_discovered'] += 1
            
            # Save research result
            result = AlphaResearchResult(
                research_id=f"research_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                query=research_query,
                alphas_discovered=validated,
                insights=[f"Discovered {len(validated)} valid alphas"],
                sources_consulted=['templates', 'genetic', 'ml']
            )
            self.research_results.append(result)
            
            # Persist
            self._save_alphas()
            
            logger.info(f"Discovered {len(validated)} valid alphas")
            
        except Exception as e:
            logger.error(f"Alpha discovery failed: {e}")
        
        return discovered
    
    def _discover_from_templates(
        self,
        query: str,
        alpha_type: Optional[AlphaType]
    ) -> List[AlphaSignal]:
        """Discover alphas from templates"""
        alphas = []
        
        for name, template in self.alpha_templates.items():
            # Filter by type if specified
            if alpha_type and template['type'] != alpha_type:
                continue
            
            # Check if query matches template
            if query.lower() in name.lower() or query.lower() in template['description'].lower():
                # Generate alpha variations
                param_combinations = self._generate_param_combinations(template['params'])
                
                for params in param_combinations[:3]:  # Limit variations
                    alpha = AlphaSignal(
                        alpha_id=f"alpha_{name}_{hashlib.md5(str(params).encode()).hexdigest()[:8]}",
                        name=f"{name}_{params}",
                        alpha_type=template['type'],
                        description=template['description'],
                        formula=template['formula'],
                        parameters=params,
                        source='template'
                    )
                    alphas.append(alpha)
        
        return alphas
    
    def _generate_param_combinations(self, params: Dict[str, List]) -> List[Dict]:
        """Generate parameter combinations"""
        if not params:
            return [{}]
        
        combinations = [{}]
        
        for param_name, values in params.items():
            new_combinations = []
            for combo in combinations:
                for value in values:
                    new_combo = combo.copy()
                    new_combo[param_name] = value
                    new_combinations.append(new_combo)
            combinations = new_combinations
        
        return combinations
    
    async def _genetic_discovery(
        self,
        query: str,
        alpha_type: Optional[AlphaType]
    ) -> List[AlphaSignal]:
        """Discover alphas using genetic programming"""
        alphas = []
        
        try:
            # Initialize population
            population = self._initialize_population(alpha_type)
            
            # Evolve
            for generation in range(min(10, self.generations)):  # Limit for speed
                # Evaluate fitness
                fitness_scores = await self._evaluate_population(population)
                
                # Select best
                sorted_pop = sorted(
                    zip(population, fitness_scores),
                    key=lambda x: x[1],
                    reverse=True
                )
                
                # Keep top performers
                survivors = [p for p, f in sorted_pop[:self.population_size // 2]]
                
                # Crossover and mutate
                offspring = self._crossover_and_mutate(survivors)
                
                population = survivors + offspring
            
            # Extract best alphas
            final_fitness = await self._evaluate_population(population)
            best_indices = np.argsort(final_fitness)[-5:]  # Top 5
            
            for idx in best_indices:
                alpha = self._genome_to_alpha(population[idx], query)
                if alpha:
                    alpha.source = 'genetic'
                    alphas.append(alpha)
                    
        except Exception as e:
            logger.error(f"Genetic discovery failed: {e}")
        
        return alphas
    
    def _initialize_population(self, alpha_type: Optional[AlphaType]) -> List[Dict]:
        """Initialize genetic population"""
        population = []
        
        # Genes: operators, indicators, parameters
        operators = ['+', '-', '*', '/', 'max', 'min', 'abs']
        indicators = ['sma', 'ema', 'rsi', 'macd', 'atr', 'std', 'roc']
        
        for _ in range(self.population_size):
            genome = {
                'operator': np.random.choice(operators),
                'indicator1': np.random.choice(indicators),
                'indicator2': np.random.choice(indicators),
                'period1': np.random.randint(5, 100),
                'period2': np.random.randint(5, 100),
                'threshold': np.random.uniform(-2, 2)
            }
            population.append(genome)
        
        return population
    
    async def _evaluate_population(self, population: List[Dict]) -> List[float]:
        """Evaluate fitness of population"""
        fitness_scores = []
        
        for genome in population:
            # Simplified fitness evaluation
            # In production, would run actual backtests
            fitness = np.random.uniform(0, 2)  # Placeholder
            
            # Penalize complexity
            complexity_penalty = 0.1 * (genome['period1'] + genome['period2']) / 200
            fitness -= complexity_penalty
            
            fitness_scores.append(max(0, fitness))
        
        return fitness_scores
    
    def _crossover_and_mutate(self, parents: List[Dict]) -> List[Dict]:
        """Crossover and mutate to create offspring"""
        offspring = []
        
        while len(offspring) < len(parents):
            # Select parents
            p1, p2 = np.random.choice(len(parents), 2, replace=False)
            parent1, parent2 = parents[p1], parents[p2]
            
            # Crossover
            child = {}
            for key in parent1.keys():
                if np.random.random() < 0.5:
                    child[key] = parent1[key]
                else:
                    child[key] = parent2[key]
            
            # Mutate
            if np.random.random() < self.mutation_rate:
                mutation_key = np.random.choice(list(child.keys()))
                if mutation_key in ['period1', 'period2']:
                    child[mutation_key] = np.random.randint(5, 100)
                elif mutation_key == 'threshold':
                    child[mutation_key] = np.random.uniform(-2, 2)
            
            offspring.append(child)
        
        return offspring
    
    def _genome_to_alpha(self, genome: Dict, query: str) -> Optional[AlphaSignal]:
        """Convert genome to alpha signal"""
        try:
            formula = f"{genome['operator']}({genome['indicator1']}(price, {genome['period1']}), {genome['indicator2']}(price, {genome['period2']}))"
            
            alpha = AlphaSignal(
                alpha_id=f"genetic_{hashlib.md5(formula.encode()).hexdigest()[:8]}",
                name=f"genetic_{genome['indicator1']}_{genome['indicator2']}",
                alpha_type=AlphaType.MACHINE_LEARNING,
                description=f"Genetically evolved alpha: {formula}",
                formula=formula,
                parameters=genome,
                sharpe_ratio=np.random.uniform(0.5, 2.0),  # Would be from backtest
                confidence=0.6
            )
            return alpha
            
        except Exception as e:
            logger.error(f"Genome conversion failed: {e}")
            return None
    
    async def _ml_discovery(
        self,
        query: str,
        alpha_type: Optional[AlphaType]
    ) -> List[AlphaSignal]:
        """Discover alphas using machine learning"""
        alphas = []
        
        try:
            # Feature importance-based alpha discovery
            # In production, would train models and extract important features
            
            ml_alpha = AlphaSignal(
                alpha_id=f"ml_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                name=f"ml_pattern_{query.replace(' ', '_')[:20]}",
                alpha_type=AlphaType.MACHINE_LEARNING,
                description=f"ML-discovered pattern for: {query}",
                formula="ml_model.predict(features)",
                parameters={'query': query, 'model': 'ensemble'},
                sharpe_ratio=np.random.uniform(0.8, 2.5),
                confidence=0.7,
                source='ml'
            )
            alphas.append(ml_alpha)
            
        except Exception as e:
            logger.error(f"ML discovery failed: {e}")
        
        return alphas
    
    async def _validate_alpha(self, alpha: AlphaSignal) -> bool:
        """Validate an alpha signal"""
        alpha.status = AlphaStatus.TESTING
        
        try:
            # Simulated validation (in production, would run backtests)
            await asyncio.sleep(0.05)  # Placeholder
            
            # Check thresholds
            if alpha.sharpe_ratio < self.min_sharpe:
                return False
            
            # Simulate out-of-sample test
            alpha.out_of_sample_sharpe = alpha.sharpe_ratio * np.random.uniform(0.5, 1.0)
            
            if alpha.out_of_sample_sharpe < self.min_sharpe * 0.7:
                return False
            
            # Update confidence
            alpha.confidence = min(0.95, alpha.out_of_sample_sharpe / 2)
            
            return True
            
        except Exception as e:
            logger.error(f"Alpha validation failed: {e}")
            return False
    
    def deploy_alpha(self, alpha_id: str) -> bool:
        """Deploy a validated alpha"""
        for alpha in self.discovered_alphas:
            if alpha.alpha_id == alpha_id and alpha.status == AlphaStatus.VALIDATED:
                alpha.status = AlphaStatus.DEPLOYED
                self.deployed_alphas.append(alpha)
                self.stats['alphas_deployed'] += 1
                self._save_alphas()
                logger.info(f"Deployed alpha: {alpha_id}")
                return True
        
        return False
    
    def get_signals(self, market_data: Dict[str, Any]) -> List[Tuple[AlphaSignal, float]]:
        """Get signals from deployed alphas"""
        signals = []
        
        for alpha in self.deployed_alphas:
            try:
                # Generate signal (simplified)
                signal_value = np.random.uniform(-1, 1)  # Would evaluate formula
                signals.append((alpha, signal_value))
                
            except Exception as e:
                logger.error(f"Signal generation failed for {alpha.alpha_id}: {e}")
        
        return signals
    
    def combine_alphas(self, signals: List[Tuple[AlphaSignal, float]]) -> float:
        """Combine multiple alpha signals"""
        if not signals:
            return 0.0
        
        # Weighted combination based on confidence
        total_weight = sum(alpha.confidence for alpha, _ in signals)
        
        if total_weight == 0:
            return 0.0
        
        combined = sum(
            signal * alpha.confidence / total_weight
            for alpha, signal in signals
        )
        
        return combined
    
    def _save_alphas(self):
        """Save alphas to storage"""
        data = {
            'discovered': [a.to_dict() for a in self.discovered_alphas],
            'deployed': [a.to_dict() for a in self.deployed_alphas],
            'stats': self.stats
        }
        
        with open(self.storage_path / 'alphas.json', 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_alphas(self):
        """Load alphas from storage"""
        alpha_file = self.storage_path / 'alphas.json'
        
        if alpha_file.exists():
            try:
                with open(alpha_file, 'r') as f:
                    data = json.load(f)
                
                self.stats = data.get('stats', self.stats)
                logger.info(f"Loaded {len(data.get('discovered', []))} alphas")
                
            except Exception as e:
                logger.error(f"Failed to load alphas: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics"""
        return {
            **self.stats,
            'discovered_count': len(self.discovered_alphas),
            'deployed_count': len(self.deployed_alphas),
            'alpha_types': {
                at.value: len([a for a in self.discovered_alphas if a.alpha_type == at])
                for at in AlphaType
            },
            'avg_sharpe': np.mean([a.sharpe_ratio for a in self.deployed_alphas]) if self.deployed_alphas else 0
        }
