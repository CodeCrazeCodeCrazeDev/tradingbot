"""
Domain 7: Technology Infrastructure
=====================================

Core technology, platform engineering, and DevOps.

Mapped Modules:
- infrastructure, core, core_api, system_supervisor, monitoring, observability
- cloud_deployer, devops, distributed, deployment, production, ultimate_production
- ops, services, api, web, dashboard, documentation, error_handling
- critical_fixes, diagnostics, profiling, testing, upgrades, utils, utils2
"""

from ..base import BaseDomain, DomainPriority, DomainStatus
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class TechnologyInfrastructureDomain(BaseDomain):
    """
    Technology Infrastructure Domain - Platform engineering.
    
    This domain is responsible for:
    - Cloud infrastructure
    - Container orchestration
    - Monitoring systems
    - Security infrastructure
    - DevOps pipelines
    """
    
    MODULE_MAPPINGS = {
        # Infrastructure
        'infrastructure': 'trading_bot.infrastructure',
        'core': 'trading_bot.core',
        'core_api': 'trading_bot.core_api',
        'system_supervisor': 'trading_bot.system_supervisor',
        'monitoring': 'trading_bot.monitoring',
        'observability': 'trading_bot.observability',
        
        # DevOps
        'cloud_deployer': 'trading_bot.cloud_deployer',
        'devops': 'trading_bot.devops',
        'distributed': 'trading_bot.distributed',
        'deployment': 'trading_bot.deployment',
        'production': 'trading_bot.production',
        'ultimate_production': 'trading_bot.ultimate_production',
        
        # Services
        'ops': 'trading_bot.ops',
        'services': 'trading_bot.services',
        'api': 'trading_bot.api',
        'web': 'trading_bot.web',
        'dashboard': 'trading_bot.dashboard',
        'documentation': 'trading_bot.documentation',
        
        # Maintenance
        'error_handling': 'trading_bot.error_handling',
        'critical_fixes': 'trading_bot.critical_fixes',
        'diagnostics': 'trading_bot.diagnostics',
        'profiling': 'trading_bot.profiling',
        'testing': 'trading_bot.testing',
        'upgrades': 'trading_bot.upgrades',
        'utils': 'trading_bot.utils',
        'utils2': 'trading_bot.utils2',
    }
    
    def __init__(self):
        super().__init__(
            domain_id="technology_infrastructure",
            domain_name="Technology Infrastructure",
            priority=DomainPriority.HIGH
        )
    
    async def initialize(self) -> bool:
        try:
            self.logger.info("Initializing Technology Infrastructure domain...")
            await self._load_core_systems()
            self.logger.info(f"Technology Infrastructure initialized with {len(self._modules)} modules")
            return True
        except Exception as e:
            self.logger.error(f"Failed to initialize Technology Infrastructure: {e}")
            return False
    
    async def shutdown(self) -> bool:
        self._modules.clear()
        return True
    
    def get_capabilities(self) -> List[str]:
        return [
            "cloud_management",
            "container_orchestration",
            "monitoring",
            "logging",
            "alerting",
            "deployment",
            "scaling",
            "security",
            "backup_recovery",
            "performance_optimization",
        ]
    
    def get_module_mapping(self) -> Dict[str, str]:
        return self.MODULE_MAPPINGS.copy()
    
    async def _load_core_systems(self):
        try:
            from trading_bot import core
            self.register_module('core', core)
        except ImportError:
            pass
        try:
            from trading_bot import services
            self.register_module('services', services)
        except ImportError:
            pass


__all__ = ['TechnologyInfrastructureDomain']
