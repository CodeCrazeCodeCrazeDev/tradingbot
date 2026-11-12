#!/usr/bin/env python
"""Keyless macro / positioning / calendar ingestion -> macro_data.db.

Every source below is public and needs no credentials:

- FRED ``fredgraph.csv`` (no API key): daily UST yields (DGS2/DGS10),
  SOFR, and the Fed noon FX reference rates (DEXUSEU/DEXUSUK/DEXJPUS).
  Covers the "Treasury rates" item from the source list — the direct
  treasury.gov CSV endpoint is unreliable, DGS* is the same data.
- ECB SDW ``data-api.ecb.europa.eu`` csvdata: daily EUR reference FX
  (independent venue check vs MT5/Dukascopy) and the euro-area AAA
  10y par yield (rate differential vs DGS10).
- CFTC Commitments of Traders annual zips: Traders-in-Financial-Futures
  (FX futures -> managed-money positioning) + disaggregated (gold).
  Positions are as of Tuesday, published Friday -> ``published_at``
  is set to report_date + 3 days so backtests cannot peek.
- faireconomy ``ff_calendar_thisweek.xml``: weekly high/low/medium
  impact scheduled events. Times are US Eastern -> converted to UTC
  with explicit DST rules. Honest boundary: this is a third-party
  mirror of a retail calendar (not BLS/BEA primary), weekly horizon
  only; treat as the "scheduled release" blackout layer, not as
  consensus data for surprise studies.

Nothing is synthesized: failed sources are reported, never faked.
Re-runs are idempotent (INSERT OR REPLACE on natural keys).

Usage:
    python scripts/collect_macro.py                       # all sources
    python scripts/collect_macro.py --sources fred,ecb
    python scripts/collect_macro.py --sources cot --cot-years 3
    python scripts/collect_macro.py --sources calendar --weeks-back 8
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "macro_data.db"

_UA = {"User-Agent": "alphaalgo-macro-collector/1.0"}
_FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv"
_ECB = "https://data-api.ecb.europa.eu/service/data"
_CFTC = "https://www.cftc.gov/files/dea/history"
_FF_XML = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"

# series_id -> (table series name, units note)
FRED_SERIES = {
    "DGS2": "us_ust_2y",
    "DGS10": "us_ust_10y",
    "SOFR": "us_sofr",
    "DEXUSEU": "usd_per_eur_fed",
    "DEXUSUK": "usd_per_gbp_fed",
    "DEXJPUS": "jpy_per_usd_fed",
}
# ECB SDW key -> series name. EXR = daily reference FX; YC = euro-area
# AAA par-yield curve spot rate (daily).
ECB_SERIES = {
    "EXR/D.USD.EUR.SP00.A": "usd_per_eur_ecb",
    "EXR/D.GBP.EUR.SP00.A": "gbp_per_eur_ecb",
    "EXR/D.JPY.EUR.SP00.A": "jpy_per_eur_ecb",
    "YC/B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y": "eu_aaa_10y",
}
# COT market-name prefix -> our symbol. TFF (futures in financials).
COT_FX_MARKETS = {
    "EURO FX": "EURUSD",
    "BRITISH POUND": "GBPUSD",
    "JAPANESE YEN": "USDJPY",
    "AUSTRALIAN DOLLAR": "AUDUSD",
    "CANADIAN DOLLAR": "USDCAD",
    "SWISS FRANC": "USDCHF",
}
COT_DISAGG_MARKETS = {
    "GOLD - COMMODITY EXCHANGE INC": "XAUUSD",
}
# COT positions are measured Tuesday, published Friday 15:30 ET.
COT_PUBLISH_LAG_DAYS = 3

# Primary-source release calendars (ICS feeds). These are the "real"
# calendars the source list points at — official agency schedules.
# Honest status: bls.ics exists but the host bot-blocks some clients;
# failures are reported in the run report, never faked.
ICS_FEEDS = {
    "bls": {"url": "https://www.bls.gov/schedule/news_release/"
                   "bls.ics",
            "currency": "USD", "impact": "High"},
    "ecb_governing_council": {
        "url": "https://www.ecb.europa.eu/press/calendars/mgcgc/"
               "html/calendar.en.ics",
        "currency": "EUR", "impact": "High"},
}
_FOMC_PAGE = ("https://www.federalreserve.gov/monetarypolicy/"
             "fomccalendars.htm")
_ALFRED = "https://alfred.stlouisfed.org/graph/alfredgraph.csv"

# Series whose ALFRED vintage-appearance dates ARE the official
# release dates — keyless release-calendar discovery. win = day range
# of the FOLLOWING month (monthly) searched for first appearance;
# quarterly_revised also hunts subsequent value revisions (2nd/3rd
# estimates). hhmm = the known ET release time for the print.
RELEASE_SERIES = {
    "PAYEMS": {"title": "Employment Situation", "kind": "monthly",
               "win": (1, 10), "hhmm": (8, 30)},
    "CPIAUCSL": {"title": "US CPI", "kind": "monthly",
                 "win": (8, 22), "hhmm": (8, 30)},
    "PPIACO": {"title": "US PPI", "kind": "monthly",
               "win": (8, 25), "hhmm": (8, 30)},
    "GDP": {"title": "US GDP estimate", "kind": "quarterly_revised",
            "win": (20, 50), "hhmm": (8, 30)},
}
_MONTHS = {"January": 1, "February": 2, "March": 3, "April": 4,
           "May": 5, "June": 6, "July": 7, "August": 8,
           "September": 9, "October": 10, "November": 11,
           "December": 12}


def init_db(p: Path) -> sqlite3.Connection:
    con = sqlite3.connect(p)
    con.execute(
        "CREATE TABLE IF NOT EXISTS macro_series ("
        "series TEXT, date TEXT, value REAL, source TEXT, "
        "published_at TEXT, "
        "PRIMARY KEY (series, date))")
    con.execute(
        "CREATE TABLE IF NOT EXISTS cot_positions ("
        "market TEXT, symbol TEXT, report_date TEXT, category TEXT, "
        "long_pos REAL, short_pos REAL, net REAL, net_pct_oi REAL, "
        "open_interest REAL, published_at TEXT, source TEXT, "
        "PRIMARY KEY (market, report_date, category))")
    con.execute(
        "CREATE TABLE IF NOT EXISTS news_events ("
        "ts_utc TEXT, title TEXT, currency TEXT, impact TEXT, "
        "forecast TEXT, previous TEXT, all_day INTEGER, source TEXT, "
        "PRIMARY KEY (ts_utc, title, currency))")
    con.execute(
        "CREATE INDEX IF NOT EXISTS ix_news_ts ON news_events(ts_utc)")
    con.commit()
    return con


def _get(url: str, timeout: int = 60, retries: int = 3) -> bytes | None:
    """urllib first; on repeated failure fall back to curl.exe
    (Schannel TLS — some hosts, e.g. fred.stlouisfed.org, stall
    python/OpenSSL reads but answer curl fine)."""
    for a in range(retries):
        try:
            req = urllib.request.Request(url, headers=_UA)
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception:  # noqa: BLE001
            time.sleep(2 * (a + 1))
    return _get_curl(url, timeout)


def _get_curl(url: str, timeout: int = 60) -> bytes | None:
    """curl subprocess with the DEFAULT curl UA. Prefers
    Git-for-Windows' mingw curl — the System32 Schannel curl (like
    python/OpenSSL) gets hung up on by some TLS edges, and Akamai
    fronting fred.stlouisfed.org drops/stalls any custom -A header
    (observed 2026-11-09: default curl UA answers in <1s, custom UA
    times out or resets)."""
    candidates = [
        r"C:\Program Files\Git\mingw64\bin\curl.exe",
        r"C:\Program Files\Git\usr\bin\curl.exe",
        shutil.which("curl") or "",
        shutil.which("curl.exe") or "",
    ]
    curl = next((c for c in candidates
                 if c and Path(c).exists()), None)
    if not curl:
        return None
    try:
        out = subprocess.run(
            [curl, "-sL", "--max-time", str(timeout), url],
            capture_output=True, timeout=timeout + 15)
        if out.returncode == 0 and out.stdout:
            return out.stdout
    except Exception:  # noqa: BLE001
        pass
    return None


# -----------------------------------------------------------------
# FRED (fredgraph.csv — the public CSV endpoint, no key needed)

def fetch_fred(con: sqlite3.Connection, years: int) -> dict:
    out = {}
    cosd = (date.today() - timedelta(days=366 * years)).isoformat()
    for sid, name in FRED_SERIES.items():
        # fred.stlouisfed.org stalls python/TLS reads on some hosts —
        # short urllib probe then straight to the curl fallback
        raw = (_get(f"{_FRED}?id={sid}&cosd={cosd}",
                    timeout=15, retries=1)
               or _get_curl(f"{_FRED}?id={sid}&cosd={cosd}"))
        if raw is None:
            out[name] = {"error": "fetch failed"}
            continue
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"))))
        n = 0
        for r in rows:
            v = (r.get(sid) or "").strip()
            if not v or v == ".":
                continue
            try:
                val = float(v)
            except ValueError:
                continue
            con.execute(
                "INSERT OR REPLACE INTO macro_series "
                "(series, date, value, source, published_at) "
                "VALUES (?,?,?,?,?)",
                (name, r["observation_date"], val, f"fred:{sid}",
                 # daily FRED series publish next business day; +1d is
                 # the conservative usable-at timestamp
                 f"{r['observation_date']}T23:59:59+00:00"))
            n += 1
        con.commit()
        out[name] = {"rows": n}
    return out


# -----------------------------------------------------------------
# ECB SDW csvdata

def parse_ecb_csv(text: str, series_name: str) -> list[tuple[str, float]]:
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        d, v = r.get("TIME_PERIOD"), r.get("OBS_VALUE")
        if not d or not v:
            continue
        try:
            rows.append((d, float(v)))
        except ValueError:
            continue
    return rows


def fetch_ecb(con: sqlite3.Connection, years: int) -> dict:
    out = {}
    start = (date.today() - timedelta(days=366 * years)).isoformat()
    for key, name in ECB_SERIES.items():
        url = (f"{_ECB}/{key}?startPeriod={start}&format=csvdata")
        raw = _get(url)
        if raw is None:
            out[name] = {"error": "fetch failed"}
            continue
        rows = parse_ecb_csv(raw.decode("utf-8"), name)
        for d, v in rows:
            # ECB reference rates publish ~16:00 CET same day; +1d is
            # the conservative usable-at bound
            con.execute(
                "INSERT OR REPLACE INTO macro_series "
                "(series, date, value, source, published_at) "
                "VALUES (?,?,?,?,?)",
                (name, d, v, f"ecb:{key}",
                 f"{d}T23:59:59+00:00"))
        con.commit()
        out[name] = {"rows": len(rows)}
    return out


# -----------------------------------------------------------------
# CFTC Commitments of Traders (annual zips)

def _cot_col(row: dict, *names: str) -> str | None:
    """Case-insensitive column lookup (CFTC header casing varies:
    'Swap_Positions_Long_All' vs '..._ALL')."""
    lower = {k.strip().lower(): v for k, v in row.items()}
    for n in names:
        if n.lower() in lower:
            return lower[n.lower()]
    return None


def _num(s) -> float:
    if s is None:
        return 0.0
    s = str(s).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def _cot_date(row: dict) -> str | None:
    d = _cot_col(row, "Report_Date_as_YYYY-MM-DD")
    if d:
        return d[:10]
    y = _cot_col(row, "As_of_Date_In_Form_YYMMDD")
    if y and len(y.strip()) == 6:
        yy, mm, dd = int(y[:2]), y[2:4], y[4:6]
        return f"{2000 + yy:04d}-{mm}-{dd}"
    return None


def parse_cot_rows(rows: list[dict], markets: dict,
                   style: str) -> list[tuple]:
    """Extract positioning rows. style='tff' uses Asset_Mgr+Lev_Money
    (the TFF managed-money aggregate); style='disagg' uses M_Money."""
    out = []
    for r in rows:
        name = (_cot_col(r, "Market_and_Exchange_Names") or "").strip()
        # cross-rate contracts ("EURO FX/BRITISH POUND XRATE") are not
        # the pair's own positioning — skip them
        if "XRATE" in name.upper() or "/" in name:
            continue
        symbol = None
        for prefix, sym in markets.items():
            if name.upper().startswith(prefix.upper()):
                symbol = sym
                break
        if symbol is None:
            continue
        rdate = _cot_date(r)
        if not rdate:
            continue
        oi = _num(_cot_col(r, "Open_Interest_ALL"))
        pub = (datetime.fromisoformat(rdate) +
               timedelta(days=COT_PUBLISH_LAG_DAYS)).isoformat()
        cats = {}
        if style == "tff":
            for cat, key in (("dealer", "Dealer"),
                             ("asset_mgr", "Asset_Mgr"),
                             ("lev_money", "Lev_Money")):
                lo = _num(_cot_col(r, f"{key}_Positions_Long_ALL"))
                sh = _num(_cot_col(r, f"{key}_Positions_Short_ALL"))
                cats[cat] = (lo, sh)
            am_l, am_s = cats["asset_mgr"]
            lm_l, lm_s = cats["lev_money"]
            cats["managed_money"] = (am_l + lm_l, am_s + lm_s)
        else:  # disaggregated
            for cat, key in (("managed_money", "M_Money"),
                             ("prod_merc", "Prod_Merc"),
                             ("swap", "Swap")):
                lo = _num(_cot_col(r, f"{key}_Positions_Long_ALL",
                                   f"{key}_Positions_Long_All"))
                sh = _num(_cot_col(r, f"{key}_Positions_Short_ALL",
                                   f"{key}_Positions_Short_All"))
                cats[cat] = (lo, sh)
        for cat, (lo, sh) in cats.items():
            net = lo - sh
            out.append((name, symbol, rdate, cat, lo, sh, net,
                        (net / oi * 100.0) if oi else None, oi,
                        pub, f"cftc_{style}"))
    return out


def fetch_cot(con: sqlite3.Connection, years: int) -> dict:
    out = {"tff": 0, "disagg": 0, "files": []}
    now = date.today().year
    for y in range(now - years + 1, now + 1):
        for style, fname, markets in (
                ("tff", f"fut_fin_txt_{y}.zip", COT_FX_MARKETS),
                ("disagg", f"fut_disagg_txt_{y}.zip",
                 COT_DISAGG_MARKETS)):
            raw = _get(f"{_CFTC}/{fname}")
            if raw is None:
                out["files"].append({fname: "fetch failed"})
                continue
            try:
                zf = zipfile.ZipFile(io.BytesIO(raw))
                member = next(n for n in zf.namelist()
                              if n.lower().endswith((".txt", ".csv")))
                text = zf.read(member).decode("latin-1")
            except Exception as exc:  # noqa: BLE001
                out["files"].append({fname: f"unzip:{exc}"})
                continue
            rows = list(csv.DictReader(io.StringIO(text)))
            recs = parse_cot_rows(rows, markets, style)
            for rec in recs:
                con.execute(
                    "INSERT OR REPLACE INTO cot_positions "
                    "(market, symbol, report_date, category, long_pos,"
                    " short_pos, net, net_pct_oi, open_interest,"
                    " published_at, source) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)", rec)
            con.commit()
            out[style] += len(recs)
            out["files"].append({fname: f"{len(recs)} rows"})
    return out


# -----------------------------------------------------------------
# Economic calendar (faireconomy mirror of the FF weekly calendar)

def _et_offset_hours(d: date) -> int:
    """US Eastern UTC offset in hours. DST: 2nd Sunday March ->
    1st Sunday November (post-2007 rules). -4 in DST, -5 otherwise."""
    def nth_sunday(year, month, n):
        first = date(year, month, 1)
        return first + timedelta(
            days=(6 - first.weekday()) % 7 + 7 * (n - 1))
    dst_start = nth_sunday(d.year, 3, 2)
    dst_end = nth_sunday(d.year, 11, 1)
    return -4 if dst_start <= d < dst_end else -5


def parse_ff_calendar(xml_text: str) -> list[dict]:
    """XML -> event dicts. Times are US Eastern; converted to UTC.
    Non-timed entries ('All Day', 'Tentative', 'Day N') get all_day=1
    with ts_utc at 00:00 UTC."""
    evs = []
    root = ET.fromstring(xml_text)
    for e in root.iter("event"):
        def _t(tag):
            el = e.find(tag)
            return (el.text or "").strip() if el is not None else ""
        title, cur = _t("title"), _t("country")
        impact = _t("impact")
        ds, ts = _t("date"), _t("time")
        if not (title and cur and ds):
            continue
        try:
            d = datetime.strptime(ds, "%m-%d-%Y").date()
        except ValueError:
            continue
        ts_utc, all_day = None, 1
        t = ts.lower().replace(" ", "")
        try:
            hhmm = datetime.strptime(t, "%I:%M%p")
            # ET -> UTC = ET - offset (offset is negative)
            off = _et_offset_hours(d)
            ts_utc = (datetime.combine(d, hhmm.time()) +
                      timedelta(hours=-off)).strftime(
                          "%Y-%m-%dT%H:%M:%S+00:00")
            all_day = 0
        except ValueError:
            ts_utc = f"{d.isoformat()}T00:00:00+00:00"
        evs.append({"ts_utc": ts_utc, "title": title, "currency": cur,
                    "impact": impact, "forecast": _t("forecast"),
                    "previous": _t("previous"), "all_day": all_day})
    return evs


def _unfold_ics(text: str) -> list[str]:
    """RFC 5545 line unfolding: continuation lines start with space
    or tab."""
    lines = []
    for ln in text.replace("\r\n", "\n").split("\n"):
        if ln.startswith((" ", "\t")) and lines:
            lines[-1] += ln[1:]
        else:
            lines.append(ln)
    return lines


def parse_ics(text: str, currency: str, impact: str) -> list[dict]:
    """Minimal VEVENT parser: DTSTART (UTC 'Z', TZID=America/New_York,
    or date-only -> all_day) + SUMMARY -> news_events dicts."""
    evs, cur = [], None
    for ln in _unfold_ics(text):
        if ln == "BEGIN:VEVENT":
            cur = {}
        elif ln == "END:VEVENT":
            if cur and cur.get("ts_utc"):
                evs.append({"ts_utc": cur["ts_utc"],
                            "title": cur.get("title", ""),
                            "currency": currency, "impact": impact,
                            "forecast": "", "previous": "",
                            "all_day": cur.get("all_day", 0)})
            cur = None
        elif cur is not None:
            if ln.startswith("SUMMARY"):
                cur["title"] = ln.split(":", 1)[1].strip()
            elif ln.startswith("DTSTART"):
                prop, _, val = ln.partition(":")
                val = val.strip()
                if "VALUE=DATE" in prop or (
                        len(val) == 8 and val.isdigit()):
                    d = datetime.strptime(val, "%Y%m%d").date()
                    cur["ts_utc"] = (f"{d.isoformat()}"
                                     "T00:00:00+00:00")
                    cur["all_day"] = 1
                else:
                    naive = datetime.strptime(
                        val.rstrip("Z"), "%Y%m%dT%H%M%S")
                    if val.endswith("Z"):
                        off = 0
                    elif "America/New_York" in prop:
                        off = _et_offset_hours(naive.date())
                    else:   # unknown TZID — record as UTC and note it
                        off = 0
                        cur.setdefault("title_suffix",
                                       f"[tz={prop}]")
                    dt = naive + timedelta(hours=-off)
                    cur["ts_utc"] = dt.strftime(
                        "%Y-%m-%dT%H:%M:%S+00:00")
                    cur["all_day"] = 0
    return evs


def fetch_ics(con: sqlite3.Connection) -> dict:
    out = {}
    for name, cfg in ICS_FEEDS.items():
        raw = _get(cfg["url"], timeout=30)
        if raw is None:
            out[name] = "fetch failed"
            continue
        if b"BEGIN:VCALENDAR" not in raw:
            out[name] = "not a calendar response (blocked/moved)"
            continue
        try:
            evs = parse_ics(raw.decode("utf-8", "replace"),
                            cfg["currency"], cfg["impact"])
        except Exception as exc:  # noqa: BLE001
            out[name] = f"parse:{exc}"
            continue
        for ev in evs:
            title = ev["title"] + ev.get("title_suffix", "")
            con.execute(
                "INSERT OR REPLACE INTO news_events "
                "(ts_utc, title, currency, impact, forecast, "
                "previous, all_day, source) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (ev["ts_utc"], title, ev["currency"], ev["impact"],
                 "", "", ev["all_day"], f"ics:{name}"))
        con.commit()
        out[name] = len(evs)
    return out


def parse_fomc_page(html: str) -> list[dict]:
    """fomccalendars.htm -> event dicts. Each meeting row carries a
    month name and a day range ('27-28', '17-18*', '30-1', or the
    month-spanning '29-30' style). The decision drops at 14:00 ET on
    the LAST meeting day; minutes release is also 14:00 ET on the
    recorded release date."""
    evs = []

    def _et_dt(y, m, d, hh, mm):
        dt0 = datetime(y, m, d, hh, mm)
        off = _et_offset_hours(dt0.date())
        return (dt0 + timedelta(hours=-off)).strftime(
            "%Y-%m-%dT%H:%M:%S+00:00")

    for yr_m in re.finditer(
            r'<a id="\d+">(\d{4}) FOMC Meetings</a>(.*?)(?=<a id="\d+">\d{4} FOMC|$)',
            html, re.S):
        year = int(yr_m.group(1))
        for row in re.finditer(
                r'fomc-meeting__month[^>]*><strong>(\w+)</strong>.*?'
                r'fomc-meeting__date[^>]*>([^<]+)</div>(.*?)(?=fomc-meeting__month|$)',
                yr_m.group(2), re.S):
            mon, rng, body = row.groups()
            m = _MONTHS.get(mon)
            if not m:
                continue
            rng = rng.strip()
            mm = re.match(r'(\d{1,2})\s*-\s*(?:(\w+)\s+)?(\d{1,2})', rng)
            if not mm:
                continue
            # month-spanning meetings ("30-May 1") name the last
            # day's month explicitly
            m_last = _MONTHS.get(mm.group(2), m) if mm.group(2) else m
            d_last = int(mm.group(3))
            try:
                ts = _et_dt(year, m_last, d_last, 14, 0)
            except ValueError:
                continue
            evs.append({"ts_utc": ts, "title": "FOMC statement",
                        "currency": "USD", "impact": "High",
                        "all_day": 0})
            rel = re.search(
                r'Released (\w+) (\d{1,2}), (\d{4})', body)
            if rel and rel.group(1) in _MONTHS:
                evs.append({
                    "ts_utc": _et_dt(int(rel.group(3)),
                                     _MONTHS[rel.group(1)],
                                     int(rel.group(2)), 14, 0),
                    "title": "FOMC minutes", "currency": "USD",
                    "impact": "Medium", "all_day": 0})
    return evs


def nfp_seed_events(year0: int, year1: int) -> list[dict]:
    """Employment Situation (NFP) — published first Friday, 08:30 ET.
    RULE-DERIVED seed, source='rule_seed:nfp_1st_friday': the schedule
    is the documented standing rule, not a scraped actual; rare
    holiday shifts (July 4th etc.) can be off by one week."""
    evs = []
    for y in range(year0, year1 + 1):
        for mo in range(1, 13):
            d = date(y, mo, 1)
            d += timedelta(days=(4 - d.weekday()) % 7)  # first Friday
            dt0 = datetime(y, mo, d.day, 8, 30)
            off = _et_offset_hours(d)
            ts = (dt0 + timedelta(hours=-off)).strftime(
                "%Y-%m-%dT%H:%M:%S+00:00")
            evs.append({"ts_utc": ts,
                        "title": "Employment Situation (NFP)",
                        "currency": "USD", "impact": "High",
                        "all_day": 0,
                        "src": "rule_seed:nfp_1st_friday"})
    return evs


def _alfred_vintage(sid: str, d: date):
    """Rows (obs_date, value) of `sid` as known on vintage day D.
    Uses the curl path — stlouisfed.org stalls python TLS reads."""
    raw = _get_curl(f"{_ALFRED}?id={sid}&vintage_date={d.isoformat()}",
                    timeout=30)
    if raw is None:
        return None
    rows = []
    for r in csv.DictReader(io.StringIO(raw.decode("utf-8"))):
        for k, v in r.items():
            if k == "observation_date" or not v or v == ".":
                continue
            try:
                rows.append((r["observation_date"], float(v)))
            except ValueError:
                pass
    return rows


def _last_obs(rows):
    return max((d for d, _ in rows), default=None)


def _obs_value(rows, obs_date):
    for d, v in rows:
        if d == obs_date:
            return v
    return None


def _first_vintage_with(sid: str, obs_date: str, lo: date,
                        hi: date):
    """Binary search the first calendar day in [lo,hi] whose ALFRED
    vintage contains `obs_date`. Returns (day, requests_made)."""
    n_req = 0
    while (hi - lo).days > 1:
        mid = lo + timedelta(days=(hi - lo).days // 2)
        rows = _alfred_vintage(sid, mid)
        n_req += 1
        if rows is None:
            return None, n_req
        if _last_obs(rows) and _last_obs(rows) >= obs_date:
            hi = mid
        else:
            lo = mid
    # verify at hi — an obs absent through the whole window must NOT
    # be recorded with hi as its release date
    rows = _alfred_vintage(sid, hi)
    n_req += 1
    if rows is None:
        return None, n_req
    return (hi if (_last_obs(rows) or "") >= obs_date
            else None), n_req


def _first_vintage_changed(sid: str, obs_date: str, old_val: float,
                           lo: date, hi: date):
    """First day in [lo,hi] where the vintage's value at obs_date
    differs from old_val — i.e., a revision release (2nd/3rd GDP
    estimates)."""
    n_req = 0
    while (hi - lo).days > 1:
        mid = lo + timedelta(days=(hi - lo).days // 2)
        rows = _alfred_vintage(sid, mid)
        n_req += 1
        if rows is None:
            return None, n_req
        v = _obs_value(rows, obs_date)
        if v is not None and v != old_val:
            hi = mid
        else:
            lo = mid
    rows = _alfred_vintage(sid, hi)
    n_req += 1
    if rows is None:
        return None, n_req
    v = _obs_value(rows, obs_date)
    return (hi if (v is not None and v != old_val) else None), n_req


def _add_month(d: date) -> date:
    return (d.replace(day=28) + timedelta(days=7)).replace(day=1)


def fetch_release_dates(con: sqlite3.Connection, lookback: int,
                        series_ids=None) -> dict:
    """Discover real release dates from ALFRED vintage appearances.
    ~4-6 requests per release — bounded by --release-lookback."""
    out = {}
    for sid, cfg in (series_ids or RELEASE_SERIES).items():
        latest = _alfred_vintage(sid, date.today())
        if latest is None:
            out[sid] = "fetch failed"
            continue
        obs_list = sorted({d for d, _ in latest}, reverse=True)
        # quarterly obs already stride 3 months; lookback counts
        # periods — each yields up to 3 releases (adv/2nd/3rd est.)
        n_target = (lookback if cfg["kind"] == "monthly"
                    else max(1, lookback // 3))
        targets = obs_list[:n_target]
        found, reqs = [], 0
        for obs in targets:
            y, m, _ = int(obs[:4]), int(obs[5:7]), 1
            next_m = _add_month(date(y, m, 1))
            if cfg["kind"] == "monthly":
                lo = next_m + timedelta(days=cfg["win"][0] - 1)
                hi = next_m + timedelta(days=cfg["win"][1])
            else:  # quarterly: quarter ends obs_start+3mo-1d;
                # advance estimate ~+20..50 days after quarter end
                end = (_add_month(_add_month(
                    _add_month(date(y, m, 1)))) - timedelta(days=1))
                lo = end + timedelta(days=cfg["win"][0])
                hi = end + timedelta(days=cfg["win"][1])
            d0, r = _first_vintage_with(sid, obs, lo, hi)
            reqs += r
            if d0 is None:
                continue
            releases = [d0]
            if cfg["kind"] == "quarterly_revised":
                rows0 = _alfred_vintage(sid, d0)
                reqs += 1
                v_prev = _obs_value(rows0 or [], obs)
                lo2, lim = d0 + timedelta(days=1), d0 + timedelta(days=95)
                while v_prev is not None and lo2 < lim:
                    dchg, r = _first_vintage_changed(
                        sid, obs, v_prev, lo2, min(lo2 + timedelta(days=34), lim))
                    reqs += r
                    if dchg is None:
                        break
                    releases.append(dchg)
                    vr = _alfred_vintage(sid, dchg)
                    reqs += 1
                    v_prev = _obs_value(vr or [], obs)
                    lo2 = dchg + timedelta(days=1)
            hh, mm = cfg["hhmm"]
            for d in releases:
                dt0 = datetime(d.year, d.month, d.day, hh, mm)
                off = _et_offset_hours(d)
                ts = (dt0 + timedelta(hours=-off)).strftime(
                    "%Y-%m-%dT%H:%M:%S+00:00")
                con.execute(
                    "INSERT OR REPLACE INTO news_events "
                    "(ts_utc, title, currency, impact, forecast, "
                    "previous, all_day, source) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (ts, cfg["title"], "USD", "High", "", "", 0,
                     f"alfred_vintage:{sid}"))
                found.append(d.isoformat())
        con.commit()
        out[sid] = {"releases": len(found), "requests": reqs,
                    "dates": sorted(found)}
    return out


def fetch_official_calendars(con: sqlite3.Connection,
                             year0: int, year1: int) -> dict:
    out = {}
    raw = _get(_FOMC_PAGE, timeout=30)
    if raw is None:
        out["fomc"] = "fetch failed"
    else:
        evs = parse_fomc_page(raw.decode("utf-8", "replace"))
        for ev in evs:
            con.execute(
                "INSERT OR REPLACE INTO news_events "
                "(ts_utc, title, currency, impact, forecast, "
                "previous, all_day, source) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (ev["ts_utc"], ev["title"], ev["currency"],
                 ev["impact"], "", "", ev["all_day"],
                 "federalreserve:fomccalendars"))
        con.commit()
        out["fomc"] = len(evs)
    nfp = nfp_seed_events(year0, year1)
    for ev in nfp:
        con.execute(
            "INSERT OR REPLACE INTO news_events "
            "(ts_utc, title, currency, impact, forecast, "
            "previous, all_day, source) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (ev["ts_utc"], ev["title"], ev["currency"],
             ev["impact"], "", "", ev["all_day"], ev["src"]))
    con.commit()
    out["nfp_rule_seed"] = len(nfp)
    return out


def fetch_calendar(con: sqlite3.Connection, weeks_back: int) -> dict:
    """Weekly feeds: only thisweek/nextweek are published by the
    mirror — history accrues by re-running weekly, nothing is
    backfilled. lastweek is attempted best-effort (usually 404)."""
    feeds = [("thisweek", _FF_XML)]
    if weeks_back >= 1:
        feeds.append(("lastweek", _FF_XML.replace(
            "thisweek", "lastweek")))
    total = 0
    out = {}
    for label, url in feeds:
        raw = _get(url)
        if raw is None:
            out[label] = "fetch failed"
            continue
        try:
            evs = parse_ff_calendar(raw.decode("windows-1252"))
        except ET.ParseError as exc:
            # e.g. lastweek returning an HTML error page — report the
            # feed as bad rather than failing the whole run
            out[label] = f"parse:{exc}"
            continue
        for ev in evs:
            con.execute(
                "INSERT OR REPLACE INTO news_events "
                "(ts_utc, title, currency, impact, forecast, "
                "previous, all_day, source) "
                "VALUES (?,?,?,?,?,?,?,?)",
                (ev["ts_utc"], ev["title"], ev["currency"],
                 ev["impact"], ev["forecast"], ev["previous"],
                 ev["all_day"], f"faireconomy_{label}"))
        con.commit()
        out[label] = len(evs)
        total += len(evs)
    return {"rows": total, "feeds": out}


# -----------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", default=str(DB))
    ap.add_argument("--sources",
                    default="fred,ecb,cot,calendar,ics,official")
    ap.add_argument("--years", type=int, default=5,
                    help="lookback for fred/ecb daily series")
    ap.add_argument("--cot-years", type=int, default=3)
    ap.add_argument("--weeks-back", type=int, default=1,
                    help="calendar: also pull last week's feed")
    ap.add_argument("--release-lookback", type=int, default=18,
                    help="release-date discovery: obs periods back "
                         "per series (~5 requests each)")
    args = ap.parse_args()

    con = init_db(Path(args.db))
    report = {}
    for src in [s.strip() for s in args.sources.split(",")]:
        t0 = time.time()
        try:
            if src == "fred":
                report["fred"] = fetch_fred(con, args.years)
            elif src == "ecb":
                report["ecb"] = fetch_ecb(con, args.years)
            elif src == "cot":
                report["cot"] = fetch_cot(con, args.cot_years)
            elif src in ("calendar", "news"):
                report["calendar"] = fetch_calendar(
                    con, args.weeks_back)
            elif src == "ics":
                report["ics"] = fetch_ics(con)
            elif src in ("official", "fomc"):
                report["official_cal"] = fetch_official_calendars(
                    con, 2021, date.today().year + 1)
            elif src == "releases":
                report["releases"] = fetch_release_dates(
                    con, args.release_lookback)
            else:
                report[src] = "unknown source"
        except Exception as exc:  # noqa: BLE001
            report[src] = {"error": str(exc)}
        report.setdefault("_elapsed_s", {})
    con.close()
    rp = ROOT / "var" / "collect_macro.json"
    rp.parent.mkdir(parents=True, exist_ok=True)
    rp.write_text(json.dumps(
        {"generated_at": time.time(), "db": args.db,
         "report": report}, indent=2))
    print(json.dumps(report, indent=2))
    print(f"report: {rp}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
