import unittest
import numpy as np
import pandas as pd
from trading_bot.ml.reinforcement import StrategyOptimizer
from trading_bot.ml.eval_states import EvaluationState

class TestDelusionLoopPrevention(unittest.TestCase):
    def test_invalid_evaluation_state_prevents_training(self):
        optimizer = StrategyOptimizer()
        optimizer.state_history = []

        # DataFrame with sufficient varying rows
        df = pd.DataFrame({
            'open': [100.0 + i for i in range(50)],
            'high': [102.0 + i for i in range(50)],
            'low': [98.0 + i for i in range(50)],
            'close': [100.0 + i for i in range(50)]
        })

        result = optimizer.train(df, epochs=5)
        self.assertFalse(result['success'])
        self.assertIn('Invalid evaluation state', result['error'])

    def test_invalid_evaluation_state_forces_zero_reward(self):
        optimizer = StrategyOptimizer()
        optimizer.state_history = []

        # Attempt to calculate reward - should fail-closed and return 0.0
        reward = optimizer.calculate_reward(action=1, next_state=np.array([1,2,3]), price_change=0.05)
        self.assertEqual(reward, 0.0)

if __name__ == '__main__':
    unittest.main()
