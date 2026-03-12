"""Confidence Calibration - Platt/Isotonic Scaling [HI-ANA-019]"""
import numpy as np
import logging
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
import numpy
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)

class ConfidenceCalibrator:
    def __init__(self, method: str = 'isotonic'):
        """method: 'isotonic' or 'platt'"""
        try:
            self.method = method
            self.calibrator = None
            self.is_fitted = False
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def fit(self, y_true: np.ndarray, y_pred_proba: np.ndarray):
        """Fit calibration model on validation data"""
        try:
            if self.method == 'isotonic':
                self.calibrator = IsotonicRegression(out_of_bounds='clip')
                self.calibrator.fit(y_pred_proba, y_true)
            elif self.method == 'platt':
                self.calibrator = LogisticRegression()
                self.calibrator.fit(y_pred_proba.reshape(-1, 1), y_true)
            else:
                raise ValueError(f"Unknown method: {self.method}")
        
            self.is_fitted = True
            logger.info(f"Calibrator fitted using {self.method} method")
        except Exception as e:
            logger.error(f"Error in fit: {e}")
            raise
    
    def calibrate(self, y_pred_proba, context: dict = None):
        """Apply calibration to predictions with optional context adjustment"""
        # Convert to numpy array if needed
        try:
            if isinstance(y_pred_proba, (int, float)):
                y_pred_proba = np.array([y_pred_proba])
                single_value = True
            else:
                y_pred_proba = np.asarray(y_pred_proba)
                single_value = False
        
            # Apply context-based adjustment if provided
            if context and 'news_impact' in context:
                impact = context['news_impact']
                if impact == 'HIGH':
                    # Reduce confidence during high-impact news
                    y_pred_proba = y_pred_proba * 0.7
                elif impact == 'MEDIUM':
                    y_pred_proba = y_pred_proba * 0.85
                # LOW impact: no adjustment
        
            # Apply calibration if fitted
            if self.is_fitted:
                if self.method == 'isotonic':
                    result = self.calibrator.predict(y_pred_proba)
                else:  # platt
                    result = self.calibrator.predict_proba(y_pred_proba.reshape(-1, 1))[:, 1]
            else:
                result = y_pred_proba
        
            # Return single value if input was single value
            return float(result[0]) if single_value else result
        except Exception as e:
            logger.error(f"Error in calibrate: {e}")
            raise
    
    def evaluate_calibration(self, y_true: np.ndarray, y_pred: np.ndarray, n_bins: int = 10):
        """Evaluate calibration quality"""
        try:
            bin_edges = np.linspace(0, 1, n_bins + 1)
            bin_true = []
            bin_pred = []
        
            for i in range(n_bins):
                mask = (y_pred >= bin_edges[i]) & (y_pred < bin_edges[i+1])
                if mask.sum() > 0:
                    bin_true.append(y_true[mask].mean())
                    bin_pred.append(y_pred[mask].mean())
        
            # Calculate calibration error
            if bin_true and bin_pred:
                ece = np.mean(np.abs(np.array(bin_true) - np.array(bin_pred)))
                logger.info(f"Expected Calibration Error: {ece:.4f}")
                return ece
            return None
        except Exception as e:
            logger.error(f"Error in evaluate_calibration: {e}")
            raise
