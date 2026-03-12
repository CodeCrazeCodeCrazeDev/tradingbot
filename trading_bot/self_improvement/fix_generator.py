"""
Fix Generator
Proposes conservative, safe fixes for identified root causes.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from enum import Enum
import logging
from datetime import datetime

from .root_cause_analyzer import RootCauseHypothesis, RootCauseType
from typing import Set
from enum import auto

logger = logging.getLogger(__name__)


class FixType(Enum):
    """Types of fixes that can be applied."""
    CONFIG_CHANGE = "config_change"
    PARAMETER_ADJUSTMENT = "parameter_adjustment"
    FILTER_ADD = "filter_add"
    THRESHOLD_CHANGE = "threshold_change"
    DISABLE_FEATURE = "disable_feature"
    MODEL_ROLLBACK = "model_rollback"
    CACHE_CLEAR = "cache_clear"


class RiskLevel(Enum):
    """Risk level of applying a fix."""
    SAFE = "safe"  # No risk increase, can auto-apply
    LOW = "low"  # Minimal risk, can auto-apply with monitoring
    MEDIUM = "medium"  # Requires human approval
    HIGH = "high"  # Requires human approval and testing
    PROHIBITED = "prohibited"  # Never auto-apply


@dataclass
class ProposedFix:
    """A proposed fix for a root cause."""
    fix_id: str
    hypothesis_id: str
    fix_type: FixType
    risk_level: RiskLevel
    description: str
    implementation: Dict[str, Any]  # Specific changes to make
    expected_impact: str
    rollback_plan: str
    validation_criteria: Dict[str, Any]
    auto_approvable: bool
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'fix_id': self.fix_id,
            'hypothesis_id': self.hypothesis_id,
            'fix_type': self.fix_type.value,
            'risk_level': self.risk_level.value,
            'description': self.description,
            'implementation': self.implementation,
            'expected_impact': self.expected_impact,
            'rollback_plan': self.rollback_plan,
            'validation_criteria': self.validation_criteria,
            'auto_approvable': self.auto_approvable
        }


class FixGenerator:
    """
    Generates conservative, safe fixes for identified root causes.
    Only proposes fixes that reduce risk or maintain current risk levels.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize fix generator.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config
            self.auto_approve_threshold = config.get('auto_approve_risk_threshold', RiskLevel.LOW)
        
            # Safety limits - NEVER increase these automatically
            self.max_lot_size = config.get('max_lot_size', 1.0)
            self.max_risk_per_trade = config.get('risk_per_trade', 0.01)
            self.min_stop_loss_pips = config.get('min_stop_loss_pips', 10)
        
            logger.info("FixGenerator initialized with conservative safety limits")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_fixes(self, hypotheses: List[RootCauseHypothesis]) -> List[ProposedFix]:
        """
        Generate safe fixes for all hypotheses.
        
        Args:
            hypotheses: List of root cause hypotheses
            
        Returns:
            List of proposed fixes
        """
        try:
            fixes = []
        
            for hypothesis in hypotheses:
                hypothesis_fixes = self._generate_fixes_for_hypothesis(hypothesis)
                fixes.extend(hypothesis_fixes)
        
            # Filter out prohibited fixes
            safe_fixes = [f for f in fixes if f.risk_level != RiskLevel.PROHIBITED]
        
            logger.info(f"Generated {len(safe_fixes)} safe fixes from {len(hypotheses)} hypotheses")
        
            return safe_fixes
        except Exception as e:
            logger.error(f"Error in generate_fixes: {e}")
            raise
    
    def _generate_fixes_for_hypothesis(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for a specific hypothesis."""
        try:
            if hypothesis.cause_type == RootCauseType.SIGNAL_QUALITY:
                return self._fixes_for_signal_quality(hypothesis)
            elif hypothesis.cause_type == RootCauseType.EXECUTION_ISSUE:
                return self._fixes_for_execution(hypothesis)
            elif hypothesis.cause_type == RootCauseType.RISK_SIZING:
                return self._fixes_for_risk_sizing(hypothesis)
            elif hypothesis.cause_type == RootCauseType.MARKET_EXTERNAL:
                return self._fixes_for_market_external(hypothesis)
            elif hypothesis.cause_type == RootCauseType.SOFTWARE_DATA:
                return self._fixes_for_software_data(hypothesis)
            else:
                return []
        except Exception as e:
            logger.error(f"Error in _generate_fixes_for_hypothesis: {e}")
            raise
    
    def _fixes_for_signal_quality(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for signal quality issues."""
        try:
            fixes = []
        
            if "low model confidence" in hypothesis.description.lower():
                # Increase confidence threshold
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_conf_threshold",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.THRESHOLD_CHANGE,
                    risk_level=RiskLevel.SAFE,
                    description="Increase minimum confidence threshold to filter weak signals",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'ai_ml.confidence_threshold',
                        'current_value': 0.5,
                        'new_value': 0.7,
                        'action': 'increase_threshold'
                    },
                    expected_impact="Reduce false signals, lower trade frequency by ~30%",
                    rollback_plan="Revert confidence_threshold to previous value",
                    validation_criteria={
                        'win_rate_improvement': 0.05,  # 5% improvement
                        'max_drawdown_reduction': 0.02,  # 2% reduction
                        'min_trade_count': 50  # Need at least 50 trades to validate
                    },
                    auto_approvable=True
                ))
        
            if "multi-timeframe disagreement" in hypothesis.description.lower():
                # Require MTF agreement
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_mtf_filter",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.FILTER_ADD,
                    risk_level=RiskLevel.SAFE,
                    description="Require multi-timeframe agreement before entry",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'trading.require_mtf_agreement',
                        'current_value': False,
                        'new_value': True,
                        'action': 'enable_filter'
                    },
                    expected_impact="Reduce conflicting signals, lower trade frequency by ~40%",
                    rollback_plan="Set require_mtf_agreement to False",
                    validation_criteria={
                        'win_rate_improvement': 0.08,
                        'max_trade_frequency_reduction': 0.5,
                        'min_trade_count': 50
                    },
                    auto_approvable=True
                ))
        
            return fixes
        except Exception as e:
            logger.error(f"Error in _fixes_for_signal_quality: {e}")
            raise
    
    def _fixes_for_execution(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for execution issues."""
        try:
            fixes = []
        
            if "high slippage" in hypothesis.description.lower():
                # Reduce position size during illiquid periods
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_reduce_size",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.PARAMETER_ADJUSTMENT,
                    risk_level=RiskLevel.SAFE,
                    description="Reduce position size by 50% during high slippage periods",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'risk.slippage_position_multiplier',
                        'current_value': 1.0,
                        'new_value': 0.5,
                        'condition': 'slippage > 0.005',
                        'action': 'conditional_multiplier'
                    },
                    expected_impact="Reduce slippage impact, lower risk exposure",
                    rollback_plan="Set slippage_position_multiplier to 1.0",
                    validation_criteria={
                        'slippage_reduction': 0.3,
                        'pnl_improvement': 0.1,
                        'min_trade_count': 30
                    },
                    auto_approvable=True
                ))
            
                # Disable trading during identified illiquid hours
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_time_filter",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.FILTER_ADD,
                    risk_level=RiskLevel.SAFE,
                    description="Disable trading during illiquid hours (identified from slippage patterns)",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'trading.disabled_hours',
                        'current_value': [],
                        'new_value': ['22:00-23:00', '00:00-01:00'],  # Example
                        'action': 'add_time_filter'
                    },
                    expected_impact="Avoid illiquid periods, reduce slippage losses",
                    rollback_plan="Clear disabled_hours list",
                    validation_criteria={
                        'slippage_reduction': 0.4,
                        'trade_frequency_reduction': 0.2,
                        'min_observation_days': 7
                    },
                    auto_approvable=True
                ))
        
            if "order fill issue" in hypothesis.description.lower():
                # Reduce position size
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_size_reduction",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.PARAMETER_ADJUSTMENT,
                    risk_level=RiskLevel.SAFE,
                    description="Reduce maximum position size to improve fill rates",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'risk.max_position_size',
                        'current_value': self.max_lot_size,
                        'new_value': self.max_lot_size * 0.7,
                        'action': 'reduce_limit'
                    },
                    expected_impact="Improve order fill rate, reduce partial fills",
                    rollback_plan="Restore max_position_size to original value",
                    validation_criteria={
                        'fill_rate_improvement': 0.15,
                        'partial_fill_reduction': 0.5,
                        'min_trade_count': 50
                    },
                    auto_approvable=True
                ))
        
            return fixes
        except Exception as e:
            logger.error(f"Error in _fixes_for_execution: {e}")
            raise
    
    def _fixes_for_risk_sizing(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for risk sizing issues."""
        try:
            fixes = []
        
            if "stop loss too tight" in hypothesis.description.lower():
                # Use ATR-based stop loss
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_atr_sl",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.PARAMETER_ADJUSTMENT,
                    risk_level=RiskLevel.SAFE,
                    description="Implement ATR-based stop loss (1.5x ATR minimum)",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'trading.stop_loss_atr_multiplier',
                        'current_value': 1.0,
                        'new_value': 1.5,
                        'action': 'increase_multiplier'
                    },
                    expected_impact="Reduce stop-outs from noise, wider stops but better win rate",
                    rollback_plan="Set stop_loss_atr_multiplier to 1.0",
                    validation_criteria={
                        'stop_out_reduction': 0.3,
                        'win_rate_improvement': 0.1,
                        'max_drawdown_neutral': True,  # Should not increase drawdown
                        'min_trade_count': 50
                    },
                    auto_approvable=True
                ))
            
                # Reduce position size to compensate for wider stops
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_compensate_size",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.PARAMETER_ADJUSTMENT,
                    risk_level=RiskLevel.SAFE,
                    description="Reduce position size to maintain same risk with wider stops",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'risk.position_size_multiplier',
                        'current_value': 1.0,
                        'new_value': 0.67,  # Compensate for 1.5x wider stops
                        'action': 'adjust_multiplier'
                    },
                    expected_impact="Maintain constant risk per trade despite wider stops",
                    rollback_plan="Set position_size_multiplier to 1.0",
                    validation_criteria={
                        'risk_per_trade_constant': True,
                        'drawdown_neutral': True,
                        'min_trade_count': 50
                    },
                    auto_approvable=True
                ))
        
            return fixes
        except Exception as e:
            logger.error(f"Error in _fixes_for_risk_sizing: {e}")
            raise
    
    def _fixes_for_market_external(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for market/external issues."""
        try:
            fixes = []
        
            if "volatility spike" in hypothesis.description.lower():
                # Add volatility filter
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_vol_filter",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.FILTER_ADD,
                    risk_level=RiskLevel.SAFE,
                    description="Disable trading when ATR increases >50% from average",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'trading.volatility_filter_enabled',
                        'current_value': False,
                        'new_value': True,
                        'additional_params': {
                            'volatility_threshold': 1.5,  # 1.5x average ATR
                            'lookback_periods': 20
                        },
                        'action': 'enable_filter'
                    },
                    expected_impact="Avoid trading during abnormal volatility, reduce unexpected losses",
                    rollback_plan="Set volatility_filter_enabled to False",
                    validation_criteria={
                        'volatility_loss_reduction': 0.4,
                        'trade_frequency_reduction': 0.15,
                        'min_observation_days': 14
                    },
                    auto_approvable=True
                ))
        
            if "news events" in hypothesis.description.lower():
                # Add news filter
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_news_filter",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.FILTER_ADD,
                    risk_level=RiskLevel.SAFE,
                    description="Disable trading 30 minutes before/after high-impact news",
                    implementation={
                        'config_file': 'config/config.yaml',
                        'parameter': 'trading.news_filter_enabled',
                        'current_value': False,
                        'new_value': True,
                        'additional_params': {
                            'buffer_minutes': 30,
                            'impact_levels': ['high', 'medium']
                        },
                        'action': 'enable_filter'
                    },
                    expected_impact="Avoid unpredictable news-driven moves, reduce volatility exposure",
                    rollback_plan="Set news_filter_enabled to False",
                    validation_criteria={
                        'news_loss_reduction': 0.5,
                        'trade_frequency_reduction': 0.1,
                        'min_observation_days': 14
                    },
                    auto_approvable=True
                ))
        
            return fixes
        except Exception as e:
            logger.error(f"Error in _fixes_for_market_external: {e}")
            raise
    
    def _fixes_for_software_data(self, hypothesis: RootCauseHypothesis) -> List[ProposedFix]:
        """Generate fixes for software/data issues."""
        try:
            fixes = []
        
            if "system errors" in hypothesis.description.lower():
                # Clear cache and rebuild
                fixes.append(ProposedFix(
                    fix_id=f"{hypothesis.hypothesis_id}_cache_clear",
                    hypothesis_id=hypothesis.hypothesis_id,
                    fix_type=FixType.CACHE_CLEAR,
                    risk_level=RiskLevel.SAFE,
                    description="Clear feature cache and rebuild from fresh data",
                    implementation={
                        'action': 'clear_cache',
                        'cache_paths': [
                            'cache/features',
                            'cache/indicators',
                            'cache/models'
                        ],
                        'rebuild': True
                    },
                    expected_impact="Eliminate stale data issues, restore data integrity",
                    rollback_plan="Restore from cache backup",
                    validation_criteria={
                        'error_elimination': True,
                        'data_integrity_check': True,
                        'min_runtime_hours': 2
                    },
                    auto_approvable=True
                ))
        
            return fixes
        except Exception as e:
            logger.error(f"Error in _fixes_for_software_data: {e}")
            raise
    
    def validate_fix_safety(self, fix: ProposedFix) -> bool:
        """
        Validate that a fix doesn't increase risk.
        
        Args:
            fix: Proposed fix to validate
            
        Returns:
            True if fix is safe, False otherwise
        """
        try:
            impl = fix.implementation
        
            # PROHIBITED: Never increase max lot size
            if impl.get('parameter') == 'risk.max_position_size':
                if impl.get('new_value', 0) > impl.get('current_value', 0):
                    logger.warning(f"Fix {fix.fix_id} REJECTED: Attempts to increase max_position_size")
                    return False
        
            # PROHIBITED: Never increase risk per trade
            if impl.get('parameter') == 'risk.risk_per_trade':
                if impl.get('new_value', 0) > impl.get('current_value', 0):
                    logger.warning(f"Fix {fix.fix_id} REJECTED: Attempts to increase risk_per_trade")
                    return False
        
            # PROHIBITED: Never remove stop loss
            if 'stop_loss' in impl.get('parameter', ''):
                if impl.get('action') == 'disable' or impl.get('new_value') is None:
                    logger.warning(f"Fix {fix.fix_id} REJECTED: Attempts to remove stop loss")
                    return False
        
            # PROHIBITED: Never remove take profit
            if 'take_profit' in impl.get('parameter', ''):
                if impl.get('action') == 'disable' or impl.get('new_value') is None:
                    logger.warning(f"Fix {fix.fix_id} REJECTED: Attempts to remove take profit")
                    return False
        
            # All other fixes are allowed if they reduce risk or maintain it
            return True
        except Exception as e:
            logger.error(f"Error in validate_fix_safety: {e}")
            raise
