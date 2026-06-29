import torch
import unittest
from trading_bot.alpha_engine.deep_learning import TransformerPricePredictor

class TestTransformerPricePredictorRecurrent(unittest.TestCase):
    def test_forward_pass(self):
        input_size = 32
        d_model = 64
        nhead = 4
        num_layers = 3
        num_classes = 3

        model = TransformerPricePredictor(
            input_size=input_size,
            d_model=d_model,
            nhead=nhead,
            num_layers=num_layers,
            num_classes=num_classes
        )

        batch_size = 4
        seq_len = 20
        x = torch.randn(batch_size, seq_len, input_size)

        probs, confidence = model(x)

        self.assertEqual(probs.shape, (batch_size, num_classes))
        self.assertEqual(confidence.shape, (batch_size, 1))
        # Probs should sum to 1
        self.assertTrue(torch.allclose(probs.sum(dim=1), torch.ones(batch_size)))

if __name__ == "__main__":
    unittest.main()
