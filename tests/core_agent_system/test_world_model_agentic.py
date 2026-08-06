import pytest
import torch
from trading_bot.world_model.latent_dynamics import AgenticPlanningWorldModel

def test_agentic_planning_world_model():
    latent_dim = 64
    action_dim = 5
    hidden_dim = 128

    model = AgenticPlanningWorldModel(latent_dim=latent_dim, hidden_dim=hidden_dim, action_dim=action_dim)

    # Test forward pass
    state = torch.randn(1, latent_dim)
    action = torch.randn(1, action_dim)

    prospective_next, success_estimate = model(state, action)

    assert prospective_next.shape == (1, latent_dim)
    assert success_estimate.shape == (1, 1)
    assert 0.0 <= success_estimate.item() <= 1.0

def test_agentic_training_stages():
    latent_dim = 64
    action_dim = 5

    model = AgenticPlanningWorldModel(latent_dim=latent_dim, action_dim=action_dim)

    states = torch.randn(4, latent_dim)
    actions = torch.randn(4, action_dim)
    next_states = torch.randn(4, latent_dim)
    structured_targets = torch.randn(4, latent_dim)
    actual_success_outcomes = torch.ones(4, 1)

    # Stage 1
    loss_amt = model.wm_amt_inject_latent_predictions(states, actions, next_states)
    assert model.training_stage == "WM-AMT"
    assert loss_amt.item() >= 0

    # Stage 2
    loss_sft = model.fe_sft_format_structure(states, actions, structured_targets)
    assert model.training_stage == "FE-SFT"
    assert loss_sft.item() >= 0

    # Stage 3
    loss_rl = model.fc_rl_refine_foresight(states, actions, actual_success_outcomes)
    assert model.training_stage == "FC-RL"
    assert loss_rl.item() >= 0
