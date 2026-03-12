"""
Phase 4: World Models - Imagination-Based Planning
Uses world model to simulate and evaluate future trajectories
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from .latent_dynamics import WorldModel

logger = logging.getLogger(__name__)


class ImaginationPlanner:
    """
    Plans trading actions by simulating future trajectories.
    Uses world model to imagine different scenarios.
    """
    
    def __init__(
        self,
        world_model: WorldModel,
        num_simulations: int = 10,
        horizon: int = 50,
        risk_aversion: float = 0.5
    ):
        self.world_model = world_model
        self.num_simulations = num_simulations
        self.horizon = horizon
        self.risk_aversion = risk_aversion
        
        logger.info("✅ Imagination Planner initialized")
        logger.info(f"   Simulations: {num_simulations}")
        logger.info(f"   Horizon: {horizon} steps")
        logger.info(f"   Risk Aversion: {risk_aversion}")
    
    def plan_action(
        self,
        current_state: torch.Tensor,
        possible_actions: List[str]
    ) -> Dict:
        """
        Plan best action by simulating futures.
        
        Args:
            current_state: Current market state
            possible_actions: List of possible actions (e.g., ['BUY', 'SELL', 'HOLD'])
        
        Returns:
            Dictionary with best action and supporting analysis
        """
        # Simulate multiple futures for each action
        action_results = {}
        
        for action in possible_actions:
            # Simulate futures with this action
            futures = self.simulate_futures(current_state, action)
            
            # Analyze futures
            analysis = self.analyze_futures(futures)
            
            action_results[action] = {
                'expected_return': analysis['expected_return'],
                'risk_metrics': analysis['risk_metrics'],
                'confidence': analysis['confidence'],
                'best_trajectory': analysis['best_trajectory'],
                'worst_trajectory': analysis['worst_trajectory']
            }
        
        # Select best action
        best_action = self.select_best_action(action_results)
        
        return {
            'action': best_action,
            'analysis': action_results[best_action],
            'all_results': action_results,
            'num_simulations': self.num_simulations,
            'horizon': self.horizon
        }
    
    def simulate_futures(
        self,
        current_state: torch.Tensor,
        action: str
    ) -> List[Dict]:
        """
        Simulate multiple possible futures.
        
        Args:
            current_state: Current market state
            action: Action to simulate
        
        Returns:
            List of simulated trajectories
        """
        futures = []
        
        for i in range(self.num_simulations):
            # Imagine trajectory
            trajectory = self.world_model.imagine_trajectory(
                current_state,
                self.horizon
            )
            
            # Calculate cumulative reward
            cumulative_reward = trajectory['predicted_rewards'].sum().item()
            
            # Store trajectory info
            futures.append({
                'trajectory': trajectory,
                'cumulative_reward': cumulative_reward,
                'final_state': trajectory['decoded_states'][-1],
                'rewards': trajectory['predicted_rewards'].detach().numpy(),
                'simulation_id': i
            })
        
        return futures
    
    def analyze_futures(self, futures: List[Dict]) -> Dict:
        """
        Analyze collection of simulated futures.
        
        Args:
            futures: List of simulated trajectories
        
        Returns:
            Analysis of futures including risk metrics
        """
        # Extract rewards
        rewards = [f['cumulative_reward'] for f in futures]
        
        # Calculate statistics
        expected_return = np.mean(rewards)
        std_return = np.std(rewards)
        
        # Risk metrics
        var_95 = np.percentile(rewards, 5)  # 95% VaR
        cvar_95 = np.mean([r for r in rewards if r <= var_95])  # 95% CVaR
        
        # Find best and worst trajectories
        best_idx = np.argmax(rewards)
        worst_idx = np.argmin(rewards)
        
        # Calculate confidence based on consistency
        reward_range = max(rewards) - min(rewards)
        consistency = 1.0 - (reward_range / abs(expected_return)) if expected_return != 0 else 0
        confidence = max(0.0, min(1.0, consistency))
        
        return {
            'expected_return': expected_return,
            'risk_metrics': {
                'std_return': std_return,
                'var_95': var_95,
                'cvar_95': cvar_95,
                'max_return': max(rewards),
                'min_return': min(rewards)
            },
            'confidence': confidence,
            'best_trajectory': futures[best_idx],
            'worst_trajectory': futures[worst_idx]
        }
    
    def select_best_action(self, action_results: Dict) -> str:
        """
        Select best action considering returns and risk.
        
        Args:
            action_results: Results for each action
        
        Returns:
            Best action
        """
        action_scores = {}
        
        for action, results in action_results.items():
            # Risk-adjusted return
            expected_return = results['expected_return']
            cvar = results['risk_metrics']['cvar_95']
            
            # Score combines return and risk based on risk aversion
            score = (
                (1 - self.risk_aversion) * expected_return +
                self.risk_aversion * cvar
            )
            
            action_scores[action] = score
        
        # Select action with highest score
        return max(action_scores.items(), key=lambda x: x[1])[0]
    
    def explain_decision(self, plan_result: Dict) -> str:
        """
        Generate human-readable explanation of planning process.
        
        Args:
            plan_result: Output from plan_action
        
        Returns:
            Detailed explanation
        """
        action = plan_result['action']
        analysis = plan_result['analysis']
        all_results = plan_result['all_results']
        
        explanation = [
            f"Selected Action: {action}\n",
            f"Based on {self.num_simulations} simulated futures over {self.horizon} steps:\n",
            "\nExpected Outcomes:",
            f"- Expected Return: ${analysis['expected_return']:.2f}",
            f"- Confidence: {analysis['confidence']:.1%}",
            "\nRisk Analysis:",
            f"- 95% VaR: ${analysis['risk_metrics']['var_95']:.2f}",
            f"- 95% CVaR: ${analysis['risk_metrics']['cvar_95']:.2f}",
            f"- Return Range: ${analysis['risk_metrics']['min_return']:.2f} to "
            f"${analysis['risk_metrics']['max_return']:.2f}",
            "\nComparison with Alternatives:"
        ]
        
        # Add comparison with other actions
        for other_action, other_results in all_results.items():
            if other_action != action:
                explanation.append(
                    f"\n{other_action}:",
                    f"- Expected Return: ${other_results['expected_return']:.2f}",
                    f"- Confidence: {other_results['confidence']:.1%}",
                    f"- 95% CVaR: ${other_results['risk_metrics']['cvar_95']:.2f}"
                )
        
        return "\n".join(explanation)
    
    def set_risk_aversion(self, risk_aversion: float):
        """Adjust risk aversion parameter."""
        self.risk_aversion = max(0.0, min(1.0, risk_aversion))
        logger.info(f"🎯 Risk aversion set to {self.risk_aversion:.2f}")
    
    def set_simulation_params(
        self,
        num_simulations: Optional[int] = None,
        horizon: Optional[int] = None
    ):
        """Adjust simulation parameters."""
        if num_simulations is not None:
            self.num_simulations = max(1, num_simulations)
        
        if horizon is not None:
            self.horizon = max(1, horizon)
        
        logger.info(f"⚙️ Simulation parameters updated:")
        logger.info(f"   Simulations: {self.num_simulations}")
        logger.info(f"   Horizon: {self.horizon}")
