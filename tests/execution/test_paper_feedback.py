"""Real paper adapter -> durable fills -> CSC economic reward -> scorer."""
import json
from dataclasses import replace

import pytest

from trading_bot.core.csc.controller import CognitiveSystemController
from trading_bot.execution.paper_feedback import PaperSettlementFeedback, match_paper_fills
from trading_bot.execution.service import CanonicalExecutionService, PaperBrokerAdapter
from trading_bot.foundation.contracts import (
    AuditEvent, Instrument, InstrumentType, OrderRequest, OrderSide, OrderStatus, OrderType)
from trading_bot.persistence.repositories import SqliteTradingRepository, decode_report


@pytest.fixture
def stack(tmp_path):
    repo = SqliteTradingRepository(str(tmp_path / "trading_state.db"))
    adapter = PaperBrokerAdapter(spread_bps=2, slippage_bps=1.25,
                                 commission_per_unit=0.05)
    adapter.market_data_source = "synthetic"
    service = CanonicalExecutionService(adapter=adapter, repository=repo)
    CognitiveSystemController._instance = None
    csc = CognitiveSystemController()
    csc.configure_decision_sink(repo)
    yield repo, adapter, service, csc
    repo.close()
    CognitiveSystemController._instance = None


async def submit(stack, cid, side, price, quantity=2, symbol="TEST", contract=10):
    repo, adapter, service, _ = stack
    adapter.on_mark(symbol, price)
    order = OrderRequest(
        instrument=Instrument(symbol, InstrumentType.SYNTHETIC, "paper",
                              contract_size=contract),
        side=side, order_type=OrderType.MARKET, quantity=quantity,
        client_order_id=cid, decision_id="decision-" + cid, price=price)
    return order, await service.submit(order)


async def events(repo):
    rows = await repo.list_audit_events(event_type="PAPER_SETTLEMENT")
    return [json.loads(row["event_json"]) for row in rows]


@pytest.mark.asyncio
@pytest.mark.parametrize("side,exit_price", [(OrderSide.BUY, 102), (OrderSide.SELL, 98)])
async def test_actual_costs_and_same_notional_baseline_reach_csc(stack, tmp_path, side, exit_price):
    repo, adapter, service, csc = stack
    _, opening = await submit(stack, "entry", side, 100)
    opposite = OrderSide.SELL if side is OrderSide.BUY else OrderSide.BUY
    _, closing = await submit(stack, "exit", opposite, exit_price)
    feedback = PaperSettlementFeedback(repo, csc)
    status = await feedback.sync()
    assert status["costed_lots"] == status["new_feedback"] == 1
    detail = (await events(repo))[0]["details"]
    direction = 1 if side is OrderSide.BUY else -1
    expected_net = (direction * 2 * 10 *
                    (closing.fills[0].price - opening.fills[0].price)
                    - opening.fills[0].commission - closing.fills[0].commission)
    assert detail["net_pnl"] == pytest.approx(expected_net)
    assert detail["entry_notional"] == 2000
    assert detail["net_return"] == pytest.approx(expected_net / 2000)
    assert detail["gross_return"] - detail["cost_return"] == pytest.approx(detail["net_return"])
    assert detail["market_data_source"] == "synthetic"
    reward = detail["rewards"][0]
    objectives = {o["name"]: o["value"] for o in reward["objectives"]}
    assert objectives["net_return"] == pytest.approx(detail["net_return"])
    if side is OrderSide.BUY:
        assert objectives["alpha_vs_baseline"] == pytest.approx(0)
    else:
        assert objectives["alpha_vs_baseline"] > 0
    # Fills alone do not assert every risk gate was satisfied.
    assert "constraints_unverified" in reward["blockers"]
    assert reward["promotion_eligible"] is False
    from scripts.score_paper_run import fill_reward_report
    score = fill_reward_report(tmp_path)
    assert score["by_currency"]["USD"]["net_pnl"] == pytest.approx(expected_net)
    assert score["opening_decisions"] == 1


@pytest.mark.asyncio
async def test_flat_price_loses_only_recorded_costs_not_costs_twice(stack):
    repo, _, _, csc = stack
    await submit(stack, "entry", OrderSide.BUY, 100)
    await submit(stack, "exit", OrderSide.SELL, 100)
    await PaperSettlementFeedback(repo, csc).sync()
    detail = (await events(repo))[0]["details"]
    # 2.25bps each side * 2000 notional + 0.2 commission = 1.1
    assert detail["gross_return"] == 0
    assert detail["net_pnl"] == pytest.approx(-1.1)
    assert detail["cost_return"] == pytest.approx(1.1 / 2000)


@pytest.mark.asyncio
async def test_scale_in_partial_close_reversal_conserve_quantity_and_fees(stack):
    repo, _, _, csc = stack
    await submit(stack, "a", OrderSide.BUY, 100, quantity=4)
    await submit(stack, "b", OrderSide.SELL, 101, quantity=1)
    feedback = PaperSettlementFeedback(repo, csc)
    assert (await feedback.sync())["matched_lots"] == 1
    await submit(stack, "c", OrderSide.SELL, 102, quantity=5)
    await submit(stack, "d", OrderSide.BUY, 101, quantity=2)
    assert (await feedback.sync())["matched_lots"] == 3
    details = [ev["details"] for ev in await events(repo)]
    assert sorted(d["quantity"] for d in details) == [1, 2, 3]
    assert sum(d["commission"] for d in details) == pytest.approx(12 * 0.05)
    a = [d for d in details if d["entry_order_id"] == "a"]
    assert sum(d["sample_weight"] for d in a) == 1
    assert (await feedback.sync())["new_feedback"] == 0


@pytest.mark.asyncio
async def test_multiple_entries_use_their_own_marks_and_notional(stack):
    repo, _, _, csc = stack
    await submit(stack, "a", OrderSide.BUY, 100, quantity=1)
    await submit(stack, "b", OrderSide.BUY, 110, quantity=2)
    await submit(stack, "c", OrderSide.SELL, 120, quantity=3)
    await PaperSettlementFeedback(repo, csc).sync()
    details = {e["details"]["entry_order_id"]: e["details"] for e in await events(repo)}
    assert details["a"]["entry_notional"] == 1000
    assert details["b"]["entry_notional"] == 2200
    assert details["a"]["gross_return"] == pytest.approx(0.2)
    assert details["b"]["gross_return"] == pytest.approx(10 / 110)


@pytest.mark.asyncio
async def test_cost_settings_at_each_fill_are_preserved(stack):
    repo, adapter, _, csc = stack
    await submit(stack, "a", OrderSide.BUY, 100)
    adapter.spread_bps = 4
    adapter.commission_per_unit = 0.2
    await submit(stack, "b", OrderSide.SELL, 100)
    adapter.spread_bps = 999  # current settings must not reprice past fills
    await PaperSettlementFeedback(repo, csc).sync()
    detail = (await events(repo))[0]["details"]
    assert detail["entry_reference"]["spread_bps"] == 2
    assert detail["exit_reference"]["spread_bps"] == 4
    assert detail["commission"] == pytest.approx(0.5)
    assert detail["net_pnl"] == pytest.approx(-(2000 * (2.25 + 3.25) / 10000 + 0.5))
    assert detail["baseline_net_return"] == pytest.approx(detail["net_return"])


@pytest.mark.asyncio
async def test_partial_fills_of_one_order_share_one_decision_weight(stack):
    repo, adapter, _, csc = stack
    order = OrderRequest(
        instrument=Instrument("TEST", InstrumentType.SYNTHETIC, "paper",
                              contract_size=10),
        side=OrderSide.BUY, order_type=OrderType.MARKET, quantity=4,
        client_order_id="partial", decision_id="one-decision", price=100)
    first = adapter._fill(replace(order, quantity=2), 100)
    await repo.record_execution(order, replace(first, status=OrderStatus.PARTIALLY_FILLED))
    second = adapter._fill(replace(order, quantity=2), 101)
    await repo.record_execution(order, second)
    await submit(stack, "exit", OrderSide.SELL, 102, quantity=4)
    await PaperSettlementFeedback(repo, csc).sync()
    details = [e["details"] for e in await events(repo)]
    assert len(details) == 2
    assert sum(d["sample_weight"] for d in details) == 1
    assert sum(d["quantity"] for d in details) == 4


@pytest.mark.asyncio
async def test_restart_and_duplicate_receipts_cannot_duplicate_rewards(stack, tmp_path):
    repo, _, service, csc = stack
    order, _ = await submit(stack, "a", OrderSide.BUY, 100)
    await submit(stack, "b", OrderSide.SELL, 100)
    feedback = PaperSettlementFeedback(repo, csc)
    await feedback.sync()
    original = (await events(repo))[0]
    await service.submit(order)
    rows = await repo.list_fill_receipts()
    assert len(match_paper_fills(rows + rows)) == 1
    # Reopen SQLite and rebuild adapter state from the same authoritative ledger.
    other = SqliteTradingRepository(str(tmp_path / "trading_state.db"))
    try:
        restored = CanonicalExecutionService(repository=other)
        await restored.restore_state()
        csc.configure_decision_sink(other)
        assert (await PaperSettlementFeedback(other, csc).sync())["new_feedback"] == 0
        assert (await events(other))[0] == original
        stored = await other.get_order("a")
        decoded = decode_report(stored["report_json"])
        assert decoded.fills[0].execution_reference["mark_price"] == 100
    finally:
        other.close()


@pytest.mark.asyncio
async def test_open_position_and_pending_orders_do_not_earn_economic_rewards(stack):
    repo, adapter, service, csc = stack
    adapter.latency_cycles = 1
    order, _ = await submit(stack, "a", OrderSide.BUY, 100)
    assert (await PaperSettlementFeedback(repo, csc).sync())["matched_lots"] == 0
    adapter.on_mark("TEST", 105)
    report = await adapter.get_order("a")
    await repo.record_execution(order, report)
    assert report.fills[0].execution_reference["mark_price"] == 105
    assert (await PaperSettlementFeedback(repo, csc).sync())["matched_lots"] == 0
    assert not await events(repo)
    adapter.latency_cycles = 0
    await submit(stack, "b", OrderSide.SELL, 110)
    await PaperSettlementFeedback(repo, csc).sync()
    detail = (await events(repo))[0]["details"]
    assert detail["gross_return"] == pytest.approx(110 / 105 - 1)


@pytest.mark.asyncio
async def test_old_fill_reference_is_missing_not_reconstructed_from_settings(stack):
    repo, adapter, service, csc = stack
    order, report = await submit(stack, "a", OrderSide.BUY, 100)
    await submit(stack, "b", OrderSide.SELL, 101)
    rows = await repo.list_fill_receipts()
    fill = json.loads(rows[0]["fill_json"])
    fill.pop("execution_reference")
    rows[0]["fill_json"] = json.dumps(fill)
    detail = match_paper_fills(rows)[0]
    assert detail["gross_return"] is detail["cost_return"] is None
    assert "missing_or_unsupported_fill_reference" in detail["blockers"]
    adapter.spread_bps = 100
    assert match_paper_fills(rows)[0] == detail


@pytest.mark.asyncio
async def test_symbols_and_contracts_do_not_cross_match(stack):
    repo, _, _, _ = stack
    await submit(stack, "a", OrderSide.BUY, 100, symbol="A")
    await submit(stack, "b", OrderSide.SELL, 100, symbol="B")
    assert not match_paper_fills(await repo.list_fill_receipts())


@pytest.mark.asyncio
async def test_audit_replay_rejects_changed_evidence(stack):
    repo, _, _, _ = stack
    event = AuditEvent(event_type="PAPER_SETTLEMENT", actor="CSC",
                       action="execution_reward", outcome="costed",
                       correlation_id="a", details={"net_return": 0.1})
    assert await repo.record_audit_event_once(event, audit_id="one")
    assert not await repo.record_audit_event_once(event, audit_id="one")
    with pytest.raises(ValueError, match="different evidence"):
        await repo.record_audit_event_once(
            replace(event, details={"net_return": 0.9}), audit_id="one")


@pytest.mark.asyncio
async def test_failed_delivery_can_retry_without_losing_feedback(stack, monkeypatch):
    repo, _, _, csc = stack
    await submit(stack, "a", OrderSide.BUY, 100)
    await submit(stack, "b", OrderSide.SELL, 101)
    feedback = PaperSettlementFeedback(repo, csc)
    original = repo.record_audit_event_once

    async def fail(*args, **kwargs):
        raise OSError("disk unavailable")

    monkeypatch.setattr(repo, "record_audit_event_once", fail)
    with pytest.raises(OSError):
        await feedback.sync()
    assert not await events(repo)
    monkeypatch.setattr(repo, "record_audit_event_once", original)
    assert (await feedback.sync())["new_feedback"] == 1
