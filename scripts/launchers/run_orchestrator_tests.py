#!/usr/bin/env python
"""
Direct test runner for orchestrator tests
Bypasses heavy imports from main trading_bot package
"""

import sys
import os

# Set environment variables to minimize TensorFlow logging
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['CUDA_VISIBLE_DEVICES'] = ''

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import test modules directly
import unittest
import asyncio
import numpy as np
from datetime import datetime, timedelta


def run_tests():
    """Run orchestrator tests directly"""
    
    # Test imports
    print("=" * 60)
    print("ORCHESTRATOR MODULE TESTS")
    print("=" * 60)
    
    # Test 1: Master Orchestrator
    print("\n[1] Testing MasterOrchestrator...")
    try:
        from trading_bot.orchestrator.master_orchestrator import (
            MasterOrchestrator, TradingMode, TradingDecision
        )
        
        config = {'capital': 100000, 'max_risk_per_trade': 0.02}
        orchestrator = MasterOrchestrator(config)
        
        assert orchestrator.total_capital == 100000
        assert orchestrator.trading_mode == TradingMode.BALANCED
        
        # Test mode filtering
        opportunities = [
            {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75, 'risk': 0.4, 'direction': 'BUY'},
            {'type': 'ARBITRAGE', 'symbol': 'GOOGL', 'confidence': 0.85, 'risk': 0.2, 'direction': 'BUY'}
        ]
        filtered = orchestrator._filter_by_mode_and_risk(opportunities)
        assert len(filtered) == 2
        
        # Test Kelly fraction
        kelly = orchestrator._calculate_kelly_fraction(0.05, 0.02, 0.7)
        assert 0 <= kelly <= 0.25
        
        # Test action determination
        assert orchestrator._determine_action({'direction': 'BUY'}) == 'BUY'
        assert orchestrator._determine_action({'direction': 'SELL'}) == 'SELL'
        
        # Test symbol extraction
        assert orchestrator._extract_symbols({'symbol': 'AAPL'}) == ['AAPL']
        
        # Test mode adjustment
        orchestrator.adjust_trading_mode({'volatility': 0.5, 'trend_strength': 0.5, 'volume': 'normal'})
        assert orchestrator.trading_mode == TradingMode.DEFENSIVE
        
        print("  [PASS] MasterOrchestrator: All tests passed")
    except Exception as e:
        print(f"  [FAIL] MasterOrchestrator: {e}")
        return False
    
    # Test 2: Execution Engine
    print("\n[2] Testing ExecutionEngine...")
    try:
        from trading_bot.orchestrator.execution_engine import (
            ExecutionEngine, OrderType, ExecutionAlgorithm, SmartOrderRouter, ExecutionResult
        )
        
        config = {'max_slippage': 0.002, 'urgency_threshold': 0.7, 'chunk_size': 1000}
        engine = ExecutionEngine(config)
        
        assert engine.max_slippage == 0.002
        assert len(engine.algorithms) == 8
        
        # Test algorithm selection
        params = {'urgency': 0.9, 'quantity': 500}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.SNIPER
        
        # Test slippage calculation
        slippage = engine._calculate_slippage(100.0, 100.5)
        assert abs(slippage - 0.005) < 0.001
        
        # Test guerrilla chunks
        chunks = engine._create_guerrilla_chunks(10000)
        assert len(chunks) > 0
        assert abs(sum(chunks) - 10000) < 1
        
        print("  [PASS] ExecutionEngine: All tests passed")
    except Exception as e:
        print(f"  [FAIL] ExecutionEngine: {e}")
        return False
    
    # Test 3: ML Predictor
    print("\n[3] Testing MLPredictor...")
    try:
        from trading_bot.orchestrator.ml_predictor import (
            OpportunityPredictor, MLFeatureExtractor, ModelEnsemble
        )
        
        config = {'lookback_window': 100, 'min_samples': 1000}
        predictor = OpportunityPredictor(config)
        
        assert predictor.lookback_window == 100
        assert 'success_classifier' in predictor.models
        
        # Test feature extraction
        extractor = MLFeatureExtractor()
        opp = {'type': 'MOMENTUM', 'confidence': 0.75, 'volatility': 0.25}
        features = extractor.extract_features(opp)
        assert len(features) == 20
        
        # Test heuristic predictions
        prob = predictor._heuristic_success_probability({'type': 'ARBITRAGE', 'confidence': 0.8})
        assert 0 <= prob <= 0.95
        
        print("  [PASS] MLPredictor: All tests passed")
    except Exception as e:
        print(f"  [FAIL] MLPredictor: {e}")
        return False
    
    # Test 4: Risk Manager
    print("\n[4] Testing RiskManager...")
    try:
        from trading_bot.orchestrator.risk_manager import (
            PortfolioRiskManager, PositionSizer, HedgeCalculator, DrawdownController
        )
        
        config = {'max_portfolio_var': 0.05, 'var_confidence': 0.95}
        manager = PortfolioRiskManager(config)
        
        assert manager.max_portfolio_var == 0.05
        
        # Test position weights
        positions = {'AAPL': {'value': 15000}, 'GOOGL': {'value': 28000}}
        manager.positions = positions
        weights = manager._get_position_weights()
        assert abs(sum(weights) - 1.0) < 0.01
        
        # Test concentration risk
        concentration = manager._assess_concentration_risk()
        assert 0 <= concentration <= 1
        
        # Test stress test
        loss = manager._stress_test_scenario(market_shock=-0.20, vol_shock=2.0)
        assert 0 < loss < 1
        
        # Test trade validation
        valid, msg = manager.validate_trade({'symbol': 'AAPL', 'risk': 0.01, 'size': 1000})
        assert valid == True
        
        # Test position sizer
        sizer = PositionSizer()
        opp = {'success_probability': 0.6, 'expected_return': 0.03, 'risk': 0.02}
        portfolio = {'available_capital': 100000}
        size = sizer._kelly_criterion(opp, portfolio)
        assert size > 0
        assert size <= 100000 * 0.25
        
        # Test drawdown controller
        controller = DrawdownController()
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(98000)
        assert action == 'normal'
        
        action, recommendations = controller.check_drawdown(78000)
        assert action == 'stop'
        assert recommendations['emergency_exit'] == True
        
        print("  [PASS] RiskManager: All tests passed")
    except Exception as e:
        print(f"  [FAIL] RiskManager: {e}")
        return False
    
    # Test 5: Performance Tracker
    print("\n[5] Testing PerformanceTracker...")
    try:
        from trading_bot.orchestrator.performance_tracker import (
            PerformanceTracker, MetricsCalculator, AutoOptimizer, BacktestEngine
        )
        
        config = {}
        tracker = PerformanceTracker(config)
        
        assert len(tracker.trade_history) == 0
        
        # Test trade tracking
        for i in range(10):
            trade = {
                'trade_id': f'TRADE_{i}',
                'timestamp': datetime.now(),
                'symbol': 'AAPL',
                'pnl': np.random.normal(100, 200),
                'strategy': 'momentum',
                'opportunity_type': 'MOMENTUM'
            }
            tracker.track_trade(trade)
        
        assert len(tracker.trade_history) == 10
        assert len(tracker.equity_curve) == 10
        
        # Test metrics calculator
        calculator = MetricsCalculator()
        metrics = calculator.calculate_metrics([], [], [])
        assert metrics.total_trades == 0
        
        # Test Sharpe ratio
        returns = [0.01, 0.02, -0.01, 0.015, 0.005]
        sharpe = calculator._calculate_sharpe_ratio(returns)
        assert sharpe > 0
        
        # Test max drawdown
        equity_curve = [100, 110, 105, 115, 100]
        max_dd = calculator._calculate_max_drawdown(equity_curve)
        assert abs(max_dd - 0.13) < 0.01
        
        # Test auto optimizer
        optimizer = AutoOptimizer()
        performance = {
            'win_rate': 0.4, 'avg_win': 100, 'avg_loss': 150,
            'by_type': {'MOMENTUM': {'win_rate': 0.3, 'wins': 3, 'total': 10}},
            'by_time': {10: {'wins': 2, 'total': 10}}
        }
        suggestions = optimizer._generate_suggestions(performance)
        assert 'reduce_size' in suggestions['position_sizing']
        
        print("  [PASS] PerformanceTracker: All tests passed")
    except Exception as e:
        print(f"  [FAIL] PerformanceTracker: {e}")
        return False
    
    # Test 6: Async Tests
    print("\n[6] Testing Async Methods...")
    try:
        async def run_async_tests():
            from trading_bot.orchestrator.ml_predictor import OpportunityPredictor
            from trading_bot.orchestrator.execution_engine import SmartOrderRouter
            
            # Test async prediction
            predictor = OpportunityPredictor({})
            opportunities = [
                {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75}
            ]
            predictions = await predictor.predict_batch(opportunities)
            assert len(predictions) == 1
            
            # Test async routing
            router = SmartOrderRouter()
            venues = {
                'exchange1': {'fee_rate': 0.001, 'latency': 5, 'liquidity': 10000, 'fill_rate': 0.98},
                'exchange2': {'fee_rate': 0.002, 'latency': 10, 'liquidity': 5000, 'fill_rate': 0.95}
            }
            scores = await router._score_venues('AAPL', 1000, venues)
            assert scores['exchange1'] > scores['exchange2']
            
            return True
        
        result = asyncio.run(run_async_tests())
        assert result == True
        
        print("  [PASS] Async Methods: All tests passed")
    except Exception as e:
        print(f"  [FAIL] Async Methods: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("ALL ORCHESTRATOR TESTS PASSED!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
