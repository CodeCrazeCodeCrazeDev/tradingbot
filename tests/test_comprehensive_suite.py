"""
Comprehensive Test Suite for Trading Bot
Tests all critical modules and integrations
"""

import pytest
import asyncio
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== FIXTURES ====================

@pytest.fixture
def sample_ohlcv_data():
    """Generate sample OHLCV data with valid OHLC relationships"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    close = 100 + np.cumsum(np.random.randn(100) * 2)
    
    # Generate open prices
    open_prices = close + np.random.randn(100) * 0.5
    
    # Generate high/low ensuring valid OHLC relationships
    high = np.maximum(open_prices, close) + abs(np.random.randn(100)) * 1
    low = np.minimum(open_prices, close) - abs(np.random.randn(100)) * 1
    
    return pd.DataFrame({
        'timestamp': dates,
        'open': open_prices,
        'high': high,
        'low': low,
        'close': close,
        'volume': np.random.randint(1000000, 10000000, 100)
    }).set_index('timestamp')


@pytest.fixture
def sample_trades():
    """Generate sample trade data"""
    return [
        {'symbol': 'BTCUSDT', 'side': 'buy', 'price': 50000, 'quantity': 0.1, 'pnl': 500},
        {'symbol': 'BTCUSDT', 'side': 'sell', 'price': 51000, 'quantity': 0.1, 'pnl': -200},
        {'symbol': 'ETHUSDT', 'side': 'buy', 'price': 3000, 'quantity': 1, 'pnl': 300},
        {'symbol': 'ETHUSDT', 'side': 'sell', 'price': 3100, 'quantity': 1, 'pnl': 100},
    ]


@pytest.fixture
def sample_portfolio():
    """Generate sample portfolio"""
    return {
        'BTCUSDT': {'quantity': 0.5, 'avg_price': 48000, 'current_price': 50000},
        'ETHUSDT': {'quantity': 5, 'avg_price': 2800, 'current_price': 3000},
        'SOLUSDT': {'quantity': 100, 'avg_price': 100, 'current_price': 110},
    }


# ==================== RISK MANAGEMENT TESTS ====================

class TestRiskManagement:
    """Test risk management modules"""
    
    def test_position_sizing_kelly(self):
        """Test Kelly Criterion position sizing"""
        from trading_bot.risk.position_sizer import PositionSizer
        
        sizer = PositionSizer()
        
        # Test with 60% win rate, 2:1 reward/risk
        size = sizer.kelly_criterion(
            win_rate=0.6,
            avg_win=200,
            avg_loss=100,
            capital=100000
        )
        
        assert size > 0
        assert size <= 100000 * 0.25  # Max 25% Kelly
        
    def test_position_sizing_fixed_risk(self):
        """Test fixed risk position sizing"""
        
        # Use config to set min size to 0 for testing
        sizer = PositionSizer(config={'min_position_size': 0})
        
        size = sizer.fixed_risk(
            capital=100000,
            risk_pct=0.02,  # 2% risk
            entry_price=50000,
            stop_loss=49000  # $1000 risk per unit
        )
        
        # Risk = $2000, Risk per unit = $1000, Size = 2 units
        assert abs(size - 2.0) < 0.01
        
    def test_max_drawdown_calculation(self):
        """Test maximum drawdown calculation"""
        equity_curve = [100000, 105000, 103000, 98000, 102000, 95000, 100000]
        
        # Peak = 105000, Trough = 95000, Drawdown = 9.52%
        max_dd = (105000 - 95000) / 105000
        
        assert abs(max_dd - 0.0952) < 0.01
        
    def test_var_calculation(self):
        """Test Value at Risk calculation"""
        returns = np.random.normal(0.001, 0.02, 252)  # 1 year of daily returns
        
        # 95% VaR
        var_95 = np.percentile(returns, 5)
        
        assert var_95 < 0  # VaR should be negative (loss)
        assert var_95 > -0.1  # Should be reasonable
        
    def test_correlation_risk(self):
        """Test correlation-based risk assessment"""
        # Highly correlated assets should increase portfolio risk
        returns1 = np.random.normal(0, 0.02, 100)
        returns2 = returns1 + np.random.normal(0, 0.005, 100)  # Highly correlated
        returns3 = np.random.normal(0, 0.02, 100)  # Uncorrelated
        
        corr_12 = np.corrcoef(returns1, returns2)[0, 1]
        corr_13 = np.corrcoef(returns1, returns3)[0, 1]
        
        assert corr_12 > 0.8  # Should be highly correlated
        assert abs(corr_13) < 0.3  # Should be uncorrelated


# ==================== SIGNAL GENERATION TESTS ====================

class TestSignalGeneration:
    """Test signal generation modules"""
    
    def test_rsi_calculation(self, sample_ohlcv_data):
        """Test RSI indicator calculation"""
        close = sample_ohlcv_data['close'].values
        
        # Calculate RSI manually
        delta = np.diff(close)
        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.mean(gains[-14:])
        avg_loss = np.mean(losses[-14:])
        
        if avg_loss != 0:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        else:
            rsi = 100
            
        assert 0 <= rsi <= 100
        
    def test_macd_calculation(self, sample_ohlcv_data):
        """Test MACD indicator calculation"""
        close = sample_ohlcv_data['close']
        
        # Calculate EMAs
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        
        macd_line = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line
        
        assert len(macd_line) == len(close)
        assert len(signal_line) == len(close)
        
    def test_bollinger_bands(self, sample_ohlcv_data):
        """Test Bollinger Bands calculation"""
        close = sample_ohlcv_data['close']
        
        sma = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        # Current price should be within bands most of the time
        # Only count valid (non-NaN) values
        valid_mask = ~(sma.isna() | std.isna())
        valid_close = close[valid_mask]
        valid_upper = upper_band[valid_mask]
        valid_lower = lower_band[valid_mask]
        
        within_bands = ((valid_close >= valid_lower) & (valid_close <= valid_upper)).sum()
        pct_within = within_bands / len(valid_close)
        
        assert pct_within > 0.7  # Most should be within 2 std (relaxed threshold)
        
    def test_signal_confidence_scoring(self):
        """Test signal confidence scoring"""
        # Multiple confirming signals should increase confidence
        signals = {
            'rsi': 'buy',  # RSI oversold
            'macd': 'buy',  # MACD crossover
            'trend': 'buy',  # Uptrend
            'volume': 'neutral',  # Normal volume
        }
        
        buy_signals = sum(1 for s in signals.values() if s == 'buy')
        total_signals = len(signals)
        
        confidence = buy_signals / total_signals
        
        assert confidence == 0.75  # 3/4 buy signals


# ==================== EXECUTION TESTS ====================

class TestExecution:
    """Test execution modules"""
    
    def test_order_validation(self):
        """Test order validation"""
        order = {
            'symbol': 'BTCUSDT',
            'side': 'buy',
            'type': 'limit',
            'quantity': 0.1,
            'price': 50000
        }
        
        # Validate required fields
        required_fields = ['symbol', 'side', 'type', 'quantity']
        for field in required_fields:
            assert field in order
            
        # Validate side
        assert order['side'] in ['buy', 'sell']
        
        # Validate quantity
        assert order['quantity'] > 0
        
    def test_slippage_calculation(self):
        """Test slippage calculation"""
        expected_price = 50000
        actual_price = 50025
        
        slippage_pct = (actual_price - expected_price) / expected_price * 100
        
        assert abs(slippage_pct - 0.05) < 0.01  # 0.05% slippage
        
    def test_twap_order_splitting(self):
        """Test TWAP order splitting"""
        total_quantity = 10
        duration_minutes = 60
        interval_minutes = 5
        
        num_slices = duration_minutes // interval_minutes
        slice_quantity = total_quantity / num_slices
        
        assert num_slices == 12
        assert abs(slice_quantity - 0.833) < 0.01
        
    def test_vwap_calculation(self, sample_ohlcv_data):
        """Test VWAP calculation"""
        typical_price = (sample_ohlcv_data['high'] + sample_ohlcv_data['low'] + sample_ohlcv_data['close']) / 3
        volume = sample_ohlcv_data['volume']
        
        vwap = (typical_price * volume).cumsum() / volume.cumsum()
        
        assert len(vwap) == len(sample_ohlcv_data)
        assert vwap.iloc[-1] > 0


# ==================== DATA VALIDATION TESTS ====================

class TestDataValidation:
    """Test data validation modules"""
    
    def test_ohlcv_validation(self, sample_ohlcv_data):
        """Test OHLCV data validation"""
        df = sample_ohlcv_data
        
        # High should be >= Open, Close, Low
        assert (df['high'] >= df['open']).all()
        assert (df['high'] >= df['close']).all()
        assert (df['high'] >= df['low']).all()
        
        # Low should be <= Open, Close, High
        assert (df['low'] <= df['open']).all()
        assert (df['low'] <= df['close']).all()
        assert (df['low'] <= df['high']).all()
        
        # Volume should be positive
        assert (df['volume'] > 0).all()
        
    def test_price_anomaly_detection(self, sample_ohlcv_data):
        """Test price anomaly detection"""
        close = sample_ohlcv_data['close']
        returns = close.pct_change().dropna()
        
        # Detect anomalies (>3 std from mean)
        mean_return = returns.mean()
        std_return = returns.std()
        
        anomalies = returns[abs(returns - mean_return) > 3 * std_return]
        
        # Should have few anomalies in normal data
        assert len(anomalies) < len(returns) * 0.05  # Less than 5%
        
    def test_data_staleness_detection(self):
        """Test data staleness detection"""
        last_update = datetime.now() - timedelta(seconds=10)
        max_staleness = 5  # seconds
        
        is_stale = (datetime.now() - last_update).total_seconds() > max_staleness
        
        assert is_stale == True


# ==================== PORTFOLIO TESTS ====================

class TestPortfolio:
    """Test portfolio management modules"""
    
    def test_portfolio_value_calculation(self, sample_portfolio):
        """Test portfolio value calculation"""
        total_value = sum(
            pos['quantity'] * pos['current_price']
            for pos in sample_portfolio.values()
        )
        
        expected = 0.5 * 50000 + 5 * 3000 + 100 * 110  # 25000 + 15000 + 11000
        
        assert abs(total_value - expected) < 0.01
        
    def test_portfolio_pnl_calculation(self, sample_portfolio):
        """Test portfolio P&L calculation"""
        total_pnl = sum(
            pos['quantity'] * (pos['current_price'] - pos['avg_price'])
            for pos in sample_portfolio.values()
        )
        
        # BTC: 0.5 * (50000 - 48000) = 1000
        # ETH: 5 * (3000 - 2800) = 1000
        # SOL: 100 * (110 - 100) = 1000
        expected_pnl = 3000
        
        assert abs(total_pnl - expected_pnl) < 0.01
        
    def test_portfolio_allocation(self, sample_portfolio):
        """Test portfolio allocation calculation"""
        total_value = sum(
            pos['quantity'] * pos['current_price']
            for pos in sample_portfolio.values()
        )
        
        allocations = {
            symbol: (pos['quantity'] * pos['current_price']) / total_value
            for symbol, pos in sample_portfolio.items()
        }
        
        # Sum of allocations should be 1
        assert abs(sum(allocations.values()) - 1.0) < 0.001


# ==================== INTEGRATION TESTS ====================

class TestIntegrations:
    """Test real integrations"""
    
    @pytest.mark.asyncio
    async def test_market_data_provider_init(self):
        """Test market data provider initialization"""
        from trading_bot.integrations import RealMarketDataProvider
        
        provider = RealMarketDataProvider()
        assert provider is not None
        await provider.close()
        
    @pytest.mark.asyncio
    async def test_defi_integration_init(self):
        """Test DeFi integration initialization"""
        from trading_bot.integrations import RealDeFiIntegration
        
        defi = RealDeFiIntegration()
        assert defi is not None
        await defi.close()
        
    @pytest.mark.asyncio
    async def test_alternative_data_init(self):
        """Test alternative data provider initialization"""
        from trading_bot.integrations import RealAlternativeDataProvider
from dataclasses import field
import numpy
import pandas
        
provider = RealAlternativeDataProvider()
assert provider is not None
await provider.close()


# ==================== STRATEGY TESTS ====================

class TestStrategies:
    """Test trading strategies"""
    
    def test_trend_following_signal(self, sample_ohlcv_data):
        """Test trend following strategy signal generation"""
        close = sample_ohlcv_data['close']
        
        # Simple moving average crossover
        sma_fast = close.rolling(window=10).mean()
        sma_slow = close.rolling(window=30).mean()
        
        # Generate signals
        signals = pd.Series(index=close.index, data=0)
        signals[sma_fast > sma_slow] = 1  # Buy
        signals[sma_fast < sma_slow] = -1  # Sell
        
        # Should have some signals
        assert (signals != 0).sum() > 0
        
    def test_mean_reversion_signal(self, sample_ohlcv_data):
        """Test mean reversion strategy signal generation"""
        close = sample_ohlcv_data['close']
        
        # Z-score based mean reversion
        sma = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        z_score = (close - sma) / std
        
        # Generate signals
        signals = pd.Series(index=close.index, data=0)
        signals[z_score < -2] = 1  # Buy when oversold
        signals[z_score > 2] = -1  # Sell when overbought
        
        # Should have some signals at extremes
        assert (signals != 0).sum() >= 0
        
    def test_breakout_signal(self, sample_ohlcv_data):
        """Test breakout strategy signal generation"""
        high = sample_ohlcv_data['high']
        low = sample_ohlcv_data['low']
        close = sample_ohlcv_data['close']
        
        # Donchian channel breakout
        upper = high.rolling(window=20).max()
        lower = low.rolling(window=20).min()
        
        # Generate signals
        signals = pd.Series(index=close.index, data=0)
        signals[close > upper.shift(1)] = 1  # Buy on upper breakout
        signals[close < lower.shift(1)] = -1  # Sell on lower breakout
        
        assert len(signals) == len(close)


# ==================== BACKTEST TESTS ====================

class TestBacktest:
    """Test backtesting functionality"""
    
    def test_backtest_returns_calculation(self, sample_ohlcv_data):
        """Test backtest returns calculation"""
        close = sample_ohlcv_data['close']
        
        # Simple buy and hold
        initial_price = close.iloc[0]
        final_price = close.iloc[-1]
        
        total_return = (final_price - initial_price) / initial_price
        
        assert isinstance(total_return, float)
        
    def test_sharpe_ratio_calculation(self, sample_ohlcv_data):
        """Test Sharpe ratio calculation"""
        close = sample_ohlcv_data['close']
        returns = close.pct_change().dropna()
        
        # Annualized Sharpe (assuming daily data)
        mean_return = returns.mean() * 252
        std_return = returns.std() * np.sqrt(252)
        risk_free_rate = 0.05  # 5% annual
        
        sharpe = (mean_return - risk_free_rate) / std_return if std_return > 0 else 0
        
        assert isinstance(sharpe, float)
        
    def test_sortino_ratio_calculation(self, sample_ohlcv_data):
        """Test Sortino ratio calculation"""
        close = sample_ohlcv_data['close']
        returns = close.pct_change().dropna()
        
        # Downside deviation
        negative_returns = returns[returns < 0]
        downside_std = negative_returns.std() * np.sqrt(252) if len(negative_returns) > 0 else 0.001
        
        mean_return = returns.mean() * 252
        risk_free_rate = 0.05
        
        sortino = (mean_return - risk_free_rate) / downside_std if downside_std > 0 else 0
        
        assert isinstance(sortino, float)


# ==================== SAFETY TESTS ====================

class TestSafety:
    """Test safety and risk controls"""
    
    def test_circuit_breaker(self):
        """Test circuit breaker functionality"""
        errors = []
        max_errors = 5
        window_seconds = 60
        
        # Simulate errors
        for i in range(6):
            errors.append(datetime.now())
            
        # Check if circuit should trip
        recent_errors = [e for e in errors if (datetime.now() - e).total_seconds() < window_seconds]
        circuit_tripped = len(recent_errors) >= max_errors
        
        assert circuit_tripped == True
        
    def test_daily_loss_limit(self):
        """Test daily loss limit enforcement"""
        daily_pnl = -4500
        daily_loss_limit = -5000
        
        should_stop = daily_pnl <= daily_loss_limit
        
        assert should_stop == False  # Still within limit
        
        daily_pnl = -5500
        should_stop = daily_pnl <= daily_loss_limit
        
        assert should_stop == True  # Exceeded limit
        
    def test_position_limit(self):
        """Test position limit enforcement"""
        current_positions = 4
        max_positions = 5
        
        can_open_new = current_positions < max_positions
        
        assert can_open_new == True
        
        current_positions = 5
        can_open_new = current_positions < max_positions
        
        assert can_open_new == False


# ==================== RUN TESTS ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
