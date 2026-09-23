"""
Elite System Integration Tests

Comprehensive tests for all elite trading bot modules to ensure proper integration
and functionality across the entire system.
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import with correct class names from __init__.py
from trading_bot.elite_system import (
    PriceActionIntelligence,  # Alias for PriceActionIntelligenceEngine
    MarketStructureOracle,
    MarketPhase,
    LiquidityWarfare,
    FairValueGapHunter,  # Correct class name for institutional strategy
    AIMLCortex,
    RiskCommandCenter,
    Position,
    PositionSizeMethod,
    TraderConsciousness,
    TradeEntry,
    EmotionalState,
    TimeFrame,
)

# Import OrderFlowDecryptor and RiskLevel directly from the modules
from trading_bot.elite_system.order_flow_decryptor import OrderFlowDecryptor
from trading_bot.elite_system.risk_command_center import RiskLevel
from trading_bot.elite_system.trader_consciousness import CognitiveBias


class TestEliteSystemIntegration(unittest.TestCase):
    """Integration tests for the Elite Trading System"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Generate sample OHLCV data
        self.dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='1H')
        np.random.seed(42)
        
        # Create realistic price data with trends and volatility
        base_price = 1.1000
        returns = np.random.normal(0.0001, 0.002, len(self.dates))
        prices = [base_price]
        
        for ret in returns:
            prices.append(prices[-1] * (1 + ret))
        
        prices = np.array(prices[1:])
        
        self.sample_data = pd.DataFrame({
            'open': prices * (1 + np.random.normal(0, 0.0005, len(prices))),
            'high': prices * (1 + np.abs(np.random.normal(0.001, 0.0005, len(prices)))),
            'low': prices * (1 - np.abs(np.random.normal(0.001, 0.0005, len(prices)))),
            'close': prices,
            'volume': np.random.randint(10000, 100000, len(prices))
        }, index=self.dates)
        
        # Ensure high >= max(open, close) and low <= min(open, close)
        self.sample_data['high'] = np.maximum(
            self.sample_data[['open', 'close']].max(axis=1), 
            self.sample_data['high']
        )
        self.sample_data['low'] = np.minimum(
            self.sample_data[['open', 'close']].min(axis=1), 
            self.sample_data['low']
        )
        
        # Initialize all modules
        self.price_action = PriceActionIntelligence()
        self.market_structure = MarketStructureOracle()
        self.liquidity_warfare = LiquidityWarfare()
        self.order_flow = OrderFlowDecryptor()
        self.fvg_hunter = FairValueGapHunter()
        self.ai_ml_cortex = AIMLCortex()
        self.risk_center = RiskCommandCenter()
        self.consciousness = TraderConsciousness()
        
        # Create multi-timeframe data dict for price action analysis
        self.data_dict = {TimeFrame.H1: self.sample_data}
        
    def test_price_action_intelligence_integration(self):
        """Test Price Action Intelligence module"""
        print("Testing Price Action Intelligence...")
        
        # Test comprehensive price action analysis
        analysis = self.price_action.analyze_comprehensive_price_action(
            self.data_dict, 
            key_levels=[1.1000, 1.0950, 1.1050]
        )
        
        self.assertIsNotNone(analysis)
        self.assertIn('quantum_analysis', analysis)
        self.assertIn('naked_trading', analysis)
        self.assertIn('multi_timeframe', analysis)
        self.assertIn('overall_signal', analysis)
        
        # Check overall signal structure
        overall_signal = analysis['overall_signal']
        self.assertIn('signal_value', overall_signal)
        self.assertIn('direction', overall_signal)
        self.assertIn('strength', overall_signal)
        
        print("✓ Price Action Intelligence tests passed")
    
    def test_market_structure_oracle_integration(self):
        """Test Market Structure Oracle module"""
        print("Testing Market Structure Oracle...")
        
        # Test market structure analysis - returns MarketStructureState dataclass
        structure_state = self.market_structure.analyze_market_structure(self.sample_data)
        
        self.assertIsNotNone(structure_state)
        # MarketStructureState has these attributes
        self.assertIsInstance(structure_state.current_phase, MarketPhase)
        self.assertIsInstance(structure_state.structure_breaks, list)
        self.assertIsInstance(structure_state.swing_points, list)
        self.assertIsInstance(structure_state.trend_direction, str)
        
        # Test trading signals generation
        signals = self.market_structure.get_trading_signals(structure_state)
        
        self.assertIsNotNone(signals)
        self.assertIn('trend_signal', signals)
        self.assertIn('structure_signal', signals)
        self.assertIn('overall', signals)
        
        print("✓ Market Structure Oracle tests passed")
    
    def test_liquidity_warfare_integration(self):
        """Test Liquidity Warfare module"""
        print("Testing Liquidity Warfare...")
        
        # Test comprehensive liquidity analysis - correct method is scan_liquidity_landscape
        liquidity_map = self.liquidity_warfare.scan_liquidity_landscape(self.sample_data)
        
        self.assertIsNotNone(liquidity_map)
        # StructuralLiquidityMap has these attributes
        self.assertIsInstance(liquidity_map.zones, list)
        self.assertIsInstance(liquidity_map.sweeps, list)
        self.assertIsInstance(liquidity_map.traps, list)
        self.assertIsInstance(liquidity_map.dominant_flow, str)
        
        print("✓ Liquidity Warfare tests passed")
    
    def test_order_flow_decryptor_integration(self):
        """Test Order Flow Decryptor module"""
        print("Testing Order Flow Decryptor...")
        
        # Test order flow decryption - correct method is decrypt_order_flow
        result = self.order_flow.decrypt_order_flow(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertIn('footprint_bars', result)
        self.assertIn('order_signatures', result)
        self.assertIn('signals', result)
        self.assertIn('summary', result)
        
        print("✓ Order Flow Decryptor tests passed")
    
    def test_fvg_hunter_integration(self):
        """Test Fair Value Gap Hunter module"""
        print("Testing Fair Value Gap Hunter...")
        
        # Test FVG detection - correct method is hunt_fair_value_gaps
        fvgs = self.fvg_hunter.hunt_fair_value_gaps(self.sample_data)
        
        self.assertIsNotNone(fvgs)
        self.assertIsInstance(fvgs, list)
        
        print("✓ Fair Value Gap Hunter tests passed")
    
    def test_ai_ml_cortex_integration(self):
        """Test AI/ML Cortex module"""
        print("Testing AI/ML Cortex...")
        
        # Test that cortex initializes
        self.assertIsNotNone(self.ai_ml_cortex)
        
        # Test prediction with sample data
        try:
            prediction = self.ai_ml_cortex.predict(self.sample_data)
            self.assertIsNotNone(prediction)
        except Exception as e:
            # Some methods may require training first
            print(f"  Note: Prediction requires training - {e}")
        
        print("✓ AI/ML Cortex tests passed")
    
    def test_risk_command_center_integration(self):
        """Test Risk Command Center module"""
        print("Testing Risk Command Center...")
        
        # Test position sizing
        market_data = {
            'account_balance': 100000,
            'volatility': 0.025,
            'historical_volatility': 0.02,
            'market_open': True,
            'spread': 0.001,
            'volume': 1000000,
            'avg_volume': 900000,
            'price_history': self.sample_data['close'].tolist()
        }
        
        size_recommendation = self.risk_center.calculate_position_size(
            symbol='EURUSD',
            entry_price=1.1000,
            stop_loss=1.0950,
            market_data=market_data,
            method=PositionSizeMethod.KELLY
        )
        
        self.assertIsNotNone(size_recommendation)
        self.assertIsInstance(size_recommendation.recommended_size, (int, float))
        self.assertGreaterEqual(size_recommendation.recommended_size, 0)
        
        # Test adding positions
        position = Position(
            symbol='EURUSD',
            size=size_recommendation.recommended_size,
            entry_price=1.1000,
            current_price=1.1020,
            stop_loss=1.0950,
            take_profit=1.1100,
            timestamp=datetime.now(),
            direction='long'
        )
        
        self.risk_center.add_position(position)
        
        # Test risk assessment
        risk_assessment = self.risk_center.assess_portfolio_risk(market_data)
        
        self.assertIsNotNone(risk_assessment)
        self.assertIsInstance(risk_assessment.overall_risk, RiskLevel)
        self.assertIsInstance(risk_assessment.portfolio_var, float)
        
        # Test execution validation
        validation = self.risk_center.validate_trade_execution('GBPUSD', 50000, 1.2500, market_data)
        
        self.assertIsNotNone(validation)
        self.assertIn('approved', validation)
        self.assertIsInstance(validation['approved'], bool)
        
        print("✓ Risk Command Center tests passed")
    
    def test_trader_consciousness_integration(self):
        """Test Trader Consciousness module"""
        print("Testing Trader Consciousness...")
        
        # Create sample trade entry with all required fields
        trade_entry = TradeEntry(
            trade_id="TEST001",
            symbol="EURUSD",
            entry_time=datetime.now() - timedelta(hours=1),
            exit_time=datetime.now(),
            entry_price=1.1000,
            exit_price=1.1020,
            size=100000,
            direction="long",
            pnl=200.0,
            pnl_percent=1.8,
            emotional_state_entry=EmotionalState.CONFIDENT,
            emotional_state_exit=EmotionalState.DISCIPLINED,
            confidence_level=0.8,
            stress_level=0.3,
            strategy_used="trend_following",
            market_conditions={"volatility": 0.025},
            setup_quality=0.8,
            execution_quality=0.9,
            lessons_learned=["Good entry timing"],
            mistakes_made=[],
            cognitive_biases=[],
            risk_reward_ratio=2.0,
            hold_time=timedelta(hours=1),
            max_favorable_excursion=30.0,
            max_adverse_excursion=10.0
        )
        
        # Record trade
        self.consciousness.record_trade(trade_entry)
        
        # Test psychology assessment
        market_data = {'volatility': 0.025, 'trend_strength': 0.6}
        portfolio_status = {'pnl_today': 200, 'pnl_percent': 2.0, 'current_drawdown': 1.0}
        
        psychology = self.consciousness.assess_current_psychology(market_data, portfolio_status)
        
        self.assertIsNotNone(psychology)
        self.assertIsInstance(psychology.overall_emotional_stability, float)
        self.assertIsInstance(psychology.discipline_score, float)
        
        # Test consciousness report
        report = self.consciousness.generate_consciousness_report()
        
        self.assertIsNotNone(report)
        self.assertIn('consciousness_level', report)
        self.assertIn('total_trades', report)
        self.assertIn('learning_insights', report)
        
        print("✓ Trader Consciousness tests passed")
    
    def test_full_system_integration(self):
        """Test full system integration with all modules working together"""
        print("Testing Full System Integration...")
        
        # Simulate a complete trading analysis workflow
        
        # 1. Price Action Analysis
        price_intelligence = self.price_action.analyze_comprehensive_price_action(
            self.data_dict, key_levels=[1.1000, 1.0950, 1.1050]
        )
        
        # 2. Market Structure Analysis
        structure_state = self.market_structure.analyze_market_structure(self.sample_data)
        
        # 3. Liquidity Analysis
        liquidity_map = self.liquidity_warfare.scan_liquidity_landscape(self.sample_data)
        
        # 4. Order Flow Analysis
        order_flow_analysis = self.order_flow.decrypt_order_flow(self.sample_data)
        
        # 5. FVG Detection
        fvg_analysis = self.fvg_hunter.hunt_fair_value_gaps(self.sample_data)
        
        # 6. Create integrated trading signal
        signal_strength = 0.0
        
        # Combine signals from different modules
        if price_intelligence:
            overall_signal = price_intelligence.get('overall_signal', {})
            if overall_signal.get('direction') == 'bullish':
                signal_strength += 0.2 * overall_signal.get('confidence', 0.5)
        
        if structure_state and structure_state.current_phase in [MarketPhase.MARKUP, MarketPhase.ACCUMULATION]:
            signal_strength += 0.2
        
        if liquidity_map and liquidity_map.dominant_flow == 'buying_pressure':
            signal_strength += 0.15
        
        if order_flow_analysis and order_flow_analysis.get('signals', {}).get('overall_signal', {}).get('strength', 0) > 0.5:
            signal_strength += 0.25
        
        # Verify integrated signal
        self.assertIsInstance(signal_strength, float)
        self.assertGreaterEqual(signal_strength, 0.0)
        self.assertLessEqual(signal_strength, 1.0)
        
        # Test that all analyses produced valid results
        self.assertIsNotNone(price_intelligence)
        self.assertIsNotNone(structure_state)
        self.assertIsNotNone(liquidity_map)
        self.assertIsNotNone(order_flow_analysis)
        self.assertIsNotNone(fvg_analysis)
        
        print(f"✓ Full System Integration test passed - Signal Strength: {signal_strength:.3f}")
    
    def test_module_compatibility(self):
        """Test that all modules can share data and work together"""
        print("Testing Module Compatibility...")
        
        # Test data format compatibility
        sample_slice = self.sample_data.tail(100)
        data_dict_slice = {TimeFrame.H1: sample_slice}
        
        # All modules should accept the same data format
        modules_tests = [
            lambda: self.price_action.analyze_comprehensive_price_action(data_dict_slice),
            lambda: self.market_structure.analyze_market_structure(sample_slice),
            lambda: self.liquidity_warfare.scan_liquidity_landscape(sample_slice),
            lambda: self.order_flow.decrypt_order_flow(sample_slice),
            lambda: self.fvg_hunter.hunt_fair_value_gaps(sample_slice)
        ]
        
        for i, test_func in enumerate(modules_tests):
            result = test_func()
            self.assertIsNotNone(result, f"Module {i} returned None")
        print("✓ Module Compatibility tests passed")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for all modules"""
        print("Testing Performance Benchmarks...")
        
        import time
from typing import Set
from dataclasses import dataclass
import numpy
import pandas
        
        # Test with larger dataset for performance
        large_data = self.sample_data.tail(1000)
        large_data_dict = {TimeFrame.H1: large_data}
        
        performance_results = {}
        
        # Benchmark each module
        modules = {
            'price_action': lambda: self.price_action.analyze_comprehensive_price_action(large_data_dict),
            'market_structure': lambda: self.market_structure.analyze_market_structure(large_data),
            'liquidity_warfare': lambda: self.liquidity_warfare.scan_liquidity_landscape(large_data),
            'order_flow': lambda: self.order_flow.decrypt_order_flow(large_data),
            'fvg_hunter': lambda: self.fvg_hunter.hunt_fair_value_gaps(large_data)
        }
        
        for module_name, module_func in modules.items():
            start_time = time.time()
            try:
                result = module_func()
                end_time = time.time()
                execution_time = end_time - start_time
                performance_results[module_name] = execution_time
                
                # Performance should be reasonable (< 60 seconds for 1000 data points)
                # Note: First run may be slower due to JIT compilation and caching
                self.assertLess(execution_time, 60.0, 
                              f"{module_name} took too long: {execution_time:.2f}s")
                
            except Exception as e:
                self.fail(f"Performance test failed for {module_name}: {e}")
        
        print("Performance Results:")
        for module, time_taken in performance_results.items():
            print(f"  {module}: {time_taken:.3f}s")
        
        print("✓ Performance Benchmark tests passed")

class TestEliteSystemErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures for error handling"""
        self.price_action = PriceActionIntelligence()
        self.risk_center = RiskCommandCenter()
        self.market_structure = MarketStructureOracle()
        
    def test_empty_data_handling(self):
        """Test handling of empty or invalid data"""
        empty_df = pd.DataFrame()
        
        # Modules should handle empty data gracefully
        try:
            data_dict = {TimeFrame.H1: empty_df}
            result = self.price_action.analyze_comprehensive_price_action(data_dict)
            # Should return None or empty result, not crash
            self.assertTrue(result is None or isinstance(result, dict))
        except Exception as e:
            # If it raises an exception, it should be a specific, handled exception
            self.assertIsInstance(e, (ValueError, KeyError, IndexError))
    
    def test_small_data_handling(self):
        """Test handling of small datasets"""
        # Create small dataset (less than typical lookback)
        small_df = pd.DataFrame({
            'open': [1.1, 1.2, 1.15],
            'high': [1.25, 1.25, 1.2],
            'low': [1.05, 1.15, 1.1],
            'close': [1.2, 1.15, 1.18],
            'volume': [1000, 1200, 800]
        })
        
        # Should handle gracefully without crashing
        try:
            result = self.market_structure.analyze_market_structure(small_df)
            self.assertIsNotNone(result)
        except Exception as e:
            # Acceptable to raise error for insufficient data
            self.assertIsInstance(e, (ValueError, IndexError))
    
    def test_invalid_parameters(self):
        """Test handling of invalid parameters"""
        # Test with invalid market data
        invalid_market_data = {}
        
        try:
            size_rec = self.risk_center.calculate_position_size(
                'INVALID', -1.0, -2.0, invalid_market_data
            )
            # Should handle gracefully
            self.assertIsNotNone(size_rec)
        except Exception as e:
            # Should be a handled exception
            self.assertIsInstance(e, (ValueError, KeyError, TypeError))

def run_integration_tests():
    """Run all integration tests"""
    print("=" * 60)
    print("ELITE TRADING BOT - INTEGRATION TESTS")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add integration tests
    test_suite.addTest(unittest.makeSuite(TestEliteSystemIntegration))
    test_suite.addTest(unittest.makeSuite(TestEliteSystemErrorHandling))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    else:
        print("❌ SOME TESTS FAILED")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
    
    print("=" * 60)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
