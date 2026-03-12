"""
Strategy Optimizer - Optimizes trading parameters based on performance
"""

import json
import os
import logging
from datetime import datetime
from dataclasses import dataclass, field
from typing import Dict
from .performance_analyzer import PerformanceAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class LearningParameters:
    """Adaptive trading parameters."""
    rsi_buy_threshold: float = 40.0
    rsi_sell_threshold: float = 60.0
    stop_loss_pct: float = 0.005
    take_profit_pct: float = 0.015
    min_macd_threshold: float = 0.0
    confidence_threshold: float = 0.5
    sma_crossover_required: bool = True
    min_volatility: float = 0.0
    max_volatility: float = 100.0
    rsi_weight: float = 0.33
    macd_weight: float = 0.33
    sma_weight: float = 0.34
    preferred_symbols: list = field(default_factory=list)
    avoid_symbols: list = field(default_factory=list)
    best_trading_hours: list = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    update_count: int = 0
    performance_score: float = 0.0


class StrategyOptimizer:
    """Optimizes trading strategy based on performance."""
    
    def __init__(self, optimization_interval: int = 10):
        self.parameters = LearningParameters()
        self.analyzer = PerformanceAnalyzer()
        self.optimization_interval = optimization_interval
        self.trades_since_optimization = 0
        
    def should_optimize(self) -> bool:
        """Check if it's time to optimize."""
        return self.trades_since_optimization >= self.optimization_interval
    
    def optimize(self) -> LearningParameters:
        """Optimize ALL trading parameters based on recent performance."""
        logger.info("\n🧠 OPTIMIZING ALL INDICATORS & STRATEGY...")
        logger.info("=" * 80)
        
        # Analyze ALL indicators
        rsi_analysis = self.analyzer.analyze_rsi_effectiveness()
        macd_analysis = self.analyzer.analyze_macd_effectiveness()
        sma_analysis = self.analyzer.analyze_sma_effectiveness()
        volatility_analysis = self.analyzer.analyze_volatility_impact()
        symbol_analysis = self.analyzer.analyze_symbol_performance()
        time_patterns = self.analyzer.analyze_time_patterns()
        indicator_weights = self.analyzer.analyze_indicator_weights()
        optimal_stop = self.analyzer.analyze_stop_loss_effectiveness()
        
        old_params = {
            'rsi_buy': self.parameters.rsi_buy_threshold,
            'rsi_sell': self.parameters.rsi_sell_threshold,
            'macd_threshold': self.parameters.min_macd_threshold,
            'stop_loss': self.parameters.stop_loss_pct,
            'sma_required': self.parameters.sma_crossover_required
        }
        
        # 1. OPTIMIZE RSI THRESHOLDS
        if rsi_analysis['confidence'] > 0.4:
            self.parameters.rsi_buy_threshold = (
                0.7 * self.parameters.rsi_buy_threshold +
                0.3 * rsi_analysis['optimal_buy']
            )
            self.parameters.rsi_sell_threshold = (
                0.7 * self.parameters.rsi_sell_threshold +
                0.3 * rsi_analysis['optimal_sell']
            )
            logger.info(f"📊 RSI OPTIMIZATION:")
            logger.info(f"   Buy:  {old_params['rsi_buy']:.1f} → {self.parameters.rsi_buy_threshold:.1f}")
            logger.info(f"   Sell: {old_params['rsi_sell']:.1f} → {self.parameters.rsi_sell_threshold:.1f}")
        
        # 2. OPTIMIZE MACD THRESHOLD
        if macd_analysis['confidence'] > 0.4:
            self.parameters.min_macd_threshold = (
                0.7 * self.parameters.min_macd_threshold +
                0.3 * macd_analysis['optimal_buy']
            )
            logger.info(f"📈 MACD OPTIMIZATION:")
            logger.info(f"   Threshold: {old_params['macd_threshold']:.5f} → {self.parameters.min_macd_threshold:.5f}")
        
        # 3. OPTIMIZE SMA STRATEGY
        if sma_analysis['confidence'] > 0.3:
            self.parameters.sma_crossover_required = sma_analysis['crossover_required']
            logger.info(f"📉 SMA OPTIMIZATION:")
            logger.info(f"   Crossover Required: {old_params['sma_required']} → {self.parameters.sma_crossover_required}")
            logger.info(f"   With Crossover Win Rate: {sma_analysis['crossover_win_rate']:.1%}")
            logger.info(f"   Without Crossover Win Rate: {sma_analysis['no_crossover_win_rate']:.1%}")
        
        # 4. OPTIMIZE VOLATILITY FILTER
        if volatility_analysis['confidence'] > 0.3:
            vol_range = volatility_analysis['optimal_volatility_range']
            self.parameters.min_volatility = vol_range[0]
            self.parameters.max_volatility = vol_range[1]
            logger.info(f"💨 VOLATILITY OPTIMIZATION:")
            logger.info(f"   Optimal Range: {vol_range[0]:.3f}% - {vol_range[1]:.3f}%")
            logger.info(f"   Avg Winning Vol: {volatility_analysis['avg_winning_volatility']:.3f}%")
        
        # 5. OPTIMIZE STOP LOSS & TAKE PROFIT
        self.parameters.stop_loss_pct = (
            0.7 * self.parameters.stop_loss_pct + 0.3 * optimal_stop
        )
        self.parameters.take_profit_pct = self.parameters.stop_loss_pct * 3
        logger.info(f"🎯 RISK MANAGEMENT OPTIMIZATION:")
        logger.info(f"   Stop Loss: {old_params['stop_loss']:.3%} → {self.parameters.stop_loss_pct:.3%}")
        logger.info(f"   Take Profit: {self.parameters.take_profit_pct:.3%}")
        
        # 6. OPTIMIZE INDICATOR WEIGHTS
        self.parameters.rsi_weight = indicator_weights['rsi_weight']
        self.parameters.macd_weight = indicator_weights['macd_weight']
        self.parameters.sma_weight = indicator_weights['sma_weight']
        logger.info(f"⚖️ INDICATOR WEIGHT OPTIMIZATION:")
        logger.info(f"   RSI Weight: {self.parameters.rsi_weight:.2f} (Accuracy: {indicator_weights['rsi_accuracy']:.1%})")
        logger.info(f"   MACD Weight: {self.parameters.macd_weight:.2f} (Accuracy: {indicator_weights['macd_accuracy']:.1%})")
        logger.info(f"   SMA Weight: {self.parameters.sma_weight:.2f} (Accuracy: {indicator_weights['sma_accuracy']:.1%})")
        
        # 7. OPTIMIZE SYMBOL SELECTION
        self.parameters.preferred_symbols = symbol_analysis['best_symbols']
        self.parameters.avoid_symbols = symbol_analysis['worst_symbols']
        if self.parameters.preferred_symbols:
            logger.info(f"🎯 SYMBOL OPTIMIZATION:")
            logger.info(f"   Best Symbols: {', '.join(self.parameters.preferred_symbols)}")
        if self.parameters.avoid_symbols:
            logger.info(f"   Avoid Symbols: {', '.join(self.parameters.avoid_symbols)}")
        
        # 8. OPTIMIZE TIME PATTERNS
        self.parameters.best_trading_hours = time_patterns['best_hours']
        if time_patterns['best_hours']:
            logger.info(f"⏰ TIME OPTIMIZATION:")
            logger.info(f"   Best Hours: {time_patterns['best_hours']}")
        if time_patterns['worst_hours']:
            logger.info(f"   Worst Hours: {time_patterns['worst_hours']}")
        
        # Update metadata
        self.parameters.last_updated = datetime.now()
        self.parameters.update_count += 1
        self.parameters.performance_score = self.analyzer.get_win_rate()
        
        logger.info("=" * 80)
        logger.info(f"✅ OPTIMIZATION COMPLETE")
        logger.info(f"   Win Rate: {self.parameters.performance_score:.1%}")
        logger.info(f"   Total Updates: {self.parameters.update_count}")
        logger.info("=" * 80)
        
        self.trades_since_optimization = 0
        return self.parameters
    
    def record_trade(self, trade_data: Dict):
        """Record trade for learning."""
        self.analyzer.add_trade(trade_data)
        self.trades_since_optimization += 1
    
    def get_parameters(self) -> LearningParameters:
        """Get current trading parameters."""
        return self.parameters
    
    def save_knowledge(self, filepath: str = 'knowledge/strategy_knowledge.json'):
        """Save learned parameters to disk."""
        os.makedirs('knowledge', exist_ok=True)
        
        knowledge = {
            'parameters': {
                'rsi_buy_threshold': self.parameters.rsi_buy_threshold,
                'rsi_sell_threshold': self.parameters.rsi_sell_threshold,
                'stop_loss_pct': self.parameters.stop_loss_pct,
                'take_profit_pct': self.parameters.take_profit_pct,
                'update_count': self.parameters.update_count,
                'performance_score': self.parameters.performance_score
            },
            'last_updated': self.parameters.last_updated.isoformat(),
            'trade_history': list(self.analyzer.trade_history)
        }
        
        with open(filepath, 'w') as f:
            json.dump(knowledge, f, indent=2, default=str)
        
        logger.info(f"💾 Knowledge saved to {filepath}")
    
    def load_knowledge(self, filepath: str = 'knowledge/strategy_knowledge.json'):
        """Load learned parameters from disk."""
        if not os.path.exists(filepath):
            logger.info("No previous knowledge found, starting fresh")
            return
        
        try:
            with open(filepath, 'r') as f:
                knowledge = json.load(f)
            
            params = knowledge['parameters']
            self.parameters.rsi_buy_threshold = params['rsi_buy_threshold']
            self.parameters.rsi_sell_threshold = params['rsi_sell_threshold']
            self.parameters.stop_loss_pct = params['stop_loss_pct']
            self.parameters.take_profit_pct = params['take_profit_pct']
            self.parameters.update_count = params['update_count']
            self.parameters.performance_score = params['performance_score']
            
            logger.info(f"📚 Knowledge loaded: {self.parameters.update_count} updates, {self.parameters.performance_score:.1%} win rate")
        except Exception as e:
            logger.error(f"Error loading knowledge: {e}")
