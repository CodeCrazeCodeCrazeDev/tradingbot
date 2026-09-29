"""
Tool Integration System

Provides comprehensive tool access for the Aletheia research system.
Integrates market data, backtesting, risk analysis, and knowledge base tools.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio

logger = logging.getLogger(__name__)


class BaseTool(ABC):
    """Base class for all tools"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
        self.call_count = 0
        self.last_used = None
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool with given parameters"""
        pass
    
    async def invoke(self, **kwargs) -> Dict[str, Any]:
        """Invoke tool with tracking"""
        if not self.enabled:
            return {"error": f"Tool {self.name} is disabled"}
        
        self.call_count += 1
        self.last_used = datetime.now()
        
        try:
            result = await self.execute(**kwargs)
            result["tool_name"] = self.name
            result["success"] = True
            return result
        except Exception as e:
            logger.error(f"Tool {self.name} execution failed: {e}")
            return {
                "tool_name": self.name,
                "success": False,
                "error": str(e)
            }


class MarketDataTool(BaseTool):
    """Tool for accessing market data"""
    
    def __init__(self, data_source: Optional[Any] = None):
        super().__init__(
            name="market_data",
            description="Access real-time and historical market data"
        )
        self.data_source = data_source
        self.cache = {}
    
    async def execute(
        self,
        symbol: str,
        timeframe: str = "1h",
        periods: int = 100,
        data_type: str = "ohlcv"
    ) -> Dict[str, Any]:
        """
        Fetch market data
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD", "AAPL")
            timeframe: Data timeframe (e.g., "1m", "5m", "1h", "1d")
            periods: Number of periods to fetch
            data_type: Type of data (ohlcv, tick, etc.)
        """
        cache_key = f"{symbol}_{timeframe}_{periods}_{data_type}"
        
        # Check cache
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(minutes=5):
                return {
                    "data": cached["data"],
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "periods": len(cached["data"]),
                    "cached": True
                }
        
        # Simulate data fetch (in real system would connect to data provider)
        data = self._generate_simulated_data(symbol, timeframe, periods)
        
        # Cache result
        self.cache[cache_key] = {
            "data": data,
            "timestamp": datetime.now()
        }
        
        return {
            "data": data,
            "symbol": symbol,
            "timeframe": timeframe,
            "periods": len(data),
            "cached": False
        }
    
    def _generate_simulated_data(self, symbol: str, timeframe: str, periods: int) -> List[Dict]:
        """Generate simulated OHLCV data"""
        import random
        import math
        
        base_price = 100.0
        if "EUR" in symbol or "GBP" in symbol:
            base_price = 1.1
        elif "JPY" in symbol:
            base_price = 150.0
        
        data = []
        price = base_price
        
        for i in range(periods):
            # Random walk
            change = (random.random() - 0.5) * 0.02 * price
            open_price = price
            close_price = price + change
            high_price = max(open_price, close_price) + abs(change) * random.random()
            low_price = min(open_price, close_price) - abs(change) * random.random()
            volume = int(random.uniform(1000, 10000))
            
            data.append({
                "timestamp": (datetime.now() - timedelta(hours=periods-i)).isoformat(),
                "open": round(open_price, 5),
                "high": round(high_price, 5),
                "low": round(low_price, 5),
                "close": round(close_price, 5),
                "volume": volume
            })
            
            price = close_price
        
        return data


class BacktestTool(BaseTool):
    """Tool for running strategy backtests"""
    
    def __init__(self):
        super().__init__(
            name="backtest",
            description="Run backtests on trading strategies"
        )
        self.backtest_history = []
    
    async def execute(
        self,
        strategy_rules: Dict[str, Any],
        market_data: List[Dict],
        initial_capital: float = 10000.0,
        position_size: float = 0.02
    ) -> Dict[str, Any]:
        """
        Run backtest on strategy
        
        Args:
            strategy_rules: Entry/exit rules and parameters
            market_data: Historical price data
            initial_capital: Starting capital
            position_size: Position size as fraction of capital
        """
        logger.info(f"Running backtest with {len(market_data)} data points")
        
        # Simulate backtest
        capital = initial_capital
        trades = []
        position = None  # None, "long", or "short"
        entry_price = 0
        
        for i, candle in enumerate(market_data):
            if i < 20:  # Skip first 20 for indicators
                continue
            
            # Simple simulation: random entry/exit based on rules
            if position is None:
                # Check entry conditions (simplified)
                if i % 10 == 0:  # Simulate entry signal
                    position = "long"
                    entry_price = candle["close"]
                    
                    trade = {
                        "entry_time": candle["timestamp"],
                        "entry_price": entry_price,
                        "position": position,
                        "size": capital * position_size
                    }
                    trades.append(trade)
            
            else:
                # Check exit conditions (simplified)
                pnl_pct = (candle["close"] - entry_price) / entry_price
                
                # Exit on profit target or stop loss
                if pnl_pct > 0.03 or pnl_pct < -0.02 or i % 15 == 0:
                    # Close position
                    trade = trades[-1]
                    trade["exit_time"] = candle["timestamp"]
                    trade["exit_price"] = candle["close"]
                    trade["pnl"] = trade["size"] * pnl_pct
                    trade["pnl_pct"] = pnl_pct
                    
                    capital += trade["pnl"]
                    position = None
        
        # Calculate metrics
        closed_trades = [t for t in trades if "exit_time" in t]
        
        if closed_trades:
            wins = sum(1 for t in closed_trades if t["pnl"] > 0)
            losses = len(closed_trades) - wins
            win_rate = wins / len(closed_trades)
            
            total_profit = sum(t["pnl"] for t in closed_trades if t["pnl"] > 0)
            total_loss = abs(sum(t["pnl"] for t in closed_trades if t["pnl"] < 0))
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            returns = [t["pnl_pct"] for t in closed_trades]
            avg_return = sum(returns) / len(returns)
            
            # Calculate Sharpe (simplified)
            sharpe = avg_return / (sum((r - avg_return)**2 for r in returns) / len(returns))**0.5 if len(returns) > 1 else 0
            
            # Max drawdown
            peak = initial_capital
            max_dd = 0
            running_capital = initial_capital
            
            for trade in closed_trades:
                running_capital += trade["pnl"]
                if running_capital > peak:
                    peak = running_capital
                dd = (peak - running_capital) / peak
                max_dd = max(max_dd, dd)
        else:
            win_rate = 0
            profit_factor = 0
            sharpe = 0
            max_dd = 0
        
        result = {
            "total_trades": len(closed_trades),
            "winning_trades": wins if closed_trades else 0,
            "losing_trades": losses if closed_trades else 0,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "final_capital": capital,
            "total_return": (capital - initial_capital) / initial_capital,
            "trades": closed_trades[:10]  # First 10 for detail
        }
        
        self.backtest_history.append({
            "timestamp": datetime.now(),
            "trades_count": len(closed_trades),
            "sharpe": sharpe,
            "result": result
        })
        
        return result


class RiskAnalysisTool(BaseTool):
    """Tool for analyzing strategy risk"""
    
    def __init__(self):
        super().__init__(
            name="risk_analysis",
            description="Analyze risk parameters and metrics"
        )
    
    async def execute(
        self,
        backtest_results: Dict[str, Any],
        strategy_params: Dict[str, Any],
        risk_limits: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Analyze risk metrics
        
        Args:
            backtest_results: Results from backtest tool
            strategy_params: Strategy risk parameters
            risk_limits: Risk limits to check against
        """
        risk_limits = risk_limits or {
            "max_drawdown": 0.15,
            "max_daily_loss": 0.03,
            "min_sharpe": 0.8,
            "max_position_size": 0.05
        }
        
        issues = []
        
        # Check drawdown
        max_dd = backtest_results.get("max_drawdown", 0)
        if max_dd > risk_limits["max_drawdown"]:
            issues.append(f"Max drawdown {max_dd:.1%} exceeds limit {risk_limits['max_drawdown']:.1%}")
        
        # Check Sharpe
        sharpe = backtest_results.get("sharpe_ratio", 0)
        if sharpe < risk_limits["min_sharpe"]:
            issues.append(f"Sharpe ratio {sharpe:.2f} below minimum {risk_limits['min_sharpe']}")
        
        # Check position sizing
        pos_size = strategy_params.get("max_position_size", 0.02)
        if pos_size > risk_limits["max_position_size"]:
            issues.append(f"Position size {pos_size:.1%} exceeds limit {risk_limits['max_position_size']:.1%}")
        
        # Calculate additional risk metrics
        trades = backtest_results.get("trades", [])
        if trades:
            returns = [t["pnl_pct"] for t in trades]
            
            # VaR (simplified 95%)
            var_95 = sorted(returns)[int(len(returns) * 0.05)] if len(returns) >= 20 else -0.02
            
            # Calmar ratio
            calmar = backtest_results.get("total_return", 0) / max_dd if max_dd > 0 else 0
            
            # Sortino (simplified)
            downside_returns = [r for r in returns if r < 0]
            if downside_returns:
                downside_std = (sum(r**2 for r in downside_returns) / len(downside_returns))**0.5
                sortino = sum(returns) / len(returns) / downside_std if downside_std > 0 else 0
            else:
                sortino = float('inf')
        else:
            var_95 = -0.02
            calmar = 0
            sortino = 0
        
        return {
            "risk_score": 1.0 - (len(issues) * 0.2),
            "issues": issues,
            "var_95": var_95,
            "calmar_ratio": calmar,
            "sortino_ratio": sortino,
            "max_drawdown": max_dd,
            "sharpe_ratio": sharpe,
            "passes_limits": len(issues) == 0
        }


class KnowledgeBaseTool(BaseTool):
    """Tool for accessing strategy knowledge base"""
    
    def __init__(self):
        super().__init__(
            name="knowledge_base",
            description="Access strategy patterns, research, and historical knowledge"
        )
        self.knowledge = self._initialize_knowledge()
    
    def _initialize_knowledge(self) -> Dict[str, Any]:
        """Initialize knowledge base with trading principles"""
        return {
            "patterns": {
                "head_and_shoulders": {
                    "description": "Reversal pattern with three peaks",
                    "reliability": 0.65,
                    "best_timeframe": "4h"
                },
                "double_top": {
                    "description": "Bearish reversal with two similar highs",
                    "reliability": 0.70,
                    "best_timeframe": "1d"
                },
                "ascending_triangle": {
                    "description": "Bullish continuation pattern",
                    "reliability": 0.72,
                    "best_timeframe": "1h"
                }
            },
            "indicators": {
                "rsi": {
                    "description": "Relative Strength Index",
                    "optimal_period": 14,
                    "overbought": 70,
                    "oversold": 30
                },
                "macd": {
                    "description": "Moving Average Convergence Divergence",
                    "fast_period": 12,
                    "slow_period": 26,
                    "signal_period": 9
                },
                "bollinger_bands": {
                    "description": "Volatility bands",
                    "period": 20,
                    "std_dev": 2.0
                }
            },
            "risk_principles": [
                "Never risk more than 2% per trade",
                "Always use stop-losses",
                "Diversify across uncorrelated strategies",
                "Maintain positive risk-adjusted returns"
            ],
            "market_regimes": {
                "trending": ["momentum", "breakout"],
                "ranging": ["mean_reversion", "oscillator"],
                "volatile": ["volatility_breakout", "options"]
            }
        }
    
    async def execute(
        self,
        query_type: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Query knowledge base
        
        Args:
            query_type: Type of query (pattern, indicator, principle, regime)
            query: Search query
        """
        query_lower = query.lower()
        
        if query_type == "pattern":
            patterns = self.knowledge.get("patterns", {})
            results = {
                k: v for k, v in patterns.items()
                if query_lower in k or query_lower in v["description"].lower()
            }
            return {"results": results, "count": len(results)}
        
        elif query_type == "indicator":
            indicators = self.knowledge.get("indicators", {})
            results = {
                k: v for k, v in indicators.items()
                if query_lower in k or query_lower in v["description"].lower()
            }
            return {"results": results, "count": len(results)}
        
        elif query_type == "principle":
            principles = self.knowledge.get("risk_principles", [])
            results = [p for p in principles if query_lower in p.lower()]
            return {"results": results, "count": len(results)}
        
        elif query_type == "regime":
            regimes = self.knowledge.get("market_regimes", {})
            results = {
                k: v for k, v in regimes.items()
                if query_lower in k
            }
            return {"results": results, "count": len(results)}
        
        return {"results": {}, "count": 0}


class ToolIntegrationSystem:
    """
    Central system for managing and integrating all tools.
    
    Provides unified interface for the Aletheia system to access
    market data, backtesting, risk analysis, and knowledge base.
    """
    
    def __init__(self):
        self.tools: Dict[str, BaseTool] = {}
        self.tool_registry = {}
        self.execution_log = []
        
        # Initialize default tools
        self._initialize_default_tools()
        
        logger.info("ToolIntegrationSystem initialized")
    
    def _initialize_default_tools(self):
        """Initialize default set of tools"""
        tools = [
            MarketDataTool(),
            BacktestTool(),
            RiskAnalysisTool(),
            KnowledgeBaseTool()
        ]
        
        for tool in tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: BaseTool):
        """Register a new tool"""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
    
    async def invoke_tool(
        self,
        tool_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke a specific tool
        
        Args:
            tool_name: Name of the tool to invoke
            **kwargs: Parameters for the tool
            
        Returns:
            Tool execution result
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        result = await tool.invoke(**kwargs)
        
        # Log execution
        self.execution_log.append({
            "timestamp": datetime.now(),
            "tool": tool_name,
            "success": result.get("success", False)
        })
        
        return result
    
    async def invoke_multiple(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Invoke multiple tools in parallel
        
        Args:
            tool_calls: List of {"tool": str, "params": dict}
            
        Returns:
            List of tool results
        """
        tasks = [
            self.invoke_tool(call["tool"], **call.get("params", {}))
            for call in tool_calls
        ]
        
        return await asyncio.gather(*tasks)
    
    def get_tool_status(self) -> Dict[str, Any]:
        """Get status of all tools"""
        return {
            name: {
                "enabled": tool.enabled,
                "call_count": tool.call_count,
                "last_used": tool.last_used.isoformat() if tool.last_used else None,
                "description": tool.description
            }
            for name, tool in self.tools.items()
        }
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics"""
        if not self.execution_log:
            return {"total_calls": 0}
        
        total = len(self.execution_log)
        successful = sum(1 for log in self.execution_log if log["success"])
        
        # Count by tool
        tool_counts = {}
        for log in self.execution_log:
            tool = log["tool"]
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        return {
            "total_calls": total,
            "successful_calls": successful,
            "success_rate": successful / total,
            "calls_by_tool": tool_counts
        }
    
    def enable_tool(self, tool_name: str):
        """Enable a tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = True
            logger.info(f"Enabled tool: {tool_name}")
    
    def disable_tool(self, tool_name: str):
        """Disable a tool"""
        if tool_name in self.tools:
            self.tools[tool_name].enabled = False
            logger.info(f"Disabled tool: {tool_name}")
