import logging
#!/usr/bin/env python
"""
Dashboard Launcher for Elite Trading Bot
Provides a unified interface for launching and managing the web dashboard
"""
import os
import sys
import yaml
import argparse
import uvicorn
from pathlib import Path
from loguru import logger

def load_config():
    """Load dashboard configuration."""
    config_path = Path(__file__).parent / "config.yaml"
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading dashboard config: {e}")
        sys.exit(1)

def setup_logging():
    """Configure logging for the dashboard."""
    log_path = Path(__file__).parent / "logs"
    log_path.mkdir(exist_ok=True)
    
    logger.add(
        log_path / "dashboard_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO"
    )

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = {
        "fastapi": "FastAPI web framework",
        "uvicorn": "ASGI server",
        "redis": "Redis client",
        "jinja2": "Template engine",
        "aiofiles": "Async file operations",
        "python-multipart": "Form data handling"
    }
    
    missing = []
    for package, description in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing.append(f"{package} ({description})")
    
    if missing:
        logger.error("Missing required dependencies:")
        for pkg in missing:
            logger.error(f"  - {pkg}")
        sys.exit(1)

def check_redis_connection(config):
    """Verify Redis connection."""
    import redis

    try:
        client = redis.Redis(
            host=config["redis"]["host"],
            port=config["redis"]["port"],
            db=config["redis"]["db"],
            decode_responses=True
        )
        client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        sys.exit(1)

def setup_static_files():
    """Ensure static files directory structure exists."""
    static_path = Path(__file__).parent / "static"
    css_path = static_path / "css"
    js_path = static_path / "js"
    
    css_path.mkdir(parents=True, exist_ok=True)
    js_path.mkdir(parents=True, exist_ok=True)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Elite Trading Bot Dashboard")
    parser.add_argument(
        "--host",
        help="Host to bind to",
        default=None
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to",
        default=None
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode"
    )
    return parser.parse_args()

def main():
    """Main entry point for the dashboard."""
    # Setup
    setup_logging()
    logger.info("Starting Elite Trading Bot Dashboard")
    
    # Load configuration
    config = load_config()
    logger.info("Configuration loaded successfully")
    
    # Parse command line arguments
    args = parse_args()
    
    # Override config with command line arguments
    if args.host:
        config["server"]["host"] = args.host
    if args.port:
        config["server"]["port"] = args.port
    if args.debug:
        config["server"]["debug"] = True
    
    # Check dependencies
    check_dependencies()
    logger.info("All dependencies available")
    
    # Check Redis connection
    check_redis_connection(config)
    
    # Setup static files
    setup_static_files()
    logger.info("Static files directory structure verified")
    
    # Start the dashboard
    logger.info(f"Starting dashboard on {config['server']['host']}:{config['server']['port']}")
    try:
        uvicorn.run(
            "app:app",
            host=config["server"]["host"],
            port=config["server"]["port"],
            reload=config["server"]["reload"],
            log_level="debug" if config["server"]["debug"] else "info"
        )
    except Exception as e:
        logger.error(f"Error starting dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
