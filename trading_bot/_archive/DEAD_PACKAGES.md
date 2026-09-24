# Quarantined Dead Packages

Moved here during the Phase-5 deep cleanup (reachability scan `scan_reachability.py`).

These 28 top-level subpackages were **unreachable** — nothing in the live
import graph (`trading_bot/__init__.py`, `main.py`, `tests/`, root scripts,
plus transitively-resolved and string-literal `importlib` references)
imports them, and they contain no `__main__` entry points of their own.

| Package | Files | Lines |
|---|---|---|
| _calendar_deprecated | 2 | 567 |
| advanced_ai | 14 | 13462 |
| aletheia_autonomous | 12 | 4877 |
| anti_rogue_ai | 5 | 1880 |
| autonomous_research_organism | 9 | 6081 |
| domains | 14 | 2290 |
| elite_integration | 1 | 20 |
| foundation_agents | 50 | 24757 |
| intelligent_delegation | 9 | 5454 |
| mosefs | 8 | 12433 |
| neuros_fi | 12 | 9989 |
| perplexity_trading | 15 | 8835 |
| phce_d | 16 | 5463 |
| quant_analysis | 2 | 432 |
| recursive_evolution | 10 | 5628 |
| research_lab | 4 | 583 |
| resilience | 2 | 329 |
| risk_intelligence | 5 | 1113 |
| self_assembly_ai | 13 | 7023 |
| self_coordinating_ai | 12 | 8981 |
| self_dialogue | 5 | 601 |
| signal_discovery | 14 | 1815 |
| strategy_discovery | 5 | 1847 |
| training | 1 | 42 |
| unified_evolution | 4 | 1734 |
| utils2 | 1 | 42 |
| visualizations | 1 | 272 |
| web | 1 | 42 |

**Not quarantined** (unreachable but contain `__main__` entry points —
possible standalone CLIs; review before deciding): `gets`, `aads`,
`apex_fi`, `superpowerful_ai`, `intelligence_core`, `neural_integration`,
`adversarial_verification`.

Verified after the move: `import trading_bot` clean; 40/40 cognition +
CSC tests pass. Restore any package by moving it back under `trading_bot/`.
