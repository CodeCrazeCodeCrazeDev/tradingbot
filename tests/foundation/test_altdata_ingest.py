"""Network-free tests for the alt-data ingest parsers and feature
logic (collect_macro / edge_features / dsc_candles). Real feeds are
never touched — every fixture is built inline."""

import struct
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.collect_macro import (  # noqa: E402
    _et_offset_hours, nfp_seed_events, parse_cot_rows,
    parse_ecb_csv, parse_ff_calendar, parse_fomc_page, parse_ics)
from scripts.dsc_candles import aggregate_ticks  # noqa: E402
from scripts.edge_features import (  # noqa: E402
    blackout_mask, _history_asof, _series_asof, _session_extremes)


# ---------- ET offset / calendar ----------

def test_et_offset_dst_boundary():
    # 2026 DST: Mar 8 .. Oct 31 inclusive; Nov 1 -> EST
    assert _et_offset_hours(date(2026, 7, 1)) == -4
    assert _et_offset_hours(date(2026, 1, 15)) == -5
    assert _et_offset_hours(date(2026, 3, 8)) == -4   # DST starts
    assert _et_offset_hours(date(2026, 3, 7)) == -5
    assert _et_offset_hours(date(2026, 11, 1)) == -5  # DST ends
    assert _et_offset_hours(date(2026, 10, 31)) == -4


def test_parse_ff_calendar_et_to_utc():
    xml = """<?xml version="1.0" encoding="windows-1252"?>
    <weeklyevents>
      <event><title>CPI m/m</title><country>USD</country>
        <date><![CDATA[07-15-2026]]></date>
        <time><![CDATA[8:30am]]></time>
        <impact><![CDATA[High]]></impact>
        <forecast><![CDATA[0.2%]]></forecast>
        <previous><![CDATA[0.1%]]></previous></event>
      <event><title>Bank Holiday</title><country>EUR</country>
        <date><![CDATA[07-15-2026]]></date>
        <time><![CDATA[All Day]]></time>
        <impact><![CDATA[Low]]></impact>
        <forecast /><previous /></event>
    </weeklyevents>"""
    evs = parse_ff_calendar(xml)
    assert len(evs) == 2
    cpi = evs[0]
    # July -> EDT (-4): 8:30 ET = 12:30 UTC
    assert cpi["ts_utc"] == "2026-07-15T12:30:00+00:00"
    assert cpi["all_day"] == 0 and cpi["impact"] == "High"
    hol = evs[1]
    assert hol["all_day"] == 1
    assert hol["ts_utc"] == "2026-07-15T00:00:00+00:00"


def test_parse_fomc_page():
    html = """
    <a id="1">2026 FOMC Meetings</a>
    <div class="fomc-meeting__month"><strong>January</strong></div>
    <div class="fomc-meeting__date">27-28</div>
    <strong>Minutes:</strong> (Released February 18, 2026)
    <div class="fomc-meeting__month"><strong>March</strong></div>
    <div class="fomc-meeting__date">17-18*</div>
    <strong>Minutes:</strong> (Released April 08, 2026)
    <div class="fomc-meeting__month"><strong>April</strong></div>
    <div class="fomc-meeting__date">30-May 1</div>
    """
    evs = parse_fomc_page(html)
    stmts = [e for e in evs if e["title"] == "FOMC statement"]
    mins = [e for e in evs if e["title"] == "FOMC minutes"]
    assert len(stmts) == 3 and len(mins) == 2
    # Jan 28 14:00 ET, winter EST (-5) -> 19:00 UTC
    assert stmts[0]["ts_utc"] == "2026-01-28T19:00:00+00:00"
    # month-spanning meeting: last day is MAY 1 not April 1
    assert stmts[2]["ts_utc"] == "2026-05-01T18:00:00+00:00"
    assert mins[0]["ts_utc"] == "2026-02-18T19:00:00+00:00"


def test_nfp_seed_first_friday():
    evs = nfp_seed_events(2026, 2026)
    assert len(evs) == 12
    # Jan 2026: first Friday = Jan 2; 8:30 EST -> 13:30 UTC
    assert evs[0]["ts_utc"] == "2026-01-02T13:30:00+00:00"
    assert evs[0]["src"] == "rule_seed:nfp_1st_friday"
    # Jul 2026: first Friday = Jul 3; EDT (-4) -> 12:30 UTC
    assert evs[6]["ts_utc"] == "2026-07-03T12:30:00+00:00"


def test_first_vintage_with_finds_release_day(monkeypatch):
    import scripts.collect_macro as cm
    # obs "2026-10-01" first appears in the vintage of 2026-11-12
    def fake(sid, d):
        if d >= date(2026, 11, 12):
            return [("2026-09-01", 1.0), ("2026-10-01", 2.0)]
        return [("2026-09-01", 1.0)]
    monkeypatch.setattr(cm, "_alfred_vintage", fake)
    d, _ = cm._first_vintage_with("X", "2026-10-01",
                                  date(2026, 11, 8),
                                  date(2026, 11, 22))
    assert d == date(2026, 11, 12)


def test_first_vintage_with_absent_is_none(monkeypatch):
    import scripts.collect_macro as cm
    # obs never appears inside the window -> None, not a false date
    monkeypatch.setattr(cm, "_alfred_vintage",
                        lambda sid, d: [("2026-09-01", 1.0)])
    d, _ = cm._first_vintage_with("X", "2026-10-01",
                                  date(2026, 11, 8),
                                  date(2026, 11, 22))
    assert d is None


def test_first_vintage_changed_detects_revision(monkeypatch):
    import scripts.collect_macro as cm
    # value at obs "2026-07-01" is revised upward on 2026-08-28
    def fake(sid, d):
        v = 3.1 if d >= date(2026, 8, 28) else 3.0
        return [("2026-07-01", v)]
    monkeypatch.setattr(cm, "_alfred_vintage", fake)
    d, _ = cm._first_vintage_changed(
        "X", "2026-07-01", 3.0,
        date(2026, 8, 10), date(2026, 9, 10))
    assert d == date(2026, 8, 28)


def test_parse_ics_variants():
    ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART;TZID=America/New_York:20260715T083000
SUMMARY:CPI m/m
END:VEVENT
BEGIN:VEVENT
DTSTART:20261105T140000Z
SUMMARY:FOMC statement
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20260801
SUMMARY:All-day marker
END:VEVENT
END:VCALENDAR"""
    evs = parse_ics(ics, "USD", "High")
    assert len(evs) == 3
    # July -> EDT (-4): 08:30 ET = 12:30 UTC
    assert evs[0]["ts_utc"] == "2026-07-15T12:30:00+00:00"
    assert evs[0]["all_day"] == 0
    assert evs[1]["ts_utc"] == "2026-11-05T14:00:00+00:00"
    assert evs[2]["all_day"] == 1


# ---------- COT ----------

def _tff_row(market, oi, d_long, d_short, am_long, am_short,
             lm_long, lm_short, rdate="2026-10-28"):
    return {
        "Market_and_Exchange_Names": market,
        "Report_Date_as_YYYY-MM-DD": rdate,
        "Open_Interest_ALL": str(oi),
        "Dealer_Positions_Long_ALL": str(d_long),
        "Dealer_Positions_Short_ALL": str(d_short),
        "Asset_Mgr_Positions_Long_ALL": str(am_long),
        "Asset_Mgr_Positions_Short_ALL": str(am_short),
        "Lev_Money_Positions_Long_ALL": str(lm_long),
        "Lev_Money_Positions_Short_ALL": str(lm_short),
    }


def test_parse_cot_tff_managed_money():
    rows = [_tff_row("EURO FX - CHICAGO MERCANTILE EXCHANGE", 1000,
                     100, 200, 300, 100, 200, 50),
            _tff_row("UNRELATED MARKET X", 10, 1, 1, 1, 1, 1, 1)]
    recs = parse_cot_rows(rows, {"EURO FX": "EURUSD"}, "tff")
    cats = {r[3]: r for r in recs}
    assert "managed_money" in cats and "dealer" in cats
    mm = cats["managed_money"]
    assert mm[1] == "EURUSD"
    assert mm[4] == 500 and mm[5] == 150      # am+lev longs/shorts
    assert mm[6] == 350                       # net
    assert mm[7] == pytest.approx(35.0)       # net % OI
    # publish lag: Tuesday report -> Friday usable
    assert mm[9][:10] == "2026-10-31"


def test_parse_cot_disagg_gold():
    row = {"Market_and_Exchange_Names":
           "GOLD - COMMODITY EXCHANGE INC.",
           "As_of_Date_In_Form_YYMMDD": "261028",
           "Open_Interest_ALL": "2000",
           "M_Money_Positions_Long_ALL": "800",
           "M_Money_Positions_Short_ALL": "300",
           "Prod_Merc_Positions_Long_ALL": "100",
           "Prod_Merc_Positions_Short_ALL": "400",
           "Swap_Positions_Long_All": "50",
           "Swap_Positions_Short_All": "60"}
    recs = parse_cot_rows([row],
                          {"GOLD - COMMODITY EXCHANGE INC": "XAUUSD"},
                          "disagg")
    cats = {r[3]: r for r in recs}
    assert cats["managed_money"][6] == 500
    assert cats["prod_merc"][6] == -300
    assert cats["swap"][6] == -10
    # YYMMDD fallback date
    assert cats["managed_money"][2] == "2026-10-28"


# ---------- ECB csvdata ----------

def test_parse_ecb_csv():
    text = ("KEY,TIME_PERIOD,OBS_VALUE\n"
            "EXR.D.USD.EUR.SP00.A,2026-11-05,1.1224\n"
            "EXR.D.USD.EUR.SP00.A,2026-11-06,1.1165\n")
    rows = parse_ecb_csv(text, "usd_per_eur_ecb")
    assert rows == [("2026-11-05", 1.1224), ("2026-11-06", 1.1165)]


# ---------- .bi5 tick aggregation ----------

def _tick(ms, ask_pts, bid_pts, av=1.0, bv=1.0):
    return struct.pack(">IIIff", ms, ask_pts, bid_pts, av, bv)


def test_aggregate_ticks_candles_and_spread():
    # 4 ticks inside one M15 bucket + 1 in the next; EURUSD 1e-5 scale
    data = (_tick(0, 110010, 110000) + _tick(60000, 110020, 110010) +
            _tick(120000, 109990, 109980) + _tick(180000, 110030, 110020) +
            _tick(900000, 110040, 110030))
    buckets = {}
    aggregate_ticks(data, 5, 1e-5, 0, 15, buckets)
    assert len(buckets) == 2
    b0 = buckets[0]
    assert b0.o == pytest.approx(1.10005)
    assert b0.h == pytest.approx(1.10025)
    assert b0.l == pytest.approx(1.09985)
    assert b0.c == pytest.approx(1.10025)
    assert b0.n == 4
    # all ticks had a 10-point spread = 1 pip ~ 0.91 bps
    assert all(s == pytest.approx(10e-5 / 1.1 * 1e4, rel=0.02)
               for s in b0.spreads)


# ---------- feature join / blackout / session ----------

def test_series_asof_point_in_time():
    pts = [(1000.0, 4.0), (2000.0, 4.2), (3000.0, 4.4)]
    f = _series_asof(pts)
    assert f(500) is None            # nothing published yet
    assert f(1500) == 4.0
    assert f(2000) == 4.2            # inclusive boundary
    assert f(9999) == 4.4


def test_blackout_mask():
    ts = [0.0, 100.0, 1000.0, 2000.0]
    events = [970.0]
    mask = blackout_mask(ts, events, pad_s=60)
    assert mask == [False, False, True, False]


def test_session_extremes_completed_range():
    # M15 bars 06:45..11:15 one day; session = 07:00-11:00
    dts = [datetime(2026, 11, 6, h, m)
           for h, m in [(6, 45), (7, 0), (7, 15), (10, 45),
                        (11, 0), (11, 15)]]
    # tz-naive fine here — only .hour/.date() are used
    highs = [1.10, 1.11, 1.12, 1.115, 1.12, 1.13]
    lows = [1.09, 1.095, 1.10, 1.10, 1.11, 1.12]
    keys, sh, sl = _session_extremes(dts, highs, lows)
    # pre-session bar sees nothing
    assert sh[0] is None and sl[0] is None
    # during session, extreme builds from completed bars only
    assert sh[1] is None                       # first session bar
    assert sh[2] == 1.11                       # sees 07:00 bar
    assert sh[4] == 1.12 and sl[4] == 1.095    # full range by 11:00
    assert sh[5] == 1.12                       # 11:15 still sees it
