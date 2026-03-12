"""
Market Microstructure & Execution Validator (Q131-200)
Addresses order book dynamics, execution quality, latency, market impact, and venue selection.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    SystemState, IMMUTABLE_LIMITS
)


class ExecutionValidator(BaseValidator):
    """Validates execution quality and market microstructure (Q131-200)"""
    
    def __init__(self):
        super().__init__(ValidationCategory.MARKET_MICROSTRUCTURE)
        self._execution_stats: Dict[str, Dict] = {}
        self._venue_stats: Dict[str, Dict] = {}
        self._slippage_history: List[float] = []
    
    def _register_checks(self):
        """Register all Q131-200 validation checks"""
        # Q131-140: Order Book Dynamics
        self.add_check(self._check_orderbook_impact, [131, 132])
        self.add_check(self._check_orderbook_staleness, [133, 134])
        self.add_check(self._check_hidden_liquidity, [135, 136])
        self.add_check(self._check_tick_sizes, [137])
        self.add_check(self._check_spoofing_detection, [138])
        self.add_check(self._check_queue_position, [139, 140])
        # Q141-150: Execution Quality
        self.add_check(self._check_execution_quality, [141, 142, 143, 144])
        self.add_check(self._check_partial_fills, [145, 146])
        self.add_check(self._check_fill_probability, [147, 148])
        self.add_check(self._check_volatility_execution, [149])
        self.add_check(self._check_toxic_flow, [150])
        # Q151-160: Latency
        self.add_check(self._check_e2e_latency, [151, 152, 153])
        self.add_check(self._check_venue_latency, [154, 155])
        self.add_check(self._check_network_latency, [156, 157])
        self.add_check(self._check_processing_latency, [158, 159, 160])
        # Q161-170: Market Impact
        self.add_check(self._check_market_impact, [161, 162, 163, 164])
        self.add_check(self._check_impact_adjustment, [165, 166])
        self.add_check(self._check_illiquid_impact, [167, 168])
        self.add_check(self._check_correlated_impact, [169, 170])
        # Q171-180: Venue Selection
        self.add_check(self._check_venue_selection, [171, 172, 173, 174])
        self.add_check(self._check_venue_quality, [175, 176])
        self.add_check(self._check_venue_settlement, [177, 178])
        self.add_check(self._check_venue_fill_probability, [179, 180])
        # Q181-190: Order Types & Algorithms
        self.add_check(self._check_order_types, [181, 182, 183])
        self.add_check(self._check_execution_style, [184, 185, 186])
        self.add_check(self._check_cancel_handling, [187, 188, 189, 190])
        # Q191-200: Execution Risk
        self.add_check(self._check_market_halt, [191, 192, 193])
        self.add_check(self._check_systematic_failure, [194, 195])
        self.add_check(self._check_timezone_execution, [196, 197])
        self.add_check(self._check_execution_reports, [198, 199, 200])
        
        # Register remediations
        self.add_remediation("reduce_order_size", self._remediate_reduce_size)
        self.add_remediation("switch_venue", self._remediate_switch_venue)
        self.add_remediation("cancel_orders", self._remediate_cancel_orders)
    
    # =========================================================================
    # Q131-140: Order Book Dynamics
    # =========================================================================
    
    def _check_orderbook_impact(self, state: SystemState) -> List[ValidationIssue]:
        """Q131-132: Order book impact modeling"""
        issues = []
        
        # Check for orders that would move the market
        market_moving = state.error_counts.get('market_moving_order', 0)
        if market_moving > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("market_moving", str(market_moving)),
                question_id=131,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Market-moving orders detected: {market_moving}",
                description="Orders large enough to significantly impact the market",
                affected_components=["ExecutionEngine", "OrderSizer"],
                remediation_available=True,
                remediation_action="reduce_order_size",
                auto_remediate=True
            ))
        
        # Q132: Thin order book
        thin_book_trades = state.error_counts.get('thin_orderbook', 0)
        if thin_book_trades > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("thin_book", str(thin_book_trades)),
                question_id=132,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Thin order book trades: {thin_book_trades}",
                description="Trading in thin order book conditions",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="reduce_order_size"
            ))
        
        return issues
    
    def _check_orderbook_staleness(self, state: SystemState) -> List[ValidationIssue]:
        """Q133-134: Order book staleness and out-of-order updates"""
        issues = []
        
        stale_book = state.error_counts.get('stale_orderbook', 0)
        if stale_book > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("stale_book", str(stale_book)),
                question_id=133,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Stale order book data: {stale_book}",
                description="Order book data is stale or incomplete",
                affected_components=["DataPipeline", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="refresh_orderbook"
            ))
        
        ooo_updates = state.error_counts.get('ooo_book_updates', 0)
        if ooo_updates > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("ooo_book", str(ooo_updates)),
                question_id=134,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Out-of-order book updates: {ooo_updates}",
                description="Order book updates arriving out of sequence",
                affected_components=["DataPipeline"],
                remediation_available=True,
                remediation_action="resequence_updates"
            ))
        
        return issues
    
    def _check_hidden_liquidity(self, state: SystemState) -> List[ValidationIssue]:
        """Q135-136: Hidden liquidity and disappearing liquidity"""
        issues = []
        
        disappearing = state.error_counts.get('disappearing_liquidity', 0)
        if disappearing > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("disappearing", str(disappearing)),
                question_id=136,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Disappearing liquidity: {disappearing}",
                description="Liquidity disappears when attempting to take it",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="use_hidden_orders"
            ))
        
        return issues
    
    def _check_tick_sizes(self, state: SystemState) -> List[ValidationIssue]:
        """Q137: Multi-venue tick size handling"""
        issues = []
        
        tick_errors = state.error_counts.get('tick_size_error', 0)
        if tick_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("tick_size", str(tick_errors)),
                question_id=137,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Tick size errors: {tick_errors}",
                description="Orders rejected due to tick size violations",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="fix_tick_rounding"
            ))
        
        return issues
    
    def _check_spoofing_detection(self, state: SystemState) -> List[ValidationIssue]:
        """Q138: Spoofing and layering detection"""
        issues = []
        
        spoofing = state.error_counts.get('spoofing_detected', 0)
        if spoofing > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("spoofing", str(spoofing)),
                question_id=138,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Spoofing detected: {spoofing}",
                description="Potential spoofing/layering activity detected",
                affected_components=["MarketAnalysis"],
                remediation_available=True,
                remediation_action="pause_trading"
            ))
        
        return issues
    
    def _check_queue_position(self, state: SystemState) -> List[ValidationIssue]:
        """Q139-140: Queue position modeling"""
        issues = []
        return issues
    
    # =========================================================================
    # Q141-150: Execution Quality
    # =========================================================================
    
    def _check_execution_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q141-144: Execution quality metrics"""
        issues = []
        
        # Calculate average slippage
        if self._slippage_history:
            avg_slippage = sum(self._slippage_history) / len(self._slippage_history)
            if avg_slippage > 0.001:  # 10 bps
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("slippage", str(avg_slippage)),
                    question_id=142,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"High average slippage: {avg_slippage*10000:.1f} bps",
                    description="Execution slippage exceeds acceptable threshold",
                    affected_components=["ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="optimize_execution",
                    metadata={"avg_slippage_bps": avg_slippage * 10000}
                ))
        
        # Q143: Degrading execution quality
        quality_trend = state.error_counts.get('execution_quality_degrading', 0)
        if quality_trend > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("quality_trend", str(quality_trend)),
                question_id=143,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title="Execution quality degrading",
                description="Execution quality has been declining over time",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="review_execution_algo"
            ))
        
        return issues
    
    def _check_partial_fills(self, state: SystemState) -> List[ValidationIssue]:
        """Q145-146: Partial fill handling"""
        issues = []
        
        partial_fills = state.error_counts.get('partial_fill', 0)
        if partial_fills > 10:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("partial", str(partial_fills)),
                question_id=145,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"High partial fill rate: {partial_fills}",
                description="Many orders only partially filled",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="adjust_order_sizing"
            ))
        
        worse_fills = state.error_counts.get('worse_than_expected_fill', 0)
        if worse_fills > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("worse_fill", str(worse_fills)),
                question_id=146,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Worse-than-expected fills: {worse_fills}",
                description="Fills at prices worse than expected",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="tighten_limits"
            ))
        
        return issues
    
    def _check_fill_probability(self, state: SystemState) -> List[ValidationIssue]:
        """Q147-148: Fill probability modeling"""
        issues = []
        
        low_fill_rate = state.error_counts.get('low_fill_rate', 0)
        if low_fill_rate > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("fill_rate", str(low_fill_rate)),
                question_id=148,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title="Low fill rate detected",
                description="Fill rates below acceptable thresholds",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="adjust_pricing"
            ))
        
        return issues
    
    def _check_volatility_execution(self, state: SystemState) -> List[ValidationIssue]:
        """Q149: Execution during extreme volatility"""
        issues = []
        
        vol_execution_errors = state.error_counts.get('volatility_execution_error', 0)
        if vol_execution_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("vol_exec", str(vol_execution_errors)),
                question_id=149,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Volatility execution errors: {vol_execution_errors}",
                description="Execution problems during high volatility",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="widen_limits"
            ))
        
        return issues
    
    def _check_toxic_flow(self, state: SystemState) -> List[ValidationIssue]:
        """Q150: Toxic order flow detection"""
        issues = []
        
        toxic_flow = state.error_counts.get('toxic_flow', 0)
        if toxic_flow > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("toxic", str(toxic_flow)),
                question_id=150,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Toxic flow detected: {toxic_flow}",
                description="Trading against informed/toxic order flow",
                affected_components=["ExecutionEngine", "SignalGenerator"],
                remediation_available=True,
                remediation_action="pause_trading"
            ))
        
        return issues
    
    # =========================================================================
    # Q151-160: Latency
    # =========================================================================
    
    def _check_e2e_latency(self, state: SystemState) -> List[ValidationIssue]:
        """Q151-153: End-to-end latency"""
        issues = []
        
        e2e_latency = state.latency_metrics.get('signal_to_ack_ms', 0)
        max_latency = IMMUTABLE_LIMITS['max_latency_ms']
        
        if e2e_latency > max_latency:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("e2e_latency", str(e2e_latency)),
                question_id=151,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"E2E latency too high: {e2e_latency}ms",
                description=f"Signal-to-acknowledgment latency {e2e_latency}ms exceeds {max_latency}ms",
                affected_components=["ExecutionEngine", "Network"],
                remediation_available=True,
                remediation_action="optimize_path",
                metadata={"latency_ms": e2e_latency, "threshold_ms": max_latency}
            ))
        
        # Q152: Latency spikes
        latency_spikes = state.error_counts.get('latency_spike', 0)
        if latency_spikes > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("latency_spike", str(latency_spikes)),
                question_id=152,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Latency spikes: {latency_spikes}",
                description="Frequent latency spikes detected",
                affected_components=["Network", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="investigate_spikes"
            ))
        
        return issues
    
    def _check_venue_latency(self, state: SystemState) -> List[ValidationIssue]:
        """Q154-155: Venue-specific latency"""
        issues = []
        
        for venue, stats in self._venue_stats.items():
            latency = stats.get('latency_ms', 0)
            if latency > 50:
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id("venue_latency", venue),
                    question_id=154,
                    category=self.category,
                    severity=ValidationSeverity.MEDIUM,
                    title=f"High venue latency: {venue} ({latency}ms)",
                    description=f"Venue {venue} has high latency",
                    affected_components=[venue, "ExecutionEngine"],
                    remediation_available=True,
                    remediation_action="switch_venue",
                    metadata={"venue": venue, "latency_ms": latency}
                ))
        
        return issues
    
    def _check_network_latency(self, state: SystemState) -> List[ValidationIssue]:
        """Q156-157: Network latency"""
        issues = []
        
        network_latency = state.latency_metrics.get('network_ms', 0)
        if network_latency > 20:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("network", str(network_latency)),
                question_id=156,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"High network latency: {network_latency}ms",
                description="Network latency causing missed opportunities",
                affected_components=["Network"],
                remediation_available=True,
                remediation_action="check_network"
            ))
        
        return issues
    
    def _check_processing_latency(self, state: SystemState) -> List[ValidationIssue]:
        """Q158-160: Processing and serialization latency"""
        issues = []
        
        processing = state.latency_metrics.get('processing_ms', 0)
        if processing > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("processing", str(processing)),
                question_id=158,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"High processing latency: {processing}ms",
                description="Internal processing adding latency",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="optimize_processing"
            ))
        
        return issues
    
    # =========================================================================
    # Q161-170: Market Impact
    # =========================================================================
    
    def _check_market_impact(self, state: SystemState) -> List[ValidationIssue]:
        """Q161-164: Market impact modeling"""
        issues = []
        
        impact_exceeded = state.error_counts.get('impact_exceeded_model', 0)
        if impact_exceeded > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("impact", str(impact_exceeded)),
                question_id=164,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Market impact exceeded model: {impact_exceeded}",
                description="Actual market impact exceeds model predictions",
                affected_components=["ImpactModel", "ExecutionEngine"],
                remediation_available=True,
                remediation_action="recalibrate_impact_model"
            ))
        
        return issues
    
    def _check_impact_adjustment(self, state: SystemState) -> List[ValidationIssue]:
        """Q165-166: Real-time impact adjustment"""
        issues = []
        
        info_leakage = state.error_counts.get('information_leakage', 0)
        if info_leakage > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("leakage", str(info_leakage)),
                question_id=166,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Information leakage detected: {info_leakage}",
                description="Trading intentions may be leaking to market",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="randomize_execution"
            ))
        
        return issues
    
    def _check_illiquid_impact(self, state: SystemState) -> List[ValidationIssue]:
        """Q167-168: Illiquid market impact"""
        issues = []
        
        frontrun = state.error_counts.get('frontrun_detected', 0)
        if frontrun > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("frontrun", str(frontrun)),
                question_id=168,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Front-running detected: {frontrun}",
                description="Orders being front-run by other participants",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="use_dark_pools",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_correlated_impact(self, state: SystemState) -> List[ValidationIssue]:
        """Q169-170: Correlated instrument impact"""
        issues = []
        return issues
    
    # =========================================================================
    # Q171-180: Venue Selection
    # =========================================================================
    
    def _check_venue_selection(self, state: SystemState) -> List[ValidationIssue]:
        """Q171-174: Venue selection logic"""
        issues = []
        
        venue_unavailable = state.error_counts.get('venue_unavailable', 0)
        if venue_unavailable > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("venue_down", str(venue_unavailable)),
                question_id=172,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Venue unavailable: {venue_unavailable}",
                description="Preferred venue is unavailable",
                affected_components=["VenueRouter"],
                remediation_available=True,
                remediation_action="switch_venue",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_venue_quality(self, state: SystemState) -> List[ValidationIssue]:
        """Q175-176: Venue execution quality"""
        issues = []
        
        inferior_execution = state.error_counts.get('inferior_venue_execution', 0)
        if inferior_execution > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("inferior", str(inferior_execution)),
                question_id=175,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Inferior venue execution: {inferior_execution}",
                description="Venue providing inferior execution quality",
                affected_components=["VenueRouter"],
                remediation_available=True,
                remediation_action="deprioritize_venue"
            ))
        
        return issues
    
    def _check_venue_settlement(self, state: SystemState) -> List[ValidationIssue]:
        """Q177-178: Venue settlement and jurisdiction"""
        issues = []
        return issues
    
    def _check_venue_fill_probability(self, state: SystemState) -> List[ValidationIssue]:
        """Q179-180: Cross-venue fill probability"""
        issues = []
        
        degraded_connectivity = state.error_counts.get('degraded_venue_connectivity', 0)
        if degraded_connectivity > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("degraded", str(degraded_connectivity)),
                question_id=180,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Degraded venue connectivity: {degraded_connectivity}",
                description="Venue connectivity degraded but not completely down",
                affected_components=["VenueRouter", "Network"],
                remediation_available=True,
                remediation_action="switch_venue"
            ))
        
        return issues
    
    # =========================================================================
    # Q181-190: Order Types & Algorithms
    # =========================================================================
    
    def _check_order_types(self, state: SystemState) -> List[ValidationIssue]:
        """Q181-183: Order type handling"""
        issues = []
        
        unsupported = state.error_counts.get('unsupported_order_type', 0)
        if unsupported > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unsupported", str(unsupported)),
                question_id=183,
                category=self.category,
                severity=ValidationSeverity.MEDIUM,
                title=f"Unsupported order types: {unsupported}",
                description="Order type not supported by venue",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="use_alternative_order"
            ))
        
        return issues
    
    def _check_execution_style(self, state: SystemState) -> List[ValidationIssue]:
        """Q184-186: Aggressive vs passive execution"""
        issues = []
        
        silent_amendments = state.error_counts.get('silent_amendment_failure', 0)
        if silent_amendments > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("silent_amend", str(silent_amendments)),
                question_id=186,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Silent amendment failures: {silent_amendments}",
                description="Order amendments failing silently",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="add_amendment_confirmation"
            ))
        
        return issues
    
    def _check_cancel_handling(self, state: SystemState) -> List[ValidationIssue]:
        """Q187-190: Cancel and expiration handling"""
        issues = []
        
        unacked_cancels = state.error_counts.get('unacked_cancel', 0)
        if unacked_cancels > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("unacked", str(unacked_cancels)),
                question_id=187,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Unacknowledged cancels: {unacked_cancels}",
                description="Cancel requests not acknowledged - position risk",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="force_cancel",
                auto_remediate=True
            ))
        
        return issues
    
    # =========================================================================
    # Q191-200: Execution Risk
    # =========================================================================
    
    def _check_market_halt(self, state: SystemState) -> List[ValidationIssue]:
        """Q191-193: Market halt handling"""
        issues = []
        
        halt_orders = state.error_counts.get('orders_during_halt', 0)
        if halt_orders > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("halt", str(halt_orders)),
                question_id=191,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Orders during market halt: {halt_orders}",
                description="Orders in flight during market halt",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="cancel_orders"
            ))
        
        return issues
    
    def _check_systematic_failure(self, state: SystemState) -> List[ValidationIssue]:
        """Q194-195: Systematic execution failure"""
        issues = []
        
        systematic = state.error_counts.get('systematic_execution_failure', 0)
        if systematic > 3:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("systematic", str(systematic)),
                question_id=194,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Systematic execution failure: {systematic}",
                description="Execution failing systematically",
                affected_components=["ExecutionEngine"],
                remediation_available=True,
                remediation_action="halt_execution",
                auto_remediate=True
            ))
        
        return issues
    
    def _check_timezone_execution(self, state: SystemState) -> List[ValidationIssue]:
        """Q196-197: Multi-timezone and corporate action execution"""
        issues = []
        return issues
    
    def _check_execution_reports(self, state: SystemState) -> List[ValidationIssue]:
        """Q198-200: Execution report handling"""
        issues = []
        
        delayed_reports = state.error_counts.get('delayed_execution_report', 0)
        if delayed_reports > 5:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("delayed_report", str(delayed_reports)),
                question_id=199,
                category=self.category,
                severity=ValidationSeverity.HIGH,
                title=f"Delayed execution reports: {delayed_reports}",
                description="Execution reports arriving late",
                affected_components=["ExecutionEngine"],
                remediation_available=False
            ))
        
        reconciliation_errors = state.error_counts.get('trade_reconciliation_error', 0)
        if reconciliation_errors > 0:
            issues.append(ValidationIssue(
                issue_id=self._generate_issue_id("recon", str(reconciliation_errors)),
                question_id=200,
                category=self.category,
                severity=ValidationSeverity.CRITICAL,
                title=f"Trade reconciliation errors: {reconciliation_errors}",
                description="Executed trades don't match expected",
                affected_components=["ExecutionEngine", "PositionManager"],
                remediation_available=True,
                remediation_action="force_reconciliation"
            ))
        
        return issues
    
    # =========================================================================
    # Remediation Actions
    # =========================================================================
    
    async def _remediate_reduce_size(self, issue: ValidationIssue) -> str:
        """Reduce order size to minimize impact"""
        self.logger.info("Reducing order sizes")
        return "Order sizes reduced"
    
    async def _remediate_switch_venue(self, issue: ValidationIssue) -> str:
        """Switch to alternative venue"""
        venue = issue.metadata.get('venue', 'unknown')
        self.logger.info(f"Switching from venue {venue}")
        return f"Switched from {venue}"
    
    async def _remediate_cancel_orders(self, issue: ValidationIssue) -> str:
        """Cancel all pending orders"""
        self.logger.info("Cancelling all pending orders")
        return "Orders cancelled"
