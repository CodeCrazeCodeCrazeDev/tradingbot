# REPRODUCIBILITY REPORT

## System Environment
- **Git SHA**: 55d3c1d74cfa1f560fff69fb09e5e04cea7a05f4 (Base)
- **Python Version**: 3.12.13
- **Dependencies**: `numpy 2.5.1`, `pandas 3.0.3`, `pytest 9.1.1`

## Deterministic Verification
The deterministic replay test `tests/test_deterministic_replay.py` ensures that running identical market configurations, random seeds, and input feature states produce 100% identical outputs in the Cognitive System Controller (CSC), including reasoning token logs and final outcomes.

## Verification Status
- **Consensus Replay**: Successfully verified via `tests/test_event_bus_e2e.py`.
- **Causal Consistency**: Validated across all 12 stages of the active inference loops.
