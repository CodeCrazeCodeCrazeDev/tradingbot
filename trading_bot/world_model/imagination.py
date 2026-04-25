"""
Phase 4: World Models - Imagination-Based Planning
Uses world model to simulate and evaluate future trajectories

L7: Hierarchical Planner
  - High-level goal planning
  - Option/skill selection via Cross-Entropy Method (CEM) over latent options
  - Latent-space MPC
  - Test-time action optimization
  - Fallback: Sampling-Based Model Predictive Path Integral (MPPI) controller
    operating on low-level action space for next 2 seconds when L10 rejects plan

L8: Actor-Controller
  - Distilled fast policy for real-time control (planning every timestep is too expensive)
  - Energy-Based Model (EBM) / Implicit Behavioral Cloning (IBC) for multimodal action
    distributions (handles "push left or push right" both valid)
  - Linear Quadratic Regulator (LQR) tracked to latent trajectory planned by L7
  - Diffusion policy for sampling from multimodal action distributions
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
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


# =============================================================================
# L7: Hierarchical Planner — CEM over Latent Options + MPPI Fallback
# =============================================================================

@dataclass
class PlanResult:
    """Result from hierarchical planner."""
    selected_option: str
    option_sequence: List[str]
    expected_value: float
    risk_score: float
    constraint_violations: List[str]
    confidence: float
    fallback_active: bool = False
    mppi_actions: Optional[np.ndarray] = None


class CEMPlanner:
    """
    L7: Cross-Entropy Method (CEM) over Latent Options.

    Searches over the Option Space defined by L4's skill library.
    For each option sequence, performs truncated rollouts in the L5 Simulator.
    If the Verifier (L10) rejects a plan due to safety invariant, falls back
    to MPPI controller operating on low-level action space for next 2 seconds.
    """

    def __init__(
        self,
        world_model: WorldModel,
        n_options: int = 50,
        cem_iterations: int = 5,
        cem_samples: int = 100,
        cem_elite_frac: float = 0.1,
        planning_horizon: int = 10,
        mppi_samples: int = 500,
        mppi_horizon: int = 20,
        mppi_lambda: float = 1.0,
        safety_verifier: Optional[Callable] = None
    ):
        self.world_model = world_model
        self.n_options = n_options
        self.cem_iterations = cem_iterations
        self.cem_samples = cem_samples
        self.cem_elite_frac = cem_elite_frac
        self.planning_horizon = planning_horizon
        self.mppi_samples = mppi_samples
        self.mppi_horizon = mppi_horizon
        self.mppi_lambda = mppi_lambda
        self.safety_verifier = safety_verifier

        # Option embeddings (learned)
        self.option_embeddings = nn.Parameter(
            torch.randn(n_options, 32) * 0.1
        )

        logger.info(f"✅ CEM Planner (L7) initialized")
        logger.info(f"   Options: {n_options}")
        logger.info(f"   CEM iterations: {cem_iterations}")
        logger.info(f"   Planning horizon: {planning_horizon}")

    def plan(
        self,
        current_latent: torch.Tensor,
        goal_latent: Optional[torch.Tensor] = None,
        skill_library: Optional[Dict] = None
    ) -> PlanResult:
        """
        Plan option sequence using CEM over latent option space.

        1. Sample option sequences from prior
        2. Roll out each sequence in world model
        3. Evaluate with value model (L6)
        4. Select elite fraction
        5. Refit prior to elites
        6. Repeat for cem_iterations
        7. If L10 rejects, fallback to MPPI
        """
        device = current_latent.device
        n_elite = max(1, int(self.cem_samples * self.cem_elite_frac))

        # Initialize CEM distribution over option sequences
        # Mean and log_std for each timestep in planning horizon
        mean = torch.zeros(self.planning_horizon, self.n_options, device=device)
        log_std = torch.zeros(self.planning_horizon, self.n_options, device=device)

        best_sequence = None
        best_value = float('-inf')

        for iteration in range(self.cem_iterations):
            # Sample option sequences
            samples = mean.unsqueeze(0) + torch.exp(log_std).unsqueeze(0) * \
                torch.randn(self.cem_samples, self.planning_horizon, self.n_options, device=device)

            # Evaluate each sample by rolling out in world model
            values = []
            for s in range(self.cem_samples):
                value = self._evaluate_option_sequence(
                    current_latent, samples[s], goal_latent
                )
                values.append(value)

            values = torch.tensor(values, device=device)

            # Select elite samples
            elite_indices = torch.topk(values, n_elite).indices
            elite_samples = samples[elite_indices]

            # Refit distribution to elites
            mean = elite_samples.mean(dim=0)
            log_std = torch.log(elite_samples.std(dim=0) + 1e-6)

            # Track best
            if values[elite_indices[0]] > best_value:
                best_value = values[elite_indices[0]].item()
                best_sequence = elite_samples[0]

        # Extract selected option sequence
        option_ids = []
        if best_sequence is not None:
            for t in range(self.planning_horizon):
                selected_option = best_sequence[t].argmax().item()
                option_ids.append(f"skill_{selected_option}")

        selected_option = option_ids[0] if option_ids else "skill_0"

        # Safety verification (L10 integration)
        constraint_violations = []
        fallback_active = False
        mppi_actions = None

        if self.safety_verifier is not None:
            is_safe = self.safety_verifier(current_latent, selected_option)
            if not is_safe:
                constraint_violations.append("safety_invariant_violation")
                fallback_active = True
                # Fallback to MPPI for next 2 seconds
                mppi_actions = self._mppi_fallback(current_latent)

        return PlanResult(
            selected_option=selected_option,
            option_sequence=option_ids,
            expected_value=best_value,
            risk_score=0.0,
            constraint_violations=constraint_violations,
            confidence=min(1.0, max(0.0, best_value)),
            fallback_active=fallback_active,
            mppi_actions=mppi_actions
        )

    def _evaluate_option_sequence(
        self,
        initial_latent: torch.Tensor,
        option_probs: torch.Tensor,
        goal_latent: Optional[torch.Tensor] = None
    ) -> float:
        """Evaluate an option sequence by rolling out in world model."""
        current = initial_latent
        total_value = 0.0
        discount = 1.0

        for t in range(self.planning_horizon):
            # Get option embedding
            option_idx = option_probs[t].argmax()
            option_emb = self.option_embeddings[option_idx]

            # Predict next state
            with torch.no_grad():
                next_latent, reward, _, info = self.world_model.predict_next(
                    current,
                    option_latent=option_emb,
                    contact_event=False
                )

            total_value += discount * reward.item()
            discount *= 0.99

            # Goal bonus
            if goal_latent is not None:
                goal_dist = F.mse_loss(next_latent, goal_latent).item()
                total_value -= goal_dist * 0.1

            current = next_latent

        return total_value

    def _mppi_fallback(self, current_latent: torch.Tensor) -> np.ndarray:
        """
        MPPI fallback controller for low-level action space.
        Operates for next 2 seconds when L10 rejects option-level plan.
        """
        action_dim = 5
        actions = np.zeros((self.mppi_horizon, action_dim))

        # Sample noise trajectories
        noise = np.random.randn(self.mppi_samples, self.mppi_horizon, action_dim) * 0.1

        # Evaluate trajectories (simplified)
        weights = np.exp(-np.sum(noise ** 2, axis=(1, 2)) / self.mppi_lambda)
        weights /= weights.sum()

        # Weighted average
        for t in range(self.mppi_horizon):
            actions[t] = np.average(noise[:, t, :], axis=0, weights=weights)

        return actions


# =============================================================================
# L8: Actor-Controller — EBM/IBC + LQR + Diffusion Policy
# =============================================================================

class EnergyBasedPolicy(nn.Module):
    """
    L8: Energy-Based Model (EBM) / Implicit Behavioral Cloning (IBC).

    For fine manipulation where multiple actions are equally valid.
    Instead of regressing to the mean of a multimodal distribution,
    learn an energy function and sample via gradient descent.
    """

    def __init__(self, latent_dim: int = 64, action_dim: int = 5, hidden_dim: int = 128):
        super().__init__()
        self.energy_net = nn.Sequential(
            nn.Linear(latent_dim + action_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1)
        )
        self.action_dim = action_dim
        self.latent_dim = latent_dim

    def energy(self, latent: torch.Tensor, action: torch.Tensor) -> torch.Tensor:
        """Compute energy of (state, action) pair. Lower = better."""
        return self.energy_net(torch.cat([latent, action], dim=-1))

    def sample_action(
        self,
        latent: torch.Tensor,
        n_samples: int = 64,
        n_steps: int = 5,
        step_size: float = 0.1
    ) -> torch.Tensor:
        """
        Sample action via gradient-based Langevin dynamics on energy landscape.
        Handles multimodal distributions (e.g., "push left or push right" both valid).
        """
        batch_size = latent.size(0)
        device = latent.device

        # Initialize random actions
        actions = torch.randn(batch_size, n_samples, self.action_dim, device=device)

        # Expand latent for broadcasting
        latent_expanded = latent.unsqueeze(1).expand(-1, n_samples, -1)

        # Langevin dynamics
        actions_sampled = actions.clone().detach().requires_grad_(True)
        for _ in range(n_steps):
            energy = self.energy(
                latent_expanded.reshape(-1, self.latent_dim),
                actions_sampled.reshape(-1, self.action_dim)
            ).reshape(batch_size, n_samples)

            # Gradient of energy w.r.t. actions
            grad = torch.autograd.grad(
                energy.sum(), actions_sampled, create_graph=False
            )[0]

            # Langevin update: move toward lower energy + noise
            actions_sampled = actions_sampled - step_size * grad + \
                torch.randn_like(actions_sampled) * step_size * 0.1
            actions_sampled = actions_sampled.detach().requires_grad_(True)

        # Select lowest-energy sample
        final_energy = self.energy(
            latent_expanded.reshape(-1, self.latent_dim),
            actions_sampled.reshape(-1, self.action_dim)
        ).reshape(batch_size, n_samples)

        best_idx = final_energy.argmin(dim=1)
        best_actions = actions_sampled[torch.arange(batch_size), best_idx]

        return best_actions


class LQRTracker:
    """
    L8: Linear Quadratic Regulator for tracking latent trajectory planned by L7.
    Fast path for real-time control when the trajectory is already planned.
    """

    def __init__(
        self,
        state_dim: int = 64,
        action_dim: int = 5,
        Q_weight: float = 1.0,
        R_weight: float = 0.01
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.Q = np.eye(state_dim) * Q_weight
        self.R = np.eye(action_dim) * R_weight

    def compute_gain(
        self,
        A: np.ndarray,
        B: np.ndarray
    ) -> np.ndarray:
        """
        Compute LQR gain matrix K such that u = -K(x - x_ref).
        Uses iterative discrete-time Riccati equation.
        """
        P = self.Q.copy()
        for _ in range(100):
            K = -np.linalg.inv(self.R + B.T @ P @ B) @ B.T @ P @ A
            P_new = self.Q + A.T @ P @ A - A.T @ P @ B @ \
                np.linalg.inv(self.R + B.T @ P @ B) @ B.T @ P @ A
            if np.allclose(P, P_new, atol=1e-6):
                break
            P = P_new
        return K

    def track(
        self,
        current_state: np.ndarray,
        reference_state: np.ndarray,
        A: np.ndarray,
        B: np.ndarray
    ) -> np.ndarray:
        """Compute control action to track reference trajectory."""
        K = self.compute_gain(A, B)
        error = current_state - reference_state
        action = -K @ error
        return action[:self.action_dim]


class DiffusionPolicyHead(nn.Module):
    """
    L8: Diffusion policy for multimodal action distributions.
    When multiple actions are equally valid, sample from a learned
    multimodal distribution rather than averaging.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        action_dim: int = 5,
        hidden_dim: int = 128,
        n_diffusion_steps: int = 10,
        beta_schedule: str = "linear"
    ):
        super().__init__()
        self.action_dim = action_dim
        self.n_diffusion_steps = n_diffusion_steps

        # Noise prediction network
        self.denoiser = nn.Sequential(
            nn.Linear(latent_dim + action_dim + 1, hidden_dim),  # +1 for timestep
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )

        # Beta schedule
        if beta_schedule == "linear":
            betas = torch.linspace(0.0001, 0.02, n_diffusion_steps)
        else:
            betas = torch.ones(n_diffusion_steps) * 0.01
        self.register_buffer('betas', betas)
        self.register_buffer('alphas', 1.0 - betas)
        self.register_buffer('alpha_cumprod', torch.cumprod(1.0 - betas, dim=0))

    def forward(
        self,
        latent: torch.Tensor,
        noisy_action: torch.Tensor,
        timestep: int
    ) -> torch.Tensor:
        """Predict noise given noisy action, latent state, and timestep."""
        t_emb = torch.full((latent.size(0), 1), timestep / self.n_diffusion_steps, device=latent.device)
        return self.denoiser(torch.cat([latent, noisy_action, t_emb], dim=-1))

    @torch.no_grad()
    def sample(
        self,
        latent: torch.Tensor,
        n_steps: Optional[int] = None
    ) -> torch.Tensor:
        """Sample action via iterative denoising (DDPM-style)."""
        steps = n_steps or self.n_diffusion_steps
        batch_size = latent.size(0)
        device = latent.device

        # Start from pure noise
        action = torch.randn(batch_size, self.action_dim, device=device)

        for t in reversed(range(steps)):
            # Predict noise
            noise_pred = self.forward(latent, action, t)

            # Denoise step
            alpha_t = self.alphas[t]
            alpha_cumprod_t = self.alpha_cumprod[t]

            if t > 0:
                noise = torch.randn_like(action)
            else:
                noise = torch.zeros_like(action)

            action = (1.0 / torch.sqrt(alpha_t)) * (
                action - (1.0 - alpha_t) / torch.sqrt(1.0 - alpha_cumprod_t) * noise_pred
            ) + torch.sqrt(1.0 - alpha_t) * noise

        return action


class ActorController:
    """
    L8: Actor-Controller — distilled fast policy for real-time control.

    Three paths:
    1. EBM/IBC for ambiguous contact/multimodal action distributions
    2. LQR for tracking planned latent trajectories (fast path)
    3. Diffusion policy for sampling from multimodal action distributions

    Planning every timestep is too expensive; this provides the fast reactive layer.
    """

    def __init__(
        self,
        latent_dim: int = 64,
        action_dim: int = 5,
        hidden_dim: int = 128,
        mode: str = "ebm"  # 'ebm', 'lqr', 'diffusion'
    ):
        self.mode = mode
        self.action_dim = action_dim

        # EBM/IBC policy
        self.ebm_policy = EnergyBasedPolicy(latent_dim, action_dim, hidden_dim)

        # LQR tracker
        self.lqr_tracker = LQRTracker(latent_dim, action_dim)

        # Diffusion policy
        self.diffusion_policy = DiffusionPolicyHead(latent_dim, action_dim, hidden_dim)

        # Mode selection network (learned)
        self.mode_selector = nn.Sequential(
            nn.Linear(latent_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 3),  # 3 modes
            nn.Softmax(dim=-1)
        )

        logger.info(f"✅ Actor-Controller (L8) initialized, default mode: {mode}")

    def select_action(
        self,
        latent_state: torch.Tensor,
        reference_trajectory: Optional[np.ndarray] = None,
        dynamics_matrices: Optional[Tuple[np.ndarray, np.ndarray]] = None,
        override_mode: Optional[str] = None
    ) -> Tuple[torch.Tensor, Dict]:
        """
        Select action using appropriate controller mode.

        Returns:
            action: Selected action
            info: Dict with mode used and auxiliary info
        """
        mode = override_mode or self.mode

        if mode == "ebm":
            action = self.ebm_policy.sample_action(latent_state.unsqueeze(0) if latent_state.dim() == 1 else latent_state)
            if action.dim() > 1:
                action = action.squeeze(0)
            info = {'mode': 'ebm', 'energy': 0.0}

        elif mode == "lqr" and reference_trajectory is not None and dynamics_matrices is not None:
            current = latent_state.detach().cpu().numpy()
            ref = reference_trajectory[0] if len(reference_trajectory) > 0 else current
            A, B = dynamics_matrices
            action_np = self.lqr_tracker.track(current, ref, A, B)
            action = torch.FloatTensor(action_np)
            info = {'mode': 'lqr'}

        elif mode == "diffusion":
            action = self.diffusion_policy.sample(
                latent_state.unsqueeze(0) if latent_state.dim() == 1 else latent_state
            )
            if action.dim() > 1:
                action = action.squeeze(0)
            info = {'mode': 'diffusion'}

        else:
            # Fallback: EBM
            action = self.ebm_policy.sample_action(latent_state.unsqueeze(0) if latent_state.dim() == 1 else latent_state)
            if action.dim() > 1:
                action = action.squeeze(0)
            info = {'mode': 'ebm_fallback'}

        return action, info

    def auto_select_mode(
        self,
        latent_state: torch.Tensor
    ) -> str:
        """Automatically select controller mode based on latent state."""
        with torch.no_grad():
            probs = self.mode_selector(
                latent_state.unsqueeze(0) if latent_state.dim() == 1 else latent_state
            )
            mode_idx = probs.argmax(dim=-1).item()

        modes = ['ebm', 'lqr', 'diffusion']
        return modes[mode_idx]


# =============================================================================
# L8 Ceiling-Pushed: Contact Modes, Compliance Control, Residual Refinement
# =============================================================================

class ContactMode(str, Enum):
    FREE = "free"
    CONTACT = "contact"
    SLIP = "slip"
    IMPACT = "impact"
    HALT = "halt"


@dataclass(frozen=True)
class ContactModeDecision:
    mode: ContactMode
    confidence: float
    reason: str


class ContactModeSwitcher:
    """Selects the actor-controller contact mode from surprise/liquidity signals."""

    def __init__(
        self,
        *,
        impact_threshold: float = 0.85,
        slip_threshold: float = 0.55,
        halt_threshold: float = 0.95,
    ) -> None:
        self.impact_threshold = impact_threshold
        self.slip_threshold = slip_threshold
        self.halt_threshold = halt_threshold
        self.history: List[ContactModeDecision] = []

    def select_mode(self, signals: Dict[str, float]) -> ContactModeDecision:
        surprise = float(signals.get("surprise", 0.0))
        liquidity_gap = float(signals.get("liquidity_gap", 0.0))
        slippage = float(signals.get("slippage", 0.0))
        halt_probability = float(signals.get("halt_probability", 0.0))
        stress = max(surprise, liquidity_gap, slippage)

        if halt_probability >= self.halt_threshold:
            decision = ContactModeDecision(ContactMode.HALT, halt_probability, "halt probability above threshold")
        elif stress >= self.impact_threshold:
            decision = ContactModeDecision(ContactMode.IMPACT, stress, "impact/contact stress above threshold")
        elif slippage >= self.slip_threshold or liquidity_gap >= self.slip_threshold:
            decision = ContactModeDecision(ContactMode.SLIP, max(slippage, liquidity_gap), "slip regime detected")
        elif surprise >= self.slip_threshold:
            decision = ContactModeDecision(ContactMode.CONTACT, surprise, "surprise implies contact-mode transition")
        else:
            decision = ContactModeDecision(ContactMode.FREE, 1.0 - stress, "free mode")

        self.history.append(decision)
        return decision


@dataclass(frozen=True)
class ComplianceAction:
    approved: bool
    adjusted_action: Dict[str, Any]
    violations: List[str]
    mode: ContactMode
    risk_multiplier: float


class ComplianceController:
    """Constrains actor-controller output by contact mode and hard risk limits."""

    def __init__(
        self,
        *,
        max_notional: float = 100_000.0,
        max_leverage: float = 2.0,
        mode_risk_multipliers: Optional[Dict[ContactMode, float]] = None,
    ) -> None:
        self.max_notional = max_notional
        self.max_leverage = max_leverage
        self.mode_risk_multipliers = mode_risk_multipliers or {
            ContactMode.FREE: 1.0,
            ContactMode.CONTACT: 0.7,
            ContactMode.SLIP: 0.5,
            ContactMode.IMPACT: 0.25,
            ContactMode.HALT: 0.0,
        }

    def constrain(self, action: Dict[str, Any], mode: ContactMode) -> ComplianceAction:
        adjusted = dict(action)
        violations: List[str] = []
        multiplier = self.mode_risk_multipliers.get(mode, 0.0)

        notional = float(adjusted.get("notional", 0.0))
        leverage = float(adjusted.get("leverage", 1.0))
        if notional > self.max_notional:
            violations.append("notional_clipped")
            adjusted["notional"] = self.max_notional
        if leverage > self.max_leverage:
            violations.append("leverage_clipped")
            adjusted["leverage"] = self.max_leverage

        adjusted["notional"] = float(adjusted.get("notional", 0.0)) * multiplier
        if multiplier == 0.0:
            adjusted["decision"] = "HOLD"
            violations.append("mode_forced_hold")

        return ComplianceAction(
            approved=multiplier > 0.0,
            adjusted_action=adjusted,
            violations=violations,
            mode=mode,
            risk_multiplier=multiplier,
        )


class ResidualDiffusionRefiner:
    """Bounded residual refinement over a compliant base action."""

    def __init__(self, *, residual_scale: float = 0.05, seed: int = 7) -> None:
        self.residual_scale = residual_scale
        self.rng = np.random.default_rng(seed)

    def refine(self, action: Dict[str, Any], *, risk_multiplier: float) -> Dict[str, Any]:
        refined = dict(action)
        if "notional" in refined and risk_multiplier > 0:
            residual = self.rng.normal(0.0, self.residual_scale) * risk_multiplier
            refined["notional"] = max(0.0, float(refined["notional"]) * (1.0 + residual))
            refined["residual_refinement"] = residual
        return refined


# =============================================================================
# Cross-Cutting Ceiling-Pushed Loops
# =============================================================================

class DreamAndVerifyLoop:
    """L5+L10 loop: dream counterfactuals, then verify them with a shield."""

    def __init__(self, simulator: Callable[[Dict[str, Any]], Iterable[Dict[str, float]]], shield: Any) -> None:
        self.simulator = simulator
        self.shield = shield

    def run(self, seed_context: Dict[str, Any]) -> Dict[str, Any]:
        dreams = list(self.simulator(seed_context))
        decisions = [self.shield.evaluate(dream) for dream in dreams]
        accepted = [dream for dream, decision in zip(dreams, decisions) if decision.approved]
        return {
            "dreams": len(dreams),
            "accepted": len(accepted),
            "blocked": len(dreams) - len(accepted),
            "degradation_levels": [decision.degradation_level.value for decision in decisions],
        }


class CausalAgentLoop:
    """B2+B3+L7 loop: probe causal context, repair options, and re-plan."""

    def __init__(self, planner: Callable[[Dict[str, Any]], Any], repairer: Callable[[Any, Dict[str, Any]], Any]) -> None:
        self.planner = planner
        self.repairer = repairer

    def run(self, causal_context: Dict[str, Any]) -> Dict[str, Any]:
        plan = self.planner(causal_context)
        repaired = self.repairer(plan, causal_context)
        return {"plan": plan, "repaired_plan": repaired, "changed": plan != repaired}


class AdversarialSelfPlay:
    """L3+L5+L7 loop: adversarially stress the world model and planner."""

    def __init__(self, planner: Callable[[Dict[str, Any]], Any], adversary: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self.planner = planner
        self.adversary = adversary
        self.history: List[Dict[str, Any]] = []

    def run_round(self, context: Dict[str, Any]) -> Dict[str, Any]:
        attacked = self.adversary(context)
        plan = self.planner(attacked)
        score = float(attacked.get("stress", 0.0)) - float(attacked.get("resilience", 0.0))
        result = {"attacked_context": attacked, "plan": plan, "adversarial_score": score}
        self.history.append(result)
        return result


# =============================================================================
# L7 Ceiling-Pushed: Risk-Aware CVaR Planning, Plan Repair, Temporal Boundaries
# =============================================================================

@dataclass
class RiskAwarePlanResult:
    """Extended plan result with risk metrics."""
    selected_option: str
    option_sequence: List[str]
    expected_value: float
    cvar: float  # Conditional Value at Risk (worst-case percentile value)
    risk_score: float
    constraint_violations: List[str]
    confidence: float
    fallback_active: bool = False
    mppi_actions: Optional[np.ndarray] = None
    # Ceiling-pushed additions
    value_distribution: Optional[np.ndarray] = None  # Full distribution of rollout values
    tail_risk_percentile: float = 0.0  # Value at the alpha-quantile
    plan_repair_count: int = 0
    boundary_violations: List[str] = field(default_factory=list)


class RiskAwareCVaRPlanner:
    """
    L7 Ceiling-Pushed: Risk-Aware CVaR CEM Planner.

    Standard CEM optimizes expected value. But in trading, tail risk matters
    more than average return. A plan with high expected value but catastrophic
    worst-case is dangerous.

    CVaR (Conditional Value at Risk) optimizes the expected value of the
    worst alpha-fraction of outcomes. This is materially different from:
    - Expected value optimization (ignores tails)
    - Worst-case optimization (too conservative, optimizes single point)
    - Risk-penalized expected value (ad hoc weighting)

    CVaR naturally balances exploration and safety:
    - Alpha=1.0: standard expected value (no risk awareness)
    - Alpha=0.1: optimize the worst 10% of outcomes (very risk-averse)
    - Alpha=0.5: optimize the worst half (moderate risk aversion)

    Implementation: during CEM, instead of selecting elites by top-k expected
    value, select by top-k CVaR. This shifts the search distribution toward
    plans that are robust, not just high-return on average.
    """

    def __init__(
        self,
        world_model=None,
        n_options: int = 50,
        cem_iterations: int = 5,
        cem_samples: int = 200,
        cem_elite_frac: float = 0.1,
        planning_horizon: int = 10,
        alpha: float = 0.2,  # CVaR alpha: optimize worst alpha-fraction
        n_rollout_samples: int = 20,  # Rollout samples per option sequence
        safety_verifier: Optional[Callable] = None
    ):
        self.world_model = world_model
        self.n_options = n_options
        self.cem_iterations = cem_iterations
        self.cem_samples = cem_samples
        self.cem_elite_frac = cem_elite_frac
        self.planning_horizon = planning_horizon
        self.alpha = alpha
        self.n_rollout_samples = n_rollout_samples
        self.safety_verifier = safety_verifier

        # Option embeddings
        self.option_embeddings = nn.Parameter(
            torch.randn(n_options, 32) * 0.1
        )

        logger.info(f"✅ Risk-Aware CVaR Planner (L7 ceiling) initialized")
        logger.info(f"   Alpha (CVaR): {alpha}")
        logger.info(f"   Rollout samples per sequence: {n_rollout_samples}")

    def plan(
        self,
        current_latent: torch.Tensor,
        goal_latent: Optional[torch.Tensor] = None
    ) -> RiskAwarePlanResult:
        """
        Plan using CVaR-optimized CEM.

        For each candidate option sequence, perform n_rollout_samples rollouts
        with different stochastic transitions. Then compute CVaR across those
        rollouts. Select elites by CVaR, not expected value.
        """
        device = current_latent.device
        n_elite = max(1, int(self.cem_samples * self.cem_elite_frac))

        # Initialize CEM distribution
        mean = torch.zeros(self.planning_horizon, self.n_options, device=device)
        log_std = torch.zeros(self.planning_horizon, self.n_options, device=device)

        best_sequence = None
        best_cvar = float('-inf')
        best_expected = 0.0
        best_value_dist = None

        for iteration in range(self.cem_iterations):
            # Sample option sequences
            samples = mean.unsqueeze(0) + torch.exp(log_std).unsqueeze(0) * \
                torch.randn(self.cem_samples, self.planning_horizon, self.n_options, device=device)

            # Evaluate each sample with multiple rollouts for CVaR
            cvar_values = []
            expected_values = []
            value_distributions = []

            for s in range(self.cem_samples):
                rollout_values = []
                for r in range(self.n_rollout_samples):
                    value = self._evaluate_option_sequence(
                        current_latent, samples[s], goal_latent
                    )
                    rollout_values.append(value)

                rollout_arr = np.array(rollout_values)
                cvar = self._compute_cvar(rollout_arr)
                expected = float(np.mean(rollout_arr))

                cvar_values.append(cvar)
                expected_values.append(expected)
                value_distributions.append(rollout_arr)

            cvar_tensor = torch.tensor(cvar_values, device=device)

            # Select elites by CVaR (not expected value!)
            elite_indices = torch.topk(cvar_tensor, n_elite).indices
            elite_samples = samples[elite_indices]

            # Refit distribution to elites
            mean = elite_samples.mean(dim=0)
            log_std = torch.log(elite_samples.std(dim=0) + 1e-6)

            # Track best
            if cvar_tensor[elite_indices[0]] > best_cvar:
                best_cvar = cvar_tensor[elite_indices[0]].item()
                best_expected = expected_values[elite_indices[0].item()]
                best_sequence = elite_samples[0]
                best_value_dist = value_distributions[elite_indices[0].item()]

        # Extract option sequence
        option_ids = []
        if best_sequence is not None:
            for t in range(self.planning_horizon):
                selected_option = best_sequence[t].argmax().item()
                option_ids.append(f"skill_{selected_option}")

        selected_option = option_ids[0] if option_ids else "skill_0"

        # Safety verification
        constraint_violations = []
        fallback_active = False
        mppi_actions = None

        if self.safety_verifier is not None:
            is_safe = self.safety_verifier(current_latent, selected_option)
            if not is_safe:
                constraint_violations.append("safety_invariant_violation")
                fallback_active = True

        # Compute tail risk percentile
        tail_percentile = 0.0
        if best_value_dist is not None and len(best_value_dist) > 0:
            tail_percentile = float(np.percentile(best_value_dist, self.alpha * 100))

        return RiskAwarePlanResult(
            selected_option=selected_option,
            option_sequence=option_ids,
            expected_value=best_expected,
            cvar=best_cvar,
            risk_score=1.0 - (best_cvar / max(abs(best_expected), 1e-8)),
            constraint_violations=constraint_violations,
            confidence=min(1.0, max(0.0, best_cvar)),
            fallback_active=fallback_active,
            mppi_actions=mppi_actions,
            value_distribution=best_value_dist,
            tail_risk_percentile=tail_percentile
        )

    def _compute_cvar(self, values: np.ndarray) -> float:
        """
        Compute Conditional Value at Risk at level alpha.

        CVaR_alpha = E[X | X <= VaR_alpha]
        where VaR_alpha is the alpha-quantile of the distribution.
        """
        if len(values) == 0:
            return 0.0

        sorted_values = np.sort(values)
        n_tail = max(1, int(len(sorted_values) * self.alpha))
        tail_values = sorted_values[:n_tail]
        return float(np.mean(tail_values))

    def _evaluate_option_sequence(
        self,
        initial_latent: torch.Tensor,
        option_probs: torch.Tensor,
        goal_latent: Optional[torch.Tensor] = None
    ) -> float:
        """Evaluate an option sequence by rolling out in world model."""
        if self.world_model is None:
            return np.random.randn()

        current = initial_latent
        total_value = 0.0
        discount = 1.0

        for t in range(self.planning_horizon):
            option_idx = option_probs[t].argmax()
            option_emb = self.option_embeddings[option_idx]

            with torch.no_grad():
                next_latent, reward, _, info = self.world_model.predict_next(
                    current,
                    option_latent=option_emb,
                    contact_event=False
                )

            total_value += discount * reward.item()
            discount *= 0.99

            if goal_latent is not None:
                goal_dist = F.mse_loss(next_latent, goal_latent).item()
                total_value -= goal_dist * 0.1

            current = next_latent

        return total_value


class PlanRepairEngine:
    """
    L7 Ceiling-Pushed: Plan Repair on Surprise Spikes.

    Current L7 plans once and executes blindly. If the world diverges from
    the plan mid-execution, the agent continues the now-invalid plan until
    the next planning cycle. This is dangerous in fast-moving markets.

    Plan repair monitors L3 ensemble surprise during plan execution. When
    surprise exceeds a threshold (the world has diverged from the plan's
    assumptions), the engine:

    1. Identifies which step in the plan is now invalid
    2. Truncates the remaining plan at that step
    3. Re-plans from the current (surprising) state
    4. Merges the new plan suffix with the still-valid prefix

    This is NOT full re-planning — it's surgical repair. The still-valid
    prefix of the plan is preserved, saving computation and maintaining
    consistency with already-committed actions.
    """

    def __init__(
        self,
        surprise_threshold: float = 2.0,
        max_repairs_per_episode: int = 3,
        repair_cooldown: int = 5,
        planner: Optional[RiskAwareCVaRPlanner] = None
    ):
        self.surprise_threshold = surprise_threshold
        self.max_repairs_per_episode = max_repairs_per_episode
        self.repair_cooldown = repair_cooldown
        self.planner = planner

        # Repair tracking
        self.repairs_this_episode = 0
        self.steps_since_last_repair = repair_cooldown  # Start ready
        self.repair_history: List[Dict] = []

    def check_and_repair(
        self,
        current_plan: RiskAwarePlanResult,
        current_latent: torch.Tensor,
        current_step: int,
        ensemble_surprise: float,
        goal_latent: Optional[torch.Tensor] = None
    ) -> RiskAwarePlanResult:
        """
        Check if plan needs repair based on surprise spike.
        If surprise exceeds threshold, truncate and re-plan.

        Returns either the original plan (if no repair needed) or
        a repaired plan with updated option sequence.
        """
        self.steps_since_last_repair += 1

        # Check if repair is warranted
        needs_repair = (
            ensemble_surprise > self.surprise_threshold and
            self.repairs_this_episode < self.max_repairs_per_episode and
            self.steps_since_last_repair >= self.repair_cooldown
        )

        if not needs_repair:
            return current_plan

        # Identify invalid step: the step where surprise spiked
        invalid_step = current_step

        # Truncate plan at invalid step
        valid_prefix = current_plan.option_sequence[:invalid_step]

        # Re-plan from current state
        if self.planner is not None:
            new_plan = self.planner.plan(current_latent, goal_latent)

            # Merge: valid prefix + new suffix
            repaired_sequence = valid_prefix + new_plan.option_sequence

            repair_record = {
                'original_steps': len(current_plan.option_sequence),
                'invalid_step': invalid_step,
                'valid_prefix_len': len(valid_prefix),
                'new_suffix_len': len(new_plan.option_sequence),
                'surprise_at_repair': ensemble_surprise
            }
            self.repair_history.append(repair_record)

            # Update plan
            new_plan.option_sequence = repaired_sequence
            new_plan.selected_option = repaired_sequence[0] if repaired_sequence else "skill_0"
            new_plan.plan_repair_count = current_plan.plan_repair_count + 1

            self.repairs_this_episode += 1
            self.steps_since_last_repair = 0

            logger.info(f"🔧 Plan repaired at step {invalid_step} "
                        f"(surprise={ensemble_surprise:.2f}, "
                        f"prefix={len(valid_prefix)}, suffix={len(new_plan.option_sequence)})")

            return new_plan

        # No planner available — return original with warning
        current_plan.constraint_violations.append("repair_failed_no_planner")
        return current_plan

    def reset_episode(self):
        """Reset repair tracking for new episode."""
        self.repairs_this_episode = 0
        self.steps_since_last_repair = self.repair_cooldown


class TemporalBoundaryConsistencyChecker:
    """
    L7 Ceiling-Pushed: Temporal Boundary Consistency.

    When L7 plans a sequence of options, it treats each option independently.
    But in reality, the end state of option N must satisfy the preconditions
    of option N+1. If the boundary state doesn't match, the plan will fail
    at the transition — not because either option is bad, but because they
    don't compose.

    This checker:
    1. For each adjacent pair of options in the plan, predicts the boundary state
    2. Checks if the boundary state satisfies the next option's preconditions
    3. Flags boundary violations
    4. Proposes transition options (short bridging skills) to fix violations

    Without this, plans can look good in expectation but fail at transitions.
    The planner optimizes each option's value independently, missing the
    compositional constraint that options must chain smoothly.
    """

    def __init__(
        self,
        world_model=None,
        boundary_tolerance: float = 0.5,
        precondition_threshold: float = 0.7
    ):
        self.world_model = world_model
        self.boundary_tolerance = boundary_tolerance
        self.precondition_threshold = precondition_threshold

        # History of boundary violations for learning
        self.violation_history: List[Dict] = []
        self.transition_options: Dict[str, str] = {}  # "skillA->skillB" -> bridging_skill

    def check_plan(
        self,
        plan_result: RiskAwarePlanResult,
        initial_latent: torch.Tensor,
        skill_library: Optional[Dict] = None
    ) -> RiskAwarePlanResult:
        """
        Check temporal boundary consistency across the plan's option sequence.

        For each pair of adjacent options, predict the boundary state and
        verify it satisfies the next option's preconditions.
        """
        if self.world_model is None or len(plan_result.option_sequence) < 2:
            return plan_result

        boundary_violations = []
        current_latent = initial_latent

        for i in range(len(plan_result.option_sequence) - 1):
            current_skill = plan_result.option_sequence[i]
            next_skill = plan_result.option_sequence[i + 1]

            # Predict boundary state after executing current option
            boundary_state = self._predict_boundary_state(
                current_latent, current_skill
            )

            # Check if boundary state satisfies next option's preconditions
            violation = self._check_precondition_match(
                boundary_state, next_skill, skill_library
            )

            if violation is not None:
                boundary_violations.append(violation)

                # Check if we have a learned transition option
                transition_key = f"{current_skill}->{next_skill}"
                if transition_key in self.transition_options:
                    # Insert bridging skill
                    violation['bridge_available'] = True
                    violation['bridge_skill'] = self.transition_options[transition_key]

            # Advance latent for next boundary check
            if boundary_state is not None:
                current_latent = boundary_state

        # Update plan result
        plan_result.boundary_violations = [v['description'] for v in boundary_violations]

        # Record for learning
        if boundary_violations:
            self.violation_history.append({
                'plan_options': plan_result.option_sequence,
                'violations': boundary_violations,
                'n_violations': len(boundary_violations)
            })

        return plan_result

    def _predict_boundary_state(
        self,
        current_latent: torch.Tensor,
        skill_id: str
    ) -> Optional[torch.Tensor]:
        """Predict the latent state after executing a skill."""
        if self.world_model is None:
            return None

        with torch.no_grad():
            # Simplified: predict a few steps ahead
            state = current_latent
            for _ in range(5):  # Assume ~5 steps per option
                next_latent, _, _, _ = self.world_model.predict_next(state)
                state = next_latent

        return state

    def _check_precondition_match(
        self,
        boundary_state: Optional[torch.Tensor],
        next_skill_id: str,
        skill_library: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Check if boundary state satisfies next skill's preconditions.

        Returns None if consistent, or a violation dict if not.
        """
        if boundary_state is None:
            return None

        # Get preconditions for next skill
        preconditions = {}
        if skill_library and next_skill_id in skill_library:
            preconditions = skill_library[next_skill_id].get('preconditions', {})

        # If no preconditions defined, check latent norm as proxy
        latent_norm = boundary_state.norm().item()

        if latent_norm > 10.0:  # Unusually large latent = likely OOD
            return {
                'description': f"Boundary state norm {latent_norm:.2f} exceeds threshold for {next_skill_id}",
                'next_skill': next_skill_id,
                'latent_norm': latent_norm,
                'preconditions': preconditions
            }

        # Check specific preconditions if available
        for prec_name, prec_value in preconditions.items():
            # Simplified: check if boundary state satisfies named preconditions
            if prec_name.startswith('latent_norm_'):
                max_norm = float(prec_name.split('_')[-1])
                if latent_norm > max_norm:
                    return {
                        'description': f"Boundary norm {latent_norm:.2f} > {max_norm} for {next_skill_id}",
                        'next_skill': next_skill_id,
                        'latent_norm': latent_norm,
                        'precondition': prec_name
                    }

        return None

    def learn_transition_option(
        self,
        from_skill: str,
        to_skill: str,
        bridge_skill: str
    ):
        """Learn that a bridge skill can smooth the transition between two skills."""
        key = f"{from_skill}->{to_skill}"
        self.transition_options[key] = bridge_skill
        logger.info(f"🔗 Learned transition: {key} -> {bridge_skill}")
