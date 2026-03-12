"""
Domain Orchestrator
====================

Master coordinator for all 12 hedge fund domains.
Manages domain lifecycle, inter-domain communication, and system-wide operations.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import logging

from .base import BaseDomain, DomainStatus, DomainPriority, DomainMessage, DomainHealth

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Overall system state."""
    OFFLINE = "offline"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class DomainOrchestrator:
    """
    Master orchestrator for the 12-domain hedge fund architecture.
    
    Coordinates all domains, manages inter-domain communication,
    and provides a unified interface for the trading system.
    
    Usage:
        orchestrator = DomainOrchestrator()
        await orchestrator.initialize()
        
        # Access domains
        signal = await orchestrator.alpha_generation.generate_signal("EURUSD")
        risk_check = await orchestrator.risk_management.check_risk(signal)
        
        # Execute trade
        if risk_check['approved']:
            result = await orchestrator.execution.execute_order(signal)
    """
    
    _instance: Optional['DomainOrchestrator'] = field(default=None, repr=False)
    _initialized: bool = field(default=False)
    _state: SystemState = field(default=SystemState.OFFLINE)
    _start_time: Optional[datetime] = field(default=None)
    _domains: Dict[str, BaseDomain] = field(default_factory=dict)
    _message_queue: asyncio.Queue = field(default_factory=asyncio.Queue)
    _message_processor_task: Optional[asyncio.Task] = field(default=None, repr=False)
    
    def __post_init__(self):
        self.logger = logging.getLogger("domain.orchestrator")
        self._lock = asyncio.Lock()
    
    @classmethod
    def get_instance(cls) -> 'DomainOrchestrator':
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    @property
    def state(self) -> SystemState:
        return self._state
    
    @property
    def uptime(self) -> float:
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return 0.0
    
    # Domain accessors
    @property
    def alpha_generation(self):
        return self._domains.get('alpha_generation')
    
    @property
    def quant_research(self):
        return self._domains.get('quant_research')
    
    @property
    def risk_management(self):
        return self._domains.get('risk_management')
    
    @property
    def execution(self):
        return self._domains.get('execution')
    
    @property
    def data_infrastructure(self):
        return self._domains.get('data_infrastructure')
    
    @property
    def machine_learning(self):
        return self._domains.get('machine_learning')
    
    @property
    def technology_infrastructure(self):
        return self._domains.get('technology_infrastructure')
    
    @property
    def compliance(self):
        return self._domains.get('compliance')
    
    @property
    def operations(self):
        return self._domains.get('operations')
    
    @property
    def research_development(self):
        return self._domains.get('research_development')
    
    @property
    def portfolio_analytics(self):
        return self._domains.get('portfolio_analytics')
    
    @property
    def governance_control(self):
        return self._domains.get('governance_control')
    
    async def initialize(self, domains_to_load: Optional[List[str]] = None) -> bool:
        """
        Initialize the domain orchestrator and all domains.
        
        Args:
            domains_to_load: Optional list of domain IDs to load. If None, loads all.
            
        Returns:
            bool: True if initialization successful
        """
        async with self._lock:
            if self._initialized:
                self.logger.warning("Orchestrator already initialized")
                return True
            
            self._state = SystemState.STARTING
            self._start_time = datetime.now()
            
            try:
                self.logger.info("=" * 60)
                self.logger.info("INITIALIZING 12-DOMAIN HEDGE FUND ARCHITECTURE")
                self.logger.info("=" * 60)
                
                # Create domain instances
                await self._create_domains()
                
                # Filter domains if specified
                if domains_to_load:
                    domains_to_init = {k: v for k, v in self._domains.items() if k in domains_to_load}
                else:
                    domains_to_init = self._domains
                
                # Initialize domains in priority order
                await self._initialize_domains_by_priority(domains_to_init)
                
                # Start message processor
                self._message_processor_task = asyncio.create_task(self._process_messages())
                
                self._initialized = True
                self._state = SystemState.RUNNING
                
                self.logger.info("=" * 60)
                self.logger.info(f"12-DOMAIN ARCHITECTURE INITIALIZED ({len(self._domains)} domains)")
                self.logger.info("=" * 60)
                
                return True
                
            except Exception as e:
                self.logger.error(f"Failed to initialize orchestrator: {e}")
                self._state = SystemState.ERROR
                return False
    
    async def shutdown(self) -> bool:
        """Gracefully shutdown all domains."""
        async with self._lock:
            if not self._initialized:
                return True
            
            self._state = SystemState.STOPPING
            self.logger.info("Shutting down 12-domain architecture...")
            
            try:
                # Stop message processor
                if self._message_processor_task:
                    self._message_processor_task.cancel()
                    try:
                        await self._message_processor_task
                    except asyncio.CancelledError:
                        pass
                
                # Shutdown domains in reverse priority order
                domains_by_priority = sorted(
                    self._domains.values(),
                    key=lambda d: d.priority.value,
                    reverse=True
                )
                
                for domain in domains_by_priority:
                    try:
                        await domain._safe_shutdown()
                    except Exception as e:
                        self.logger.error(f"Error shutting down {domain.domain_name}: {e}")
                
                self._initialized = False
                self._state = SystemState.OFFLINE
                self.logger.info("12-domain architecture shutdown complete")
                return True
                
            except Exception as e:
                self.logger.error(f"Error during shutdown: {e}")
                self._state = SystemState.ERROR
                return False
    
    async def _create_domains(self):
        """Create all domain instances."""
        from .alpha_generation import AlphaGenerationDomain
        from .quant_research import QuantResearchDomain
        from .risk_management import RiskManagementDomain
        from .execution import ExecutionDomain
        from .data_infrastructure import DataInfrastructureDomain
        from .machine_learning import MachineLearningDomain
        from .technology_infrastructure import TechnologyInfrastructureDomain
        from .compliance import ComplianceDomain
        from .operations import OperationsDomain
        from .research_development import ResearchDevelopmentDomain
        from .portfolio_analytics import PortfolioAnalyticsDomain
        from .governance_control import GovernanceControlDomain
        
        self._domains = {
            'alpha_generation': AlphaGenerationDomain(),
            'quant_research': QuantResearchDomain(),
            'risk_management': RiskManagementDomain(),
            'execution': ExecutionDomain(),
            'data_infrastructure': DataInfrastructureDomain(),
            'machine_learning': MachineLearningDomain(),
            'technology_infrastructure': TechnologyInfrastructureDomain(),
            'compliance': ComplianceDomain(),
            'operations': OperationsDomain(),
            'research_development': ResearchDevelopmentDomain(),
            'portfolio_analytics': PortfolioAnalyticsDomain(),
            'governance_control': GovernanceControlDomain(),
        }
        
        self.logger.info(f"Created {len(self._domains)} domain instances")
    
    async def _initialize_domains_by_priority(self, domains: Dict[str, BaseDomain]):
        """Initialize domains in priority order (CRITICAL first)."""
        # Group by priority
        priority_groups = {}
        for domain in domains.values():
            priority = domain.priority
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(domain)
        
        # Initialize in priority order
        for priority in sorted(priority_groups.keys(), key=lambda p: p.value):
            group = priority_groups[priority]
            self.logger.info(f"Initializing {priority.name} priority domains...")
            
            # Initialize domains in parallel within same priority
            tasks = [domain._safe_initialize() for domain in group]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for domain, result in zip(group, results):
                if isinstance(result, Exception):
                    self.logger.error(f"Failed to initialize {domain.domain_name}: {result}")
                elif result:
                    self.logger.info(f"  ✓ {domain.domain_name}")
                else:
                    self.logger.warning(f"  ✗ {domain.domain_name} (initialization returned False)")
    
    async def _process_messages(self):
        """Process inter-domain messages."""
        while True:
            try:
                message = await self._message_queue.get()
                target_domain = self._domains.get(message.target_domain)
                
                if target_domain:
                    await target_domain.handle_message(message)
                else:
                    self.logger.warning(f"Unknown target domain: {message.target_domain}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")
    
    async def send_message(self, message: DomainMessage) -> Optional[Dict[str, Any]]:
        """Send a message to a domain."""
        target_domain = self._domains.get(message.target_domain)
        if target_domain:
            return await target_domain.handle_message(message)
        return None
    
    def get_domain(self, domain_id: str) -> Optional[BaseDomain]:
        """Get a domain by ID."""
        return self._domains.get(domain_id)
    
    def get_all_domains(self) -> Dict[str, BaseDomain]:
        """Get all domains."""
        return self._domains.copy()
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health."""
        domain_health = {}
        healthy_count = 0
        
        for domain_id, domain in self._domains.items():
            health = domain.get_health()
            domain_health[domain_id] = health.to_dict()
            if health.is_healthy():
                healthy_count += 1
        
        return {
            'state': self._state.value,
            'uptime_seconds': self.uptime,
            'total_domains': len(self._domains),
            'healthy_domains': healthy_count,
            'degraded_domains': len(self._domains) - healthy_count,
            'domains': domain_health,
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status summary."""
        return {
            'state': self._state.value,
            'initialized': self._initialized,
            'uptime_seconds': self.uptime,
            'domains': {
                domain_id: {
                    'name': domain.domain_name,
                    'priority': domain.priority.name,
                    'status': domain.health.status.value,
                    'initialized': domain.is_initialized,
                }
                for domain_id, domain in self._domains.items()
            },
        }
    
    def get_capabilities(self) -> Dict[str, List[str]]:
        """Get all capabilities across domains."""
        return {
            domain_id: domain.get_capabilities()
            for domain_id, domain in self._domains.items()
        }
    
    def get_module_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get all module mappings across domains."""
        return {
            domain_id: domain.get_module_mapping()
            for domain_id, domain in self._domains.items()
        }
    
    # Convenience methods for common operations
    async def generate_and_execute_signal(
        self,
        symbol: str,
        timeframe: str = "1H",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a signal and execute it through the full pipeline.
        
        This demonstrates the inter-domain workflow:
        1. Alpha Generation generates signal
        2. Risk Management validates
        3. Compliance checks
        4. Execution executes
        5. Portfolio Analytics records
        """
        result = {
            'symbol': symbol,
            'timeframe': timeframe,
            'steps': [],
            'success': False,
        }
        
        try:
            # Step 1: Generate signal
            if self.alpha_generation:
                signal = await self.alpha_generation.generate_signal(symbol, timeframe, **kwargs)
                result['steps'].append({'step': 'signal_generation', 'result': signal})
                
                if not signal or signal.get('confidence', 0) < 0.5:
                    result['reason'] = 'Low confidence signal'
                    return result
            else:
                result['reason'] = 'Alpha Generation domain not available'
                return result
            
            # Step 2: Risk check
            if self.risk_management:
                risk_check = await self.risk_management.check_risk(signal)
                result['steps'].append({'step': 'risk_check', 'result': risk_check})
                
                if not risk_check.get('approved', False):
                    result['reason'] = 'Risk check failed'
                    return result
            
            # Step 3: Compliance check
            if self.compliance:
                compliance_check = await self.compliance.check_compliance(signal)
                result['steps'].append({'step': 'compliance_check', 'result': compliance_check})
                
                if not compliance_check.get('compliant', False):
                    result['reason'] = 'Compliance check failed'
                    return result
            
            # Step 4: Execute
            if self.execution:
                execution_result = await self.execution.execute_order(signal)
                result['steps'].append({'step': 'execution', 'result': execution_result})
                result['success'] = True
            
            return result
            
        except Exception as e:
            result['error'] = str(e)
            return result


# Convenience function
async def create_orchestrator(domains: Optional[List[str]] = None) -> DomainOrchestrator:
    """Create and initialize a domain orchestrator."""
    orchestrator = DomainOrchestrator()
    await orchestrator.initialize(domains)
    return orchestrator


__all__ = ['DomainOrchestrator', 'SystemState', 'create_orchestrator']
