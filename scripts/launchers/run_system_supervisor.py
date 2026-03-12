"""
AlphaAlgo AI System Supervisor
Production Launcher
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from trading_bot.system_supervisor import SystemSupervisor


def setup_logging():
    """Configure production logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/system_supervisor.log'),
            logging.FileHandler('logs/system_supervisor_errors.log', level=logging.ERROR)
        ]
    )


async def main():
    """Main entry point"""
    print("\n" + "=" * 80)
    print("🤖 ALPHAALGO AI SYSTEM SUPERVISOR")
    print("Self-Healing Autonomous Trading System")
    print("=" * 80)
    print("\nInitializing...")
    print("Press Ctrl+C to stop\n")
    
    # Setup logging
    setup_logging()
    
    # Production configuration
    config = {
        'internet': {
            'primary_endpoints': [
                'api.broker.com',
                'api.marketdata.com',
                'newsapi.org'
            ],
            'backup_endpoints': ['8.8.8.8', '1.1.1.1'],
            'failover_enabled': True,
            'vpn_enabled': False,
            'backup_isp_enabled': False,
            'max_retries': 5,
            'recovery_log': 'logs/network_recovery.log'
        },
        'modules': {
            'check_interval': 30,
            'stale_threshold': 300,
            'max_restart_attempts': 3,
            'degraded_mode_threshold': 3
        },
        'repair': {
            'backup_dir': 'bot_backups',
            'backup_sources': {
                'market_data': ['alpha_vantage', 'yahoo_finance', 'finnhub'],
                'news': ['newsapi', 'finnhub', 'alpha_vantage'],
                'sentiment': ['twitter_api', 'reddit_api', 'stocktwits']
            }
        },
        'data_validation': {
            'price_change_threshold': 0.10,
            'max_data_age': 300,
            'data_providers': {
                'market_data': ['primary', 'backup1', 'backup2'],
                'news': ['newsapi', 'finnhub'],
                'sentiment': ['twitter', 'reddit']
            }
        },
        'check_interval': 60,
        'status_log': 'logs/system_status.log'
    }
    
    # Create supervisor
    supervisor = SystemSupervisor(config)
    
    try:
        # Start system
        started = await supervisor.start()
        
        if not started:
            print("❌ System failed to start")
            sys.exit(1)
        
        print("\n✅ System running")
        print(f"Trading Mode: {supervisor.trading_mode.value.upper()}")
        print("\nMonitoring:")
        print("  🌐 Internet health")
        print("  📡 Module status")
        print("  🔧 Auto-repair")
        print("  📊 Data validation")
        print("  🔄 Auto-updates")
        print("  🔒 Security")
        print("\nLogs: logs/system_supervisor.log\n")
        
        # Run indefinitely
        while True:
            await asyncio.sleep(3600)  # Sleep 1 hour
            
            # Periodic report
            supervisor.save_report(f'reports/system_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Shutdown signal received...")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error")
        sys.exit(1)
    
    finally:
        # Graceful shutdown
        print("\n🛑 Stopping system...")
        await supervisor.stop()
        
        # Save final report
        supervisor.save_report('system_supervisor_final_report.json')
        
        print("✅ System stopped gracefully")
        print(f"📊 Final report: system_supervisor_final_report.json\n")


if __name__ == '__main__':
    from datetime import datetime
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
