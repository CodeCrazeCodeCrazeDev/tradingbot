#!/usr/bin/env python
"""
Dashboard for Elite Trading System

This script runs a web dashboard for monitoring and controlling the Elite Trading System.
"""

import argparse
import logging
import os
import yaml
import json
import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, Request, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import redis
import pandas as pd
import numpy as np
from pathlib import Path

# Configure logging
def setup_logging(log_level="INFO", log_file=None):
    """Set up logging configuration"""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    
    handlers = [logging.StreamHandler()]
    
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

# Parse command line arguments
def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Elite Trading System Dashboard")
    
    parser.add_argument(
        "--config",
        help="Path to dashboard configuration file",
        default="config/dashboard_config.yaml"
    )
    
    parser.add_argument(
        "--host",
        help="Dashboard host",
        default=None
    )
    
    parser.add_argument(
        "--port",
        help="Dashboard port",
        type=int,
        default=None
    )
    
    parser.add_argument(
        "--log-level",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
        default="INFO"
    )
    
    parser.add_argument(
        "--log-file",
        help="Path to log file",
        default="logs/dashboard.log"
    )
    
    parser.add_argument(
        "--debug",
        help="Enable debug mode",
        action="store_true"
    )
    
    return parser.parse_args()

# Load configuration
def load_config(config_path):
    """Load configuration from file"""
    default_config = {
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": False,
            "reload": False
        },
        "redis": {
            "host": "localhost",
            "port": 6379,
            "db": 0,
            "decode_responses": True
        },
        "ui": {
            "refresh_intervals": {
                "system_status": 5000,
                "positions": 1000,
                "performance": 60000,
                "alerts": 10000,
                "market_data": 1000
            }
        }
    }
    
    if not os.path.exists(config_path):
        print(f"Configuration file not found: {config_path}, using defaults")
        return default_config
    
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            # Merge with defaults
            merged_config = {**default_config, **config}
            return merged_config
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return default_config

# Create FastAPI app
app = FastAPI(title="Elite Trading System Dashboard")

# Create Redis client
redis_client = None

# Create templates
templates = Jinja2Templates(directory="trading_bot/dashboard/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="trading_bot/dashboard/static"), name="static")

# WebSocket connections
active_connections = []

# Dashboard routes
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/api/system/status")
async def system_status():
    """Get current system status"""
    try:
        status_data = redis_client.hgetall("system:status")
        components = json.loads(redis_client.get("system:components") or "{}")
        
        return {
            "status": status_data.get("status", "unknown"),
            "components": components,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting system status: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/trading/positions")
async def positions():
    """Get current trading positions"""
    try:
        positions_data = redis_client.get("trading:positions")
        positions_list = json.loads(positions_data) if positions_data else []
        
        return {
            "positions": positions_list,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting positions: {e}")
        return {
            "positions": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/trading/orders")
async def orders():
    """Get current orders"""
    try:
        orders_data = redis_client.get("trading:orders")
        orders_list = json.loads(orders_data) if orders_data else []
        
        return {
            "orders": orders_list,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting orders: {e}")
        return {
            "orders": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/trading/performance")
async def performance():
    """Get trading performance metrics"""
    try:
        metrics_data = redis_client.get("trading:performance:metrics")
        metrics = json.loads(metrics_data) if metrics_data else {}
        
        daily_pnl_data = redis_client.get("trading:performance:daily_pnl")
        daily_pnl = json.loads(daily_pnl_data) if daily_pnl_data else {}
        
        return {
            "metrics": metrics,
            "daily_pnl": daily_pnl,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting performance: {e}")
        return {
            "metrics": {},
            "daily_pnl": {},
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/alerts")
async def alerts():
    """Get system alerts"""
    try:
        alerts_data = redis_client.lrange("system:alerts", 0, 99)  # Get last 100 alerts
        alerts_list = [json.loads(alert) for alert in alerts_data] if alerts_data else []
        
        return {
            "alerts": alerts_list,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logging.error(f"Error getting alerts: {e}")
        return {
            "alerts": [],
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.websocket("/ws/market_data")
async def market_data_websocket(websocket: WebSocket):
    """WebSocket endpoint for real-time market data"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            # Get latest market data from Redis
            market_data = redis_client.get("market:latest")
            market_data_dict = json.loads(market_data) if market_data else {}
            
            # Send to client
            await websocket.send_json({
                "market_data": market_data_dict,
                "timestamp": datetime.now().isoformat()
            })
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

@app.post("/api/trading/pause")
async def pause_trading():
    """Pause all trading activities"""
    try:
        redis_client.publish("commands", json.dumps({
            "command": "pause",
            "timestamp": datetime.now().isoformat()
        }))
        return {"status": "success", "message": "Trading pause command sent"}
    except Exception as e:
        logging.error(f"Error pausing trading: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/trading/resume")
async def resume_trading():
    """Resume trading activities"""
    try:
        redis_client.publish("commands", json.dumps({
            "command": "resume",
            "timestamp": datetime.now().isoformat()
        }))
        return {"status": "success", "message": "Trading resume command sent"}
    except Exception as e:
        logging.error(f"Error resuming trading: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/position/close/{symbol}")
async def close_position(symbol: str):
    """Close position for a specific symbol"""
    try:
        redis_client.publish("commands", json.dumps({
            "command": "close_position",
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }))
        return {"status": "success", "message": f"Close position command sent for {symbol}"}
    except Exception as e:
        logging.error(f"Error closing position: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/position/close_all")
async def close_all_positions():
    """Close all open positions"""
    try:
        redis_client.publish("commands", json.dumps({
            "command": "close_all_positions",
            "timestamp": datetime.now().isoformat()
        }))
        return {"status": "success", "message": "Close all positions command sent"}
    except Exception as e:
        logging.error(f"Error closing all positions: {e}")
        return {"status": "error", "message": str(e)}

# Main function
def main():
    """Main function"""
    # Parse command line arguments
    args = parse_args()
    
    # Set up logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger("dashboard")
    
    # Load configuration
    config = load_config(args.config)
    
    # Override configuration with command line arguments
    if args.host:
        config["server"]["host"] = args.host
    
    if args.port:
        config["server"]["port"] = args.port
    
    if args.debug:
        config["server"]["debug"] = True
    
    # Initialize Redis client
    global redis_client
    redis_client = redis.Redis(
        host=config["redis"]["host"],
        port=config["redis"]["port"],
        db=config["redis"]["db"],
        decode_responses=config["redis"]["decode_responses"]
    )
    
    # Check Redis connection
    try:
        redis_client.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Error connecting to Redis: {e}")
        return
    
    # Start Uvicorn server
    logger.info(f"Starting dashboard on {config['server']['host']}:{config['server']['port']}")
    uvicorn.run(
        "run_dashboard:app",
        host=config["server"]["host"],
        port=config["server"]["port"],
        reload=config["server"]["reload"],
        log_level=args.log_level.lower()
    )

# Entry point
if __name__ == "__main__":
    main()
