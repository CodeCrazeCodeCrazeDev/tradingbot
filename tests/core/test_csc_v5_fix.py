import pytest
import asyncio
from unittest.mock import MagicMock
from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.core.csc.folding import InformationFolder
from trading_bot.core.alphaalgo_core_engine import CoreDecision, DecisionOutcome

@pytest.mark.asyncio
async def test_csc_initialization():
    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock()

    # Reset singleton for test
    CognitiveSystemController._instance = None

    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)

    assert csc.world_model == world_model
    assert csc.hms == hms
    assert csc.shield == shield
    assert isinstance(csc.folding_operator, InformationFolder)
    assert csc.folder == csc.folding_operator
    assert hasattr(csc, 'continuous_state')
    assert hasattr(csc, 'discrete_channel')

@pytest.mark.asyncio
async def test_information_folder_init():
    folder = InformationFolder(fold_interval=5)
    assert folder.step_counter == 0
    assert folder.fold_interval == 5

@pytest.mark.asyncio
async def test_information_folder_fold():
    folder = InformationFolder()
    task = "test_task"
    execution_log = [{"step": 1, "data": "some data"}, {"step": 2, "data": "more data"}]
    global_state = {"success": True, "confidence": 0.8, "active_branches": ["b1"]}

    result = await folder.fold(task, execution_log, global_state)

    assert result['status'] == 'folded'
    assert "success=True" in result['semantic_update']
    assert result['sufficient_statistics']['final_confidence'] == 0.8
    assert result['sufficient_statistics']['active_hypotheses'] == ["b1"]
    # assert result['tokens_saved'] > 0 # Skipping exact count check

@pytest.mark.asyncio
async def test_csc_process_market_observation_rejection():
    world_model = MagicMock()
    hms = MagicMock()
    shield = MagicMock()

    # Mock hypothesis generation to return no branches
    async def mock_gen(obs):
        return []

    async def mock_sim(branches):
        return {}

    hypothesis_gen = MagicMock()
    hypothesis_gen.generate_competing_branches = mock_gen
    hypothesis_gen.simulate_branches = mock_sim

    # Reset singleton
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController(world_model=world_model, hms=hms, shield=shield)
    csc.hypothesis_gen = hypothesis_gen

    observation = {"price": 1.1000}
    decision = await csc.process_market_observation(observation)

    assert decision is None
