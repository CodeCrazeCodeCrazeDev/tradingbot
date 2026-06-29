import torch
import unittest
from trading_bot.ml.recurrent_transformer import RecurrentDepthTransformerBase

class TestRecurrentTransformer(unittest.TestCase):
    def test_fixed_depth_forward(self):
        d_model = 64
        nhead = 4
        dim_feedforward = 128
        depth = 3

        model = RecurrentDepthTransformerBase(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            recurrent_depth=depth,
            use_act=False
        )

        batch_size = 2
        seq_len = 10
        x = torch.randn(batch_size, seq_len, d_model)

        output, stats = model(x)

        self.assertEqual(output.shape, (batch_size, seq_len, d_model))
        self.assertEqual(stats['actual_depth'], depth)

    def test_act_forward(self):
        d_model = 64
        nhead = 4
        dim_feedforward = 128
        max_depth = 10

        model = RecurrentDepthTransformerBase(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            max_depth=max_depth,
            use_act=True
        )

        batch_size = 2
        seq_len = 10
        x = torch.randn(batch_size, seq_len, d_model)

        output, stats = model(x)

        self.assertEqual(output.shape, (batch_size, seq_len, d_model))
        self.assertTrue(stats['actual_depth'] <= max_depth)
        self.assertTrue('mean_steps' in stats)

if __name__ == "__main__":
    unittest.main()
