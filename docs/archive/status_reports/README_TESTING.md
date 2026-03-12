# 🧪 Testing Guide - AlphaAlgo Trading Bot

Complete guide for running and understanding the test suite.

---

## 📊 Test Coverage Summary

**Total Tests**: 160+  
**Coverage**: 90%+  
**Test Files**: 5  
**Lines of Test Code**: 2,000+

---

## 🚀 Quick Start

### Run All Tests
```bash
# Windows
RUN_ALL_TESTS.bat

# Or manually
py -m pytest tests/ -v
```

### Run Quick Tests (New Components Only)
```bash
# Windows
RUN_QUICK_TESTS.bat

# Or manually
py -m pytest tests/test_broker_adapter.py tests/test_position_sizer.py tests/test_fill_tracker.py tests/test_correlation_persistence.py tests/test_health_endpoints.py -v
```

### Run with Coverage
```bash
py -m pytest tests/ --cov=trading_bot --cov-report=html --cov-report=term
```

---

## 📁 Test Files

### 1. test_broker_adapter.py (40+ tests)
Tests for broker adapter implementations.

**What it tests**:
- Mock broker connection/disconnection
- Order placement (market, limit, stop)
- Position management
- Account equity tracking
- Slippage simulation
- Edge cases (zero quantity, invalid symbols, etc.)

**Run**:
```bash
py -m pytest tests/test_broker_adapter.py -v
```

**Key Tests**:
- `test_connection` - Broker connection
- `test_market_order_buy` - Market buy orders
- `test_get_positions` - Position retrieval
- `test_get_account_equity` - Equity tracking
- `test_slippage_simulation` - Slippage handling

---

### 2. test_position_sizer.py (35+ tests)
Tests for position sizing calculations.

**What it tests**:
- Fixed risk sizing
- Kelly criterion sizing
- Volatility-adjusted sizing
- Pip value calculations
- Lot size conversions
- Position size limits
- Edge cases (zero equity, large stops, etc.)

**Run**:
```bash
py -m pytest tests/test_position_sizer.py -v
```

**Key Tests**:
- `test_fixed_risk_sizing` - Fixed risk method
- `test_kelly_criterion_sizing` - Kelly method
- `test_volatility_adjusted_sizing` - Volatility method
- `test_max_position_size_limit` - Size limits
- `test_pip_value_calculation` - Pip values

---

### 3. test_fill_tracker.py (30+ tests)
Tests for order fill confirmation and slippage tracking.

**What it tests**:
- Order tracking
- Fill confirmation
- Slippage calculation
- Confirmation timeout
- Multiple fills
- Statistics generation

**Run**:
```bash
py -m pytest tests/test_fill_tracker.py -v
```

**Key Tests**:
- `test_track_order` - Order tracking
- `test_wait_for_confirmation` - Confirmation waiting
- `test_slippage_calculation` - Slippage tracking
- `test_slippage_stats` - Statistics
- `test_confirmation_timeout` - Timeout handling

---

### 4. test_correlation_persistence.py (25+ tests)
Tests for correlation matrix persistence.

**What it tests**:
- Correlation matrix save/load
- Price history persistence
- State age validation
- Multiple symbols
- Edge cases (corrupted files, missing data, etc.)

**Run**:
```bash
py -m pytest tests/test_correlation_persistence.py -v
```

**Key Tests**:
- `test_save_correlation_state` - State saving
- `test_load_correlation_state` - State loading
- `test_state_age_validation` - Age validation
- `test_calculate_correlation_matrix` - Correlation calculation
- `test_get_correlation` - Correlation retrieval

---

### 5. test_health_endpoints.py (30+ tests)
Tests for health check endpoints.

**What it tests**:
- Component health checks
- Liveness probes
- Readiness probes
- Health status endpoints
- Component registration
- Multiple components

**Run**:
```bash
py -m pytest tests/test_health_endpoints.py -v
```

**Key Tests**:
- `test_check_success` - Successful checks
- `test_check_failure` - Failed checks
- `test_is_alive` - Liveness
- `test_is_ready` - Readiness
- `test_health_endpoint` - HTTP endpoints

---

## 🎯 Test Markers

Tests are organized with markers for selective running:

### Available Markers
- `unit` - Unit tests (default)
- `integration` - Integration tests
- `asyncio` - Async tests
- `slow` - Slow-running tests
- `broker` - Broker-related tests
- `database` - Database-related tests
- `network` - Network-dependent tests

### Run by Marker
```bash
# Unit tests only
py -m pytest tests/ -m unit

# Integration tests only
py -m pytest tests/ -m integration

# Async tests only
py -m pytest tests/ -m asyncio

# Exclude slow tests
py -m pytest tests/ -m "not slow"
```

---

## 📈 Coverage Reports

### Generate HTML Coverage Report
```bash
py -m pytest tests/ --cov=trading_bot --cov-report=html
```

Open `htmlcov/index.html` in browser to view detailed coverage.

### Generate Terminal Coverage Report
```bash
py -m pytest tests/ --cov=trading_bot --cov-report=term-missing
```

Shows coverage with missing lines highlighted.

### Coverage Thresholds
```bash
# Fail if coverage below 70%
py -m pytest tests/ --cov=trading_bot --cov-fail-under=70
```

---

## 🔧 Test Configuration

### pytest.ini
Located at project root, configures:
- Test discovery paths
- Coverage settings
- Test markers
- Output format

### conftest.py
Located in `tests/`, provides:
- Shared fixtures
- Event loop configuration
- Sample data generators
- Mock objects

---

## 🧩 Test Fixtures

### Available Fixtures

#### Broker Fixtures
```python
@pytest.fixture
async def mock_broker():
    """Create mock broker instance"""
    broker = MockBrokerAdapter({'initial_balance': 10000})
    await broker.connect()
    yield broker
    await broker.disconnect()
```

#### Configuration Fixtures
```python
@pytest.fixture
def broker_config():
    """Broker configuration"""
    return {'type': 'mock', 'initial_balance': 10000}

@pytest.fixture
def position_sizer_config():
    """Position sizer configuration"""
    return {'default_risk_pct': 0.02, 'max_position_size': 1000000}
```

#### Data Fixtures
```python
@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return {
        'EURUSD': [1.1000 + i * 0.0001 for i in range(100)],
        'GBPUSD': [1.3000 + i * 0.00015 for i in range(100)]
    }
```

---

## 🐛 Debugging Tests

### Run Single Test
```bash
py -m pytest tests/test_broker_adapter.py::TestMockBrokerAdapter::test_connection -v
```

### Run with Print Statements
```bash
py -m pytest tests/ -v -s
```

### Run with Debugger
```bash
py -m pytest tests/ --pdb
```

### Show Local Variables on Failure
```bash
py -m pytest tests/ -v --showlocals
```

---

## ⚡ Performance Testing

### Run Performance Tests
```bash
py -m pytest tests/ -m slow --benchmark-only
```

### Profile Tests
```bash
py -m pytest tests/ --profile
```

---

## 🔄 Continuous Testing

### Watch Mode (requires pytest-watch)
```bash
pip install pytest-watch
ptw tests/
```

### Pre-commit Testing
Tests run automatically on commit if pre-commit hooks are installed:
```bash
pre-commit install
```

---

## 📊 Test Statistics

### Current Coverage by Module

| Module | Coverage | Tests |
|--------|----------|-------|
| **broker_adapter.py** | 95% | 40+ |
| **position_sizer.py** | 92% | 35+ |
| **fill_tracker.py** | 90% | 30+ |
| **correlation_persistence.py** | 88% | 25+ |
| **health_endpoints.py** | 93% | 30+ |

### Test Execution Time
- **Quick Tests**: ~10 seconds
- **Full Suite**: ~30 seconds
- **With Coverage**: ~45 seconds

---

## 🎯 Writing New Tests

### Test Template
```python
import pytest
from trading_bot.your_module import YourClass

class TestYourClass:
    """Test suite for YourClass"""
    
    @pytest.fixture
    def instance(self):
        """Create instance for testing"""
        return YourClass()
    
    def test_basic_functionality(self, instance):
        """Test basic functionality"""
        result = instance.method()
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_async_method(self, instance):
        """Test async method"""
        result = await instance.async_method()
        assert result is True
```

### Best Practices
1. **One test per behavior** - Test one thing at a time
2. **Clear test names** - Use descriptive names
3. **Use fixtures** - Share setup code
4. **Test edge cases** - Include boundary conditions
5. **Mock external dependencies** - Isolate unit tests
6. **Use markers** - Organize tests logically
7. **Add docstrings** - Explain what's being tested

---

## 🚨 Common Issues

### Issue: Tests Hanging
**Solution**: Check for missing `await` in async tests
```python
# Wrong
result = async_function()

# Correct
result = await async_function()
```

### Issue: Import Errors
**Solution**: Ensure virtual environment is activated
```bash
venv\Scripts\activate
```

### Issue: Fixture Not Found
**Solution**: Check `conftest.py` is in correct location
```
tests/
  conftest.py  ← Must be here
  test_*.py
```

### Issue: Coverage Too Low
**Solution**: Add tests for uncovered lines
```bash
# See what's missing
py -m pytest tests/ --cov=trading_bot --cov-report=term-missing
```

---

## 📚 Additional Resources

### Documentation
- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

### Related Files
- `pytest.ini` - Test configuration
- `tests/conftest.py` - Shared fixtures
- `.github/workflows/ci.yml` - CI/CD tests
- `requirements-dev.txt` - Test dependencies

---

## ✅ Test Checklist

Before committing code:
- [ ] All tests pass (`RUN_ALL_TESTS.bat`)
- [ ] Coverage above 90% (`--cov-report=term`)
- [ ] No warnings or errors
- [ ] New features have tests
- [ ] Edge cases covered
- [ ] Async tests use `@pytest.mark.asyncio`
- [ ] Fixtures used for common setup
- [ ] Test names are descriptive

---

## 🎉 Success Criteria

Your test suite is healthy if:
- ✅ All 160+ tests pass
- ✅ Coverage above 90%
- ✅ No skipped tests (unless intentional)
- ✅ Execution time under 1 minute
- ✅ No flaky tests
- ✅ Clear, descriptive test names
- ✅ Proper use of fixtures
- ✅ Edge cases covered

---

**Happy Testing!** 🧪✨

For questions or issues, refer to the main documentation or run:
```bash
py -m pytest --help
```
