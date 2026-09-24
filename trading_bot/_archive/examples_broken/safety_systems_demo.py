"""
Safety Systems Demo

Demonstrates all P0 critical safety systems.
"""

import time
import random
import logging
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.safety import (
from enum import auto
    EmergencyKillSwitch,
    LatencyCircuitBreaker,
    ResourceWatchdog,
    ConnectivityMonitor,
    AutoPauseManager,
    TradingMode,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def demo_emergency_kill_switch():
    pass
    """Demonstrate emergency kill switch."""
    print("\n" + "=" * 80)
    print("DEMO 1: Emergency Kill Switch")
    print("=" * 80)
    
    kill_switch = EmergencyKillSwitch(
        max_drawdown=0.10,  # 10% for demo
        max_consecutive_losses=3,
        max_daily_loss_pct=0.05
    )
    
    # Simulate trading
    equity = 10000.0
    peak_equity = equity
    
    print(f"\nStarting equity: ${equity:.2f}")
    
    # Simulate some losing trades
    for i in range(5):
    pass
        # Simulate a loss
        loss = random.uniform(100, 300)
        equity -= loss
        
        print(f"\nTrade {i+1}: Loss ${loss:.2f}, Equity: ${equity:.2f}")
        
        # Check triggers
        triggers = kill_switch.check_triggers(equity, -loss)
        
        # Check if any triggered
        triggered = [t for t in triggers if t.triggered]
        if triggered:
    pass
            print("\n⚠️  TRIGGERS ACTIVATED:")
            for t in triggered:
    pass
                print(f"  - {t.name}: {t.message}")
            
            # Execute emergency stop
            if kill_switch.execute_emergency_stop(triggers):
    pass
                print("\n🚨 Emergency stop executed!")
                break
        else:
    pass
            print("  ✓ All triggers OK")
    
    print("\n" + "=" * 80)


def demo_latency_circuit_breaker():
    pass
    """Demonstrate latency circuit breaker."""
    print("\n" + "=" * 80)
    print("DEMO 2: Latency Circuit Breaker")
    print("=" * 80)
    
    circuit_breaker = LatencyCircuitBreaker(
        latency_threshold_ms=200,
        consecutive_failures=3
    )
    
    # Simulate varying latency
    latencies = [100, 150, 250, 300, 350, 400, 200, 100]
    
    for i, latency in enumerate(latencies, 1):
    pass
        mode = circuit_breaker.check_latency(latency)
        multiplier = circuit_breaker.get_position_size_multiplier()
        
        print(f"\nCheck {i}: Latency {latency}ms")
        print(f"  Mode: {mode.value}")
        print(f"  Position size multiplier: {multiplier:.1%}")
        print(f"  Allow new entries: {circuit_breaker.should_allow_new_entries()}")
        
        time.sleep(0.5)
    
    print("\n" + "=" * 80)


def demo_resource_watchdog():
    pass
    """Demonstrate resource watchdog."""
    print("\n" + "=" * 80)
    print("DEMO 3: Resource Watchdog")
    print("=" * 80)
    
    watchdog = ResourceWatchdog(
        cpu_threshold=70.0,  # Lower for demo
        memory_threshold=75.0
    )
    
    # Check current resources
    status = watchdog.check_resources()
    
    print(f"\nCurrent Resources:")
    print(f"  CPU: {status.cpu_percent:.1f}%")
    print(f"  Memory: {status.memory_percent:.1f}%")
    print(f"  Mode: {status.mode.value}")
    print(f"  Message: {status.message}")
    
    if status.should_reduce_positions or status.should_stop_scanning:
    pass
        print(f"\n⚠️  Recommended Actions:")
        actions = watchdog.get_recommended_actions(status)
        for action in actions:
    pass
            print(f"  - {action}")
    else:
    pass
        print("\n✓ Resources OK")
    
    print("\n" + "=" * 80)


def demo_auto_pause_manager():
    pass
    """Demonstrate auto-pause manager."""
    print("\n" + "=" * 80)
    print("DEMO 4: Auto-Pause Manager")
    print("=" * 80)
    
    pause_manager = AutoPauseManager(
        drift_cooldown_minutes=5,  # Short for demo
        latency_cooldown_minutes=2,
        resource_cooldown_minutes=3
    )
    
    print("\nSimulating drift detection...")
    
    # Simulate drift in multiple features
    drifted_features = ["rsi", "macd", "volume"]
    
    # First alert
    pause_manager.check_drift_trigger(["rsi"])
    state = pause_manager.get_state()
    print(f"\nAfter 1st drift alert:")
    print(f"  Paused: {state.is_paused}")
    print(f"  Message: {state.message}")
    
    # Second alert (should trigger pause)
    pause_manager.check_drift_trigger(drifted_features)
    state = pause_manager.get_state()
    print(f"\nAfter 2nd drift alert:")
    print(f"  Paused: {state.is_paused}")
    print(f"  Reason: {state.reason.value}")
    print(f"  Message: {state.message}")
    
    # Check if trading allowed
    allowed = pause_manager.should_allow_trading()
    print(f"\nTrading allowed: {allowed}")
    
    print("\n" + "=" * 80)


def demo_integrated_safety():
    pass
    """Demonstrate integrated safety system."""
    print("\n" + "=" * 80)
    print("DEMO 5: Integrated Safety System")
    print("=" * 80)
    
    # Initialize all safety systems
    kill_switch = EmergencyKillSwitch()
    circuit_breaker = LatencyCircuitBreaker()
    watchdog = ResourceWatchdog()
    pause_manager = AutoPauseManager()
    
    print("\n✓ All safety systems initialized")
    
    # Simulate trading loop
    equity = 10000.0
    
    for i in range(3):
    pass
        print(f"\n--- Trading Cycle {i+1} ---")
        
        # Check latency
        latency = random.uniform(100, 300)
        mode = circuit_breaker.check_latency(latency)
        print(f"Latency: {latency:.0f}ms → Mode: {mode.value}")
        
        # Check resources
        status = watchdog.check_resources()
        print(f"Resources: CPU {status.cpu_percent:.1f}%, Memory {status.memory_percent:.1f}%")
        
        # Check pause state
        if not pause_manager.should_allow_trading():
    pass
            print("⏸️  Trading paused")
            continue
        
        # Check if new entries allowed
        if not circuit_breaker.should_allow_new_entries():
    pass
            print("⏸️  New entries blocked (high latency)")
            continue
        
        # Simulate trade
        pnl = random.uniform(-100, 150)
        equity += pnl
        print(f"Trade PnL: ${pnl:.2f}, Equity: ${equity:.2f}")
        
        # Check kill switch
        triggers = kill_switch.check_triggers(equity, pnl)
        if any(t.triggered for t in triggers):
    pass
            print("🚨 Emergency triggers activated!")
            break
        
        time.sleep(1)
    
    print("\n✓ Safety systems demo complete")
    print("=" * 80)


def main():
    pass
    """Run all demos."""
    print("\n" + "=" * 80)
    print("SAFETY SYSTEMS DEMONSTRATION")
    print("=" * 80)
    
    try:
    pass
        demo_emergency_kill_switch()
        time.sleep(2)
        
        demo_latency_circuit_breaker()
        time.sleep(2)
        
        demo_resource_watchdog()
        time.sleep(2)
        
        demo_auto_pause_manager()
        time.sleep(2)
        
        demo_integrated_safety()
        
    except KeyboardInterrupt:
    pass
        print("\n\nDemo interrupted by user")
    except Exception as e:
    pass
        logger.error(f"Demo error: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review the safety system logs")
    print("2. Integrate into your main trading loop")
    print("3. Test thoroughly in paper trading")
    print("4. Proceed to P1 ML improvements")
    print("=" * 80)


if __name__ == "__main__":
    pass
    main()
