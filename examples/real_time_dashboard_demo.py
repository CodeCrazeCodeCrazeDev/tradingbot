"""
Elite Trading Bot - Real-Time Dashboard Demo

This demo showcases the comprehensive real-time dashboard for monitoring
trading performance, market analysis, and system metrics.
"""

import sys
import os
import time
import logging
from datetime import datetime, timedelta
import random
import threading
import numpy as np
import pandas as pd

# Add the trading_bot package to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.dashboard.dashboard_server import DashboardServer, DashboardConfig
from trading_bot.dashboard.components import MarketPanel, PerformancePanel, ComponentConfig, ComponentType
from trading_bot.dashboard.components_risk_signal import RiskPanel, SignalPanel
from trading_bot.dashboard.components_analytics import AnalyticsPanel
from trading_bot.dashboard.components_system import SystemPanel
from trading_bot.dashboard.data_provider import DashboardDataProvider
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealTimeDashboardDemo:
    """
    Demonstrates the real-time dashboard capabilities of the Elite Trading Bot.
    """
    
    def __init__(self):
        """Initialize the dashboard demo."""
        # Create dashboard configuration
        self.config = DashboardConfig(
            port=8050,
            host="0.0.0.0",
            theme="darkly",
            title="Elite Trading Bot Dashboard",
            refresh_interval=2000,  # 2 seconds
            debug=False
        )
        
        # Create dashboard server
        self.dashboard = DashboardServer(self.config)
        
        # Create data provider
        self.data_provider = DashboardDataProvider()
        
        # Initialize components
        self._init_components()
        
        # Register data sources
        self._register_data_sources()
        
        # Register section layouts
        self._register_section_layouts()
        
        logger.info("Real-time dashboard demo initialized")
    
    def _init_components(self):
        """Initialize dashboard components."""
        # Create market panel
        market_config = ComponentConfig(
            id="market-panel",
            title="Market Analysis",
            type=ComponentType.CHART,
            refresh_interval=2000,
            width=12
        )
        self.market_panel = MarketPanel(market_config)
        self.dashboard.register_component("market-panel", self.market_panel)
        
        # Create performance panel
        performance_config = ComponentConfig(
            id="performance-panel",
            title="Trading Performance",
            type=ComponentType.CHART,
            refresh_interval=5000,
            width=12
        )
        self.performance_panel = PerformancePanel(performance_config)
        self.dashboard.register_component("performance-panel", self.performance_panel)
        
        # Create risk panel
        risk_config = ComponentConfig(
            id="risk-panel",
            title="Risk Management",
            type=ComponentType.CHART,
            refresh_interval=5000,
            width=12
        )
        self.risk_panel = RiskPanel(risk_config)
        self.dashboard.register_component("risk-panel", self.risk_panel)
        
        # Create signal panel
        signal_config = ComponentConfig(
            id="signal-panel",
            title="Trading Signals",
            type=ComponentType.TABLE,
            refresh_interval=2000,
            width=12
        )
        self.signal_panel = SignalPanel(signal_config)
        self.dashboard.register_component("signal-panel", self.signal_panel)
        
        # Create analytics panel
        analytics_config = ComponentConfig(
            id="analytics-panel",
            title="Advanced Analytics",
            type=ComponentType.CHART,
            refresh_interval=5000,
            width=12
        )
        self.analytics_panel = AnalyticsPanel(analytics_config)
        self.dashboard.register_component("analytics-panel", self.analytics_panel)
        
        # Create system panel
        system_config = ComponentConfig(
            id="system-panel",
            title="System Metrics",
            type=ComponentType.CHART,
            refresh_interval=5000,
            width=12
        )
        self.system_panel = SystemPanel(system_config)
        self.dashboard.register_component("system-panel", self.system_panel)
    
    def _register_data_sources(self):
        """Register data sources for the dashboard."""
        # Register market data source
        self.data_provider.register_data_source(
            "market_data",
            self._generate_market_data,
            update_interval=2.0
        )
        
        # Register performance data source
        self.data_provider.register_data_source(
            "performance_data",
            self._generate_performance_data,
            update_interval=5.0
        )
        
        # Register risk data source
        self.data_provider.register_data_source(
            "risk_data",
            self._generate_risk_data,
            update_interval=5.0
        )
        
        # Register signal data source
        self.data_provider.register_data_source(
            "signal_data",
            self._generate_signal_data,
            update_interval=3.0
        )
        
        # Register analytics data source
        self.data_provider.register_data_source(
            "analytics_data",
            self._generate_analytics_data,
            update_interval=5.0
        )
        
        # Register system data source
        self.data_provider.register_data_source(
            "system_data",
            self._generate_system_data,
            update_interval=2.0
        )
    
    def _register_section_layouts(self):
        """Register section layouts for the dashboard."""
        # Register market section layout
        self.dashboard.register_section_layout("market", self._render_market_section)
        
        # Register performance section layout
        self.dashboard.register_section_layout("performance", self._render_performance_section)
        
        # Register risk section layout
        self.dashboard.register_section_layout("risk", self._render_risk_section)
        
        # Register signals section layout
        self.dashboard.register_section_layout("signals", self._render_signals_section)
        
        # Register analytics section layout
        self.dashboard.register_section_layout("analytics", self._render_analytics_section)
        
        # Register system section layout
        self.dashboard.register_section_layout("system", self._render_system_section)
    
    def _render_market_section(self, data):
        """Render market section."""
        market_data = self.data_provider.get_data("market_data")
        return self.market_panel.render()
    
    def _render_performance_section(self, data):
        """Render performance section."""
        performance_data = self.data_provider.get_data("performance_data")
        return self.performance_panel.render()
    
    def _render_risk_section(self, data):
        """Render risk section."""
        risk_data = self.data_provider.get_data("risk_data")
        return self.risk_panel.render()
    
    def _render_signals_section(self, data):
        """Render signals section."""
        signal_data = self.data_provider.get_data("signal_data")
        return self.signal_panel.render()
    
    def _render_analytics_section(self, data):
        """Render analytics section."""
        analytics_data = self.data_provider.get_data("analytics_data")
        return self.analytics_panel.render()
    
    def _render_system_section(self, data):
        """Render system section."""
        system_data = self.data_provider.get_data("system_data")
        return self.system_panel.render()
    
    def _generate_market_data(self):
        """Generate sample market data."""
        # Generate OHLCV data
        now = datetime.now()
        dates = [now - timedelta(minutes=i) for i in range(100, 0, -1)]
        
        # Generate price data
        base_price = 1.1050
        noise = np.random.normal(0, 0.0002, 100)
        trend = np.linspace(0, 0.0050, 100) * np.sin(np.linspace(0, np.pi * 2, 100))
        prices = base_price + noise + trend
        
        # Create OHLCV data
        ohlcv = []
        for i in range(100):
            candle = {
                "timestamp": dates[i].isoformat(),
                "open": prices[i] - 0.0005 + random.random() * 0.0010,
                "high": prices[i] + 0.0010 + random.random() * 0.0010,
                "low": prices[i] - 0.0010 - random.random() * 0.0010,
                "close": prices[i],
                "volume": 100000 + random.random() * 50000
            }
            ohlcv.append(candle)
        
        # Create market data
        market_data = {
            "symbol": "EURUSD",
            "timeframe": "1h",
            "ohlcv": ohlcv,
            "current_price": prices[-1],
            "daily_change": f"{(prices[-1] - prices[0]) / prices[0] * 100:.2f}%",
            "daily_range": f"{(max(prices) - min(prices)):.5f}",
            "volume": f"{sum(c['volume'] for c in ohlcv):.0f}",
            "spread": f"{0.00010 + random.random() * 0.00005:.5f}"
        }
        
        # Update dashboard data
        self.dashboard.update_data("market_data", market_data)
        
        return market_data
    
    def _generate_performance_data(self):
        """Generate sample performance data."""
        # Generate equity curve
        now = datetime.now()
        dates = [now - timedelta(hours=i) for i in range(100, 0, -1)]
        
        # Generate equity data
        base_equity = 10000
        noise = np.random.normal(0, 50, 100)
        trend = np.linspace(0, 1500, 100)
        equity = base_equity + noise + trend
        
        # Create equity curve data
        equity_curve = []
        for i in range(100):
            point = {
                "timestamp": dates[i].isoformat(),
                "equity": equity[i]
            }
            equity_curve.append(point)
        
        # Generate trade history
        trade_history = []
        for i in range(10):
            # Determine if trade is win or loss
            is_win = random.random() > 0.35
            
            # Generate trade data
            trade = {
                "id": f"T{1000 + i}",
                "symbol": random.choice(["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]),
                "type": random.choice(["Buy", "Sell"]),
                "entry_time": (now - timedelta(hours=random.randint(1, 100))).strftime("%Y-%m-%d %H:%M"),
                "entry_price": round(1.1000 + random.random() * 0.0500, 5),
                "exit_time": (now - timedelta(hours=random.randint(0, 24))).strftime("%Y-%m-%d %H:%M"),
                "exit_price": 0,
                "size": round(random.choice([0.1, 0.2, 0.5, 1.0]), 1),
                "profit_loss": 0,
                "status": "Closed"
            }
            
            # Calculate profit/loss
            direction_multiplier = 1 if trade["type"] == "Buy" else -1
            price_change = random.random() * 0.0100
            if is_win:
                trade["exit_price"] = round(trade["entry_price"] + direction_multiplier * price_change, 5)
                trade["profit_loss"] = round(direction_multiplier * (trade["exit_price"] - trade["entry_price"]) * trade["size"] * 100000, 2)
            else:
                trade["exit_price"] = round(trade["entry_price"] - direction_multiplier * price_change, 5)
                trade["profit_loss"] = round(direction_multiplier * (trade["exit_price"] - trade["entry_price"]) * trade["size"] * 100000, 2)
            
            trade_history.append(trade)
        
        # Create performance data
        performance_data = {
            "equity_curve": equity_curve,
            "trade_history": trade_history,
            "total_profit": f"${equity[-1] - base_equity:.2f}",
            "win_rate": f"{sum(1 for t in trade_history if t['profit_loss'] > 0) / len(trade_history) * 100:.1f}%",
            "profit_factor": f"{sum(t['profit_loss'] for t in trade_history if t['profit_loss'] > 0) / abs(sum(t['profit_loss'] for t in trade_history if t['profit_loss'] < 0)):.2f}",
            "max_drawdown": f"{(max(equity) - min(equity[np.argmax(equity):] or [equity[-1]])) / max(equity) * 100:.2f}%",
            "sharpe_ratio": f"{(equity[-1] - equity[0]) / (np.std(equity) or 1):.2f}",
            "total_trades": len(trade_history),
            "avg_trade": f"${sum(t['profit_loss'] for t in trade_history) / len(trade_history):.2f}"
        }
        
        # Update dashboard data
        self.dashboard.update_data("performance_data", performance_data)
        
        return performance_data
    
    def _generate_risk_data(self):
        """Generate sample risk data."""
        # Generate VaR data
        now = datetime.now()
        dates = [now - timedelta(days=i) for i in range(30, 0, -1)]
        
        # Generate VaR values
        var_95 = [100 + i * 2 + np.random.normal(0, 10) for i in range(30)]
        var_99 = [150 + i * 2 + np.random.normal(0, 15) for i in range(30)]
        actual_loss = [50 + i * 1.5 + np.random.normal(0, 30) for i in range(30)]
        
        # Create VaR data
        var_data = {
            "dates": [d.strftime("%Y-%m-%d") for d in dates],
            "var_95": var_95,
            "var_99": var_99,
            "actual_loss": actual_loss
        }
        
        # Generate risk allocation data
        risk_allocation = {
            "categories": ["EURUSD", "GBPUSD", "USDJPY", "BTCUSD", "XAUUSD"],
            "values": [30, 25, 20, 15, 10]
        }
        
        # Generate black swan protection data
        black_swan_data = {
            "protection_level": random.choice(["Low", "Medium", "High"]),
            "tail_risk_score": round(random.random() * 0.5, 2),
            "volatility_regime": random.choice(["Low", "Normal", "High"]),
            "correlation_status": random.choice(["Stable", "Changing", "Breakdown"]),
            "gap_risk": random.choice(["Low", "Medium", "High"]),
            "hedging_status": random.choice(["Inactive", "Partial", "Active"]),
            "alerts": [
                {"level": "info", "message": "Volatility slightly elevated in EURUSD"},
                {"level": "warning", "message": "Correlation breakdown detected in commodity pairs"}
            ] if random.random() > 0.5 else []
        }
        
        # Create risk data
        risk_data = {
            "account_balance": f"${10000 + random.random() * 1000:.2f}",
            "margin_used": f"${1000 + random.random() * 500:.2f}",
            "free_margin": f"${9000 + random.random() * 500:.2f}",
            "margin_level": f"{900 + random.random() * 100:.0f}%",
            "daily_drawdown": f"{random.random() * 2:.2f}%",
            "risk_exposure": f"{10 + random.random() * 10:.1f}%",
            "risk_per_trade": f"{1 + random.random():.1f}%",
            "portfolio_heat": f"{2 + random.random() * 3:.1f}%",
            "risk_reward_ratio": f"1:{1.5 + random.random():.1f}",
            "risk_level": random.choice(["Low", "Medium", "High"]),
            "var_data": var_data,
            "risk_allocation": risk_allocation,
            "black_swan": black_swan_data
        }
        
        # Update dashboard data
        self.dashboard.update_data("risk_data", risk_data)
        
        return risk_data
    
    def _generate_signal_data(self):
        """Generate sample signal data."""
        # Generate active signals
        active_signals = []
        for i in range(random.randint(0, 5)):
            signal = {
                "symbol": random.choice(["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]),
                "type": random.choice(["Entry", "Exit", "StopLoss", "TakeProfit"]),
                "direction": random.choice(["Buy", "Sell"]),
                "timeframe": random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
                "price": round(1.1000 + random.random() * 0.0500, 5),
                "time": (datetime.now() - timedelta(minutes=random.randint(1, 60))).strftime("%H:%M:%S"),
                "strength": random.choice(["Weak", "Moderate", "Strong"]),
                "source": random.choice(["Price Action", "Indicator", "Pattern", "Liquidity", "Order Flow"])
            }
            active_signals.append(signal)
        
        # Generate signal history
        signal_history = []
        for i in range(10):
            # Determine if signal resulted in win or loss
            is_win = random.random() > 0.35
            
            # Generate signal data
            signal = {
                "symbol": random.choice(["EURUSD", "GBPUSD", "USDJPY", "BTCUSD"]),
                "type": random.choice(["Entry", "Exit"]),
                "direction": random.choice(["Buy", "Sell"]),
                "timeframe": random.choice(["1m", "5m", "15m", "1h", "4h", "1d"]),
                "price": round(1.1000 + random.random() * 0.0500, 5),
                "time": (datetime.now() - timedelta(hours=random.randint(1, 24))).strftime("%Y-%m-%d %H:%M"),
                "result": "Win" if is_win else "Loss",
                "profit_loss": round((random.random() * 100) * (1 if is_win else -1), 2)
            }
            signal_history.append(signal)
        
        # Create signal data
        signal_data = {
            "active_signals": active_signals,
            "signal_history": signal_history
        }
        
        # Update dashboard data
        self.dashboard.update_data("signal_data", signal_data)
        
        return signal_data
    
    def _generate_analytics_data(self):
        """Generate sample analytics data."""
        # Generate liquidity zones
        liquidity_zones = []
        for i in range(5):
            zone = {
                "type": random.choice(["buy_side", "sell_side"]),
                "strength": random.choice(["weak", "moderate", "strong"]),
                "price_level": round(1.1000 + random.random() * 0.0500, 5),
                "price_range": [
                    round(1.1000 + random.random() * 0.0500, 5),
                    round(1.1050 + random.random() * 0.0500, 5)
                ],
                "volume": round(random.random() * 1000000, 0),
                "confidence": random.random(),
                "touches": random.randint(0, 5)
            }
            liquidity_zones.append(zone)
        
        # Generate order flow signals
        order_flow_signals = []
        for i in range(3):
            signal = {
                "type": random.choice(["absorption", "divergence", "climax", "iceberg", "momentum_shift"]),
                "strength": random.choice(["weak", "moderate", "strong"]),
                "price_level": round(1.1000 + random.random() * 0.0500, 5),
                "delta": round((random.random() * 500) * (1 if random.random() > 0.5 else -1), 0),
                "volume": round(random.random() * 1000000, 0),
                "confidence": random.random(),
                "timestamp": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat()
            }
            order_flow_signals.append(signal)
        
        # Create analytics data
        analytics_data = {
            "liquidity": {
                "zones": liquidity_zones,
                "buy_side_liquidity": round(random.random() * 100, 0),
                "sell_side_liquidity": round(random.random() * 100, 0),
                "net_liquidity": round((random.random() * 50) * (1 if random.random() > 0.5 else -1), 0)
            },
            "order_flow": {
                "signals": order_flow_signals,
                "delta_momentum": round(random.random(), 2),
                "absorption_ratio": round(random.random(), 2),
                "momentum_score": round(random.random() * 10, 1)
            },
            "microstructure": {
                "bid_ask_spread": round(0.0001 + random.random() * 0.0001, 5),
                "effective_spread": round(0.0001 + random.random() * 0.0002, 5),
                "price_impact": round(0.00005 + random.random() * 0.0001, 5),
                "depth_imbalance": round(random.random() * 0.5, 2),
                "market_quality_score": round(0.5 + random.random() * 0.5, 2),
                "regime": random.choice(["liquid", "illiquid", "stressed", "volatile"]),
                "institutional_flow": random.choice(["accumulation", "distribution", "neutral", "rotation"])
            }
        }
        
        # Update dashboard data
        self.dashboard.update_data("analytics_data", analytics_data)
        
        return analytics_data
    
    def _generate_system_data(self):
        """Generate sample system data."""
        # Generate CPU usage data
        cpu_usage = [25 + random.random() * 20 for _ in range(10)]
        
        # Generate memory usage data
        memory_usage = [500 + random.random() * 100 for _ in range(10)]
        
        # Generate disk I/O data
        disk_io = [5 + random.random() * 15 for _ in range(10)]
        
        # Generate network I/O data
        network_io = [20 + random.random() * 30 for _ in range(10)]
        
        # Generate logs
        logs = []
        log_levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]
        log_messages = [
            "System heartbeat",
            "Processing market data update",
            "Signal analysis completed",
            "Slow response from data provider",
            "Failed to connect to secondary data source"
        ]
        
        for i in range(10):
            idx = random.randint(0, len(log_levels) - 1)
            log = {
                "level": log_levels[idx],
                "timestamp": (datetime.now() - timedelta(seconds=random.randint(1, 600))).strftime("%Y-%m-%d %H:%M:%S"),
                "message": log_messages[idx]
            }
            logs.append(log)
        
        # Sort logs by timestamp (newest first)
        logs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Generate connections
        connections = [
            {"name": "Market Data Feed", "status": "connected", "latency": 45, "uptime": "12h 30m"},
            {"name": "Broker API", "status": "connected", "latency": 120, "uptime": "12h 30m"},
            {"name": "News Provider", "status": "connected", "latency": 250, "uptime": "12h 30m"},
            {"name": "Secondary Data Source", "status": "disconnected" if random.random() > 0.8 else "connected", 
             "latency": None if random.random() > 0.8 else 180, "uptime": "0h 0m" if random.random() > 0.8 else "12h 30m"},
            {"name": "Historical Data API", "status": "connected", "latency": 180, "uptime": "12h 30m"}
        ]
        
        # Create system data
        system_data = {
            "status": "running",
            "uptime": "12h 30m",
            "cpu_usage": f"{cpu_usage[-1]:.1f}%",
            "memory_usage": f"{memory_usage[-1]:.0f} MB",
            "active_strategies": 3,
            "open_positions": 2,
            "pending_orders": 1,
            "last_signal": "5m ago",
            "data_feed_status": "connected",
            "broker_status": "connected",
            "resources": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "disk_io": disk_io,
                "network_io": network_io
            },
            "logs": logs,
            "connections": connections,
            "execution_times": {
                "market_analysis": [0.05, 0.06, 0.04, 0.07, 0.05],
                "signal_generation": [0.12, 0.15, 0.11, 0.14, 0.13],
                "risk_calculation": [0.03, 0.04, 0.03, 0.03, 0.04],
                "order_execution": [0.08, 0.07, 0.09, 0.08, 0.08]
            },
            "bottlenecks": [
                {"name": "signal_generation", "percentage": 35.2, "mean_time": 0.13},
                {"name": "order_execution", "percentage": 22.1, "mean_time": 0.08},
                {"name": "market_analysis", "percentage": 15.5, "mean_time": 0.05}
            ]
        }
        
        # Update dashboard data
        self.dashboard.update_data("system_data", system_data)
        
        return system_data
    
    def start(self):
        """Start the dashboard demo."""
        # Start data provider
        self.data_provider.start()
        
        # Start dashboard server
        self.dashboard.start(use_thread=False)
    
    def stop(self):
        """Stop the dashboard demo."""
        # Stop data provider
        self.data_provider.stop()
        
        # Stop dashboard server
        self.dashboard.stop()


def main():
    """Main function to run the demo."""
    print("\n" + "="*80)
    print("ELITE TRADING BOT - REAL-TIME DASHBOARD DEMO")
    print("="*80)
    print("\nThis demo showcases the comprehensive real-time dashboard:")
    print("• Market Analysis - Price charts, indicators, and market data")
    print("• Trading Performance - Equity curve, trade history, and performance metrics")
    print("• Risk Management - Position sizing, risk allocation, and VaR analysis")
    print("• Trading Signals - Entry/exit signals and signal history")
    print("• Advanced Analytics - Liquidity zones, order flow, and microstructure")
    print("• System Metrics - Performance monitoring and system status")
    print("\nStarting dashboard server...")
    print("Dashboard will be available at: http://localhost:8050")
    print("\n" + "="*80)
    
    # Create and start demo
    demo = RealTimeDashboardDemo()
    
    try:
        demo.start()
    except KeyboardInterrupt:
        print("\nStopping dashboard demo...")
        demo.stop()
    except Exception as e:
        print(f"\nError running dashboard demo: {str(e)}")
        demo.stop()


if __name__ == "__main__":
    main()
