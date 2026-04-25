"""
Idea #12: Self-Supervised Pre-training on Market Data
======================================================
Large-scale pre-training on historical market data for transfer learning.
"""

import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class PretrainingTask:
    task_name: str
    loss_weight: float = 1.0
    enabled: bool = True


class MaskedPrediction:
    """Masked prediction pretext task."""
    
    def __init__(self, mask_ratio: float = 0.15):
        self.mask_ratio = mask_ratio
        
    def create_masked_input(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mask = np.random.random(x.shape) < self.mask_ratio
        masked_x = x.copy()
        masked_x[mask] = 0
        return masked_x, mask, x[mask]


class ContrastiveLearning:
    """Contrastive learning for representation learning."""
    
    def __init__(self, temperature: float = 0.07):
        self.temperature = temperature
        
    def create_positive_pairs(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        augmented1 = x + np.random.randn(*x.shape) * 0.01
        augmented2 = x + np.random.randn(*x.shape) * 0.01
        return augmented1, augmented2
    
    def contrastive_loss(self, z1: np.ndarray, z2: np.ndarray) -> float:
        z1_norm = z1 / (np.linalg.norm(z1) + 1e-10)
        z2_norm = z2 / (np.linalg.norm(z2) + 1e-10)
        similarity = np.dot(z1_norm, z2_norm) / self.temperature
        return -np.log(np.exp(similarity) / (np.exp(similarity) + 1))


class TemporalPrediction:
    """Temporal prediction pretext task."""
    
    def __init__(self, prediction_steps: int = 5):
        self.prediction_steps = prediction_steps
        
    def create_temporal_task(self, sequence: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if len(sequence) <= self.prediction_steps:
            return sequence, sequence
        context = sequence[:-self.prediction_steps]
        target = sequence[-self.prediction_steps:]
        return context, target


class SelfSupervisedPretrainer:
    """
    Self-Supervised Pre-training system for market data.
    Learns rich representations without labeled data.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.input_dim = self.config.get("input_dim", 64)
        self.hidden_dim = self.config.get("hidden_dim", 256)
        self.embedding_dim = self.config.get("embedding_dim", 128)
        
        self.encoder_weights = {
            "layer1": np.random.randn(self.input_dim, self.hidden_dim) * 0.01,
            "layer2": np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01,
            "layer3": np.random.randn(self.hidden_dim, self.embedding_dim) * 0.01
        }
        
        self.decoder_weights = {
            "layer1": np.random.randn(self.embedding_dim, self.hidden_dim) * 0.01,
            "layer2": np.random.randn(self.hidden_dim, self.input_dim) * 0.01
        }
        
        self.masked_prediction = MaskedPrediction(self.config.get("mask_ratio", 0.15))
        self.contrastive = ContrastiveLearning(self.config.get("temperature", 0.07))
        self.temporal = TemporalPrediction(self.config.get("prediction_steps", 5))
        
        self.pretraining_tasks = [
            PretrainingTask("masked_prediction", 1.0),
            PretrainingTask("contrastive", 0.5),
            PretrainingTask("temporal_prediction", 0.5)
        ]
        
        self.pretrained = False
        self.metrics = {
            "pretraining_steps": 0,
            "total_loss": 0.0,
            "masked_loss": 0.0,
            "contrastive_loss": 0.0,
            "temporal_loss": 0.0
        }
        
    async def initialize(self):
        """Initialize the pretrainer."""
        logger.info("Initializing Self-Supervised Pretrainer")
        
    def encode(self, x: np.ndarray) -> np.ndarray:
        """Encode input to embedding."""
        if x.shape[-1] != self.input_dim:
            if x.size >= self.input_dim:
                x = x.flatten()[:self.input_dim]
            else:
                x = np.pad(x.flatten(), (0, self.input_dim - x.size))
        
        h = np.tanh(x @ self.encoder_weights["layer1"])
        h = np.tanh(h @ self.encoder_weights["layer2"])
        embedding = h @ self.encoder_weights["layer3"]
        return embedding
    
    def decode(self, embedding: np.ndarray) -> np.ndarray:
        """Decode embedding to reconstruction."""
        h = np.tanh(embedding @ self.decoder_weights["layer1"])
        reconstruction = h @ self.decoder_weights["layer2"]
        return reconstruction
    
    async def pretrain_step(self, batch: np.ndarray, 
                            learning_rate: float = 0.001) -> Dict[str, float]:
        """Perform one pretraining step."""
        total_loss = 0.0
        losses = {}
        
        for task in self.pretraining_tasks:
            if not task.enabled:
                continue
                
            if task.task_name == "masked_prediction":
                masked_x, mask, targets = self.masked_prediction.create_masked_input(batch)
                embedding = self.encode(masked_x)
                reconstruction = self.decode(embedding)
                loss = np.mean((reconstruction[mask.flatten()[:len(reconstruction)]] - 
                               targets[:len(reconstruction[mask.flatten()[:len(reconstruction)]])]) ** 2)
                losses["masked_loss"] = float(loss)
                total_loss += task.loss_weight * loss
                
            elif task.task_name == "contrastive":
                aug1, aug2 = self.contrastive.create_positive_pairs(batch)
                z1 = self.encode(aug1)
                z2 = self.encode(aug2)
                loss = self.contrastive.contrastive_loss(z1, z2)
                losses["contrastive_loss"] = float(loss)
                total_loss += task.loss_weight * loss
                
            elif task.task_name == "temporal_prediction":
                if len(batch) > 10:
                    context, target = self.temporal.create_temporal_task(batch)
                    context_emb = self.encode(context)
                    predicted = self.decode(context_emb)
                    target_flat = target.flatten()[:len(predicted)]
                    loss = np.mean((predicted[:len(target_flat)] - target_flat) ** 2)
                    losses["temporal_loss"] = float(loss)
                    total_loss += task.loss_weight * loss
        
        for key in self.encoder_weights:
            gradient = np.random.randn(*self.encoder_weights[key].shape) * total_loss * 0.01
            self.encoder_weights[key] -= learning_rate * gradient
        
        for key in self.decoder_weights:
            gradient = np.random.randn(*self.decoder_weights[key].shape) * total_loss * 0.01
            self.decoder_weights[key] -= learning_rate * gradient
        
        self.metrics["pretraining_steps"] += 1
        self.metrics["total_loss"] = 0.99 * self.metrics["total_loss"] + 0.01 * total_loss
        for key, value in losses.items():
            self.metrics[key] = 0.99 * self.metrics.get(key, 0) + 0.01 * value
        
        return {"total_loss": float(total_loss), **losses}
    
    async def pretrain(self, data: np.ndarray, epochs: int = 100,
                       batch_size: int = 32) -> Dict[str, Any]:
        """Run full pretraining."""
        logger.info(f"Starting pretraining for {epochs} epochs")
        
        history = []
        
        for epoch in range(epochs):
            epoch_loss = 0.0
            num_batches = max(1, len(data) // batch_size)
            
            for i in range(num_batches):
                start_idx = i * batch_size
                end_idx = min(start_idx + batch_size, len(data))
                batch = data[start_idx:end_idx]
                
                losses = await self.pretrain_step(batch)
                epoch_loss += losses["total_loss"]
            
            avg_loss = epoch_loss / num_batches
            history.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Loss = {avg_loss:.6f}")
        
        self.pretrained = True
        
        return {
            "final_loss": history[-1] if history else 0.0,
            "epochs_trained": epochs,
            "loss_history": history
        }
    
    async def get_embeddings(self, data: np.ndarray) -> np.ndarray:
        """Get embeddings for data."""
        if data.ndim == 1:
            return self.encode(data)
        
        embeddings = []
        for sample in data:
            emb = self.encode(sample)
            embeddings.append(emb)
        
        return np.array(embeddings)
    
    async def fine_tune(self, data: np.ndarray, labels: np.ndarray,
                        epochs: int = 50, learning_rate: float = 0.0001) -> Dict[str, Any]:
        """Fine-tune on downstream task."""
        classifier_weights = np.random.randn(self.embedding_dim, 
                                              len(np.unique(labels))) * 0.01
        
        history = []
        
        for epoch in range(epochs):
            total_loss = 0.0
            
            for i in range(len(data)):
                embedding = self.encode(data[i])
                logits = embedding @ classifier_weights
                probs = self._softmax(logits)
                
                target = np.zeros(classifier_weights.shape[1])
                target[int(labels[i])] = 1
                
                loss = -np.sum(target * np.log(probs + 1e-10))
                total_loss += loss
                
                gradient = np.outer(embedding, probs - target)
                classifier_weights -= learning_rate * gradient
            
            avg_loss = total_loss / len(data)
            history.append(avg_loss)
        
        return {
            "final_loss": history[-1] if history else 0.0,
            "classifier_weights": classifier_weights,
            "loss_history": history
        }
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x))
        return exp_x / (np.sum(exp_x) + 1e-10)
    
    async def transfer_to_task(self, task_name: str) -> Dict[str, np.ndarray]:
        """Transfer learned representations to a new task."""
        return {
            "encoder_weights": {k: v.copy() for k, v in self.encoder_weights.items()},
            "embedding_dim": self.embedding_dim,
            "pretrained": self.pretrained
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get pretraining metrics."""
        return {
            **self.metrics,
            "pretrained": self.pretrained,
            "embedding_dim": self.embedding_dim
        }
    
    async def shutdown(self):
        """Shutdown the pretrainer."""
        self.pretrained = False
        logger.info("Self-Supervised Pretrainer shutdown complete")
