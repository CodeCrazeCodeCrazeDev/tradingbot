#!/usr/bin/env python
"""
Risk Management Demonstration

This script demonstrates the risk management and survival capabilities
of the Elite Trading Bot, including:
- Position sizing
- Risk limits
- Drawdown protection
- Error recovery
- Emergency procedures
"""

import asyncio
import logging
import yaml
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from pathlib import Path

from trading_bot.core.survival_core import SurvivalCore
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("risk_management_demo.log")
    ]
)
logger = logging.getLogger("risk_management_demo")


async def demonstrate_position_sizing(system: SurvivalCore):
    """Demonstrate position sizing capabilities"""
    logger.info("\n=== Position Sizing Demonstration ===")
    
    # Get account status
    status = system.execution.get_portfolio_status()
    account_balance = status['account_balance']
    logger.info(f"Account Balance: ${account_balance:.2f}")
    
    # Calculate position sizes for different scenarios
    scenarios = [
        {
            'name': 'Conservative',
            'win_rate': 0.55,
            'reward_risk': 1.5,
            'volatility': 'low'
        },
        {
            'name': 'Moderate',
            'win_rate': 0.50,
            'reward_risk': 2.0,
            'volatility': 'medium'
        },
        {
            'name': 'Aggressive',
            'win_rate': 0.45,
            'reward_risk': 3.0,
            'volatility': 'high'
        }
    ]
    
    for scenario in scenarios:
        # Calculate position size
        entry_price = 1.1000
        stop_distance = {
            'low': 0.0010,    # 10 pips
            'medium': 0.0020, # 20 pips
            'high': 0.0040    # 40 pips
        }[scenario['volatility']]
        
        stop_loss = entry_price - stop_distance
        
        position = system.execution.calculate_position_size(
            symbol="EURUSD",
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_rate=scenario['win_rate'],
            reward_risk_ratio=scenario['reward_risk']
        )
        
        # Log results
        logger.info(f"\n{scenario['name']} Scenario:")
        logger.info(f"Win Rate: {scenario['win_rate']:.0%}")
        logger.info(f"Reward/Risk: {scenario['reward_risk']:.1f}")
        logger.info(f"Volatility: {scenario['volatility']}")
        logger.info(f"Position Size: {position['recommended_size']:.2f}")
        logger.info(f"Risk Amount: ${position['risk_amount']:.2f}")
        logger.info(f"Risk Percentage: {position['risk_amount']/account_balance:.2%}")


async def demonstrate_risk_limits(system: SurvivalCore):
    """Demonstrate risk limit enforcement"""
    logger.info("\n=== Risk Limits Demonstration ===")
    
    # Get initial status
    status = system.execution.get_portfolio_status()
    account_balance = status['account_balance']
    
    # Demonstrate daily loss limit
    daily_loss_limit = account_balance * system.risk_limits['max_daily_loss']
    logger.info(f"Daily Loss Limit: ${daily_loss_limit:.2f}")
    
    # Simulate approaching daily loss limit
    current_loss = daily_loss_limit * 0.8  # 80% of limit
    logger.info(f"Current Loss: ${current_loss:.2f} ({current_loss/daily_loss_limit:.1%} of limit)")
    
    await system._send_notification(
        "Daily Loss Warning",
        f"Approaching daily loss limit: ${current_loss:.2f}",
        level="warning"
    )
    
    # Demonstrate position limits
    max_positions = system.risk_limits['max_open_positions']
    logger.info(f"\nMaximum Open Positions: {max_positions}")
    
    # Try to open positions
    for i in range(max_positions + 1):
        position = system.execution.calculate_position_size(
            symbol=f"PAIR{i}",
            entry_price=1.0,
            stop_loss=0.99,
            win_rate=0.55,
            reward_risk_ratio=1.5
        )
        
        added = system.execution.add_position(position)
        logger.info(f"Position {i+1}: {'Added' if added else 'Rejected'}")
    
    # Demonstrate correlation limits
    logger.info("\nCorrelation Management:")
    correlated_pairs = [
        ('EURUSD', 'GBPUSD'),
        ('AUDUSD', 'NZDUSD'),
        ('EURJPY', 'GBPJPY')
    ]
    
    for pair1, pair2 in correlated_pairs:
        # Calculate position for first pair
        position1 = system.execution.calculate_position_size(
            symbol=pair1,
            entry_price=1.0,
            stop_loss=0.99,
            win_rate=0.55,
            reward_risk_ratio=1.5
        )
        
        # Try to add correlated position
        position2 = system.execution.calculate_position_size(
            symbol=pair2,
            entry_price=1.0,
            stop_loss=0.99,
            win_rate=0.55,
            reward_risk_ratio=1.5
        )
        
        # Check correlation risk
        risk_check = system.execution.check_portfolio_risk(position2)
        logger.info(f"Correlation check {pair1}-{pair2}: {'Passed' if risk_check['approved'] else 'Failed'}")


async def demonstrate_drawdown_protection(system: SurvivalCore):
    """Demonstrate drawdown protection"""
    logger.info("\n=== Drawdown Protection Demonstration ===")
    
    # Get initial status
    status = system.execution.get_portfolio_status()
    account_balance = status['account_balance']
    max_drawdown = system.risk_limits['max_drawdown']
    
    logger.info(f"Maximum Drawdown Limit: {max_drawdown:.1%}")
    
    # Simulate increasing drawdown
    drawdown_levels = [0.05, 0.10, 0.15, 0.20]
    
    for drawdown in drawdown_levels:
        # Update equity
        new_equity = account_balance * (1 - drawdown)
        await system.execution.update_account_equity(new_equity)
        
        # Get updated status
        status = system.get_system_status()
        
        logger.info(f"\nDrawdown: {drawdown:.1%}")
        logger.info(f"Equity: ${new_equity:.2f}")
        logger.info(f"System State: {'Paused' if system.paused else 'Running'}")


async def demonstrate_error_recovery(system: SurvivalCore):
    """Demonstrate error recovery capabilities"""
    logger.info("\n=== Error Recovery Demonstration ===")
    
    # Simulate various error scenarios
    scenarios = [
        {
            'component': 'market_data',
            'error': 'Connection lost to data feed',
            'severity': 'error'
        },
        {
            'component': 'execution',
            'error': 'Order placement timeout',
            'severity': 'warning'
        },
        {
            'component': 'analysis',
            'error': 'Signal generation failed',
            'severity': 'warning'
        },
        {
            'component': 'risk',
            'error': 'Risk calculation error',
            'severity': 'error'
        }
    ]
    
    for scenario in scenarios:
        logger.info(f"\nSimulating {scenario['component']} error:")
        logger.info(f"Error: {scenario['error']}")
        logger.info(f"Severity: {scenario['severity']}")
        
        # Update component status
        system.monitoring.update_component_status(
            scenario['component'],
            scenario['severity'],
            {'error': scenario['error']}
        )
        
        # Wait for recovery attempt
        await asyncio.sleep(2)
        
        # Simulate recovery
        system.monitoring.update_component_status(
            scenario['component'],
            'ok',
            {'recovered': True}
        )
        
        # Get system status
        status = system.get_system_status()
        logger.info(f"System Status: {status['system']['running']}")
        logger.info(f"Component Status: {status['monitoring']['components'][scenario['component']]['status']}")


async def demonstrate_emergency_procedures(system: SurvivalCore):
    """Demonstrate emergency procedures"""
    logger.info("\n=== Emergency Procedures Demonstration ===")
    
    # Open some test positions
    test_positions = [
        {
            'symbol': 'EURUSD',
            'entry_price': 1.1000,
            'stop_loss': 1.0950
        },
        {
            'symbol': 'GBPUSD',
            'entry_price': 1.2500,
            'stop_loss': 1.2450
        },
        {
            'symbol': 'USDJPY',
            'entry_price': 150.00,
            'stop_loss': 149.50
        }
    ]
    
    for pos in test_positions:
        position = system.execution.calculate_position_size(
            symbol=pos['symbol'],
            entry_price=pos['entry_price'],
            stop_loss=pos['stop_loss'],
            win_rate=0.55,
            reward_risk_ratio=1.5
        )
        system.execution.add_position(position)
    
    # Show initial positions
    positions = system.execution.get_active_positions()
    logger.info(f"\nInitial Positions: {len(positions)}")
    for pos in positions:
        logger.info(f"  {pos.symbol}: {pos.quantity:.2f} @ {pos.entry_price:.4f}")
    
    # Demonstrate emergency shutdown
    logger.info("\nInitiating emergency shutdown...")
    await system.emergency_stop()
    
    # Verify system state
    status = system.get_system_status()
    logger.info(f"System Running: {status['system']['running']}")
    logger.info(f"Emergency Shutdown: {status['system']['emergency_shutdown']}")
    
    # Verify positions closed
    positions = system.execution.get_active_positions()
    logger.info(f"Remaining Positions: {len(positions)}")


async def main():
    """Main function"""
    logger.info("Starting Risk Management Demonstration")
    
    try:
        # Load configuration
        config_path = Path("config/survival_config.yaml")
        if not config_path.exists():
            logger.error(f"Configuration file not found: {config_path}")
            return
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Create survival system
        system = SurvivalCore(config)
        
        # Start system
        await system.start()
        logger.info("Trading system started")
        
        try:
            # Run demonstrations
            await demonstrate_position_sizing(system)
            await demonstrate_risk_limits(system)
            await demonstrate_drawdown_protection(system)
            await demonstrate_error_recovery(system)
            await demonstrate_emergency_procedures(system)
            
        finally:
            # Stop system
            await system.stop()
            logger.info("Trading system stopped")
        
    except Exception as e:
        logger.exception(f"Error in demonstration: {e}")
    
    logger.info("Risk Management Demonstration completed")


if __name__ == "__main__":
    asyncio.run(main())
