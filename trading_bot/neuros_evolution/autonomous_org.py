"""
Autonomous Organization Management

AI project managers, performance monitors, resource economists, and
strategy portfolio managers for autonomous system coordination.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Set
import numpy as np
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class ProjectStatus(Enum):
    """Project status"""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DEPLOYED = "deployed"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ResourceType(Enum):
    """Resource types"""
    CAPITAL = "capital"
    COMPUTE = "compute"
    DATA = "data"
    HUMAN_OVERSIGHT = "human_oversight"


@dataclass
class Project:
    """Research/development project"""
    project_id: str
    name: str
    description: str
    status: ProjectStatus
    priority: int
    created_at: datetime
    estimated_duration_days: int
    assigned_agents: List[str] = field(default_factory=list)
    required_resources: Dict[str, float] = field(default_factory=dict)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    progress: float = 0.0
    expected_value: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'project_id': self.project_id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority,
            'created_at': self.created_at.isoformat(),
            'estimated_duration_days': self.estimated_duration_days,
            'assigned_agents': self.assigned_agents,
            'required_resources': self.required_resources,
            'milestones': self.milestones,
            'progress': self.progress,
            'expected_value': self.expected_value,
        }


@dataclass
class PerformanceMetric:
    """Performance metric"""
    metric_id: str
    component_id: str
    metric_name: str
    value: float
    timestamp: datetime
    threshold_min: Optional[float] = None
    threshold_max: Optional[float] = None
    
    def is_within_bounds(self) -> bool:
        """Check if metric is within acceptable bounds"""
        if self.threshold_min is not None and self.value < self.threshold_min:
            return False
        if self.threshold_max is not None and self.value > self.threshold_max:
            return False
        return True


class AIProjectManager:
    """
    AI project manager that coordinates research initiatives.
    
    Responsibilities:
    - Project planning and scheduling
    - Resource allocation
    - Progress tracking
    - Risk management
    - Stakeholder communication
    """
    
    def __init__(self, manager_id: str, config: Optional[Dict[str, Any]] = None):
        self.manager_id = manager_id
        self.config = config or {}
        self.projects: Dict[str, Project] = {}
        self.completed_projects: List[Project] = []
        self.project_history: deque = deque(maxlen=1000)
        
    def create_project(self, name: str, description: str, 
                      priority: int, estimated_duration_days: int,
                      required_resources: Dict[str, float]) -> Project:
        """Create a new project"""
        project_id = f"proj_{self.manager_id}_{len(self.projects)}"
        
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            status=ProjectStatus.PLANNED,
            priority=priority,
            created_at=datetime.utcnow(),
            estimated_duration_days=estimated_duration_days,
            required_resources=required_resources,
        )
        
        self.projects[project_id] = project
        logger.info(f"Created project: {name}")
        
        return project
    
    def assign_agents(self, project_id: str, agent_ids: List[str]):
        """Assign agents to a project"""
        if project_id in self.projects:
            self.projects[project_id].assigned_agents = agent_ids
            logger.info(f"Assigned {len(agent_ids)} agents to project {project_id}")
    
    def update_progress(self, project_id: str, progress: float):
        """Update project progress"""
        if project_id in self.projects:
            project = self.projects[project_id]
            project.progress = min(1.0, max(0.0, progress))
            
            # Auto-update status
            if project.progress >= 1.0 and project.status == ProjectStatus.IN_PROGRESS:
                project.status = ProjectStatus.TESTING
            
            self.project_history.append({
                'project_id': project_id,
                'progress': progress,
                'timestamp': datetime.utcnow(),
            })
    
    def complete_project(self, project_id: str, success: bool = True):
        """Mark project as completed"""
        if project_id in self.projects:
            project = self.projects[project_id]
            project.status = ProjectStatus.COMPLETED if success else ProjectStatus.FAILED
            project.progress = 1.0
            
            self.completed_projects.append(project)
            del self.projects[project_id]
            
            logger.info(f"Project {project_id} completed: {'success' if success else 'failed'}")
    
    def get_active_projects(self) -> List[Project]:
        """Get all active projects"""
        return list(self.projects.values())
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed project status"""
        if project_id in self.projects:
            project = self.projects[project_id]
            
            # Calculate estimated completion
            if project.progress > 0:
                days_elapsed = (datetime.utcnow() - project.created_at).days
                estimated_total_days = days_elapsed / project.progress
                estimated_completion = project.created_at + timedelta(days=estimated_total_days)
            else:
                estimated_completion = project.created_at + timedelta(days=project.estimated_duration_days)
            
            return {
                **project.to_dict(),
                'estimated_completion': estimated_completion.isoformat(),
                'days_elapsed': (datetime.utcnow() - project.created_at).days,
            }
        
        return None
    
    def prioritize_projects(self) -> List[Project]:
        """Prioritize projects based on value and urgency"""
        projects = list(self.projects.values())
        
        # Score based on priority, expected value, and progress
        def project_score(p: Project) -> float:
            priority_score = p.priority * 10
            value_score = p.expected_value
            urgency_score = 5 if p.progress > 0 else 0
            
            return priority_score + value_score + urgency_score
        
        return sorted(projects, key=project_score, reverse=True)


class PerformanceMonitor:
    """
    Performance monitor that tracks and evaluates all components.
    
    Monitors:
    - System performance metrics
    - Component health
    - Resource utilization
    - Error rates
    - Latency
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[Dict[str, Any]] = []
        self.component_health: Dict[str, str] = {}
        
    def record_metric(self, component_id: str, metric_name: str, 
                     value: float, threshold_min: Optional[float] = None,
                     threshold_max: Optional[float] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_id=f"{component_id}_{metric_name}_{datetime.utcnow().timestamp()}",
            component_id=component_id,
            metric_name=metric_name,
            value=value,
            timestamp=datetime.utcnow(),
            threshold_min=threshold_min,
            threshold_max=threshold_max,
        )
        
        key = f"{component_id}_{metric_name}"
        self.metrics[key].append(metric)
        
        # Check thresholds
        if not metric.is_within_bounds():
            self.alerts.append({
                'component_id': component_id,
                'metric_name': metric_name,
                'value': value,
                'threshold_min': threshold_min,
                'threshold_max': threshold_max,
                'timestamp': datetime.utcnow(),
                'severity': 'warning',
            })
    
    def get_component_metrics(self, component_id: str) -> Dict[str, Any]:
        """Get all metrics for a component"""
        component_metrics = {}
        
        for key, metrics in self.metrics.items():
            if key.startswith(component_id):
                metric_name = key.replace(f"{component_id}_", "")
                recent_metrics = list(metrics)[-100:]
                
                if recent_metrics:
                    component_metrics[metric_name] = {
                        'current': recent_metrics[-1].value,
                        'avg': np.mean([m.value for m in recent_metrics]),
                        'min': np.min([m.value for m in recent_metrics]),
                        'max': np.max([m.value for m in recent_metrics]),
                        'std': np.std([m.value for m in recent_metrics]),
                    }
        
        return component_metrics
    
    def evaluate_health(self, component_id: str) -> str:
        """Evaluate component health"""
        metrics = self.get_component_metrics(component_id)
        
        if not metrics:
            return "unknown"
        
        # Check for recent alerts
        recent_alerts = [a for a in self.alerts[-100:] 
                        if a['component_id'] == component_id]
        
        if len(recent_alerts) > 10:
            health = "critical"
        elif len(recent_alerts) > 5:
            health = "degraded"
        elif len(recent_alerts) > 0:
            health = "warning"
        else:
            health = "healthy"
        
        self.component_health[component_id] = health
        return health
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health"""
        health_counts = defaultdict(int)
        
        for component_id in set(k.split('_')[0] for k in self.metrics.keys()):
            health = self.evaluate_health(component_id)
            health_counts[health] += 1
        
        total_components = sum(health_counts.values())
        
        return {
            'total_components': total_components,
            'health_distribution': dict(health_counts),
            'healthy_percentage': health_counts['healthy'] / total_components if total_components > 0 else 0.0,
            'critical_components': health_counts['critical'],
            'recent_alerts': len([a for a in self.alerts[-100:]]),
        }
    
    def get_alerts(self, severity: Optional[str] = None, 
                   component_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get alerts with optional filtering"""
        alerts = self.alerts
        
        if severity:
            alerts = [a for a in alerts if a['severity'] == severity]
        
        if component_id:
            alerts = [a for a in alerts if a['component_id'] == component_id]
        
        return alerts


class ResourceEconomist:
    """
    Resource economist that optimizes capital and compute allocation.
    
    Optimizes:
    - Capital allocation across strategies
    - Compute resource distribution
    - Cost-benefit analysis
    - ROI maximization
    """
    
    def __init__(self, total_capital: float, config: Optional[Dict[str, Any]] = None):
        self.total_capital = total_capital
        self.config = config or {}
        self.allocations: Dict[str, Dict[str, float]] = {}
        self.allocation_history: deque = deque(maxlen=1000)
        self.performance_tracking: Dict[str, List[float]] = defaultdict(list)
        
    def allocate_capital(self, strategy_id: str, amount: float, 
                        expected_return: float, risk_score: float) -> bool:
        """Allocate capital to a strategy"""
        # Check if capital is available
        current_allocation = sum(a['amount'] for a in self.allocations.values())
        available = self.total_capital - current_allocation
        
        if amount > available:
            logger.warning(f"Insufficient capital for {strategy_id}: requested {amount}, available {available}")
            return False
        
        self.allocations[strategy_id] = {
            'amount': amount,
            'expected_return': expected_return,
            'risk_score': risk_score,
            'allocated_at': datetime.utcnow().isoformat(),
            'sharpe_estimate': expected_return / risk_score if risk_score > 0 else 0.0,
        }
        
        self.allocation_history.append({
            'strategy_id': strategy_id,
            'amount': amount,
            'timestamp': datetime.utcnow(),
        })
        
        logger.info(f"Allocated ${amount:,.2f} to {strategy_id}")
        return True
    
    def reallocate_capital(self) -> Dict[str, Any]:
        """Reallocate capital based on performance"""
        # Calculate performance scores
        performance_scores = {}
        
        for strategy_id, allocation in self.allocations.items():
            if strategy_id in self.performance_tracking:
                returns = self.performance_tracking[strategy_id]
                if returns:
                    avg_return = np.mean(returns)
                    volatility = np.std(returns) if len(returns) > 1 else 0.1
                    sharpe = avg_return / volatility if volatility > 0 else 0.0
                    performance_scores[strategy_id] = sharpe
                else:
                    performance_scores[strategy_id] = allocation['sharpe_estimate']
            else:
                performance_scores[strategy_id] = allocation['sharpe_estimate']
        
        # Reallocate using risk parity approach
        total_score = sum(max(0, s) for s in performance_scores.values())
        
        if total_score == 0:
            return {'reallocations': 0}
        
        reallocations = []
        
        for strategy_id, score in performance_scores.items():
            if score > 0:
                target_allocation = (score / total_score) * self.total_capital
                current_allocation = self.allocations[strategy_id]['amount']
                
                if abs(target_allocation - current_allocation) > self.total_capital * 0.05:
                    self.allocations[strategy_id]['amount'] = target_allocation
                    reallocations.append({
                        'strategy_id': strategy_id,
                        'old_allocation': current_allocation,
                        'new_allocation': target_allocation,
                    })
        
        return {
            'reallocations': len(reallocations),
            'details': reallocations,
        }
    
    def record_performance(self, strategy_id: str, return_pct: float):
        """Record strategy performance"""
        self.performance_tracking[strategy_id].append(return_pct)
    
    def get_allocation_summary(self) -> Dict[str, Any]:
        """Get capital allocation summary"""
        total_allocated = sum(a['amount'] for a in self.allocations.values())
        
        return {
            'total_capital': self.total_capital,
            'total_allocated': total_allocated,
            'available': self.total_capital - total_allocated,
            'utilization': total_allocated / self.total_capital if self.total_capital > 0 else 0.0,
            'num_strategies': len(self.allocations),
            'allocations': {
                strategy_id: {
                    'amount': alloc['amount'],
                    'percentage': alloc['amount'] / self.total_capital if self.total_capital > 0 else 0.0,
                    'expected_return': alloc['expected_return'],
                    'risk_score': alloc['risk_score'],
                }
                for strategy_id, alloc in self.allocations.items()
            },
        }


class StrategyPortfolioManager:
    """
    Strategy portfolio manager that balances risk across autonomous strategies.
    
    Manages:
    - Strategy diversification
    - Risk budgeting
    - Correlation management
    - Performance attribution
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.strategies: Dict[str, Dict[str, Any]] = {}
        self.correlation_matrix: Dict[Tuple[str, str], float] = {}
        self.risk_budget = {
            'max_portfolio_var': 0.02,  # 2% daily VaR
            'max_strategy_weight': 0.30,  # 30% max per strategy
            'min_strategies': 3,
            'max_correlation': 0.7,
        }
        
    def add_strategy(self, strategy_id: str, strategy_type: str,
                    expected_return: float, volatility: float,
                    max_drawdown: float):
        """Add a strategy to the portfolio"""
        self.strategies[strategy_id] = {
            'strategy_type': strategy_type,
            'expected_return': expected_return,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'weight': 0.0,
            'active': True,
            'sharpe_ratio': expected_return / volatility if volatility > 0 else 0.0,
        }
        
        logger.info(f"Added strategy {strategy_id} to portfolio")
    
    def update_correlation(self, strategy1: str, strategy2: str, correlation: float):
        """Update correlation between strategies"""
        self.correlation_matrix[(strategy1, strategy2)] = correlation
        self.correlation_matrix[(strategy2, strategy1)] = correlation
    
    def optimize_weights(self) -> Dict[str, float]:
        """Optimize strategy weights"""
        if len(self.strategies) < self.risk_budget['min_strategies']:
            logger.warning("Insufficient strategies for optimization")
            return {}
        
        # Simple equal-weight with Sharpe adjustment
        sharpe_ratios = {sid: s['sharpe_ratio'] for sid, s in self.strategies.items() if s['active']}
        
        if not sharpe_ratios:
            return {}
        
        total_sharpe = sum(max(0, s) for s in sharpe_ratios.values())
        
        if total_sharpe == 0:
            # Equal weight
            weight = 1.0 / len(sharpe_ratios)
            weights = {sid: weight for sid in sharpe_ratios}
        else:
            # Sharpe-weighted
            weights = {
                sid: max(0, sharpe) / total_sharpe
                for sid, sharpe in sharpe_ratios.items()
            }
        
        # Apply max weight constraint
        for sid, weight in weights.items():
            weights[sid] = min(weight, self.risk_budget['max_strategy_weight'])
        
        # Renormalize
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {sid: w / total_weight for sid, w in weights.items()}
        
        # Update strategy weights
        for sid, weight in weights.items():
            self.strategies[sid]['weight'] = weight
        
        return weights
    
    def calculate_portfolio_risk(self) -> Dict[str, float]:
        """Calculate portfolio risk metrics"""
        active_strategies = {sid: s for sid, s in self.strategies.items() if s['active']}
        
        if not active_strategies:
            return {'portfolio_volatility': 0.0, 'portfolio_var': 0.0}
        
        # Calculate weighted volatility
        portfolio_variance = 0.0
        
        for sid1, s1 in active_strategies.items():
            for sid2, s2 in active_strategies.items():
                w1 = s1['weight']
                w2 = s2['weight']
                vol1 = s1['volatility']
                vol2 = s2['volatility']
                
                if sid1 == sid2:
                    correlation = 1.0
                else:
                    correlation = self.correlation_matrix.get((sid1, sid2), 0.3)
                
                portfolio_variance += w1 * w2 * vol1 * vol2 * correlation
        
        portfolio_volatility = np.sqrt(portfolio_variance)
        portfolio_var = portfolio_volatility * 1.65  # 95% VaR
        
        return {
            'portfolio_volatility': portfolio_volatility,
            'portfolio_var': portfolio_var,
            'within_risk_budget': portfolio_var <= self.risk_budget['max_portfolio_var'],
        }
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get portfolio summary"""
        active_strategies = {sid: s for sid, s in self.strategies.items() if s['active']}
        
        risk_metrics = self.calculate_portfolio_risk()
        
        return {
            'total_strategies': len(self.strategies),
            'active_strategies': len(active_strategies),
            'strategy_weights': {sid: s['weight'] for sid, s in active_strategies.items()},
            'expected_portfolio_return': sum(s['expected_return'] * s['weight'] 
                                            for s in active_strategies.values()),
            'risk_metrics': risk_metrics,
            'risk_budget': self.risk_budget,
        }
