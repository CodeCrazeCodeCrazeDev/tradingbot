"""
Risk Management Innovations Module (Ideas 61-90)
==================================================
Advanced risk management and control systems.
"""

from .tail_risk import TailRiskHedger
from .regime_var import RegimeAwareVaR
from .liquidity_risk import LiquidityRiskManager
from .correlation_breakdown import CorrelationBreakdownDetector
from .stress_testing import DynamicStressTester
from .drawdown_control import DrawdownController
from .risk_budgeting import RiskBudgetAllocator
from .factor_risk import FactorRiskDecomposer
from .contagion_risk import ContagionRiskMonitor
from .counterparty_risk import CounterpartyRiskAnalyzer
from .operational_risk import OperationalRiskManager
from .model_risk import ModelRiskValidator
from .cyber_risk import CyberRiskMonitor
from .climate_risk import ClimateRiskAnalyzer
from .geopolitical_risk import GeopoliticalRiskTracker
from .concentration_risk import ConcentrationRiskManager
from .leverage_monitor import LeverageMonitor
from .margin_optimizer import MarginOptimizer
from .collateral_manager import CollateralManager
from .risk_attribution import RiskAttributionEngine
from .scenario_generator import ScenarioGenerator
from .risk_limits import DynamicRiskLimits
from .hedging_optimizer import HedgingOptimizer
from .portfolio_insurance import PortfolioInsurance
from .risk_parity import RiskParityEngine
from .volatility_targeting import VolatilityTargeting
from .risk_overlay import RiskOverlayManager
from .extreme_value import ExtremeValueAnalyzer
from .copula_risk import CopulaRiskModeler
from .jump_risk import JumpRiskDetector

__all__ = [
    "TailRiskHedger",
    "RegimeAwareVaR",
    "LiquidityRiskManager",
    "CorrelationBreakdownDetector",
    "DynamicStressTester",
    "DrawdownController",
    "RiskBudgetAllocator",
    "FactorRiskDecomposer",
    "ContagionRiskMonitor",
    "CounterpartyRiskAnalyzer",
    "OperationalRiskManager",
    "ModelRiskValidator",
    "CyberRiskMonitor",
    "ClimateRiskAnalyzer",
    "GeopoliticalRiskTracker",
    "ConcentrationRiskManager",
    "LeverageMonitor",
    "MarginOptimizer",
    "CollateralManager",
    "RiskAttributionEngine",
    "ScenarioGenerator",
    "DynamicRiskLimits",
    "HedgingOptimizer",
    "PortfolioInsurance",
    "RiskParityEngine",
    "VolatilityTargeting",
    "RiskOverlayManager",
    "ExtremeValueAnalyzer",
    "CopulaRiskModeler",
    "JumpRiskDetector",
]
