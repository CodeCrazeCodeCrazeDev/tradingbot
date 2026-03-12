"""
AlphaAlgo Autonomous Offline RL System

Complete autonomous trading system that:
1. Continuously collects live trading data
2. Trains multiple candidate policies offline (CQL, IQL, BCQ)
3. Evaluates policies with FQE, DR, WIS, and CVaR metrics
4. Deploys only safe, validated policies
5. Monitors performance and auto-rollbacks if needed
6. Self-improves through continuous learning

This is the master controller for AlphaAlgo's autonomous evolution.
"""

import os
import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import threading
from collections import deque

logger = logging.getLogger(__name__)

try:
    from .continuous_learning_orchestrator import ContinuousLearningOrchestrator
    from .cql_agent import CQLAgent
    from .bcq_agent import BCQAgent
    from .iql_agent import IQLAgent
    from .dataset_builder import OfflineRLDataset, build_dataset_from_trades
    from .ope import ImportanceSampling, DoublyRobust, FittedQEvaluation
    from .policy_selector import PolicySelector
    from .risk_adjusted_ope import CVaRPolicyEvaluator, RiskAdjustedPolicySelector
    from .replay_buffer import ReplayBuffer
except ImportError as e:
    logger.error(f"Failed to import offline RL components: {e}")


class AlphaAlgoAutonomousSystem:
    """
    Master autonomous system for AlphaAlgo.
    
    Manages the complete lifecycle:
    - Data collection from live trading
    - Offline policy training
    - Risk-adjusted evaluation
    - Safe deployment
    - Performance monitoring
    - Automatic rollback
    - Continuous improvement
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AlphaAlgo autonomous system.
        
        Args:
            state_dim: State dimension (market features)
            action_dim: Action dimension (hold, buy, sell, etc.)
            config: System configuration
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.config = config or {}
        
        # Directories
        self.base_dir = Path(self.config.get('base_dir', 'alphaalgo_autonomous'))
        self.log_dir = self.base_dir / 'logs'
        self.model_dir = self.base_dir / 'models'
        self.data_dir = self.base_dir / 'data'
        self.report_dir = self.base_dir / 'reports'
        
        for dir_path in [self.log_dir, self.model_dir, self.data_dir, self.report_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # Core components
        self.orchestrator = ContinuousLearningOrchestrator(
            state_dim=state_dim,
            action_dim=action_dim,
            buffer_size=self.config.get('buffer_size', 100000),
            min_buffer_size=self.config.get('min_buffer_size', 10000),
            training_interval_hours=self.config.get('training_interval_hours', 24),
            evaluation_window=self.config.get('evaluation_window', 100),
            safety_thresholds=self.config.get('safety_thresholds'),
            log_dir=str(self.log_dir / 'orchestrator'),
            model_dir=str(self.model_dir)
        )
        
        # State tracking
        self.is_running = False
        self.last_training_time = None
        self.training_thread = None
        self.monitoring_thread = None
        
        # Performance tracking
        self.live_performance = deque(maxlen=1000)
        self.deployment_history = []
        self.rollback_history = []
        
        # Statistics
        self.stats = {
            'total_trades': 0,
            'successful_trades': 0,
            'failed_trades': 0,
            'total_training_cycles': 0,
            'total_deployments': 0,
            'total_rollbacks': 0,
            'current_policy': None,
            'system_uptime': 0,
            'last_update': None
        }
        
        logger.info("="*80)
        logger.info("ALPHAALGO AUTONOMOUS SYSTEM INITIALIZED")
        logger.info("="*80)
        logger.info(f"State dim: {state_dim}, Action dim: {action_dim}")
        logger.info(f"Base directory: {self.base_dir}")
        logger.info(f"Training interval: {self.config.get('training_interval_hours', 24)}h")
        logger.info("="*80)
    
    def start(self):
        """Start the autonomous system."""
        if self.is_running:
            logger.warning("System already running")
            return
        
        self.is_running = True
        self.start_time = time.time()
        
        logger.info("\n" + "="*80)
        logger.info("STARTING ALPHAALGO AUTONOMOUS SYSTEM")
        logger.info("="*80)
        
        # Start background threads
        self.training_thread = threading.Thread(target=self._training_loop, daemon=True)
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        
        self.training_thread.start()
        self.monitoring_thread.start()
        
        logger.info("✅ Autonomous system started")
        logger.info("   - Training loop: ACTIVE")
        logger.info("   - Monitoring loop: ACTIVE")
        logger.info("="*80)
    
    def stop(self):
        """Stop the autonomous system."""
        logger.info("\n" + "="*80)
        logger.info("STOPPING ALPHAALGO AUTONOMOUS SYSTEM")
        logger.info("="*80)
        
        self.is_running = False
        
        # Wait for threads to finish
        if self.training_thread:
            self.training_thread.join(timeout=5)
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        # Save final state
        self._save_system_state()
        
        logger.info("✅ Autonomous system stopped")
        logger.info("="*80)
    
    def collect_trade_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool,
        info: Optional[Dict] = None
    ):
        """
        Collect experience from live trading.
        
        Args:
            state: Current market state
            action: Action taken
            reward: Reward received
            next_state: Next market state
            done: Episode done flag
            info: Additional information
        """
        # Pass to orchestrator
        self.orchestrator.collect_experience(state, action, reward, next_state, done)
        
        # Update statistics
        self.stats['total_trades'] += 1
        if reward > 0:
            self.stats['successful_trades'] += 1
        else:
            self.stats['failed_trades'] += 1
        
        # Track live performance
        self.live_performance.append(reward)
        
        # Log periodically
        if self.stats['total_trades'] % 100 == 0:
            avg_reward = np.mean(list(self.live_performance)[-100:])
            logger.info(f"📊 Trades: {self.stats['total_trades']}, "
                       f"Avg Reward (last 100): {avg_reward:.4f}, "
                       f"Buffer: {len(self.orchestrator.data_buffer['states'])}")
    
    def get_action(self, state: np.ndarray) -> int:
        """
        Get action from deployed policy.
        
        Args:
            state: Current market state
        
        Returns:
            Action to take
        """
        return self.orchestrator.get_action(state)
    
    def _training_loop(self):
        """Background training loop."""
        logger.info("🔄 Training loop started")
        
        while self.is_running:
            try:
                # Check if it's time to train
                should_train = False
                
                if self.last_training_time is None:
                    # First training when enough data
                    should_train = self.orchestrator.can_train()
                else:
                    # Periodic training
                    hours_since_training = (time.time() - self.last_training_time) / 3600
                    should_train = (
                        hours_since_training >= self.config.get('training_interval_hours', 24)
                        and self.orchestrator.can_train()
                    )
                
                if should_train:
                    logger.info("\n" + "🚀 " + "="*78)
                    logger.info("INITIATING TRAINING CYCLE")
                    logger.info("="*80)
                    
                    # Run training cycle
                    self.orchestrator.run_training_cycle(
                        n_epochs=self.config.get('training_epochs', 50)
                    )
                    
                    # Update tracking
                    self.last_training_time = time.time()
                    self.stats['total_training_cycles'] += 1
                    self.stats['total_deployments'] += 1
                    self.stats['current_policy'] = self.orchestrator.deployed_policy_name
                    self.stats['last_update'] = datetime.now().isoformat()
                    
                    # Save state
                    self._save_system_state()
                    
                    # Generate report
                    self._generate_training_report()
                    
                    logger.info("✅ Training cycle complete")
                    logger.info("="*80 + "\n")
                
                # Sleep for a bit
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"❌ Error in training loop: {e}", exc_info=True)
                time.sleep(300)  # Wait 5 minutes on error
    
    def _monitoring_loop(self):
        """Background monitoring loop."""
        logger.info("👁️  Monitoring loop started")
        
        while self.is_running:
            try:
                # Monitor deployed policy performance
                if len(self.live_performance) >= self.config.get('evaluation_window', 100):
                    recent_rewards = list(self.live_performance)[-100:]
                    avg_reward = np.mean(recent_rewards)
                    
                    # Check performance with orchestrator
                    is_acceptable = self.orchestrator.monitor_performance(avg_reward)
                    
                    if not is_acceptable:
                        logger.error("\n" + "⚠️ " + "="*78)
                        logger.error("PERFORMANCE DEGRADATION DETECTED")
                        logger.error("="*80)
                        logger.error(f"Average reward: {avg_reward:.4f}")
                        logger.error("Initiating automatic rollback...")
                        
                        # Rollback
                        self.orchestrator.rollback_policy()
                        
                        # Track rollback
                        self.stats['total_rollbacks'] += 1
                        self.rollback_history.append({
                            'timestamp': datetime.now().isoformat(),
                            'reason': 'performance_degradation',
                            'avg_reward': avg_reward,
                            'previous_policy': self.stats['current_policy']
                        })
                        
                        # Update stats
                        self.stats['current_policy'] = self.orchestrator.deployed_policy_name
                        
                        logger.error("✅ Rollback complete")
                        logger.error("="*80 + "\n")
                
                # Update uptime
                self.stats['system_uptime'] = time.time() - self.start_time
                
                # Sleep
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)
    
    def _save_system_state(self):
        """Save system state to disk."""
        try:
            state = {
                'stats': self.stats,
                'deployment_history': self.deployment_history,
                'rollback_history': self.rollback_history,
                'config': self.config,
                'last_training_time': self.last_training_time,
                'timestamp': datetime.now().isoformat()
            }
            
            state_path = self.data_dir / 'system_state.json'
            with open(state_path, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.debug(f"💾 System state saved to {state_path}")
            
        except Exception as e:
            logger.error(f"Failed to save system state: {e}")
    
    def _generate_training_report(self):
        """Generate training report."""
        try:
            report = []
            report.append("="*80)
            report.append("ALPHAALGO TRAINING REPORT")
            report.append("="*80)
            report.append(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            report.append(f"Training Cycle: #{self.stats['total_training_cycles']}")
            report.append("")
            
            report.append("SYSTEM STATISTICS")
            report.append("-"*80)
            report.append(f"Total Trades: {self.stats['total_trades']}")
            report.append(f"Successful Trades: {self.stats['successful_trades']}")
            report.append(f"Failed Trades: {self.stats['failed_trades']}")
            report.append(f"Success Rate: {self.stats['successful_trades']/max(1, self.stats['total_trades'])*100:.2f}%")
            report.append(f"Total Deployments: {self.stats['total_deployments']}")
            report.append(f"Total Rollbacks: {self.stats['total_rollbacks']}")
            report.append(f"Current Policy: {self.stats['current_policy']}")
            report.append(f"System Uptime: {self.stats['system_uptime']/3600:.2f} hours")
            report.append("")
            
            report.append("PERFORMANCE METRICS")
            report.append("-"*80)
            if len(self.live_performance) > 0:
                perf = list(self.live_performance)
                report.append(f"Mean Reward: {np.mean(perf):.4f}")
                report.append(f"Std Reward: {np.std(perf):.4f}")
                report.append(f"Min Reward: {np.min(perf):.4f}")
                report.append(f"Max Reward: {np.max(perf):.4f}")
                report.append(f"Sharpe Ratio: {np.mean(perf)/max(np.std(perf), 1e-8):.4f}")
            report.append("")
            
            report.append("BUFFER STATUS")
            report.append("-"*80)
            report.append(f"Buffer Size: {len(self.orchestrator.data_buffer['states'])}")
            report.append(f"Buffer Capacity: {self.orchestrator.buffer_size}")
            report.append(f"Buffer Usage: {len(self.orchestrator.data_buffer['states'])/self.orchestrator.buffer_size*100:.1f}%")
            report.append("")
            
            report.append("="*80)
            
            # Save report
            report_text = "\n".join(report)
            report_path = self.report_dir / f"training_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(report_path, 'w') as f:
                f.write(report_text)
            
            logger.info(f"📊 Training report saved to {report_path}")
            
            # Also log to console
            logger.info("\n" + report_text)
            
        except Exception as e:
            logger.error(f"Failed to generate training report: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status.
        
        Returns:
            Dictionary with system status
        """
        return {
            'is_running': self.is_running,
            'stats': self.stats.copy(),
            'buffer_size': len(self.orchestrator.data_buffer['states']),
            'deployed_policy': self.orchestrator.deployed_policy_name,
            'last_training': datetime.fromtimestamp(self.last_training_time).isoformat() if self.last_training_time else None,
            'recent_performance': {
                'mean': float(np.mean(list(self.live_performance))) if self.live_performance else 0.0,
                'std': float(np.std(list(self.live_performance))) if self.live_performance else 0.0,
                'count': len(self.live_performance)
            }
        }
    
    def force_training(self):
        """Force immediate training cycle (for testing/manual trigger)."""
        logger.info("🔧 Manual training trigger activated")
        
        if not self.orchestrator.can_train():
            logger.warning("⚠️  Insufficient data for training")
            return False
        try:
        
            self.orchestrator.run_training_cycle(
                n_epochs=self.config.get('training_epochs', 50)
            )
            
            self.last_training_time = time.time()
            self.stats['total_training_cycles'] += 1
            self.stats['total_deployments'] += 1
            self.stats['current_policy'] = self.orchestrator.deployed_policy_name
            
            self._save_system_state()
            self._generate_training_report()
            
            logger.info("✅ Manual training complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Manual training failed: {e}", exc_info=True)
            return False
    
    def export_metrics(self) -> pd.DataFrame:
        """
        Export performance metrics as DataFrame.
        
        Returns:
            DataFrame with metrics
        """
        metrics = {
            'timestamp': [datetime.now()],
            'total_trades': [self.stats['total_trades']],
            'successful_trades': [self.stats['successful_trades']],
            'success_rate': [self.stats['successful_trades']/max(1, self.stats['total_trades'])],
            'training_cycles': [self.stats['total_training_cycles']],
            'deployments': [self.stats['total_deployments']],
            'rollbacks': [self.stats['total_rollbacks']],
            'current_policy': [self.stats['current_policy']],
            'buffer_size': [len(self.orchestrator.data_buffer['states'])],
            'mean_reward': [np.mean(list(self.live_performance)) if self.live_performance else 0.0],
            'std_reward': [np.std(list(self.live_performance)) if self.live_performance else 0.0]
        }
        
        return pd.DataFrame(metrics)


# Convenience function for quick initialization
def create_alphaalgo_system(
    state_dim: int = 50,
    action_dim: int = 3,
    config: Optional[Dict[str, Any]] = None
) -> AlphaAlgoAutonomousSystem:
    """
    Create and initialize AlphaAlgo autonomous system.
    
    Args:
        state_dim: State dimension
        action_dim: Action dimension (default: 3 for hold/buy/sell)
        config: System configuration
    
    Returns:
        Initialized AlphaAlgo system
    """
    default_config = {
        'buffer_size': 100000,
        'min_buffer_size': 10000,
        'training_interval_hours': 24,
        'training_epochs': 50,
        'evaluation_window': 100,
        'safety_thresholds': {
            'min_mean_return': 0.0,
            'max_cvar': -0.15,
            'min_sharpe': 0.3,
            'max_drawdown': -0.25
        }
    }
    
    if config:
        default_config.update(config)
    
    return AlphaAlgoAutonomousSystem(
        state_dim=state_dim,
        action_dim=action_dim,
        config=default_config
    )


if __name__ == "__main__":
    # Demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    logger.info("ALPHAALGO AUTONOMOUS SYSTEM DEMO")
    print("="*80)
    
    # Create system
    system = create_alphaalgo_system(state_dim=20, action_dim=3)
    
    # Start system
    system.start()
    
    # Simulate trading
    logger.info("\nSimulating live trading...")
    for i in range(2000):
        state = np.random.randn(20)
        action = system.get_action(state)
        reward = np.random.randn() * 0.1
        next_state = np.random.randn(20)
        done = np.random.rand() < 0.05
        
        system.collect_trade_experience(state, action, reward, next_state, done)
        
        if (i + 1) % 500 == 0:
            logger.info(f"  Collected {i+1} experiences...")
    
    # Force training
    logger.info("\nForcing training cycle...")
    system.force_training()
    
    # Get status
    logger.info("\nSystem Status:")
    status = system.get_status()
    for key, value in status.items():
        logger.info(f"  {key}: {value}")
    
    # Export metrics
    logger.info("\nExporting metrics...")
    metrics_df = system.export_metrics()
    print(metrics_df.to_string())
    
    # Stop system
    logger.info("\nStopping system...")
    system.stop()
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE!")
    print("="*80)
