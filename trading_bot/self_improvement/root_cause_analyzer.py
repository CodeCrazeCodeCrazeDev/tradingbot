"""
Root Cause Analyzer
Automated diagnosis of why trades lost money.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
import numpy as np

from .triage import TriageDiagnostic, TradeData, SignalContext, MarketSnapshot, SystemMetrics
import numpy

logger = logging.getLogger(__name__)


class RootCauseType(Enum):
    """Types of root causes for losses."""
    SIGNAL_QUALITY = "signal_quality"
    EXECUTION_ISSUE = "execution_issue"
    RISK_SIZING = "risk_sizing"
    MARKET_EXTERNAL = "market_external"
    SOFTWARE_DATA = "software_data"
    UNKNOWN = "unknown"


@dataclass
class CheckResult:
    """Result of a single diagnostic check."""
    check_name: str
    passed: bool
    confidence: float
    metric_values: Dict[str, Any]
    evidence: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class RootCauseHypothesis:
    """A hypothesis for why the trade lost."""
    hypothesis_id: str
    cause_type: RootCauseType
    description: str
    confidence: float  # 0.0 to 1.0
    estimated_impact: float  # Estimated PnL impact
    evidence: List[CheckResult]
    suggested_fixes: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'hypothesis_id': self.hypothesis_id,
            'cause_type': self.cause_type.value,
            'description': self.description,
            'confidence': self.confidence,
            'estimated_impact': self.estimated_impact,
            'evidence': [e.to_dict() for e in self.evidence],
            'suggested_fixes': self.suggested_fixes
        }


class RootCauseAnalyzer:
    """
    Automated root cause analysis for losing trades.
    Runs comprehensive checks and generates ranked hypotheses.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize root cause analyzer.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config
        
            # Thresholds
            self.low_confidence_threshold = config.get('low_confidence_threshold', 0.5)
            self.high_slippage_threshold = config.get('high_slippage_threshold', 0.005)
            self.high_latency_threshold = config.get('high_latency_threshold', 1000)
            self.tight_sl_atr_ratio = config.get('tight_sl_atr_ratio', 1.5)
            self.volatility_spike_threshold = config.get('volatility_spike_threshold', 2.0)
        
            logger.info("RootCauseAnalyzer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def analyze(self, diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """
        Perform complete root cause analysis.
        
        Args:
            diagnostic: Triage diagnostic
            
        Returns:
            List of hypotheses ranked by confidence
        """
        try:
            logger.info(f"Starting root cause analysis for trade {diagnostic.trade_id}")
        
            # Run all checks
            signal_checks = self._check_signal_quality(diagnostic)
            execution_checks = self._check_execution_issues(diagnostic)
            risk_checks = self._check_risk_sizing(diagnostic)
            market_checks = self._check_market_external(diagnostic)
            software_checks = self._check_software_data(diagnostic)
        
            # Generate hypotheses from failed checks
            hypotheses = []
        
            hypotheses.extend(self._generate_signal_hypotheses(signal_checks, diagnostic))
            hypotheses.extend(self._generate_execution_hypotheses(execution_checks, diagnostic))
            hypotheses.extend(self._generate_risk_hypotheses(risk_checks, diagnostic))
            hypotheses.extend(self._generate_market_hypotheses(market_checks, diagnostic))
            hypotheses.extend(self._generate_software_hypotheses(software_checks, diagnostic))
        
            # Rank by confidence
            hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        
            # Take top 3
            top_hypotheses = hypotheses[:3]
        
            logger.info(f"Generated {len(top_hypotheses)} hypotheses for trade {diagnostic.trade_id}")
            for i, h in enumerate(top_hypotheses, 1):
                logger.info(f"  {i}. {h.description} (confidence: {h.confidence:.2f})")
        
            return top_hypotheses
        except Exception as e:
            logger.error(f"Error in analyze: {e}")
            raise
    
    def _check_signal_quality(self, diagnostic: TriageDiagnostic) -> List[CheckResult]:
        """Check A: Signal Quality checks."""
        try:
            checks = []
            signal = diagnostic.signal_context
        
            # A1: Low confidence
            low_conf = signal.model_confidence < self.low_confidence_threshold
            checks.append(CheckResult(
                check_name="signal_confidence",
                passed=not low_conf,
                confidence=0.8 if low_conf else 0.3,
                metric_values={'confidence': signal.model_confidence},
                evidence=f"Model confidence: {signal.model_confidence:.2f}",
                severity='high' if low_conf else 'low'
            ))
        
            # A2: Multi-timeframe disagreement
            mtf_disagree = not signal.multi_tf_agreement
            checks.append(CheckResult(
                check_name="multi_tf_agreement",
                passed=not mtf_disagree,
                confidence=0.75 if mtf_disagree else 0.2,
                metric_values={'agreement': signal.multi_tf_agreement},
                evidence=f"Multi-TF agreement: {signal.multi_tf_agreement}",
                severity='high' if mtf_disagree else 'low'
            ))
        
            # A3: Signal drift (post-entry vs pre-entry)
            high_drift = abs(signal.signal_drift) > 0.3
            checks.append(CheckResult(
                check_name="signal_drift",
                passed=not high_drift,
                confidence=0.7 if high_drift else 0.2,
                metric_values={'drift': signal.signal_drift},
                evidence=f"Signal drift: {signal.signal_drift:.2f}",
                severity='medium' if high_drift else 'low'
            ))
        
            return checks
        except Exception as e:
            logger.error(f"Error in _check_signal_quality: {e}")
            raise
    
    def _check_execution_issues(self, diagnostic: TriageDiagnostic) -> List[CheckResult]:
        """Check B: Execution issues."""
        try:
            checks = []
            trade = diagnostic.trade_data
            system = diagnostic.system_metrics
        
            # B1: High slippage
            high_slip = abs(trade.slippage) > self.high_slippage_threshold
            checks.append(CheckResult(
                check_name="slippage",
                passed=not high_slip,
                confidence=0.85 if high_slip else 0.2,
                metric_values={'slippage': trade.slippage, 'threshold': self.high_slippage_threshold},
                evidence=f"Slippage: {trade.slippage:.4f} ({trade.slippage*100:.2f}%)",
                severity='high' if high_slip else 'low'
            ))
        
            # B2: Partial fill or rejection
            partial_fill = system.order_fill_type != 'full'
            checks.append(CheckResult(
                check_name="order_fill",
                passed=not partial_fill,
                confidence=0.9 if partial_fill else 0.1,
                metric_values={'fill_type': system.order_fill_type},
                evidence=f"Order fill type: {system.order_fill_type}",
                severity='critical' if system.order_fill_type == 'rejected' else 'medium'
            ))
        
            # B3: High latency
            high_latency = trade.execution_latency_ms > self.high_latency_threshold
            checks.append(CheckResult(
                check_name="execution_latency",
                passed=not high_latency,
                confidence=0.6 if high_latency else 0.2,
                metric_values={'latency_ms': trade.execution_latency_ms},
                evidence=f"Execution latency: {trade.execution_latency_ms:.0f}ms",
                severity='medium' if high_latency else 'low'
            ))
        
            return checks
        except Exception as e:
            logger.error(f"Error in _check_execution_issues: {e}")
            raise
    
    def _check_risk_sizing(self, diagnostic: TriageDiagnostic) -> List[CheckResult]:
        """Check C: Risk sizing issues."""
        try:
            checks = []
            trade = diagnostic.trade_data
            market = diagnostic.market_snapshot
        
            # C1: Stop loss too tight relative to ATR
            if trade.sl and market.atr > 0:
                sl_distance = abs(trade.entry_price - trade.sl)
                atr_ratio = sl_distance / market.atr
                too_tight = atr_ratio < self.tight_sl_atr_ratio
            
                checks.append(CheckResult(
                    check_name="stop_loss_tightness",
                    passed=not too_tight,
                    confidence=0.78 if too_tight else 0.3,
                    metric_values={
                        'sl_distance': sl_distance,
                        'atr': market.atr,
                        'ratio': atr_ratio,
                        'threshold': self.tight_sl_atr_ratio
                    },
                    evidence=f"SL distance: {sl_distance:.5f}, ATR: {market.atr:.5f}, Ratio: {atr_ratio:.2f}",
                    severity='high' if too_tight else 'low'
                ))
        
            # C2: Position size validation (would need config limits)
            max_lot_size = self.config.get('max_lot_size', 1.0)
            oversized = trade.size > max_lot_size
            checks.append(CheckResult(
                check_name="position_size",
                passed=not oversized,
                confidence=0.7 if oversized else 0.2,
                metric_values={'size': trade.size, 'max_lot_size': max_lot_size},
                evidence=f"Position size: {trade.size:.2f}, Max: {max_lot_size:.2f}",
                severity='high' if oversized else 'low'
            ))
        
            return checks
        except Exception as e:
            logger.error(f"Error in _check_risk_sizing: {e}")
            raise
    
    def _check_market_external(self, diagnostic: TriageDiagnostic) -> List[CheckResult]:
        """Check D: Market & external factors."""
        try:
            checks = []
            market = diagnostic.market_snapshot
        
            # D1: Volatility spike
            vol_spike = market.volatility_spike
            checks.append(CheckResult(
                check_name="volatility_spike",
                passed=not vol_spike,
                confidence=0.65 if vol_spike else 0.2,
                metric_values={'spike_detected': vol_spike},
                evidence=f"Volatility spike: {vol_spike}",
                severity='high' if vol_spike else 'low'
            ))
        
            # D2: News events
            news_present = len(market.news_events) > 0
            checks.append(CheckResult(
                check_name="news_events",
                passed=not news_present,
                confidence=0.6 if news_present else 0.1,
                metric_values={'news_count': len(market.news_events)},
                evidence=f"News events: {len(market.news_events)}",
                severity='medium' if news_present else 'low'
            ))
        
            # D3: Spread widening (illiquidity)
            # Assume normal spread is < 0.0005 (5 pips for forex)
            wide_spread = market.spread > 0.001
            checks.append(CheckResult(
                check_name="spread_widening",
                passed=not wide_spread,
                confidence=0.7 if wide_spread else 0.2,
                metric_values={'spread': market.spread},
                evidence=f"Spread: {market.spread:.5f}",
                severity='medium' if wide_spread else 'low'
            ))
        
            return checks
        except Exception as e:
            logger.error(f"Error in _check_market_external: {e}")
            raise
    
    def _check_software_data(self, diagnostic: TriageDiagnostic) -> List[CheckResult]:
        """Check E: Software & data issues."""
        try:
            checks = []
            system = diagnostic.system_metrics
        
            # E1: System errors in logs
            has_errors = len(system.errors_in_logs) > 0
            checks.append(CheckResult(
                check_name="system_errors",
                passed=not has_errors,
                confidence=0.8 if has_errors else 0.1,
                metric_values={'error_count': len(system.errors_in_logs)},
                evidence=f"System errors: {len(system.errors_in_logs)}",
                severity='critical' if has_errors else 'low'
            ))
        
            # E2: High CPU/memory usage
            high_cpu = system.cpu_usage > 90
            high_mem = system.memory_usage > 90
            resource_issue = high_cpu or high_mem
            checks.append(CheckResult(
                check_name="resource_usage",
                passed=not resource_issue,
                confidence=0.5 if resource_issue else 0.1,
                metric_values={'cpu': system.cpu_usage, 'memory': system.memory_usage},
                evidence=f"CPU: {system.cpu_usage:.1f}%, Memory: {system.memory_usage:.1f}%",
                severity='medium' if resource_issue else 'low'
            ))
        
            return checks
        except Exception as e:
            logger.error(f"Error in _check_software_data: {e}")
            raise
    
    def _generate_signal_hypotheses(self, checks: List[CheckResult], 
                                   diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """Generate hypotheses from signal quality checks."""
        try:
            hypotheses = []
            failed_checks = [c for c in checks if not c.passed and c.confidence > 0.5]
        
            for check in failed_checks:
                if check.check_name == "signal_confidence":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_signal_conf",
                        cause_type=RootCauseType.SIGNAL_QUALITY,
                        description=f"Low model confidence ({check.metric_values['confidence']:.2f}) led to poor signal quality",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.7,
                        evidence=[check],
                        suggested_fixes=[
                            "Increase minimum confidence threshold",
                            "Require multi-timeframe confirmation",
                            "Add signal strength filter"
                        ]
                    ))
            
                elif check.check_name == "multi_tf_agreement":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_mtf_disagree",
                        cause_type=RootCauseType.SIGNAL_QUALITY,
                        description="Multi-timeframe disagreement indicated conflicting market views",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.6,
                        evidence=[check],
                        suggested_fixes=[
                            "Require multi-timeframe agreement before entry",
                            "Add higher timeframe trend filter",
                            "Implement timeframe weighting system"
                        ]
                    ))
        
            return hypotheses
        except Exception as e:
            logger.error(f"Error in _generate_signal_hypotheses: {e}")
            raise
    
    def _generate_execution_hypotheses(self, checks: List[CheckResult],
                                      diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """Generate hypotheses from execution checks."""
        try:
            hypotheses = []
            failed_checks = [c for c in checks if not c.passed and c.confidence > 0.5]
        
            for check in failed_checks:
                if check.check_name == "slippage":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_slippage",
                        cause_type=RootCauseType.EXECUTION_ISSUE,
                        description=f"High slippage ({check.metric_values['slippage']*100:.2f}%) due to illiquidity or market impact",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.8,
                        evidence=[check],
                        suggested_fixes=[
                            "Reduce position size during illiquid periods",
                            "Avoid trading during high-impact news",
                            "Use limit orders instead of market orders",
                            "Disable trading for this instrument during identified illiquid hours"
                        ]
                    ))
            
                elif check.check_name == "order_fill":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_fill_issue",
                        cause_type=RootCauseType.EXECUTION_ISSUE,
                        description=f"Order fill issue: {check.metric_values['fill_type']}",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.9,
                        evidence=[check],
                        suggested_fixes=[
                            "Check broker connection stability",
                            "Reduce position size",
                            "Increase order timeout",
                            "Switch to more liquid instruments"
                        ]
                    ))
        
            return hypotheses
        except Exception as e:
            logger.error(f"Error in _generate_execution_hypotheses: {e}")
            raise
    
    def _generate_risk_hypotheses(self, checks: List[CheckResult],
                                 diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """Generate hypotheses from risk sizing checks."""
        try:
            hypotheses = []
            failed_checks = [c for c in checks if not c.passed and c.confidence > 0.5]
        
            for check in failed_checks:
                if check.check_name == "stop_loss_tightness":
                    ratio = check.metric_values['ratio']
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_tight_sl",
                        cause_type=RootCauseType.RISK_SIZING,
                        description=f"Stop loss too tight at {ratio:.2f}x ATR, hit by normal market noise",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.75,
                        evidence=[check],
                        suggested_fixes=[
                            f"Increase SL to {self.tight_sl_atr_ratio}x ATR minimum",
                            "Use ATR-based dynamic stop loss",
                            "Implement volatility-adjusted position sizing"
                        ]
                    ))
        
            return hypotheses
        except Exception as e:
            logger.error(f"Error in _generate_risk_hypotheses: {e}")
            raise
    
    def _generate_market_hypotheses(self, checks: List[CheckResult],
                                   diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """Generate hypotheses from market/external checks."""
        try:
            hypotheses = []
            failed_checks = [c for c in checks if not c.passed and c.confidence > 0.5]
        
            for check in failed_checks:
                if check.check_name == "volatility_spike":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_vol_spike",
                        cause_type=RootCauseType.MARKET_EXTERNAL,
                        description="Volatility spike during trade caused unexpected price movement",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.65,
                        evidence=[check],
                        suggested_fixes=[
                            "Implement volatility filter before entry",
                            "Widen stops during high volatility periods",
                            "Reduce position size when ATR increases",
                            "Avoid trading during scheduled high-impact events"
                        ]
                    ))
            
                elif check.check_name == "news_events":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_news",
                        cause_type=RootCauseType.MARKET_EXTERNAL,
                        description=f"News events ({check.metric_values['news_count']}) caused unexpected market reaction",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.6,
                        evidence=[check],
                        suggested_fixes=[
                            "Implement news calendar filter",
                            "Close positions before high-impact news",
                            "Disable trading 30 minutes before/after major news",
                            "Reduce position size during news-heavy periods"
                        ]
                    ))
        
            return hypotheses
        except Exception as e:
            logger.error(f"Error in _generate_market_hypotheses: {e}")
            raise
    
    def _generate_software_hypotheses(self, checks: List[CheckResult],
                                     diagnostic: TriageDiagnostic) -> List[RootCauseHypothesis]:
        """Generate hypotheses from software/data checks."""
        try:
            hypotheses = []
            failed_checks = [c for c in checks if not c.passed and c.confidence > 0.5]
        
            for check in failed_checks:
                if check.check_name == "system_errors":
                    hypotheses.append(RootCauseHypothesis(
                        hypothesis_id=f"{diagnostic.trade_id}_sys_error",
                        cause_type=RootCauseType.SOFTWARE_DATA,
                        description=f"System errors ({check.metric_values['error_count']}) affected trade execution",
                        confidence=check.confidence,
                        estimated_impact=abs(diagnostic.pnl) * 0.85,
                        evidence=[check],
                        suggested_fixes=[
                            "Review and fix system errors",
                            "Clear cache and rebuild features",
                            "Restart trading system",
                            "Check data feed connectivity"
                        ]
                    ))
        
            return hypotheses
        except Exception as e:
            logger.error(f"Error in _generate_software_hypotheses: {e}")
            raise
