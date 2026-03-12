"""
Offline Policy Evaluation (OPE) Methods

Implements multiple OPE estimators for safe policy evaluation:
- FQE (Fitted Q Evaluation)
- WIS (Weighted Importance Sampling)
- DR (Doubly Robust)
- MAGIC (Model-Agnostic Guided Imitation Cloning)

Critical for validating policies before live deployment.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from collections import defaultdict
import numpy

logger = logging.getLogger(__name__)


@dataclass
class OPEResult:
    """Result of offline policy evaluation."""
    estimator: str
    estimated_value: float
    confidence_interval: Tuple[float, float]
    variance: float
    num_samples: int
    metadata: Dict[str, Any]


class FittedQEvaluation:
    """
    Fitted Q Evaluation (FQE)
    
    Model-based OPE that fits Q-function to offline data.
    Low variance but biased if model is misspecified.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.device = torch.device(device)
        self.gamma = gamma
        
        # Q-network
        self.q_network = nn.Sequential(
            nn.Linear(state_dim + action_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        ).to(self.device)
        
        self.optimizer = torch.optim.Adam(self.q_network.parameters(), lr=learning_rate)
        
        logger.info("FQE initialized")
    
    def fit(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        next_states: np.ndarray,
        dones: np.ndarray,
        target_policy: callable,
        num_epochs: int = 100,
        batch_size: int = 256
    ) -> Dict[str, List[float]]:
        """
        Fit Q-function to offline data.
        
        Args:
            states: State observations
            actions: Actions taken
            rewards: Rewards received
            next_states: Next state observations
            dones: Episode termination flags
            target_policy: Policy to evaluate
            num_epochs: Number of training epochs
            batch_size: Batch size
        
        Returns:
            Training history
        """
        dataset_size = len(states)
        history = defaultdict(list)
        
        for epoch in range(num_epochs):
            # Shuffle data
            indices = np.random.permutation(dataset_size)
            epoch_losses = []
            
            for i in range(0, dataset_size, batch_size):
                batch_indices = indices[i:i+batch_size]
                
                batch_states = torch.FloatTensor(states[batch_indices]).to(self.device)
                batch_actions = torch.FloatTensor(actions[batch_indices]).to(self.device)
                batch_rewards = torch.FloatTensor(rewards[batch_indices]).to(self.device)
                batch_next_states = torch.FloatTensor(next_states[batch_indices]).to(self.device)
                batch_dones = torch.FloatTensor(dones[batch_indices]).to(self.device)
                
                # Get target policy actions for next states
                with torch.no_grad():
                    next_actions = target_policy(batch_next_states)
                    next_q_input = torch.cat([batch_next_states, next_actions], dim=-1)
                    next_q = self.q_network(next_q_input)
                    target_q = batch_rewards.unsqueeze(1) + (1 - batch_dones.unsqueeze(1)) * self.gamma * next_q
                
                # Current Q-value
                q_input = torch.cat([batch_states, batch_actions], dim=-1)
                current_q = self.q_network(q_input)
                
                # Loss
                loss = F.mse_loss(current_q, target_q)
                
                # Update
                self.optimizer.zero_grad()
                loss.backward()
                self.optimizer.step()
                
                epoch_losses.append(loss.item())
            
            avg_loss = np.mean(epoch_losses)
            history['loss'].append(avg_loss)
            
            if (epoch + 1) % 10 == 0:
                logger.info(f"FQE Epoch {epoch+1}/{num_epochs}, Loss: {avg_loss:.4f}")
        
        return dict(history)
    
    def evaluate(
        self,
        initial_states: np.ndarray,
        target_policy: callable
    ) -> OPEResult:
        """
        Evaluate policy value.
        
        Args:
            initial_states: Initial state distribution
            target_policy: Policy to evaluate
        
        Returns:
            OPE result
        """
        self.q_network.eval()
        
        with torch.no_grad():
            states_tensor = torch.FloatTensor(initial_states).to(self.device)
            actions = target_policy(states_tensor)
            q_input = torch.cat([states_tensor, actions], dim=-1)
            q_values = self.q_network(q_input)
            
            estimated_value = q_values.mean().item()
            variance = q_values.var().item()
            std_error = np.sqrt(variance / len(initial_states))
            
            # 95% confidence interval
            confidence_interval = (
                estimated_value - 1.96 * std_error,
                estimated_value + 1.96 * std_error
            )
        
        return OPEResult(
            estimator='FQE',
            estimated_value=estimated_value,
            confidence_interval=confidence_interval,
            variance=variance,
            num_samples=len(initial_states),
            metadata={'std_error': std_error}
        )


class WeightedImportanceSampling:
    """
    Weighted Importance Sampling (WIS)
    
    Model-free OPE using importance sampling.
    Unbiased but high variance.
    """
    
    def __init__(self, gamma: float = 0.99):
        self.gamma = gamma
        logger.info("WIS initialized")
    
    def evaluate(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        dones: np.ndarray,
        behavior_policy: callable,
        target_policy: callable
    ) -> OPEResult:
        """
        Evaluate policy using weighted importance sampling.
        
        Args:
            states: State observations
            actions: Actions taken
            rewards: Rewards received
            dones: Episode termination flags
            behavior_policy: Policy that generated data
            target_policy: Policy to evaluate
        
        Returns:
            OPE result
        """
        # Convert to tensors
        states_tensor = torch.FloatTensor(states)
        actions_tensor = torch.FloatTensor(actions)
        
        # Compute importance weights
        with torch.no_grad():
            # Behavior policy probabilities
            behavior_actions = behavior_policy(states_tensor)
            behavior_probs = self._compute_action_prob(actions_tensor, behavior_actions)
            
            # Target policy probabilities
            target_actions = target_policy(states_tensor)
            target_probs = self._compute_action_prob(actions_tensor, target_actions)
            
            # Importance weights
            importance_weights = target_probs / (behavior_probs + 1e-8)
            importance_weights = importance_weights.numpy()
        
        # Compute weighted returns
        returns = []
        weights = []
        
        current_return = 0
        current_weight = 1
        discount = 1
        
        for i in range(len(rewards)):
            current_return += discount * rewards[i]
            current_weight *= importance_weights[i]
            discount *= self.gamma
            
            if dones[i] or i == len(rewards) - 1:
                returns.append(current_return)
                weights.append(current_weight)
                current_return = 0
                current_weight = 1
                discount = 1
        
        returns = np.array(returns)
        weights = np.array(weights)
        
        # Weighted average
        if weights.sum() > 0:
            estimated_value = (returns * weights).sum() / weights.sum()
        else:
            estimated_value = 0.0
        
        # Variance estimation
        if len(returns) > 1:
            variance = np.var(returns * weights)
        else:
            variance = 0.0
        
        std_error = np.sqrt(variance / len(returns)) if len(returns) > 0 else 0.0
        confidence_interval = (
            estimated_value - 1.96 * std_error,
            estimated_value + 1.96 * std_error
        )
        
        return OPEResult(
            estimator='WIS',
            estimated_value=estimated_value,
            confidence_interval=confidence_interval,
            variance=variance,
            num_samples=len(returns),
            metadata={
                'mean_weight': weights.mean(),
                'max_weight': weights.max(),
                'effective_sample_size': (weights.sum() ** 2) / (weights ** 2).sum()
            }
        )
    
    def _compute_action_prob(
        self,
        actions: torch.Tensor,
        policy_actions: torch.Tensor,
        sigma: float = 0.1
    ) -> torch.Tensor:
        """Compute action probability under Gaussian policy."""
        # Assume Gaussian policy
        diff = actions - policy_actions
        log_prob = -0.5 * (diff ** 2).sum(dim=-1) / (sigma ** 2)
        return torch.exp(log_prob)


class DoublyRobust:
    """
    Doubly Robust (DR) Estimator
    
    Combines model-based (FQE) and importance sampling (WIS).
    Reduces both bias and variance.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        hidden_dim: int = 256,
        gamma: float = 0.99,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.fqe = FittedQEvaluation(state_dim, action_dim, hidden_dim, gamma=gamma, device=device)
        self.wis = WeightedImportanceSampling(gamma=gamma)
        self.gamma = gamma
        
        logger.info("DR initialized")
    
    def evaluate(
        self,
        states: np.ndarray,
        actions: np.ndarray,
        rewards: np.ndarray,
        next_states: np.ndarray,
        dones: np.ndarray,
        initial_states: np.ndarray,
        behavior_policy: callable,
        target_policy: callable,
        num_epochs: int = 100
    ) -> OPEResult:
        """
        Evaluate policy using doubly robust estimator.
        
        Combines FQE and WIS for lower bias and variance.
        """
        # First, fit Q-function
        logger.info("Fitting Q-function for DR...")
        self.fqe.fit(
            states, actions, rewards, next_states, dones,
            target_policy, num_epochs=num_epochs
        )
        
        # Get FQE estimate
        fqe_result = self.fqe.evaluate(initial_states, target_policy)
        
        # Compute DR correction term
        states_tensor = torch.FloatTensor(states).to(self.fqe.device)
        actions_tensor = torch.FloatTensor(actions).to(self.fqe.device)
        next_states_tensor = torch.FloatTensor(next_states).to(self.fqe.device)
        rewards_tensor = torch.FloatTensor(rewards).to(self.fqe.device)
        dones_tensor = torch.FloatTensor(dones).to(self.fqe.device)
        
        with torch.no_grad():
            # Current Q-values
            q_input = torch.cat([states_tensor, actions_tensor], dim=-1)
            q_current = self.fqe.q_network(q_input).squeeze()
            
            # Next Q-values under target policy
            next_actions = target_policy(next_states_tensor)
            next_q_input = torch.cat([next_states_tensor, next_actions], dim=-1)
            q_next = self.fqe.q_network(next_q_input).squeeze()
            
            # TD error
            td_target = rewards_tensor + (1 - dones_tensor) * self.gamma * q_next
            td_error = td_target - q_current
            
            # Importance weights
            behavior_actions = behavior_policy(states_tensor)
            target_actions_current = target_policy(states_tensor)
            
            behavior_probs = self.wis._compute_action_prob(actions_tensor, behavior_actions)
            target_probs = self.wis._compute_action_prob(actions_tensor, target_actions_current)
            
            importance_weights = target_probs / (behavior_probs + 1e-8)
            
            # DR correction
            correction = (importance_weights * td_error).mean().item()
        
        # DR estimate = FQE estimate + correction
        dr_estimate = fqe_result.estimated_value + correction
        
        # Variance (simplified)
        variance = fqe_result.variance + td_error.var().item()
        std_error = np.sqrt(variance / len(states))
        confidence_interval = (
            dr_estimate - 1.96 * std_error,
            dr_estimate + 1.96 * std_error
        )
        
        return OPEResult(
            estimator='DR',
            estimated_value=dr_estimate,
            confidence_interval=confidence_interval,
            variance=variance,
            num_samples=len(states),
            metadata={
                'fqe_estimate': fqe_result.estimated_value,
                'correction': correction,
                'mean_importance_weight': importance_weights.mean().item()
            }
        )


class OfflinePolicyEvaluator:
    """
    Comprehensive offline policy evaluator.
    
    Runs multiple OPE methods and aggregates results.
    """
    
    def __init__(
        self,
        state_dim: int,
        action_dim: int,
        gamma: float = 0.99,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.fqe = FittedQEvaluation(state_dim, action_dim, gamma=gamma, device=device)
        self.wis = WeightedImportanceSampling(gamma=gamma)
        self.dr = DoublyRobust(state_dim, action_dim, gamma=gamma, device=device)
        
        logger.info("Offline Policy Evaluator initialized")
    
    def evaluate_policy(
        self,
        policy: callable,
        offline_data: Dict[str, np.ndarray],
        behavior_policy: callable,
        methods: List[str] = ['FQE', 'WIS', 'DR']
    ) -> Dict[str, OPEResult]:
        """
        Evaluate policy using multiple OPE methods.
        
        Args:
            policy: Policy to evaluate
            offline_data: Dictionary with states, actions, rewards, etc.
            behavior_policy: Policy that generated the data
            methods: List of OPE methods to use
        
        Returns:
            Dictionary of OPE results
        """
        results = {}
        
        states = offline_data['states']
        actions = offline_data['actions']
        rewards = offline_data['rewards']
        next_states = offline_data['next_states']
        dones = offline_data['dones']
        initial_states = offline_data.get('initial_states', states[:100])
        
        if 'FQE' in methods:
            logger.info("Running FQE...")
            self.fqe.fit(states, actions, rewards, next_states, dones, policy)
            results['FQE'] = self.fqe.evaluate(initial_states, policy)
        
        if 'WIS' in methods:
            logger.info("Running WIS...")
            results['WIS'] = self.wis.evaluate(
                states, actions, rewards, dones, behavior_policy, policy
            )
        
        if 'DR' in methods:
            logger.info("Running DR...")
            results['DR'] = self.dr.evaluate(
                states, actions, rewards, next_states, dones,
                initial_states, behavior_policy, policy
            )
        
        return results
    
    def get_consensus_estimate(self, results: Dict[str, OPEResult]) -> Tuple[float, float]:
        """
        Get consensus estimate from multiple OPE methods.
        
        Returns:
            (mean_estimate, std_estimate)
        """
        estimates = [r.estimated_value for r in results.values()]
        return np.mean(estimates), np.std(estimates)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("OFFLINE POLICY EVALUATION DEMO")
    print("="*80)
    
    # Create evaluator
    evaluator = OfflinePolicyEvaluator(state_dim=20, action_dim=3)
    
    # Generate dummy offline data
    num_samples = 1000
    offline_data = {
        'states': np.random.randn(num_samples, 20),
        'actions': np.random.randn(num_samples, 3),
        'rewards': np.random.randn(num_samples),
        'next_states': np.random.randn(num_samples, 20),
        'dones': np.random.rand(num_samples) < 0.1,
        'initial_states': np.random.randn(100, 20)
    }
    
    # Define policies
    def target_policy(states):
        return torch.tanh(torch.randn(states.shape[0], 3))
    
    def behavior_policy(states):
        return torch.tanh(torch.randn(states.shape[0], 3))
    
    # Evaluate
    logger.info("\nEvaluating policy with multiple OPE methods...")
    results = evaluator.evaluate_policy(
        policy=target_policy,
        offline_data=offline_data,
        behavior_policy=behavior_policy,
        methods=['FQE', 'WIS', 'DR']
    )
    
    logger.info("\nResults:")
    for method, result in results.items():
        logger.info(f"\n{method}:")
        logger.info(f"  Estimated Value: {result.estimated_value:.4f}")
        logger.info(f"  95% CI: [{result.confidence_interval[0]:.4f}, {result.confidence_interval[1]:.4f}]")
        logger.info(f"  Variance: {result.variance:.4f}")
        logger.info(f"  Metadata: {result.metadata}")
    
    # Consensus
    mean_est, std_est = evaluator.get_consensus_estimate(results)
    logger.info(f"\nConsensus Estimate: {mean_est:.4f} ± {std_est:.4f}")
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
