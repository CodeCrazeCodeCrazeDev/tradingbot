"""Extended-capability tests — measured components and honest
unavailable interfaces."""
import pytest

from trading_bot.core.csc.extended_capabilities import (
    AdversarialScenarioSampler, BrokerRegistry, DEFI_INTERFACE,
    Edgar13FAdvisor, LeadLagAnalyzer, ML_MODEL_MONITOR,
    VoiceAlerter, WHALE_TRACKER, WyckoffPhaseAnalyzer)


def _bars(closes, vols=None):
    vols = vols or [100.0] * len(closes)
    return [{"close": c, "volume": v} for c, v in zip(closes, vols)]


class TestWyckoff:
    def test_markup_on_rising_expanding(self):
        # Steadily rising with expanding range + up-volume dominance
        closes = [100 + i * 0.5 for i in range(60)]
        vols = [100 if i % 3 else 300 for i in range(60)]
        out = WyckoffPhaseAnalyzer().analyze(_bars(closes, vols))
        assert out["phase"] == "markup"
        assert out["trend_slope_per_bar"] > 0

    def test_markdown_on_falling(self):
        closes = [130 - i * 0.5 for i in range(60)]
        out = WyckoffPhaseAnalyzer().analyze(_bars(closes))
        assert out["phase"] == "markdown"

    def test_compressed_range_classifies(self):
        # Wide early range then compressed, up-volume dominance →
        # accumulation
        closes = [100 + (20 if i % 2 else -20) for i in range(20)]
        closes += [100 + (0.5 if i % 2 else -0.5) for i in range(20)]
        vols = [100] * 20 + [300 if i % 2 else 50 for i in range(20)]
        out = WyckoffPhaseAnalyzer().analyze(_bars(closes, vols))
        assert out["range_compression"] < 0.6
        assert out["phase"] in ("accumulation", "markdown_exit")

    def test_insufficient_bars_uncertain(self):
        out = WyckoffPhaseAnalyzer().analyze(_bars([1.0] * 10))
        assert out["phase"] == "uncertain"


class TestLeadLag:
    def test_peer_leads_detected(self):
        # Peer moves first by 2 bars
        import math
        n = 80
        peer = [100 + math.sin(i / 8) * 2 for i in range(n)]
        own = [peer[i - 2] if i >= 2 else 100 for i in range(n)]
        hist = [{"close": o, "dxy": p} for o, p in zip(own, peer)]
        out = LeadLagAnalyzer(peer_keys=("dxy",)).analyze(hist)
        assert out["status"] == "measured"
        assert out["best_lag_bars"] == 2
        assert out["correlation"] > 0.9

    def test_insufficient_data(self):
        out = LeadLagAnalyzer().analyze([{"close": 1.0}])
        assert out["status"] == "insufficient_data"


class TestAdversarialSampler:
    BARS = _bars([100 * (1.001 ** i) for i in range(40)])

    def test_deterministic_per_seed(self):
        s1 = AdversarialScenarioSampler(seed=3).scenarios(self.BARS, 2)
        s2 = AdversarialScenarioSampler(seed=3).scenarios(self.BARS, 2)
        assert s1 == s2
        assert all(sc["synthetic"] for sc in s1)

    def test_different_seeds_differ(self):
        a = AdversarialScenarioSampler(seed=3).scenarios(self.BARS, 2)
        b = AdversarialScenarioSampler(seed=4).scenarios(self.BARS, 2)
        assert a != b

    def test_empty_on_short_history(self):
        assert AdversarialScenarioSampler().scenarios(self.BARS[:5]) == []


class TestVoiceAlerter:
    def test_disabled_by_default(self):
        v = VoiceAlerter()
        assert not v.alert("test")

    def test_enabled_fires_speaker(self):
        sent = []
        v = VoiceAlerter(enabled=True, speaker=sent.append)
        assert v.alert("emergency halt")
        import time
        for _ in range(50):
            if sent:
                break
            time.sleep(0.02)
        assert sent == ["emergency halt"]


class TestBrokerRegistry:
    def test_register_and_status(self):
        class _Adapter:
            def status(self):
                return {"ok": True}
        reg = BrokerRegistry()
        reg.register("mt5", _Adapter(), {"filling": "FOK", "hedging": True})
        st = reg.status()
        assert st["mt5"]["probeable"]
        assert st["mt5"]["capabilities"]["filling"] == "FOK"
        assert reg.get("mt5") is not None and reg.get("none") is None


class TestEdgar13F:
    def test_disabled_returns_unavailable(self):
        out = Edgar13FAdvisor(enabled=False).recent_13f("320193")
        assert out["status"] == "unavailable"

    def test_offline_fetcher_returns_unavailable(self):
        def _boom(url):
            raise OSError("no network")
        out = Edgar13FAdvisor(enabled=True, fetcher=_boom).recent_13f("1")
        assert out["status"] == "unavailable"
        assert "OSError" in out["reason"]

    def test_fixture_fetcher_returns_measured(self):
        payload = ('{"name": "Berkshire", "filings": {"recent": '
                   '{"form": ["13F-HR", "10-K"], '
                   '"filingDate": ["2026-08-14", "2026-03-01"], '
                   '"accessionNumber": ["0001", "0002"]}}}')
        out = Edgar13FAdvisor(enabled=True,
                              fetcher=lambda u: payload).recent_13f("1067983")
        assert out["status"] == "measured"
        assert out["count"] == 1
        assert out["recent_13f"][0]["form"] == "13F-HR"


class TestUnavailableInterfaces:
    def test_defi_unavailable(self):
        st = DEFI_INTERFACE.status()
        assert st["status"] == "unavailable"
        assert "rpc_endpoint" in st["requires"]

    def test_whale_unavailable(self):
        st = WHALE_TRACKER.analyze({})
        assert st["status"] == "unavailable"

    def test_ml_monitor_unavailable(self):
        assert ML_MODEL_MONITOR.status()["status"] == "unavailable"


class TestCSCReports:
    def test_pruning_and_ml_health_reports(self):
        from trading_bot.core.csc.controller import (
            CognitiveSystemController)
        CognitiveSystemController._instance = None
        csc = CognitiveSystemController()
        pr = csc.pruning_report()
        assert pr["status"] in ("measured", "unavailable")
        assert "electorate_states" in pr or pr["status"] == "unavailable"
        mh = csc.ml_health_report()
        assert mh["status"] == "measured"
        CognitiveSystemController._instance = None


class TestInnovativeDecisionAdvisory:
    def test_engine_emits_advisory_evidence(self):
        import inspect
        from trading_bot.core.csc.advisory import (
            _innovative_decision_service, _run_coro_sync)
        svc = _innovative_decision_service()
        out = None
        for i in range(30):
            ctx = {"symbol": "EURUSD", "close": 1.09 + i * 0.0005,
                   "price": 1.09 + i * 0.0005, "volume": 100.0,
                   "volatility": 0.01, "trend": "UP", "sentiment": 0.1}
            out = svc.analyze(ctx)
            if inspect.isawaitable(out):
                out = _run_coro_sync(out)
        assert out["capability_id"] == "innovative_decision_engine"
        ev = out["evidence"]
        assert ev["concepts_run"] == 110
        assert ev["contributing"] > 0
        assert 0.0 <= ev["consensus_level"] <= 1.0
        # evidence only — advisory strip leaves no authority
        assert out["advisory_only"] is True
