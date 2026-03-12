"""
AlphaAlgo Network Monitor - Quick Start Script
Run this to start network monitoring with AlphaAlgo.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/network_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


async def main():
    """Main entry point for network monitor."""
    logger.info("=" * 80)
    logger.info("AlphaAlgo Network Monitor Starting...")
    logger.info("=" * 80)
    
    try:
        # Load configuration
        config_file = Path('config/alphaalgo_config.yaml')
        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            logger.error("Please create config/alphaalgo_config.yaml")
            return 1
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        logger.info("Configuration loaded successfully")
        
        # Initialize network integration
        from trading_bot.connectivity import NetworkIntegration
        
        integration = NetworkIntegration(config)
        await integration.initialize()
        
        logger.info("✅ Network monitoring started successfully!")
        logger.info("")
        logger.info("Monitoring Status:")
        logger.info(f"  - Primary Endpoints: {len(config.get('network', {}).get('primary_endpoints', []))}")
        logger.info(f"  - Fallback Endpoints: {len(config.get('network', {}).get('fallback_endpoints', []))}")
        logger.info(f"  - Check Interval: {config.get('network', {}).get('check_interval_seconds', 10)}s")
        logger.info(f"  - Latency Warning: {config.get('network', {}).get('latency_warning_ms', 150)}ms")
        logger.info(f"  - Latency Critical: {config.get('network', {}).get('latency_critical_ms', 300)}ms")
        logger.info("")
        logger.info("Press Ctrl+C to stop monitoring...")
        logger.info("=" * 80)
        
        # Keep running and display status updates
        try:
            while True:
                await asyncio.sleep(30)  # Update every 30 seconds
                
                # Get current status
                status = integration.get_network_status()
                
                # Display status
                logger.info("")
                logger.info("=" * 80)
                logger.info(f"Network Status Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("=" * 80)
                logger.info(f"Network Status: {status.get('network_status', 'unknown').upper()}")
                logger.info(f"Trading Mode: {status.get('trading_mode', 'unknown').upper()}")
                logger.info(f"Average Latency: {status.get('average_latency_ms', 0):.1f}ms")
                logger.info(f"Trading Allowed: {'✅ YES' if status.get('is_trading_allowed', False) else '⛔ NO'}")
                
                if status.get('stable_since'):
                    logger.info(f"Stable Since: {status['stable_since']}")
                if status.get('offline_since'):
                    logger.info(f"⚠️ Offline Since: {status['offline_since']}")
                
                logger.info("=" * 80)
        
        except KeyboardInterrupt:
            logger.info("\n\nShutdown requested by user...")
        
        # Shutdown
        logger.info("Shutting down network monitoring...")
        await integration.shutdown()
        
        logger.info("✅ Network monitoring stopped successfully")
        logger.info("=" * 80)
        
        return 0
    
    except Exception as e:
        logger.error(f"❌ Error starting network monitor: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    # Create required directories
    Path('logs').mkdir(exist_ok=True)
    Path('state').mkdir(exist_ok=True)
    
    # Run
    exit_code = asyncio.run(main())
    exit(exit_code)
