"""
Elite Trading Bot - Brain Architecture Demo
Demonstrates the integration of the brain architecture with advanced strategies
"""

import asyncio
import logging
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.brain.brain_architecture import BrainArchitecture
from trading_bot.brain.central_controller import CentralController
from trading_bot.dashboard.strategy_dashboard import StrategyDashboard

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def run_brain_demo(duration_minutes=30):
    pass
    """Run brain architecture demo"""
    logger.info("Starting Brain Architecture Demo")
    
    # Initialize brain
    brain = BrainArchitecture({
        'learning_rate': 0.02,
        'min_decision_interval_minutes': 1,
        'component_weights': {
            'market_regime': 0.15,
            'sentiment': 0.12,
            'alternative_data': 0.13,
            'multi_timeframe_rl': 0.15,
            'liquidity_holography': 0.10,
            'institutional_dna': 0.12,
            'volatility_impulse': 0.08,
            'fractal_momentum': 0.07,
            'multi_agent_rl': 0.08
        }
    })
    
    # Initialize dashboard
    dashboard = StrategyDashboard({
        'port': 8051,
        'update_interval': 5
    })
    
    # Start dashboard
    dashboard.start()
    
    # Add strategies to dashboard
    dashboard.add_strategy("BrainArchitecture")
    
    # Run for specified duration
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    decisions = []
    
    try:
    pass
        while datetime.now() < end_time:
    pass
            # Process each symbol
            for symbol in symbols:
    pass
                # Make decision
                decision = await brain.make_decision(symbol, timeframes)
                
                if decision:
    pass
                    # Store decision
                    decisions.append(decision)
                    
                    # Update dashboard
                    dashboard.add_signal("BrainArchitecture", {
                        'symbol': decision.symbol,
                        'timestamp': decision.timestamp,
                        'signal_type': decision.action,
                        'confidence': decision.confidence,
                        'success': True,
                        'return': np.random.normal(0.01, 0.02)  # Simulated return
                    })
                    
                    # Log decision
                    logger.info(f"Decision for {symbol}: {decision.action} (confidence: {decision.confidence:.2f})")
                    
                    # Simulate performance metrics
                    update_dashboard_metrics(dashboard, "BrainArchitecture", decision)
            
            # Wait before next cycle
            await asyncio.sleep(5)
        
        # Final analysis
        analyze_decisions(decisions)
        
        logger.info("Brain Architecture Demo completed")
        
        # Keep dashboard running
        logger.info("Dashboard running at http://localhost:8051")
        while True:
    pass
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
    pass
        logger.info("Demo stopped by user")
    except Exception as e:
    pass
        logger.error(f"Error in demo: {e}")
    finally:
    pass
        # Save decisions
        save_decisions(decisions)


async def run_controller_demo(duration_minutes=30):
    pass
    """Run central controller demo"""
    logger.info("Starting Central Controller Demo")
    
    # Initialize controller
    controller = CentralController('config/elite_config.yaml')
    
    try:
    pass
        # Start controller
        await controller.start()
    except KeyboardInterrupt:
    pass
        logger.info("Demo stopped by user")
    except Exception as e:
    pass
        logger.error(f"Error in demo: {e}")
    finally:
    pass
        # Stop controller
        await controller.stop()


def update_dashboard_metrics(dashboard, strategy_name, decision):
    pass
    """Update dashboard with simulated metrics"""
    # Simulate equity curve
    equity = 1000000 * (1 + np.random.normal(0.0001, 0.0002))
    drawdown = np.random.uniform(0, 0.02)
    
    # Update metrics
    dashboard.update_strategy(strategy_name, {
        'equity': equity,
        'drawdown': drawdown,
        'total_return': (equity - 1000000) / 1000000,
        'win_rate': np.random.uniform(0.55, 0.65),
        'profit_factor': np.random.uniform(1.2, 1.5),
        'sharpe_ratio': np.random.uniform(1.0, 2.0),
        'max_drawdown': drawdown,
        'recovery_factor': np.random.uniform(1.5, 2.5),
        'avg_trade': np.random.uniform(100, 200),
        'alpha': np.random.uniform(0.01, 0.03)
    })


def analyze_decisions(decisions):
    pass
    """Analyze decisions made by the brain"""
    if not decisions:
    pass
        logger.warning("No decisions to analyze")
        return
    
    # Count actions
    actions = {}
    for decision in decisions:
    pass
        action = decision.action
        if action not in actions:
    pass
            actions[action] = 0
        actions[action] += 1
    
    # Calculate average confidence
    avg_confidence = sum(d.confidence for d in decisions) / len(decisions)
    
    # Calculate component contributions
    components = {}
    for decision in decisions:
    pass
        for component, signal in decision.components.items():
    pass
            if component not in components:
    pass
                components[component] = {'count': 0, 'signals': {}}
            
            components[component]['count'] += 1
            
            if signal not in components[component]['signals']:
    pass
                components[component]['signals'][signal] = 0
            
            components[component]['signals'][signal] += 1
    
    # Print analysis
    logger.info("\n===== Decision Analysis =====")
    logger.info(f"Total decisions: {len(decisions)}")
    logger.info(f"Actions: {actions}")
    logger.info(f"Average confidence: {avg_confidence:.2f}")
    logger.info("\nComponent contributions:")
    
    for component, data in components.items():
    pass
        logger.info(f"  {component}: {data['count']} decisions")
        logger.info(f"    Signals: {data['signals']}")
    
    # Create visualization directory
    os.makedirs('visualizations', exist_ok=True)
    
    # Plot decision distribution
    plt.figure(figsize=(10, 6))
    plt.bar(actions.keys(), actions.values())
    plt.title('Decision Distribution')
    plt.xlabel('Action')
    plt.ylabel('Count')
    plt.savefig('visualizations/decision_distribution.png')
    
    # Plot component contributions
    plt.figure(figsize=(12, 8))
    component_names = list(components.keys())
    component_counts = [components[c]['count'] for c in component_names]
    plt.bar(component_names, component_counts)
    plt.title('Component Contributions')
    plt.xlabel('Component')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig('visualizations/component_contributions.png')
    
    logger.info("Analysis visualizations saved to 'visualizations' directory")


def save_decisions(decisions):
    pass
    """Save decisions to file"""
    if not decisions:
    pass
        return
    
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Convert decisions to serializable format
    serializable_decisions = []
    for decision in decisions:
    pass
        serializable_decisions.append({
            'symbol': decision.symbol,
            'timestamp': decision.timestamp.isoformat(),
            'action': decision.action,
            'confidence': decision.confidence,
            'size': decision.size,
            'price': decision.price,
            'timeframe': decision.timeframe,
            'reasoning': decision.reasoning,
            'components': decision.components
        })
    
    # Save to file
    with open('data/brain_decisions.json', 'w') as f:
    pass
        json.dump(serializable_decisions, f, indent=2)
    
    logger.info(f"Saved {len(decisions)} decisions to data/brain_decisions.json")


if __name__ == "__main__":
    pass
    # Parse command line arguments
    import argparse
import numpy
import pandas
    parser = argparse.ArgumentParser(description='Elite Trading Bot Brain Architecture Demo')
    parser.add_argument('--mode', choices=['brain', 'controller'], default='brain',
                      help='Demo mode: brain or controller')
    parser.add_argument('--duration', type=int, default=30,
                      help='Demo duration in minutes')
    args = parser.parse_args()
    
    # Run selected demo
    if args.mode == 'brain':
    pass
        asyncio.run(run_brain_demo(args.duration))
    else:
    pass
        asyncio.run(run_controller_demo(args.duration))
