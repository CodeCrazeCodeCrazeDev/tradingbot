"""
Complete Autonomous AlphaAlgo System
Integrates Internet Access + AI System Supervisor
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.internet_access import AlphaAlgoOrchestrator as InternetOrchestrator
from trading_bot.system_supervisor import SystemSupervisor
import json


class CompleteAutonomousSystem:
    """
    Complete autonomous trading system combining:
    - Internet-empowered data acquisition
    - AI system supervision and self-healing
    """
    
    def __init__(self):
        # Internet access configuration
        self.internet_config = {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'cache_dir': 'data_cache',
            'trading_interval_minutes': 5,
            'connections': {
                'endpoints': {
                    'broker_feed': {
                        'url': 'https://api.broker.com/feed',
                        'backup_url': 'https://backup.broker.com/feed'
                    }
                }
            },
            'fusion': {
                'fusion_weights': {
                    'technical': 0.60,
                    'sentiment': 0.25,
                    'news': 0.10,
                    'volatility': 0.05
                },
                'min_confidence': 0.6
            }
        }
        
        # System supervisor configuration
        self.supervisor_config = {
            'internet': {
                'primary_endpoints': [
                    'api.broker.com',
                    'api.marketdata.com',
                    'newsapi.org'
                ],
                'backup_endpoints': ['8.8.8.8', '1.1.1.1'],
                'failover_enabled': True,
                'max_retries': 5
            },
            'modules': {
                'check_interval': 30,
                'stale_threshold': 300,
                'max_restart_attempts': 3
            },
            'repair': {
                'backup_dir': 'bot_backups',
                'backup_sources': {
                    'market_data': ['alpha_vantage', 'yahoo_finance'],
                    'news': ['newsapi', 'finnhub'],
                    'sentiment': ['twitter_api', 'reddit_api']
                }
            },
            'data_validation': {
                'price_change_threshold': 0.10,
                'max_data_age': 300
            },
            'check_interval': 60
        }
        
        # Initialize components
        self.internet_orchestrator = InternetOrchestrator(self.internet_config)
        self.system_supervisor = SystemSupervisor(self.supervisor_config)
        
        self.is_running = False
    
    async def initialize(self) -> bool:
        """Initialize complete system"""
        print("\n" + "=" * 80)
        print("🤖 COMPLETE AUTONOMOUS ALPHAALGO SYSTEM")
        print("=" * 80)
        print("\nInitializing all components...\n")
        
        # Initialize system supervisor
        print("1️⃣ Initializing AI System Supervisor...")
        supervisor_ready = await self.system_supervisor.initialize()
        
        if not supervisor_ready:
            print("❌ System supervisor initialization failed")
            return False
        
        print("✅ System supervisor ready\n")
        
        # Initialize internet orchestrator
        print("2️⃣ Initializing Internet Orchestrator...")
        internet_ready = await self.internet_orchestrator.initialize()
        
        if not internet_ready:
            print("❌ Internet orchestrator initialization failed")
            return False
        
        print("✅ Internet orchestrator ready\n")
        
        print("=" * 80)
        print("✅ COMPLETE SYSTEM INITIALIZED")
        print("=" * 80 + "\n")
        
        return True
    
    async def run_unified_trading_cycle(self):
        """
        Run unified trading cycle with supervision.
        """
        try:
            # Check system health
            system_status = await self.system_supervisor.get_system_status()
            
            print(f"\n{'=' * 80}")
            print(f"SYSTEM STATUS CHECK")
            print(f"{'=' * 80}")
            print(f"Health:        {system_status.health.value.upper()}")
            print(f"Trading Mode:  {system_status.trading_mode.value.upper()}")
            print(f"Internet:      {system_status.internet_health:.1f}%")
            print(f"Modules:       {system_status.modules_healthy}/{system_status.modules_total}")
            print(f"Data Quality:  {system_status.data_validity_pct:.1f}%")
            
            # Check if trading is allowed
            if system_status.trading_mode.value == 'disabled':
                print("\n⚠️ Trading disabled due to system health")
                return None
            
            # Run internet-powered trading cycle
            print(f"\n{'=' * 80}")
            print(f"RUNNING TRADING CYCLE")
            print(f"{'=' * 80}\n")
            
            decision = await self.internet_orchestrator.run_trading_cycle()
            
            if decision:
                print(f"\n{'=' * 80}")
                print(f"TRADING DECISION")
                print(f"{'=' * 80}")
                print(f"Symbol:      {decision.symbol}")
                print(f"Action:      {decision.action}")
                print(f"Confidence:  {decision.confidence:.2%}")
                print(f"Strength:    {decision.strength:.2f}")
                print(f"Risk Score:  {decision.risk_score:.2%}")
                print(f"{'=' * 80}\n")
                
                # Execute trade if confidence is high enough
                if decision.confidence >= 0.75 and decision.action != 'HOLD':
                    print(f"💡 High confidence {decision.action} signal")
                    print(f"   Executing trade... (simulated)")
                    # await self.execute_trade(decision)
            
            return decision
        
        except Exception as e:
            print(f"\n❌ Error in trading cycle: {e}")
            logging.exception("Trading cycle error")
            return None
    
    async def autonomous_operation(self, duration_minutes: int = 60):
        """
        Run autonomous operation for specified duration.
        """
        print(f"\n{'=' * 80}")
        print(f"STARTING AUTONOMOUS OPERATION")
        print(f"Duration: {duration_minutes} minutes")
        print(f"{'=' * 80}\n")
        
        self.is_running = True
        start_time = asyncio.get_event_loop().time()
        end_time = start_time + (duration_minutes * 60)
        
        cycle_count = 0
        
        while self.is_running and asyncio.get_event_loop().time() < end_time:
            try:
                cycle_count += 1
                print(f"\n{'#' * 80}")
                print(f"CYCLE {cycle_count}")
                print(f"{'#' * 80}")
                
                # Run trading cycle
                await self.run_unified_trading_cycle()
                
                # Wait for next cycle (5 minutes)
                remaining = end_time - asyncio.get_event_loop().time()
                if remaining > 0:
                    wait_time = min(300, remaining)  # 5 minutes or remaining time
                    print(f"\n⏰ Next cycle in {wait_time:.0f} seconds...")
                    await asyncio.sleep(wait_time)
            
            except asyncio.CancelledError:
                break
            
            except Exception as e:
                print(f"\n❌ Error in autonomous operation: {e}")
                logging.exception("Autonomous operation error")
                await asyncio.sleep(60)  # Wait 1 minute on error
        
        print(f"\n{'=' * 80}")
        print(f"AUTONOMOUS OPERATION COMPLETE")
        print(f"Total Cycles: {cycle_count}")
        print(f"{'=' * 80}\n")
    
    async def stop(self):
        """Stop all systems gracefully"""
        print("\n🛑 Stopping all systems...")
        
        self.is_running = False
        
        # Stop internet orchestrator
        await self.internet_orchestrator.stop()
        
        # Stop system supervisor
        await self.system_supervisor.stop()
        
        # Generate final reports
        print("\n📊 Generating final reports...")
        
        self.internet_orchestrator.save_status_report('final_internet_status.json')
        self.system_supervisor.save_report('final_supervisor_status.json')
        
        print("✅ All systems stopped")
        print("📊 Reports saved:")
        print("   - final_internet_status.json")
        print("   - final_supervisor_status.json\n")


async def main():
    """Main entry point"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('complete_autonomous_system.log')
        ]
    )
    
    # Create complete system
    system = CompleteAutonomousSystem()
    
    try:
        # Initialize
        initialized = await system.initialize()
        
        if not initialized:
            print("❌ System initialization failed")
            return
        
        # Run autonomous operation
        print("\nStarting autonomous operation...")
        print("Press Ctrl+C to stop\n")
        
        await system.autonomous_operation(duration_minutes=60)
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user")
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        logging.exception("Fatal error")
    
    finally:
        await system.stop()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
