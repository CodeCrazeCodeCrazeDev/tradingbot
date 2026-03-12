"""
Comprehensive Test Suite for MasterOrchestrator
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock


@pytest.fixture
def sample_config():
    return {
        'capital': 100000,
        'max_risk_per_trade': 0.02,
        'max_portfolio_risk': 0.06,
        'max_correlation': 0.7
    }


@pytest.fixture
def sample_opportunities():
    return [
        {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75, 'expected_return': 0.03, 'risk': 0.4, 'direction': 'BUY'},
        {'type': 'ARBITRAGE', 'symbol': 'GOOGL', 'confidence': 0.85, 'expected_return': 0.01, 'risk': 0.2, 'direction': 'BUY'},
        {'type': 'NEWS', 'symbol': 'MSFT', 'confidence': 0.65, 'expected_return': 0.02, 'risk': 0.5, 'direction': 'SELL'}
    ]


@pytest.fixture
def sample_positions():
    return {
        'AAPL': {'value': 15000, 'quantity': 100, 'entry_price': 150},
        'GOOGL': {'value': 28000, 'quantity': 10, 'entry_price': 2800}
    }


class TestMasterOrchestratorImport:
    def test_import(self):
        from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator
        assert MasterOrchestrator is not None

    def test_trading_mode_import(self):
        from trading_bot.orchestrator.master_orchestrator import TradingMode
        assert TradingMode.BALANCED.value == "balanced"
        assert TradingMode.AGGRESSIVE.value == "aggressive"

    def test_trading_decision_import(self):
        from trading_bot.orchestrator.master_orchestrator import TradingDecision
        assert TradingDecision is not None


class TestMasterOrchestratorInit:
    def test_initialization(self, sample_config):
        from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator, TradingMode
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator.total_capital == 100000
        assert orchestrator.max_risk_per_trade == 0.02
        assert orchestrator.trading_mode == TradingMode.BALANCED

    def test_default_initialization(self):
        orchestrator = MasterOrchestrator()
        assert orchestrator.total_capital == 100000
        assert orchestrator.active_positions == {}


class TestTradingModeFiltering:
    def test_filter_balanced_mode(self, sample_config, sample_opportunities):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.trading_mode = TradingMode.BALANCED
        filtered = orchestrator._filter_by_mode_and_risk(sample_opportunities)
        assert len(filtered) == 3

    def test_filter_conservative_mode(self, sample_config, sample_opportunities):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.trading_mode = TradingMode.CONSERVATIVE
        filtered = orchestrator._filter_by_mode_and_risk(sample_opportunities)
        assert all(opp.get('risk', 0.5) <= 0.3 for opp in filtered)

    def test_matches_scalping_mode(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.trading_mode = TradingMode.SCALPING
        assert orchestrator._matches_trading_mode({'type': 'ARBITRAGE'}) == True
        assert orchestrator._matches_trading_mode({'type': 'MOMENTUM'}) == False

    def test_matches_swing_mode(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.trading_mode = TradingMode.SWING
        assert orchestrator._matches_trading_mode({'type': 'MOMENTUM'}) == True


class TestCorrelationRemoval:
    def test_remove_correlated_trades(self, sample_config, sample_opportunities):
        orchestrator = MasterOrchestrator(sample_config)
        for i, opp in enumerate(sample_opportunities):
            opp['unique_id'] = f"OPP_{i}"
            opp['ml_score'] = opp.get('confidence', 0.5)
        uncorrelated = orchestrator._remove_correlated_trades(sample_opportunities)
        symbols = [opp.get('symbol') for opp in uncorrelated]
        assert len(symbols) == len(set(symbols))


class TestAllocationOptimization:
    def test_optimize_allocation(self, sample_config, sample_opportunities):
        orchestrator = MasterOrchestrator(sample_config)
        for i, opp in enumerate(sample_opportunities):
            opp['unique_id'] = f"OPP_{i}"
            opp['ml_score'] = opp.get('confidence', 0.5)
        allocations = orchestrator._optimize_allocation(sample_opportunities)
        assert isinstance(allocations, dict)
        assert all(v >= 0 for v in allocations.values())

    def test_kelly_fraction(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        kelly = orchestrator._calculate_kelly_fraction(0.05, 0.02, 0.7)
        assert 0 <= kelly <= 0.25

    def test_kelly_zero_risk(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        kelly = orchestrator._calculate_kelly_fraction(0.05, 0, 0.5)
        assert kelly == 0


class TestCapitalManagement:
    def test_available_capital(self, sample_config, sample_positions):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.active_positions = sample_positions
        available = orchestrator._get_available_capital()
        used = sum(pos['value'] for pos in sample_positions.values())
        reserve = 100000 * 0.1
        expected = max(0, 100000 - used - reserve)
        assert available == expected


class TestActionDetermination:
    def test_determine_buy_action(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._determine_action({'direction': 'BUY'}) == 'BUY'
        assert orchestrator._determine_action({'direction': 'LONG'}) == 'BUY'

    def test_determine_sell_action(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._determine_action({'direction': 'SELL'}) == 'SELL'
        assert orchestrator._determine_action({'direction': 'SHORT'}) == 'SELL'

    def test_determine_hold_action(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._determine_action({'direction': 'NEUTRAL'}) == 'HOLD'


class TestSymbolExtraction:
    def test_extract_single_symbol(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._extract_symbols({'symbol': 'AAPL'}) == ['AAPL']

    def test_extract_multiple_symbols(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._extract_symbols({'symbols': ['AAPL', 'GOOGL']}) == ['AAPL', 'GOOGL']

    def test_extract_pair(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        assert orchestrator._extract_symbols({'pair': ('AAPL', 'GOOGL')}) == ['AAPL', 'GOOGL']


class TestModeAdjustment:
    def test_high_volatility_defensive(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.adjust_trading_mode({'volatility': 0.5, 'trend_strength': 0.5, 'volume': 'normal'})
        assert orchestrator.trading_mode == TradingMode.DEFENSIVE

    def test_low_volatility_aggressive(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.adjust_trading_mode({'volatility': 0.05, 'trend_strength': 0.5, 'volume': 'normal'})
        assert orchestrator.trading_mode == TradingMode.AGGRESSIVE

    def test_strong_trend_swing(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.adjust_trading_mode({'volatility': 0.2, 'trend_strength': 0.8, 'volume': 'normal'})
        assert orchestrator.trading_mode == TradingMode.SWING


class TestPerformanceSummary:
    def test_get_summary(self, sample_config):
        orchestrator = MasterOrchestrator(sample_config)
        summary = orchestrator.get_performance_summary()
        assert 'win_rate' in summary
        assert 'sharpe_ratio' in summary
        assert 'total_capital' in summary


class TestRiskValidation:
    def test_check_portfolio_risk(self, sample_config, sample_positions):
        from trading_bot.orchestrator.master_orchestrator import MasterOrchestrator, TradingDecision
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.active_positions = sample_positions
        decision = TradingDecision(
            decision_id="DEC_001", timestamp=datetime.now(),
            opportunity_ids=["OPP_001"], action="BUY", symbols=["AAPL"],
            allocation={"OPP_001": 1000}, risk_score=0.1,
            expected_return=0.02, confidence=0.75,
            execution_plan={}, metadata={}
        )
        assert orchestrator._check_portfolio_risk(decision) == True

    def test_check_position_limits(self, sample_config, sample_positions):
        orchestrator = MasterOrchestrator(sample_config)
        orchestrator.active_positions = sample_positions
        decision = TradingDecision(
            decision_id="DEC_001", timestamp=datetime.now(),
            opportunity_ids=["OPP_001"], action="BUY", symbols=["AAPL"],
            allocation={"OPP_001": 1000}, risk_score=0.3,
            expected_return=0.02, confidence=0.75,
            execution_plan={}, metadata={}
        )
        assert orchestrator._check_position_limits(decision) == True


@pytest.mark.asyncio
class TestAsyncOrchestration:
    async def test_orchestrate_trading(self, sample_config):
    pass
import numpy
        orchestrator = MasterOrchestrator(sample_config)
        mock_scanner = MagicMock()
        mock_scanner.scan_all_opportunities = AsyncMock(return_value=[
            {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75, 'expected_return': 0.03, 'risk': 0.4, 'direction': 'BUY'}
        ])
        orchestrator.opportunity_scanner = mock_scanner
        decisions = await orchestrator.orchestrate_trading({'AAPL': {'price': 150}})
        assert isinstance(decisions, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
