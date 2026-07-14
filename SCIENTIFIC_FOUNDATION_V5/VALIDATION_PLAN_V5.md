# Validation Plan: AlphaAlgo UCA V5

## 1. Unit Testing
- **Target**: Functional correctness of DiscoLoop, SAGE, and HASP.
- **Suite**: `tests/uca_v5/`
- **Execution**: `python3 -m pytest tests/uca_v5/`

## 2. Integrated Verification
- **Target**: 12-step pipeline completeness and consensus reliability.
- **Suite**: `tests/uca_v5_validation.py`
- **Execution**: `python3 -m pytest tests/uca_v5_validation.py`

## 3. Benchmarks
- **Latency**: Ensure $K=3$ DiscoLoop + SAGE retrieval < 500ms.
- **Derivation Depth**: Verify multi-hop evidence recovery depth using SAGE.
- **Calibration (Brier Score)**: Measure probability calibration of trade proposals.

## 4. Institutional Audits
- **Immutable Shield**: Verify that no trade bypasses the compliance gate.
- **LogAct Integrity**: Ensure all actions are reproducible from the shared log.
