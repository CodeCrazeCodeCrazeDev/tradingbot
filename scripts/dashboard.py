"""Read-only CSC dashboard — serves the runner's snapshot.json as a
live HTML view. GET-only, binds localhost, auto-refresh every 5s.

    python scripts/dashboard.py --state-dir var/hl_run --port 8080
"""

import argparse
import http.server
import json
import os
import sys
import threading
import time

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
const s=await(await fetch('/snapshot.json')).json();
const f=s.funnel||{};const c=s.control||{};
let h='<h1>CSC Live — '+ (s.symbol||'?') +' '+ (s.data_timeframe||'')
+' <span class="warn">'+ (s.mode||'') +'</span></h1>';
h+='<div class=big>cycles: '+(s.cycles??'—')+
' | trading: '+(c.trading_enabled?'ENABLED':'PAUSED')+
' | estop: '+(c.estop?'YES':'no')+'</div>';
h+='<h2>decisions</h2><table>';
for(const k of ['terminal_ABSTAIN','terminal_TRADE_APPROVED',
 'terminal_TRADE_REJECTED','exploratory_trades','settled_positions',
 'churn_abstain','nondirectional_abstain'])
 h+='<tr><td>'+k+'<td class='+(f[k]?'warn':'')+'>'+(f[k]??0);
h+='<h2>pipeline</h2><table>';
for(const k of ['observations','advisory_artifacts','advisor_substantive',
 'advisor_directional_calls','advisor_degenerate','advisors_deferred',
 'sig_quarantined','tilt_quarantined','hypothesis_branches',
 'verification','verification_terminal','directional_proposals',
 'risk_check','shield','governance','swarm_deliberations'])
 h+='<tr><td>'+k+'<td>'+(f[k]??0);
h+='<h2>advisors/exceptions</h2><table>';
for(const k of ['advisor_exceptions','self_feedback_suspect'])
 h+='<tr><td>'+k+'<td>'+(f[k]??0);
const adv=s.advisors||{};const st=adv.states||{};
h+='<tr><td>electorate<td>'+Object.keys(st).length+' tracked';
h+='<h2>research</h2><table>';
h+='<tr><td>economic_rewards<td>'+JSON.stringify(s.economic_rewards);
h+='<tr><td>ai_stack<td>'+JSON.stringify(s.ai_stack).slice(0,300);
h+='</table><div style="color:#484f58;margin-top:16px">'+
new Date().toLocaleTimeString()+' — auto-refresh 5s</div>';
document.getElementById('x').innerHTML=h}catch(e){
document.getElementById('x').innerHTML='waiting for snapshot… '+e}}
go();setInterval(go,5000)</script>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state-dir", required=True)
    ap.add_argument("--port", type=int, default=8080)
    args = ap.parse_args()
    snap_path = os.path.join(args.state_dir, "snapshot.json")

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path in ("/", "/index.html"):
                body = _HTML.encode()
            elif self.path == "/snapshot.json":
                try:
                    body = open(snap_path, "rb").read()
                except OSError:
                    body = b'{"status":"waiting_for_runner"}'
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type",
                             "text/html" if self.path in ("/", "/index.html")
                             else "application/json")
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
