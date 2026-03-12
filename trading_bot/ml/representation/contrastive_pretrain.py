"""
Contrastive Learning for Time-Series Representations (TS-TCC)

Self-supervised pretraining on unlabeled tick data to learn robust features.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class TimeSeriesEncoder(nn.Module):
    """1D CNN encoder for time series"""
    
    def __init__(self, input_channels: int = 1, hidden_dim: int = 128, output_dim: int = 128):
        try:
            super().__init__()
        
            self.conv_layers = nn.Sequential(
                nn.Conv1d(input_channels, 32, kernel_size=7, padding=3),
                nn.BatchNorm1d(32),
                nn.ReLU(),
                nn.MaxPool1d(2),
            
                nn.Conv1d(32, 64, kernel_size=5, padding=2),
                nn.BatchNorm1d(64),
                nn.ReLU(),
                nn.MaxPool1d(2),
            
                nn.Conv1d(64, hidden_dim, kernel_size=3, padding=1),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.AdaptiveAvgPool1d(1)
            )
        
            self.projection_head = nn.Sequential(
                nn.Linear(hidden_dim, hidden_dim),
                nn.ReLU(),
                nn.Linear(hidden_dim, output_dim)
            )
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forward(self, x):
        # x: [batch, channels, length]
        try:
            features = self.conv_layers(x)
            features = features.squeeze(-1)
            embeddings = self.projection_head(features)
            return embeddings
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise


class TimeSeriesAugmentation:
    """Data augmentation for time series"""
    
    @staticmethod
    def jitter(x: torch.Tensor, sigma: float = 0.03) -> torch.Tensor:
        """Add Gaussian noise"""
        try:
            noise = torch.randn_like(x) * sigma
            return x + noise
        except Exception as e:
            logger.error(f"Error in jitter: {e}")
            raise
    
    @staticmethod
    def scaling(x: torch.Tensor, sigma: float = 0.1) -> torch.Tensor:
        """Scale by random factor"""
        try:
            factor = torch.randn(x.size(0), 1, 1, device=x.device) * sigma + 1.0
            return x * factor
        except Exception as e:
            logger.error(f"Error in scaling: {e}")
            raise
    
    @staticmethod
    def time_warp(x: torch.Tensor, sigma: float = 0.2) -> torch.Tensor:
        """Time warping (stretch/compress)"""
        try:
            batch_size, channels, length = x.shape
        
            # Generate random warp
            orig_steps = torch.arange(length, dtype=torch.float32)
            warp = torch.randn(length) * sigma
            warped_steps = orig_steps + warp
            warped_steps = torch.clamp(warped_steps, 0, length - 1)
        
            # Interpolate
            warped_x = torch.zeros_like(x)
            for b in range(batch_size):
                for c in range(channels):
                    warped_x[b, c] = torch.from_numpy(
                        np.interp(orig_steps.numpy(), warped_steps.numpy(), x[b, c].cpu().numpy())
                    ).to(x.device)
        
            return warped_x
        except Exception as e:
            logger.error(f"Error in time_warp: {e}")
            raise
    
    @staticmethod
    def window_slice(x: torch.Tensor, slice_ratio: float = 0.9) -> torch.Tensor:
        """Random window slicing"""
        try:
            batch_size, channels, length = x.shape
            slice_length = int(length * slice_ratio)
        
            start_idx = torch.randint(0, length - slice_length + 1, (1,)).item()
            return x[:, :, start_idx:start_idx + slice_length]
        except Exception as e:
            logger.error(f"Error in window_slice: {e}")
            raise
    
    @staticmethod
    def augment(x: torch.Tensor, methods: list = None) -> torch.Tensor:
        """Apply random augmentation"""
        try:
            if methods is None:
                methods = ['jitter', 'scaling']
        
            aug_method = np.random.choice(methods)
        
            if aug_method == 'jitter':
                return TimeSeriesAugmentation.jitter(x)
            elif aug_method == 'scaling':
                return TimeSeriesAugmentation.scaling(x)
            elif aug_method == 'time_warp':
                return TimeSeriesAugmentation.time_warp(x)
            elif aug_method == 'window_slice':
                return TimeSeriesAugmentation.window_slice(x)
            else:
                return x
        except Exception as e:
            logger.error(f"Error in augment: {e}")
            raise


class ContrastiveLoss(nn.Module):
    """NT-Xent (Normalized Temperature-scaled Cross Entropy) Loss"""
    
    def __init__(self, temperature: float = 0.5):
        try:
            super().__init__()
            self.temperature = temperature
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def forward(self, z1: torch.Tensor, z2: torch.Tensor) -> torch.Tensor:
        """
        Compute contrastive loss
        
        Args:
            z1: Embeddings from view 1 [batch, dim]
            z2: Embeddings from view 2 [batch, dim]
            
        Returns:
            Contrastive loss
        """
        try:
            batch_size = z1.size(0)
        
            # Normalize embeddings
            z1 = F.normalize(z1, dim=1)
            z2 = F.normalize(z2, dim=1)
        
            # Concatenate
            z = torch.cat([z1, z2], dim=0)  # [2*batch, dim]
        
            # Compute similarity matrix
            sim_matrix = torch.mm(z, z.t()) / self.temperature  # [2*batch, 2*batch]
        
            # Create labels (positive pairs)
            labels = torch.arange(batch_size, device=z.device)
            labels = torch.cat([labels + batch_size, labels])
        
            # Mask out self-similarity
            mask = torch.eye(2 * batch_size, device=z.device).bool()
            sim_matrix.masked_fill_(mask, -9e15)
        
            # Compute loss
            loss = F.cross_entropy(sim_matrix, labels)
        
            return loss
        except Exception as e:
            logger.error(f"Error in forward: {e}")
            raise


class ContrastivePretrainer:
    """
    Contrastive pretraining pipeline
    
    Process:
    1. Load unlabeled tick data
    2. Create augmented views
    3. Train encoder with contrastive loss
    4. Save pretrained encoder
    """
    
    def __init__(
        self,
        encoder: TimeSeriesEncoder,
        temperature: float = 0.5,
        learning_rate: float = 1e-3
    ):
        try:
            self.encoder = encoder
            self.criterion = ContrastiveLoss(temperature)
            self.optimizer = torch.optim.Adam(encoder.parameters(), lr=learning_rate)
            self.augmentation = TimeSeriesAugmentation()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def pretrain_step(self, batch: torch.Tensor) -> float:
        """Single pretraining step"""
        # Create two augmented views
        try:
            view1 = self.augmentation.augment(batch)
            view2 = self.augmentation.augment(batch)
        
            # Encode both views
            z1 = self.encoder(view1)
            z2 = self.encoder(view2)
        
            # Compute contrastive loss
            loss = self.criterion(z1, z2)
        
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
        
            return loss.item()
        except Exception as e:
            logger.error(f"Error in pretrain_step: {e}")
            raise
    
    def pretrain(
        self,
        data_loader,
        epochs: int = 100,
        device: str = 'cpu'
    ) -> dict:
        """
        Pretrain encoder
        
        Args:
            data_loader: DataLoader with unlabeled time series
            epochs: Number of epochs
            device: Device to train on
            
        Returns:
            Training history
        """
        try:
            self.encoder.to(device)
            history = {'loss': []}
        
            for epoch in range(epochs):
                epoch_loss = 0.0
                n_batches = 0
            
                for batch in data_loader:
                    batch = batch.to(device)
                    loss = self.pretrain_step(batch)
                    epoch_loss += loss
                    n_batches += 1
            
                avg_loss = epoch_loss / n_batches
                history['loss'].append(avg_loss)
            
                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}")
        
            return history
        except Exception as e:
            logger.error(f"Error in pretrain: {e}")
            raise
    
    def save_encoder(self, path: str):
        """Save pretrained encoder"""
        try:
            torch.save(self.encoder.state_dict(), path)
            logger.info(f"Encoder saved to {path}")
        except Exception as e:
            logger.error(f"Error in save_encoder: {e}")
            raise
    
    def load_encoder(self, path: str):
        """Load pretrained encoder"""
        try:
            self.encoder.load_state_dict(torch.load(path))
            logger.info(f"Encoder loaded from {path}")
        except Exception as e:
            logger.error(f"Error in load_encoder: {e}")
            raise


class FineTuner:
    """Fine-tune pretrained encoder for downstream tasks"""
    
    def __init__(
        self,
        encoder: TimeSeriesEncoder,
        num_classes: int = 3,
        freeze_encoder: bool = True,
        learning_rate: float = 1e-4
    ):
        try:
            self.encoder = encoder
            self.freeze_encoder = freeze_encoder
        
            # Freeze encoder if specified
            if freeze_encoder:
                for param in encoder.parameters():
                    param.requires_grad = False
        
            # Add classification head
            self.classifier = nn.Linear(encoder.projection_head[-1].out_features, num_classes)
        
            # Optimizer
            params = list(self.classifier.parameters())
            if not freeze_encoder:
                params += list(encoder.parameters())
            self.optimizer = torch.optim.Adam(params, lr=learning_rate)
        
            self.criterion = nn.CrossEntropyLoss()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def finetune_step(
        self,
        features: torch.Tensor,
        labels: torch.Tensor
    ) -> float:
        """Single fine-tuning step"""
        # Encode
        try:
            embeddings = self.encoder(features)
        
            # Classify
            logits = self.classifier(embeddings)
        
            # Compute loss
            loss = self.criterion(logits, labels)
        
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
        
            return loss.item()
        except Exception as e:
            logger.error(f"Error in finetune_step: {e}")
            raise
    
    def finetune(
        self,
        train_loader,
        val_loader,
        epochs: int = 50,
        device: str = 'cpu'
    ) -> dict:
        """Fine-tune on labeled data"""
        try:
            self.encoder.to(device)
            self.classifier.to(device)
        
            history = {'train_loss': [], 'val_loss': [], 'val_acc': []}
        
            for epoch in range(epochs):
                # Training
                self.encoder.train()
                self.classifier.train()
                train_loss = 0.0
                n_batches = 0
            
                for features, labels in train_loader:
                    features, labels = features.to(device), labels.to(device)
                    loss = self.finetune_step(features, labels)
                    train_loss += loss
                    n_batches += 1
            
                train_loss /= n_batches
                history['train_loss'].append(train_loss)
            
                # Validation
                val_loss, val_acc = self.validate(val_loader, device)
                history['val_loss'].append(val_loss)
                history['val_acc'].append(val_acc)
            
                if (epoch + 1) % 10 == 0:
                    logger.info(
                        f"Epoch {epoch+1}/{epochs} - "
                        f"Train Loss: {train_loss:.4f}, "
                        f"Val Loss: {val_loss:.4f}, "
                        f"Val Acc: {val_acc:.2%}"
                    )
        
            return history
        except Exception as e:
            logger.error(f"Error in finetune: {e}")
            raise
    
    def validate(self, val_loader, device: str) -> Tuple[float, float]:
        """Validate model"""
        try:
            self.encoder.eval()
            self.classifier.eval()
        
            total_loss = 0.0
            correct = 0
            total = 0
        
            with torch.no_grad():
                for features, labels in val_loader:
                    features, labels = features.to(device), labels.to(device)
                
                    embeddings = self.encoder(features)
                    logits = self.classifier(embeddings)
                
                    loss = self.criterion(logits, labels)
                    total_loss += loss.item()
                
                    predictions = logits.argmax(dim=1)
                    correct += (predictions == labels).sum().item()
                    total += labels.size(0)
        
            avg_loss = total_loss / len(val_loader)
            accuracy = correct / total
        
            return avg_loss, accuracy
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create encoder
    encoder = TimeSeriesEncoder(input_channels=1, hidden_dim=128, output_dim=128)
    
    # Create sample unlabeled data
    logger.info("Creating sample data...")
    unlabeled_data = torch.randn(1000, 1, 168)  # 1000 samples, 1 channel, 168 timesteps
    
    # Create data loader
    from torch.utils.data import TensorDataset, DataLoader
    dataset = TensorDataset(unlabeled_data)
    data_loader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    # Pretrain
    logger.info("Pretraining encoder...")
    pretrainer = ContrastivePretrainer(encoder, temperature=0.5, learning_rate=1e-3)
    history = pretrainer.pretrain(data_loader, epochs=50)
    
    # Create labeled data for fine-tuning
    logger.info("\nFine-tuning on labeled data...")
    labeled_features = torch.randn(500, 1, 168)
    labeled_targets = torch.randint(0, 3, (500,))
    
    train_dataset = TensorDataset(labeled_features[:400], labeled_targets[:400])
    val_dataset = TensorDataset(labeled_features[400:], labeled_targets[400:])
    
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32)
    
    # Fine-tune
    finetuner = FineTuner(encoder, num_classes=3, freeze_encoder=True)
    ft_history = finetuner.finetune(train_loader, val_loader, epochs=30)
    
    print("\n" + "="*60)
    logger.info("CONTRASTIVE LEARNING COMPLETE!")
    print("="*60)
    logger.info(f"Pretraining final loss: {history['loss'][-1]:.4f}")
    logger.info(f"Fine-tuning final val acc: {ft_history['val_acc'][-1]:.2%}")
    print("="*60)
