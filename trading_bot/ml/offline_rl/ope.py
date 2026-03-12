"""
Offline Policy Evaluation (OPE)

Methods for evaluating policies without live deployment.
"""

import logging
import numpy as np
from typing import Any, Callable, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    logger.warning("PyTorch not available. Install with: pip install torch")
    TORCH_AVAILABLE = False


class OPEMethod(ABC):
    """Base class for OPE methods."""
    
    @abstractmethod
    def evaluate(self, dataset, policy) -> float:
        """
        Evaluate policy on dataset.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Estimated policy value
        """
        pass


class ImportanceSampling(OPEMethod):
    """
    Weighted Importance Sampling (WIS) for OPE.
    
    Reweights historical data based on policy probabilities.
    """
    
    def __init__(self, behavior_policy: Optional[Callable] = None, discount: float = 0.99):
        """
        Initialize WIS.
        
        Args:
            behavior_policy: Behavior policy that generated the data
            discount: Reward discount factor
        """
        self.behavior_policy = behavior_policy
        self.discount = discount
        
        logger.info("Weighted Importance Sampling initialized")
    
    def evaluate(self, dataset, policy) -> float:
        """
        Evaluate policy using WIS.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Estimated policy value
        """
        states = dataset.states
        actions = dataset.actions
        rewards = dataset.rewards
        
        # Get target policy probabilities
        target_probs = self._get_policy_probs(policy, states, actions)
        
        # Get behavior policy probabilities
        if self.behavior_policy:
            behavior_probs = self._get_policy_probs(self.behavior_policy, states, actions)
        else:
            # Assume uniform behavior policy if not provided
            behavior_probs = np.ones_like(target_probs) / dataset.action_names
        
        # Compute importance weights
        weights = target_probs / behavior_probs
        
        # Normalize weights
        normalized_weights = weights / np.sum(weights)
        
        # Compute weighted average of rewards
        estimated_value = np.sum(normalized_weights * rewards)
        
        logger.info(f"WIS estimated policy value: {estimated_value:.4f}")
        return estimated_value
    
    def _get_policy_probs(self, policy, states, actions) -> np.ndarray:
        """
        Get policy probabilities for state-action pairs.
        
        Args:
            policy: Policy to evaluate
            states: States
            actions: Actions
        
        Returns:
            Policy probabilities
        """
        if hasattr(policy, 'predict_proba'):
            # Policy has predict_proba method
            return policy.predict_proba(states)[np.arange(len(actions)), actions]
        else:
            # Policy only has predict method
            predicted_actions = policy.predict_batch(states)
            return (predicted_actions == actions).astype(float)


class DoublyRobust(OPEMethod):
    """
    Doubly Robust (DR) estimator for OPE.
    
    Combines model-based and importance sampling approaches.
    """
    
    def __init__(
        self,
        behavior_policy: Optional[Callable] = None,
        q_function: Optional[Callable] = None,
        discount: float = 0.99
    ):
        """
        Initialize DR.
        
        Args:
            behavior_policy: Behavior policy that generated the data
            q_function: Q-function for model-based estimation
            discount: Reward discount factor
        """
        self.behavior_policy = behavior_policy
        self.q_function = q_function
        self.discount = discount
        
        logger.info("Doubly Robust estimator initialized")
    
    def evaluate(self, dataset, policy) -> float:
        """
        Evaluate policy using DR.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Estimated policy value
        """
        states = dataset.states
        actions = dataset.actions
        rewards = dataset.rewards
        next_states = dataset.next_states
        
        # Train Q-function if not provided
        if self.q_function is None:
            self.q_function = self._train_q_function(dataset)
        
        # Get target policy probabilities
        target_probs = self._get_policy_probs(policy, states, actions)
        
        # Get behavior policy probabilities
        if self.behavior_policy:
            behavior_probs = self._get_policy_probs(self.behavior_policy, states, actions)
        else:
            # Assume uniform behavior policy if not provided
            behavior_probs = np.ones_like(target_probs) / dataset.action_names
        
        # Compute importance weights
        weights = target_probs / behavior_probs
        
        # Get Q-values
        q_values = self._get_q_values(self.q_function, states, actions)
        
        # Get V-values for next states
        next_v_values = self._get_v_values(self.q_function, next_states, policy)
        
        # Compute DR estimate
        direct_method = np.mean(next_v_values)
        is_correction = np.mean(weights * (rewards + self.discount * next_v_values - q_values))
        dr_estimate = direct_method + is_correction
        
        logger.info(f"DR estimated policy value: {dr_estimate:.4f}")
        return dr_estimate
    
    def _train_q_function(self, dataset):
        """
        Train Q-function on dataset.
        
        Args:
            dataset: Dataset to train on
        
        Returns:
            Trained Q-function
        """
        if not TORCH_AVAILABLE:
            logger.error("PyTorch required for Q-function training")
            return None
        
        # Simple Q-network
        class QNetwork(nn.Module):
            def __init__(self, state_dim, action_dim):
                super(QNetwork, self).__init__()
                self.fc1 = nn.Linear(state_dim, 256)
                self.fc2 = nn.Linear(256, 256)
                self.fc3 = nn.Linear(256, action_dim)
            
            def forward(self, x):
                x = F.relu(self.fc1(x))
                x = F.relu(self.fc2(x))
                return self.fc3(x)
        
        # Create and train Q-network
        state_dim = dataset.states.shape[1]
        action_dim = len(dataset.action_names)
        
        q_net = QNetwork(state_dim, action_dim)
        optimizer = optim.Adam(q_net.parameters(), lr=3e-4)
        
        # Convert to tensors
        states = torch.FloatTensor(dataset.states)
        actions = torch.LongTensor(dataset.actions)
        rewards = torch.FloatTensor(dataset.rewards)
        next_states = torch.FloatTensor(dataset.next_states)
        dones = torch.FloatTensor(dataset.dones)
        
        # Training loop
        batch_size = 256
        n_epochs = 100
        
        for epoch in range(n_epochs):
            # Sample batch
            indices = np.random.choice(len(states), batch_size)
            
            batch_states = states[indices]
            batch_actions = actions[indices]
            batch_rewards = rewards[indices]
            batch_next_states = next_states[indices]
            batch_dones = dones[indices]
            
            # Compute Q values
            q_values = q_net(batch_states)
            q_values = q_values.gather(1, batch_actions.unsqueeze(1))
            
            # Compute target Q values
            with torch.no_grad():
                next_q_values = q_net(batch_next_states)
                next_q_values_max = next_q_values.max(1, keepdim=True)[0]
                target_q_values = batch_rewards.unsqueeze(1) + (1 - batch_dones.unsqueeze(1)) * self.discount * next_q_values_max
            
            # Compute loss
            loss = F.mse_loss(q_values, target_q_values)
            
            # Update network
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                logger.debug(f"Q-function training: Epoch {epoch+1}/{n_epochs}, Loss: {loss.item():.4f}")
        
        logger.info("Q-function training complete")
        
        # Create wrapper for Q-function
        class QFunction:
            def __init__(self, q_net):
                self.q_net = q_net
            
            def predict(self, states):
                with torch.no_grad():
                    states_tensor = torch.FloatTensor(states)
                    return self.q_net(states_tensor).numpy()
        
        return QFunction(q_net)
    
    def _get_policy_probs(self, policy, states, actions) -> np.ndarray:
        """Get policy probabilities for state-action pairs."""
        if hasattr(policy, 'predict_proba'):
            # Policy has predict_proba method
            return policy.predict_proba(states)[np.arange(len(actions)), actions]
        else:
            # Policy only has predict method
            predicted_actions = policy.predict_batch(states)
            return (predicted_actions == actions).astype(float)
    
    def _get_q_values(self, q_function, states, actions) -> np.ndarray:
        """Get Q-values for state-action pairs."""
        q_values = q_function.predict(states)
        return q_values[np.arange(len(actions)), actions]
    
    def _get_v_values(self, q_function, states, policy) -> np.ndarray:
        """Get V-values (expected Q-values under policy) for states."""
        q_values = q_function.predict(states)
        
        if hasattr(policy, 'predict_proba'):
            # Policy has predict_proba method
            policy_probs = policy.predict_proba(states)
            v_values = np.sum(q_values * policy_probs, axis=1)
        else:
            # Policy only has predict method
            actions = policy.predict_batch(states)
            v_values = q_values[np.arange(len(states)), actions]
        
        return v_values


class FittedQEvaluation(OPEMethod):
    """
    Fitted Q Evaluation (FQE) for OPE.
    
    Learns Q-function for target policy from offline data.
    """
    
    def __init__(self, discount: float = 0.99, n_epochs: int = 100):
        """
        Initialize FQE.
        
        Args:
            discount: Reward discount factor
            n_epochs: Number of training epochs
        """
        self.discount = discount
        self.n_epochs = n_epochs
        self.q_function = None
        
        logger.info("Fitted Q Evaluation initialized")
    
    def evaluate(self, dataset, policy) -> float:
        """
        Evaluate policy using FQE.
        
        Args:
            dataset: Dataset to evaluate on
            policy: Policy to evaluate
        
        Returns:
            Estimated policy value
        """
        if not TORCH_AVAILABLE:
            logger.error("PyTorch required for FQE")
            return 0.0
        
        # Train Q-function for target policy
        self.q_function = self._train_fqe(dataset, policy)
        
        # Compute average value
        states = dataset.states
        v_values = self._get_v_values(states, policy)
        estimated_value = np.mean(v_values)
        
        logger.info(f"FQE estimated policy value: {estimated_value:.4f}")
        return estimated_value
    
    def _train_fqe(self, dataset, policy):
        """
        Train FQE on dataset.
        
        Args:
            dataset: Dataset to train on
            policy: Target policy
        
        Returns:
            Trained Q-function
        """
        # Simple Q-network
        class QNetwork(nn.Module):
            def __init__(self, state_dim, action_dim):
                super(QNetwork, self).__init__()
                self.fc1 = nn.Linear(state_dim, 256)
                self.fc2 = nn.Linear(256, 256)
                self.fc3 = nn.Linear(256, action_dim)
            
            def forward(self, x):
                x = F.relu(self.fc1(x))
                x = F.relu(self.fc2(x))
                return self.fc3(x)
        
        # Create and train Q-network
        state_dim = dataset.states.shape[1]
        action_dim = len(dataset.action_names)
        
        q_net = QNetwork(state_dim, action_dim)
        optimizer = optim.Adam(q_net.parameters(), lr=3e-4)
        
        # Convert to tensors
        states = torch.FloatTensor(dataset.states)
        actions = torch.LongTensor(dataset.actions)
        rewards = torch.FloatTensor(dataset.rewards)
        next_states = torch.FloatTensor(dataset.next_states)
        dones = torch.FloatTensor(dataset.dones)
        
        # Get policy actions for next states
        next_actions = policy.predict_batch(dataset.next_states)
        next_actions = torch.LongTensor(next_actions)
        
        # Training loop
        batch_size = 256
        
        for epoch in range(self.n_epochs):
            # Sample batch
            indices = np.random.choice(len(states), batch_size)
            
            batch_states = states[indices]
            batch_actions = actions[indices]
            batch_rewards = rewards[indices]
            batch_next_states = next_states[indices]
            batch_next_actions = next_actions[indices]
            batch_dones = dones[indices]
            
            # Compute Q values
            q_values = q_net(batch_states)
            q_values = q_values.gather(1, batch_actions.unsqueeze(1))
            
            # Compute target Q values
            with torch.no_grad():
                next_q_values = q_net(batch_next_states)
                next_q_values = next_q_values.gather(1, batch_next_actions.unsqueeze(1))
                target_q_values = batch_rewards.unsqueeze(1) + (1 - batch_dones.unsqueeze(1)) * self.discount * next_q_values
            
            # Compute loss
            loss = F.mse_loss(q_values, target_q_values)
            
            # Update network
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                logger.debug(f"FQE training: Epoch {epoch+1}/{self.n_epochs}, Loss: {loss.item():.4f}")
        
        logger.info("FQE training complete")
        
        # Create wrapper for Q-function
        class QFunction:
            def __init__(self, q_net):
                self.q_net = q_net
            
            def predict(self, states):
                with torch.no_grad():
                    states_tensor = torch.FloatTensor(states)
                    return self.q_net(states_tensor).numpy()
        
        return QFunction(q_net)
    
    def _get_v_values(self, states, policy) -> np.ndarray:
        """Get V-values for states under policy."""
        q_values = self.q_function.predict(states)
        
        if hasattr(policy, 'predict_proba'):
            # Policy has predict_proba method
            policy_probs = policy.predict_proba(states)
            v_values = np.sum(q_values * policy_probs, axis=1)
        else:
            # Policy only has predict method
            actions = policy.predict_batch(states)
            v_values = q_values[np.arange(len(states)), actions]
        
        return v_values
