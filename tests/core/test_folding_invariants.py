import pytest
from trading_bot.core.csc.folding import InformationFolder, FoldingOperator

@pytest.mark.asyncio
async def test_folding_determinism():
    folder = InformationFolder()
    task = "execute_arbitrage"
    log = [{"step": 1, "action": "buy"}, {"step": 2, "action": "sell"}]
    state = {"success": True, "confidence": 0.95, "active_branches": ["branch_a"]}

    res1 = await folder.fold(task, log, state)
    res2 = await folder.fold(task, log, state)

    assert res1["semantic_update"] == res2["semantic_update"]
    assert res1["determinism_hash"] == res2["determinism_hash"]

@pytest.mark.asyncio
async def test_folding_bounded_growth():
    folder = InformationFolder()
    task = "market_analysis"
    # Large execution log
    log = [{"msg": f"Very high resolution trace message {i}"} for i in range(100)]
    state = {"success": True}

    res = await folder.fold(task, log, state)
    original_size = sum(len(str(s)) for s in log)
    folded_size = len(res["semantic_update"])

    assert folded_size < original_size
    assert res["tokens_saved"] > 0

@pytest.mark.asyncio
async def test_folding_operator_inheritance():
    # Verify legacy alias works
    operator = FoldingOperator()
    assert isinstance(operator, InformationFolder)
    assert hasattr(operator, "fold")
