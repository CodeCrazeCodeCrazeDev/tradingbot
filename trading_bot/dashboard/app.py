"""
from typing import Set
Web Dashboard for Elite Trading Bot
Provides real-time monitoring and control interface
"""
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import redis
import json
import asyncio
from datetime import datetime
import pandas as pd
from pathlib import Path
from typing import Dict, List

app = FastAPI(title="Elite Trading Bot Dashboard")
templates = Jinja2Templates(directory="trading_bot/dashboard/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="trading_bot/dashboard/static"), name="static")

# Redis connection
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request):
    """Main dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/system/status")
async def system_status():
    """Get current system status."""
    health_metrics = redis_client.hgetall("system:health")
    recovery_status = redis_client.hgetall("system:recovery_status")
    trading_mode = redis_client.get("trading:mode")
    
    return {
        "health": health_metrics,
        "recovery": recovery_status,
        "trading_mode": trading_mode,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/trading/positions")
async def positions():
    """Get current trading positions."""
    positions = redis_client.hgetall("positions:current")
    return {
        "positions": positions,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/trading/performance")
async def performance():
    """Get trading performance metrics."""
    daily_pnl = redis_client.hgetall("performance:daily_pnl")
    metrics = redis_client.hgetall("performance:metrics")
    return {
        "daily_pnl": daily_pnl,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/alerts")
async def alerts():
    """Get system alerts."""
    alerts = redis_client.lrange("system:alerts", 0, 99)  # Get last 100 alerts
    return {
        "alerts": [json.loads(alert) for alert in alerts],
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/market_data")
async def market_data_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time market data."""
    await websocket.accept()
    
    try:
        while True:
            # Get latest market data from Redis
            market_data = redis_client.hgetall("market:latest")
            
            # Send to client
            await websocket.send_json({
                "market_data": market_data,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)  # Update every second
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

@app.post("/api/trading/pause")
async def pause_trading():
    """Pause all trading activities."""
    redis_client.set("trading:paused", "1")
    return {"status": "success", "message": "Trading paused"}

@app.post("/api/trading/resume")
async def resume_trading():
    """Resume trading activities."""
    redis_client.set("trading:paused", "0")
    return {"status": "success", "message": "Trading resumed"}

@app.post("/api/trading/mode/{mode}")
async def set_trading_mode(mode: str):
    """Set trading mode (aggressive, balanced, conservative)."""
    valid_modes = ["aggressive", "balanced", "conservative", "ultra_conservative"]
    if mode not in valid_modes:
        return {"status": "error", "message": f"Invalid mode. Must be one of {valid_modes}"}
        
    redis_client.set("trading:mode", mode)
    return {"status": "success", "message": f"Trading mode set to {mode}"}

@app.post("/api/position/close/{symbol}")
async def close_position(symbol: str):
    """Close position for a specific symbol."""
    redis_client.publish("commands", json.dumps({
        "command": "close_position",
        "symbol": symbol,
        "timestamp": datetime.now().isoformat()
    }))
    return {"status": "success", "message": f"Close position command sent for {symbol}"}

@app.post("/api/position/close_all")
async def close_all_positions():
    """Close all open positions."""
    redis_client.publish("commands", json.dumps({
        "command": "close_all_positions",
        "timestamp": datetime.now().isoformat()
    }))
    return {"status": "success", "message": "Close all positions command sent"}

if __name__ == "__main__":
    import uvicorn
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


    uvicorn.run(app, host="0.0.0.0", port=8000)
