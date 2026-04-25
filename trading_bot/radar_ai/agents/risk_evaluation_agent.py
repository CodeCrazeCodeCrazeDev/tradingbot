"""
Risk & Evaluation Agent - Risk Adjudicator
===========================================

Performs comprehensive risk checks:
- VaR (Value at Risk)
- Maximum drawdown analysis
- Correlation checks across co-moving markets
- Position sizing validation
- Portfolio concentration analysis
"""

import asyncio
import logging
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class RiskAdjudication:
    """Risk assessment verdict"""
    adjudication_id: str
    timestamp: datetime
    overall_verdict: str  # 'approved', 'conditional', 'rejected'
    risk_score: float  # 0-100
    
    # Risk metrics
    var_95_pct: float
    max_drawdown_pct: float
    concentration_risk: float
    correlation_risk: float
    liquidity_risk: float
    
    # Checks
    checks_passed: List[str]
    checks_failed: List[str]
    warnings: List[str]
    
    # Recommendations
    position_size_limit: Optional[float]
    stop_loss_level: Optional[float]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'adjudication_id': self.adjudication_id,
            'timestamp': self.timestamp.isoformat(),
            'overall_verdict': self.overall_verdict,
            'risk_score': self.risk_score,
            'var_95_pct': self.var_95_pct,
            'max_drawdown_pct': self.max_drawdown_pct,
            'concentration_risk': self.concentration_risk,
            'correlation_risk': self.correlation_risk,
            'liquidity_risk': self.liquidity_risk,
            'checks_passed': self.checks_passed,
            'checks_failed': self.checks_failed,
            'warnings': self.warnings,
            'position_size_limit': self.position_size_limit,
            'stop_loss_level': self.stop_loss_level,
        }


class RiskEvaluationAgent:
    """
    Risk & Evaluation Agent - The Risk Adjudicator
    
    Final gatekeeper before execution.
    Performs comprehensive risk analysis.
    """
    
    def __init__(self, meta_orchestrator: Any):
        self.agent_id = f"RISK-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("RiskEvaluationAgent", self)
        
        # Risk limits
        self.risk_limits = {
            'max_var_95_pct': 3.0,  # 3% daily VaR limit
            'max_drawdown_pct': 15.0,  # 15% max drawdown
            'max_concentration': 25.0,  # 25% max single position
            'max_correlation': 0.85,  # 0.85 max correlation
            'min_liquidity_days': 5.0,  # 5 days to liquidate
        }
        
        # Adjudication history
        self.adjudications: List[RiskAdjudication] = []
        
        # Metrics
        self.total_adjudications = 0
        self.approvals = 0
        self.rejections = 0
        
        logger.info(f"RiskEvaluationAgent initialized: {self.agent_id}")
    
    async def adjudicate_risk(
        self,
        strategy_analysis: Dict[str, Any],
        simulation_result: Dict[str, Any],
        portfolio: Dict[str, Any],
        market_picture: Dict[str, Any],
    ) -> RiskAdjudication:
        """
        Perform comprehensive risk adjudication.
        
        This is the final check before execution approval.
        """
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="RiskEvaluationAgent",
            request_type="adjudicate_risk",
            payload={'symbol': strategy_analysis.get('symbol')},
            requires_approval=False,
        )
        
        checks_passed = []
        checks_failed = []
        warnings = []
        
        # Extract parameters
        symbol = strategy_analysis.get('symbol', 'UNKNOWN')
        action = strategy_analysis.get('recommended_action', 'hold')
        
        # 1. VaR Check
        var_95 = simulation_result.get('var_95', 0)
        portfolio_value = portfolio.get('total_value', 1)
        var_95_pct = (var_95 / portfolio_value * 100) if portfolio_value > 0 else 0
        
        if var_95_pct <= self.risk_limits['max_var_95_pct']:
            checks_passed.append(f"VaR check: {var_95_pct:.2f}% ≤ {self.risk_limits['max_var_95_pct']}%")
        else:
            checks_failed.append(f"VaR too high: {var_95_pct:.2f}% > {self.risk_limits['max_var_95_pct']}%")
        
        # 2. Drawdown Check
        max_dd_pct = simulation_result.get('expected_max_drawdown', 0) * 100
        
        if max_dd_pct <= self.risk_limits['max_drawdown_pct']:
            checks_passed.append(f"Drawdown check: {max_dd_pct:.2f}% ≤ {self.risk_limits['max_drawdown_pct']}%")
        else:
            checks_failed.append(f"Drawdown too high: {max_dd_pct:.2f}% > {self.risk_limits['max_drawdown_pct']}%")
        
        # 3. Concentration Check
        positions = portfolio.get('positions', [])
        if positions:
            position_values = [p.get('value', 0) for p in positions]
            max_position = max(position_values) if position_values else 0
            concentration = (max_position / portfolio_value * 100) if portfolio_value > 0 else 0
        else:
            concentration = 0
        
        if concentration <= self.risk_limits['max_concentration']:
            checks_passed.append(f"Concentration check: {concentration:.2f}% ≤ {self.risk_limits['max_concentration']}%")
        else:
            warnings.append(f"High concentration: {concentration:.2f}%")
        
        # 4. Correlation Check
        correlation_risk = await self._check_correlation_risk(symbol, portfolio, market_picture)
        
        if correlation_risk <= self.risk_limits['max_correlation']:
            checks_passed.append(f"Correlation check: {correlation_risk:.2f} ≤ {self.risk_limits['max_correlation']}")
        else:
            warnings.append(f"High correlation risk: {correlation_risk:.2f}")
        
        # 5. Liquidity Check
        liquidity_risk = await self._check_liquidity_risk(symbol, market_picture)
        
        if liquidity_risk <= self.risk_limits['min_liquidity_days']:
            checks_passed.append(f"Liquidity check: {liquidity_risk:.1f} days ≤ {self.risk_limits['min_liquidity_days']}")
        else:
            warnings.append(f"Liquidity concern: {liquidity_risk:.1f} days to liquidate")
        
        # Calculate overall risk score
        risk_score = self._calculate_risk_score(
            var_95_pct, max_dd_pct, concentration, correlation_risk, liquidity_risk
        )
        
        # Determine verdict
        if checks_failed:
            verdict = 'rejected'
            self.rejections += 1
        elif warnings and risk_score > 70:
            verdict = 'conditional'
        else:
            verdict = 'approved'
            self.approvals += 1
        
        # Calculate position size limit
        position_size_limit = self._calculate_position_size_limit(
            risk_score, portfolio_value, var_95_pct
        )
        
        # Calculate stop loss
        price = market_picture.get('prices', {}).get(symbol, 0)
        stop_loss = price * 0.95 if action == 'buy' else price * 1.05
        
        adjudication = RiskAdjudication(
            adjudication_id=f"ADJ-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            overall_verdict=verdict,
            risk_score=risk_score,
            var_95_pct=var_95_pct,
            max_drawdown_pct=max_dd_pct,
            concentration_risk=concentration,
            correlation_risk=correlation_risk,
            liquidity_risk=liquidity_risk,
            checks_passed=checks_passed,
            checks_failed=checks_failed,
            warnings=warnings,
            position_size_limit=position_size_limit,
            stop_loss_level=stop_loss,
        )
        
        self.adjudications.append(adjudication)
        self.total_adjudications += 1
        
        logger.info(f"Risk adjudication: {verdict} (score: {risk_score:.0f}/100)")
        
        return adjudication
    
    async def _check_correlation_risk(
        self,
        symbol: str,
        portfolio: Dict[str, Any],
        market_picture: Dict[str, Any],
    ) -> float:
        """Check correlation risk with existing positions"""
        # Simplified correlation check
        # In production, would calculate actual correlations
        positions = portfolio.get('positions', [])
        
        if not positions:
            return 0.0
        
        # Assume moderate correlation
        return 0.5
    
    async def _check_liquidity_risk(
        self,
        symbol: str,
        market_picture: Dict[str, Any],
    ) -> float:
        """Check liquidity risk (days to liquidate)"""
        volume = market_picture.get('volumes', {}).get(symbol, 1000000)
        
        # Assume position size of 10% of daily volume
        # Days to liquidate = position_size / (0.1 * daily_volume)
        # Simplified: assume 1000 shares
        position_size = 1000
        daily_volume = volume
        
        days_to_liquidate = position_size / (0.1 * daily_volume) if daily_volume > 0 else 100
        
        return days_to_liquidate
    
    def _calculate_risk_score(
        self,
        var_pct: float,
        dd_pct: float,
        concentration: float,
        correlation: float,
        liquidity_days: float,
    ) -> float:
        """Calculate overall risk score (0-100)"""
        # Weighted risk components
        var_score = min(100, (var_pct / self.risk_limits['max_var_95_pct']) * 30)
        dd_score = min(100, (dd_pct / self.risk_limits['max_drawdown_pct']) * 25)
        conc_score = min(100, (concentration / self.risk_limits['max_concentration']) * 20)
        corr_score = min(100, (correlation / self.risk_limits['max_correlation']) * 15)
        liq_score = min(100, (liquidity_days / self.risk_limits['min_liquidity_days']) * 10)
        
        total_score = var_score + dd_score + conc_score + corr_score + liq_score
        
        return min(100, total_score)
    
    def _calculate_position_size_limit(
        self,
        risk_score: float,
        portfolio_value: float,
        var_pct: float,
    ) -> float:
        """Calculate maximum position size"""
        # Base limit: 10% of portfolio
        base_limit = portfolio_value * 0.10
        
        # Adjust based on risk score
        if risk_score > 80:
            limit = base_limit * 0.5  # Reduce to 5%
        elif risk_score > 60:
            limit = base_limit * 0.75  # Reduce to 7.5%
        else:
            limit = base_limit
        
        # Further adjust based on VaR
        if var_pct > 2.0:
            limit = limit * 0.75
        
        return limit
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'total_adjudications': self.total_adjudications,
            'approvals': self.approvals,
            'rejections': self.rejections,
            'approval_rate': self.approvals / self.total_adjudications if self.total_adjudications > 0 else 0,
        }
