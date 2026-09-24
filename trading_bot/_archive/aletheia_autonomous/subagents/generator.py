"""
Strategy Generator Subagent

Generates trading strategy hypotheses based on market context and research prompts.
Uses natural language reasoning to create explainable strategies.
"""

import logging
import random
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class StrategyGenerator:
    """
    Generates trading strategy hypotheses using natural language reasoning.
    
    Based on Aletheia's approach of generating solutions with clear rationales
    that can be verified and improved iteratively.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.generation_history: List[Dict] = []
        self.strategy_templates = self._load_strategy_templates()
        
    def _load_strategy_templates(self) -> Dict[str, Any]:
        """Load strategy generation templates"""
        return {
            "momentum": {
                "name": "Momentum Strategy",
                "description": "Trades in direction of established trend",
                "indicators": ["RSI", "MACD", "Moving Averages"],
                "timeframes": ["H1", "H4", "D1"]
            },
            "mean_reversion": {
                "name": "Mean Reversion Strategy",
                "description": "Trades against extreme price movements",
                "indicators": ["Bollinger Bands", "Z-Score", "Stochastic"],
                "timeframes": ["M15", "H1", "H4"]
            },
            "breakout": {
                "name": "Breakout Strategy",
                "description": "Trades price breakouts from consolidation",
                "indicators": ["ATR", "Volume", "Support/Resistance"],
                "timeframes": ["H1", "H4", "D1"]
            },
            "statistical_arbitrage": {
                "name": "Statistical Arbitrage",
                "description": "Exploits mean-reverting relationships",
                "indicators": ["Cointegration", "Z-Score", "Correlation"],
                "timeframes": ["M5", "M15", "H1"]
            },
            "sentiment": {
                "name": "Sentiment-Driven Strategy",
                "description": "Trades based on market sentiment analysis",
                "indicators": ["Fear/Greed Index", "News Sentiment", "Social Data"],
                "timeframes": ["M5", "M15", "H1"]
            }
        }
    
    async def generate(
        self,
        prompt: str,
        market_context: Optional[Dict[str, Any]] = None,
        constraints: Optional[Dict[str, Any]] = None
    ) -> 'StrategyHypothesis':
        """
        Generate a trading strategy hypothesis
        
        Args:
            prompt: Natural language description of desired strategy
            market_context: Current market conditions
            constraints: Risk and operational constraints
            
        Returns:
            StrategyHypothesis with complete strategy specification
        """
        from .aletheia_orchestrator import StrategyHypothesis
        
        logger.info(f"Generating strategy for: {prompt[:100]}...")
        
        # Analyze prompt to determine strategy type
        strategy_type = self._determine_strategy_type(prompt, market_context)
        
        # Generate strategy components
        title = self._generate_title(prompt, strategy_type)
        description = self._generate_description(strategy_type, market_context)
        rationale = self._generate_rationale(strategy_type, market_context)
        
        # Generate trading rules
        entry_rules = self._generate_entry_rules(strategy_type, market_context)
        exit_rules = self._generate_exit_rules(strategy_type)
        
        # Generate market conditions
        market_conditions = self._identify_market_conditions(strategy_type, market_context)
        
        # Generate risk parameters
        risk_parameters = self._generate_risk_parameters(strategy_type, constraints)
        
        # Generate expected performance
        expected_performance = self._estimate_performance(strategy_type, market_context)
        
        # Create hypothesis
        hypothesis = StrategyHypothesis(
            title=title,
            description=description,
            rationale=rationale,
            market_conditions=market_conditions,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            risk_parameters=risk_parameters,
            expected_performance=expected_performance,
            confidence_score=self._calculate_initial_confidence(strategy_type, market_context),
            generation_trace=[{
                "timestamp": datetime.now().isoformat(),
                "action": "initial_generation",
                "strategy_type": strategy_type,
                "prompt": prompt[:200]
            }]
        )
        
        self.generation_history.append({
            "hypothesis_id": hypothesis.hypothesis_id,
            "prompt": prompt,
            "strategy_type": strategy_type,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Generated hypothesis: {hypothesis.hypothesis_id}")
        return hypothesis
    
    def _determine_strategy_type(
        self, 
        prompt: str, 
        market_context: Optional[Dict[str, Any]]
    ) -> str:
        """Determine strategy type from prompt and context"""
        prompt_lower = prompt.lower()
        
        # Check for keywords in prompt
        if any(word in prompt_lower for word in ["momentum", "trend", "following"]):
            return "momentum"
        elif any(word in prompt_lower for word in ["mean reversion", "reverting", "bounce", "oversold", "overbought"]):
            return "mean_reversion"
        elif any(word in prompt_lower for word in ["breakout", "break", "consolidation", "range"]):
            return "breakout"
        elif any(word in prompt_lower for word in ["arbitrage", "pairs", "correlation", "cointegration"]):
            return "statistical_arbitrage"
        elif any(word in prompt_lower for word in ["sentiment", "news", "social", "fear", "greed"]):
            return "sentiment"
        
        # Use market context if available
        if market_context:
            volatility = market_context.get("volatility", "medium")
            trend = market_context.get("trend", "neutral")
            
            if trend == "strong_up" or trend == "strong_down":
                return "momentum"
            elif volatility == "high":
                return "breakout"
            elif volatility == "low":
                return "mean_reversion"
        
        # Default to momentum
        return "momentum"
    
    def _generate_title(self, prompt: str, strategy_type: str) -> str:
        """Generate strategy title"""
        template = self.strategy_templates.get(strategy_type, {})
        base_name = template.get("name", "Trading Strategy")
        
        # Add unique identifier based on prompt keywords
        keywords = [word for word in prompt.split() if len(word) > 4]
        if keywords:
            keyword = random.choice(keywords[:5])
            return f"{base_name} - {keyword.title()} Focus"
        
        return f"{base_name} - Auto Generated"
    
    def _generate_description(self, strategy_type: str, market_context: Optional[Dict]) -> str:
        """Generate strategy description"""
        template = self.strategy_templates.get(strategy_type, {})
        base_desc = template.get("description", "Automated trading strategy")
        
        context_info = ""
        if market_context:
            regime = market_context.get("regime", "mixed")
            context_info = f" Optimized for {regime} market conditions."
        
        return f"{base_desc}.{context_info} Generated using natural language reasoning and market analysis."
    
    def _generate_rationale(self, strategy_type: str, market_context: Optional[Dict]) -> str:
        """Generate strategy rationale"""
        rationales = {
            "momentum": "Markets exhibit trending behavior due to herd mentality and information diffusion. This strategy capitalizes on established trends with confirmation indicators.",
            "mean_reversion": "Prices tend to revert to mean after extreme movements due to profit-taking and value-based buying. This strategy identifies oversold/overbought conditions.",
            "breakout": "Consolidation periods often lead to strong directional moves when key levels break. This strategy identifies high-probability breakout setups.",
            "statistical_arbitrage": "Related assets maintain long-term equilibrium relationships. This strategy exploits temporary deviations with mean-reversion expectation.",
            "sentiment": "Market sentiment drives short-term price movements. This strategy uses sentiment indicators to anticipate crowd behavior shifts."
        }
        
        base_rationale = rationales.get(strategy_type, "Strategy based on technical analysis principles.")
        
        if market_context:
            conditions = market_context.get("conditions", [])
            if conditions:
                base_rationale += f" Current conditions: {', '.join(conditions)}."
        
        return base_rationale
    
    def _generate_entry_rules(self, strategy_type: str, market_context: Optional[Dict]) -> List[str]:
        """Generate entry rules"""
        rules = {
            "momentum": [
                "Price above 20-period EMA for longs, below for shorts",
                "RSI(14) between 50-70 for longs, 30-50 for shorts",
                "MACD histogram positive for longs, negative for shorts",
                "Volume above 20-period average"
            ],
            "mean_reversion": [
                "Price touches lower Bollinger Band (2 std dev) for longs",
                "Stochastic < 20 and rising for longs, > 80 and falling for shorts",
                "RSI below 30 for longs, above 70 for shorts",
                "Price extends >2 ATR from mean"
            ],
            "breakout": [
                "Price breaks above 20-period high for longs, below low for shorts",
                "Volume spikes >150% of average on breakout candle",
                "ATR expanding confirming volatility increase",
                "Consolidation pattern identified (5+ periods range-bound)"
            ],
            "statistical_arbitrage": [
                "Z-score of spread exceeds +/- 2.0",
                "Correlation > 0.8 over 50-period lookback",
                "Cointegration test p-value < 0.05",
                "Half-life of mean reversion < 10 periods"
            ],
            "sentiment": [
                "Fear/Greed Index < 25 for longs, > 75 for shorts",
                "News sentiment score > 0.6 for longs, < 0.4 for shorts",
                "Social media momentum positive for longs, negative for shorts",
                "Contrarian indicator at extreme readings"
            ]
        }
        
        return rules.get(strategy_type, ["Technical indicator confirmation required"])
    
    def _generate_exit_rules(self, strategy_type: str) -> List[str]:
        """Generate exit rules"""
        return [
            "Stop-loss at 2x ATR from entry",
            "Take-profit at 3:1 reward-to-risk ratio",
            "Trailing stop at 1.5x ATR once 1R profit reached",
            "Time exit if position held >5 days without hitting targets",
            "Reversal signal from entry indicators"
        ]
    
    def _identify_market_conditions(
        self, 
        strategy_type: str, 
        market_context: Optional[Dict]
    ) -> List[str]:
        """Identify required market conditions"""
        conditions = {
            "momentum": ["Trending market", "Clear direction", "Sufficient volatility"],
            "mean_reversion": ["Range-bound market", "Mean-reverting behavior", "Low volatility"],
            "breakout": ["Consolidation phase", "Decreasing volatility", "Defined support/resistance"],
            "statistical_arbitrage": ["Correlated assets", "Cointegrated relationship", "Stationary spread"],
            "sentiment": ["High retail participation", "News-driven moves", "Social media activity"]
        }
        
        base_conditions = conditions.get(strategy_type, ["Favorable market conditions"])
        
        if market_context:
            regime = market_context.get("regime")
            if regime:
                base_conditions.append(f"{regime} regime active")
        
        return base_conditions
    
    def _generate_risk_parameters(
        self, 
        strategy_type: str, 
        constraints: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate risk parameters"""
        default_params = {
            "max_position_size": 2.0,  # % of portfolio
            "max_daily_loss": 3.0,  # % of portfolio
            "max_drawdown": 10.0,  # % of portfolio
            "max_correlation": 0.7,  # with existing positions
            "min_liquidity": 1000000,  # daily volume
        }
        
        # Apply constraints if provided
        if constraints:
            max_risk = constraints.get("max_risk_per_trade", 2.0)
            default_params["max_position_size"] = min(default_params["max_position_size"], max_risk)
            
            max_daily = constraints.get("max_daily_loss", 3.0)
            default_params["max_daily_loss"] = min(default_params["max_daily_loss"], max_daily)
        
        # Strategy-specific adjustments
        if strategy_type == "statistical_arbitrage":
            default_params["max_position_size"] *= 1.5  # Lower risk per trade
        elif strategy_type == "breakout":
            default_params["max_position_size"] *= 0.8  # Higher risk but smaller size
        
        return default_params
    
    def _estimate_performance(
        self, 
        strategy_type: str, 
        market_context: Optional[Dict]
    ) -> Dict[str, Any]:
        """Estimate expected performance"""
        base_expectations = {
            "momentum": {"win_rate": 0.55, "profit_factor": 1.8, "sharpe": 1.2},
            "mean_reversion": {"win_rate": 0.60, "profit_factor": 1.5, "sharpe": 1.0},
            "breakout": {"win_rate": 0.45, "profit_factor": 2.2, "sharpe": 1.4},
            "statistical_arbitrage": {"win_rate": 0.65, "profit_factor": 1.4, "sharpe": 1.8},
            "sentiment": {"win_rate": 0.52, "profit_factor": 1.6, "sharpe": 0.9}
        }
        
        expectations = base_expectations.get(strategy_type, {"win_rate": 0.50, "profit_factor": 1.5, "sharpe": 1.0})
        
        # Adjust based on market context
        if market_context:
            volatility = market_context.get("volatility", "medium")
            if volatility == "high":
                expectations["profit_factor"] *= 1.2
                expectations["win_rate"] *= 0.95
        
        return {
            "expected_win_rate": expectations["win_rate"],
            "expected_profit_factor": expectations["profit_factor"],
            "expected_sharpe_ratio": expectations["sharpe"],
            "expected_trades_per_month": 8 if strategy_type != "statistical_arbitrage" else 15,
            "expected_max_drawdown": 8.0
        }
    
    def _calculate_initial_confidence(
        self, 
        strategy_type: str, 
        market_context: Optional[Dict]
    ) -> float:
        """Calculate initial confidence score"""
        base_confidence = 0.75
        
        # Adjust based on strategy type historical performance
        confidence_adjustments = {
            "momentum": 0.05,
            "mean_reversion": 0.03,
            "breakout": 0.02,
            "statistical_arbitrage": 0.08,
            "sentiment": -0.05
        }
        
        base_confidence += confidence_adjustments.get(strategy_type, 0)
        
        # Adjust based on market context quality
        if market_context and market_context.get("data_quality") == "high":
            base_confidence += 0.05
        
        return min(0.90, max(0.60, base_confidence))
