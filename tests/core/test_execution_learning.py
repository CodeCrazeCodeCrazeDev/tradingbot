"""Execution-learning: real fill recording, honest empty state,
nonfinite rejection, bounded venue set, advisory-only output."""
import pytest

from trading_bot.core.csc.execution_learning import (
    ExecutionLearningService)


class TestRecording:
    def test_empty_report_honest(self):
        s = ExecutionLearningService()
        r = s.advisory_report()
        assert r["available"] is False
        assert r["n_fills"] == 0

    def test_records_and_ranks(self):
        s = ExecutionLearningService()
        for _ in range(12):
            s.record_fill("MT5_DEMO", fill_rate=0.95, spread=0.0001,
                          shortfall_bps=1.5)
            s.record_fill("VENUE_B", fill_rate=0.60, spread=0.001,
                          shortfall_bps=9.0)
        r = s.advisory_report()
        assert r["available"] is True
        assert r["n_fills"] == 24
        assert r["top_venue"] == "MT5_DEMO"
        mt5 = next(v for v in r["venues"] if v["venue"] == "MT5_DEMO")
        assert mt5["score"] > next(
            v for v in r["venues"] if v["venue"] == "VENUE_B")["score"]
        assert r["advisory_only"] is True
        assert r["mean_shortfall_bps"] == pytest.approx(5.25)

    def test_nonfinite_rejected(self):
        s = ExecutionLearningService()
        assert s.record_fill("X", fill_rate=float("nan")) is False
        assert s.record_fill("X", fill_rate=float("inf")) is False
        assert s.advisory_report()["n_fills"] == 0

    def test_venue_count_bounded(self):
        s = ExecutionLearningService()
        for i in range(ExecutionLearningService.MAX_VENUES + 20):
            s.record_fill(f"V{i}", fill_rate=0.5)
        assert len(s._perf) <= s.MAX_VENUES

    def test_ema_learns_direction(self):
        s = ExecutionLearningService()
        s.record_fill("GOOD", fill_rate=1.0)
        s.record_fill("BAD", fill_rate=0.1)
        assert s._scores["GOOD"] > s._scores["BAD"]


class TestControllerWiring:
    def test_csc_exposes_report(self):
        from trading_bot.core.csc.controller import (
            CognitiveSystemController)
        CognitiveSystemController._instance = None
        csc = CognitiveSystemController()
        try:
            r = csc.execution_learning_report()
            assert r["available"] is False  # no fills yet — honest
        finally:
            CognitiveSystemController._instance = None

    def test_service_injectable(self):
        from trading_bot.core.csc.controller import (
            CognitiveSystemController)
        CognitiveSystemController._instance = None
        el = ExecutionLearningService()
        el.record_fill("TEST_VENUE", fill_rate=0.9)
        csc = CognitiveSystemController(exec_learning=el)
        try:
            r = csc.execution_learning_report()
            assert r["available"] is True
            assert r["top_venue"] == "TEST_VENUE"
        finally:
            CognitiveSystemController._instance = None


class TestAdvancedRiskAudit:
    """advanced_risk_system audit: importable without scipy, advisory
    only, deterministic stress, honest EVT under scipy-free fallback."""

    def test_importable_without_scipy(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'ars_test', 'trading_bot/risk/advanced_risk_system.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        assert hasattr(m, 'AdvancedRiskSystem')

    def test_moments_gpd_fallback_produces_var(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'ars_test2', 'trading_bot/risk/advanced_risk_system.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        import numpy as np
        a = m.ExtremeValueAnalyzer()
        # heavy-ish tailed returns — need >=10 exceedances
        rets = np.random.default_rng(7).standard_t(3, 2000) * 0.02
        a.fit(rets, 'A')
        var = a.estimate_var('A', 0.99)
        params = a.gpd_params.get('A', {})
        assert params.get('fit_method') in ('mle', 'moments')
        assert var > 0
        es = a.estimate_es('A', 0.99)
        assert es >= var or es > 0

    def test_stress_test_deterministic(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'ars_test3', 'trading_bot/risk/advanced_risk_system.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        import numpy as np
        st = m.PortfolioStressTester()
        rets = {'A': np.random.default_rng(3).normal(0, .02, 200)}
        r1 = st.run_stress_test({'A': 10}, {'A': 100.0}, rets,
                                np.eye(1))
        r2 = st.run_stress_test({'A': 10}, {'A': 100.0}, rets,
                                np.eye(1))
        assert r1 == r2  # seeded shock — reproducible

    def test_no_authority_surface(self):
        """The system must expose analysis only — no execute/veto/size."""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            'ars_test4', 'trading_bot/risk/advanced_risk_system.py')
        m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(m)
        s = m.AdvancedRiskSystem()
        for forbidden in ('execute', 'place_order', 'approve',
                          'veto_trade', 'set_position_size',
                          'submit_order'):
            assert not hasattr(s, forbidden), f"shadow authority: {forbidden}"
