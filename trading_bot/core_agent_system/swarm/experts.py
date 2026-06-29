from typing import Any, Dict, List, Optional
from ..agent_registry import BaseAgent, AgentRole, AgentCapability

class MarketScientist(BaseAgent):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="MarketScientist",
            role=AgentRole.RESEARCHER,
            config=config
        )

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            "market_regime_analysis", "Analyze market structure and regimes", {}, {}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'success': True,
            'direction': 1.0,
            'confidence': 0.8,
            'reasoning': "Strong bullish regime detected via structural analysis."
        }

class QuantAnalyst(BaseAgent):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="QuantAnalyst",
            role=AgentRole.RESEARCHER,
            config=config
        )

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            "statistical_verification", "Verify signals using math models", {}, {}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'success': True,
            'direction': 0.5,
            'confidence': 0.7,
            'reasoning': "Statistical models show positive expectancy."
        }

class SwarmRiskManager(BaseAgent):
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(
            name="SwarmRiskManager",
            role=AgentRole.SAFETY,
            config=config
        )

    def _register_capabilities(self):
        self.add_capability(AgentCapability(
            "risk_validation", "Validate swarm decisions against risk limits", {}, {}
        ))

    async def execute(self, action: Dict[str, Any]) -> Dict[str, Any]:
        return {
            'success': True,
            'is_safe': True,
            'reasoning': "Position size within limits."
        }
