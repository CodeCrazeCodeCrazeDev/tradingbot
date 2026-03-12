"""
12-Domain Hedge Fund Architecture
==================================

This package implements a professional hedge fund architecture that organizes
the entire trading bot system into 12 cohesive domains, mirroring the structure
used by top hedge funds like Renaissance Technologies, Two Sigma, and Citadel.

Domains:
--------
1. Alpha Generation - Signal generation & strategies
2. Quant Research - Mathematical models & analysis
3. Risk Management - Risk control & monitoring
4. Execution - Trading operations & order routing
5. Data Infrastructure - Data engineering & feeds
6. Machine Learning - AI/ML platform & models
7. Technology Infrastructure - Core platform & systems
8. Compliance - Regulatory compliance
9. Operations - Business operations & support
10. Research & Development - Innovation & future tech
11. Portfolio Analytics - Performance & attribution
12. Governance & Control - Enterprise governance

Usage:
------
    from trading_bot.domains import DomainOrchestrator
    
    orchestrator = DomainOrchestrator()
    await orchestrator.initialize()
    
    # Access specific domains
    alpha = orchestrator.alpha_generation
    risk = orchestrator.risk_management
    execution = orchestrator.execution
"""

from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Domain identifiers
DOMAIN_ALPHA_GENERATION = "alpha_generation"
DOMAIN_QUANT_RESEARCH = "quant_research"
DOMAIN_RISK_MANAGEMENT = "risk_management"
DOMAIN_EXECUTION = "execution"
DOMAIN_DATA_INFRASTRUCTURE = "data_infrastructure"
DOMAIN_MACHINE_LEARNING = "machine_learning"
DOMAIN_TECHNOLOGY_INFRASTRUCTURE = "technology_infrastructure"
DOMAIN_COMPLIANCE = "compliance"
DOMAIN_OPERATIONS = "operations"
DOMAIN_RESEARCH_DEVELOPMENT = "research_development"
DOMAIN_PORTFOLIO_ANALYTICS = "portfolio_analytics"
DOMAIN_GOVERNANCE_CONTROL = "governance_control"

ALL_DOMAINS = [
    DOMAIN_ALPHA_GENERATION,
    DOMAIN_QUANT_RESEARCH,
    DOMAIN_RISK_MANAGEMENT,
    DOMAIN_EXECUTION,
    DOMAIN_DATA_INFRASTRUCTURE,
    DOMAIN_MACHINE_LEARNING,
    DOMAIN_TECHNOLOGY_INFRASTRUCTURE,
    DOMAIN_COMPLIANCE,
    DOMAIN_OPERATIONS,
    DOMAIN_RESEARCH_DEVELOPMENT,
    DOMAIN_PORTFOLIO_ANALYTICS,
    DOMAIN_GOVERNANCE_CONTROL,
]

# Lazy imports to avoid circular dependencies
def get_domain_orchestrator():
    """Get the main domain orchestrator."""
    from .orchestrator import DomainOrchestrator
    return DomainOrchestrator

def get_alpha_generation():
    """Get Alpha Generation domain."""
    from .alpha_generation import AlphaGenerationDomain
    return AlphaGenerationDomain

def get_quant_research():
    """Get Quant Research domain."""
    from .quant_research import QuantResearchDomain
    return QuantResearchDomain

def get_risk_management():
    """Get Risk Management domain."""
    from .risk_management import RiskManagementDomain
    return RiskManagementDomain

def get_execution():
    """Get Execution domain."""
    from .execution import ExecutionDomain
    return ExecutionDomain

def get_data_infrastructure():
    """Get Data Infrastructure domain."""
    from .data_infrastructure import DataInfrastructureDomain
    return DataInfrastructureDomain

def get_machine_learning():
    """Get Machine Learning domain."""
    from .machine_learning import MachineLearningDomain
    return MachineLearningDomain

def get_technology_infrastructure():
    """Get Technology Infrastructure domain."""
    from .technology_infrastructure import TechnologyInfrastructureDomain
    return TechnologyInfrastructureDomain

def get_compliance():
    """Get Compliance domain."""
    from .compliance import ComplianceDomain
    return ComplianceDomain

def get_operations():
    """Get Operations domain."""
    from .operations import OperationsDomain
    return OperationsDomain

def get_research_development():
    """Get Research & Development domain."""
    from .research_development import ResearchDevelopmentDomain
    return ResearchDevelopmentDomain

def get_portfolio_analytics():
    """Get Portfolio Analytics domain."""
    from .portfolio_analytics import PortfolioAnalyticsDomain
    return PortfolioAnalyticsDomain

def get_governance_control():
    """Get Governance & Control domain."""
    from .governance_control import GovernanceControlDomain
    return GovernanceControlDomain

__all__ = [
    # Domain identifiers
    'DOMAIN_ALPHA_GENERATION',
    'DOMAIN_QUANT_RESEARCH',
    'DOMAIN_RISK_MANAGEMENT',
    'DOMAIN_EXECUTION',
    'DOMAIN_DATA_INFRASTRUCTURE',
    'DOMAIN_MACHINE_LEARNING',
    'DOMAIN_TECHNOLOGY_INFRASTRUCTURE',
    'DOMAIN_COMPLIANCE',
    'DOMAIN_OPERATIONS',
    'DOMAIN_RESEARCH_DEVELOPMENT',
    'DOMAIN_PORTFOLIO_ANALYTICS',
    'DOMAIN_GOVERNANCE_CONTROL',
    'ALL_DOMAINS',
    # Lazy getters
    'get_domain_orchestrator',
    'get_alpha_generation',
    'get_quant_research',
    'get_risk_management',
    'get_execution',
    'get_data_infrastructure',
    'get_machine_learning',
    'get_technology_infrastructure',
    'get_compliance',
    'get_operations',
    'get_research_development',
    'get_portfolio_analytics',
    'get_governance_control',
]
