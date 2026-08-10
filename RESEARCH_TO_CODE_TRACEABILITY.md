# 🔗 Research-to-Code Traceability Matrix

This matrix provides mathematical, algorithmic, and file-level traceability from peer-reviewed scientific papers to active implementation files in AlphaAlgo.

---

| Paper ID | ArXiv ID | Title | Key Mechanism | Implementation File | Verification Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RSI-001** | 2601.14007 | Introspection Threshold | Thread-safe singletons | `trading_bot/core/unified_event_bus.py` | `tests/conftest.py` |
| **SR-001** | 2602.14015 | Self-Rewarding Models | Faceted evaluation | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_v5.py` |
| **ACT-001** | 2506.14023 | Active Inference | Surprise invalidation | `trading_bot/core/csc/controller.py` | `tests/uca_v5/test_csc_v5.py` |

---
