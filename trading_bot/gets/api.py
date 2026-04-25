"""
GETS REST API

FastAPI-based REST API for GETS:
- Signal generation endpoints
- Health checks
- Metrics export
- Configuration management
- Champion promotion
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import asdict

logger = logging.getLogger(__name__)

# FastAPI imports (commented if not installed)
try:
    from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
    from fastapi.responses import JSONResponse, PlainTextResponse
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    logger.warning("FastAPI not installed. API module will not function.")

from .types import MarketData, GETSSignal, ForecastHorizon, GETSConfig
from .gets_system import GETS
from .integration import MarketDataAdapter


if HAS_FASTAPI:
    
    class SignalRequest(BaseModel):
        """Request model for signal generation."""
        symbol: str
        price: float
        open: Optional[float] = None
        high: Optional[float] = None
        low: Optional[float] = None
        volume: Optional[float] = 0
        spread: Optional[float] = 0.001
        volatility: Optional[float] = 0.2
        horizon: str = "SHORT"  # IMMEDIATE, SHORT, MEDIUM, LONG, EXTENDED
    
    
    class SignalResponse(BaseModel):
        """Response model for signal generation."""
        symbol: str
        direction: int
        confidence: float
        expected_edge: float
        governance_decision: str
        abstain_recommended: bool
        abstain_reason: Optional[str]
        uncertainty_low: float
        uncertainty_high: float
        timestamp: str
    
    
    class HealthResponse(BaseModel):
        """Health check response."""
        status: str
        timestamp: str
        layers: Dict[str, Any]
    
    
    class MetricsResponse(BaseModel):
        """Metrics response."""
        counters: Dict[str, float]
        gauges: Dict[str, float]
        histograms: Dict[str, Dict[str, float]]
    
    
    def create_gets_api(gets_instance: Optional[GETS] = None) -> FastAPI:
        """
        Create FastAPI application for GETS.
        
        Args:
            gets_instance: Pre-initialized GETS instance, or None to create new
            
        Returns:
            Configured FastAPI application
        """
        app = FastAPI(
            title="GETS API",
            description="Governed Evolving Time-Series Foundation System API",
            version="0.1.0"
        )
        
        # Store GETS instance in app state
        if gets_instance:
            app.state.gets = gets_instance
        else:
            app.state.gets = None
        
        @app.on_event("startup")
        async def startup():
            """Initialize GETS on startup."""
            if app.state.gets is None:
                app.state.gets = GETS()
            
            if not app.state.gets._initialized:
                success = app.state.gets.initialize()
                if not success:
                    logger.error("Failed to initialize GETS on startup")
        
        @app.on_event("shutdown")
        async def shutdown():
            """Shutdown GETS gracefully."""
            if app.state.gets and app.state.gets._initialized:
                app.state.gets.shutdown()
        
        @app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint."""
            return {
                "name": "GETS API",
                "version": "0.1.0",
                "description": "Governed Evolving Time-Series Foundation System"
            }
        
        @app.post("/signal", response_model=SignalResponse)
        async def generate_signal(request: SignalRequest):
            """
            Generate trading signal from market data.
            
            This endpoint processes market data through all 5 layers:
            1. Temporal Perception - Foundation model inference
            2. Forecast & Representation - Trading-native heads
            3. Self-Diagnosis - Disagreement geometry and introspection
            4. Governance Decision - Final approval/rejection
            """
            if not app.state.gets or not app.state.gets._initialized:
                raise HTTPException(status_code=503, detail="GETS not initialized")
            
            # Create market data
            market_data = MarketData(
                symbol=request.symbol,
                timestamp=datetime.now(),
                ohlcv={
                    'open': request.open or request.price,
                    'high': request.high or request.price,
                    'low': request.low or request.price,
                    'close': request.price,
                    'volume': request.volume or 0
                },
                bid_ask_spread=request.spread,
                realized_volatility=request.volatility
            )
            
            # Parse horizon
            horizon_map = {
                "IMMEDIATE": ForecastHorizon.IMMEDIATE,
                "SHORT": ForecastHorizon.SHORT,
                "MEDIUM": ForecastHorizon.MEDIUM,
                "LONG": ForecastHorizon.LONG,
                "EXTENDED": ForecastHorizon.EXTENDED
            }
            horizon = horizon_map.get(request.horizon.upper(), ForecastHorizon.SHORT)
            
            # Generate signal
            signal = app.state.gets.generate_signal(market_data, horizon)
            
            # Convert to response
            return SignalResponse(
                symbol=signal.symbol,
                direction=signal.direction,
                confidence=signal.confidence,
                expected_edge=signal.expected_edge,
                governance_decision=signal.governance_decision.name,
                abstain_recommended=signal.abstain_recommended,
                abstain_reason=signal.abstain_reason,
                uncertainty_low=signal.uncertainty_quantile_05,
                uncertainty_high=signal.uncertainty_quantile_95,
                timestamp=signal.timestamp.isoformat()
            )
        
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """
            Comprehensive health check of all GETS layers.
            """
            if not app.state.gets:
                raise HTTPException(status_code=503, detail="GETS not available")
            
            status = app.state.gets.get_system_status()
            
            overall = "HEALTHY"
            if any(v == "ERROR" or v == "NOT_INITIALIZED" for v in status.values()):
                overall = "DEGRADED"
            if all(v == "NOT_INITIALIZED" for v in status.values()):
                overall = "CRITICAL"
            
            return HealthResponse(
                status=overall,
                timestamp=datetime.now().isoformat(),
                layers=status
            )
        
        @app.get("/metrics")
        async def get_metrics(format: str = Query("json", enum=["json", "prometheus"])):
            """
            Get system metrics.
            
            Args:
                format: Output format (json or prometheus)
            """
            if not app.state.gets or not hasattr(app.state.gets, '_metrics'):
                raise HTTPException(status_code=503, detail="Metrics not available")
            
            # This would integrate with the monitoring module
            if format == "prometheus":
                # Return Prometheus format
                return PlainTextResponse(
                    content="# GETS metrics\ngets_up 1\n",
                    media_type="text/plain"
                )
            
            return MetricsResponse(
                counters={},
                gauges={},
                histograms={}
            )
        
        @app.get("/status")
        async def system_status():
            """
            Get detailed system status.
            """
            if not app.state.gets:
                raise HTTPException(status_code=503, detail="GETS not available")
            
            status = {
                "initialized": app.state.gets._initialized,
                "config": {
                    "kronos_enabled": app.state.gets.config.kronos_enabled,
                    "timesfm_enabled": app.state.gets.config.timesfm_enabled,
                    "moirai_enabled": app.state.gets.config.moirai_enabled,
                    "ttm_enabled": app.state.gets.config.ttm_enabled,
                },
                "layers": {
                    "layer1": app.state.gets.layer1_perception is not None,
                    "layer2": app.state.gets.layer2_representation is not None,
                    "layer3": app.state.gets.layer3_diagnosis is not None,
                    "layer4": app.state.gets.layer4_evolution is not None,
                    "layer5": app.state.gets.layer5_governance is not None,
                },
                "signal_history_count": len(app.state.gets.signal_history),
                "current_regime": app.state.gets._current_regime.name
            }
            
            return JSONResponse(content=status)
        
        @app.post("/record_outcome")
        async def record_outcome(
            symbol: str,
            predicted_edge: float,
            realized_return: float,
            regime: Optional[str] = None
        ):
            """
            Record outcome for a signal (used for Layer 4 evolution).
            
            This endpoint is used to provide feedback on signal performance,
            enabling the Controlled Evolution layer to analyze failures and
            propose improvements.
            """
            if not app.state.gets:
                raise HTTPException(status_code=503, detail="GETS not available")
            
            # Create synthetic signal for outcome recording
            from dataclasses import replace
            from .types import GETSSignal, DisagreementGeometry, SelfDiagnosisReport, ModelType
            
            # This is a simplified version - in production, you'd store signal IDs
            signal = GETSSignal(
                timestamp=datetime.now(),
                symbol=symbol,
                horizon=ForecastHorizon.SHORT,
                direction=1 if predicted_edge > 0 else -1,
                confidence=0.5,
                expected_edge=predicted_edge,
                uncertainty_quantile_05=0,
                uncertainty_quantile_95=0,
                prediction_interval=(0, 0),
                source_models=[ModelType.KRONOS],
                disagreement_geometry=DisagreementGeometry(),
                diagnosis_report=SelfDiagnosisReport(),
                recommended_size_scale=1.0,
                abstain_recommended=False,
                abstain_reason=None,
                governance_decision=app.state.gets.layer5_governance.layer5_govern.decide_governance if app.state.gets.layer5_governance else None
            )
            
            # Record outcome
            market_data = MarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                ohlcv={'close': 100, 'open': 100, 'high': 100, 'low': 100, 'volume': 0}
            )
            
            app.state.gets.record_outcome(signal, realized_return, market_data)
            
            return {
                "status": "recorded",
                "symbol": symbol,
                "predicted": predicted_edge,
                "realized": realized_return,
                "prediction_error": abs(predicted_edge - realized_return)
            }
        
        @app.get("/evolution/status")
        async def evolution_status():
            """
            Get controlled evolution layer status.
            
            Returns information about:
            - Failure clusters
            - Pending champions
            - Mutation proposals
            """
            if not app.state.gets or not app.state.gets.layer4_evolution:
                raise HTTPException(status_code=503, detail="Evolution layer not available")
            
            status = app.state.gets.get_evolution_status()
            return JSONResponse(content=status)
        
        @app.post("/evolution/propose")
        async def propose_mutations(background_tasks: BackgroundTasks):
            """
            Trigger mutation proposal (runs in background).
            
            This is an offline/sandbox operation that does not affect production.
            """
            if not app.state.gets or not app.state.gets.layer4_evolution:
                raise HTTPException(status_code=503, detail="Evolution layer not available")
            
            def propose():
                candidates = app.state.gets.layer4_evolution.propose_mutations(
                    app.state.gets.config
                )
                logger.info(f"Proposed {len(candidates)} mutations")
            
            background_tasks.add_task(propose)
            
            return {"status": "proposing", "message": "Mutation proposal started in background"}
        
        @app.get("/audit/trail")
        async def get_audit_trail(limit: int = Query(100, ge=1, le=1000)):
            """
            Get governance audit trail.
            
            Returns the most recent audit records with full provenance.
            """
            if not app.state.gets or not app.state.gets.layer5_governance:
                raise HTTPException(status_code=503, detail="Governance layer not available")
            
            audit_status = app.state.gets.layer5_governance.get_audit_status()
            
            return {
                "total_records": audit_status.get('total_records', 0),
                "chain_valid": audit_status.get('chain_valid', False),
                "recent_records": []  # Would fetch actual records
            }
        
        @app.post("/config/reload")
        async def reload_config():
            """
            Reload configuration (requires governance approval).
            """
            # This would trigger Layer 5 governance check
            return {"status": "pending_approval", "message": "Config reload requires governance approval"}
        
        return app
    
else:
    # Stub for when FastAPI is not available
    def create_gets_api(gets_instance=None):
        """Stub function when FastAPI is not installed."""
        logger.error("FastAPI is required for the API module. Install with: pip install fastapi uvicorn")
        raise ImportError("FastAPI not installed")


def run_api_server(
    host: str = "0.0.0.0",
    port: int = 8000,
    gets_instance: Optional[GETS] = None
):
    """
    Run GETS API server.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        gets_instance: Optional pre-initialized GETS instance
    """
    if not HAS_FASTAPI:
        logger.error("Cannot run API server - FastAPI not installed")
        return
    
    import uvicorn
    
    app = create_gets_api(gets_instance)
    
    logger.info(f"Starting GETS API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
