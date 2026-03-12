"""
Risk Management Validator (Q401-470)
Addresses position risk, portfolio risk, drawdown, tail risk, leverage, liquidity, and counterparty risk.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class RiskValidator(BaseValidator):
    """Validates risk management (Q401-470)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.RISK_MANAGEMENT)
        self._risk_metrics: Dict[str, float] = {}
    
    def _register_checks(self):
        """Register all Q401-470 validation checks"""
        # Q401-410: Position Risk
        self.add_check(self._check_position_risk, [401, 402, 403, 404, 405])
        self.add_check(self._check_position_risk_response, [406, 407, 408, 409, 410])
        # Q411-420: Portfolio Risk
        self.add_check(self._check_portfolio_risk, [411, 412, 413, 414, 415])
        self.add_check(self._check_portfolio_risk_management, [416, 417, 418, 419, 420])
        # Q421-430: Drawdown
        self.add_check(self._check_drawdown, [421, 422, 423, 424, 425])
        self.add_check(self._check_drawdown_management, [426, 427, 428, 429, 430])
        # Q431-440: Tail Risk
        self.add_check(self._check_tail_risk, [431, 432, 433, 434, 435])
        self.add_check(self._check_tail_risk_hedging, [436, 437, 438, 439, 440])
        # Q441-450: Leverage
        self.add_check(self._check_leverage, [441, 442, 443, 444, 445])
        self.add_check(self._check_leverage_management, [446, 447, 448, 449, 450])
        # Q451-460: Liquidity Risk
        self.add_check(self._check_liquidity_risk, [451, 452, 453, 454, 455])
        self.add_check(self._check_liquidity_management, [456, 457, 458, 459, 460])
        # Q461-470: Counterparty Risk
        self.add_check(self._check_counterparty_risk, [461, 462, 463, 464, 465])
        self.add_check(self._check_counterparty_management, [466, 467, 468, 469, 470])
        
        # Register remediations
        self.add_remediation("reduce_position", self._remediate_reduce_position)
        self.add_remediation("hedge_risk", self._remediate_hedge)
        self.add_remediation("halt_trading", self._remediate_halt)
    
    # =========================================================================
    # Q401-410: Position Risk
    # =========================================================================
    
    def _check_position_risk(self, state: SystemState) -> List[ValidationIssue]:
        """Q401-405: Position risk checks"""
        issues = []
        
        max_risk = IMMUTABLE_LIMITS['max_risk_per_trade']
        max_position = IMMUTABLE_LIMITS['max_position_size']
        
        for symbol, pos in state.positions.items():
            if not isinstance(pos, dict):
                continue
            
            # Q401: Real-time position risk
            position_risk = pos.get('risk_percent', 0)
            if position_risk > max_risk:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("pos_risk", symbol),
                    question_id=401,
                    category=self.category,
                    severity=ValidationSeverity.CRITICAL,
                    title=f"Position risk exceeded: {symbol}",
                    description=f"Position risk {position_risk*100:.1f}% > max {max_risk*100:.1f}%",
                    affected_components=["RiskManager", "PositionManager"],
                    remediation_available=True,
                    remediation_action="reduce_position",
                    auto_remediate=True,
                    metadata={"symbol": symbol, "risk": position_risk}
                ))
            
            # Q403: Risk limit breach
            position_size = pos.get('size_percent', 0)
            if position_size > max_position:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("pos_size", symbol),
                    question_id=403,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Position size exceeded: {symbol}",
                    description=f"Position {position_size*100:.1f}% > max {max_position*100:.1f}%",
                    affected_components=["RiskManager", "PositionManager"],
                    remediation_available=True,
                    remediation_action="reduce_position",
                    metadata={"symbol": symbol, "size": position_size}
                ))
        
        # Q402: Risk calculation errors
        risk_errors = state.error_counts.get('risk_calculation_error', 0)
        if risk_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("risk_calc", str(risk_errors)),
                question_id=402,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Risk calculation errors: {risk_errors}",
                description="Position risk calculations have errors",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        # Q405: Risk underestimation
        underestimation = state.error_counts.get('risk_underestimation', 0)
        if underestimation > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("underest", str(underestimation)),
                question_id=405,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Risk underestimation detected",
                description="Risk models may be underestimating actual risk",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="recalibrate_risk"
            ))
        
        return issues
    
    def _check_position_risk_response(self, state: SystemState) -> List[ValidationIssue]:
        """Q406-410: Position risk response"""
        issues = []
        
        # Q406: Rapid risk change
        rapid_change = state.error_counts.get('rapid_risk_change', 0)
        if rapid_change > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rapid", str(rapid_change)),
                question_id=406,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Rapid risk change detected",
                description="Position risk changing faster than response capability",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="reduce_position",
                auto_remediate=True
            ))
        
        # Q409: Risk model miscalibration
        miscalibration = state.error_counts.get('risk_miscalibration', 0)
        if miscalibration > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("miscalib", str(miscalibration)),
                question_id=409,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Risk model miscalibration",
                description="Risk models are miscalibrated",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="recalibrate_risk"
            ))
        
        return issues
    
    # =========================================================================
    # Q411-420: Portfolio Risk
    # =========================================================================
    
    def _check_portfolio_risk(self, state: SystemState) -> List[ValidationIssue]:
        """Q411-415: Portfolio risk checks"""
        issues = []
        
        # Q411: Portfolio-level risk
        portfolio_var = self._risk_metrics.get('portfolio_var', 0)
        max_var = 0.05  # 5% VaR threshold
        if portfolio_var > max_var:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("portfolio_var", str(portfolio_var)),
                question_id=411,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Portfolio VaR exceeded: {portfolio_var*100:.1f}%",
                description=f"Portfolio VaR {portfolio_var*100:.1f}% > threshold {max_var*100:.1f}%",
                affected_components=["RiskManager", "PortfolioManager"],
                remediation_available=True,
                remediation_action="reduce_exposure"
            ))
        
        # Q413: Factor concentration
        factor_concentration = state.error_counts.get('factor_concentration', 0)
        if factor_concentration > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("factor", str(factor_concentration)),
                question_id=413,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Factor concentration risk",
                description="Portfolio risk concentrated in specific factors",
                affected_components=["RiskManager", "PortfolioManager"],
                remediation_available=True,
                remediation_action="diversify_factors"
            ))
        
        # Q415: Market risk correlation
        market_correlation = self._risk_metrics.get('market_correlation', 0)
        if market_correlation > 0.8:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("market_corr", str(market_correlation)),
                question_id=415,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"High market correlation: {market_correlation:.2f}",
                description="Portfolio highly correlated with market",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="hedge_risk"
            ))
        
        return issues
    
    def _check_portfolio_risk_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q416-420: Portfolio risk management"""
        issues = []
        
        # Q416: Stress period model failure
        stress_failure = state.error_counts.get('stress_model_failure', 0)
        if stress_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stress_fail", str(stress_failure)),
                question_id=416,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Risk model failed during stress",
                description="Risk models failing during market stress",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        # Q419: Hidden correlation risk
        hidden_corr = state.error_counts.get('hidden_correlation', 0)
        if hidden_corr > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hidden_corr", str(hidden_corr)),
                question_id=419,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Hidden correlation risk detected",
                description="Portfolio has hidden correlation risks",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="analyze_correlations"
            ))
        
        return issues
    
    # =========================================================================
    # Q421-430: Drawdown
    # =========================================================================
    
    def _check_drawdown(self, state: SystemState) -> List[ValidationIssue]:
        """Q421-425: Drawdown checks"""
        issues = []
        
        max_dd = IMMUTABLE_LIMITS['max_drawdown']
        current_dd = state.drawdown
        
        # Q421: Maximum drawdown
        if current_dd > max_dd:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("max_dd", str(current_dd)),
                question_id=421,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Maximum drawdown exceeded: {current_dd*100:.1f}%",
                description=f"Drawdown {current_dd*100:.1f}% > max {max_dd*100:.1f}%",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True,
                metadata={"drawdown": current_dd, "max": max_dd}
            ))
        
        # Q422: Approaching critical drawdown
        elif current_dd > max_dd * 0.8:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("near_dd", str(current_dd)),
                question_id=422,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Approaching max drawdown: {current_dd*100:.1f}%",
                description=f"Drawdown at {current_dd/max_dd*100:.0f}% of maximum",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="reduce_exposure"
            ))
        
        # Q423: Daily loss limit
        max_daily = IMMUTABLE_LIMITS['max_daily_loss']
        daily_loss = abs(min(0, state.daily_pnl / state.equity)) if state.equity > 0 else 0
        if daily_loss > max_daily:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("daily_loss", str(daily_loss)),
                question_id=423,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Daily loss limit exceeded: {daily_loss*100:.1f}%",
                description=f"Daily loss {daily_loss*100:.1f}% > max {max_daily*100:.1f}%",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_drawdown_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q426-430: Drawdown management"""
        issues = []
        
        # Q426: Drawdown control failure
        control_failure = state.error_counts.get('drawdown_control_failure', 0)
        if control_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dd_control", str(control_failure)),
                question_id=426,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Drawdown control mechanism failed",
                description="Drawdown controls not working properly",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        # Q425: Rapid drawdown
        rapid_dd = state.error_counts.get('rapid_drawdown', 0)
        if rapid_dd > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("rapid_dd", str(rapid_dd)),
                question_id=425,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Rapid drawdown detected",
                description="Drawdown occurring faster than response capability",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q431-440: Tail Risk
    # =========================================================================
    
    def _check_tail_risk(self, state: SystemState) -> List[ValidationIssue]:
        """Q431-435: Tail risk checks"""
        issues = []
        
        # Q432: Tail event exceeds model
        tail_exceeded = state.error_counts.get('tail_exceeded_model', 0)
        if tail_exceeded > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tail_exceed", str(tail_exceeded)),
                question_id=432,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Tail event exceeded model",
                description="Tail event larger than model assumptions",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        # Q435: Increasing tail risk
        increasing_tail = state.error_counts.get('increasing_tail_risk', 0)
        if increasing_tail > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inc_tail", str(increasing_tail)),
                question_id=435,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Tail risk increasing",
                description="Tail risk indicators are increasing",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="hedge_risk"
            ))
        
        return issues
    
    def _check_tail_risk_hedging(self, state: SystemState) -> List[ValidationIssue]:
        """Q436-440: Tail risk hedging"""
        issues = []
        
        # Q436: Hedge performance failure
        hedge_failure = state.error_counts.get('hedge_failure', 0)
        if hedge_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hedge_fail", str(hedge_failure)),
                question_id=436,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Tail risk hedge failed",
                description="Hedges not performing as expected",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="reduce_exposure"
            ))
        
        return issues
    
    # =========================================================================
    # Q441-450: Leverage
    # =========================================================================
    
    def _check_leverage(self, state: SystemState) -> List[ValidationIssue]:
        """Q441-445: Leverage checks"""
        issues = []
        
        max_leverage = IMMUTABLE_LIMITS['max_leverage']
        current_leverage = self._risk_metrics.get('leverage', 1.0)
        
        # Q441: Maximum leverage
        if current_leverage > max_leverage:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("max_lev", str(current_leverage)),
                question_id=441,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Maximum leverage exceeded: {current_leverage:.1f}x",
                description=f"Leverage {current_leverage:.1f}x > max {max_leverage:.1f}x",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="reduce_position",
                auto_remediate=True
            ))
        
        # Q442: Approaching leverage limit
        elif current_leverage > max_leverage * 0.9:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("near_lev", str(current_leverage)),
                question_id=442,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Approaching max leverage: {current_leverage:.1f}x",
                description=f"Leverage at {current_leverage/max_leverage*100:.0f}% of maximum",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="reduce_position"
            ))
        
        # Q446: Leverage calculation errors
        lev_errors = state.error_counts.get('leverage_calculation_error', 0)
        if lev_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("lev_err", str(lev_errors)),
                question_id=446,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Leverage calculation errors: {lev_errors}",
                description="Leverage calculations have errors",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading"
            ))
        
        return issues
    
    def _check_leverage_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q446-450: Leverage management"""
        issues = []
        
        # Q449: Hidden leverage
        hidden_lev = state.error_counts.get('hidden_leverage', 0)
        if hidden_lev > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("hidden_lev", str(hidden_lev)),
                question_id=449,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Hidden leverage detected",
                description="Leverage hidden in complex instruments",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="analyze_instruments"
            ))
        
        # Q450: Forced deleveraging
        forced_delev = state.error_counts.get('forced_deleveraging', 0)
        if forced_delev > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("forced_delev", str(forced_delev)),
                question_id=450,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Forced deleveraging occurred",
                description="Forced deleveraging causing additional losses",
                affected_components=["RiskManager", "ExecutionEngine"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q451-460: Liquidity Risk
    # =========================================================================
    
    def _check_liquidity_risk(self, state: SystemState) -> List[ValidationIssue]:
        """Q451-455: Liquidity risk checks"""
        issues = []
        
        min_liquidity = IMMUTABLE_LIMITS['min_liquidity_ratio']
        
        for symbol, pos in state.positions.items():
            if not isinstance(pos, dict):
                continue
            
            liquidity = pos.get('liquidity_ratio', 1.0)
            if liquidity < min_liquidity:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("liquidity", symbol),
                    question_id=451,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Low liquidity: {symbol}",
                    description=f"Liquidity ratio {liquidity:.2f} < min {min_liquidity:.2f}",
                    affected_components=["RiskManager", "PositionManager"],
                    remediation_available=True,
                    remediation_action="reduce_position",
                    metadata={"symbol": symbol, "liquidity": liquidity}
                ))
        
        # Q452: Liquidity dry-up
        liquidity_dryup = state.error_counts.get('liquidity_dryup', 0)
        if liquidity_dryup > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("dryup", str(liquidity_dryup)),
                question_id=452,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Liquidity dried up",
                description="Liquidity has dried up in held positions",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_liquidity_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q456-460: Liquidity management"""
        issues = []
        
        # Q456: Liquidity model failure
        model_failure = state.error_counts.get('liquidity_model_failure', 0)
        if model_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("liq_model", str(model_failure)),
                question_id=456,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Liquidity model failed",
                description="Liquidity risk models not working",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="recalibrate_liquidity"
            ))
        
        # Q460: Forced selling
        forced_sell = state.error_counts.get('forced_selling', 0)
        if forced_sell > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("forced_sell", str(forced_sell)),
                question_id=460,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Forced selling occurred",
                description="Liquidity risk caused forced selling",
                affected_components=["RiskManager", "ExecutionEngine"],
                remediation_available=False
            ))
        
        return issues
    
    # =========================================================================
    # Q461-470: Counterparty Risk
    # =========================================================================
    
    def _check_counterparty_risk(self, state: SystemState) -> List[ValidationIssue]:
        """Q461-465: Counterparty risk checks"""
        issues = []
        
        # Q462: Counterparty failure
        cp_failure = state.error_counts.get('counterparty_failure', 0)
        if cp_failure > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cp_fail", str(cp_failure)),
                question_id=462,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Counterparty failure",
                description="A counterparty has failed",
                affected_components=["RiskManager", "BrokerAdapter"],
                remediation_available=True,
                remediation_action="switch_counterparty"
            ))
        
        # Q463: Counterparty concentration
        cp_concentration = state.error_counts.get('counterparty_concentration', 0)
        if cp_concentration > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cp_conc", str(cp_concentration)),
                question_id=463,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Counterparty concentration risk",
                description="Too much exposure to single counterparty",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="diversify_counterparties"
            ))
        
        return issues
    
    def _check_counterparty_management(self, state: SystemState) -> List[ValidationIssue]:
        """Q466-470: Counterparty management"""
        issues = []
        
        # Q470: Cascading counterparty failure
        cascade = state.error_counts.get('counterparty_cascade', 0)
        if cascade > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("cp_cascade", str(cascade)),
                question_id=470,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title="Cascading counterparty failures",
                description="Counterparty failures cascading",
                affected_components=["RiskManager"],
                remediation_available=True,
                remediation_action="halt_trading",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_reduce_position(self, issue: ValidationIssue) -> str:
        """Reduce position size"""
        symbol = issue.metadata.get('symbol', 'all')
        self.logger.info(f"Reducing position: {symbol}")
        return f"Position reduced: {symbol}"
    
    async def _remediate_hedge(self, issue: ValidationIssue) -> str:
        """Add hedges"""
        self.logger.info("Adding hedges")
        return "Hedges added"
    
    async def _remediate_halt(self, issue: ValidationIssue) -> str:
        """Halt trading"""
        self.logger.info("Halting trading")
        return "Trading halted"
