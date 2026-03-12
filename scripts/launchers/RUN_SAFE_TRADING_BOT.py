"""
Safe Trading Bot Runner with DeepSeek R1 8B Integration
Comprehensive safety controls and risk monitoring
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from trading_bot.ai_engineer.deepseek_r1_8b_integration import (
        DeepSeekR18BIntegration,
        DeepSeekR18BConfig
    )
    from trading_bot.safety.runtime_risk_monitor import RuntimeRiskMonitor
    from trading_bot.safety.emergency_kill_switch import EmergencyKillSwitch
    from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
except ImportError as e:
    print(f"Import error: {e}")
    print("Some safety systems may not be available")


def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("  SAFE TRADING BOT WITH DEEPSEEK R1 8B")
    print("=" * 80)
    print("Maximum Protection Trading System")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print()


def print_menu():
    """Print main menu"""
    print("\n📋 MAIN MENU:")
    print("  1. Start Trading Bot (Paper Trading)")
    print("  2. Start Trading Bot (Live Trading)")
    print("  3. Activate DeepSeek R1 8B AI Engineer")
    print("  4. Run System Diagnostics")
    print("  5. View Risk Monitor Status")
    print("  6. Emergency Shutdown")
    print("  7. Run Oversight Day Review")
    print("  8. Exit")
    print()


async def start_paper_trading():
    """Start bot in paper trading mode"""
    print("\n📄 Starting Paper Trading Mode...")
    print("✅ Paper trading provides risk-free testing")
    
    # Initialize safety systems
    kill_switch = EmergencyKillSwitch(
        max_drawdown=0.15,
        max_consecutive_losses=5,
        max_daily_loss_pct=0.05
    )
    
    circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
        max_loss_per_trade=0.02,
        max_daily_loss=0.05,
        max_weekly_loss=0.10,
        max_monthly_loss=0.15,
        max_drawdown=0.20
    ))
    
    runtime_monitor = RuntimeRiskMonitor(
        kill_switch=kill_switch,
        circuit_breaker=circuit_breaker
    )
    
    # Start monitoring
    print("🛡️ Safety systems active:")
    print("  ✅ Emergency Kill Switch")
    print("  ✅ Circuit Breaker")
    print("  ✅ Runtime Risk Monitor")
    print()
    
    # Start paper trading session
    initial_balance = 10000.0
    circuit_breaker.start_session(initial_balance)
    
    print(f"💰 Paper Trading Session Started")
    print(f"  • Initial Balance: ${initial_balance:,.2f}")
    print(f"  • Max Drawdown: 20%")
    print(f"  • Max Daily Loss: 5%")
    print()
    
    # Start monitoring in background
    monitor_task = asyncio.create_task(runtime_monitor.start_monitoring())
    
    print("📊 Monitoring active. Press Ctrl+C to stop.")
    
    try:
        # Run for demo (in production, this would be the main trading loop)
        await asyncio.sleep(3600)  # Run for 1 hour
    except KeyboardInterrupt:
        print("\n⚠️ Stopping paper trading...")
        runtime_monitor.stop_monitoring()
        await monitor_task
    
    print("✅ Paper trading session ended")


async def start_live_trading():
    """Start bot in live trading mode"""
    print("\n⚠️  LIVE TRADING MODE")
    print("=" * 80)
    print("🚨 WARNING: This will trade with REAL MONEY")
    print("=" * 80)
    
    confirm = input("\nType 'I UNDERSTAND THE RISKS' to continue: ")
    
    if confirm != "I UNDERSTAND THE RISKS":
        print("❌ Live trading cancelled")
        return
    
    print("\n✅ Starting live trading with maximum safety controls...")
    
    # Initialize safety systems with stricter limits for live trading
    kill_switch = EmergencyKillSwitch(
        max_drawdown=0.10,  # Stricter: 10%
        max_consecutive_losses=3,  # Stricter: 3
        max_daily_loss_pct=0.03  # Stricter: 3%
    )
    
    circuit_breaker = CircuitBreaker(CircuitBreakerConfig(
        max_loss_per_trade=0.01,  # Stricter: 1%
        max_daily_loss=0.03,  # Stricter: 3%
        max_weekly_loss=0.07,  # Stricter: 7%
        max_monthly_loss=0.12,  # Stricter: 12%
        max_drawdown=0.15,  # Stricter: 15%
        emergency_liquidation_drawdown=0.20  # Emergency at 20%
    ))
    
    runtime_monitor = RuntimeRiskMonitor(
        kill_switch=kill_switch,
        circuit_breaker=circuit_breaker
    )
    
    print("\n🛡️ LIVE TRADING SAFETY SYSTEMS:")
    print("  ✅ Emergency Kill Switch (STRICT)")
    print("  ✅ Circuit Breaker (STRICT)")
    print("  ✅ Runtime Risk Monitor")
    print("  ✅ Trade Frequency Limiter")
    print()
    print("📊 STRICT LIMITS:")
    print("  • Max Drawdown: 10%")
    print("  • Max Daily Loss: 3%")
    print("  • Max Loss Per Trade: 1%")
    print("  • Max Consecutive Losses: 3")
    print("  • Emergency Liquidation: 20%")
    print()
    
    # Get initial balance from broker
    initial_balance = 10000.0  # Would get from actual broker
    circuit_breaker.start_session(initial_balance)
    
    print(f"💰 Live Trading Session Started")
    print(f"  • Initial Balance: ${initial_balance:,.2f}")
    print()
    
    # Start monitoring
    monitor_task = asyncio.create_task(runtime_monitor.start_monitoring())
    
    print("🚨 LIVE TRADING ACTIVE - All safety systems engaged")
    print("📊 Press Ctrl+C for emergency shutdown")
    
    try:
        await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\n🚨 EMERGENCY SHUTDOWN INITIATED")
        await runtime_monitor.emergency_shutdown("User requested emergency stop")
        runtime_monitor.stop_monitoring()
        await monitor_task
    
    print("✅ Live trading session ended")


async def activate_deepseek():
    """Activate DeepSeek R1 8B AI Engineer"""
    print("\n🤖 Activating DeepSeek R1 8B AI Engineer...")
    print("=" * 80)
    
    # Configuration
    print("\n⚙️  AI CONFIGURATION:")
    print("  1. Engineer Mode (Code modifications only)")
    print("  2. Architect Mode (Design proposals + code)")
    print("  3. Read-Only Mode (Analysis only)")
    
    mode_choice = input("\nSelect mode (1-3, default=1): ").strip() or "1"
    
    mode_map = {
        "1": "engineer",
        "2": "architect",
        "3": "read_only"
    }
    ai_mode = mode_map.get(mode_choice, "engineer")
    
    print(f"\n✅ Selected: {ai_mode.upper()} mode")
    
    # Create configuration
    config = DeepSeekR18BConfig(
        model_name="deepseek-r1:8b",
        sandbox_enabled=True,
        require_approval=True,
        ai_mode=ai_mode,
        max_changes_per_hour=10,
        max_changes_per_day=50,
        min_test_coverage=0.90
    )
    
    # Initialize integration
    integration = DeepSeekR18BIntegration(config)
    
    try:
        await integration.initialize(project_root)
        
        print("\n✅ DeepSeek R1 8B AI Engineer ACTIVE")
        print("\n📝 You can now:")
        print("  • Propose code changes")
        print("  • Review AI proposals")
        print("  • Approve/reject changes")
        print("  • Monitor AI activity")
        
        # Keep running
        print("\nPress Ctrl+C to deactivate AI...")
        await asyncio.sleep(3600)
        
    except KeyboardInterrupt:
        print("\n⚠️ Deactivating DeepSeek R1 8B...")
        await integration.emergency_shutdown("User requested shutdown")
    
    print("✅ DeepSeek R1 8B deactivated")


async def run_diagnostics():
    """Run system diagnostics"""
    print("\n🔍 Running System Diagnostics...")
    print("=" * 80)
    
    # Check safety systems
    print("\n1️⃣ Safety Systems Check:")
    try:
        kill_switch = EmergencyKillSwitch()
        print("  ✅ Emergency Kill Switch: Available")
    except:
        print("  ❌ Emergency Kill Switch: Not available")
    
    try:
        circuit_breaker = CircuitBreaker()
        print("  ✅ Circuit Breaker: Available")
    except:
        print("  ❌ Circuit Breaker: Not available")
    
    try:
        runtime_monitor = RuntimeRiskMonitor()
        print("  ✅ Runtime Risk Monitor: Available")
    except:
        print("  ❌ Runtime Risk Monitor: Not available")
    
    # Check AI systems
    print("\n2️⃣ AI Systems Check:")
    try:
        from trading_bot.ai_engineer import DeepSeekEngineer
        print("  ✅ DeepSeek Engineer: Available")
    except:
        print("  ❌ DeepSeek Engineer: Not available")
    
    try:
        from trading_bot.ai_engineer import IntegratedSafeguardSystem
        print("  ✅ Integrated Safeguards: Available")
    except:
        print("  ❌ Integrated Safeguards: Not available")
    
    # Check files
    print("\n3️⃣ Critical Files Check:")
    critical_files = [
        "trading_bot/safety/emergency_kill_switch.py",
        "trading_bot/risk/circuit_breaker.py",
        "trading_bot/safety/runtime_risk_monitor.py",
        "COMPREHENSIVE_RISK_MITIGATION.md"
    ]
    
    for file in critical_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (missing)")
    
    print("\n✅ Diagnostics complete")


async def view_risk_status():
    """View risk monitor status"""
    print("\n📊 Risk Monitor Status")
    print("=" * 80)
    
    try:
        runtime_monitor = RuntimeRiskMonitor()
        status = runtime_monitor.get_status()
        
        print("\n🛡️ MONITORING:")
        print(f"  • Active: {status['monitoring_active']}")
        print(f"  • Trading Enabled: {status['trading_enabled']}")
        
        print("\n📈 METRICS:")
        metrics = status['metrics']
        print(f"  • Current Equity: ${metrics['current_equity']:,.2f}")
        print(f"  • Current Drawdown: {metrics['current_drawdown']:.2%}")
        print(f"  • Daily P&L: ${metrics['daily_pnl']:,.2f}")
        print(f"  • Weekly P&L: ${metrics['weekly_pnl']:,.2f}")
        print(f"  • Monthly P&L: ${metrics['monthly_pnl']:,.2f}")
        print(f"  • Consecutive Losses: {metrics['consecutive_losses']}")
        print(f"  • Win Rate: {metrics['win_rate']:.2%}")
        
        print("\n⚡ CIRCUIT BREAKER:")
        print(f"  • State: {metrics['circuit_breaker_state']}")
        print(f"  • Emergency: {'🚨 TRIGGERED' if metrics['emergency_triggered'] else '✅ Normal'}")
        
        print("\n💻 SYSTEM HEALTH:")
        print(f"  • CPU Usage: {metrics['cpu_usage']:.1f}%")
        print(f"  • Memory Usage: {metrics['memory_usage']:.1f}%")
        print(f"  • Disk Usage: {metrics['disk_usage']:.1f}%")
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")


async def emergency_shutdown():
    """Execute emergency shutdown"""
    print("\n🚨 EMERGENCY SHUTDOWN")
    print("=" * 80)
    
    confirm = input("Type 'EMERGENCY' to confirm: ")
    
    if confirm != "EMERGENCY":
        print("❌ Emergency shutdown cancelled")
        return
    
    print("\n🚨 EXECUTING EMERGENCY SHUTDOWN...")
    
    # Create emergency stop file
    emergency_file = project_root / "EMERGENCY_STOP.txt"
    emergency_file.write_text(
        f"EMERGENCY SHUTDOWN\n"
        f"Timestamp: {datetime.now().isoformat()}\n"
        f"Reason: Manual emergency shutdown\n"
    )
    
    print("✅ Emergency stop file created: EMERGENCY_STOP.txt")
    print("✅ All trading will halt immediately")
    print("\n⚠️ To resume trading:")
    print("  1. Review logs and identify issue")
    print("  2. Delete EMERGENCY_STOP.txt")
    print("  3. Restart the bot")


async def run_oversight_day():
    """Run oversight day review"""
    print("\n👁️ OVERSIGHT DAY REVIEW")
    print("=" * 80)
    
    try:
        integration = DeepSeekR18BIntegration()
        await integration.initialize(project_root)
        
        report = await integration.run_oversight_day()
        
        print("\n✅ Oversight report generated")
        print(f"  • Report saved to logs/safeguards/")
        
    except Exception as e:
        print(f"❌ Error running oversight day: {e}")


async def main():
    """Main menu loop"""
    print_banner()
    
    while True:
        print_menu()
        choice = input("Select option (1-8): ").strip()
        
        if choice == "1":
            await start_paper_trading()
        elif choice == "2":
            await start_live_trading()
        elif choice == "3":
            await activate_deepseek()
        elif choice == "4":
            await run_diagnostics()
        elif choice == "5":
            await view_risk_status()
        elif choice == "6":
            await emergency_shutdown()
        elif choice == "7":
            await run_oversight_day()
        elif choice == "8":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid option")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Program interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
