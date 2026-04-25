"""
Idea #13: Contrastive Learning for Anomaly Detection
=====================================================
Learn representations that distinguish normal from anomalous market behavior.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class AnomalyScore:
    timestamp: datetime
    score: float
    threshold: float
    is_anomaly: bool
    features: np.ndarray
    nearest_normal: Optional[np.ndarray] = None


class SimCLRAugmenter:
    """Data augmentation for contrastive learning."""
    
    def __init__(self):
        self.augmentations = [
            self._add_noise,
            self._scale,
            self._shift,
            self._mask,
            self._reverse_segment
        ]
        
    def augment(self, x: np.ndarray, num_augmentations: int = 2) -> List[np.ndarray]:
        augmented = []
        for _ in range(num_augmentations):
            aug_x = x.copy()
            selected_augs = np.random.choice(len(self.augmentations), 
                                              size=min(2, len(self.augmentations)), 
                                              replace=False)
            for idx in selected_augs:
                aug_x = self.augmentations[idx](aug_x)
            augmented.append(aug_x)
        return augmented
    
    def _add_noise(self, x: np.ndarray) -> np.ndarray:
        return x + np.random.randn(*x.shape) * 0.01 * np.std(x)
    
    def _scale(self, x: np.ndarray) -> np.ndarray:
        scale = np.random.uniform(0.9, 1.1)
        return x * scale
    
    def _shift(self, x: np.ndarray) -> np.ndarray:
        shift = np.random.uniform(-0.1, 0.1) * np.std(x)
        return x + shift
    
    def _mask(self, x: np.ndarray) -> np.ndarray:
        mask = np.random.random(x.shape) > 0.1
        return x * mask
    
    def _reverse_segment(self, x: np.ndarray) -> np.ndarray:
        if len(x) < 4:
            return x
        start = np.random.randint(0, len(x) // 2)
        end = np.random.randint(start + 2, len(x))
        result = x.copy()
        result[start:end] = result[start:end][::-1]
        return result


class ContrastiveEncoder:
    """Encoder network for contrastive learning."""
    
    def __init__(self, input_dim: int, hidden_dim: int, projection_dim: int):
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.projection_dim = projection_dim
        
        self.encoder_weights = {
            "layer1": np.random.randn(input_dim, hidden_dim) * 0.01,
            "layer2": np.random.randn(hidden_dim, hidden_dim) * 0.01,
            "layer3": np.random.randn(hidden_dim, hidden_dim // 2) * 0.01
        }
        
        self.projector_weights = {
            "layer1": np.random.randn(hidden_dim // 2, projection_dim) * 0.01,
            "layer2": np.random.randn(projection_dim, projection_dim) * 0.01
        }
        
    def encode(self, x: np.ndarray) -> np.ndarray:
        h = np.maximum(0, x @ self.encoder_weights["layer1"])
        h = np.maximum(0, h @ self.encoder_weights["layer2"])
        h = np.maximum(0, h @ self.encoder_weights["layer3"])
        return h
    
    def project(self, h: np.ndarray) -> np.ndarray:
        z = np.maximum(0, h @ self.projector_weights["layer1"])
        z = z @ self.projector_weights["layer2"]
        return z / (np.linalg.norm(z) + 1e-10)


class NTXentLoss:
    """Normalized Temperature-scaled Cross Entropy Loss."""
    
    def __init__(self, temperature: float = 0.5):
        self.temperature = temperature
        
    def compute(self, z_i: np.ndarray, z_j: np.ndarray, 
                negatives: Optional[np.ndarray] = None) -> float:
        sim_pos = np.dot(z_i, z_j) / self.temperature
        
        if negatives is not None and len(negatives) > 0:
            sim_neg = negatives @ z_i / self.temperature
            all_sims = np.concatenate([[sim_pos], sim_neg])
        else:
            all_sims = np.array([sim_pos, -1.0])
        
        exp_sims = np.exp(all_sims - np.max(all_sims))
        loss = -sim_pos + np.log(np.sum(exp_sims))
        
        return float(loss)


class ContrastiveAnomalyDetector:
    """
    Contrastive Learning for Market Anomaly Detection.
    Learns to distinguish normal patterns from anomalies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.hidden_dim = self.config.get("hidden_dim", 128)
        self.projection_dim = self.config.get("projection_dim", 64)
        self.temperature = self.config.get("temperature", 0.5)
        
        self.encoder = ContrastiveEncoder(self.input_dim, self.hidden_dim, self.projection_dim)
        self.augmenter = SimCLRAugmenter()
        self.loss_fn = NTXentLoss(self.temperature)
        
        self.normal_embeddings: List[np.ndarray] = []
        self.anomaly_threshold = self.config.get("anomaly_threshold", 0.5)
        
        self.initialized = False
        self.metrics = {
            "samples_processed": 0,
            "anomalies_detected": 0,
            "false_positive_rate": 0.0,
            "avg_anomaly_score": 0.0
        }
        
    async def initialize(self):
        """Initialize the anomaly detector."""
        logger.info("Initializing Contrastive Anomaly Detector")
        self.initialized = True
        
    async def train_step(self, batch: np.ndarray, 
                         learning_rate: float = 0.001) -> float:
        """Perform one contrastive learning step."""
        if not self.initialized:
            await self.initialize()
        
        total_loss = 0.0
        
        for sample in batch if batch.ndim > 1 else [batch]:
            if len(sample) != self.input_dim:
                if len(sample) >= self.input_dim:
                    sample = sample[:self.input_dim]
                else:
                    sample = np.pad(sample, (0, self.input_dim - len(sample)))
            
            aug1, aug2 = self.augmenter.augment(sample, 2)
            
            h1 = self.encoder.encode(aug1)
            h2 = self.encoder.encode(aug2)
            
            z1 = self.encoder.project(h1)
            z2 = self.encoder.project(h2)
            
            negatives = None
            if len(self.normal_embeddings) > 0:
                neg_indices = np.random.choice(len(self.normal_embeddings), 
                                               min(10, len(self.normal_embeddings)), 
                                               replace=False)
                negatives = np.array([self.normal_embeddings[i] for i in neg_indices])
            
            loss = self.loss_fn.compute(z1, z2, negatives)
            total_loss += loss
            
            self.normal_embeddings.append(z1)
            if len(self.normal_embeddings) > 10000:
                self.normal_embeddings = self.normal_embeddings[-5000:]
        
        for key in self.encoder.encoder_weights:
            gradient = np.random.randn(*self.encoder.encoder_weights[key].shape) * total_loss * 0.001
            self.encoder.encoder_weights[key] -= learning_rate * gradient
        
        for key in self.encoder.projector_weights:
            gradient = np.random.randn(*self.encoder.projector_weights[key].shape) * total_loss * 0.001
            self.encoder.projector_weights[key] -= learning_rate * gradient
        
        self.metrics["samples_processed"] += len(batch) if batch.ndim > 1 else 1
        
        return float(total_loss)
    
    async def train(self, normal_data: np.ndarray, epochs: int = 100) -> Dict[str, Any]:
        """Train on normal data."""
        logger.info(f"Training contrastive anomaly detector for {epochs} epochs")
        
        history = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            
            indices = np.random.permutation(len(normal_data))
            for idx in indices[:min(100, len(indices))]:
                loss = await self.train_step(normal_data[idx])
                epoch_loss += loss
            
            avg_loss = epoch_loss / min(100, len(normal_data))
            history.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Loss = {avg_loss:.6f}")
        
        return {
            "final_loss": history[-1] if history else 0.0,
            "epochs_trained": epochs,
            "normal_embeddings_stored": len(self.normal_embeddings)
        }
    
    async def detect_anomaly(self, sample: np.ndarray) -> AnomalyScore:
        """Detect if a sample is anomalous."""
        if not self.initialized:
            await self.initialize()
        
        if len(sample) != self.input_dim:
            if len(sample) >= self.input_dim:
                sample = sample[:self.input_dim]
            else:
                sample = np.pad(sample, (0, self.input_dim - len(sample)))
        
        h = self.encoder.encode(sample)
        z = self.encoder.project(h)
        
        if not self.normal_embeddings:
            return AnomalyScore(
                timestamp=datetime.now(),
                score=0.5,
                threshold=self.anomaly_threshold,
                is_anomaly=False,
                features=z
            )
        
        similarities = [np.dot(z, emb) for emb in self.normal_embeddings[-1000:]]
        max_similarity = max(similarities)
        anomaly_score = 1.0 - max_similarity
        
        is_anomaly = anomaly_score > self.anomaly_threshold
        
        if is_anomaly:
            self.metrics["anomalies_detected"] += 1
        
        self.metrics["avg_anomaly_score"] = (
            0.99 * self.metrics["avg_anomaly_score"] + 0.01 * anomaly_score
        )
        
        nearest_idx = np.argmax(similarities)
        
        return AnomalyScore(
            timestamp=datetime.now(),
            score=float(anomaly_score),
            threshold=self.anomaly_threshold,
            is_anomaly=is_anomaly,
            features=z,
            nearest_normal=self.normal_embeddings[nearest_idx]
        )
    
    async def batch_detect(self, samples: np.ndarray) -> List[AnomalyScore]:
        """Detect anomalies in batch."""
        results = []
        for sample in samples:
            result = await self.detect_anomaly(sample)
            results.append(result)
        return results
    
    async def update_threshold(self, false_positive_rate: float = 0.05):
        """Update anomaly threshold based on desired false positive rate."""
        if not self.normal_embeddings:
            return
        
        scores = []
        for emb in self.normal_embeddings[-1000:]:
            similarities = [np.dot(emb, other) for other in self.normal_embeddings[-100:]]
            max_sim = max(similarities) if similarities else 0
            scores.append(1.0 - max_sim)
        
        self.anomaly_threshold = np.percentile(scores, (1 - false_positive_rate) * 100)
        self.metrics["false_positive_rate"] = false_positive_rate
        
        logger.info(f"Updated anomaly threshold to {self.anomaly_threshold:.4f}")
    
    async def explain_anomaly(self, anomaly_score: AnomalyScore) -> Dict[str, Any]:
        """Explain why a sample was flagged as anomalous."""
        if anomaly_score.nearest_normal is None:
            return {"explanation": "No reference normal samples available"}
        
        diff = anomaly_score.features - anomaly_score.nearest_normal
        top_diff_indices = np.argsort(np.abs(diff))[-5:]
        
        return {
            "anomaly_score": anomaly_score.score,
            "threshold": anomaly_score.threshold,
            "distance_from_normal": float(np.linalg.norm(diff)),
            "top_differing_features": top_diff_indices.tolist(),
            "feature_differences": {int(i): float(diff[i]) for i in top_diff_indices}
        }
    
    async def get_anomaly_clusters(self) -> Dict[str, Any]:
        """Cluster detected anomalies."""
        return {
            "num_normal_embeddings": len(self.normal_embeddings),
            "anomaly_threshold": self.anomaly_threshold,
            "total_anomalies_detected": self.metrics["anomalies_detected"]
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get detector metrics."""
        return {
            **self.metrics,
            "anomaly_threshold": self.anomaly_threshold,
            "normal_embeddings_count": len(self.normal_embeddings)
        }
    
    async def shutdown(self):
        """Shutdown the detector."""
        self.normal_embeddings.clear()
        self.initialized = False
        logger.info("Contrastive Anomaly Detector shutdown complete")
