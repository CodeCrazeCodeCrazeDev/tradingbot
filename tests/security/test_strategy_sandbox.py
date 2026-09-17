import asyncio
import pytest
from trading_bot.core.security.sandbox import StrategySandbox, UnsafeCodeError

@pytest.mark.asyncio
async def test_sandbox_successful_execution():
    sandbox = StrategySandbox()

    code = """
def compute_signal(data):
    print("Computing signal...")
    return data * 2.5
"""

    response = await sandbox.execute_secure(code, "compute_signal", (10.0,))
    assert response["success"] is True
    assert response["result"] == 25.0
    assert "Computing signal..." in response["stdout"]

@pytest.mark.asyncio
async def test_sandbox_ast_validation_rejects_unsafe_import():
    sandbox = StrategySandbox()

    code = """
import os
def malicious_func(data):
    return data
"""

    with pytest.raises(UnsafeCodeError) as exc_info:
        await sandbox.execute_secure(code, "malicious_func", (10.0,))

    assert "Import of module 'os' is blocked" in str(exc_info.value)

@pytest.mark.asyncio
async def test_sandbox_ast_validation_rejects_unsafe_call():
    sandbox = StrategySandbox()

    code = """
def malicious_func(data):
    eval("print('hello')")
    return data
"""

    with pytest.raises(UnsafeCodeError) as exc_info:
        await sandbox.execute_secure(code, "malicious_func", (10.0,))

    assert "Call to blocked function 'eval'" in str(exc_info.value)

@pytest.mark.asyncio
async def test_sandbox_process_isolation_timeout():
    # Enforce a tight 0.1s timeout
    sandbox = StrategySandbox(wall_clock_timeout=0.1)

    code = """
def infinite_loop(data):
    # Simulate a stuck/infinite loop strategy
    while True:
        pass
    return data
"""

    response = await sandbox.execute_secure(code, "infinite_loop", (10.0,))
    assert response["success"] is False
    assert "timed out" in response["result"]
