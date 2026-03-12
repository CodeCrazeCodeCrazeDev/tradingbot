import logging
logger = logging.getLogger(__name__)
"""Meta-Learning for Strategy Discovery.

This module implements meta-learning capabilities that enable the trading bot
to discover new strategies and adapt its learning approach based on experience.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import itertools
from collections import defaultdict
import numpy
import pandas


class StrategyComponent(Enum):
    """Components that can be combined to form strategies."""
    ENTRY_SIGNAL = "entry_signal"
    EXIT_SIGNAL = "exit_signal"
    RISK_MANAGEMENT = "risk_management"
    POSITION_SIZING = "position_sizing"
    MARKET_FILTER = "market_filter"
    TIME_FILTER = "time_filter"


@dataclass
class StrategyBlueprint:
    """Blueprint for a discovered strategy."""
    strategy_id: str
    components: Dict[StrategyComponent, str]
    performance_score: float
    discovery_date: datetime
    test_results: Dict[str, float]
    confidence: float
    complexity_score: float
    market_regimes: List[str]
    validation_trades: int = 0
    live_performance: float = 0.0
    active: bool = True


@dataclass
class LearningMetaData:
    """Metadata about the learning process itself."""
    learning_speed: float
    adaptation_rate: float
    exploration_vs_exploitation: float
    successful_patterns: List[str]
    failed_patterns: List[str]
    optimal_learning_conditions: Dict[str, Any]


class MetaLearningEngine:
    """Advanced meta-learning system for strategy discovery and learning optimization."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the meta-learning engine."""
        try:
            self.config = config or {}
            self.discovered_strategies = {}
            self.strategy_components = {}
            self.learning_metadata = LearningMetaData(
                learning_speed=0.5,
                adaptation_rate=0.3,
                exploration_vs_exploitation=0.7,
                successful_patterns=[],
                failed_patterns=[],
                optimal_learning_conditions={}
            )
        
            # Meta-learning parameters
            self.exploration_rate = self.config.get('exploration_rate', 0.3)
            self.min_validation_trades = self.config.get('min_validation_trades', 50)
            self.strategy_complexity_limit = self.config.get('complexity_limit', 5)
        
            # Component library
            self._initialize_component_library()
        
            # Performance tracking
            self.strategy_performance_history = defaultdict(list)
            self.learning_performance_history = []
        
            logger.info("MetaLearningEngine initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_component_library(self):
        """Initialize the library of strategy components."""
        try:
            self.strategy_components = {
                StrategyComponent.ENTRY_SIGNAL: {
                    'rsi_oversold': {'type': 'momentum', 'params': {'period': 14, 'threshold': 30}},
                    'ma_crossover': {'type': 'trend', 'params': {'fast': 10, 'slow': 20}},
                    'bollinger_breakout': {'type': 'volatility', 'params': {'period': 20, 'std': 2}},
                    'sentiment_alignment': {'type': 'sentiment', 'params': {'threshold': 0.6}},
                    'volume_spike': {'type': 'volume', 'params': {'multiplier': 2.0}},
                    'price_pattern': {'type': 'pattern', 'params': {'pattern': 'hammer'}},
                    'regime_confirmation': {'type': 'regime', 'params': {'confidence': 0.7}}
                },
            
                StrategyComponent.EXIT_SIGNAL: {
                    'fixed_target': {'type': 'fixed', 'params': {'ratio': 2.0}},
                    'trailing_stop': {'type': 'dynamic', 'params': {'atr_multiplier': 2.0}},
                    'time_based': {'type': 'time', 'params': {'max_hours': 24}},
                    'rsi_overbought': {'type': 'momentum', 'params': {'threshold': 70}},
                    'bollinger_reversion': {'type': 'mean_reversion', 'params': {'band': 'upper'}},
                    'sentiment_reversal': {'type': 'sentiment', 'params': {'threshold': -0.3}},
                    'volatility_expansion': {'type': 'volatility', 'params': {'expansion_ratio': 1.5}}
                },
            
                StrategyComponent.RISK_MANAGEMENT: {
                    'fixed_percent': {'type': 'fixed', 'params': {'risk_percent': 0.02}},
                    'atr_based': {'type': 'volatility', 'params': {'atr_multiplier': 2.0}},
                    'kelly_criterion': {'type': 'optimal', 'params': {'win_rate': 0.6, 'avg_win': 1.5}},
                    'regime_adjusted': {'type': 'adaptive', 'params': {'base_risk': 0.02}},
                    'correlation_adjusted': {'type': 'portfolio', 'params': {'max_correlation': 0.7}}
                },
            
                StrategyComponent.MARKET_FILTER: {
                    'trending_only': {'type': 'regime', 'params': {'regimes': ['trending_bull', 'trending_bear']}},
                    'high_volume': {'type': 'volume', 'params': {'min_volume_ratio': 1.5}},
                    'low_volatility': {'type': 'volatility', 'params': {'max_volatility': 0.02}},
                    'sentiment_strong': {'type': 'sentiment', 'params': {'min_strength': 0.5}},
                    'no_news': {'type': 'news', 'params': {'hours_since_news': 2}}
                },
            
                StrategyComponent.TIME_FILTER: {
                    'market_hours': {'type': 'session', 'params': {'sessions': ['london', 'new_york']}},
                    'avoid_friday': {'type': 'weekday', 'params': {'excluded_days': [4]}},
                    'first_hour': {'type': 'session_time', 'params': {'start_minutes': 0, 'end_minutes': 60}},
                    'avoid_news_time': {'type': 'news_avoidance', 'params': {'buffer_minutes': 30}}
                }
            }
        except Exception as e:
            logger.error(f"Error in _initialize_component_library: {e}")
            raise
    
    def discover_new_strategies(self, performance_data: List[Dict[str, Any]]) -> List[StrategyBlueprint]:
        """Discover new trading strategies through meta-learning."""
        try:
            logger.info("Starting strategy discovery process")
        
            # Analyze current performance patterns
            performance_patterns = self._analyze_performance_patterns(performance_data)
        
            # Generate strategy candidates
            candidates = self._generate_strategy_candidates(performance_patterns)
        
            # Evaluate candidates
            evaluated_strategies = []
            for candidate in candidates:
                evaluation = self._evaluate_strategy_candidate(candidate, performance_data)
                if evaluation['score'] > 0.6:  # Minimum viability threshold
                    blueprint = self._create_strategy_blueprint(candidate, evaluation)
                    evaluated_strategies.append(blueprint)
        
            # Select best strategies for testing
            best_strategies = sorted(evaluated_strategies, 
                                   key=lambda x: x.performance_score, reverse=True)[:5]
        
            for strategy in best_strategies:
                self.discovered_strategies[strategy.strategy_id] = strategy
                logger.info(f"Discovered new strategy: {strategy.strategy_id} "
                           f"(score: {strategy.performance_score:.3f})")
        
            return best_strategies
        except Exception as e:
            logger.error(f"Error in discover_new_strategies: {e}")
            raise
    
    def _analyze_performance_patterns(self, performance_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in performance data to guide strategy discovery."""
        try:
            if not performance_data:
                return {}
        
            patterns = {
                'regime_performance': defaultdict(list),
                'time_performance': defaultdict(list),
                'volatility_performance': defaultdict(list),
                'sentiment_performance': defaultdict(list)
            }
        
            for trade in performance_data:
                pnl = trade.get('pnl', 0)
                regime = trade.get('regime', 'unknown')
                hour = trade.get('entry_time', datetime.now()).hour
                volatility = trade.get('volatility', 0.02)
                sentiment = trade.get('sentiment_score', 0.0)
            
                patterns['regime_performance'][regime].append(pnl)
                patterns['time_performance'][hour].append(pnl)
            
                vol_bucket = 'low' if volatility < 0.015 else 'high' if volatility > 0.03 else 'medium'
                patterns['volatility_performance'][vol_bucket].append(pnl)
            
                sent_bucket = 'negative' if sentiment < -0.2 else 'positive' if sentiment > 0.2 else 'neutral'
                patterns['sentiment_performance'][sent_bucket].append(pnl)
        
            # Calculate average performance for each pattern
            analyzed_patterns = {}
            for pattern_type, pattern_data in patterns.items():
                analyzed_patterns[pattern_type] = {}
                for key, values in pattern_data.items():
                    if len(values) >= 5:  # Minimum sample size
                        analyzed_patterns[pattern_type][key] = {
                            'avg_pnl': np.mean(values),
                            'win_rate': sum(1 for v in values if v > 0) / len(values),
                            'sample_size': len(values),
                            'volatility': np.std(values)
                        }
        
            return analyzed_patterns
        except Exception as e:
            logger.error(f"Error in _analyze_performance_patterns: {e}")
            raise
    
    def _generate_strategy_candidates(self, patterns: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate strategy candidates based on performance patterns."""
        try:
            candidates = []
        
            # Find best performing conditions
            best_regimes = self._find_best_conditions(patterns.get('regime_performance', {}))
            best_times = self._find_best_conditions(patterns.get('time_performance', {}))
            best_volatility = self._find_best_conditions(patterns.get('volatility_performance', {}))
            best_sentiment = self._find_best_conditions(patterns.get('sentiment_performance', {}))
        
            # Generate combinations
            entry_signals = list(self.strategy_components[StrategyComponent.ENTRY_SIGNAL].keys())
            exit_signals = list(self.strategy_components[StrategyComponent.EXIT_SIGNAL].keys())
            risk_methods = list(self.strategy_components[StrategyComponent.RISK_MANAGEMENT].keys())
        
            # Create focused candidates based on patterns
            for regime in best_regimes[:2]:  # Top 2 regimes
                for entry in entry_signals[:3]:  # Top 3 entry signals
                    for exit in exit_signals[:2]:  # Top 2 exit signals
                        candidate = {
                            'entry_signal': entry,
                            'exit_signal': exit,
                            'risk_management': 'regime_adjusted',
                            'market_filter': f'regime_{regime}',
                            'complexity': 3
                        }
                        candidates.append(candidate)
        
            # Add time-based candidates
            for time_period in best_times[:2]:
                candidate = {
                    'entry_signal': 'ma_crossover',
                    'exit_signal': 'trailing_stop',
                    'risk_management': 'atr_based',
                    'time_filter': f'hour_{time_period}',
                    'complexity': 3
                }
                candidates.append(candidate)
        
            # Add sentiment-based candidates
            for sentiment_condition in best_sentiment[:2]:
                candidate = {
                    'entry_signal': 'sentiment_alignment',
                    'exit_signal': 'sentiment_reversal',
                    'risk_management': 'fixed_percent',
                    'market_filter': f'sentiment_{sentiment_condition}',
                    'complexity': 3
                }
                candidates.append(candidate)
        
            return candidates[:20]  # Limit to top 20 candidates
        except Exception as e:
            logger.error(f"Error in _generate_strategy_candidates: {e}")
            raise
    
    def _find_best_conditions(self, condition_data: Dict[str, Dict[str, float]]) -> List[str]:
        """Find the best performing conditions from pattern analysis."""
        try:
            if not condition_data:
                return []
        
            # Score conditions based on avg_pnl and win_rate
            scored_conditions = []
            for condition, metrics in condition_data.items():
                score = metrics['avg_pnl'] * metrics['win_rate'] * np.sqrt(metrics['sample_size'])
                scored_conditions.append((condition, score))
        
            # Sort by score and return top conditions
            scored_conditions.sort(key=lambda x: x[1], reverse=True)
            return [condition for condition, score in scored_conditions if score > 0]
        except Exception as e:
            logger.error(f"Error in _find_best_conditions: {e}")
            raise
    
    def _evaluate_strategy_candidate(self, candidate: Dict[str, Any], 
                                   performance_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate a strategy candidate using historical data."""
        # Simulate strategy performance on historical data
        try:
            simulated_trades = []
        
            for trade_data in performance_data[-100:]:  # Last 100 trades
                if self._strategy_would_trigger(candidate, trade_data):
                    # Simulate trade outcome with strategy rules
                    simulated_pnl = self._simulate_trade_outcome(candidate, trade_data)
                    simulated_trades.append(simulated_pnl)
        
            if len(simulated_trades) < 10:  # Insufficient data
                return {'score': 0.0, 'trades': 0, 'win_rate': 0.0, 'avg_pnl': 0.0}
        
            # Calculate performance metrics
            avg_pnl = np.mean(simulated_trades)
            win_rate = sum(1 for pnl in simulated_trades if pnl > 0) / len(simulated_trades)
            sharpe_ratio = avg_pnl / (np.std(simulated_trades) + 1e-6)
        
            # Composite score
            score = (avg_pnl * 0.4 + win_rate * 0.3 + sharpe_ratio * 0.3)
        
            return {
                'score': max(0.0, score),
                'trades': len(simulated_trades),
                'win_rate': win_rate,
                'avg_pnl': avg_pnl,
                'sharpe_ratio': sharpe_ratio
            }
        except Exception as e:
            logger.error(f"Error in _evaluate_strategy_candidate: {e}")
            raise
    
    def _strategy_would_trigger(self, candidate: Dict[str, Any], trade_data: Dict[str, Any]) -> bool:
        """Check if a strategy would trigger on given trade data."""
        # Simplified logic - in real implementation, this would be more sophisticated
        
        # Check market filter
        try:
            if 'market_filter' in candidate:
                filter_type = candidate['market_filter']
                if 'regime_' in filter_type:
                    required_regime = filter_type.split('_')[1]
                    if trade_data.get('regime') != required_regime:
                        return False
        
            # Check time filter
            if 'time_filter' in candidate:
                filter_type = candidate['time_filter']
                if 'hour_' in filter_type:
                    required_hour = int(filter_type.split('_')[1])
                    trade_hour = trade_data.get('entry_time', datetime.now()).hour
                    if trade_hour != required_hour:
                        return False
        
            # Check entry signal compatibility
            entry_signal = candidate.get('entry_signal', '')
            if 'sentiment' in entry_signal:
                sentiment_score = trade_data.get('sentiment_score', 0.0)
                if abs(sentiment_score) < 0.3:  # Weak sentiment
                    return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _strategy_would_trigger: {e}")
            raise
    
    def _simulate_trade_outcome(self, candidate: Dict[str, Any], trade_data: Dict[str, Any]) -> float:
        """Simulate trade outcome using strategy rules."""
        try:
            base_pnl = trade_data.get('pnl', 0.0)
        
            # Adjust based on strategy components
            risk_method = candidate.get('risk_management', 'fixed_percent')
            if risk_method == 'atr_based':
                # ATR-based risk typically reduces volatility
                base_pnl *= 0.9
            elif risk_method == 'kelly_criterion':
                # Kelly criterion optimizes position size
                base_pnl *= 1.1
        
            exit_signal = candidate.get('exit_signal', 'fixed_target')
            if exit_signal == 'trailing_stop':
                # Trailing stops typically improve win rate but reduce avg win
                if base_pnl > 0:
                    base_pnl *= 0.8  # Smaller wins
                else:
                    base_pnl *= 0.9  # Smaller losses
            elif exit_signal == 'time_based':
                # Time-based exits reduce extreme outcomes
                base_pnl *= 0.85
        
            return base_pnl
        except Exception as e:
            logger.error(f"Error in _simulate_trade_outcome: {e}")
            raise
    
    def _create_strategy_blueprint(self, candidate: Dict[str, Any], 
                                 evaluation: Dict[str, float]) -> StrategyBlueprint:
        """Create a strategy blueprint from a candidate and evaluation."""
        try:
            strategy_id = f"discovered_{int(datetime.now().timestamp())}_{hash(str(candidate)) % 10000}"
        
            components = {}
            for comp_type in StrategyComponent:
                comp_key = comp_type.value
                if comp_key in candidate:
                    components[comp_type] = candidate[comp_key]
        
            return StrategyBlueprint(
                strategy_id=strategy_id,
                components=components,
                performance_score=evaluation['score'],
                discovery_date=datetime.now(),
                test_results=evaluation,
                confidence=min(1.0, evaluation['trades'] / 50.0),  # Confidence based on sample size
                complexity_score=candidate.get('complexity', 3),
                market_regimes=[candidate.get('market_filter', 'all').replace('regime_', '')]
            )
        except Exception as e:
            logger.error(f"Error in _create_strategy_blueprint: {e}")
            raise
    
    def optimize_learning_process(self, learning_history: List[Dict[str, Any]]):
        """Optimize the learning process itself based on historical learning performance."""
        try:
            if len(learning_history) < 10:
                return
        
            # Analyze learning patterns
            successful_learning = [l for l in learning_history if l.get('improvement', 0) > 0.05]
            failed_learning = [l for l in learning_history if l.get('improvement', 0) < -0.02]
        
            # Update learning metadata
            if successful_learning:
                # Find common patterns in successful learning
                successful_conditions = defaultdict(int)
                for learning in successful_learning:
                    for condition, value in learning.get('conditions', {}).items():
                        successful_conditions[f"{condition}_{value}"] += 1
            
                # Update successful patterns
                self.learning_metadata.successful_patterns = [
                    pattern for pattern, count in successful_conditions.items() 
                    if count >= 2
                ]
        
            if failed_learning:
                # Find patterns to avoid
                failed_conditions = defaultdict(int)
                for learning in failed_learning:
                    for condition, value in learning.get('conditions', {}).items():
                        failed_conditions[f"{condition}_{value}"] += 1
            
                self.learning_metadata.failed_patterns = [
                    pattern for pattern, count in failed_conditions.items() 
                    if count >= 2
                ]
        
            # Adjust learning parameters
            recent_performance = learning_history[-10:]
            avg_improvement = np.mean([l.get('improvement', 0) for l in recent_performance])
        
            if avg_improvement > 0.1:
                # Learning is going well, can be more exploitative
                self.learning_metadata.exploration_vs_exploitation *= 0.95
            elif avg_improvement < 0:
                # Learning is struggling, need more exploration
                self.learning_metadata.exploration_vs_exploitation *= 1.05
        
            # Update learning speed based on adaptation success
            adaptation_success_rate = sum(1 for l in recent_performance if l.get('improvement', 0) > 0) / len(recent_performance)
            self.learning_metadata.adaptation_rate = adaptation_success_rate
        
            logger.info(f"Optimized learning process: exploration={self.learning_metadata.exploration_vs_exploitation:.2f}, "
                       f"adaptation_rate={self.learning_metadata.adaptation_rate:.2f}")
        except Exception as e:
            logger.error(f"Error in optimize_learning_process: {e}")
            raise
    
    def validate_discovered_strategy(self, strategy_id: str, trade_results: List[Dict[str, Any]]):
        """Validate a discovered strategy with real trading results."""
        try:
            if strategy_id not in self.discovered_strategies:
                return
        
            strategy = self.discovered_strategies[strategy_id]
        
            # Update validation metrics
            strategy.validation_trades += len(trade_results)
        
            if trade_results:
                avg_pnl = np.mean([t.get('pnl', 0) for t in trade_results])
                strategy.live_performance = (strategy.live_performance * 0.8 + avg_pnl * 0.2)
            
                # Update confidence based on live performance vs expected
                expected_performance = strategy.test_results.get('avg_pnl', 0)
                performance_ratio = strategy.live_performance / (expected_performance + 1e-6)
            
                if 0.8 <= performance_ratio <= 1.2:  # Within 20% of expected
                    strategy.confidence = min(1.0, strategy.confidence + 0.1)
                else:
                    strategy.confidence = max(0.0, strategy.confidence - 0.1)
            
                # Deactivate if performing poorly
                if strategy.confidence < 0.3 and strategy.validation_trades > 20:
                    strategy.active = False
                    logger.warning(f"Deactivated strategy {strategy_id} due to poor performance")
        except Exception as e:
            logger.error(f"Error in validate_discovered_strategy: {e}")
            raise
    
    def get_meta_learning_insights(self) -> Dict[str, Any]:
        """Get insights about the meta-learning process."""
        try:
            active_strategies = len([s for s in self.discovered_strategies.values() if s.active])
        
            return {
                'total_discovered_strategies': len(self.discovered_strategies),
                'active_strategies': active_strategies,
                'learning_metadata': {
                    'exploration_rate': self.learning_metadata.exploration_vs_exploitation,
                    'adaptation_rate': self.learning_metadata.adaptation_rate,
                    'successful_patterns': self.learning_metadata.successful_patterns,
                    'failed_patterns': self.learning_metadata.failed_patterns
                },
                'best_strategies': [
                    {
                        'strategy_id': s.strategy_id,
                        'performance_score': s.performance_score,
                        'confidence': s.confidence,
                        'validation_trades': s.validation_trades,
                        'live_performance': s.live_performance
                    }
                    for s in sorted(self.discovered_strategies.values(), 
                                  key=lambda x: x.performance_score, reverse=True)[:5]
                ]
            }
        except Exception as e:
            logger.error(f"Error in get_meta_learning_insights: {e}")
            raise
