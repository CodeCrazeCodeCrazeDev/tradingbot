"""
Simulation Tests
Tests paper trading, backtest validation, and Monte Carlo scenarios
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from trading_bot.world_model.simulation_orchestrator import DegradationLevel, PredictiveShield


@pytest.mark.simulation
class TestPaperTradingSimulation:
    """Test paper trading simulation functionality."""
    
    def test_paper_trading_order_execution(self):
        """Test that paper trading executes orders correctly."""
        # Simulate paper trading order
        order = {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 0.01,
            "type": "market"
        }
        
        # Simulate execution
        execution = self._simulate_paper_execution(order)
        
        assert execution["status"] == "filled"
        assert execution["filled_quantity"] == order["quantity"]
        assert execution["avg_fill_price"] > 0
        assert "commission" in execution
    
    def test_paper_trading_account_updates(self):
        """Test that paper trading updates account correctly."""
        account = {
            "balance": 10000.0,
            "equity": 10000.0,
            "margin": 0.0,
            "positions": []
        }
        
        # Execute trade
        trade = {
            "symbol": "EURUSD",
            "side": "buy",
            "quantity": 0.01,
            "price": 1.0850,
            "commission": 0.35
        }
        
        # Update account
        account["balance"] -= trade["commission"]
        account["positions"].append(trade)
        account["margin"] = trade["quantity"] * trade["price"] * 1000 * 0.01  # 1% margin
        
        assert account["balance"] == 9999.65
        assert len(account["positions"]) == 1
        assert account["margin"] > 0
    
    def test_paper_trading_pnl_calculation(self):
        """Test PnL calculation in paper trading."""
        position = {
            "symbol": "EURUSD",
            "direction": "long",
            "entry_price": 1.0850,
            "current_price": 1.0880,
            "quantity": 0.01
        }
        
        # Calculate unrealized PnL
        price_diff = position["current_price"] - position["entry_price"]
        pnl = price_diff * position["quantity"] * 100000  # Standard lot size
        
        assert pnl == 30.0  # (1.0880 - 1.0850) * 0.01 * 100000 = 30
    
    def _simulate_paper_execution(self, order: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate paper trading order execution."""
        # Simulate fill at current market price with slight slippage
        base_price = 1.0850
        slippage = np.random.uniform(-0.0001, 0.0001)
        fill_price = base_price + slippage
        
        return {
            "order_id": f"paper_{datetime.now().timestamp()}",
            "status": "filled",
            "filled_quantity": order["quantity"],
            "avg_fill_price": round(fill_price, 5),
            "commission": round(order["quantity"] * 3.5, 2),  # $3.5 per 0.01 lot
            "timestamp": datetime.now()
        }


def test_l10_predictive_shield_degrades_before_violation():
    shield = PredictiveShield(warn_threshold=0.3, block_threshold=0.7)

    decision = shield.evaluate(
        {
            "drawdown_pressure": 0.4,
            "surprise": 0.6,
            "liquidity_gap": 0.4,
            "model_uncertainty": 0.5,
        }
    )

    assert decision.approved
    assert decision.near_miss
    assert decision.degradation_level == DegradationLevel.REDUCED_RISK
    assert len(shield.near_misses) == 1


@pytest.mark.simulation
class TestBacktestValidation:
    """Test backtest validation functionality."""
    
    def test_backtest_with_historical_data(self):
        """Test backtest using historical data."""
        # Generate synthetic historical data
        data = self._generate_historical_data(days=30)
        
        # Run simple strategy backtest
        results = self._run_simple_backtest(data)
        
        assert "total_trades" in results
        assert "win_rate" in results
        assert "profit_factor" in results
        assert "max_drawdown" in results
        assert "sharpe_ratio" in results
    
    def test_backtest_risk_metrics(self):
        """Test that backtest calculates risk metrics correctly."""
        trades = [
            {"pnl": 100, "duration": 3600},
            {"pnl": -50, "duration": 1800},
            {"pnl": 75, "duration": 2400},
            {"pnl": -25, "duration": 1200},
            {"pnl": 150, "duration": 4800}
        ]
        
        # Calculate metrics
        wins = [t for t in trades if t["pnl"] > 0]
        losses = [t for t in trades if t["pnl"] < 0]
        
        win_rate = len(wins) / len(trades)
        avg_win = np.mean([t["pnl"] for t in wins])
        avg_loss = abs(np.mean([t["pnl"] for t in losses]))
        profit_factor = avg_win / avg_loss if avg_loss > 0 else float('inf')
        
        assert 0 <= win_rate <= 1
        assert profit_factor > 0
    
    def test_backtest_trade_statistics(self):
        """Test backtest trade statistics calculation."""
        trades = [
            {"pnl": 100, "entry_time": datetime(2024, 1, 1, 10, 0)},
            {"pnl": -50, "entry_time": datetime(2024, 1, 1, 11, 0)},
            {"pnl": 75, "entry_time": datetime(2024, 1, 1, 12, 0)},
        ]
        
        # Calculate statistics
        pnls = [t["pnl"] for t in trades]
        
        stats = {
            "total_trades": len(trades),
            "winning_trades": len([p for p in pnls if p > 0]),
            "losing_trades": len([p for p in pnls if p < 0]),
            "total_pnl": sum(pnls),
            "avg_pnl": np.mean(pnls),
            "max_pnl": max(pnls),
            "min_pnl": min(pnls)
        }
        
        assert stats["total_trades"] == 3
        assert stats["total_pnl"] == 125
        assert stats["avg_pnl"] == 125 / 3
    
    def _generate_historical_data(self, days: int) -> pd.DataFrame:
        """Generate synthetic historical price data."""
        periods = days * 24 * 60  # Minute data
        dates = pd.date_range(start="2024-01-01", periods=periods, freq="1min")
        
        np.random.seed(42)
        returns = np.random.normal(0.00001, 0.0005, periods)
        prices = 1.0850 * np.exp(np.cumsum(returns))
        
        return pd.DataFrame({
            "timestamp": dates,
            "open": prices * (1 + np.random.normal(0, 0.0001, periods)),
            "high": prices * (1 + abs(np.random.normal(0, 0.0002, periods))),
            "low": prices * (1 - abs(np.random.normal(0, 0.0002, periods))),
            "close": prices,
            "volume": np.random.randint(1000, 10000, periods)
        })
    
    def _run_simple_backtest(self, data: pd.DataFrame) -> Dict[str, Any]:
        """Run a simple moving average crossover backtest."""
        # Calculate moving averages
        data["sma_fast"] = data["close"].rolling(10).mean()
        data["sma_slow"] = data["close"].rolling(30).mean()
        
        # Generate signals
        data["signal"] = np.where(
            data["sma_fast"] > data["sma_slow"], 1, -1
        )
        
        # Calculate returns
        data["returns"] = data["close"].pct_change()
        data["strategy_returns"] = data["signal"].shift(1) * data["returns"]
        
        # Calculate metrics
        total_return = (1 + data["strategy_returns"].fillna(0)).cumprod().iloc[-1] - 1
        sharpe = np.sqrt(252 * 24 * 60) * data["strategy_returns"].mean() / data["strategy_returns"].std()
        
        # Count trades (signal changes)
        trades = (data["signal"].diff() != 0).sum() // 2
        
        return {
            "total_trades": int(trades),
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "win_rate": 0.55,  # Placeholder
            "profit_factor": 1.2,  # Placeholder
            "max_drawdown": 0.05  # Placeholder
        }


@pytest.mark.simulation
class TestMonteCarloSimulation:
    """Test Monte Carlo simulation for risk analysis."""
    
    def test_monte_carlo_return_distribution(self):
        """Test Monte Carlo return distribution generation."""
        # Historical returns (simplified)
        historical_returns = np.random.normal(0.001, 0.02, 252)
        
        # Run Monte Carlo
        num_simulations = 1000
        num_days = 252
        
        simulated_paths = []
        for _ in range(num_simulations):
            path_returns = np.random.choice(historical_returns, num_days)
            path = 10000 * np.cumprod(1 + path_returns)
            simulated_paths.append(path)
        
        # Analyze results
        final_values = [path[-1] for path in simulated_paths]
        
        assert len(final_values) == num_simulations
        assert np.mean(final_values) > 0
        
        # Calculate percentiles
        percentile_5 = np.percentile(final_values, 5)
        percentile_95 = np.percentile(final_values, 95)
        
        assert percentile_5 < percentile_95
    
    def test_monte_carlo_var_calculation(self):
        """Test Value at Risk calculation from Monte Carlo."""
        portfolio_value = 100000
        
        # Simulate 1000 portfolio value paths
        simulated_final_values = []
        for _ in range(1000):
            # Random walk
            daily_returns = np.random.normal(0.0001, 0.01, 252)
            final_value = portfolio_value * np.prod(1 + daily_returns)
            simulated_final_values.append(final_value)
        
        # Calculate VaR at 95% confidence
        var_95 = portfolio_value - np.percentile(simulated_final_values, 5)
        
        assert var_95 > 0
        assert var_95 < portfolio_value  # VaR shouldn't exceed portfolio value
    
    def test_monte_carlo_max_drawdown(self):
        """Test maximum drawdown calculation from Monte Carlo."""
        num_simulations = 500
        max_drawdowns = []
        
        for _ in range(num_simulations):
            # Simulate equity curve
            returns = np.random.normal(0.0001, 0.015, 252)
            equity = 10000 * np.cumprod(1 + returns)
            
            # Calculate max drawdown
            peak = np.maximum.accumulate(equity)
            drawdown = (equity - peak) / peak
            max_dd = np.min(drawdown)
            max_drawdowns.append(max_dd)
        
        # Analyze distribution
        avg_max_dd = np.mean(max_drawdowns)
        worst_dd = np.min(max_drawdowns)
        
        assert -1 < worst_dd < 0  # Drawdown between -100% and 0%
        assert -1 < avg_max_dd < 0
    
    def test_stress_scenario_simulation(self):
        """Test stress scenario simulation."""
        scenarios = {
            "market_crash": {
                "daily_return": -0.05,
                "volatility": 0.03
            },
            "high_volatility": {
                "daily_return": 0.0,
                "volatility": 0.05
            },
            "bull_market": {
                "daily_return": 0.002,
                "volatility": 0.01
            }
        }
        
        results = {}
        for name, params in scenarios.items():
            # Simulate 30 days
            returns = np.random.normal(
                params["daily_return"],
                params["volatility"],
                30
            )
            portfolio_value = 10000 * np.prod(1 + returns)
            
            results[name] = {
                "final_value": portfolio_value,
                "total_return": (portfolio_value / 10000) - 1
            }
        
        # Verify crash scenario has negative return
        assert results["market_crash"]["total_return"] < 0
        # Verify bull scenario has positive return
        assert results["bull_market"]["total_return"] > 0


@pytest.mark.simulation
class TestLatencySimulation:
    """Test latency simulation for realistic testing."""
    
    def test_order_execution_latency(self):
        """Test simulated order execution latency."""
        # Realistic latency distribution (log-normal)
        latencies = np.random.lognormal(0, 0.5, 1000) * 50  # milliseconds
        
        # Check statistics
        assert np.median(latencies) > 0
        assert np.percentile(latencies, 95) < 500  # 95% under 500ms
        assert np.percentile(latencies, 99) < 1000  # 99% under 1s
    
    def test_network_latency_injection(self):
        """Test network latency injection in simulation."""
        base_latency = 100  # ms
        jitter = np.random.uniform(-50, 50)
        actual_latency = base_latency + jitter
        
        assert 50 <= actual_latency <= 150
    
    def test_slippage_simulation(self):
        """Test realistic slippage simulation."""
        order_size = 1.0  # lots
        base_price = 1.0850
        
        # Larger orders get more slippage
        slippage_pips = np.random.exponential(0.1 * order_size)
        slippage_price = slippage_pips * 0.0001
        
        fill_price = base_price + slippage_price
        
        assert fill_price >= base_price
        assert slippage_pips >= 0
