"""
Migrated Planner Agent - Comprehensive Analysis
Refactored from trading_bot/agents/planner_agent.py for core_agent_system compatibility.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np

from ..agent_registry import BaseAgent, AgentRole, AgentCapability, AgentStatus

logger = logging.getLogger(__name__)

class MigratedPlannerAgent(BaseAgent):
    """
    Migrated Planner Agent that uses technical, fundamental, sentiment and forecast scores.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name=config.get("name", "MigratedPlannerAgent"),
            role=AgentRole.PLANNER,
            config=config
        )
        self.min_confidence = config.get("min_confidence", 0.6)
        self.min_risk_reward = config.get("min_risk_reward", 2.0)

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            name="comprehensive_planning",
            description="Analyze multiple data sources to propose trades",
            input_schema={"market_data": "Dict"},
            output_schema={"proposal": "Dict"}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        operation = action.get('operation', 'propose')

        if operation in ['propose', 'execute_task']:
            context = action.get('context', action.get('data', {}))
            market_data = context.get('market_state', context) if isinstance(context, dict) else {}

            # Analyze
            technical = self._analyze_technical(market_data)
            sentiment = market_data.get('news_sentiment', 0.5)
            forecast = self._analyze_forecast(market_data)

            confidence = np.mean([technical, sentiment, forecast])

            if confidence > self.min_confidence:
                trade_action = 'long'
            elif confidence < (1 - self.min_confidence):
                trade_action = 'short'
            else:
                trade_action = 'hold'

            return {
                'success': True,
                'type': trade_action,
                'action': {'operation': f'open_{trade_action}', 'size': 0.02},
                'confidence': float(confidence),
                'reasoning': f"Technical: {technical:.2f}, Sentiment: {sentiment:.2f}, Forecast: {forecast:.2f}",
                'metadata': {
                    'technical_score': float(technical),
                    'sentiment_score': float(sentiment),
                    'forecast_score': float(forecast)
                }
            }

        return {'success': False, 'error': f'Unknown operation: {operation}'}

    def _analyze_technical(self, data: Dict) -> float:
        score = 0.5
        rsi = data.get('rsi', 50)
        if rsi < 30: score += 0.2
        elif rsi > 70: score -= 0.2
        return np.clip(score, 0, 1)

    def _analyze_forecast(self, data: Dict) -> float:
        forecast = data.get('forecast', {})
        if not forecast: return 0.5
        median = forecast.get('median_prediction', 0)
        return np.clip(0.5 + median * 10, 0, 1)
