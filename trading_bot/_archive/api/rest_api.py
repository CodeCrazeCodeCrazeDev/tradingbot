"""
from typing import Any, List, Optional, Set
REST API Server with OpenAPI Documentation

Production-ready API for:
- Trading operations
- Position management
- Account information
- System monitoring
- Configuration management
- WebSocket streaming
"""

import asyncio
import logging
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import os

logger = logging.getLogger(__name__)

# Order enums
class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(Enum):
    pass
try:
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

# FastAPI imports
    from fastapi import FastAPI, HTTPException, Depends, Query, Body, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logger.warning("FastAPI not installed. Install with: pip install fastapi uvicorn")


# Pydantic models for API
if FASTAPI_AVAILABLE:
    
    class OrderSideEnum(str, Enum):
        BUY = "buy"
        SELL = "sell"
    
    class OrderTypeEnum(str, Enum):
        MARKET = "market"
        LIMIT = "limit"
        STOP = "stop"
        STOP_LIMIT = "stop_limit"
    
    class OrderRequest(BaseModel):
        """Order placement request"""
        symbol: str = Field(..., description="Trading symbol", example="EURUSD")
        side: OrderSideEnum = Field(..., description="Order side")
        order_type: OrderTypeEnum = Field(..., description="Order type")
        quantity: float = Field(..., gt=0, description="Order quantity")
        price: Optional[float] = Field(None, description="Limit price")
        stop_price: Optional[float] = Field(None, description="Stop price")
        client_order_id: Optional[str] = Field(None, description="Client order ID")
        
        class Config:
            schema_extra = {
                "example": {
                    "symbol": "EURUSD",
                    "side": "buy",
                    "order_type": "market",
                    "quantity": 100000
                }
            }
    
    class OrderResponse(BaseModel):
        """Order response"""
        order_id: str
        client_order_id: Optional[str]
        symbol: str
        side: str
        order_type: str
        quantity: float
        filled_quantity: float
        average_price: float
        status: str
        created_at: str
        
    class PositionResponse(BaseModel):
        """Position response"""
        symbol: str
        side: str
        quantity: float
        entry_price: float
        current_price: float
        unrealized_pnl: float
        realized_pnl: float
        
    class AccountResponse(BaseModel):
        """Account information response"""
        balance: float
        equity: float
        margin: float
        free_margin: float
        margin_level: float
        profit: float
        currency: str
        
    class HealthResponse(BaseModel):
        """Health check response"""
        status: str
        timestamp: str
        uptime_seconds: float
        version: str
        
    class AlertRequest(BaseModel):
        """Alert request"""
        severity: str = Field(..., description="Alert severity: info, warning, error, critical")
        title: str = Field(..., description="Alert title")
        message: str = Field(..., description="Alert message")
        
    class ConfigUpdateRequest(BaseModel):
        """Configuration update request"""
        key: str = Field(..., description="Configuration key")
        value: Any = Field(..., description="Configuration value")
        
    class FeatureFlagRequest(BaseModel):
        """Feature flag request"""
        flag: str = Field(..., description="Feature flag name")
        enabled: bool = Field(..., description="Enable/disable flag")


class TradingAPIServer:
    """
    Production-ready REST API server for trading operations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI not installed")
        
        self.config = config or {}
        self.host = self.config.get('host', '0.0.0.0')
        self.port = self.config.get('port', 8080)
        self.api_key = self.config.get('api_key', os.getenv('API_KEY', 'dev-key'))
        
        # Create FastAPI app
        self.app = FastAPI(
            title="AlphaAlgo Trading API",
            description="""
## AlphaAlgo Trading Bot REST API

Production-ready API for algorithmic trading operations.

### Features
- **Trading**: Place, modify, and cancel orders
- **Positions**: View and manage positions
- **Account**: Account information and balance
- **Monitoring**: Health checks and metrics
- **Configuration**: Runtime configuration management
- **WebSocket**: Real-time data streaming

### Authentication
Use API key in the `X-API-Key` header for all requests.
            """,
            version="2.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
            openapi_url="/openapi.json"
        )
        
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.get('cors_origins', ["*"]),
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Dependencies
        self.broker = None
        self.order_router = None
        self.monitor = None
        self.feature_flags: Dict[str, bool] = {}
        self.runtime_config: Dict[str, Any] = {}
        
        # WebSocket connections
        self.ws_connections: List[WebSocket] = []
        
        # Start time
        self._start_time = datetime.now()
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"TradingAPIServer initialized on {self.host}:{self.port}")
    
    def set_broker(self, broker):
        """Set broker adapter"""
        self.broker = broker
    
    def set_order_router(self, router):
        """Set order router"""
        self.order_router = router
    
    def set_monitor(self, monitor):
        """Set production monitor"""
        self.monitor = monitor
    
    def _verify_api_key(self, api_key: str = Depends(APIKeyHeader(name="X-API-Key", auto_error=False))):
        """Verify API key"""
        if not api_key or api_key != self.api_key:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return api_key
    
    def _setup_routes(self):
        """Setup all API routes by delegating to focused methods."""
        self._setup_health_routes()
        self._setup_trading_routes()
        self._setup_position_routes()
        self._setup_account_routes()
        self._setup_config_routes()
        self._setup_alert_routes()
        self._setup_metrics_routes()
        self._setup_websocket_routes()

    # ==========================================
    # Health & Status Routes
    # ==========================================
    def _setup_health_routes(self):
        """Setup health and status endpoints."""
        @self.app.get("/health/live", response_model=HealthResponse, tags=["Health"])
        async def liveness_check():
            """Kubernetes liveness probe"""
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "version": "2.0.0"
            }
        
        @self.app.get("/health/ready", response_model=HealthResponse, tags=["Health"])
        async def readiness_check():
            """Kubernetes readiness probe"""
            # Check if broker is connected
            broker_ready = self.broker and getattr(self.broker, 'connected', False)
            
            if not broker_ready:
                raise HTTPException(status_code=503, detail="Broker not connected")
            
            return {
                "status": "ready",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "version": "2.0.0"
            }
        
        @self.app.get("/status", tags=["Health"])
        async def get_status(api_key: str = Depends(self._verify_api_key)):
            """Get complete system status"""
            status = {
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self._start_time).total_seconds(),
                "broker_connected": self.broker and getattr(self.broker, 'connected', False),
                "feature_flags": self.feature_flags,
            }
            
            if self.monitor:
                status["monitoring"] = self.monitor.get_status()
            
            return status
        
    # ==========================================
    # Trading Operations Routes
    # ==========================================
    def _setup_trading_routes(self):
        """Setup trading operation endpoints."""
        @self.app.post("/orders", response_model=OrderResponse, tags=["Trading"])
        async def place_order(
            order: OrderRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Place a new order"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                # Import order types
                from trading_bot.brokers.broker_adapter import OrderSide, OrderType
                
                side = OrderSide.BUY if order.side == "buy" else OrderSide.SELL
                order_type = OrderType(order.order_type)
                
                response = await self.broker.place_order(
                    symbol=order.symbol,
                    side=side,
                    order_type=order_type,
                    quantity=order.quantity,
                    price=order.price,
                    stop_price=order.stop_price,
                    client_order_id=order.client_order_id
                )
                
                if not response:
                    raise HTTPException(status_code=400, detail="Order rejected")
                
                # Broadcast to WebSocket clients
                await self._broadcast({
                    "type": "order",
                    "data": {
                        "order_id": response.order_id,
                        "status": response.status.value
                    }
                })
                
                return {
                    "order_id": response.order_id,
                    "client_order_id": order.client_order_id,
                    "symbol": order.symbol,
                    "side": order.side,
                    "order_type": order.order_type,
                    "quantity": order.quantity,
                    "filled_quantity": response.filled_quantity,
                    "average_price": response.average_fill_price,
                    "status": response.status.value,
                    "created_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Order placement failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/orders/{order_id}", tags=["Trading"])
        async def cancel_order(
            order_id: str,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Cancel an order"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                success = await self.broker.cancel_order(order_id)
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to cancel order")
                
                return {"status": "cancelled", "order_id": order_id}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/orders/{order_id}", tags=["Trading"])
        async def get_order(
            order_id: str,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get order status"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                response = await self.broker.get_order_status(order_id)
                
                if not response:
                    raise HTTPException(status_code=404, detail="Order not found")
                
                return {
                    "order_id": response.order_id,
                    "status": response.status.value,
                    "filled_quantity": response.filled_quantity,
                    "average_price": response.average_fill_price
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
    # ==========================================
    # Position Routes
    # ==========================================
    def _setup_position_routes(self):
        """Setup position management endpoints."""
        @self.app.get("/positions", response_model=List[PositionResponse], tags=["Positions"])
        async def get_positions(api_key: str = Depends(self._verify_api_key)):
            """Get all open positions"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                positions = await self.broker.get_positions()
                
                return [
                    {
                        "symbol": p.symbol,
                        "side": p.side,
                        "quantity": p.quantity,
                        "entry_price": p.entry_price,
                        "current_price": p.current_price,
                        "unrealized_pnl": p.unrealized_pnl,
                        "realized_pnl": p.realized_pnl
                    }
                    for p in positions
                ]
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/positions/{symbol}", response_model=PositionResponse, tags=["Positions"])
        async def get_position(
            symbol: str,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get position for a symbol"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                position = await self.broker.get_position(symbol)
                
                if not position:
                    raise HTTPException(status_code=404, detail="Position not found")
                
                return {
                    "symbol": position.symbol,
                    "side": position.side,
                    "quantity": position.quantity,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "unrealized_pnl": position.unrealized_pnl,
                    "realized_pnl": position.realized_pnl
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/positions/{symbol}", tags=["Positions"])
        async def close_position(
            symbol: str,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Close position for a symbol"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                if hasattr(self.broker, 'close_position'):
                    success = await self.broker.close_position(symbol)
                else:
                    # Manual close
                    position = await self.broker.get_position(symbol)
                    if not position:
                        raise HTTPException(status_code=404, detail="Position not found")
                    
                    side = OrderSide.SELL if position.side == 'buy' else OrderSide.BUY
                    
                    response = await self.broker.place_order(
                        symbol=symbol,
                        side=side,
                        order_type=OrderType.MARKET,
                        quantity=position.quantity
                    )
                    success = response and response.success
                
                if not success:
                    raise HTTPException(status_code=400, detail="Failed to close position")
                
                return {"status": "closed", "symbol": symbol}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/positions", tags=["Positions"])
        async def close_all_positions(api_key: str = Depends(self._verify_api_key)):
            """Close all positions"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                if hasattr(self.broker, 'close_all_positions'):
                    success = await self.broker.close_all_positions()
                else:
                    positions = await self.broker.get_positions()
                    success = True
                    for p in positions:
                        if hasattr(self.broker, 'close_position'):
                            if not await self.broker.close_position(p.symbol):
                                success = False
                
                return {"status": "closed" if success else "partial", "message": "All positions closed"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
    # ==========================================
    # Account Routes
    # ==========================================
    def _setup_account_routes(self):
        """Setup account information endpoints."""
        @self.app.get("/account", response_model=AccountResponse, tags=["Account"])
        async def get_account(api_key: str = Depends(self._verify_api_key)):
            """Get account information"""
            if not self.broker:
                raise HTTPException(status_code=503, detail="Broker not configured")
            try:
            
                info = await self.broker.get_account_info()
                
                return {
                    "balance": info.get('balance', 0),
                    "equity": info.get('equity', 0),
                    "margin": info.get('margin', 0),
                    "free_margin": info.get('free_margin', 0),
                    "margin_level": info.get('margin_level', 0),
                    "profit": info.get('profit', 0),
                    "currency": info.get('currency', 'USD')
                }
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
    # ==========================================
    # Configuration Routes
    # ==========================================
    def _setup_config_routes(self):
        """Setup configuration management endpoints."""
        @self.app.get("/config", tags=["Configuration"])
        async def get_config(api_key: str = Depends(self._verify_api_key)):
            """Get runtime configuration"""
            return self.runtime_config
        
        @self.app.put("/config", tags=["Configuration"])
        async def update_config(
            request: ConfigUpdateRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Update runtime configuration"""
            self.runtime_config[request.key] = request.value
            
            # Broadcast config change
            await self._broadcast({
                "type": "config_update",
                "data": {"key": request.key, "value": request.value}
            })
            
            return {"status": "updated", "key": request.key}
        
        @self.app.get("/features", tags=["Configuration"])
        async def get_feature_flags(api_key: str = Depends(self._verify_api_key)):
            """Get feature flags"""
            return self.feature_flags
        
        @self.app.put("/features", tags=["Configuration"])
        async def update_feature_flag(
            request: FeatureFlagRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Update feature flag"""
            self.feature_flags[request.flag] = request.enabled
            
            return {"status": "updated", "flag": request.flag, "enabled": request.enabled}
        
    # ==========================================
    # Alert Routes
    # ==========================================
    def _setup_alert_routes(self):
        """Setup alert endpoints."""
        @self.app.post("/alerts", tags=["Alerts"])
        async def send_alert(
            request: AlertRequest,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Send an alert"""
            if not self.monitor:
                raise HTTPException(status_code=503, detail="Monitor not configured")
            try:
            
                from trading_bot.monitoring.production_monitoring import AlertSeverity
                
                severity = AlertSeverity(request.severity)
                await self.monitor.send_alert(
                    severity=severity,
                    title=request.title,
                    message=request.message,
                    source="API"
                )
                
                return {"status": "sent"}
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/alerts", tags=["Alerts"])
        async def get_alerts(
            limit: int = Query(100, ge=1, le=1000),
            api_key: str = Depends(self._verify_api_key)
        ):
            """Get recent alerts"""
            if not self.monitor:
                return []
            
            alerts = self.monitor.alert_manager.get_alerts(limit=limit)
            return [a.to_dict() for a in alerts]
        
    # ==========================================
    # Metrics Routes
    # ==========================================
    def _setup_metrics_routes(self):
        """Setup monitoring and metrics endpoints."""
        @self.app.get("/metrics", tags=["Monitoring"])
        async def get_metrics():
            """Get Prometheus metrics"""
            if self.monitor:
                return JSONResponse(
                    content=self.monitor.get_metrics_endpoint(),
                    media_type="text/plain"
                )
            return ""
        
    # ==========================================
    # WebSocket Routes
    # ==========================================
    def _setup_websocket_routes(self):
        """Setup WebSocket endpoints."""
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates"""
            await websocket.accept()
            self.ws_connections.append(websocket)
            
            try:
                while True:
                    # Keep connection alive
                    data = await websocket.receive_text()
                    
                    # Handle ping
                    if data == "ping":
                        await websocket.send_text("pong")
                    
            except WebSocketDisconnect:
                self.ws_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.ws_connections:
                    self.ws_connections.remove(websocket)
    
    async def _broadcast(self, message: Dict):
        """Broadcast message to all WebSocket clients"""
        for ws in self.ws_connections[:]:
            try:
                await ws.send_json(message)
            except Exception:
                self.ws_connections.remove(ws)
    
    def run(self):
        """Run the API server"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
    
    async def run_async(self):
        """Run the API server asynchronously"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


# Export
__all__ = ['TradingAPIServer']
