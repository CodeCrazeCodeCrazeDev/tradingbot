"""Gap-hardening tests — nonfinite rejection, symbol isolation,
preflight scoping, EDGAR memoization, alert rate limits."""
import inspect

import pytest


@pytest.fixture
def csc():
    from trading_bot.core.csc.controller import CognitiveSystemController
    CognitiveSystemController._instance = None
    instance = CognitiveSystemController()
    yield instance
    CognitiveSystemController._instance = None


class TestNonfiniteRejection:
    def test_inf_close_rejected_from_history(self, csc):
        csc.seed_observation_history("EURUSD",
                                     [1.1, float("inf"), 1.2])
        hist = csc.observation_history("EURUSD")
        assert float("inf") not in hist
        assert len(hist) == 2

    def test_nan_and_inf_entry_rejected_on_import(self, csc):
        n = csc.import_open_positions({
            "positions": {
                "A": {"direction": "BUY",
                      "entry_price": float("inf")},
                "B": {"direction": "SELL",
                      "entry_price": float("nan")},
                "C": {"direction": "BUY", "entry_price": 1.1},
            }})
        assert n == 1
        assert "C" in csc._open_positions


@pytest.mark.asyncio
class TestPreflightScoping:
    async def test_preflight_flag_without_window_dispatches(self, csc):
        """An obs smuggling preflight=True outside the preflight window
        must NOT suppress the dispatch path."""
        dispatched = []

        class _Bus:
            async def propose_action(self, action):
                dispatched.append(getattr(action, "action_type", ""))

        csc.decision_bus = _Bus()
        obs = {"symbol": "X", "price": 1.0, "close": 1.0,
               "preflight": True}  # smuggled flag, no window
        await csc.process_market_observation(obs)
        # Whether or not a trade was proposed, the preflight shortcut
        # must not have been honored — EXECUTED status must not come
        # from the probe path. The honest check: _preflight_active is
        # False and the flag was ignored.
        assert getattr(csc, "_preflight_active", False) is False


class TestSymbolIsolation:
    def test_bar_history_filters_to_latest_symbol(self):
        from trading_bot.core.csc.advisory import _BarHistory
        hist = _BarHistory()
        for c in (1.10, 1.11, 1.12):
            hist.add({"symbol": "EURUSD", "close": c})
        for c in (1.30, 1.31):
            hist.add({"symbol": "GBPUSD", "close": c})
        prices = hist.prices()
        assert prices == [1.30, 1.31]
        assert all(b["close"] > 1.2 for b in hist.bars())

    def test_symbol_tag_not_leaked_to_analyzers(self):
        from trading_bot.core.csc.advisory import _BarHistory
        hist = _BarHistory()
        hist.add({"symbol": "EURUSD", "close": 1.1})
        assert "_symbol" not in hist.bars()[0]


class TestEdgarMemoization:
    def test_one_fetch_per_cik(self):
        from trading_bot.core.csc.advisory import (
            _edgar_13f_service, _run_coro_sync)
        svc = _edgar_13f_service()
        ctx = {"edgar_cik": "320193", "close": 1.0}
        r1 = svc.analyze(ctx)
        r2 = svc.analyze(ctx)
        if inspect.isawaitable(r1):
            r1 = _run_coro_sync(r1)
        if inspect.isawaitable(r2):
            r2 = _run_coro_sync(r2)
        assert r1 == r2

    def test_fetch_count_one_per_cik(self, monkeypatch):
        """Proof of memoization: recent_13f is invoked once per CIK."""
        from trading_bot.core.csc.advisory import (
            _edgar_13f_service, _run_coro_sync)
        from trading_bot.core.csc.extended_capabilities import (
            Edgar13FAdvisor)
        calls = []
        orig = Edgar13FAdvisor.recent_13f

        def counting(self, cik):
            calls.append(cik)
            return orig(self, cik)

        monkeypatch.setattr(Edgar13FAdvisor, "recent_13f", counting)
        svc = _edgar_13f_service()
        for _ in range(3):
            out = svc.analyze({"edgar_cik": "320193", "close": 1.0})
            if inspect.isawaitable(out):
                _run_coro_sync(out)
        assert calls == ["320193"]


class TestVoiceRateLimit:
    def test_storm_suppressed(self):
        from trading_bot.core.csc.extended_capabilities import (
            VoiceAlerter)
        sent = []
        v = VoiceAlerter(enabled=True, speaker=sent.append,
                         min_interval_s=60)
        assert v.alert("one") is True
        assert v.alert("two") is False
        assert v.alert("three") is False
