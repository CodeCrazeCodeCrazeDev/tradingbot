"""
Automated Feature Engineering
=============================

Automatically discovers and creates optimal features
for trading strategies using genetic programming and
automated transformations.
"""

import hashlib
import logging
import math
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
import numpy as np

logger = logging.getLogger(__name__)


class TransformationType(Enum):
    """Types of feature transformations"""
    # Unary operations
    LOG = "log"
    SQRT = "sqrt"
    SQUARE = "square"
    ABS = "abs"
    SIGN = "sign"
    INVERSE = "inverse"
    EXP = "exp"
    TANH = "tanh"
    SIGMOID = "sigmoid"
    NORMALIZE = "normalize"
    STANDARDIZE = "standardize"
    RANK = "rank"
    DIFF = "diff"
    PCT_CHANGE = "pct_change"
    CUMSUM = "cumsum"
    CUMPROD = "cumprod"
    
    # Binary operations
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    MAX = "max"
    MIN = "min"
    CORRELATION = "correlation"
    COVARIANCE = "covariance"
    
    # Rolling operations
    ROLLING_MEAN = "rolling_mean"
    ROLLING_STD = "rolling_std"
    ROLLING_MIN = "rolling_min"
    ROLLING_MAX = "rolling_max"
    ROLLING_SUM = "rolling_sum"
    ROLLING_SKEW = "rolling_skew"
    ROLLING_KURT = "rolling_kurt"
    ROLLING_ZSCORE = "rolling_zscore"
    EMA = "ema"
    
    # Lag operations
    LAG = "lag"
    LEAD = "lead"
    DELTA = "delta"
    
    # Technical indicators
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    ATR = "atr"
    ADX = "adx"
    MOMENTUM = "momentum"
    ROC = "roc"
    WILLIAMS_R = "williams_r"
    STOCHASTIC = "stochastic"


@dataclass
class Feature:
    """A generated feature"""
    feature_id: str
    name: str
    expression: str
    transformations: List[Tuple[TransformationType, Dict[str, Any]]]
    source_features: List[str]
    importance: float = 0.0
    correlation_with_target: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'feature_id': self.feature_id,
            'name': self.name,
            'expression': self.expression,
            'importance': self.importance,
            'correlation': self.correlation_with_target
        }


@dataclass
class FeatureSet:
    """A set of features"""
    features: List[Feature]
    fitness: float = 0.0
    generation: int = 0
    
    def get_feature_names(self) -> List[str]:
        return [f.name for f in self.features]


class FeatureTransformer:
    """Applies transformations to create new features"""
    
    @staticmethod
    def apply_unary(
        data: np.ndarray,
        transform: TransformationType,
        params: Dict[str, Any] = None
    ) -> np.ndarray:
        """Apply unary transformation"""
        params = params or {}
        eps = 1e-10
        
        if transform == TransformationType.LOG:
            return np.log(np.abs(data) + eps)
        
        elif transform == TransformationType.SQRT:
            return np.sqrt(np.abs(data))
        
        elif transform == TransformationType.SQUARE:
            return data ** 2
        
        elif transform == TransformationType.ABS:
            return np.abs(data)
        
        elif transform == TransformationType.SIGN:
            return np.sign(data)
        
        elif transform == TransformationType.INVERSE:
            return 1.0 / (data + eps)
        
        elif transform == TransformationType.EXP:
            return np.exp(np.clip(data, -10, 10))
        
        elif transform == TransformationType.TANH:
            return np.tanh(data)
        
        elif transform == TransformationType.SIGMOID:
            return 1.0 / (1.0 + np.exp(-np.clip(data, -10, 10)))
        
        elif transform == TransformationType.NORMALIZE:
            min_val, max_val = np.min(data), np.max(data)
            return (data - min_val) / (max_val - min_val + eps)
        
        elif transform == TransformationType.STANDARDIZE:
            return (data - np.mean(data)) / (np.std(data) + eps)
        
        elif transform == TransformationType.RANK:
            return np.argsort(np.argsort(data)).astype(float) / len(data)
        
        elif transform == TransformationType.DIFF:
            result = np.diff(data, prepend=data[0])
            return result
        
        elif transform == TransformationType.PCT_CHANGE:
            shifted = np.roll(data, 1)
            shifted[0] = data[0]
            return (data - shifted) / (np.abs(shifted) + eps)
        
        elif transform == TransformationType.CUMSUM:
            return np.cumsum(data)
        
        elif transform == TransformationType.CUMPROD:
            return np.cumprod(1 + data / 100)  # Assume percentage returns
        
        return data
    
    @staticmethod
    def apply_binary(
        data1: np.ndarray,
        data2: np.ndarray,
        transform: TransformationType,
        params: Dict[str, Any] = None
    ) -> np.ndarray:
        """Apply binary transformation"""
        params = params or {}
        eps = 1e-10
        
        if transform == TransformationType.ADD:
            return data1 + data2
        
        elif transform == TransformationType.SUBTRACT:
            return data1 - data2
        
        elif transform == TransformationType.MULTIPLY:
            return data1 * data2
        
        elif transform == TransformationType.DIVIDE:
            return data1 / (data2 + eps)
        
        elif transform == TransformationType.MAX:
            return np.maximum(data1, data2)
        
        elif transform == TransformationType.MIN:
            return np.minimum(data1, data2)
        
        elif transform == TransformationType.CORRELATION:
            window = params.get('window', 20)
            result = np.zeros_like(data1)
            for i in range(window, len(data1)):
                result[i] = np.corrcoef(data1[i-window:i], data2[i-window:i])[0, 1]
            return result
        
        elif transform == TransformationType.COVARIANCE:
            window = params.get('window', 20)
            result = np.zeros_like(data1)
            for i in range(window, len(data1)):
                result[i] = np.cov(data1[i-window:i], data2[i-window:i])[0, 1]
            return result
        
        return data1
    
    @staticmethod
    def apply_rolling(
        data: np.ndarray,
        transform: TransformationType,
        params: Dict[str, Any] = None
    ) -> np.ndarray:
        """Apply rolling window transformation"""
        params = params or {}
        window = params.get('window', 20)
        eps = 1e-10
        
        result = np.zeros_like(data)
        
        for i in range(len(data)):
            start = max(0, i - window + 1)
            window_data = data[start:i+1]
            
            if len(window_data) == 0:
                continue
            
            if transform == TransformationType.ROLLING_MEAN:
                result[i] = np.mean(window_data)
            
            elif transform == TransformationType.ROLLING_STD:
                result[i] = np.std(window_data) if len(window_data) > 1 else 0
            
            elif transform == TransformationType.ROLLING_MIN:
                result[i] = np.min(window_data)
            
            elif transform == TransformationType.ROLLING_MAX:
                result[i] = np.max(window_data)
            
            elif transform == TransformationType.ROLLING_SUM:
                result[i] = np.sum(window_data)
            
            elif transform == TransformationType.ROLLING_SKEW:
                if len(window_data) > 2:
                    mean = np.mean(window_data)
                    std = np.std(window_data) + eps
                    result[i] = np.mean(((window_data - mean) / std) ** 3)
            
            elif transform == TransformationType.ROLLING_KURT:
                if len(window_data) > 3:
                    mean = np.mean(window_data)
                    std = np.std(window_data) + eps
                    result[i] = np.mean(((window_data - mean) / std) ** 4) - 3
            
            elif transform == TransformationType.ROLLING_ZSCORE:
                mean = np.mean(window_data)
                std = np.std(window_data) + eps
                result[i] = (data[i] - mean) / std
            
            elif transform == TransformationType.EMA:
                alpha = 2.0 / (window + 1)
                if i == 0:
                    result[i] = data[i]
                else:
                    result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
        
        return result
    
    @staticmethod
    def apply_lag(
        data: np.ndarray,
        transform: TransformationType,
        params: Dict[str, Any] = None
    ) -> np.ndarray:
        """Apply lag/lead transformation"""
        params = params or {}
        periods = params.get('periods', 1)
        
        if transform == TransformationType.LAG:
            result = np.roll(data, periods)
            result[:periods] = data[0]
            return result
        
        elif transform == TransformationType.LEAD:
            result = np.roll(data, -periods)
            result[-periods:] = data[-1]
            return result
        
        elif transform == TransformationType.DELTA:
            lagged = np.roll(data, periods)
            lagged[:periods] = data[0]
            return data - lagged
        
        return data
    
    @staticmethod
    def apply_technical(
        data: np.ndarray,
        transform: TransformationType,
        params: Dict[str, Any] = None,
        high: Optional[np.ndarray] = None,
        low: Optional[np.ndarray] = None,
        close: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Apply technical indicator transformation"""
        params = params or {}
        period = params.get('period', 14)
        eps = 1e-10
        
        if transform == TransformationType.RSI:
            delta = np.diff(data, prepend=data[0])
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            
            avg_gain = FeatureTransformer.apply_rolling(
                gain, TransformationType.ROLLING_MEAN, {'window': period}
            )
            avg_loss = FeatureTransformer.apply_rolling(
                loss, TransformationType.ROLLING_MEAN, {'window': period}
            )
            
            rs = avg_gain / (avg_loss + eps)
            return 100 - (100 / (1 + rs))
        
        elif transform == TransformationType.MACD:
            fast = params.get('fast', 12)
            slow = params.get('slow', 26)
            
            ema_fast = FeatureTransformer.apply_rolling(
                data, TransformationType.EMA, {'window': fast}
            )
            ema_slow = FeatureTransformer.apply_rolling(
                data, TransformationType.EMA, {'window': slow}
            )
            
            return ema_fast - ema_slow
        
        elif transform == TransformationType.BOLLINGER:
            band = params.get('band', 'middle')  # 'upper', 'middle', 'lower', 'width'
            std_mult = params.get('std_mult', 2)
            
            middle = FeatureTransformer.apply_rolling(
                data, TransformationType.ROLLING_MEAN, {'window': period}
            )
            std = FeatureTransformer.apply_rolling(
                data, TransformationType.ROLLING_STD, {'window': period}
            )
            
            if band == 'upper':
                return middle + std_mult * std
            elif band == 'lower':
                return middle - std_mult * std
            elif band == 'width':
                return 2 * std_mult * std / (middle + eps)
            else:
                return middle
        
        elif transform == TransformationType.ATR:
            if high is not None and low is not None and close is not None:
                prev_close = np.roll(close, 1)
                prev_close[0] = close[0]
                
                tr = np.maximum(
                    high - low,
                    np.maximum(
                        np.abs(high - prev_close),
                        np.abs(low - prev_close)
                    )
                )
                
                return FeatureTransformer.apply_rolling(
                    tr, TransformationType.ROLLING_MEAN, {'window': period}
                )
            return data
        
        elif transform == TransformationType.MOMENTUM:
            lagged = np.roll(data, period)
            lagged[:period] = data[0]
            return data - lagged
        
        elif transform == TransformationType.ROC:
            lagged = np.roll(data, period)
            lagged[:period] = data[0]
            return (data - lagged) / (np.abs(lagged) + eps) * 100
        
        elif transform == TransformationType.WILLIAMS_R:
            if high is not None and low is not None:
                highest = FeatureTransformer.apply_rolling(
                    high, TransformationType.ROLLING_MAX, {'window': period}
                )
                lowest = FeatureTransformer.apply_rolling(
                    low, TransformationType.ROLLING_MIN, {'window': period}
                )
                return -100 * (highest - data) / (highest - lowest + eps)
            return data
        
        elif transform == TransformationType.STOCHASTIC:
            if high is not None and low is not None:
                highest = FeatureTransformer.apply_rolling(
                    high, TransformationType.ROLLING_MAX, {'window': period}
                )
                lowest = FeatureTransformer.apply_rolling(
                    low, TransformationType.ROLLING_MIN, {'window': period}
                )
                return 100 * (data - lowest) / (highest - lowest + eps)
            return data
        
        return data


class GeneticFeatureEvolution:
    """
    Genetic Programming for Feature Evolution
    
    Evolves optimal feature combinations using genetic algorithms.
    """
    
    def __init__(
        self,
        population_size: int = 100,
        max_features: int = 50,
        max_depth: int = 3,
        mutation_rate: float = 0.3,
        crossover_rate: float = 0.7,
        elite_ratio: float = 0.1
    ):
        self.population_size = population_size
        self.max_features = max_features
        self.max_depth = max_depth
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_ratio = elite_ratio
        
        self.population: List[FeatureSet] = []
        self.generation = 0
        self.best_feature_set: Optional[FeatureSet] = None
        
        # Available transformations by category
        self.unary_transforms = [
            TransformationType.LOG, TransformationType.SQRT,
            TransformationType.SQUARE, TransformationType.ABS,
            TransformationType.SIGN, TransformationType.TANH,
            TransformationType.SIGMOID, TransformationType.NORMALIZE,
            TransformationType.STANDARDIZE, TransformationType.RANK,
            TransformationType.DIFF, TransformationType.PCT_CHANGE
        ]
        
        self.rolling_transforms = [
            TransformationType.ROLLING_MEAN, TransformationType.ROLLING_STD,
            TransformationType.ROLLING_MIN, TransformationType.ROLLING_MAX,
            TransformationType.ROLLING_ZSCORE, TransformationType.EMA
        ]
        
        self.technical_transforms = [
            TransformationType.RSI, TransformationType.MACD,
            TransformationType.BOLLINGER, TransformationType.MOMENTUM,
            TransformationType.ROC
        ]
        
        logger.info("GeneticFeatureEvolution initialized")
    
    def _generate_random_feature(
        self,
        source_features: List[str],
        depth: int = 0
    ) -> Feature:
        """Generate a random feature"""
        
        # Select source feature(s)
        num_sources = random.randint(1, min(2, len(source_features)))
        selected_sources = random.sample(source_features, num_sources)
        
        # Generate transformation chain
        transformations = []
        num_transforms = random.randint(1, self.max_depth - depth)
        
        for _ in range(num_transforms):
            transform_type = random.choice([
                'unary', 'rolling', 'technical', 'lag'
            ])
            
            if transform_type == 'unary':
                transform = random.choice(self.unary_transforms)
                params = {}
            
            elif transform_type == 'rolling':
                transform = random.choice(self.rolling_transforms)
                params = {'window': random.choice([5, 10, 20, 50, 100])}
            
            elif transform_type == 'technical':
                transform = random.choice(self.technical_transforms)
                params = {'period': random.choice([7, 14, 21, 28])}
            
            else:  # lag
                transform = random.choice([
                    TransformationType.LAG, TransformationType.DELTA
                ])
                params = {'periods': random.choice([1, 2, 3, 5, 10])}
            
            transformations.append((transform, params))
        
        # Generate expression string
        expr_parts = []
        for t, p in transformations:
            if p:
                expr_parts.append(f"{t.value}({p})")
            else:
                expr_parts.append(t.value)
        
        expression = " -> ".join([str(selected_sources)] + expr_parts)
        
        # Generate ID
        feature_id = hashlib.sha256(
            f"{expression}:{datetime.utcnow().isoformat()}:{random.random()}".encode()
        ).hexdigest()[:12]
        
        return Feature(
            feature_id=feature_id,
            name=f"feat_{feature_id[:6]}",
            expression=expression,
            transformations=transformations,
            source_features=selected_sources
        )
    
    def initialize_population(self, source_features: List[str]):
        """Initialize random population"""
        
        self.population = []
        
        for _ in range(self.population_size):
            num_features = random.randint(5, self.max_features)
            features = [
                self._generate_random_feature(source_features)
                for _ in range(num_features)
            ]
            self.population.append(FeatureSet(features=features))
        
        logger.info(f"Initialized population with {len(self.population)} feature sets")
    
    def evaluate_feature_set(
        self,
        feature_set: FeatureSet,
        data: Dict[str, np.ndarray],
        target: np.ndarray,
        fitness_function: Optional[Callable] = None
    ) -> float:
        """Evaluate fitness of a feature set"""
        
        if fitness_function:
            return fitness_function(feature_set, data, target)
        
        # Default: correlation-based fitness
        total_correlation = 0.0
        valid_features = 0
        
        for feature in feature_set.features:
            try:
                # Apply transformations
                feature_data = data[feature.source_features[0]].copy()
                
                for transform, params in feature.transformations:
                    if transform in self.unary_transforms:
                        feature_data = FeatureTransformer.apply_unary(
                            feature_data, transform, params
                        )
                    elif transform in self.rolling_transforms:
                        feature_data = FeatureTransformer.apply_rolling(
                            feature_data, transform, params
                        )
                    elif transform in [TransformationType.LAG, TransformationType.DELTA]:
                        feature_data = FeatureTransformer.apply_lag(
                            feature_data, transform, params
                        )
                    elif transform in self.technical_transforms:
                        feature_data = FeatureTransformer.apply_technical(
                            feature_data, transform, params
                        )
                
                # Remove NaN/Inf
                valid_mask = np.isfinite(feature_data) & np.isfinite(target)
                if np.sum(valid_mask) > 10:
                    corr = np.abs(np.corrcoef(
                        feature_data[valid_mask],
                        target[valid_mask]
                    )[0, 1])
                    
                    if np.isfinite(corr):
                        feature.correlation_with_target = corr
                        total_correlation += corr
                        valid_features += 1
            
            except Exception as e:
                logger.debug(f"Error evaluating feature: {e}")
                continue
        
        if valid_features == 0:
            return 0.0
        
        # Fitness = average correlation with penalty for too many features
        avg_correlation = total_correlation / valid_features
        complexity_penalty = 0.001 * len(feature_set.features)
        
        fitness = avg_correlation - complexity_penalty
        feature_set.fitness = max(0, fitness)
        
        return feature_set.fitness
    
    def _crossover(
        self,
        parent1: FeatureSet,
        parent2: FeatureSet
    ) -> FeatureSet:
        """Crossover two feature sets"""
        
        if random.random() > self.crossover_rate:
            return FeatureSet(
                features=list(parent1.features if random.random() > 0.5 else parent2.features),
                generation=self.generation
            )
        
        # Combine features from both parents
        all_features = parent1.features + parent2.features
        
        # Select subset
        num_features = random.randint(
            min(len(parent1.features), len(parent2.features)),
            min(self.max_features, len(all_features))
        )
        
        selected = random.sample(all_features, num_features)
        
        return FeatureSet(features=selected, generation=self.generation)
    
    def _mutate(
        self,
        feature_set: FeatureSet,
        source_features: List[str]
    ) -> FeatureSet:
        """Mutate a feature set"""
        
        if random.random() > self.mutation_rate:
            return feature_set
        
        new_features = list(feature_set.features)
        
        mutation_type = random.choice([
            'add', 'remove', 'modify', 'replace'
        ])
        
        if mutation_type == 'add' and len(new_features) < self.max_features:
            new_features.append(self._generate_random_feature(source_features))
        
        elif mutation_type == 'remove' and len(new_features) > 1:
            new_features.pop(random.randint(0, len(new_features) - 1))
        
        elif mutation_type == 'modify' and new_features:
            idx = random.randint(0, len(new_features) - 1)
            feature = new_features[idx]
            
            # Modify a transformation
            if feature.transformations:
                t_idx = random.randint(0, len(feature.transformations) - 1)
                transform_type = random.choice(['unary', 'rolling'])
                
                if transform_type == 'unary':
                    new_transform = random.choice(self.unary_transforms)
                    new_params = {}
                else:
                    new_transform = random.choice(self.rolling_transforms)
                    new_params = {'window': random.choice([5, 10, 20, 50])}
                
                new_transformations = list(feature.transformations)
                new_transformations[t_idx] = (new_transform, new_params)
                
                new_features[idx] = Feature(
                    feature_id=feature.feature_id + "_m",
                    name=feature.name + "_m",
                    expression=feature.expression + " [mutated]",
                    transformations=new_transformations,
                    source_features=feature.source_features
                )
        
        elif mutation_type == 'replace' and new_features:
            idx = random.randint(0, len(new_features) - 1)
            new_features[idx] = self._generate_random_feature(source_features)
        
        return FeatureSet(features=new_features, generation=self.generation)
    
    def evolve_generation(
        self,
        data: Dict[str, np.ndarray],
        target: np.ndarray,
        source_features: List[str],
        fitness_function: Optional[Callable] = None
    ) -> FeatureSet:
        """Evolve one generation"""
        
        self.generation += 1
        
        # Evaluate all
        for fs in self.population:
            if fs.fitness == 0.0:
                self.evaluate_feature_set(fs, data, target, fitness_function)
        
        # Sort by fitness
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # Update best
        if self.population and (
            self.best_feature_set is None or
            self.population[0].fitness > self.best_feature_set.fitness
        ):
            self.best_feature_set = self.population[0]
        
        # Elite selection
        elite_count = max(1, int(self.population_size * self.elite_ratio))
        new_population = self.population[:elite_count]
        
        # Generate offspring
        while len(new_population) < self.population_size:
            # Tournament selection
            tournament = random.sample(self.population, min(5, len(self.population)))
            parent1 = max(tournament, key=lambda x: x.fitness)
            
            tournament = random.sample(self.population, min(5, len(self.population)))
            parent2 = max(tournament, key=lambda x: x.fitness)
            
            child = self._crossover(parent1, parent2)
            child = self._mutate(child, source_features)
            new_population.append(child)
        
        self.population = new_population
        
        logger.info(
            f"Generation {self.generation}: "
            f"Best fitness = {self.population[0].fitness:.4f}, "
            f"Features = {len(self.population[0].features)}"
        )
        
        return self.best_feature_set
    
    async def evolve(
        self,
        data: Dict[str, np.ndarray],
        target: np.ndarray,
        source_features: List[str],
        num_generations: int = 50,
        fitness_function: Optional[Callable] = None
    ) -> FeatureSet:
        """Run full evolution"""
        
        logger.info(f"Starting feature evolution for {num_generations} generations")
        
        self.initialize_population(source_features)
        
        for _ in range(num_generations):
            self.evolve_generation(data, target, source_features, fitness_function)
        
        logger.info(
            f"Evolution complete. Best feature set has {len(self.best_feature_set.features)} features "
            f"with fitness {self.best_feature_set.fitness:.4f}"
        )
        
        return self.best_feature_set


class AutoFeatureEngine:
    """
    Automated Feature Engineering Engine
    
    High-level interface for automatic feature discovery.
    """
    
    def __init__(
        self,
        max_features: int = 100,
        correlation_threshold: float = 0.95,
        importance_threshold: float = 0.01
    ):
        self.max_features = max_features
        self.correlation_threshold = correlation_threshold
        self.importance_threshold = importance_threshold
        
        self.genetic_evolver = GeneticFeatureEvolution(max_features=max_features)
        self.generated_features: List[Feature] = []
        self.feature_matrix: Optional[np.ndarray] = None
        
        logger.info("AutoFeatureEngine initialized")
    
    def generate_base_features(
        self,
        data: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """Generate base technical features"""
        
        features = {}
        
        for name, values in data.items():
            # Original
            features[name] = values
            
            # Basic transforms
            features[f"{name}_log"] = FeatureTransformer.apply_unary(
                values, TransformationType.LOG
            )
            features[f"{name}_pct"] = FeatureTransformer.apply_unary(
                values, TransformationType.PCT_CHANGE
            )
            
            # Rolling features
            for window in [5, 10, 20, 50]:
                features[f"{name}_sma_{window}"] = FeatureTransformer.apply_rolling(
                    values, TransformationType.ROLLING_MEAN, {'window': window}
                )
                features[f"{name}_std_{window}"] = FeatureTransformer.apply_rolling(
                    values, TransformationType.ROLLING_STD, {'window': window}
                )
                features[f"{name}_zscore_{window}"] = FeatureTransformer.apply_rolling(
                    values, TransformationType.ROLLING_ZSCORE, {'window': window}
                )
            
            # Technical indicators
            features[f"{name}_rsi"] = FeatureTransformer.apply_technical(
                values, TransformationType.RSI
            )
            features[f"{name}_macd"] = FeatureTransformer.apply_technical(
                values, TransformationType.MACD
            )
            features[f"{name}_mom"] = FeatureTransformer.apply_technical(
                values, TransformationType.MOMENTUM
            )
            
            # Lags
            for lag in [1, 2, 3, 5, 10]:
                features[f"{name}_lag_{lag}"] = FeatureTransformer.apply_lag(
                    values, TransformationType.LAG, {'periods': lag}
                )
                features[f"{name}_delta_{lag}"] = FeatureTransformer.apply_lag(
                    values, TransformationType.DELTA, {'periods': lag}
                )
        
        logger.info(f"Generated {len(features)} base features")
        return features
    
    def remove_correlated_features(
        self,
        features: Dict[str, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        """Remove highly correlated features"""
        
        feature_names = list(features.keys())
        n_features = len(feature_names)
        
        # Build correlation matrix
        feature_matrix = np.column_stack([features[name] for name in feature_names])
        
        # Handle NaN/Inf
        feature_matrix = np.nan_to_num(feature_matrix, nan=0, posinf=0, neginf=0)
        
        # Compute correlations
        corr_matrix = np.corrcoef(feature_matrix.T)
        
        # Find features to remove
        to_remove = set()
        
        for i in range(n_features):
            if i in to_remove:
                continue
            for j in range(i + 1, n_features):
                if j in to_remove:
                    continue
                if abs(corr_matrix[i, j]) > self.correlation_threshold:
                    to_remove.add(j)
        
        # Filter features
        filtered = {
            name: values
            for idx, (name, values) in enumerate(features.items())
            if idx not in to_remove
        }
        
        logger.info(f"Removed {len(to_remove)} correlated features, {len(filtered)} remaining")
        return filtered
    
    def select_top_features(
        self,
        features: Dict[str, np.ndarray],
        target: np.ndarray,
        n_features: int = 50
    ) -> Dict[str, np.ndarray]:
        """Select top features by importance"""
        
        importances = {}
        
        for name, values in features.items():
            # Handle NaN/Inf
            valid_mask = np.isfinite(values) & np.isfinite(target)
            
            if np.sum(valid_mask) > 10:
                try:
                    corr = abs(np.corrcoef(values[valid_mask], target[valid_mask])[0, 1])
                    if np.isfinite(corr):
                        importances[name] = corr
                except:
                    pass
        
        # Sort by importance
        sorted_features = sorted(importances.items(), key=lambda x: x[1], reverse=True)
        
        # Select top N
        selected_names = [name for name, _ in sorted_features[:n_features]]
        
        selected = {name: features[name] for name in selected_names}
        
        logger.info(f"Selected top {len(selected)} features")
        return selected
    
    async def auto_engineer(
        self,
        data: Dict[str, np.ndarray],
        target: np.ndarray,
        use_genetic: bool = True,
        num_generations: int = 20
    ) -> Dict[str, np.ndarray]:
        """
        Automatically engineer features
        
        Args:
            data: Raw input data
            target: Target variable
            use_genetic: Whether to use genetic evolution
            num_generations: Generations for genetic evolution
        
        Returns:
            Dictionary of engineered features
        """
        
        logger.info("Starting automated feature engineering")
        
        # Generate base features
        features = self.generate_base_features(data)
        
        # Remove correlated
        features = self.remove_correlated_features(features)
        
        # Select top features
        features = self.select_top_features(features, target, self.max_features)
        
        # Optionally use genetic evolution
        if use_genetic:
            source_features = list(data.keys())
            best_set = await self.genetic_evolver.evolve(
                data, target, source_features, num_generations
            )
            
            # Add evolved features
            for feature in best_set.features[:20]:  # Top 20 evolved
                try:
                    feature_data = data[feature.source_features[0]].copy()
                    
                    for transform, params in feature.transformations:
                        feature_data = FeatureTransformer.apply_unary(
                            feature_data, transform, params
                        )
                    
                    features[feature.name] = feature_data
                except:
                    pass
        
        # Final cleanup
        features = self.remove_correlated_features(features)
        
        logger.info(f"Feature engineering complete: {len(features)} features")
        
        return features
    
    def get_report(self) -> Dict[str, Any]:
        """Get feature engineering report"""
        
        return {
            'total_features': len(self.generated_features),
            'genetic_generations': self.genetic_evolver.generation,
            'best_fitness': (
                self.genetic_evolver.best_feature_set.fitness
                if self.genetic_evolver.best_feature_set else 0
            ),
            'top_features': [
                f.to_dict()
                for f in sorted(
                    self.generated_features,
                    key=lambda x: x.importance,
                    reverse=True
                )[:10]
            ]
        }


# Convenience functions
async def auto_engineer_features(
    data: Dict[str, np.ndarray],
    target: np.ndarray,
    max_features: int = 50
) -> Dict[str, np.ndarray]:
    """Quick feature engineering"""
    
    engine = AutoFeatureEngine(max_features=max_features)
    return await engine.auto_engineer(data, target)


def create_feature_engine(max_features: int = 50, **kwargs) -> AutoFeatureEngine:
    """
    Create an AutoFeatureEngine instance.
    
    Args:
        max_features: Maximum number of features to generate
        **kwargs: Additional arguments for the engine
        
    Returns:
        AutoFeatureEngine instance
    """
    return AutoFeatureEngine(max_features=max_features, **kwargs)
