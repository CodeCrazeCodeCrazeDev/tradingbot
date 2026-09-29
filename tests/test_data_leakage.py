import unittest
import numpy as np
import pandas as pd
from trading_bot.ml.predictive_models import PricePredictor

class TestDataLeakage(unittest.TestCase):
    def test_no_lookahead_bias_in_prepare_features(self):
        """
        Verify that modifying future price data does not affect historical features.
        This is a robust scientific check for data leakage/lookahead bias.
        """
        predictor = PricePredictor()

        # Base historical data
        np.random.seed(42)
        prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, 100))

        df1 = pd.DataFrame({
            'open': prices - 0.5,
            'high': prices + 0.5,
            'low': prices - 0.5,
            'close': prices,
            'volume': [1000] * 100
        })

        # Duplicate dataframe but change the very last (future) price
        df2 = df1.copy()
        df2.loc[df2.index[-1], 'close'] = df2.loc[df2.index[-1], 'close'] + 50.0  # Massive future shock

        # Prepare features for both
        X1 = predictor.prepare_features(df1)
        X2 = predictor.prepare_features(df2)

        # The features for all bars EXCEPT the last one should be identical
        # (Since future price should not affect past indicators)
        np.testing.assert_array_almost_equal(
            X1[:-1],
            X2[:-1],
            decimal=5,
            err_msg="CRITICAL: Lookahead bias detected! Modifying future close price changed past features."
        )

if __name__ == '__main__':
    unittest.main()
