"""Stream Binance UM bookTicker daily zips -> per-second last-quote CSVs.

Each day's zip is ~128MB; we stream-decompress and retain only a 1s
resample (~5MB/day). Raw zips are never written to disk.
Usage: python scripts/stream_bookticker.py 2024-01-05 2024-01-06
"""
import csv
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

UM = "https://data.binance.vision/data/futures/um/daily"
L2_DIR = Path("var/l2data")


def stream_day(symbol: str, day: str) -> int:
    dest = L2_DIR / f"{symbol}-bookTicker1s-{day}.csv"
    if dest.exists():
        print(day, "cached", flush=True)
        return sum(1 for _ in dest.open()) - 1
    url = f"{UM}/bookTicker/{symbol}/{symbol}-bookTicker-{day}.zip"
    print(day, "downloading...", flush=True)
    req = urllib.request.Request(url)
    blob = urllib.request.urlopen(req, timeout=300).read()
    z = zipfile.ZipFile(io.BytesIO(blob))
    L2_DIR.mkdir(parents=True, exist_ok=True)
    last: dict = {}
    n = 0
    with z.open(z.namelist()[0]) as f, dest.open("w", newline="") as out:
        w = csv.writer(out)
        w.writerow(["ts", "bid", "ask", "bid_qty", "ask_qty"])
        for line in io.TextIOWrapper(f):
            p = line.strip().split(",")
            if p[0] == "update_id" or len(p) < 6:
                continue
            sec = int(p[5]) // 1000
            if sec != last.get("sec") and last:
                w.writerow([last["sec"] * 1000, last["b"],
                            last["a"], last["bq"], last["aq"]])
                n += 1
            last = {"sec": sec, "b": p[1], "bq": p[2],
                    "a": p[3], "aq": p[4]}
    print(day, "done", n, "quotes", flush=True)
    return n


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("20") else "BTCUSDT"
    days = [a for a in sys.argv[1:] if a.startswith("20")] or sys.argv[2:]
    for d in days:
        try:
            stream_day(sym, d)
        except Exception as e:
            print(d, "FAIL", repr(e)[:160], flush=True)
