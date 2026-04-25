# Module Integration Checklist Template

**Use this template for each module being integrated into the production trading system.**

---

## Module Information

| Field | Value |
|-------|-------|
| **File Path** | `[absolute/path/to/module.py]` |
| **Module Name** | `[module_name]` |
| **Package** | `[parent.package]` |
| **Domain** | `[D01-D12]` |
| **Line Count** | `[number]` |
| **Complexity Score** | `[number]` |
| **Integration Status** | `[PENDING/ANALYZING/INTEGRATING/TESTING/COMPLETE/BLOCKED/ERROR]` |
| **Assigned To** | `[name]` |
| **Start Date** | `[YYYY-MM-DD]` |
| **Completion Date** | `[YYYY-MM-DD]` |

---

## Phase 1: Code Analysis

### 1.1 Source Code Review
- [ ] Read entire source code (do NOT assume based on name)
- [ ] Understand primary purpose and functionality
- [ ] Document all classes with their responsibilities
- [ ] Document all public functions with their signatures
- [ ] Identify any TODO/FIXME/HACK comments
- [ ] Note any hardcoded values that should be configurable

**Classes Found**:
```
1. ClassName1 - [description]
2. ClassName2 - [description]
```

**Functions Found**:
```
1. function_name(params) -> return_type - [description]
2. function_name(params) -> return_type - [description]
```

**Notes**:
```
[Any special observations about the code]
```

### 1.2 Import Analysis
- [ ] List all internal imports
- [ ] List all external imports
- [ ] Verify each import is resolvable
- [ ] Check for potential circular imports
- [ ] Verify external packages are in requirements.txt

**Internal Imports**:
```python
from trading_bot.xxx import YYY
from trading_bot.zzz import AAA
```

**External Imports**:
```python
import numpy as np
import pandas as pd
```

**Import Issues Found**:
```
[List any import problems]
```

### 1.3 Export Analysis
- [ ] Check for `__all__` definition
- [ ] Identify all public exports
- [ ] Verify exports are properly documented

**Exports**:
```python
__all__ = ['Class1', 'function1', 'CONSTANT1']
```

---

## Phase 2: Interface Definition

### 2.1 Input Specification
- [ ] Define all input parameters
- [ ] Document expected data types
- [ ] Document validation requirements
- [ ] Document default values

**Inputs**:
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| param1 | `str` | Yes | - | Description |
| param2 | `int` | No | `10` | Description |

### 2.2 Output Specification
- [ ] Define all output types
- [ ] Document return value structure
- [ ] Document side effects

**Outputs**:
| Output | Type | Description |
|--------|------|-------------|
| result | `Dict[str, Any]` | Description |

### 2.3 Event Specification
- [ ] Define events consumed
- [ ] Define events emitted
- [ ] Document event schemas

**Events Consumed**:
| Event Type | Handler | Description |
|------------|---------|-------------|
| `MarketDataEvent` | `on_market_data()` | Handles incoming market data |

**Events Emitted**:
| Event Type | Trigger | Description |
|------------|---------|-------------|
| `SignalEvent` | Signal generated | Emits trading signal |

### 2.4 Error Specification
- [ ] Define all error conditions
- [ ] Document exception types
- [ ] Document error codes

**Errors**:
| Error Type | Code | Condition | Recovery |
|------------|------|-----------|----------|
| `ValidationError` | `E001` | Invalid input | Return error response |
| `ConnectionError` | `E002` | Broker disconnect | Retry with backoff |

---

## Phase 3: Error Handling

### 3.1 Exception Handling
- [ ] Add try/except blocks for all external calls
- [ ] Use specific exception types (not bare except)
- [ ] Log all exceptions with context
- [ ] Implement graceful degradation where appropriate

**Implementation**:
```python
try:
    result = external_call()
except SpecificError as e:
    logger.error("Operation failed", error=str(e), context={...})
    raise TradingError(f"Failed: {e}", code="E001") from e
```

### 3.2 Retry Logic
- [ ] Implement retry for transient failures
- [ ] Use exponential backoff
- [ ] Set maximum retry attempts
- [ ] Log retry attempts

**Implementation**:
```python
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
async def operation():
    ...
```

### 3.3 Circuit Breaker
- [ ] Implement circuit breaker for external dependencies
- [ ] Configure failure threshold
- [ ] Configure recovery timeout

---

## Phase 4: Logging & Monitoring

### 4.1 Structured Logging
- [ ] Add structured logging with appropriate levels
- [ ] Include correlation IDs
- [ ] Include relevant context
- [ ] Avoid logging sensitive data

**Implementation**:
```python
import structlog
logger = structlog.get_logger(__name__)

logger.info(
    "operation_completed",
    operation="process_signal",
    symbol=symbol,
    duration_ms=duration,
    correlation_id=correlation_id
)
```

### 4.2 Metrics Collection
- [ ] Define key metrics to track
- [ ] Implement metric collection
- [ ] Add metric labels for filtering

**Metrics**:
| Metric Name | Type | Labels | Description |
|-------------|------|--------|-------------|
| `signals_generated_total` | Counter | symbol, strategy | Total signals generated |
| `signal_latency_seconds` | Histogram | symbol | Signal generation latency |

### 4.3 Health Check
- [ ] Implement health check method
- [ ] Return meaningful health status
- [ ] Include dependency health

**Implementation**:
```python
def health_check(self) -> Dict[str, Any]:
    return {
        "status": "healthy",
        "component": "SignalGenerator",
        "dependencies": {
            "database": self._check_db_health(),
            "broker": self._check_broker_health()
        },
        "metrics": {
            "signals_today": self._signals_today,
            "error_rate": self._error_rate
        }
    }
```

---

## Phase 5: Configuration

### 5.1 Configuration Extraction
- [ ] Extract all hardcoded values to config
- [ ] Define configuration schema
- [ ] Add environment-specific overrides
- [ ] Document all configuration parameters

**Configuration Parameters**:
| Parameter | Type | Default | Env Var | Description |
|-----------|------|---------|---------|-------------|
| `max_signals_per_minute` | `int` | `100` | `SIGNAL_RATE_LIMIT` | Rate limit |
| `confidence_threshold` | `float` | `0.7` | `SIGNAL_CONFIDENCE` | Min confidence |

### 5.2 Configuration Validation
- [ ] Validate configuration on startup
- [ ] Fail fast on invalid configuration
- [ ] Log configuration values (non-sensitive)

---

## Phase 6: Testing

### 6.1 Unit Tests
- [ ] Write unit tests for all public methods
- [ ] Achieve >80% code coverage
- [ ] Test edge cases
- [ ] Test error conditions

**Test Files**:
```
tests/unit/test_[module_name].py
```

**Coverage**: `[XX]%`

### 6.2 Integration Tests
- [ ] Write integration tests with dependencies
- [ ] Test event flow
- [ ] Test error propagation

**Test Files**:
```
tests/integration/test_[module_name]_integration.py
```

### 6.3 Performance Tests
- [ ] Benchmark critical paths
- [ ] Verify latency requirements
- [ ] Test under load

**Benchmarks**:
| Operation | Target | Actual | Status |
|-----------|--------|--------|--------|
| `generate_signal()` | <1ms | 0.5ms | ✅ |
| `validate_trade()` | <5ms | 3ms | ✅ |

---

## Phase 7: Documentation

### 7.1 Code Documentation
- [ ] Add/update module docstring
- [ ] Add/update class docstrings
- [ ] Add/update function docstrings
- [ ] Include usage examples

### 7.2 API Documentation
- [ ] Document public API
- [ ] Include request/response examples
- [ ] Document error responses

### 7.3 Integration Documentation
- [ ] Document integration points
- [ ] Document event contracts
- [ ] Document configuration

---

## Phase 8: Governance Compliance

### 8.1 Safety Constraints
- [ ] Verify compliance with immutable constraints
- [ ] Implement required safety checks
- [ ] Add kill switch support if applicable

**Constraints Verified**:
- [ ] Max risk per trade: 2%
- [ ] Max daily loss: 5%
- [ ] Max drawdown: 20%
- [ ] Human override available

### 8.2 Audit Logging
- [ ] Add audit logging for critical operations
- [ ] Include actor, action, timestamp
- [ ] Ensure immutability of audit trail

### 8.3 Approval Workflow
- [ ] Identify operations requiring approval
- [ ] Implement approval request flow
- [ ] Document approval requirements

---

## Phase 9: Final Verification

### 9.1 Code Review
- [ ] Code review completed
- [ ] All review comments addressed
- [ ] Reviewer sign-off obtained

**Reviewer**: `[name]`
**Review Date**: `[YYYY-MM-DD]`

### 9.2 Integration Verification
- [ ] All imports resolve correctly
- [ ] All tests passing
- [ ] No circular dependencies
- [ ] Performance requirements met

### 9.3 Production Readiness
- [ ] Logging implemented
- [ ] Health checks working
- [ ] Metrics collecting
- [ ] Documentation complete
- [ ] Configuration externalized

---

## Sign-Off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Developer | | | |
| Reviewer | | | |
| QA | | | |
| Tech Lead | | | |

---

## Notes & Issues

```
[Document any issues, blockers, or special considerations]
```

---

## Change History

| Date | Author | Change |
|------|--------|--------|
| YYYY-MM-DD | Name | Initial integration |
| YYYY-MM-DD | Name | Fixed import issue |
