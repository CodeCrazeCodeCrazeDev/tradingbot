"""
Offline RL Demo

Demonstrates training and evaluation of offline RL agents.
"""

import os
import sys
import logging
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.ml.offline_rl import (
    OfflineRLDataset,
    build_dataset_from_trades,
    ReplayBuffer,
    CQLAgent,
    BCQAgent,
    ImportanceSampling,
    DoublyRobust,
    FittedQEvaluation,
    PolicySelector
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_synthetic_dataset(n_samples=5000):
    pass
    """
    Create synthetic dataset for demo purposes.
    
    Args:
    pass
        n_samples: Number of samples
    
    Returns:
    pass
        OfflineRLDataset
    """
    logger.info(f"Creating synthetic dataset with {n_samples} samples")
    
    # Define feature names
    feature_names = [
        'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower',
        'atr', 'volume_ratio', 'price_change', 'trend_strength'
    ]
    
    # Create random states
    states = np.random.randn(n_samples, len(feature_names))
    
    # Create actions (0: long, 1: short, 2: hold)
    actions = np.random.choice([0, 1, 2], size=n_samples)
    
    # Create rewards based on actions and states
    rewards = np.zeros(n_samples)
    
    for i in range(n_samples):
    pass
        if actions[i] == 0:  # long
            # Reward is positive if trend is up (positive price_change)
            rewards[i] = 0.5 * states[i, 7] + 0.2 * states[i, 8] + np.random.randn() * 0.2
        elif actions[i] == 1:  # short
            # Reward is positive if trend is down (negative price_change)
            rewards[i] = -0.5 * states[i, 7] + 0.2 * states[i, 8] + np.random.randn() * 0.2
        else:  # hold
            # Small reward for holding
            rewards[i] = 0.1 + np.random.randn() * 0.05
    
    # Create next states (simple transition model)
    next_states = states.copy()
    for i in range(n_samples):
    pass
        next_states[i] += np.random.randn(len(feature_names)) * 0.1
    
    # All transitions are terminal for simplicity
    dones = np.ones(n_samples, dtype=bool)
    
    # Create info dict
    info = {
        'timestamps': np.array([datetime.now().isoformat() for _ in range(n_samples)]),
        'symbols': np.array(['EURUSD' for _ in range(n_samples)]),
        'trade_ids': np.array([f'trade_{i}' for i in range(n_samples)])
    }
    
    # Create dataset
    dataset = OfflineRLDataset(
        states=states,
        actions=actions,
        rewards=rewards,
        next_states=next_states,
        dones=dones,
        info=info,
        feature_names=feature_names,
        action_names=['long', 'short', 'hold']
    )
    
    logger.info(f"Created synthetic dataset with {dataset.num_samples} samples")
    return dataset


def train_and_evaluate_agents(dataset):
    pass
    """
    Train and evaluate offline RL agents.
    
    Args:
    pass
        dataset: Dataset to train on
    
    Returns:
    pass
        Dictionary of trained agents
    """
    logger.info("Training and evaluating agents")
    
    # Split dataset
    train, val, test = dataset.split()
    
    # Create agents
    state_dim = dataset.states.shape[1]
    action_dim = 3  # long, short, hold
    
    agents = {}
    
    # Train CQL agent
    logger.info("Training CQL agent")
    cql_agent = CQLAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        alpha=1.0,
        log_dir="logs/offline_rl/cql"
    )
    cql_metrics = cql_agent.train(train, n_epochs=50, eval_dataset=val)
    agents['cql'] = cql_agent
    
    # Train BCQ agent
    logger.info("Training BCQ agent")
    bcq_agent = BCQAgent(
        state_dim=state_dim,
        action_dim=action_dim,
        threshold=0.3,
        log_dir="logs/offline_rl/bcq"
    )
    bcq_metrics = bcq_agent.train(train, n_epochs=50, eval_dataset=val)
    agents['bcq'] = bcq_agent
    
    # Create baseline agent (random policy)
    class RandomAgent:
    pass
        def __init__(self, action_dim):
    pass
            self.action_dim = action_dim
        
        def predict(self, state):
    pass
            return np.random.randint(0, self.action_dim)
        
        def predict_batch(self, states):
    pass
            return np.random.randint(0, self.action_dim, size=len(states))
        
        def predict_proba(self, states):
    pass
            batch_size = states.shape[0]
            return np.ones((batch_size, self.action_dim)) / self.action_dim
    
    agents['random'] = RandomAgent(action_dim)
    
    # Evaluate agents using OPE
    logger.info("Evaluating agents using OPE")
    policy_selector = PolicySelector(methods=['is', 'dr', 'fqe'])
    
    evaluation_results = policy_selector.evaluate_policies(
        test,
        policies=agents
    )
    
    best_policy = policy_selector.select_best_policy(evaluation_results)
    policy_selector.generate_report(evaluation_results, best_policy)
    
    logger.info(f"Best policy: {best_policy}")
    
    # Save agents
    os.makedirs("models/offline_rl", exist_ok=True)
    for name, agent in agents.items():
    pass
        if hasattr(agent, 'save'):
    pass
            agent.save(f"models/offline_rl/{name}")
    
    return agents, evaluation_results, best_policy


def compare_agent_actions(agents, dataset):
    pass
    """
    Compare actions from different agents.
    
    Args:
    pass
        agents: Dictionary of agents
        dataset: Dataset to evaluate on
    """
    logger.info("Comparing agent actions")
    
    # Select 5 random states
    indices = np.random.choice(dataset.num_samples, 5)
    states = dataset.states[indices]
    
    # Get actions from each agent
    actions = {}
    for name, agent in agents.items():
    pass
        actions[name] = agent.predict_batch(states)
    
    # Print comparison
    print("\nAction Comparison:")
    print("-" * 50)
    print(f"{'State':10} | {'Original':10} | {'CQL':10} | {'BCQ':10} | {'Random':10}")
    print("-" * 50)
    
    action_names = dataset.action_names
    original_actions = dataset.actions[indices]
    
    for i in range(len(indices)):
    pass
        print(f"{i:10} | {action_names[original_actions[i]]:10} | {action_names[actions['cql'][i]]:10} | {action_names[actions['bcq'][i]]:10} | {action_names[actions['random'][i]]:10}")
    
    print("-" * 50)


def visualize_q_values(agents, dataset):
    pass
    """
    Visualize Q-values from different agents.
    
    Args:
    pass
        agents: Dictionary of agents
        dataset: Dataset to evaluate on
    """
    try:
    pass
        import torch
import numpy
        
        logger.info("Visualizing Q-values")
        
        # Select a random state
        idx = np.random.choice(dataset.num_samples)
        state = dataset.states[idx]
        
        # Get Q-values
        q_values = {}
        
        # For CQL
        if 'cql' in agents and hasattr(agents['cql'], 'q_network'):
    pass
            with torch.no_grad():
    pass
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                if agents['cql'].use_gpu:
    pass
                    state_tensor = state_tensor.cuda()
                q_values['cql'] = agents['cql'].q_network(state_tensor).cpu().numpy()[0]
        elif 'cql' in agents and hasattr(agents['cql'], 'model'):
    pass
            q_values['cql'] = agents['cql'].model.predict_value([state])[0]
        
        # For BCQ
        if 'bcq' in agents and hasattr(agents['bcq'], 'q_network'):
    pass
            with torch.no_grad():
    pass
                state_tensor = torch.FloatTensor(state).unsqueeze(0)
                if agents['bcq'].use_gpu:
    pass
                    state_tensor = state_tensor.cuda()
                q_values['bcq'] = agents['bcq'].q_network(state_tensor).cpu().numpy()[0]
        elif 'bcq' in agents and hasattr(agents['bcq'], 'model'):
    pass
            q_values['bcq'] = agents['bcq'].model.predict_value([state])[0]
        
        # Create visualization
        if q_values:
    pass
            plt.figure(figsize=(10, 6))
            
            action_names = dataset.action_names
            x = np.arange(len(action_names))
            width = 0.35
            
            for i, (name, values) in enumerate(q_values.items()):
    pass
                plt.bar(x + i * width, values, width, label=name.upper())
            
            plt.xlabel('Actions')
            plt.ylabel('Q-Values')
            plt.title('Q-Values Comparison')
            plt.xticks(x + width / 2, action_names)
            plt.legend()
            
            plt.tight_layout()
            plt.savefig("logs/offline_rl/q_values_comparison.png")
            plt.close()
            
            logger.info("Q-values visualization saved to logs/offline_rl/q_values_comparison.png")
    
    pass
        logger.error(f"Failed to visualize Q-values: {e}")


def main():
    pass
    """Run offline RL demo."""
    print("\n" + "=" * 80)
    print("OFFLINE RL DEMONSTRATION")
    print("=" * 80)
    
    try:
    pass
        # Create output directories
        os.makedirs("logs/offline_rl", exist_ok=True)
        os.makedirs("data/offline_rl", exist_ok=True)
        os.makedirs("models/offline_rl", exist_ok=True)
        
        # Step 1: Create synthetic dataset
        print("\n📊 Step 1: Creating dataset...")
        dataset = create_synthetic_dataset(n_samples=5000)
        
        # Save dataset
        dataset.save("data/offline_rl/synthetic_dataset.npz")
        
        # Step 2: Train and evaluate agents
        print("\n🤖 Step 2: Training agents...")
        agents, evaluation_results, best_policy = train_and_evaluate_agents(dataset)
        
        # Step 3: Compare agent actions
        print("\n🔍 Step 3: Comparing agent actions...")
        compare_agent_actions(agents, dataset)
        
        # Step 4: Visualize Q-values
        print("\n📈 Step 4: Visualizing Q-values...")
        visualize_q_values(agents, dataset)
        
        print("\n✅ Demo complete!")
        print(f"Best policy: {best_policy}")
        print("Results saved to logs/offline_rl/")
        
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
    print("1. Review the policy evaluation results")
    print("2. Deploy the best policy to paper trading")
    print("3. Proceed to TFT forecasting implementation")
    print("=" * 80)


if __name__ == "__main__":
    pass
    main()
