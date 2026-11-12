"""spec_extractor tests — honest-empty guarantee + template mapping."""

from trading_bot.core.csc.research.spec_extractor import extract_specs
from trading_bot.core.csc.research.method_spec import (
    FAMILIES, SpecError, compile_rule)


def test_empty_on_unrelated_text():
    assert extract_specs("a paper about baked goods and sourdough") == []
    assert extract_specs("") == []
    assert extract_specs(None) == []
    # observed live leak: software crash log with generic words
    assert extract_specs(
        "---- Minecraft Crash Report ---- Ticking entity "
        "java.lang.OutOfMemoryError: Java heap space") == []
    # 'momentum' in a climate abstract is not a tradeable claim
    assert extract_specs(
        "atmospheric momentum and volatility of storm systems "
        "in climate models") == []


def test_momentum_keywords_map():
    specs = extract_specs(
        "time series momentum with a 20-period lookback and 0.5% "
        "threshold on daily bars", provenance={"url": "u"})
    assert len(specs) == 1
    s = specs[0]
    assert s.family == "momentum"
    assert s.params["lookback"] == 20.0
    assert s.params["threshold_bps"] == 50.0  # 0.5% -> 50bps
    assert s.provenance["url"] == "u"


def test_meanrev_and_donchian_and_volmom():
    mr = extract_specs("bollinger band z-score 2.5 mean reversion")
    assert mr and mr[0].family == "meanrev"
    assert mr[0].params.get("z") == 2.5
    dc = extract_specs("20-period donchian channel breakout follow")
    assert dc and dc[0].family == "donchian"
    assert dc[0].params.get("channel") == 20.0
    vm = extract_specs("volatility regime switching momentum expansion")
    assert vm and vm[0].family == "vol_regime_momentum"


def test_specificity_order_volmom_before_momentum():
    # text mentions both 'volatility regime' and 'momentum' — the
    # more specific family must win
    specs = extract_specs("volatility regime momentum following")
    assert specs[0].family == "vol_regime_momentum"


def test_clamps_recorded_not_silent():
    specs = extract_specs("momentum with 500-period lookback")
    s = specs[0]
    # 500 > bound 60 -> clamped, and the clamp is in provenance
    assert s.params["lookback"] == 60.0
    assert "param_clamps" in s.provenance


def test_extracted_specs_compile():
    for text in ["20-period momentum trend following 0.3% threshold "
                 "on equity index futures",
                 "bollinger z-score mean reversion window 30",
                 "donchian breakout 55 channel",
                 "volatility expansion momentum regime"]:
        for s in extract_specs(text):
            compile_rule(s)  # must not raise — bounds enforced upstream


def test_no_free_code_path():
    # extractor can only emit allow-listed families — assert the
    # emitted set is a subset of FAMILIES by construction
    specs = extract_specs(
        "momentum mean reversion breakout volatility regime trend")
    assert specs
    assert all(s.family in FAMILIES for s in specs)
