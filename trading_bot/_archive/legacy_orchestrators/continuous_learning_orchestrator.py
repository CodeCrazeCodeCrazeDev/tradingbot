"""
from typing import Any, Optional, Set, Tuple
Continuous Learning Orchestrator

Autonomous system that:
1. Collects live trading data into offline buffer
2. Trains multiple candidate policies offline
3. Evaluates all policies with FQE, DR, and CVaR metrics
4. Deploys only the top-performing, safe policy
5. Monitors performance and rolls back if needed
"""

import os
import logging
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
import json
import time
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)

try:
    from .cql_agent import CQLAgent
    from .bcq_agent import BCQAgent
    from .iql_agent import IQLAgent
    from .dataset_builder import OfflineRLDataset, build_dataset_from_trades
    from .ope import ImportanceSampling, DoublyRobust, FittedQEvaluation
    from .policy_selector import PolicySelector
    from .risk_adjusted_ope import CVaRPolicyEvaluator, RiskAdjustedPolicySelector
except ImportError as e:
    logger.error(f"Failed to import offline RL components: {e}")


class ContinuousLearningOrchestrator:
    """
    Orchestrates continuous learning loop for AlphaAlgo.
    
    Workflow:
    1. Collect data → Offline buffer
    2. Train candidate policies (CQL, BCQ, IQL)
    3. Evaluate with FQE, DR, WIS, CVaR
    4. Select best safe policy
    5. Deploy and monitor
    6. Rollback if performance drops
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        buffer_size: int = 100000,
        min_buffer_size: int = 10000,
        training_interval_hours: int = 24,
        evaluation_window: int = 100,
        safety_thresholds: Optional[Dict[str, float]] = None,
        log_dir: str = "logs/continuous_learning",
        model_dir: str = "models/offline_rl"
    ):
        """
        Initialize orchestrator.
        
        Args:
            state_dim: State dimension
            action_dim: Action dimension
            buffer_size: Maximum buffer size
            min_buffer_size: Minimum data before training
            training_interval_hours: Hours between training cycles
            evaluation_window: Number of trades for performance monitoring
            safety_thresholds: Safety criteria for deployment
            log_dir: Directory for logs
            model_dir: Directory for model checkpoints
        """
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.buffer_size = buffer_size
        self.min_buffer_size = min_buffer_size
        self.training_interval_hours = training_interval_hours
        self.evaluation_window = evaluation_window
        
        # Safety thresholds
        self.safety_thresholds = safety_thresholds or {
            'min_mean_return': 0.0,
            'max_cvar': -0.15,
            'min_sharpe': 0.3,
            'max_drawdown': -0.25
        }
        
        # Directories
        self.log_dir = Path(log_dir)
        self.model_dir = Path(model_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        # Data buffer
        self.data_buffer = {
            'states': [],
            'actions': [],
            'rewards': [],
            'next_states': [],
            'dones': []
        }
        
        # Current deployed policy
        self.deployed_policy = None
        self.deployed_policy_name = None
        self.deployment_timestamp = None
        
        # Performance tracking
        self.performance_history = []
        self.baseline_performance = None
        
        # Training history
        self.training_history = []
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        # Running flag
        self.is_running = False
        
        logger.info("="*60)
        logger.info("CONTINUOUS LEARNING ORCHESTRATOR INITIALIZED")
        logger.info("="*60)
        logger.info(f"State dim: {state_dim}, Action dim: {action_dim}")
        logger.info(f"Buffer size: {buffer_size}, Min buffer: {min_buffer_size}")
        logger.info(f"Training interval: {training_interval_hours}h")
        logger.info(f"Safety thresholds: {self.safety_thresholds}")
        logger.info("="*60)
    
    def collect_experience(
        self,
        state: np.ndarray,
        action: int,
        reward: float,
        next_state: np.ndarray,
        done: bool
    ):
        """
        Collect experience from live trading.
        
        Args:
            state: Current state
            action: Action taken
            reward: Reward received
            next_state: Next state
            done: Episode done flag
        """
        with self.lock:
            self.data_buffer['states'].append(state)
            self.data_buffer['actions'].append(action)
            self.data_buffer['rewards'].append(reward)
            self.data_buffer['next_states'].append(next_state)
            self.data_buffer['dones'].append(done)
            
            # Limit buffer size
            if len(self.data_buffer['states']) > self.buffer_size:
                for key in self.data_buffer:
                    self.data_buffer[key] = self.data_buffer[key][-self.buffer_size:]
            
            if len(self.data_buffer['states']) % 1000 == 0:
                logger.info(f"Buffer size: {len(self.data_buffer['states'])}/{self.buffer_size}")
    
    def can_train(self) -> bool:
        """Check if enough data collected for training."""
        with self.lock:
            buffer_size = len(self.data_buffer['states'])
        
        return buffer_size >= self.min_buffer_size
    
    def train_candidate_policies(self, n_epochs: int = 50) -> Dict[str, Any]:
        """
        Train multiple candidate policies.
        
        Args:
            n_epochs: Number of training epochs
        
        Returns:
            Dictionary of trained policies
        """
        logger.info("\n" + "="*60)
        logger.info("TRAINING CANDIDATE POLICIES")
        logger.info("="*60)
        
        # Create dataset
        with self.lock:
            dataset = OfflineRLDataset(
                states=np.array(self.data_buffer['states']),
                actions=np.array(self.data_buffer['actions']),
                rewards=np.array(self.data_buffer['rewards']),
                next_states=np.array(self.data_buffer['next_states']),
                dones=np.array(self.data_buffer['dones']),
                action_names=['hold', 'buy', 'sell']  # Adjust as needed
            )
        
        logger.info(f"Dataset size: {len(dataset.states)} transitions")
        
        policies = {}
        
        try:
            # Train CQL
            logger.info("\n--- Training CQL Agent ---")
            cql = CQLAgent(
                state_dim=self.state_dim,
                action_dim=self.action_dim,
                alpha=1.0,
                log_dir=str(self.log_dir / "cql"),
                use_d3rlpy=True
            )
            cql.train(dataset, n_epochs=n_epochs)
            policies['CQL'] = cql
            logger.info("✅ CQL training complete")
        except Exception as e:
            logger.error(f"❌ CQL training failed: {e}")
        # Train BCQ
            logger.info("\n--- Training BCQ Agent ---")
            bcq = BCQAgent(
                state_dim=self.state_dim,
                action_dim=self.action_dim,
                log_dir=str(self.log_dir / "bcq"),
                use_d3rlpy=True
            )
            bcq.train(dataset, n_epochs=n_epochs)
            policies['BCQ'] = bcq
            logger.info("✅ BCQ training complete")
        except Exception as e:
            logger.error(f"❌ BCQ training failed: {e}")
        # Train IQL
            logger.info("\n--- Training IQL Agent ---")
            iql = IQLAgent(
                state_dim=self.state_dim,
                action_dim=self.action_dim,
                expectile=0.7,
                log_dir=str(self.log_dir / "iql"),
                use_d3rlpy=True
            )
            iql.train(dataset, n_epochs=n_epochs)
            policies['IQL'] = iql
            logger.info("✅ IQL training complete")
        except Exception as e:
            logger.error(f"❌ IQL training failed: {e}")
        
        logger.info(f"\n✅ Trained {len(policies)} candidate policies")
        
        return policies, dataset
    
    def evaluate_and_select_policy(
        self,
        policies: Dict[str, Any],
        dataset
    ) -> Tuple[Optional[str], Optional[Any], Dict]:
        """
        Evaluate all policies and select best safe one.
        
        Args:
            policies: Dictionary of candidate policies
            dataset: Evaluation dataset
        
        Returns:
            Tuple of (policy_name, policy, evaluation_results)
        """
        logger.info("\n" + "="*60)
        logger.info("EVALUATING POLICIES")
        logger.info("="*60)
        
        # Risk-adjusted evaluation
        selector = RiskAdjustedPolicySelector(
            weights={
                'mean_return': 0.3,
                'sharpe': 0.3,
                'sortino': 0.2,
                'cvar': 0.2
            },
            alpha=0.05
        )
        
        best_policy_name, all_metrics = selector.select_best_policy(
            dataset,
            policies,
            safety_thresholds=self.safety_thresholds
        )
        
        if best_policy_name is None:
            logger.error("❌ No safe policy found!")
            return None, None, all_metrics
        
        # Generate report
        report = selector.compare_policies(all_metrics)
        
        # Save report
        report_path = self.log_dir / f"policy_evaluation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"📊 Evaluation report saved: {report_path}")
        
        # Save metrics
        metrics_path = self.log_dir / f"policy_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_path, 'w') as f:
            json.dump(all_metrics, f, indent=2)
        
        return best_policy_name, policies[best_policy_name], all_metrics
    
    def deploy_policy(self, policy_name: str, policy: Any):
        """
        Deploy selected policy.
        
        Args:
            policy_name: Name of policy
            policy: Policy object
        """
        logger.info("\n" + "="*60)
        logger.info(f"DEPLOYING POLICY: {policy_name}")
        logger.info("="*60)
        
        # Save current policy as backup
        if self.deployed_policy is not None:
            backup_path = self.model_dir / f"backup_{self.deployed_policy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.deployed_policy.save(str(backup_path))
            logger.info(f"💾 Backup saved: {backup_path}")
        
        # Deploy new policy
        with self.lock:
            self.deployed_policy = policy
            self.deployed_policy_name = policy_name
            self.deployment_timestamp = datetime.now()
        
        # Save deployed policy
        deploy_path = self.model_dir / "deployed_policy"
        policy.save(str(deploy_path))
        
        # Save metadata
        metadata = {
            'policy_name': policy_name,
            'deployment_timestamp': self.deployment_timestamp.isoformat(),
            'state_dim': self.state_dim,
            'action_dim': self.action_dim
        }
        
        with open(self.model_dir / "deployed_policy_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Reset performance tracking
        self.performance_history = []
        self.baseline_performance = None
        
        logger.info(f"✅ Policy {policy_name} deployed successfully")
        logger.info(f"📅 Deployment time: {self.deployment_timestamp}")
    
    def monitor_performance(self, reward: float) -> bool:
        """
        Monitor deployed policy performance.
        
        Args:
            reward: Latest reward
        
        Returns:
            True if performance acceptable, False if rollback needed
        """
        self.performance_history.append(reward)
        
        # Keep only recent window
        if len(self.performance_history) > self.evaluation_window:
            self.performance_history = self.performance_history[-self.evaluation_window:]
        
        # Need enough data for evaluation
        if len(self.performance_history) < self.evaluation_window:
            return True
        
        # Compute current performance
        current_performance = np.mean(self.performance_history)
        
        # Set baseline on first full window
        if self.baseline_performance is None:
            self.baseline_performance = current_performance
            logger.info(f"📊 Baseline performance set: {self.baseline_performance:.4f}")
            return True
        
        # Check for significant degradation (>20% drop)
        degradation = (current_performance - self.baseline_performance) / abs(self.baseline_performance)
        
        if degradation < -0.20:
            logger.warning(f"⚠️ Performance degradation detected: {degradation:.2%}")
            logger.warning(f"   Baseline: {self.baseline_performance:.4f}, Current: {current_performance:.4f}")
            return False
        
        return True
    
    def rollback_policy(self):
        """Rollback to previous policy."""
        logger.error("\n" + "="*60)
        logger.error("ROLLING BACK POLICY")
        logger.error("="*60)
        
        # Find most recent backup
        backups = list(self.model_dir.glob("backup_*"))
        
        if not backups:
            logger.error("❌ No backup found! Cannot rollback.")
            return
        
        # Sort by timestamp
        backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_backup = backups[0]
        
        logger.info(f"📦 Rolling back to: {latest_backup}")
        
        # Load backup policy
        # Note: Need to determine policy type from backup name
        policy_type = latest_backup.name.split('_')[1]  # e.g., "backup_CQL_..."
        
        if policy_type == 'CQL':
            policy = CQLAgent(self.state_dim, self.action_dim)
        elif policy_type == 'BCQ':
            policy = BCQAgent(self.state_dim, self.action_dim)
        elif policy_type == 'IQL':
            policy = IQLAgent(self.state_dim, self.action_dim)
        else:
            logger.error(f"❌ Unknown policy type: {policy_type}")
            return
        
        policy.load(str(latest_backup))
        
        with self.lock:
            self.deployed_policy = policy
            self.deployed_policy_name = f"{policy_type}_ROLLBACK"
        
        logger.info(f"✅ Rollback complete: {self.deployed_policy_name}")
    
    def run_training_cycle(self, n_epochs: int = 50):
        """
        Run one complete training cycle.
        
        Args:
            n_epochs: Number of training epochs
        """
        logger.info("\n" + "="*80)
        logger.info("STARTING TRAINING CYCLE")
        logger.info("="*80)
        logger.info(f"Timestamp: {datetime.now()}")
        
        cycle_start = time.time()
        
        # Check if enough data
        if not self.can_train():
            logger.warning(f"⚠️ Insufficient data: {len(self.data_buffer['states'])}/{self.min_buffer_size}")
            return
        
        # Train policies
        policies, dataset = self.train_candidate_policies(n_epochs=n_epochs)
        
        if len(policies) == 0:
            logger.error("❌ No policies trained successfully")
            return
        
        # Evaluate and select
        best_name, best_policy, metrics = self.evaluate_and_select_policy(policies, dataset)
        
        if best_policy is None:
            logger.error("❌ No safe policy selected")
            return
        
        # Deploy
        self.deploy_policy(best_name, best_policy)
        
        # Record training cycle
        cycle_time = time.time() - cycle_start
        
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'deployed_policy': best_name,
            'metrics': metrics[best_name],
            'cycle_time': cycle_time,
            'buffer_size': len(self.data_buffer['states'])
        })
        
        # Save training history
        with open(self.log_dir / "training_history.json", 'w') as f:
            json.dump(self.training_history, f, indent=2)
        
        logger.info("\n" + "="*80)
        logger.info(f"✅ TRAINING CYCLE COMPLETE ({cycle_time:.2f}s)")
        logger.info("="*80)
    
    def get_action(self, state: np.ndarray) -> int:
        """
        Get action from deployed policy.
        
        Args:
            state: Current state
        
        Returns:
            Action to take
        """
        with self.lock:
            if self.deployed_policy is None:
                # No policy deployed, return random action
                return np.random.randint(0, self.action_dim)
            
            return self.deployed_policy.predict(state)
    
    def save_state(self):
        """Save orchestrator state."""
        state = {
            'buffer_size': len(self.data_buffer['states']),
            'deployed_policy_name': self.deployed_policy_name,
            'deployment_timestamp': self.deployment_timestamp.isoformat() if self.deployment_timestamp else None,
            'training_history': self.training_history,
            'safety_thresholds': self.safety_thresholds
        }
        
        with open(self.log_dir / "orchestrator_state.json", 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("💾 Orchestrator state saved")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    logger.info("CONTINUOUS LEARNING ORCHESTRATOR DEMO")
    print("="*80)
    
    # Initialize orchestrator
    orchestrator = ContinuousLearningOrchestrator(
        state_dim=20,
        action_dim=3,
        buffer_size=10000,
        min_buffer_size=1000
    )
    
    # Simulate data collection
    logger.info("\nSimulating data collection...")
    for i in range(1500):
        state = np.random.randn(20)
        action = np.random.randint(0, 3)
        reward = np.random.randn() * 0.1
        next_state = np.random.randn(20)
        done = np.random.rand() < 0.1
        
        orchestrator.collect_experience(state, action, reward, next_state, done)
    
    logger.info(f"✅ Collected {len(orchestrator.data_buffer['states'])} experiences")
    
    # Run training cycle
    logger.info("\nRunning training cycle...")
    orchestrator.run_training_cycle(n_epochs=10)
    
    # Test deployed policy
    logger.info("\nTesting deployed policy...")
    test_state = np.random.randn(20)
    action = orchestrator.get_action(test_state)
    logger.info(f"Action selected: {action}")
    
    # Save state
    orchestrator.save_state()
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE!")
    print("="*80)
