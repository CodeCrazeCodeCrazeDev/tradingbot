"""
Loss Learning Self-Improvement Engine - Comprehensive Demo

This demo showcases the complete self-improvement pipeline:
    pass
1. Triage losing trades
2. Automated root-cause analysis
3. Conservative fix generation
4. Canary validation
5. Automated deployment with rollback capability
6. Continuous learning from labeled examples

Run this demo to see how the bot automatically learns from losses.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.self_improvement import (
    SelfImprovementEngine,
    TradeTriage,
    LossCategory,
    RootCauseAnalyzer,
    FixGenerator,
    CanaryValidator,
    AuditLogger,
    ContinuousLearner
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('loss_learning_demo.log')
    ]
)

logger = logging.getLogger(__name__)


class LossLearningDemo:
    pass
    """Comprehensive demo for loss learning self-improvement."""
    
    def __init__(self):
    pass
        """Initialize the demo."""
        # Configuration
        self.config = {
            'AUTO_LEARN': True,
            'CONF_THRESHOLD': 0.6,
            'AUTO_PROMOTE': False,  # Require human approval for safety
            'repo_path': '.',
            'backup_dir': 'diagnostics/self_improve/backups',
            
            'triage': {
                'loss_small_threshold': 0.005,  # 0.5%
                'loss_medium_threshold': 0.02,  # 2%
                'max_drawdown': 0.20,  # 20%
                'candles_lookback': 200,
                'news_window_minutes': 30
            },
            
            'root_cause': {
                'low_confidence_threshold': 0.5,
                'high_slippage_threshold': 0.005,
                'high_latency_threshold': 1000,
                'tight_sl_atr_ratio': 1.5,
                'volatility_spike_threshold': 2.0
            },
            
            'fix_generator': {
                'max_lot_size': 1.0,
                'risk_per_trade': 0.01,
                'min_stop_loss_pips': 10
            },
            
            'canary': {
                'canary_duration_minutes': 60,
                'canary_min_trades': 100,
                'canary_instruments': ['EURUSD', 'GBPUSD'],
                'max_win_rate_degradation': 0.10,
                'max_drawdown_increase': 0.05,
                'min_trade_count': 30,
                'max_slippage_increase': 0.002
            },
            
            'audit': {
                'log_dir': 'diagnostics/self_improve',
                'changes_log': 'diagnostics/changes-log.txt'
            },
            
            'learning': {
                'model_dir': 'models/self_improvement',
                'retrain_threshold': 500,  # Retrain after 500 new examples
                'validation_split': 0.2
            }
        }
        
        # Initialize engine
        self.engine = SelfImprovementEngine(self.config)
        
        # Demo data directory
        self.demo_dir = Path('diagnostics/self_improve/demo')
        self.demo_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Loss Learning Demo initialized")
    
    async def run_complete_demo(self):
    pass
        """Run the complete demo with various loss scenarios."""
        logger.info("=" * 80)
        logger.info("LOSS LEARNING SELF-IMPROVEMENT ENGINE - COMPREHENSIVE DEMO")
        logger.info("=" * 80)
        
        # Scenario 1: Low confidence signal loss
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 1: Low Confidence Signal Loss")
        logger.info("=" * 80)
        await self._scenario_low_confidence()
        
        # Scenario 2: High slippage execution loss
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 2: High Slippage Execution Loss")
        logger.info("=" * 80)
        await self._scenario_high_slippage()
        
        # Scenario 3: Stop loss too tight
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 3: Stop Loss Too Tight")
        logger.info("=" * 80)
        await self._scenario_tight_stop_loss()
        
        # Scenario 4: Market regime mismatch
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 4: Market Regime Mismatch")
        logger.info("=" * 80)
        await self._scenario_regime_mismatch()
        
        # Scenario 5: Software/data issue
        logger.info("\n" + "=" * 80)
        logger.info("SCENARIO 5: Software/Data Issue")
        logger.info("=" * 80)
        await self._scenario_software_issue()
        
        # Display final statistics
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        self._display_final_stats()
        
        logger.info("\n" + "=" * 80)
        logger.info("DEMO COMPLETED")
        logger.info("=" * 80)
    
    async def _scenario_low_confidence(self):
    pass
        """Scenario: Trade loss due to low model confidence."""
        logger.info("Simulating trade with low model confidence...")
        
        # Create losing trade
        trade = {
            'ticket_id': 'TRADE_001',
            'entry_time': datetime.now() - timedelta(hours=2),
            'exit_time': datetime.now() - timedelta(hours=1),
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.1000,
            'exit_price': 1.0950,  # Loss
            'size': 0.1,
            'sl': 1.0950,
            'tp': 1.1100,
            'pnl': -50.0,
            'fees': 2.0,
            'slippage': 0.0001,
            'execution_latency_ms': 150
        }
        
        # Signal context with LOW confidence
        signal_data = {
            'indicators_used': ['RSI', 'MACD', 'MA'],
            'indicator_values': {'RSI': 45, 'MACD': 0.0002, 'MA_20': 1.0995},
            'model_confidence': 0.42,  # LOW CONFIDENCE
            'timeframe': 'H1',
            'market_regime': 'trending',
            'multi_tf_agreement': True,
            'signal_drift': 0.15
        }
        
        # Market data
        market_data = {
            'candles_before': self._generate_candles(200),
            'candles_after': self._generate_candles(50),
            'atr': 0.0015,
            'spread': 0.0001,
            'volume_avg': 1000,
            'volatility_spike': False,
            'news_events': []
        }
        
        # System metrics
        system_data = {
            'cpu_usage': 45.0,
            'memory_usage': 60.0,
            'latency_ms': 150,
            'order_fill_type': 'full',
            'errors_in_logs': []
        }
        
        # Current equity
        equity = 10000.0
        
        # Process the losing trade
        result = self.engine.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        self._display_result(result, "Low Confidence Signal")
    
    async def _scenario_high_slippage(self):
    pass
        """Scenario: Trade loss due to high slippage."""
        logger.info("Simulating trade with high slippage...")
        
        trade = {
            'ticket_id': 'TRADE_002',
            'entry_time': datetime.now() - timedelta(hours=3),
            'exit_time': datetime.now() - timedelta(hours=2),
            'symbol': 'GBPUSD',
            'side': 'sell',
            'entry_price': 1.2500,
            'exit_price': 1.2550,  # Loss
            'size': 0.15,
            'sl': 1.2550,
            'tp': 1.2400,
            'pnl': -75.0,
            'fees': 3.0,
            'slippage': 0.0065,  # HIGH SLIPPAGE (0.65%)
            'execution_latency_ms': 2500  # High latency
        }
        
        signal_data = {
            'indicators_used': ['Bollinger', 'ATR', 'Volume'],
            'indicator_values': {'BB_upper': 1.2520, 'ATR': 0.0025, 'Volume': 500},
            'model_confidence': 0.75,  # Good confidence
            'timeframe': 'M15',
            'market_regime': 'volatile',
            'multi_tf_agreement': True,
            'signal_drift': 0.05
        }
        
        market_data = {
            'candles_before': self._generate_candles(200),
            'candles_after': self._generate_candles(50),
            'atr': 0.0025,
            'spread': 0.0008,  # Wide spread
            'volume_avg': 500,  # Low volume
            'volatility_spike': True,
            'news_events': ['BOE Interest Rate Decision']
        }
        
        system_data = {
            'cpu_usage': 55.0,
            'memory_usage': 65.0,
            'latency_ms': 2500,  # High latency
            'order_fill_type': 'partial',  # Partial fill
            'errors_in_logs': []
        }
        
        equity = 9925.0  # After first loss
        
        result = self.engine.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        self._display_result(result, "High Slippage")
    
    async def _scenario_tight_stop_loss(self):
    pass
        """Scenario: Trade loss due to stop loss too tight relative to ATR."""
        logger.info("Simulating trade with stop loss too tight...")
        
        trade = {
            'ticket_id': 'TRADE_003',
            'entry_time': datetime.now() - timedelta(hours=4),
            'exit_time': datetime.now() - timedelta(hours=3),
            'symbol': 'USDJPY',
            'side': 'buy',
            'entry_price': 150.00,
            'exit_price': 149.85,  # Hit stop loss
            'size': 0.2,
            'sl': 149.85,  # Only 15 pips away
            'tp': 150.50,
            'pnl': -30.0,
            'fees': 2.5,
            'slippage': 0.0002,
            'execution_latency_ms': 180
        }
        
        signal_data = {
            'indicators_used': ['EMA', 'Stochastic', 'ADX'],
            'indicator_values': {'EMA_20': 149.95, 'Stochastic': 35, 'ADX': 25},
            'model_confidence': 0.68,
            'timeframe': 'H4',
            'market_regime': 'ranging',
            'multi_tf_agreement': True,
            'signal_drift': 0.08
        }
        
        market_data = {
            'candles_before': self._generate_candles(200),
            'candles_after': self._generate_candles(50),
            'atr': 0.35,  # ATR is 35 pips, but SL only 15 pips away (0.43 * ATR)
            'spread': 0.02,
            'volume_avg': 1200,
            'volatility_spike': False,
            'news_events': []
        }
        
        system_data = {
            'cpu_usage': 42.0,
            'memory_usage': 58.0,
            'latency_ms': 180,
            'order_fill_type': 'full',
            'errors_in_logs': []
        }
        
        equity = 9850.0
        
        result = self.engine.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        self._display_result(result, "Tight Stop Loss")
    
    async def _scenario_regime_mismatch(self):
    pass
        """Scenario: Trade loss due to market regime mismatch."""
        logger.info("Simulating trade with market regime mismatch...")
        
        trade = {
            'ticket_id': 'TRADE_004',
            'entry_time': datetime.now() - timedelta(hours=5),
            'exit_time': datetime.now() - timedelta(hours=4),
            'symbol': 'EURUSD',
            'side': 'buy',
            'entry_price': 1.0980,
            'exit_price': 1.0960,  # Loss
            'size': 0.12,
            'sl': 1.0950,
            'tp': 1.1050,
            'pnl': -24.0,
            'fees': 2.0,
            'slippage': 0.0001,
            'execution_latency_ms': 160
        }
        
        signal_data = {
            'indicators_used': ['Trend_Following', 'Momentum'],
            'indicator_values': {'Trend': 'up', 'Momentum': 0.65},
            'model_confidence': 0.72,
            'timeframe': 'H1',
            'market_regime': 'trending',  # Strategy assumes trending
            'multi_tf_agreement': False,  # But higher TF shows ranging!
            'signal_drift': 0.25  # High drift
        }
        
        market_data = {
            'candles_before': self._generate_candles(200),
            'candles_after': self._generate_candles(50),
            'atr': 0.0018,
            'spread': 0.0001,
            'volume_avg': 950,
            'volatility_spike': False,
            'news_events': []
        }
        
        system_data = {
            'cpu_usage': 48.0,
            'memory_usage': 62.0,
            'latency_ms': 160,
            'order_fill_type': 'full',
            'errors_in_logs': []
        }
        
        equity = 9820.0
        
        result = self.engine.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        self._display_result(result, "Regime Mismatch")
    
    async def _scenario_software_issue(self):
    pass
        """Scenario: Trade loss due to software/data issue."""
        logger.info("Simulating trade with software issue...")
        
        trade = {
            'ticket_id': 'TRADE_005',
            'entry_time': datetime.now() - timedelta(hours=6),
            'exit_time': datetime.now() - timedelta(hours=5),
            'symbol': 'AUDUSD',
            'side': 'sell',
            'entry_price': 0.6500,
            'exit_price': 0.6520,  # Loss
            'size': 0.18,
            'sl': 0.6520,
            'tp': 0.6450,
            'pnl': -36.0,
            'fees': 2.2,
            'slippage': 0.0003,
            'execution_latency_ms': 5000  # Very high latency
        }
        
        signal_data = {
            'indicators_used': ['RSI', 'MACD'],
            'indicator_values': {'RSI': float('nan'), 'MACD': 0.0001},  # NaN value!
            'model_confidence': 0.55,
            'timeframe': 'M30',
            'market_regime': 'unknown',  # Unknown regime
            'multi_tf_agreement': True,
            'signal_drift': 0.35  # High drift
        }
        
        market_data = {
            'candles_before': self._generate_candles(150),  # Missing some candles
            'candles_after': self._generate_candles(50),
            'atr': 0.0020,
            'spread': 0.0002,
            'volume_avg': 800,
            'volatility_spike': False,
            'news_events': []
        }
        
        system_data = {
            'cpu_usage': 85.0,  # High CPU
            'memory_usage': 92.0,  # High memory
            'latency_ms': 5000,  # Very high latency
            'order_fill_type': 'full',
            'errors_in_logs': [
                'ValueError: invalid value encountered in double_scalars',
                'Warning: NaN detected in indicator calculation',
                'Error: Cache read timeout'
            ]
        }
        
        equity = 9784.0
        
        result = self.engine.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        self._display_result(result, "Software Issue")
    
    def _generate_candles(self, count: int) -> list:
    pass
        """Generate dummy candle data."""
        import random
        candles = []
        base_price = 1.1000
        
        for i in range(count):
    pass
            open_price = base_price + random.uniform(-0.0020, 0.0020)
            high_price = open_price + random.uniform(0, 0.0015)
            low_price = open_price - random.uniform(0, 0.0015)
            close_price = random.uniform(low_price, high_price)
            
            candles.append({
                'time': (datetime.now() - timedelta(minutes=count-i)).isoformat(),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': random.randint(500, 1500)
            })
            
            base_price = close_price
        
        return candles
    
    def _display_result(self, result: Dict[str, Any], scenario_name: str):
    pass
        """Display processing result."""
        logger.info(f"\n{'='*60}")
        logger.info(f"RESULT: {scenario_name}")
        logger.info(f"{'='*60}")
        logger.info(f"Status: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'processed':
    pass
            logger.info(f"Trade ID: {result.get('trade_id')}")
            logger.info(f"Hypotheses Generated: {result.get('hypotheses_count', 0)}")
            logger.info(f"Fixes Proposed: {result.get('fixes_proposed', 0)}")
            logger.info(f"Git Branch: {result.get('branch', 'N/A')}")
            
            if result.get('canary_results'):
    pass
                logger.info(f"Canary Validations Started: {len(result['canary_results'])}")
                for canary in result['canary_results']:
    pass
                    logger.info(f"  - Fix {canary.get('fix_id')}: {canary.get('status')}")
        
        elif result.get('status') == 'escalated':
    pass
            logger.info(f"Reason: {result.get('reason')}")
            logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
            logger.info("⚠️  ESCALATED TO HUMAN REVIEW")
        
        elif result.get('status') == 'no_fixes':
    pass
            logger.info("No safe fixes could be generated")
        
        elif result.get('status') == 'error':
    pass
            logger.error(f"Error: {result.get('error')}")
        
        logger.info(f"{'='*60}\n")
    
    def _display_final_stats(self):
    pass
        """Display final statistics."""
        # Check audit logs
        audit_dir = Path(self.config['audit']['log_dir'])
        
        if audit_dir.exists():
    pass
            triage_files = list(audit_dir.glob('*/triage_*.json'))
            hypothesis_files = list(audit_dir.glob('*/hypotheses_*.json'))
            fix_files = list(audit_dir.glob('*/fixes_*.json'))
            
            logger.info(f"Total Triage Reports: {len(triage_files)}")
            logger.info(f"Total Hypothesis Reports: {len(hypothesis_files)}")
            logger.info(f"Total Fix Proposals: {len(fix_files)}")
        
        # Check if changes log exists
        changes_log = Path(self.config['audit']['changes_log'])
        if changes_log.exists():
    pass
            with open(changes_log, 'r') as f:
    pass
                lines = f.readlines()
            logger.info(f"Total Change Log Entries: {len(lines)}")
        
        logger.info("\n📊 LEARNING SUMMARY:")
        logger.info("  ✓ Automated triage of all losing trades")
        logger.info("  ✓ Root cause analysis with ranked hypotheses")
        logger.info("  ✓ Conservative fix generation (risk-reducing only)")
        logger.info("  ✓ Git branching and backup before changes")
        logger.info("  ✓ Canary validation framework ready")
        logger.info("  ✓ Full audit trail maintained")
        logger.info("  ✓ Continuous learning from labeled examples")
        
        logger.info("\n🔒 SAFETY FEATURES:")
        logger.info("  ✓ Never increases risk automatically")
        logger.info("  ✓ Requires human approval for medium+ risk fixes")
        logger.info("  ✓ Automatic rollback on canary failure")
        logger.info("  ✓ Confidence threshold for escalation")
        logger.info("  ✓ Complete reversibility of all changes")
        
        logger.info("\n📁 OUTPUT LOCATIONS:")
        logger.info(f"  - Audit logs: {self.config['audit']['log_dir']}")
        logger.info(f"  - Changes log: {self.config['audit']['changes_log']}")
        logger.info(f"  - Backups: {self.config['backup_dir']}")
        logger.info(f"  - Models: {self.config['learning']['model_dir']}")


async def main():
    pass
    """Run the comprehensive demo."""
    demo = LossLearningDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    pass
    asyncio.run(main())
