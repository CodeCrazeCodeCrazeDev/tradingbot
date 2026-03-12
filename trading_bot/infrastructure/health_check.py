"""
Phase 8: Production Deployment - Health Checks
System health monitoring and diagnostics
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import psutil
import requests
import json
import os

logger = logging.getLogger(__name__)


class HealthCheck:
    """
    System health monitoring and diagnostics.
    Checks various components for proper operation.
    """
    
    def __init__(
        self,
        check_interval: int = 60,  # seconds
        history_size: int = 1000
    ):
        # Component status
        self.components = {
            'data_feed': {
                'status': 'unknown',
                'last_check': None,
                'error': None
            },
            'model': {
                'status': 'unknown',
                'last_check': None,
                'error': None
            },
            'database': {
                'status': 'unknown',
                'last_check': None,
                'error': None
            },
            'api': {
                'status': 'unknown',
                'last_check': None,
                'error': None
            },
            'trading': {
                'status': 'unknown',
                'last_check': None,
                'error': None
            }
        }
        
        # Health check history
        self.history = []
        self.history_size = history_size
        
        # Check interval
        self.check_interval = check_interval
        self.last_check = None
        
        # Overall system status
        self.is_healthy = False
        
        logger.info("✅ Health Check initialized")
        logger.info(f"   Check interval: {check_interval}s")
        logger.info(f"   History size: {history_size}")
    
    def check_all(self) -> Dict:
        """
        Run all health checks.
        
        Returns:
            Dictionary with check results
        """
        now = datetime.now()
        
        # Check interval
        if (self.last_check and 
            (now - self.last_check).total_seconds() < self.check_interval):
            return self.get_status()
        
        # Run component checks
        results = {
            'data_feed': self._check_data_feed(),
            'model': self._check_model(),
            'database': self._check_database(),
            'api': self._check_api(),
            'trading': self._check_trading()
        }
        
        # Update component status
        for component, result in results.items():
            self.components[component].update(result)
        
        # Update overall health
        self.is_healthy = all(
            comp['status'] == 'healthy'
            for comp in self.components.values()
        )
        
        # Record check
        self.last_check = now
        self.history.append({
            'timestamp': now,
            'is_healthy': self.is_healthy,
            'components': {
                name: comp.copy()
                for name, comp in self.components.items()
            }
        })
        
        # Trim history
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        return self.get_status()
    
    def _check_data_feed(self) -> Dict:
        """Check market data feed."""
        try:
            # Example: Check if recent data exists
            last_update = self._get_last_data_update()
            
            if last_update is None:
                return {
                    'status': 'error',
                    'last_check': datetime.now(),
                    'error': 'No data feed found'
                }
            
            # Check if data is stale
            if datetime.now() - last_update > timedelta(minutes=5):
                return {
                    'status': 'warning',
                    'last_check': datetime.now(),
                    'error': 'Data feed may be stale'
                }
            
            return {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def _check_model(self) -> Dict:
        """Check ML model status."""
        try:
            # Example: Check if model is loaded and responding
            if not self._is_model_loaded():
                return {
                    'status': 'error',
                    'last_check': datetime.now(),
                    'error': 'Model not loaded'
                }
            
            # Check prediction latency
            latency = self._check_model_latency()
            if latency > 1000:  # >1s is too slow
                return {
                    'status': 'warning',
                    'last_check': datetime.now(),
                    'error': f'High prediction latency: {latency}ms'
                }
            
            return {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def _check_database(self) -> Dict:
        """Check database connection."""
        try:
            # Example: Check database connection
            if not self._test_db_connection():
                return {
                    'status': 'error',
                    'last_check': datetime.now(),
                    'error': 'Database connection failed'
                }
            
            return {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def _check_api(self) -> Dict:
        """Check API endpoints."""
        try:
            # Example: Check API health
            endpoints = [
                'http://localhost:8000/health',
                'http://localhost:8000/status'
            ]
            
            for endpoint in endpoints:
                response = requests.get(endpoint, timeout=5)
                if response.status_code != 200:
                    return {
                        'status': 'error',
                        'last_check': datetime.now(),
                        'error': f'API endpoint {endpoint} returned {response.status_code}'
                    }
            
            return {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def _check_trading(self) -> Dict:
        """Check trading system."""
        try:
            # Example: Check trading status
            if not self._is_trading_active():
                return {
                    'status': 'warning',
                    'last_check': datetime.now(),
                    'error': 'Trading system inactive'
                }
            
            # Check for failed trades
            failed = self._get_failed_trades()
            if failed > 5:  # Too many failed trades
                return {
                    'status': 'error',
                    'last_check': datetime.now(),
                    'error': f'High trade failure rate: {failed} failed trades'
                }
            
            return {
                'status': 'healthy',
                'last_check': datetime.now(),
                'error': None
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'last_check': datetime.now(),
                'error': str(e)
            }
    
    def _get_last_data_update(self) -> Optional[datetime]:
        """Get timestamp of last data update."""
        # Implement actual check
        return datetime.now()  # Placeholder
    
    def _is_model_loaded(self) -> bool:
        """Check if model is loaded."""
        # Implement actual check
        return True  # Placeholder
    
    def _check_model_latency(self) -> float:
        """Check model prediction latency."""
        # Implement actual check
        return 50.0  # Placeholder
    
    def _test_db_connection(self) -> bool:
        """Test database connection."""
        # Implement actual check
        return True  # Placeholder
    
    def _is_trading_active(self) -> bool:
        """Check if trading system is active."""
        # Implement actual check
        return True  # Placeholder
    
    def _get_failed_trades(self) -> int:
        """Get number of failed trades."""
        # Implement actual check
        return 0  # Placeholder
    
    def get_status(self) -> Dict:
        """Get current system status."""
        return {
            'is_healthy': self.is_healthy,
            'last_check': self.last_check,
            'components': self.components,
            'system_resources': self._get_system_resources()
        }
    
    def _get_system_resources(self) -> Dict:
        """Get system resource usage."""
        return {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }
    
    def get_component_history(
        self,
        component: str,
        window: timedelta = timedelta(hours=1)
    ) -> List[Dict]:
        """
        Get history for specific component.
        
        Args:
            component: Component name
            window: Time window
        """
        if not self.history:
            return []
        
        cutoff = datetime.now() - window
        return [
            {
                'timestamp': h['timestamp'],
                'status': h['components'][component]['status'],
                'error': h['components'][component]['error']
            }
            for h in self.history
            if h['timestamp'] > cutoff
        ]
    
    def generate_health_report(self) -> str:
        """Generate detailed health report."""
        status = self.get_status()
        
        report = [
            "SYSTEM HEALTH REPORT",
            "=" * 50,
            f"\nOverall Status: {'✅ HEALTHY' if status['is_healthy'] else '❌ UNHEALTHY'}",
            f"Last Check: {status['last_check']}",
            
            "\nCOMPONENT STATUS:"
        ]
        
        for name, comp in status['components'].items():
            icon = "✅" if comp['status'] == 'healthy' else "⚠️" if comp['status'] == 'warning' else "❌"
            report.append(f"{icon} {name}: {comp['status']}")
            if comp['error']:
                report.append(f"   Error: {comp['error']}")
        
        report.extend([
            "\nSYSTEM RESOURCES:",
            f"CPU Usage: {status['system_resources']['cpu']}%",
            f"Memory Usage: {status['system_resources']['memory']}%",
            f"Disk Usage: {status['system_resources']['disk']}%"
        ])
        
        return "\n".join(report)
    
    def save_state(self, filepath: str):
        """Save health check state."""
        state = {
            'components': self.components,
            'history': self.history,
            'last_check': self.last_check,
            'is_healthy': self.is_healthy
        }
        torch.save(state, filepath)
        logger.info(f"💾 Health Check state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load health check state."""
        state = torch.load(filepath)
        
        self.components = state['components']
        self.history = state['history']
        self.last_check = state['last_check']
        self.is_healthy = state['is_healthy']
        
        logger.info(f"📂 Health Check state loaded from {filepath}")
        logger.info(f"   History samples: {len(self.history)}")
        logger.info(f"   System healthy: {self.is_healthy}")
