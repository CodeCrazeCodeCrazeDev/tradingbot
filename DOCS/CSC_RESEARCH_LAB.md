# CSC Research Lab — specialist agents behind an adaptive router

`trading_bot/core/csc/research_lab.py` implements the autonomous
research & discovery layer as a manifest-declared advisory service.
Buzzword → what it honestly is here:

| Requested | Implementation |
|---|---|
| Researcher agent | `ResearcherAgent` — delegates to the existing `research/` engine fetchers; reports unreachable honestly |
| ML research | `MLResearchAgent` — runs/reads the real edge gates (`var/edge_features.json` verdicts); measured, never simulated |
| Risk engineer | `RiskEngineerAgent` — realized vol from `market_data.db`, COT positioning z-score, forward release density from `news_events` |
| Distributed-systems engineer | `SystemsEngineerAgent` — runs `discovery.scan_packages` on the repo: wired nodes, blocked interfaces, cycles, coverage |
| Global economic & opportunity radar | `OpportunityRadarAgent` — fuses market momentum + COT positioning + edge-gate candidates into a ranked watchlist with per-row provenance |
| Adaptive routing / self-rewiring network | `AdaptiveRouter` — routes task kind → agent `provides` interface, ordered by an EMA health score updated on measured outcomes (same evidence-only rule the electorate obeys) |
| Self-assembly / self-managing | `CSC_MANIFEST` on the module → `discovery.py` finds it, dep-orders it, wires it to the CSC as advisory at SHADOW; `build()` is the factory |
| Palantir/Google/CIA/Mosaic "best of" | provenance-tagged artifacts (Palantir-style ontology), measured evidence at scale (Google-style eval culture), multi-source fusion (Mosaic-style intel = macro + COT + calendar + market), Perplexity-style = the `research/` fetcher layer |

Every artifact carries `confidence: measured | partial | unprovisioned`
— the radar reports signal strength, never asserted edge. The lab is
advisory-only by construction (`authority: advisory_only`); the CSC
decides.

## Boundaries (unchanged)

- Agents cannot create orders, change sizing, or promote anything
- Router score adapts on measured outcomes only — one bad run can't
  kill an agent; sustained failure costs routing share
- `MAX_TASKS_PER_CYCLE` and per-agent timeouts bound every cycle

```python
from trading_bot.core.csc.research_lab import build, ResearchTask
lab = build()
report = lab.run([ResearchTask("risk_memo", {"symbol": "EURUSD"})])
```

Tests: `tests/foundation/test_research_lab.py` (6 tests — routing,
score adaptation, honest fallback, manifest parseability, bounded
queue, advisory interface).
