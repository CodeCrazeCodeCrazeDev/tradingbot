import numpy as np
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

class CalibrationMonitor:
    """Monitors Expected Calibration Error (ECE) of system predictions."""
    def __init__(self, n_bins: int = 10):
        self.n_bins = n_bins
        self.predictions = []
        self.outcomes = []

    def record_prediction(self, confidence: float, correct: bool):
        self.predictions.append(confidence)
        self.outcomes.append(float(correct))

    def calculate_ece(self) -> float:
        if not self.predictions: return 0.0

        preds = np.array(self.predictions)
        labels = np.array(self.outcomes)

        bin_boundaries = np.linspace(0, 1, self.n_bins + 1)
        ece = 0
        for i in range(self.n_bins):
            mask = (preds > bin_boundaries[i]) & (preds <= bin_boundaries[i+1])
            if np.any(mask):
                bin_acc = np.mean(labels[mask])
                bin_conf = np.mean(preds[mask])
                ece += np.abs(bin_acc - bin_conf) * np.sum(mask) / len(preds)

        return float(ece)
