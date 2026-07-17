import unittest
import numpy as np
from trading_bot.ml.offline_rl.replay_buffer import ReplayBuffer

class TestReplayBufferProvenance(unittest.TestCase):
    def test_missing_provenance_raises_value_error(self):
        buffer = ReplayBuffer(capacity=10)
        state = np.array([1, 2, 3])
        next_state = np.array([4, 5, 6])

        # Missing provenance completely
        with self.assertRaises(ValueError):
            buffer.push(state, 1, 0.5, next_state, False, info={})

    def test_complete_provenance_succeeds(self):
        buffer = ReplayBuffer(capacity=10)
        state = np.array([1, 2, 3])
        next_state = np.array([4, 5, 6])

        info = {
            'source': 'live_execution',
            'timestamp': '2026-01-28T12:00:00',
            'symbol': 'BTCUSDT',
            'execution_type': 'limit',
            'slippage': 0.0001,
            'commission': 0.001,
            'market_regime': 'bull_trend'
        }

        buffer.push(state, 1, 0.5, next_state, False, info=info)
        self.assertEqual(len(buffer), 1)

if __name__ == '__main__':
    unittest.main()
