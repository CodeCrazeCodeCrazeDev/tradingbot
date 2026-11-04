"""Read-only CSC dashboard — serves the runner's snapshot.json as a
live HTML view. GET-only, binds localhost, auto-refresh every 5s.

    python scripts/dashboard.py --state-dir var/hl_run --port 8080
"""

import argparse
import http.server
import json
import math
from pathlib import Path
import sys
import time

def dashboard_status(snapshot, now=None):
    """Missing/stale evidence must never be rendered as a healthy live run."""
    now = time.time() if now is None else now
    control = snapshot.get("control") or {}
    emergency = (control.get("emergency_stop") or {}).get("triggered")
    trading = ("BLOCKED" if emergency is True else
               "PAUSED" if control.get("trading_paused") is True else
               "ALLOWED" if emergency is False and control.get("trading_allowed") is True else
               "BLOCKED" if control.get("trading_allowed") is False else "UNKNOWN")
    as_of = snapshot.get("as_of")
    valid = (type(as_of) in (int, float) and math.isfinite(as_of)
             and 0 < as_of <= now + 5)
    age = max(0, now - as_of) if valid else None
    return {
        "trading": trading,
        "emergency": "ACTIVE" if emergency is True else "CLEAR" if emergency is False else "UNKNOWN",
        "age_seconds": round(age) if age is not None else None,
        "freshness": "UNKNOWN" if age is None else "STALE" if age > 60 else "RECENT",
    }

_HTML = """<!doctype html><meta charset=utf-8><title>CSC Dashboard</title>
<style>
body{background:#0d1117;color:#c9d1d9;font-family:Consolas,monospace;
margin:24px;font-size:14px}
h1{color:#58a6ff;font-size:18px} h2{color:#8b949e;font-size:14px;
margin:18px 0 4px} table{border-collapse:collapse}
td{padding:2px 14px 2px 0;border-bottom:1px solid #21262d}
td:first-child{color:#8b949e}.big{font-size:22px;color:#f0f6fc}
.ok{color:#3fb950}.warn{color:#d29922}.bad{color:#f85149}
</style>
<div id=x>loading…</div>
<script>
async function go(){try{
const s=await(await fetch('/snapshot.json',{cache:'no-store'})).json();
const f=s.funnel||{};const c=s.control||{};
const d=s._dashboard||{};
const esc=v=>String(v??'unknown').replace(/[&<>"']/g,
 ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
let h='<h1>CSC Snapshot — '+ esc(s.symbol||'?') +' '+ esc(s.data_timeframe||'')
+' <span class="warn">'+ esc(s.mode||'') +'</span></h1>';
h+='<div class=big>cycles: '+(s.cycles??'—')+
' | trading permission: '+esc(d.trading)+
' | emergency stop: '+esc(d.emergency)+'</div>';
h+='<p class="'+(d.freshness==='RECENT'?'ok':'warn')+'">'+esc(d.freshness)+
' snapshot | age: '+esc(d.age_seconds)+' seconds | captured: '+
esc(s.as_of?new Date(s.as_of*1000).toLocaleString():'unknown')+'</p>';
h+='<p>These are saved cycle results. A recent snapshot alone does not prove the runner is still running.</p>';
if(s._run) h+='<p>Supervised run: '+
esc(['running','stopping'].includes(s._run.status) &&
    (!s._run.heartbeat || Date.now()/1000-s._run.heartbeat>10)
    ?'UNCONFIRMED (stale heartbeat)':s._run.status)+
' | heartbeat: '+esc(s._run.heartbeat?new Date(s._run.heartbeat*1000).toLocaleString():'unknown')+
' | deadline: '+esc(s._run.deadline?new Date(s._run.deadline*1000).toLocaleString():'unknown')+'</p>';
h+='<h2>decisions</h2><table>';
for(const k of ['terminal_ABSTAIN','terminal_TRADE_APPROVED',
 'terminal_TRADE_REJECTED','exploratory_trades','settled_positions',
 'churn_abstain','nondirectional_abstain'])
 h+='<tr><td>'+k+'<td class='+(f[k]?'warn':'')+'>'+(f[k]??0);
h+='</table><h2>pipeline</h2><table>';
for(const k of ['observations','advisory_artifacts','advisor_substantive',
 'advisor_directional_calls','advisor_degenerate','advisors_deferred',
 'sig_quarantined','tilt_quarantined','hypothesis_branches',
 'verification','verification_terminal','directional_proposals',
 'risk_check','shield','governance','swarm_deliberations'])
 h+='<tr><td>'+k+'<td>'+(f[k]??0);
h+='</table><h2>advisors/exceptions</h2><table>';
for(const k of ['advisor_exceptions','self_feedback_suspect'])
 h+='<tr><td>'+k+'<td>'+(f[k]??0);
const adv=s.advisors||{};
h+='<tr><td>electorate<td>'+esc(Array.isArray(adv.attached)?adv.attached.length:adv.attached)+' attached';
h+='</table><h2>research</h2><table>';
h+='<tr><td>economic_rewards<td>'+esc(JSON.stringify(s.economic_rewards));
h+='<tr><td>ai_stack<td>'+esc(JSON.stringify(s.ai_stack));
h+='</table><div style="color:#484f58;margin-top:16px">'+
new Date().toLocaleTimeString()+' — auto-refresh 5s</div>';
document.getElementById('x').innerHTML=h}catch(e){
document.getElementById('x').textContent='Snapshot unavailable: '+e}}
go();setInterval(go,5000)</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    state_dir = Path(args.state_dir)
    snap_path = state_dir / "snapshot.json"

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                body = _HTML.encode()
            elif self.path == "/snapshot.json":
                try:
                    snapshot = json.loads(snap_path.read_text(encoding="utf-8"))
                    if not isinstance(snapshot, dict):
                        raise ValueError("snapshot must be an object")
                except (OSError, ValueError):
                    snapshot = {"status": "waiting_for_runner"}
                snapshot["_dashboard"] = dashboard_status(snapshot)
                try:
                    snapshot["_run"] = json.loads(
                        (state_dir / "validation_run.json").read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    pass
                body = json.dumps(snapshot).encode("utf-8")
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html" if self.path in ("/", "/index.html")
                             else "application/json")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *a):
            pass  # quiet

    srv = http.server.HTTPServer(("127.0.0.1", args.port), H)
    print(f"dashboard: http://localhost:{args.port} "
          f"(reading {snap_path}) — GET-only, localhost")
    srv.serve_forever()


if __name__ == "__main__":
    sys.exit(main())
