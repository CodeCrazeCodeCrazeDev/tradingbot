def eksft_token_masking(model_probs, ref_probs, entropy_threshold, kl_threshold):
    """
    Entropy-KL Selective Fine-Tuning (EKSFT) Token Masking.

    Args:
        model_probs: Probabilities from the model being fine-tuned (T, V).
        ref_probs: Probabilities from the reference (pre-trained) model (T, V).
        entropy_threshold: \tau_H.
        kl_threshold: \tau_{KL}.

    Returns:
        mask: Boolean mask (T,) where True means the token should be masked (ignored).
    """
    import torch

    # Entropy calculation: H = -sum(p * log(p))
    entropy = -torch.sum(model_probs * torch.log(model_probs + 1e-10), dim=-1)

    # KL Divergence calculation: D_KL(P_ref || P_model)
    kl_div = torch.sum(ref_probs * (torch.log(ref_probs + 1e-10) - torch.log(model_probs + 1e-10)), dim=-1)

    # Selective masking
    mask = (entropy > entropy_threshold) | (kl_div > kl_threshold)

    return mask
