import torch
import unittest
import numpy as np
from trading_bot.ml.transformer_model import TimeSeriesTransformer as TSTModel
from trading_bot.ml.transformer_forecaster import TimeSeriesTransformer as TSTForecaster

class TestTimeSeriesTransformerRecurrent(unittest.TestCase):
    def test_tst_model_forward(self):
        input_dim = 10
        d_model = 32
        model = TSTModel(input_dim=input_dim, d_model=d_model, num_layers=2)
        x = torch.randn(4, 20, input_dim)
        output = model(x)
        self.assertEqual(output.shape, (4, 1))

    def test_tst_forecaster_forward(self):
        input_dim = 5
        forecast_horizon = 3
        model = TSTForecaster(
            input_dim=input_dim,
            d_model=16,
            num_encoder_layers=2,
            num_decoder_layers=2,
            forecast_horizon=forecast_horizon
        )
        src = torch.randn(2, 10, input_dim)
        # Teacher forcing
        tgt = torch.randn(2, forecast_horizon, input_dim)
        pred, uncertainty = model(src, tgt)
        self.assertEqual(pred.shape, (2, forecast_horizon))
        self.assertEqual(uncertainty.shape, (2, forecast_horizon))

if __name__ == "__main__":
    unittest.main()
