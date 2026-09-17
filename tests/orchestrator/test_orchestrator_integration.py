"""
Integration Tests for Complete Orchestrator System
Tests end-to-end flows and component interactions
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def full_config():
    return {
        'capital': 100000,
        'max_risk_per_trade': 0.02,
        'max_portfolio_risk': 0.06,
        'max_correlation': 0.7,
        'max_slippage': 0.002,
        'urgency_threshold': 0.7,
        'chunk_size': 1000,
        'var_confidence': 0.95,
        'lookback_period': 252
    }


@pytest.fixture
def sample_market_data():
    return {
        'AAPL': {'price': 150.0, 'volume': 1000000, 'volatility': 0.25,
                 'price_history': np.random.uniform(140, 160, 100).tolist()},
        'GOOGL': {'price': 2800.0, 'volume': 500000, 'volatility': 0.30,
                  'price_history': np.random.uniform(2700, 2900, 100).tolist()},
        'MSFT': {'price': 300.0, 'volume': 800000, 'volatility': 0.22,
                 'price_history': np.random.uniform(290, 310, 100).tolist()}
    }


class TestFullSystemIntegration:
    """Test complete orchestrator system integration"""

    def test_all_imports(self):
        """Test all orchestrator components can be imported together"""
        from trading_bot.orchestrator import (
            MasterOrchestrator, TradingMode, TradingDecision,
            ExecutionEngine, OrderType, ExecutionAlgorithm, SmartOrderRouter, ExecutionResult,
            OpportunityPredictor, SuccessPredictor, MLFeatureExtractor, ModelEnsemble,
            PortfolioRiskManager, PositionSizer, HedgeCalculator, RiskMetrics, DrawdownController,
            PerformanceTracker, MetricsCalculator, AutoOptimizer, BacktestEngine
        )
        assert all([
            MasterOrchestrator, TradingMode, TradingDecision,
            ExecutionEngine, OrderType, ExecutionAlgorithm, SmartOrderRouter, ExecutionResult,
            OpportunityPredictor, SuccessPredictor, MLFeatureExtractor, ModelEnsemble,
            PortfolioRiskManager, PositionSizer, HedgeCalculator, RiskMetrics, DrawdownController,
            PerformanceTracker, MetricsCalculator, AutoOptimizer, BacktestEngine
        ])

    def test_orchestrator_with_execution_engine(self, full_config):
        """Test MasterOrchestrator with ExecutionEngine"""
        from trading_bot.orchestrator import MasterOrchestrator, ExecutionEngine
        orchestrator = MasterOrchestrator(full_config)
        execution_engine = ExecutionEngine(full_config)
        orchestrator.execution_engine = execution_engine
        assert orchestrator.execution_engine is not None

    def test_orchestrator_with_ml_predictor(self, full_config):
        """Test MasterOrchestrator with MLPredictor"""
        from trading_bot.orchestrator import MasterOrchestrator, OpportunityPredictor
        orchestrator = MasterOrchestrator(full_config)
        ml_predictor = OpportunityPredictor(full_config)
        orchestrator.ml_predictor = ml_predictor
        assert orchestrator.ml_predictor is not None

    def test_orchestrator_with_risk_manager(self, full_config):
        """Test MasterOrchestrator with RiskManager"""
        from trading_bot.orchestrator import MasterOrchestrator, PortfolioRiskManager
        orchestrator = MasterOrchestrator(full_config)
        risk_manager = PortfolioRiskManager(full_config)
        orchestrator.risk_manager = risk_manager
        assert orchestrator.risk_manager is not None


class TestMLToExecutionFlow:
    """Test ML prediction to execution flow"""

    @pytest.mark.asyncio
    async def test_predict_and_execute_flow(self, full_config):
        """Test flow from ML prediction to execution"""
        OpportunityPredictor, ExecutionEngine, TradingDecision
        )
        predictor = OpportunityPredictor(full_config)
        engine = ExecutionEngine(full_config)

        # Create opportunity
        opportunity = {
            'type': 'MOMENTUM', 'symbol': 'AAPL',
            'confidence': 0.75, 'expected_return': 0.03, 'risk': 0.4
        }

        # Get prediction
        predictions = await predictor.predict_batch([opportunity])
        assert len(predictions) == 1
        assert predictions[0].success_probability > 0

        # Create decision based on prediction
        decision = TradingDecision(
            decision_id="DEC_001", timestamp=datetime.now(),
            opportunity_ids=["OPP_001"], action="BUY", symbols=["AAPL"],
            allocation={"OPP_001": 5000}, risk_score=predictions[0].risk_score,
            expected_return=predictions[0].expected_return,
            confidence=predictions[0].success_probability,
            execution_plan={'urgency': 0.5, 'entry_method': 'ADAPTIVE'},
            metadata={'type': 'MOMENTUM'}
        )
        assert decision.confidence == predictions[0].success_probability


class TestRiskToPositionSizingFlow:
    """Test risk assessment to position sizing flow"""

    def test_risk_assessment_to_sizing(self, full_config, sample_market_data):
        """Test flow from risk assessment to position sizing"""
        from trading_bot.orchestrator import PortfolioRiskManager, PositionSizer

        risk_manager = PortfolioRiskManager(full_config)
        position_sizer = PositionSizer()

        positions = {
            'AAPL': {'value': 15000, 'quantity': 100, 'entry_price': 150},
            'GOOGL': {'value': 28000, 'quantity': 10, 'entry_price': 2800}
        }

        # Assess risk
        metrics = risk_manager.assess_portfolio_risk(positions, sample_market_data)
        assert metrics is not None

        # Size new position based on risk
        opportunity = {
            'success_probability': 0.6,
            'expected_return': 0.03,
            'risk': metrics.portfolio_var,
            'volatility': 0.25,
            'stop_loss_percent': 0.05
        }
        portfolio = {'available_capital': 100000 - sum(p['value'] for p in positions.values())}

        size = position_sizer.calculate_position_size(opportunity, portfolio, 'kelly')
        assert size > 0


class TestPerformanceTrackingFlow:
    """Test performance tracking flow"""

    def test_trade_to_metrics_flow(self, full_config):
        """Test flow from trade tracking to metrics calculation"""
        from trading_bot.orchestrator import PerformanceTracker

        tracker = PerformanceTracker(full_config)

        # Simulate trades
        for i in range(20):
            trade = {
                'trade_id': f'TRADE_{i}',
                'timestamp': datetime.now() - timedelta(hours=i),
                'symbol': 'AAPL',
                'pnl': np.random.normal(100, 200),
                'strategy': 'momentum',
                'opportunity_type': 'MOMENTUM'
            }
            tracker.track_trade(trade)

        # Get metrics
        metrics = tracker.get_performance_metrics()
        assert metrics.total_trades == 20
        assert 0 <= metrics.win_rate <= 1

        # Get comparison
        comparison = tracker.get_strategy_comparison()
        assert 'momentum' in comparison


class TestDrawdownProtectionFlow:
    """Test drawdown protection flow"""

    def test_drawdown_to_hedge_flow(self, full_config):
        """Test flow from drawdown detection to hedge calculation"""
        from trading_bot.orchestrator import DrawdownController, HedgeCalculator, RiskMetrics

        controller = DrawdownController()
        hedge_calculator = HedgeCalculator()

        # Simulate drawdown
        controller.equity_peak = 100000
        action, recommendations = controller.check_drawdown(85000)  # 15% drawdown

        assert action == 'defensive'
        assert recommendations['hedge_required'] == True

        # Calculate hedge
        positions = {'AAPL': {'value': 50000}, 'GOOGL': {'value': 35000}}
        metrics = RiskMetrics(
            portfolio_var=0.03, portfolio_cvar=0.04, sharpe_ratio=1.0,
            sortino_ratio=1.5, max_drawdown=0.15, current_drawdown=0.15,
            beta=1.2, correlation_risk=0.6, concentration_risk=0.4,
            liquidity_risk=0.3, tail_risk=0.5, stress_test_results={}
        )

        hedge = hedge_calculator.calculate_hedge(positions, {}, metrics)
        assert 'recommendations' in hedge


class TestAutoOptimizationFlow:
    """Test auto-optimization flow"""

    def test_performance_to_optimization_flow(self, full_config):
        """Test flow from performance analysis to optimization"""
        from trading_bot.orchestrator import PerformanceTracker, AutoOptimizer

        tracker = PerformanceTracker(full_config)
        optimizer = AutoOptimizer()

        # Simulate trades with poor performance
        for i in range(100):
            trade = {
                'trade_id': f'TRADE_{i}',
                'timestamp': datetime.now() - timedelta(hours=i),
                'symbol': 'AAPL',
                'pnl': np.random.normal(-50, 200),  # Negative bias
                'strategy': 'momentum',
                'opportunity_type': 'MOMENTUM'
            }
            tracker.track_trade(trade)

        # Get recommendations
        recommendations = tracker.get_optimization_recommendations()
        assert 'parameter_adjustments' in recommendations


class TestEndToEndOrchestration:
    """Test complete end-to-end orchestration"""

    @pytest.mark.asyncio
    async def test_full_orchestration_cycle(self, full_config, sample_market_data):
        """Test complete orchestration cycle"""
            MasterOrchestrator, ExecutionEngine, OpportunityPredictor,
            PortfolioRiskManager, PerformanceTracker
        )

        # Initialize all components
        orchestrator = MasterOrchestrator(full_config)
        execution_engine = ExecutionEngine(full_config)
        ml_predictor = OpportunityPredictor(full_config)
        risk_manager = PortfolioRiskManager(full_config)
        performance_tracker = PerformanceTracker(full_config)

        # Connect components
        orchestrator.execution_engine = execution_engine
        orchestrator.ml_predictor = ml_predictor
        orchestrator.risk_manager = risk_manager

        # Mock opportunity scanner
        mock_scanner = MagicMock()
        mock_scanner.scan_all_opportunities = AsyncMock(return_value=[
            {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75,
             'expected_return': 0.03, 'risk': 0.4, 'direction': 'BUY',
             'volatility': 0.25, 'volume': 1000000}
        ])
        orchestrator.opportunity_scanner = mock_scanner

        # Run orchestration
        decisions = await orchestrator.orchestrate_trading(sample_market_data)
        assert isinstance(decisions, list)

        # Track performance
        for decision in decisions:
            trade = {
                'trade_id': decision.decision_id,
                'timestamp': datetime.now(),
                'symbol': decision.symbols[0] if decision.symbols else 'UNKNOWN',
                'pnl': np.random.normal(100, 200),
                'strategy': 'orchestrated',
                'opportunity_type': decision.metadata.get('opportunity_type', 'UNKNOWN')
            }
            performance_tracker.track_trade(trade)


class TestComponentCompatibility:
    """Test component compatibility"""

    def test_trading_decision_compatibility(self, full_config):
        """Test TradingDecision works with all components"""
            TradingDecision, ExecutionEngine, PortfolioRiskManager
        )

        decision = TradingDecision(
            decision_id="DEC_001", timestamp=datetime.now(),
            opportunity_ids=["OPP_001"], action="BUY", symbols=["AAPL"],
            allocation={"OPP_001": 5000}, risk_score=0.3,
            expected_return=0.02, confidence=0.75,
            execution_plan={'urgency': 0.5, 'entry_method': 'ADAPTIVE'},
            metadata={'type': 'MOMENTUM'}
        )

        # Test with risk manager
        risk_manager = PortfolioRiskManager(full_config)
        # Use the correct public method name
        valid = risk_manager.assess_portfolio_risk({})
        assert isinstance(valid, dict)

    def test_execution_result_compatibility(self, full_config):
        """Test ExecutionResult works with performance tracker"""
        from trading_bot.orchestrator import ExecutionResult, PerformanceTracker

        result = ExecutionResult(
            order_id="ORD_001", success=True, executed_price=150.0,
            executed_quantity=100, slippage=0.001, execution_time=0.5,
            fees=0.15, venue="exchange1", metadata={'algorithm': 'TWAP'}
        )

        tracker = PerformanceTracker(full_config)
        trade = {
            'trade_id': result.order_id,
            'timestamp': datetime.now(),
            'symbol': 'AAPL',
            'pnl': 100 if result.success else -100,
            'strategy': 'test',
            'opportunity_type': 'TEST'
        }
        tracker.track_trade(trade)
        assert len(tracker.trade_history) == 1


class TestErrorHandling:
    """Test error handling across components"""

    def test_empty_opportunities(self, full_config):
        """Test handling of empty opportunities"""
        from trading_bot.orchestrator import MasterOrchestrator
        orchestrator = MasterOrchestrator(full_config)
        allocations = orchestrator._optimize_allocation([])
        assert allocations == {}

    def test_empty_positions_risk(self, full_config):
        """Test risk assessment with empty positions"""
        from trading_bot.orchestrator import PortfolioRiskManager
        risk_manager = PortfolioRiskManager(full_config)
        metrics = risk_manager.assess_portfolio_risk({}, {})
        assert metrics is not None

    @pytest.mark.asyncio
    async def test_empty_venues_routing(self, full_config):
        """Test routing with empty venues"""
        from trading_bot.orchestrator import SmartOrderRouter
from enum import auto
import numpy
        router = SmartOrderRouter()
        params = {'symbols': ['AAPL'], 'quantity': 1000}
        plan = await router.route(params, {})
        assert plan == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
