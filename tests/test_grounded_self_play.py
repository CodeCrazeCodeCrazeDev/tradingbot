import pytest
import asyncio
import pandas as pd
from datetime import datetime
from trading_bot.core_agent_system.self_play_loop import SelfPlayLoop

@pytest.mark.asyncio
async def test_self_play_grounded_data():
    loop = SelfPlayLoop()
    # Should automatically generate grounded data if none exists
    game = await loop._play_game()

    assert game.outcome is not None
    assert loop.backtest_engine.data is not None
    assert 'EURUSD' in loop.backtest_engine.data

    # Check if data is grounded (not just a single random number)
    df = loop.backtest_engine.data['EURUSD']
    assert len(df) == 1000
    assert isinstance(df.index, pd.DatetimeIndex)

if __name__ == "__main__":
    asyncio.run(test_self_play_grounded_data())
