# Hypothesis Promotion Points

The following paths describe how a hypothesis moves from a raw claim to institutional knowledge or production deployment:

| Source State | Destination State | Promotion Logic / Gate | File Path |
|--------------|-------------------|------------------------|-----------|
| `OBSERVATION` | `LEVEL_1 (Candidate)`| `generate_hypothesis()` | `SRE Core` |
| `Candidate` | `LEVEL_2 (Validated)`| `evaluate_results()` | `SRE Core` |
| `Validated` | `LEVEL_3 (Research)` | `integrate_knowledge()` | `SRE Core` |
| `Research` | `LEVEL_4 (Production)`| `improve_policy()` | `SRE Core` |
| `Production` | `LEVEL_5 (Institutional)`| `retire_hypothesis()` (Confirmed Path) | `SRE Core` |
| `ACTIVE` | `PAPER_TRADE_CANDIDATE`| Passing `ValidationGateway` | `PHCE-D` |
| `PAPER_TRADE`| `LIVE_EXECUTION` | `PaperTradePromotionThresholds` met | `phce_d/paper_trade_promotion.py` |
| `Hypothesis` | `Memory Tier 4/5` | Successful meta-analysis & consolidation | `core/hms/memory.py` |
| `Signal` | `Alpha` | Consistent outperformance vs benchmark | `autonomous/alpha_factor_discovery.py` |
