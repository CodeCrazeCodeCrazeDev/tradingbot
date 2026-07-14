
import torch
import torch.nn as nn
from trading_bot.learning.eksft import EKSFTTrainer

class SimpleLM(nn.Module):
    def __init__(self, vocab_size, dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, dim)
        self.linear = nn.Linear(dim, vocab_size)

    def forward(self, x):
        h = self.embedding(x)
        logits = self.linear(h)
        # Mock class with .logits for compatibility
        class Output:
            def __init__(self, l): self.logits = l
        return Output(logits)

def test_eksft_masking():
    vocab_size = 10
    dim = 8
    model = SimpleLM(vocab_size, dim)
    ref_model = SimpleLM(vocab_size, dim)

    trainer = EKSFTTrainer(model, ref_model, entropy_tau=1.5, kl_tau=0.1)

    input_ids = torch.LongTensor([[1, 2, 3]])
    labels = torch.LongTensor([[2, 3, 4]])

    loss = trainer.compute_selective_loss(input_ids, labels)
    assert loss >= 0
    print(f"EKSFT Loss: {loss.item()}")

if __name__ == "__main__":
    test_eksft_masking()
    print("EKSFT Test PASSED")
