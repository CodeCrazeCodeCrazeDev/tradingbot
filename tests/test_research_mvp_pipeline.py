#!/usr/bin/env python3
"""Tests for AlphaAlgo's research MVP pipeline substrate."""

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path


MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "core" / "research_mvp_pipeline.py"
SPEC = importlib.util.spec_from_file_location("research_mvp_pipeline_direct", MODULE_PATH)
rp = importlib.util.module_from_spec(SPEC)
sys.modules["research_mvp_pipeline_direct"] = rp
SPEC.loader.exec_module(rp)


def _ts(day):
    return datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp()


def _bar(symbol, day, close, volume=1000.0):
    return rp.MarketBar(
        symbol=symbol,
        timestamp=_ts(day),
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=volume,
        source_id="test-feed",
    )


def _assert_raises(exc_type, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except exc_type:
        return
    raise AssertionError(f"expected {exc_type.__name__}")


def test_clean_data_pipeline_rejects_bad_rows_dedupes_sorts_and_hashes_lineage():
    rows = [
        {"symbol": "bbb", "timestamp": "2024-01-02", "open": 20, "high": 21, "low": 19, "close": 20, "volume": 200},
        {"symbol": "aaa", "timestamp": "2024-01-01", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100},
        {"symbol": "aaa", "timestamp": "2024-01-01", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100},
        {"symbol": "aaa", "timestamp": "2024-01-04", "open": 13, "high": 14, "low": 12, "close": 13, "volume": 120},
        {"symbol": "bad", "timestamp": "2024-01-01", "open": -1, "high": 1, "low": 1, "close": 1, "volume": 10},
    ]

    pipeline = rp.CleanDataPipeline(expected_interval_seconds=86400.0)
    report = pipeline.normalize(rows)
    report_again = pipeline.normalize(rows)

    assert [bar.symbol for bar in report.bars] == ["AAA", "AAA", "BBB"]
    assert report.duplicate_count == 1
    assert len(report.rejected_rows) == 1
    assert "OHLC prices must be positive" in report.rejected_rows[0].reason
    assert any("AAA missing session" in warning for warning in report.missing_sessions)
    assert report.lineage_hash == report_again.lineage_hash
    assert len(report.lineage_hash) == 64


def test_corporate_actions_and_survivorship_free_universe_keep_point_in_time_history():
    bars = [
        _bar("AAA", "2024-01-01", 100, 100),
        _bar("AAA", "2024-01-03", 110, 100),
        _bar("DEL", "2024-01-01", 50, 100),
        _bar("DEL", "2024-01-03", 40, 100),
    ]
    actions = [
        rp.CorporateAction(
            symbol="AAA",
            effective_at=_ts("2024-01-02"),
            action_type=rp.CorporateActionType.SPLIT,
            ratio=2.0,
        )
    ]

    adjusted = rp.CorporateActionsHandler().apply(bars, actions)
    adjusted_aaa = [bar for bar in adjusted if bar.symbol == "AAA"]
    assert adjusted_aaa[0].close == 50
    assert adjusted_aaa[0].volume == 200
    assert adjusted_aaa[0].adjusted is True
    assert adjusted_aaa[1].close == 110
    assert adjusted_aaa[1].adjusted is False

    universe = rp.SurvivorshipFreeUniverse(
        [
            rp.UniverseMembership("u1", "AAA", _ts("2024-01-01")),
            rp.UniverseMembership("u1", "DEL", _ts("2024-01-01"), end_at=_ts("2024-01-02")),
        ]
    )
    filtered = universe.filter_bars("u1", adjusted)
    assert [(bar.symbol, bar.timestamp) for bar in filtered] == [
        ("AAA", _ts("2024-01-01")),
        ("AAA", _ts("2024-01-03")),
        ("DEL", _ts("2024-01-01")),
    ]
    assert universe.active_symbols("u1", _ts("2024-01-01")) == ["AAA", "DEL"]
    assert universe.active_symbols("u1", _ts("2024-01-03")) == ["AAA"]


def test_transaction_costs_paper_ledger_and_portfolio_accounting_reconcile():
    cost_model = rp.ResearchTransactionCostModel(
        broker_fee_model=rp.BrokerFeeModel(per_share_fee=0.01, per_order_fee=1.0, fee_bps=1.0, min_fee=1.0),
        half_spread_bps=1.0,
        slippage_bps=1.0,
        market_impact_coefficient_bps=0.0,
    )
    ledger = rp.PaperTradingLedger(starting_cash=10_000.0, cost_model=cost_model)

    buy_fill = ledger.execute_order(
        rp.PaperOrder("buy-1", "AAA", rp.OrderSide.BUY, 10, _ts("2024-01-01")),
        _bar("AAA", "2024-01-01", 100),
    )
    assert buy_fill is not None
    assert buy_fill.cost.total_cost > 0
    assert ledger.cash < 9000
    assert ledger.positions["AAA"].quantity == 10
    assert ledger.positions["AAA"].average_cost > 100

    sell_fill = ledger.execute_order(
        rp.PaperOrder("sell-1", "AAA", rp.OrderSide.SELL, 5, _ts("2024-01-02")),
        _bar("AAA", "2024-01-02", 110),
    )
    assert sell_fill is not None
    assert sell_fill.realized_pnl > 0
    snapshot = ledger.snapshot(_ts("2024-01-02"), {"AAA": 110})
    assert snapshot.positions == {"AAA": 5}
    assert snapshot.net_liquidation_value > ledger.cash
    assert snapshot.realized_pnl > 0


def test_reproducible_runner_produces_stable_run_ids_and_config_sensitive_ids():
    bars = [_bar("AAA", "2024-01-01", 100), _bar("AAA", "2024-01-02", 110)]
    orders = [rp.PaperOrder("order-1", "AAA", rp.OrderSide.BUY, 10, _ts("2024-01-01"))]
    registry = rp.ExperimentRegistry()
    runner = rp.ReproducibleResearchRunner(experiment_registry=registry)
    config = rp.ResearchRunConfig(
        experiment_name="smoke-test",
        strategy_name="buy-and-hold",
        starting_cash=10_000.0,
        benchmark_dataset_id="user_supplied_point_in_time_equities",
        universe_id="u1",
        parameters={"lookback": 5},
        code_version="abc123",
    )

    report_one = runner.run(config, bars, orders)
    report_two = runner.run(config, list(reversed(bars)), orders)
    changed_config = rp.ResearchRunConfig(
        experiment_name="smoke-test",
        strategy_name="buy-and-hold",
        starting_cash=10_000.0,
        benchmark_dataset_id="user_supplied_point_in_time_equities",
        universe_id="u1",
        parameters={"lookback": 10},
        code_version="abc123",
    )
    report_three = runner.run(changed_config, bars, orders)

    assert report_one.run_id == report_two.run_id
    assert report_one.run_id != report_three.run_id
    assert report_one.metrics["fill_count"] == 1.0
    assert report_one.metrics["total_cost"] > 0
    assert registry.get(report_one.run_id).data_lineage_hash == report_one.data_lineage_hash


def test_experiment_registry_records_artifacts_and_reuses_identical_records():
    registry = rp.ExperimentRegistry()

    one = registry.record(
        name="exp",
        config={"threshold": 1},
        data_lineage_hash="data-hash",
        code_version="code",
        artifact_hashes={"report": "abc"},
        metrics={"return": 0.1},
    )
    two = registry.record(
        name="exp",
        config={"threshold": 1},
        data_lineage_hash="data-hash",
        code_version="code",
        artifact_hashes={"report": "abc"},
        metrics={"return": 0.1},
    )
    three = registry.record(
        name="exp",
        config={"threshold": 2},
        data_lineage_hash="data-hash",
        code_version="code",
    )

    assert one.experiment_id == two.experiment_id
    assert one.experiment_id != three.experiment_id
    assert len(registry.records) == 2
    assert registry.get(one.experiment_id).artifact_hashes["report"] == "abc"


def test_onboarding_workflow_and_customer_report_create_a_minimum_customer_surface():
    dataset = rp.BenchmarkDatasetRegistry.with_default_datasets().get("user_supplied_point_in_time_equities")
    checklist = rp.OnboardingWorkflow().evaluate(
        rp.OnboardingRequest(
            customer_name="Seed Customer",
            asset_universe=["aaa", "bbb"],
            data_sources=[dataset],
            strategy_description="mean reversion on a point-in-time equities universe",
            benchmark_dataset_ids=[dataset.dataset_id],
            cost_assumptions={
                "half_spread_bps": 1.0,
                "slippage_bps": 2.0,
                "broker_fee_model": {"per_share_fee": 0.005},
            },
            risk_limits={"max_drawdown": 0.1, "max_position_size": 0.05, "kill_switch": True},
        )
    )
    assert checklist.accepted is True
    assert checklist.normalized_config["asset_universe"] == ["AAA", "BBB"]

    runner = rp.ReproducibleResearchRunner()
    run_report = runner.run(
        rp.ResearchRunConfig(
            experiment_name="customer-demo",
            strategy_name="buy-and-hold",
            starting_cash=10_000.0,
            benchmark_dataset_id=dataset.dataset_id,
            universe_id="u1",
        ),
        [_bar("AAA", "2024-01-01", 100), _bar("AAA", "2024-01-02", 105)],
        [rp.PaperOrder("buy", "AAA", rp.OrderSide.BUY, 10, _ts("2024-01-01"))],
    )
    builder = rp.CustomerReportBuilder()
    markdown = builder.build_markdown(run_report)
    payload = builder.build_payload(run_report)

    assert "# AlphaAlgo Research Report" in markdown
    assert "transaction cost" in markdown.lower()
    assert payload["run_id"] == run_report.run_id
    assert any("transaction costs" in item for item in payload["kill_criteria"])


def test_benchmark_dataset_registry_rejects_unknown_private_unlicensed_or_weak_sources():
    registry = rp.BenchmarkDatasetRegistry()
    weak = rp.BenchmarkDataset(
        dataset_id="weak",
        name="Weak source",
        asset_class="equities",
        source_uri="",
        license_status=rp.DatasetLicenseStatus.UNKNOWN,
        provenance=[],
        timestamp=0.0,
        compliance_score=0.2,
    )
    private = rp.BenchmarkDataset(
        dataset_id="private",
        name="Private source",
        asset_class="equities",
        source_uri="private://leak",
        license_status=rp.DatasetLicenseStatus.PRIVATE,
        provenance=["unapproved export"],
        timestamp=0.0,
        compliance_score=0.99,
    )

    _assert_raises(ValueError, registry.register, weak)
    _assert_raises(ValueError, registry.register, private)
    assert "fred_macro_public" in {dataset.dataset_id for dataset in rp.BenchmarkDatasetRegistry.with_default_datasets().list()}

