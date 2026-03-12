# AlphaAlgo Institutional Quantitative Research System
# A multi-disciplinary institutional quantitative research, risk, and portfolio intelligence platform
#
# CORE PHILOSOPHY (NON-NEGOTIABLE):
# - Markets are non-stationary, adversarial, and partially efficient
# - Prediction is unreliable; distribution control is superior
# - Capital preservation has veto power over opportunity
# - All models decay; systems must adapt or delete them
# - Portfolio behavior matters more than individual strategies
# - Risk is global, not local
# - No single model is ever trusted
# - Evolution is mostly subtraction, not addition
#
# SYSTEM ARCHITECTURE (7 LAYERS):
# 1. Market Selection Layer
# 2. Regime Detection Layer
# 3. Quantitative Research Layer
# 4. Strategic Portfolio Allocation Layer
# 5. Risk Governance Layer
# 6. Execution & Microstructure Layer
# 7. Monitoring, Audit & Evolution Layer

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .layer1_market_selection import MarketSelectionLayer, MarketSelectionCommittee
    from .layer2_regime_detection import RegimeDetectionLayer, RegimeIntelligenceUnit
    from .layer3_quantitative_research import QuantitativeResearchLayer, QuantitativeResearchLab
    from .layer4_portfolio_allocation import PortfolioAllocationLayer, PortfolioCapitalCommittee
    from .layer5_risk_governance import RiskGovernanceLayer, ValidationKillCommittee
    from .layer6_execution import ExecutionLayer, ExecutionIntelligenceUnit
    from .layer7_monitoring_evolution import MonitoringEvolutionLayer, EvolutionAuditEngine
    from .idea_vectors import IdeaVectorConstraints
    from .research_loop import SelfEvolvingResearchLoop
    from .orchestrator import AlphaAlgoInstitutional

__all__ = [
    # Layer 1: Market Selection
    'MarketSelectionLayer',
    'MarketSelectionCommittee',
    
    # Layer 2: Regime Detection
    'RegimeDetectionLayer',
    'RegimeIntelligenceUnit',
    
    # Layer 3: Quantitative Research
    'QuantitativeResearchLayer',
    'QuantitativeResearchLab',
    
    # Layer 4: Portfolio Allocation
    'PortfolioAllocationLayer',
    'PortfolioCapitalCommittee',
    
    # Layer 5: Risk Governance
    'RiskGovernanceLayer',
    'ValidationKillCommittee',
    
    # Layer 6: Execution
    'ExecutionLayer',
    'ExecutionIntelligenceUnit',
    
    # Layer 7: Monitoring & Evolution
    'MonitoringEvolutionLayer',
    'EvolutionAuditEngine',
    
    # Core Components
    'IdeaVectorConstraints',
    'SelfEvolvingResearchLoop',
    'AlphaAlgoInstitutional',
]


def __getattr__(name: str):
    """Lazy import to avoid circular dependencies."""
    if name == 'MarketSelectionLayer':
        from .layer1_market_selection import MarketSelectionLayer
        return MarketSelectionLayer
    elif name == 'MarketSelectionCommittee':
        from .layer1_market_selection import MarketSelectionCommittee
        return MarketSelectionCommittee
    elif name == 'RegimeDetectionLayer':
        from .layer2_regime_detection import RegimeDetectionLayer
        return RegimeDetectionLayer
    elif name == 'RegimeIntelligenceUnit':
        from .layer2_regime_detection import RegimeIntelligenceUnit
        return RegimeIntelligenceUnit
    elif name == 'QuantitativeResearchLayer':
        from .layer3_quantitative_research import QuantitativeResearchLayer
        return QuantitativeResearchLayer
    elif name == 'QuantitativeResearchLab':
        from .layer3_quantitative_research import QuantitativeResearchLab
        return QuantitativeResearchLab
    elif name == 'PortfolioAllocationLayer':
        from .layer4_portfolio_allocation import PortfolioAllocationLayer
        return PortfolioAllocationLayer
    elif name == 'PortfolioCapitalCommittee':
        from .layer4_portfolio_allocation import PortfolioCapitalCommittee
        return PortfolioCapitalCommittee
    elif name == 'RiskGovernanceLayer':
        from .layer5_risk_governance import RiskGovernanceLayer
        return RiskGovernanceLayer
    elif name == 'ValidationKillCommittee':
        from .layer5_risk_governance import ValidationKillCommittee
        return ValidationKillCommittee
    elif name == 'ExecutionLayer':
        from .layer6_execution import ExecutionLayer
        return ExecutionLayer
    elif name == 'ExecutionIntelligenceUnit':
        from .layer6_execution import ExecutionIntelligenceUnit
        return ExecutionIntelligenceUnit
    elif name == 'MonitoringEvolutionLayer':
        from .layer7_monitoring_evolution import MonitoringEvolutionLayer
        return MonitoringEvolutionLayer
    elif name == 'EvolutionAuditEngine':
        from .layer7_monitoring_evolution import EvolutionAuditEngine
        return EvolutionAuditEngine
    elif name == 'IdeaVectorConstraints':
        return IdeaVectorConstraints
    elif name == 'SelfEvolvingResearchLoop':
        return SelfEvolvingResearchLoop
    elif name == 'AlphaAlgoInstitutional':
        return AlphaAlgoInstitutional
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
