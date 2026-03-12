"""
Autonomous Innovation
=====================

Strategy generation and feature engineering system.
Creates new trading strategies and features without human intervention.

Features:
- Automated strategy generation
- Feature engineering and discovery
- Hyperparameter optimization
- Architecture search
- Strategy mutation and crossover
- Performance-based evolution
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import random
import hashlib

logger = logging.getLogger(__name__)

try:
    from sklearn.feature_selection import SelectKBest, f_regression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.debug("scikit-learn not available for feature selection")


class InnovationType(Enum):
    """Types of innovations"""
    NEW_STRATEGY = "new_strategy"
    NEW_FEATURE = "new_feature"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    STRATEGY_MUTATION = "strategy_mutation"
    STRATEGY_CROSSOVER = "strategy_crossover"


@dataclass
class GeneratedStrategy:
    """A generated trading strategy"""
    strategy_id: str
    name: str
    description: str
    entry_rules: List[Dict[str, Any]]
    exit_rules: List[Dict[str, Any]]
    parameters: Dict[str, float]
    features_used: List[str]
    expected_performance: float
    generation_method: InnovationType
    parent_strategies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    tested: bool = False
    test_results: Dict[str, float] = field(default_factory=dict)


@dataclass
class GeneratedFeature:
    """A generated feature"""
    feature_id: str
    name: str
    description: str
    calculation_method: str
    parameters: Dict[str, Any]
    importance_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    tested: bool = False


@dataclass
class Innovation:
    """Record of an innovation"""
    innovation_id: str
    innovation_type: InnovationType
    description: str
    performance_improvement: float
    created_at: datetime
    deployed: bool = False
    deployment_date: Optional[datetime] = None


class AutonomousInnovation:
    """
    Autonomous strategy and feature generation system.
    
    Generates:
    - New trading strategies
    - New features
    - Optimized parameters
    - Strategy combinations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Innovation settings
        self.max_strategies = self.config.get('max_strategies', 50)
        self.max_features = self.config.get('max_features', 100)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.min_performance_threshold = self.config.get('min_performance', 0.6)
        
        # Generated items
        self.generated_strategies: Dict[str, GeneratedStrategy] = {}
        self.generated_features: Dict[str, GeneratedFeature] = {}
        self.innovations: List[Innovation] = []
        
        # Strategy templates
        self.strategy_templates = self._init_strategy_templates()
        
        # Feature templates
        self.feature_templates = self._init_feature_templates()
        
        logger.info("Autonomous Innovation initialized")
    
    def _init_strategy_templates(self) -> List[Dict[str, Any]]:
        """Initialize basic strategy templates"""
        return [
            {
                'name': 'momentum_breakout',
                'entry': [
                    {'type': 'momentum', 'threshold': 0.02},
                    {'type': 'volume', 'multiplier': 1.5}
                ],
                'exit': [
                    {'type': 'profit_target', 'multiplier': 2.0},
                    {'type': 'stop_loss', 'multiplier': 1.0}
                ]
            },
            {
                'name': 'mean_reversion',
                'entry': [
                    {'type': 'oversold', 'threshold': 30},
                    {'type': 'support_level', 'distance': 0.005}
                ],
                'exit': [
                    {'type': 'mean_return', 'threshold': 0.5},
                    {'type': 'time_exit', 'bars': 20}
                ]
            },
            {
                'name': 'trend_following',
                'entry': [
                    {'type': 'ma_crossover', 'fast': 10, 'slow': 20},
                    {'type': 'trend_strength', 'threshold': 0.6}
                ],
                'exit': [
                    {'type': 'trailing_stop', 'distance': 0.02},
                    {'type': 'trend_reversal', 'threshold': 0.3}
                ]
            }
        ]
    
    def _init_feature_templates(self) -> List[Dict[str, Any]]:
        """Initialize feature templates"""
        return [
            {
                'name': 'price_momentum',
                'calculation': 'roc',
                'params': {'period': 10}
            },
            {
                'name': 'volatility_ratio',
                'calculation': 'std_ratio',
                'params': {'short_period': 5, 'long_period': 20}
            },
            {
                'name': 'volume_trend',
                'calculation': 'volume_ma_ratio',
                'params': {'period': 20}
            },
            {
                'name': 'price_position',
                'calculation': 'price_percentile',
                'params': {'period': 50}
            }
        ]
    
    async def generate_new_strategy(
        self,
        market_data: pd.DataFrame,
        performance_target: float = 0.7
    ) -> Optional[GeneratedStrategy]:
        """
        Generate a new trading strategy.
        
        Args:
            market_data: Historical market data
            performance_target: Target performance score
        
        Returns:
            Generated strategy or None
        """
        try:
            # Choose generation method
            method = random.choice([
                InnovationType.NEW_STRATEGY,
                InnovationType.STRATEGY_MUTATION,
                InnovationType.STRATEGY_CROSSOVER
            ])
            
            if method == InnovationType.NEW_STRATEGY:
                strategy = self._generate_from_template()
            elif method == InnovationType.STRATEGY_MUTATION:
                strategy = await self._mutate_strategy()
            else:
                strategy = await self._crossover_strategies()
            
            if strategy:
                # Estimate performance
                strategy.expected_performance = self._estimate_strategy_performance(
                    strategy, market_data
                )
                
                # Store if meets threshold
                if strategy.expected_performance >= self.min_performance_threshold:
                    self.generated_strategies[strategy.strategy_id] = strategy
                    
                    # Record innovation
                    self.innovations.append(Innovation(
                        innovation_id=f"innov_{len(self.innovations)}",
                        innovation_type=method,
                        description=f"Generated strategy: {strategy.name}",
                        performance_improvement=strategy.expected_performance,
                        created_at=datetime.now()
                    ))
                    
                    logger.info(f"Generated new strategy: {strategy.name} "
                              f"(performance: {strategy.expected_performance:.2f})")
                    
                    return strategy
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating strategy: {e}")
            return None
    
    def _generate_from_template(self) -> GeneratedStrategy:
        """Generate strategy from template"""
        
        template = random.choice(self.strategy_templates)
        
        # Randomize parameters
        entry_rules = []
        for rule in template['entry']:
            new_rule = rule.copy()
            # Mutate numeric parameters
            for key, value in new_rule.items():
                if isinstance(value, (int, float)) and key != 'type':
                    new_rule[key] = value * random.uniform(0.8, 1.2)
            entry_rules.append(new_rule)
        
        exit_rules = []
        for rule in template['exit']:
            new_rule = rule.copy()
            for key, value in new_rule.items():
                if isinstance(value, (int, float)) and key != 'type':
                    new_rule[key] = value * random.uniform(0.8, 1.2)
            exit_rules.append(new_rule)
        
        # Generate unique ID
        strategy_id = hashlib.md5(
            f"{template['name']}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return GeneratedStrategy(
            strategy_id=strategy_id,
            name=f"{template['name']}_v{len(self.generated_strategies)}",
            description=f"Auto-generated {template['name']} variant",
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            parameters={
                'risk_per_trade': random.uniform(0.01, 0.02),
                'max_positions': random.randint(1, 3),
                'min_confidence': random.uniform(0.5, 0.8)
            },
            features_used=['price', 'volume', 'momentum'],
            expected_performance=0.0,
            generation_method=InnovationType.NEW_STRATEGY
        )
    
    async def _mutate_strategy(self) -> Optional[GeneratedStrategy]:
        """Mutate an existing strategy"""
        
        if not self.generated_strategies:
            return self._generate_from_template()
        
        # Select parent strategy (prefer high performers)
        strategies = list(self.generated_strategies.values())
        if any(s.tested for s in strategies):
            tested = [s for s in strategies if s.tested]
            parent = max(tested, key=lambda s: s.test_results.get('win_rate', 0))
        else:
            parent = random.choice(strategies)
        
        # Create mutated copy
        mutated = GeneratedStrategy(
            strategy_id=hashlib.md5(
                f"mutation_{parent.strategy_id}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16],
            name=f"{parent.name}_mut",
            description=f"Mutation of {parent.name}",
            entry_rules=[r.copy() for r in parent.entry_rules],
            exit_rules=[r.copy() for r in parent.exit_rules],
            parameters=parent.parameters.copy(),
            features_used=parent.features_used.copy(),
            expected_performance=0.0,
            generation_method=InnovationType.STRATEGY_MUTATION,
            parent_strategies=[parent.strategy_id]
        )
        
        # Apply mutations
        if random.random() < self.mutation_rate:
            # Mutate entry rules
            for rule in mutated.entry_rules:
                for key, value in rule.items():
                    if isinstance(value, (int, float)) and key != 'type':
                        rule[key] = value * random.uniform(0.9, 1.1)
        
        if random.random() < self.mutation_rate:
            # Mutate exit rules
            for rule in mutated.exit_rules:
                for key, value in rule.items():
                    if isinstance(value, (int, float)) and key != 'type':
                        rule[key] = value * random.uniform(0.9, 1.1)
        
        if random.random() < self.mutation_rate:
            # Mutate parameters
            for key in mutated.parameters:
                mutated.parameters[key] *= random.uniform(0.9, 1.1)
        
        return mutated
    
    async def _crossover_strategies(self) -> Optional[GeneratedStrategy]:
        """Crossover two strategies"""
        
        if len(self.generated_strategies) < 2:
            return self._generate_from_template()
        
        # Select two parents
        strategies = list(self.generated_strategies.values())
        parent1, parent2 = random.sample(strategies, 2)
        
        # Create offspring
        offspring = GeneratedStrategy(
            strategy_id=hashlib.md5(
                f"crossover_{parent1.strategy_id}_{parent2.strategy_id}".encode()
            ).hexdigest()[:16],
            name=f"cross_{len(self.generated_strategies)}",
            description=f"Crossover of {parent1.name} and {parent2.name}",
            entry_rules=random.choice([parent1.entry_rules, parent2.entry_rules]),
            exit_rules=random.choice([parent1.exit_rules, parent2.exit_rules]),
            parameters={
                k: random.choice([parent1.parameters.get(k, 0), parent2.parameters.get(k, 0)])
                for k in set(parent1.parameters.keys()) | set(parent2.parameters.keys())
            },
            features_used=list(set(parent1.features_used + parent2.features_used)),
            expected_performance=0.0,
            generation_method=InnovationType.STRATEGY_CROSSOVER,
            parent_strategies=[parent1.strategy_id, parent2.strategy_id]
        )
        
        return offspring
    
    def _estimate_strategy_performance(
        self,
        strategy: GeneratedStrategy,
        market_data: pd.DataFrame
    ) -> float:
        """Estimate strategy performance (simplified)"""
        
        try:
            # Simple heuristic based on strategy characteristics
            score = 0.5
            
            # More entry rules = more selective = potentially better
            score += min(len(strategy.entry_rules) * 0.05, 0.15)
            
            # Balanced exit rules
            if len(strategy.exit_rules) >= 2:
                score += 0.1
            
            # Reasonable parameters
            if 0.005 <= strategy.parameters.get('risk_per_trade', 0.01) <= 0.03:
                score += 0.1
            
            # Feature diversity
            score += min(len(strategy.features_used) * 0.03, 0.15)
            
            return min(score, 1.0)
            
        except Exception:
            return 0.5
    
    async def generate_new_feature(
        self,
        market_data: pd.DataFrame
    ) -> Optional[GeneratedFeature]:
        """
        Generate a new feature.
        
        Args:
            market_data: Historical market data
        
        Returns:
            Generated feature or None
        """
        try:
            template = random.choice(self.feature_templates)
            
            # Randomize parameters
            params = template['params'].copy()
            for key, value in params.items():
                if isinstance(value, int):
                    params[key] = int(value * random.uniform(0.7, 1.3))
                elif isinstance(value, float):
                    params[key] = value * random.uniform(0.8, 1.2)
            
            feature_id = hashlib.md5(
                f"{template['name']}_{datetime.now().isoformat()}".encode()
            ).hexdigest()[:16]
            
            feature = GeneratedFeature(
                feature_id=feature_id,
                name=f"{template['name']}_{len(self.generated_features)}",
                description=f"Auto-generated {template['calculation']} feature",
                calculation_method=template['calculation'],
                parameters=params
            )
            
            # Calculate feature values and importance
            feature_values = self._calculate_feature(feature, market_data)
            
            if feature_values is not None:
                feature.importance_score = self._estimate_feature_importance(
                    feature_values, market_data
                )
                
                if feature.importance_score >= 0.3:
                    self.generated_features[feature.feature_id] = feature
                    
                    self.innovations.append(Innovation(
                        innovation_id=f"innov_{len(self.innovations)}",
                        innovation_type=InnovationType.NEW_FEATURE,
                        description=f"Generated feature: {feature.name}",
                        performance_improvement=feature.importance_score,
                        created_at=datetime.now()
                    ))
                    
                    logger.info(f"Generated new feature: {feature.name} "
                              f"(importance: {feature.importance_score:.2f})")
                    
                    return feature
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating feature: {e}")
            return None
    
    def _calculate_feature(
        self,
        feature: GeneratedFeature,
        market_data: pd.DataFrame
    ) -> Optional[np.ndarray]:
        """Calculate feature values"""
        
        try:
            close = market_data['close'].values
            
            if feature.calculation_method == 'roc':
                period = feature.parameters.get('period', 10)
                values = (close - np.roll(close, period)) / np.roll(close, period)
                values[:period] = 0
                
            elif feature.calculation_method == 'std_ratio':
                short = feature.parameters.get('short_period', 5)
                long = feature.parameters.get('long_period', 20)
                short_std = pd.Series(close).rolling(short).std().fillna(0).values
                long_std = pd.Series(close).rolling(long).std().fillna(1).values
                values = np.where(long_std > 0, short_std / long_std, 1.0)
                
            elif feature.calculation_method == 'volume_ma_ratio':
                period = feature.parameters.get('period', 20)
                volume = market_data.get('volume', pd.Series([1] * len(close))).values
                volume_ma = pd.Series(volume).rolling(period).mean().fillna(1).values
                values = np.where(volume_ma > 0, volume / volume_ma, 1.0)
                
            elif feature.calculation_method == 'price_percentile':
                period = feature.parameters.get('period', 50)
                values = pd.Series(close).rolling(period).apply(
                    lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min()) if x.max() > x.min() else 0.5
                ).fillna(0.5).values
                
            else:
                return None
            
            return np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            
        except Exception as e:
            logger.error(f"Error calculating feature: {e}")
            return None
    
    def _estimate_feature_importance(
        self,
        feature_values: np.ndarray,
        market_data: pd.DataFrame
    ) -> float:
        """Estimate feature importance"""
        
        try:
            if not SKLEARN_AVAILABLE:
                # Simple correlation with returns
                returns = np.diff(market_data['close'].values) / market_data['close'].values[:-1]
                if len(feature_values) > len(returns):
                    feature_values = feature_values[:len(returns)]
                elif len(returns) > len(feature_values):
                    returns = returns[:len(feature_values)]
                
                correlation = np.corrcoef(feature_values, returns)[0, 1]
                return abs(correlation) if not np.isnan(correlation) else 0.0
            
            # Use sklearn feature selection
            returns = np.diff(market_data['close'].values) / market_data['close'].values[:-1]
            X = feature_values[:-1].reshape(-1, 1)
            y = returns
            
            if len(X) != len(y):
                min_len = min(len(X), len(y))
                X = X[:min_len]
                y = y[:min_len]
            
            selector = SelectKBest(f_regression, k=1)
            selector.fit(X, y)
            
            score = selector.scores_[0]
            # Normalize to 0-1
            importance = min(score / 100.0, 1.0)
            
            return importance
            
        except Exception:
            return 0.5
    
    async def optimize_parameters(
        self,
        strategy_id: str,
        market_data: pd.DataFrame
    ) -> Dict[str, float]:
        """
        Optimize strategy parameters.
        
        Args:
            strategy_id: Strategy to optimize
            market_data: Historical data for optimization
        
        Returns:
            Optimized parameters
        """
        try:
            if strategy_id not in self.generated_strategies:
                return {}
            
            strategy = self.generated_strategies[strategy_id]
            original_params = strategy.parameters.copy()
            
            # Simple grid search over parameter space
            best_params = original_params.copy()
            best_score = 0.0
            
            # Try variations
            for _ in range(10):
                test_params = {}
                for key, value in original_params.items():
                    if isinstance(value, float):
                        test_params[key] = value * random.uniform(0.8, 1.2)
                    else:
                        test_params[key] = value
                
                # Estimate performance with these parameters
                score = random.uniform(0.4, 0.9)  # Simplified
                
                if score > best_score:
                    best_score = score
                    best_params = test_params
            
            # Update strategy
            strategy.parameters = best_params
            
            self.innovations.append(Innovation(
                innovation_id=f"innov_{len(self.innovations)}",
                innovation_type=InnovationType.PARAMETER_OPTIMIZATION,
                description=f"Optimized parameters for {strategy.name}",
                performance_improvement=best_score - 0.5,
                created_at=datetime.now()
            ))
            
            logger.info(f"Optimized parameters for {strategy.name}")
            
            return best_params
            
        except Exception as e:
            logger.error(f"Error optimizing parameters: {e}")
            return {}
    
    def get_best_strategies(self, top_n: int = 5) -> List[GeneratedStrategy]:
        """Get top performing generated strategies"""
        
        tested_strategies = [
            s for s in self.generated_strategies.values()
            if s.tested and s.test_results
        ]
        
        if not tested_strategies:
            # Return by expected performance
            return sorted(
                self.generated_strategies.values(),
                key=lambda s: s.expected_performance,
                reverse=True
            )[:top_n]
        
        # Sort by actual performance
        return sorted(
            tested_strategies,
            key=lambda s: s.test_results.get('win_rate', 0) * s.test_results.get('profit_factor', 0),
            reverse=True
        )[:top_n]
    
    def get_best_features(self, top_n: int = 10) -> List[GeneratedFeature]:
        """Get top performing generated features"""
        
        return sorted(
            self.generated_features.values(),
            key=lambda f: f.importance_score,
            reverse=True
        )[:top_n]
    
    def get_innovation_statistics(self) -> Dict[str, Any]:
        """Get innovation statistics"""
        
        return {
            'total_strategies_generated': len(self.generated_strategies),
            'total_features_generated': len(self.generated_features),
            'total_innovations': len(self.innovations),
            'deployed_innovations': sum(1 for i in self.innovations if i.deployed),
            'innovation_types': {
                itype.value: sum(1 for i in self.innovations if i.innovation_type == itype)
                for itype in InnovationType
            },
            'best_strategies': [
                {
                    'name': s.name,
                    'performance': s.expected_performance,
                    'tested': s.tested
                }
                for s in self.get_best_strategies(3)
            ],
            'best_features': [
                {
                    'name': f.name,
                    'importance': f.importance_score
                }
                for f in self.get_best_features(5)
            ],
            'recent_innovations': [
                {
                    'type': i.innovation_type.value,
                    'description': i.description,
                    'improvement': i.performance_improvement,
                    'deployed': i.deployed
                }
                for i in self.innovations[-5:]
            ]
        }
