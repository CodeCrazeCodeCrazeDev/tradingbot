"""
Health check REST endpoints for monitoring
"""

import logging
from typing import Dict
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import psutil

logger = logging.getLogger(__name__)


class HealthEndpoints:
    """
    REST API endpoints for health monitoring.
    """
    
    def __init__(self, app: FastAPI, system_components: Dict):
        self.app = app
        self.components = system_components
        
        # Register endpoints
        self._register_endpoints()
        
        logger.info("✅ Health endpoints registered")
    
    def _register_endpoints(self):
        """Register health check endpoints."""
        
        @self.app.get("/health")
        async def health_check():
            """Basic health check."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "AlphaAlgo 2.0"
            }
        
        @self.app.get("/health/detailed")
        async def detailed_health():
            """Detailed health check with component status."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "components": {}
                }
                
                # Check each component
                for name, component in self.components.items():
                    try:
                        if hasattr(component, 'get_health'):
                            component_health = component.get_health()
                        else:
                            component_health = {"status": "unknown"}
                        
                        status["components"][name] = component_health
                    except Exception as e:
                        status["components"][name] = {
                            "status": "unhealthy",
                            "error": str(e)
                        }
                        status["status"] = "degraded"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/system")
        async def system_health():
            """System resource health check."""
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                
                # Memory usage
                memory = psutil.virtual_memory()
                
                # Disk usage
                disk = psutil.disk_usage('/')
                
                # Network
                net_io = psutil.net_io_counters()
                
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "cpu": {
                            "usage_percent": cpu_percent,
                            "count": psutil.cpu_count(),
                            "status": "healthy" if cpu_percent < 80 else "warning"
                        },
                        "memory": {
                            "total_gb": memory.total / (1024**3),
                            "available_gb": memory.available / (1024**3),
                            "used_percent": memory.percent,
                            "status": "healthy" if memory.percent < 80 else "warning"
                        },
                        "disk": {
                            "total_gb": disk.total / (1024**3),
                            "free_gb": disk.free / (1024**3),
                            "used_percent": disk.percent,
                            "status": "healthy" if disk.percent < 80 else "warning"
                        },
                        "network": {
                            "bytes_sent": net_io.bytes_sent,
                            "bytes_recv": net_io.bytes_recv,
                            "packets_sent": net_io.packets_sent,
                            "packets_recv": net_io.packets_recv
                        }
                    }
                }
                
                # Overall status
                if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                    status["status"] = "critical"
                elif cpu_percent > 80 or memory.percent > 80 or disk.percent > 80:
                    status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ System health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/trading")
        async def trading_health():
            """Trading system health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "trading": {}
                }
                
                # Check position manager
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    summary = pm.get_position_summary()
                    
                    status["trading"]["positions"] = {
                        "count": summary['num_positions'],
                        "total_exposure": summary['total_exposure'],
                        "current_capital": summary['current_capital'],
                        "return_pct": summary['return_pct'],
                        "status": "healthy" if summary['num_positions'] < 10 else "warning"
                    }
                
                # Check execution engine
                if 'execution_engine' in self.components:
                    ee = self.components['execution_engine']
                    if hasattr(ee, 'get_stats'):
                        exec_stats = ee.get_stats()
                        status["trading"]["execution"] = exec_stats
                
                # Check broker connection
                if 'broker' in self.components:
                    broker = self.components['broker']
                    if hasattr(broker, 'is_connected'):
                        connected = broker.is_connected()
                        status["trading"]["broker"] = {
                            "connected": connected,
                            "status": "healthy" if connected else "critical"
                        }
                        
                        if not connected:
                            status["status"] = "critical"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Trading health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/ml")
        async def ml_health():
            """Machine learning system health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "ml": {}
                }
                
                # Check model status
                if 'ml_pipeline' in self.components:
                    pipeline = self.components['ml_pipeline']
                    if hasattr(pipeline, 'get_model_status'):
                        model_status = pipeline.get_model_status()
                        status["ml"]["models"] = model_status
                
                # Check prediction latency
                if 'predictor' in self.components:
                    predictor = self.components['predictor']
                    if hasattr(predictor, 'get_latency_stats'):
                        latency = predictor.get_latency_stats()
                        status["ml"]["latency"] = latency
                        
                        if latency.get('avg_ms', 0) > 1000:
                            status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ ML health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/data")
        async def data_health():
            """Data pipeline health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "data": {}
                }
                
                # Check market data stream
                if 'market_data' in self.components:
                    md = self.components['market_data']
                    if hasattr(md, 'get_stream_status'):
                        stream_status = md.get_stream_status()
                        status["data"]["stream"] = stream_status
                        
                        if not stream_status.get('connected', False):
                            status["status"] = "critical"
                
                # Check data quality
                if 'data_validator' in self.components:
                    validator = self.components['data_validator']
                    if hasattr(validator, 'get_quality_metrics'):
                        quality = validator.get_quality_metrics()
                        status["data"]["quality"] = quality
                        
                        if quality.get('error_rate', 0) > 0.05:
                            status["status"] = "warning"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Data health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/health/risk")
        async def risk_health():
            """Risk management health check."""
            try:
                status = {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "risk": {}
                }
                
                # Check risk metrics
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    metrics = pm.portfolio_metrics
                    
                    status["risk"]["metrics"] = {
                        "total_exposure": metrics['total_exposure'],
                        "total_risk": metrics['total_risk'],
                        "sharpe_ratio": metrics['sharpe_ratio'],
                        "max_drawdown": metrics['max_drawdown']
                    }
                    
                    # Check thresholds
                    if metrics['max_drawdown'] > 0.15:
                        status["status"] = "critical"
                    elif metrics['max_drawdown'] > 0.10:
                        status["status"] = "warning"
                
                # Check compliance
                if 'compliance_monitor' in self.components:
                    cm = self.components['compliance_monitor']
                    if hasattr(cm, 'get_summary'):
                        compliance = cm.get_summary()
                        status["risk"]["compliance"] = compliance
                        
                        if compliance.get('by_severity', {}).get('CRITICAL', 0) > 0:
                            status["status"] = "critical"
                
                return status
                
            except Exception as e:
                logger.error(f"❌ Risk health check error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/metrics")
        async def metrics():
            """Prometheus-style metrics endpoint."""
            try:
                metrics_text = []
                
                # System metrics
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                
                metrics_text.append(f"# HELP system_cpu_usage_percent CPU usage percentage")
                metrics_text.append(f"# TYPE system_cpu_usage_percent gauge")
                metrics_text.append(f"system_cpu_usage_percent {cpu_percent}")
                
                metrics_text.append(f"# HELP system_memory_usage_percent Memory usage percentage")
                metrics_text.append(f"# TYPE system_memory_usage_percent gauge")
                metrics_text.append(f"system_memory_usage_percent {memory.percent}")
                
                # Trading metrics
                if 'position_manager' in self.components:
                    pm = self.components['position_manager']
                    summary = pm.get_position_summary()
                    
                    metrics_text.append(f"# HELP trading_positions_count Number of open positions")
                    metrics_text.append(f"# TYPE trading_positions_count gauge")
                    metrics_text.append(f"trading_positions_count {summary['num_positions']}")
                    
                    metrics_text.append(f"# HELP trading_capital_current Current trading capital")
                    metrics_text.append(f"# TYPE trading_capital_current gauge")
                    metrics_text.append(f"trading_capital_current {summary['current_capital']}")
                
                return JSONResponse(
                    content="\n".join(metrics_text),
                    media_type="text/plain"
                )
                
            except Exception as e:
                logger.error(f"❌ Metrics error: {e}")
                raise HTTPException(status_code=500, detail=str(e))
