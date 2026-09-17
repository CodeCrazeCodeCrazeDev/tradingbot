"""
Comprehensive Test Suite for ExecutionEngine and SmartOrderRouter
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def sample_config():
    return {
        'max_slippage': 0.002,
        'urgency_threshold': 0.7,
        'chunk_size': 1000
    }


class TestExecutionEngineImport:
    def test_import_execution_engine(self):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine
        assert ExecutionEngine is not None

    def test_import_order_type(self):
        from trading_bot.orchestrator.execution_engine import OrderType
        assert OrderType.MARKET.value == "market"
        assert OrderType.LIMIT.value == "limit"
        assert OrderType.ICEBERG.value == "iceberg"

    def test_import_execution_algorithm(self):
        from trading_bot.orchestrator.execution_engine import ExecutionAlgorithm
        assert ExecutionAlgorithm.TWAP.value == "twap"
        assert ExecutionAlgorithm.VWAP.value == "vwap"
        assert ExecutionAlgorithm.ADAPTIVE.value == "adaptive"

    def test_import_execution_result(self):
        from trading_bot.orchestrator.execution_engine import ExecutionResult
        assert ExecutionResult is not None

    def test_import_smart_router(self):
        from trading_bot.orchestrator.execution_engine import SmartOrderRouter
        assert SmartOrderRouter is not None


class TestExecutionEngineInit:
    def test_initialization(self, sample_config):
        engine = ExecutionEngine(sample_config)
        assert engine.max_slippage == 0.002
        assert engine.urgency_threshold == 0.7
        assert engine.chunk_size == 1000

    def test_default_initialization(self):
        engine = ExecutionEngine()
        assert engine.max_slippage == 0.002
        assert len(engine.algorithms) == 8

    def test_algorithms_registered(self, sample_config):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine, ExecutionAlgorithm
        engine = ExecutionEngine(sample_config)
        assert ExecutionAlgorithm.TWAP in engine.algorithms
        assert ExecutionAlgorithm.VWAP in engine.algorithms
        assert ExecutionAlgorithm.ADAPTIVE in engine.algorithms
        assert ExecutionAlgorithm.SNIPER in engine.algorithms


class TestExecutionResult:
    def test_execution_result_creation(self):
        result = ExecutionResult(
            order_id="ORD_001", success=True, executed_price=150.0,
            executed_quantity=100, slippage=0.001, execution_time=0.5,
            fees=0.15, venue="exchange1", metadata={'algorithm': 'TWAP'}
        )
        assert result.order_id == "ORD_001"
        assert result.success == True
        assert result.executed_price == 150.0
        assert result.slippage == 0.001


class TestAlgorithmSelection:
    def test_high_urgency_small_quantity_sniper(self, sample_config):
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.9, 'quantity': 500}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.SNIPER

    def test_high_urgency_large_quantity_guerrilla(self, sample_config):
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.9, 'quantity': 5000}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.GUERRILLA

    def test_very_large_order_vwap(self, sample_config):
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.5, 'quantity': 50000}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.VWAP

    def test_medium_order_adaptive(self, sample_config):
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.5, 'quantity': 5000}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.ADAPTIVE

    def test_small_order_liquidity_seeking(self, sample_config):
        engine = ExecutionEngine(sample_config)
        params = {'urgency': 0.5, 'quantity': 500}
        algo = engine._select_algorithm(params)
        assert algo == ExecutionAlgorithm.LIQUIDITY_SEEKING


class TestSlippageCalculation:
    def test_normal_slippage(self, sample_config):
        engine = ExecutionEngine(sample_config)
        slippage = engine._calculate_slippage(100.0, 100.5)
        assert slippage == pytest.approx(0.005, rel=0.01)

    def test_no_expected_price(self, sample_config):
        engine = ExecutionEngine(sample_config)
        slippage = engine._calculate_slippage(None, 100.5)
        assert slippage == 0

    def test_zero_slippage(self, sample_config):
        engine = ExecutionEngine(sample_config)
        slippage = engine._calculate_slippage(100.0, 100.0)
        assert slippage == 0

    def test_negative_slippage(self, sample_config):
        engine = ExecutionEngine(sample_config)
        slippage = engine._calculate_slippage(100.0, 99.5)
        assert slippage == pytest.approx(0.005, rel=0.01)


class TestGuerrillaChunks:
    def test_create_chunks(self, sample_config):
        engine = ExecutionEngine(sample_config)
        chunks = engine._create_guerrilla_chunks(10000)
        assert len(chunks) > 0
        assert sum(chunks) == pytest.approx(10000, rel=0.01)

    def test_chunks_positive(self, sample_config):
        engine = ExecutionEngine(sample_config)
        chunks = engine._create_guerrilla_chunks(10000)
        assert all(chunk > 0 for chunk in chunks)

    def test_small_quantity_chunks(self, sample_config):
        engine = ExecutionEngine(sample_config)
        chunks = engine._create_guerrilla_chunks(100)
        assert sum(chunks) == pytest.approx(100, rel=0.01)


class TestOptimalTrajectory:
    def test_high_urgency_front_loaded(self, sample_config):
        engine = ExecutionEngine(sample_config)
        trajectory = engine._calculate_optimal_trajectory(1000, 60, 0.9)
        assert len(trajectory) == 3
        assert trajectory[0]['quantity'] > trajectory[1]['quantity']

    def test_low_urgency_even_distribution(self, sample_config):
        engine = ExecutionEngine(sample_config)
        trajectory = engine._calculate_optimal_trajectory(1000, 60, 0.5)
        assert len(trajectory) == 5
        quantities = [t['quantity'] for t in trajectory]
        assert max(quantities) - min(quantities) < 1


class TestExecutionStats:
    def test_update_stats(self, sample_config):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine, ExecutionResult
        engine = ExecutionEngine(sample_config)
        result = ExecutionResult(
            order_id="ORD_001", success=True, executed_price=150.0,
            executed_quantity=100, slippage=0.001, execution_time=0.5,
            fees=0.15, venue="exchange1", metadata={'algorithm': 'TWAP'}
        )
        engine._update_execution_stats(result)
        assert 'TWAP' in engine.execution_stats
        assert engine.execution_stats['TWAP']['count'] == 1
        assert engine.execution_stats['TWAP']['success_rate'] == 1.0

    def test_multiple_stats_updates(self, sample_config):
        engine = ExecutionEngine(sample_config)
        for i in range(5):
            result = ExecutionResult(
                order_id=f"ORD_{i}", success=i % 2 == 0, executed_price=150.0,
                executed_quantity=100, slippage=0.001, execution_time=0.5,
                fees=0.15, venue="exchange1", metadata={'algorithm': 'VWAP'}
            )
            engine._update_execution_stats(result)
        assert engine.execution_stats['VWAP']['count'] == 5
        assert engine.execution_stats['VWAP']['success_rate'] == 0.6


@pytest.mark.asyncio
class TestAsyncExecutionMethods:
    async def test_execute_slice(self, sample_config):
        engine = ExecutionEngine(sample_config)
        result = await engine._execute_slice('AAPL', 100, 'BUY', {})
        assert 'quantity' in result
        assert 'cost' in result
        assert 'price' in result
        assert result['quantity'] == 100

    async def test_get_volume_profile(self, sample_config):
        engine = ExecutionEngine(sample_config)
        profile = await engine._get_volume_profile('AAPL')
        assert isinstance(profile, dict)
        assert len(profile) == 24
        assert profile[10] > profile[2]

    async def test_get_market_volume(self, sample_config):
        engine = ExecutionEngine(sample_config)
        volume = await engine._get_market_volume('AAPL')
        assert volume > 0

    async def test_assess_market_conditions(self, sample_config):
        engine = ExecutionEngine(sample_config)
        conditions = await engine._assess_market_conditions('AAPL')
        assert 'liquidity' in conditions
        assert 'volatility' in conditions
        assert 'trend' in conditions

    async def test_find_best_price(self, sample_config):
        engine = ExecutionEngine(sample_config)
        venue, price = await engine._find_best_price('AAPL', 'BUY')
        assert venue is not None
        assert price > 0

    async def test_map_liquidity(self, sample_config):
        engine = ExecutionEngine(sample_config)
        liquidity_map = await engine._map_liquidity('AAPL')
        assert isinstance(liquidity_map, dict)
        assert len(liquidity_map) > 0
        assert all(v > 0 for v in liquidity_map.values())

    async def test_send_order(self, sample_config):
        from trading_bot.orchestrator.execution_engine import ExecutionEngine, OrderType
        engine = ExecutionEngine(sample_config)
        result = await engine._send_order(
            venue='exchange1', symbol='AAPL',
            order_type=OrderType.MARKET, quantity=100, action='BUY'
        )
        assert result['success'] == True
        assert result['quantity'] == 100


class TestSmartOrderRouter:
    def test_initialization(self):
        router = SmartOrderRouter()
        assert router.routing_cache == {}
        assert router.venue_scores == {}

    @pytest.mark.asyncio
    async def test_route(self):
        router = SmartOrderRouter()
        params = {'symbols': ['AAPL'], 'quantity': 1000}
        venues = {
            'exchange1': {'fee_rate': 0.001, 'latency': 5, 'liquidity': 10000, 'fill_rate': 0.98},
            'exchange2': {'fee_rate': 0.002, 'latency': 10, 'liquidity': 5000, 'fill_rate': 0.95}
        }
        routing_plan = await router.route(params, venues)
        assert isinstance(routing_plan, dict)
        assert len(routing_plan) > 0

    @pytest.mark.asyncio
    async def test_score_venues(self):
        router = SmartOrderRouter()
        venues = {
            'exchange1': {'fee_rate': 0.001, 'latency': 5, 'liquidity': 10000, 'fill_rate': 0.98},
            'exchange2': {'fee_rate': 0.002, 'latency': 10, 'liquidity': 5000, 'fill_rate': 0.95}
        }
        scores = await router._score_venues('AAPL', 1000, venues)
        assert 'exchange1' in scores
        assert 'exchange2' in scores
        assert scores['exchange1'] > scores['exchange2']

    def test_create_routing_plan(self):
        router = SmartOrderRouter()
        venue_scores = {'exchange1': 0.9, 'exchange2': 0.7, 'exchange3': 0.5}
        plan = router._create_routing_plan(venue_scores, 1000)
        assert isinstance(plan, dict)

    def test_routing_plan_priority(self):
    pass
import numpy
        router = SmartOrderRouter()
        venue_scores = {'exchange1': 0.9, 'exchange2': 0.7}
        plan = router._create_routing_plan(venue_scores, 1000)
        if 'exchange1' in plan and 'exchange2' in plan:
            assert plan['exchange1']['priority'] < plan['exchange2']['priority']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
