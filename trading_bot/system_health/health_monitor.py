"""
from typing import Set
AlphaAlgo System Health Monitor
Comprehensive diagnostics, auto-repair, and validation system.
"""

import logging
import psutil
import time
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"


class ComponentStatus(Enum):
    """Individual component status."""
    STABLE = "stable"
    UNSTABLE = "unstable"
    FAILED = "failed"
    REPAIRING = "repairing"


class SystemHealthMonitor:
    """
    PHASE 1: System Diagnostics
    Scans all critical components and detects issues.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize health monitor."""
        self.config = config
        self.diagnostics_log = []
        self.auto_fixes_log = []
        
        # Thresholds
        self.max_latency_ms = config.get('max_latency_ms', 100)
        self.max_cpu_percent = config.get('max_cpu_percent', 90)
        self.min_memory_mb = config.get('min_memory_mb', 500)
        self.min_system_health = config.get('min_system_health', 95)
        
        # Paths
        self.log_dir = Path(config.get('log_dir', 'diagnostics/system_health'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("SystemHealthMonitor initialized")
    
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        PHASE 1: Complete system diagnostics.
        
        Returns:
            Diagnostic report with all findings
        """
        timestamp = datetime.now()
        logger.info("=" * 80)
        logger.info(f"PHASE 1: SYSTEM DIAGNOSTICS - {timestamp}")
        logger.info("=" * 80)
        
        diagnostics = {
            'timestamp': timestamp,
            'components': {},
            'system_resources': {},
            'issues': [],
            'overall_health': 100.0
        }
        
        # Check system resources
        logger.info("Checking system resources...")
        diagnostics['system_resources'] = await self._check_system_resources()
        
        # Check all components
        logger.info("Scanning all modules...")
        
        components = [
            'system_validator',
            'risk_manager',
            'elite_brain',
            'ml_models',
            'data_feed',
            'order_executor'
        ]
        
        for component in components:
            logger.info(f"  Checking {component}...")
            result = await self._check_component(component)
            diagnostics['components'][component] = result
            
            if result['status'] != ComponentStatus.STABLE:
                diagnostics['issues'].extend(result['issues'])
        
        # Calculate overall health
        diagnostics['overall_health'] = self._calculate_overall_health(diagnostics)
        
        # Log diagnostics
        self._log_diagnostics(diagnostics)
        
        logger.info(f"\nDiagnostics complete: {len(diagnostics['issues'])} issues found")
        logger.info(f"Overall system health: {diagnostics['overall_health']:.1f}%")
        
        return diagnostics
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check CPU, memory, disk, and network."""
        resources = {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'issues': []
        }
        
        # Check CPU
        if resources['cpu_percent'] > self.max_cpu_percent:
            resources['issues'].append({
                'type': 'high_cpu',
                'severity': 'critical',
                'value': resources['cpu_percent'],
                'threshold': self.max_cpu_percent,
                'message': f"CPU usage {resources['cpu_percent']:.1f}% exceeds {self.max_cpu_percent}%"
            })
        
        # Check memory
        if resources['memory_available_mb'] < self.min_memory_mb:
            resources['issues'].append({
                'type': 'low_memory',
                'severity': 'critical',
                'value': resources['memory_available_mb'],
                'threshold': self.min_memory_mb,
                'message': f"Available memory {resources['memory_available_mb']:.0f}MB below {self.min_memory_mb}MB"
            })
        
        # Check disk
        if resources['disk_percent'] > 95:
            resources['issues'].append({
                'type': 'low_disk',
                'severity': 'warning',
                'value': resources['disk_percent'],
                'threshold': 95,
                'message': f"Disk usage {resources['disk_percent']:.1f}% critical"
            })
        
        return resources
    
    async def _check_component(self, component_name: str) -> Dict[str, Any]:
        """Check individual component health."""
        result = {
            'name': component_name,
            'status': ComponentStatus.STABLE,
            'issues': [],
            'metrics': {}
        }
        
        try:
            # Check if component can be imported
            if component_name == 'system_validator':
                result['metrics'] = await self._check_system_validator()
            
            elif component_name == 'risk_manager':
                result['metrics'] = await self._check_risk_manager()
            
            elif component_name == 'elite_brain':
                result['metrics'] = await self._check_elite_brain()
            
            elif component_name == 'ml_models':
                result['metrics'] = await self._check_ml_models()
            
            elif component_name == 'data_feed':
                result['metrics'] = await self._check_data_feed()
            
            elif component_name == 'order_executor':
                result['metrics'] = await self._check_order_executor()
            
            # Analyze metrics for issues
            if result['metrics'].get('latency_ms', 0) > self.max_latency_ms:
                result['issues'].append({
                    'type': 'high_latency',
                    'severity': 'warning',
                    'value': result['metrics']['latency_ms'],
                    'message': f"Latency {result['metrics']['latency_ms']}ms exceeds {self.max_latency_ms}ms"
                })
            
            if result['metrics'].get('import_failed'):
                result['issues'].append({
                    'type': 'import_failed',
                    'severity': 'critical',
                    'message': f"Failed to import {component_name}"
                })
                result['status'] = ComponentStatus.FAILED
            
            if result['metrics'].get('null_objects'):
                result['issues'].append({
                    'type': 'null_objects',
                    'severity': 'critical',
                    'message': f"Null objects detected in {component_name}"
                })
                result['status'] = ComponentStatus.FAILED
            
            if result['metrics'].get('missing_files'):
                result['issues'].append({
                    'type': 'missing_files',
                    'severity': 'critical',
                    'files': result['metrics']['missing_files'],
                    'message': f"Missing files in {component_name}"
                })
                result['status'] = ComponentStatus.FAILED
            
            # Set status based on issues
            if result['issues']:
                critical_issues = [i for i in result['issues'] if i['severity'] == 'critical']
                if critical_issues:
                    result['status'] = ComponentStatus.FAILED
                else:
                    result['status'] = ComponentStatus.UNSTABLE
        
        except Exception as e:
            logger.error(f"Error checking {component_name}: {e}")
            result['status'] = ComponentStatus.FAILED
            result['issues'].append({
                'type': 'check_failed',
                'severity': 'critical',
                'message': f"Health check failed: {str(e)}"
            })
        
        return result
    
    async def _check_system_validator(self) -> Dict[str, Any]:
        """Check system validator component."""
        metrics = {'latency_ms': 0, 'import_failed': False}
        
        try:
            start = time.time()
            # Try to import and instantiate
            from trading_bot.validation import ComprehensiveValidator
            validator = ComprehensiveValidator({})
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['initialized'] = True
        except Exception as e:
            logger.error(f"System validator check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    async def _check_risk_manager(self) -> Dict[str, Any]:
        """Check risk manager component."""
        metrics = {'latency_ms': 0, 'import_failed': False}
        
        try:
            start = time.time()
            from trading_bot.risk import AdvancedRiskManager
            risk_mgr = AdvancedRiskManager({})
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['initialized'] = True
            
            # Check for null objects
            if risk_mgr is None:
                metrics['null_objects'] = True
        
        except Exception as e:
            logger.error(f"Risk manager check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    async def _check_elite_brain(self) -> Dict[str, Any]:
        """Check elite brain component."""
        metrics = {'latency_ms': 0, 'import_failed': False}
        
        try:
            start = time.time()
            from trading_bot.brain import EliteBrain
            brain = EliteBrain({})
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['initialized'] = True
            
            # Check components
            if brain.self_improvement is None:
                metrics['self_improvement_disabled'] = True
        
        except Exception as e:
            logger.error(f"Elite brain check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    async def _check_ml_models(self) -> Dict[str, Any]:
        """Check ML models."""
        metrics = {'latency_ms': 0, 'import_failed': False, 'missing_files': []}
        
        try:
            start = time.time()
            
            # Check for model files
            model_dir = Path('models')
            if not model_dir.exists():
                metrics['missing_files'].append('models directory')
            
            # Try to import ML components
            from trading_bot.ml import OnlineLearner
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['initialized'] = True
        
        except Exception as e:
            logger.error(f"ML models check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    async def _check_data_feed(self) -> Dict[str, Any]:
        """Check data feed component."""
        metrics = {'latency_ms': 0, 'import_failed': False}
        
        try:
            start = time.time()
            # Simulate data feed check
            # In production, actually test connection
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['connected'] = True
        
        except Exception as e:
            logger.error(f"Data feed check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    async def _check_order_executor(self) -> Dict[str, Any]:
        """Check order executor component."""
        metrics = {'latency_ms': 0, 'import_failed': False}
        
        try:
            start = time.time()
            from trading_bot.execution import SmartOrderExecutor
            executor = SmartOrderExecutor({})
            metrics['latency_ms'] = (time.time() - start) * 1000
            metrics['initialized'] = True
        
        except Exception as e:
            logger.error(f"Order executor check failed: {e}")
            metrics['import_failed'] = True
            metrics['error'] = str(e)
        
        return metrics
    
    def _calculate_overall_health(self, diagnostics: Dict[str, Any]) -> float:
        """Calculate overall system health percentage."""
        total_score = 100.0
        
        # Deduct for system resource issues
        for issue in diagnostics['system_resources'].get('issues', []):
            if issue['severity'] == 'critical':
                total_score -= 20
            elif issue['severity'] == 'warning':
                total_score -= 5
        
        # Deduct for component issues
        for component, result in diagnostics['components'].items():
            if result['status'] == ComponentStatus.FAILED:
                total_score -= 15
            elif result['status'] == ComponentStatus.UNSTABLE:
                total_score -= 5
        
        return max(0.0, total_score)
    
    def _log_diagnostics(self, diagnostics: Dict[str, Any]):
        """Log diagnostics to file."""
        log_file = self.log_dir / f"diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to JSON-serializable format
        log_data = {
            'timestamp': diagnostics['timestamp'].isoformat(),
            'overall_health': diagnostics['overall_health'],
            'system_resources': diagnostics['system_resources'],
            'components': {
                name: {
                    'status': result['status'].value,
                    'issues': result['issues'],
                    'metrics': result['metrics']
                }
                for name, result in diagnostics['components'].items()
            },
            'issues': diagnostics['issues']
        }
        
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2, default=str)
        
        logger.info(f"Diagnostics logged to {log_file}")
