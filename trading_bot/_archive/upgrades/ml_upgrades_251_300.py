"""
ML/AI Upgrades 251-300
"""
import numpy as np
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum, auto
from collections import deque

# UPGRADE 251: Anomaly Detection Model
class AnomalyDetectionModel:
    def __init__(self, threshold: float = 2.5):
        self.threshold = threshold
        self.mean = 0
        self.std = 1
        
    def fit(self, data: List[float]):
        self.mean = np.mean(data)
        self.std = np.std(data) or 1
        
    def predict(self, x: float) -> bool:
        z_score = abs(x - self.mean) / self.std
        return z_score > self.threshold
    
    def get_score(self, x: float) -> float:
        return abs(x - self.mean) / self.std

# UPGRADE 252: Isolation Forest
class IsolationForest:
    def __init__(self, n_trees: int = 100, sample_size: int = 256):
        self.n_trees = n_trees
        self.sample_size = sample_size
        self.trees: List[Dict] = []
        
    def fit(self, data: List[List[float]]):
        for _ in range(self.n_trees):
            sample_idx = np.random.choice(len(data), min(self.sample_size, len(data)), replace=False)
            sample = [data[i] for i in sample_idx]
            self.trees.append(self._build_tree(sample, 0))
            
    def _build_tree(self, data: List[List[float]], depth: int, max_depth: int = 10) -> Dict:
        if depth >= max_depth or len(data) <= 1:
            return {'type': 'leaf', 'size': len(data)}
        feature = np.random.randint(len(data[0]))
        values = [d[feature] for d in data]
        split = np.random.uniform(min(values), max(values))
        return {'type': 'node', 'feature': feature, 'split': split, 'depth': depth}
    
    def predict(self, x: List[float]) -> float:
        depths = [self._get_depth(tree, x) for tree in self.trees]
        avg_depth = np.mean(depths)
        return 2 ** (-avg_depth / self.sample_size)
    
    def _get_depth(self, tree: Dict, x: List[float]) -> int:
        if tree['type'] == 'leaf': return tree.get('depth', 0)
        return tree.get('depth', 0) + 1

# UPGRADE 253: One-Class SVM
class OneClassSVM:
    def __init__(self, nu: float = 0.1):
        self.nu = nu
        self.support_vectors: List[List[float]] = []
        self.threshold = 0
        
    def fit(self, data: List[List[float]]):
        self.support_vectors = data[:int(len(data) * self.nu)]
        distances = [self._min_distance(d) for d in data]
        self.threshold = np.percentile(distances, (1 - self.nu) * 100)
        
    def _min_distance(self, x: List[float]) -> float:
        if not self.support_vectors: return 0
        return min(np.sqrt(sum((a - b) ** 2 for a, b in zip(x, sv))) for sv in self.support_vectors)
    
    def predict(self, x: List[float]) -> bool:
        return self._min_distance(x) > self.threshold

# UPGRADE 254: Local Outlier Factor
class LocalOutlierFactor:
    def __init__(self, k: int = 5):
        self.k = k
        self.data: List[List[float]] = []
        
    def fit(self, data: List[List[float]]):
        self.data = data
        
    def predict(self, x: List[float]) -> float:
        if len(self.data) < self.k: return 1.0
        distances = sorted([self._distance(x, d) for d in self.data])[:self.k]
        k_distance = distances[-1]
        lrd_x = 1 / (np.mean(distances) + 0.0001)
        neighbor_lrds = []
        for d in self.data[:self.k]:
            d_distances = sorted([self._distance(d, other) for other in self.data])[:self.k]
            neighbor_lrds.append(1 / (np.mean(d_distances) + 0.0001))
        return np.mean(neighbor_lrds) / lrd_x if lrd_x > 0 else 1.0
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 255: DBSCAN Clustering
class DBSCANClustering:
    def __init__(self, eps: float = 0.5, min_samples: int = 5):
        self.eps = eps
        self.min_samples = min_samples
        self.labels: List[int] = []
        
    def fit(self, data: List[List[float]]) -> List[int]:
        n = len(data)
        self.labels = [-1] * n
        cluster_id = 0
        for i in range(n):
            if self.labels[i] != -1: continue
            neighbors = self._get_neighbors(data, i)
            if len(neighbors) < self.min_samples: continue
            self.labels[i] = cluster_id
            self._expand_cluster(data, neighbors, cluster_id)
            cluster_id += 1
        return self.labels
    
    def _get_neighbors(self, data: List[List[float]], idx: int) -> List[int]:
        return [j for j in range(len(data)) if self._distance(data[idx], data[j]) <= self.eps]
    
    def _expand_cluster(self, data: List[List[float]], neighbors: List[int], cluster_id: int):
        for j in neighbors:
            if self.labels[j] == -1: self.labels[j] = cluster_id
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 256: K-Means Clustering
class KMeansClustering:
    def __init__(self, k: int = 3, max_iter: int = 100):
        self.k = k
        self.max_iter = max_iter
        self.centroids: List[List[float]] = []
        
    def fit(self, data: List[List[float]]) -> List[int]:
        self.centroids = [data[i] for i in np.random.choice(len(data), self.k, replace=False)]
        for _ in range(self.max_iter):
            labels = [self._nearest_centroid(d) for d in data]
            new_centroids = []
            for c in range(self.k):
                cluster_points = [data[i] for i in range(len(data)) if labels[i] == c]
                if cluster_points:
                    new_centroids.append([np.mean([p[j] for p in cluster_points]) for j in range(len(data[0]))])
                else:
                    new_centroids.append(self.centroids[c])
            self.centroids = new_centroids
        return [self._nearest_centroid(d) for d in data]
    
    def _nearest_centroid(self, x: List[float]) -> int:
        distances = [self._distance(x, c) for c in self.centroids]
        return int(np.argmin(distances))
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 257: Hierarchical Clustering
class HierarchicalClustering:
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        
    def fit(self, data: List[List[float]]) -> List[int]:
        n = len(data)
        clusters = [[i] for i in range(n)]
        while len(clusters) > self.n_clusters:
            min_dist = float('inf')
            merge_i, merge_j = 0, 1
            for i in range(len(clusters)):
                for j in range(i + 1, len(clusters)):
                    dist = self._cluster_distance(data, clusters[i], clusters[j])
                    if dist < min_dist:
                        min_dist = dist
                        merge_i, merge_j = i, j
            clusters[merge_i].extend(clusters[merge_j])
            clusters.pop(merge_j)
        labels = [0] * n
        for cluster_id, cluster in enumerate(clusters):
            for idx in cluster:
                labels[idx] = cluster_id
        return labels
    
    def _cluster_distance(self, data: List[List[float]], c1: List[int], c2: List[int]) -> float:
        return min(self._distance(data[i], data[j]) for i in c1 for j in c2)
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 258: Spectral Clustering
class SpectralClustering:
    def __init__(self, n_clusters: int = 3):
        self.n_clusters = n_clusters
        
    def fit(self, data: List[List[float]]) -> List[int]:
        n = len(data)
        affinity = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                affinity[i, j] = np.exp(-self._distance(data[i], data[j]) ** 2)
        degree = np.diag(affinity.sum(axis=1))
        laplacian = degree - affinity
        eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
        features = eigenvectors[:, :self.n_clusters]
        kmeans = KMeansClustering(self.n_clusters)
        return kmeans.fit([list(f) for f in features])
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 259: Mean Shift Clustering
class MeanShiftClustering:
    def __init__(self, bandwidth: float = 1.0):
        self.bandwidth = bandwidth
        self.centroids: List[List[float]] = []
        
    def fit(self, data: List[List[float]], max_iter: int = 100) -> List[int]:
        points = [list(d) for d in data]
        for _ in range(max_iter):
            new_points = []
            for p in points:
                neighbors = [d for d in data if self._distance(p, d) <= self.bandwidth]
                if neighbors:
                    new_p = [np.mean([n[j] for n in neighbors]) for j in range(len(p))]
                    new_points.append(new_p)
                else:
                    new_points.append(p)
            points = new_points
        self.centroids = self._find_unique_centroids(points)
        return [self._nearest_centroid(p) for p in points]
    
    def _find_unique_centroids(self, points: List[List[float]]) -> List[List[float]]:
        unique = []
        for p in points:
            is_unique = True
            for u in unique:
                if self._distance(p, u) < self.bandwidth / 2:
                    is_unique = False
                    break
            if is_unique: unique.append(p)
        return unique
    
    def _nearest_centroid(self, x: List[float]) -> int:
        if not self.centroids: return 0
        distances = [self._distance(x, c) for c in self.centroids]
        return int(np.argmin(distances))
    
    def _distance(self, a: List[float], b: List[float]) -> float:
        return np.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))

# UPGRADE 260: Time Series Forecaster
class TimeSeriesForecaster:
    def __init__(self, lookback: int = 10):
        self.lookback = lookback
        self.weights: np.ndarray = None
        
    def fit(self, series: List[float]):
        if len(series) < self.lookback + 1: return
        X, y = [], []
        for i in range(self.lookback, len(series)):
            X.append(series[i-self.lookback:i])
            y.append(series[i])
        X, y = np.array(X), np.array(y)
        self.weights = np.linalg.lstsq(X, y, rcond=None)[0]
        
    def predict(self, recent: List[float]) -> float:
        if self.weights is None or len(recent) < self.lookback: return recent[-1] if recent else 0
        return float(np.dot(recent[-self.lookback:], self.weights))

# UPGRADE 261: ARIMA Model
class ARIMAModel:
    def __init__(self, p: int = 2, d: int = 1, q: int = 2):
        self.p = p
        self.d = d
        self.q = q
        self.ar_coeffs: List[float] = []
        self.ma_coeffs: List[float] = []
        
    def fit(self, series: List[float]):
        diff_series = self._difference(series, self.d)
        if len(diff_series) < self.p + 1: return
        X, y = [], []
        for i in range(self.p, len(diff_series)):
            X.append(diff_series[i-self.p:i])
            y.append(diff_series[i])
        if X:
            X, y = np.array(X), np.array(y)
            self.ar_coeffs = list(np.linalg.lstsq(X, y, rcond=None)[0])
        self.ma_coeffs = [0.1] * self.q
        
    def _difference(self, series: List[float], d: int) -> List[float]:
        for _ in range(d):
            series = [series[i] - series[i-1] for i in range(1, len(series))]
        return series
    
    def predict(self, recent: List[float], steps: int = 1) -> List[float]:
        predictions = []
        current = list(recent)
        for _ in range(steps):
            if len(self.ar_coeffs) > 0 and len(current) >= self.p:
                pred = sum(c * current[-i-1] for i, c in enumerate(self.ar_coeffs))
            else:
                pred = current[-1] if current else 0
            predictions.append(pred)
            current.append(pred)
        return predictions

# UPGRADE 262: Exponential Smoothing
class ExponentialSmoothing:
    def __init__(self, alpha: float = 0.3, beta: float = 0.1, gamma: float = 0.1):
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.level = 0
        self.trend = 0
        
    def fit(self, series: List[float]):
        if len(series) < 2: return
        self.level = series[0]
        self.trend = series[1] - series[0]
        for i in range(1, len(series)):
            prev_level = self.level
            self.level = self.alpha * series[i] + (1 - self.alpha) * (self.level + self.trend)
            self.trend = self.beta * (self.level - prev_level) + (1 - self.beta) * self.trend
            
    def predict(self, steps: int = 1) -> List[float]:
        return [self.level + (i + 1) * self.trend for i in range(steps)]

# UPGRADE 263: Prophet-like Decomposition
class ProphetDecomposition:
    def __init__(self):
        self.trend: List[float] = []
        self.seasonal: List[float] = []
        self.residual: List[float] = []
        
    def decompose(self, series: List[float], period: int = 7) -> Dict[str, List[float]]:
        n = len(series)
        self.trend = self._moving_average(series, period)
        detrended = [series[i] - self.trend[i] for i in range(n)]
        self.seasonal = self._extract_seasonal(detrended, period)
        self.residual = [series[i] - self.trend[i] - self.seasonal[i % period] for i in range(n)]
        return {'trend': self.trend, 'seasonal': self.seasonal, 'residual': self.residual}
    
    def _moving_average(self, series: List[float], window: int) -> List[float]:
        result = []
        for i in range(len(series)):
            start = max(0, i - window // 2)
            end = min(len(series), i + window // 2 + 1)
            result.append(np.mean(series[start:end]))
        return result
    
    def _extract_seasonal(self, detrended: List[float], period: int) -> List[float]:
        seasonal = []
        for i in range(period):
            values = [detrended[j] for j in range(i, len(detrended), period)]
            seasonal.append(np.mean(values) if values else 0)
        return seasonal

# UPGRADE 264: Wavelet Transform
class WaveletTransform:
    def __init__(self):
        self.coefficients: List[List[float]] = []
        
    def transform(self, signal: List[float], levels: int = 3) -> List[List[float]]:
        self.coefficients = []
        current = signal
        for _ in range(levels):
            low, high = self._haar_step(current)
            self.coefficients.append(high)
            current = low
        self.coefficients.append(current)
        return self.coefficients
    
    def _haar_step(self, signal: List[float]) -> Tuple[List[float], List[float]]:
        n = len(signal) // 2
        low = [(signal[2*i] + signal[2*i+1]) / np.sqrt(2) for i in range(n)]
        high = [(signal[2*i] - signal[2*i+1]) / np.sqrt(2) for i in range(n)]
        return low, high
    
    def inverse(self) -> List[float]:
        if not self.coefficients: return []
        current = self.coefficients[-1]
        for high in reversed(self.coefficients[:-1]):
            current = self._haar_inverse(current, high)
        return current
    
    def _haar_inverse(self, low: List[float], high: List[float]) -> List[float]:
        result = []
        for i in range(len(low)):
            result.append((low[i] + high[i]) / np.sqrt(2))
            result.append((low[i] - high[i]) / np.sqrt(2))
        return result

# UPGRADE 265: Fourier Transform Analyzer
class FourierTransformAnalyzer:
    def analyze(self, signal: List[float]) -> Dict[str, Any]:
        n = len(signal)
        fft = np.fft.fft(signal)
        freqs = np.fft.fftfreq(n)
        magnitudes = np.abs(fft)
        dominant_idx = np.argsort(magnitudes)[-5:]
        return {
            'dominant_frequencies': [freqs[i] for i in dominant_idx],
            'dominant_magnitudes': [magnitudes[i] for i in dominant_idx],
            'spectral_entropy': self._spectral_entropy(magnitudes)
        }
    
    def _spectral_entropy(self, magnitudes: np.ndarray) -> float:
        psd = magnitudes ** 2
        psd_norm = psd / (psd.sum() + 0.0001)
        return -np.sum(psd_norm * np.log(psd_norm + 0.0001))

# UPGRADE 266: Kalman Filter
class KalmanFilter:
    def __init__(self, process_noise: float = 0.01, measurement_noise: float = 0.1):
        self.Q = process_noise
        self.R = measurement_noise
        self.x = 0
        self.P = 1
        
    def update(self, measurement: float) -> float:
        x_pred = self.x
        P_pred = self.P + self.Q
        K = P_pred / (P_pred + self.R)
        self.x = x_pred + K * (measurement - x_pred)
        self.P = (1 - K) * P_pred
        return self.x
    
    def predict(self, steps: int = 1) -> List[float]:
        return [self.x] * steps

# UPGRADE 267: Extended Kalman Filter
class ExtendedKalmanFilter:
    def __init__(self, state_dim: int = 2):
        self.state_dim = state_dim
        self.x = np.zeros(state_dim)
        self.P = np.eye(state_dim)
        self.Q = np.eye(state_dim) * 0.01
        self.R = np.eye(1) * 0.1
        
    def update(self, measurement: float) -> np.ndarray:
        H = np.array([[1] + [0] * (self.state_dim - 1)])
        y = measurement - H @ self.x
        S = H @ self.P @ H.T + self.R
        K = self.P @ H.T @ np.linalg.inv(S)
        self.x = self.x + K.flatten() * y
        self.P = (np.eye(self.state_dim) - K @ H) @ self.P
        return self.x

# UPGRADE 268: Particle Filter
class ParticleFilter:
    def __init__(self, n_particles: int = 100):
        self.n_particles = n_particles
        self.particles = np.random.randn(n_particles)
        self.weights = np.ones(n_particles) / n_particles
        
    def update(self, measurement: float, noise: float = 0.1) -> float:
        self.particles += np.random.randn(self.n_particles) * noise
        likelihoods = np.exp(-0.5 * ((measurement - self.particles) / noise) ** 2)
        self.weights = likelihoods / (likelihoods.sum() + 0.0001)
        if 1 / (self.weights ** 2).sum() < self.n_particles / 2:
            indices = np.random.choice(self.n_particles, self.n_particles, p=self.weights)
            self.particles = self.particles[indices]
            self.weights = np.ones(self.n_particles) / self.n_particles
        return np.average(self.particles, weights=self.weights)

# UPGRADE 269: State Space Model
class StateSpaceModel:
    def __init__(self, state_dim: int = 2, obs_dim: int = 1):
        self.A = np.eye(state_dim)
        self.B = np.zeros((state_dim, 1))
        self.C = np.zeros((obs_dim, state_dim))
        self.C[0, 0] = 1
        self.state = np.zeros(state_dim)
        
    def step(self, control: float = 0) -> float:
        self.state = self.A @ self.state + self.B.flatten() * control
        return float(self.C @ self.state)
    
    def update(self, observation: float, gain: float = 0.1):
        error = observation - float(self.C @ self.state)
        self.state += gain * self.C.T.flatten() * error

# UPGRADE 270: Recurrent Neural Network
class RecurrentNeuralNetwork:
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.Wxh = np.random.randn(hidden_size, input_size) * 0.01
        self.Whh = np.random.randn(hidden_size, hidden_size) * 0.01
        self.Why = np.random.randn(output_size, hidden_size) * 0.01
        self.bh = np.zeros(hidden_size)
        self.by = np.zeros(output_size)
        self.h = np.zeros(hidden_size)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        self.h = np.tanh(self.Wxh @ x + self.Whh @ self.h + self.bh)
        return self.Why @ self.h + self.by
    
    def reset(self):
        self.h = np.zeros_like(self.h)

# UPGRADE 271: GRU Cell
class GRUCell:
    def __init__(self, input_size: int, hidden_size: int):
        self.hidden_size = hidden_size
        scale = 0.01
        self.Wz = np.random.randn(input_size + hidden_size, hidden_size) * scale
        self.Wr = np.random.randn(input_size + hidden_size, hidden_size) * scale
        self.Wh = np.random.randn(input_size + hidden_size, hidden_size) * scale
        
    def forward(self, x: np.ndarray, h: np.ndarray) -> np.ndarray:
        combined = np.concatenate([x, h], axis=-1)
        z = self._sigmoid(combined @ self.Wz)
        r = self._sigmoid(combined @ self.Wr)
        combined_r = np.concatenate([x, r * h], axis=-1)
        h_tilde = np.tanh(combined_r @ self.Wh)
        return (1 - z) * h + z * h_tilde
    
    def _sigmoid(self, x: np.ndarray) -> np.ndarray:
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

# UPGRADE 272: Bidirectional RNN
class BidirectionalRNN:
    def __init__(self, input_size: int, hidden_size: int):
        self.forward_rnn = RecurrentNeuralNetwork(input_size, hidden_size, hidden_size)
        self.backward_rnn = RecurrentNeuralNetwork(input_size, hidden_size, hidden_size)
        
    def forward(self, sequence: List[np.ndarray]) -> List[np.ndarray]:
        self.forward_rnn.reset()
        self.backward_rnn.reset()
        forward_outputs = [self.forward_rnn.forward(x) for x in sequence]
        backward_outputs = [self.backward_rnn.forward(x) for x in reversed(sequence)]
        backward_outputs = list(reversed(backward_outputs))
        return [np.concatenate([f, b]) for f, b in zip(forward_outputs, backward_outputs)]

# UPGRADE 273: Sequence-to-Sequence Model
class Seq2SeqModel:
    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.encoder = RecurrentNeuralNetwork(input_size, hidden_size, hidden_size)
        self.decoder = RecurrentNeuralNetwork(output_size, hidden_size, output_size)
        
    def encode(self, sequence: List[np.ndarray]) -> np.ndarray:
        self.encoder.reset()
        for x in sequence:
            self.encoder.forward(x)
        return self.encoder.h
    
    def decode(self, context: np.ndarray, length: int) -> List[np.ndarray]:
        self.decoder.h = context
        outputs = []
        x = np.zeros(self.decoder.Why.shape[0])
        for _ in range(length):
            y = self.decoder.forward(x)
            outputs.append(y)
            x = y
        return outputs

# UPGRADE 274: Temporal Convolutional Network
class TemporalConvNetwork:
    def __init__(self, input_channels: int, output_channels: int, kernel_size: int = 3):
        self.kernel_size = kernel_size
        self.weights = np.random.randn(output_channels, input_channels, kernel_size) * 0.01
        self.bias = np.zeros(output_channels)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        batch_size, seq_len, channels = x.shape
        output_len = seq_len - self.kernel_size + 1
        output = np.zeros((batch_size, output_len, self.weights.shape[0]))
        for i in range(output_len):
            window = x[:, i:i+self.kernel_size, :]
            for j in range(self.weights.shape[0]):
                output[:, i, j] = np.sum(window * self.weights[j].T, axis=(1, 2)) + self.bias[j]
        return np.maximum(0, output)

# UPGRADE 275: Causal Convolution
class CausalConvolution:
    def __init__(self, in_channels: int, out_channels: int, kernel_size: int = 3, dilation: int = 1):
        self.kernel_size = kernel_size
        self.dilation = dilation
        self.padding = (kernel_size - 1) * dilation
        self.weights = np.random.randn(out_channels, in_channels, kernel_size) * 0.01
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        padded = np.pad(x, ((0, 0), (self.padding, 0), (0, 0)), mode='constant')
        output = np.zeros((x.shape[0], x.shape[1], self.weights.shape[0]))
        for i in range(x.shape[1]):
            indices = [i + self.padding - j * self.dilation for j in range(self.kernel_size)]
            window = padded[:, indices, :]
            for j in range(self.weights.shape[0]):
                output[:, i, j] = np.sum(window * self.weights[j].T, axis=(1, 2))
        return output

# UPGRADE 276: Multi-Head Attention
class MultiHeadAttention:
    def __init__(self, d_model: int, n_heads: int):
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        self.W_q = np.random.randn(d_model, d_model) * 0.01
        self.W_k = np.random.randn(d_model, d_model) * 0.01
        self.W_v = np.random.randn(d_model, d_model) * 0.01
        self.W_o = np.random.randn(d_model, d_model) * 0.01
        
    def forward(self, query: np.ndarray, key: np.ndarray, value: np.ndarray) -> np.ndarray:
        Q = query @ self.W_q
        K = key @ self.W_k
        V = value @ self.W_v
        scores = Q @ K.T / np.sqrt(self.d_k)
        weights = self._softmax(scores)
        return weights @ V @ self.W_o
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / exp_x.sum(axis=-1, keepdims=True)

# UPGRADE 277: Positional Encoding
class PositionalEncoding:
    def __init__(self, d_model: int, max_len: int = 5000):
        self.encoding = np.zeros((max_len, d_model))
        position = np.arange(max_len)[:, np.newaxis]
        div_term = np.exp(np.arange(0, d_model, 2) * (-np.log(10000.0) / d_model))
        self.encoding[:, 0::2] = np.sin(position * div_term)
        self.encoding[:, 1::2] = np.cos(position * div_term)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        return x + self.encoding[:x.shape[0]]

# UPGRADE 278: Layer Normalization
class LayerNormalization:
    def __init__(self, features: int, eps: float = 1e-6):
        self.gamma = np.ones(features)
        self.beta = np.zeros(features)
        self.eps = eps
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        mean = np.mean(x, axis=-1, keepdims=True)
        std = np.std(x, axis=-1, keepdims=True)
        return self.gamma * (x - mean) / (std + self.eps) + self.beta

# UPGRADE 279: Batch Normalization
class BatchNormalization:
    def __init__(self, features: int, momentum: float = 0.1):
        self.gamma = np.ones(features)
        self.beta = np.zeros(features)
        self.running_mean = np.zeros(features)
        self.running_var = np.ones(features)
        self.momentum = momentum
        
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        if training:
            mean = np.mean(x, axis=0)
            var = np.var(x, axis=0)
            self.running_mean = (1 - self.momentum) * self.running_mean + self.momentum * mean
            self.running_var = (1 - self.momentum) * self.running_var + self.momentum * var
        else:
            mean, var = self.running_mean, self.running_var
        return self.gamma * (x - mean) / np.sqrt(var + 1e-8) + self.beta

# UPGRADE 280: Dropout Layer
class DropoutLayer:
    def __init__(self, rate: float = 0.5):
        self.rate = rate
        self.mask = None
        
    def forward(self, x: np.ndarray, training: bool = True) -> np.ndarray:
        if not training: return x
        self.mask = np.random.binomial(1, 1 - self.rate, x.shape) / (1 - self.rate)
        return x * self.mask

# UPGRADE 281: Residual Connection
class ResidualConnection:
    def __init__(self, sublayer):
        self.sublayer = sublayer
        self.norm = LayerNormalization(1)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        return x + self.sublayer(self.norm.forward(x))

# UPGRADE 282: Feed Forward Network
class FeedForwardNetwork:
    def __init__(self, d_model: int, d_ff: int):
        self.W1 = np.random.randn(d_model, d_ff) * 0.01
        self.W2 = np.random.randn(d_ff, d_model) * 0.01
        self.b1 = np.zeros(d_ff)
        self.b2 = np.zeros(d_model)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        hidden = np.maximum(0, x @ self.W1 + self.b1)
        return hidden @ self.W2 + self.b2

# UPGRADE 283: Embedding Layer
class EmbeddingLayer:
    def __init__(self, vocab_size: int, d_model: int):
        self.embeddings = np.random.randn(vocab_size, d_model) * 0.01
        
    def forward(self, indices: List[int]) -> np.ndarray:
        return self.embeddings[indices]

# UPGRADE 284: Output Projection
class OutputProjection:
    def __init__(self, d_model: int, vocab_size: int):
        self.W = np.random.randn(d_model, vocab_size) * 0.01
        self.b = np.zeros(vocab_size)
        
    def forward(self, x: np.ndarray) -> np.ndarray:
        logits = x @ self.W + self.b
        return self._softmax(logits)
    
    def _softmax(self, x: np.ndarray) -> np.ndarray:
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / exp_x.sum(axis=-1, keepdims=True)

# UPGRADE 285: Loss Functions
class LossFunctions:
    @staticmethod
    def mse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean((y_true - y_pred) ** 2))
    
    @staticmethod
    def mae(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(np.mean(np.abs(y_true - y_pred)))
    
    @staticmethod
    def cross_entropy(y_true: np.ndarray, y_pred: np.ndarray) -> float:
        return float(-np.mean(y_true * np.log(y_pred + 1e-10)))
    
    @staticmethod
    def huber(y_true: np.ndarray, y_pred: np.ndarray, delta: float = 1.0) -> float:
        error = y_true - y_pred
        is_small = np.abs(error) <= delta
        squared_loss = 0.5 * error ** 2
        linear_loss = delta * (np.abs(error) - 0.5 * delta)
        return float(np.mean(np.where(is_small, squared_loss, linear_loss)))

# UPGRADE 286: Optimizer Base
class OptimizerBase:
    def __init__(self, lr: float = 0.01):
        self.lr = lr
        
    def step(self, params: Dict[str, np.ndarray], grads: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        return {k: params[k] - self.lr * grads[k] for k in params}

# UPGRADE 287: Adam Optimizer
class AdamOptimizer:
    def __init__(self, lr: float = 0.001, beta1: float = 0.9, beta2: float = 0.999, eps: float = 1e-8):
        self.lr = lr
        self.beta1 = beta1
        self.beta2 = beta2
        self.eps = eps
        self.m: Dict[str, np.ndarray] = {}
        self.v: Dict[str, np.ndarray] = {}
        self.t = 0
        
    def step(self, params: Dict[str, np.ndarray], grads: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        self.t += 1
        result = {}
        for k in params:
            if k not in self.m:
                self.m[k] = np.zeros_like(params[k])
                self.v[k] = np.zeros_like(params[k])
            self.m[k] = self.beta1 * self.m[k] + (1 - self.beta1) * grads[k]
            self.v[k] = self.beta2 * self.v[k] + (1 - self.beta2) * grads[k] ** 2
            m_hat = self.m[k] / (1 - self.beta1 ** self.t)
            v_hat = self.v[k] / (1 - self.beta2 ** self.t)
            result[k] = params[k] - self.lr * m_hat / (np.sqrt(v_hat) + self.eps)
        return result

# UPGRADE 288: RMSprop Optimizer
class RMSpropOptimizer:
    def __init__(self, lr: float = 0.01, decay: float = 0.99, eps: float = 1e-8):
        self.lr = lr
        self.decay = decay
        self.eps = eps
        self.cache: Dict[str, np.ndarray] = {}
        
    def step(self, params: Dict[str, np.ndarray], grads: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        result = {}
        for k in params:
            if k not in self.cache:
                self.cache[k] = np.zeros_like(params[k])
            self.cache[k] = self.decay * self.cache[k] + (1 - self.decay) * grads[k] ** 2
            result[k] = params[k] - self.lr * grads[k] / (np.sqrt(self.cache[k]) + self.eps)
        return result

# UPGRADE 289: Learning Rate Scheduler
class LearningRateScheduler:
    def __init__(self, initial_lr: float, schedule_type: str = 'step'):
        self.initial_lr = initial_lr
        self.schedule_type = schedule_type
        self.step_count = 0
        
    def get_lr(self) -> float:
        self.step_count += 1
        if self.schedule_type == 'step':
            return self.initial_lr * (0.1 ** (self.step_count // 1000))
        elif self.schedule_type == 'exponential':
            return self.initial_lr * (0.99 ** self.step_count)
        elif self.schedule_type == 'cosine':
            return self.initial_lr * (1 + np.cos(np.pi * self.step_count / 10000)) / 2
        return self.initial_lr

# UPGRADE 290: Early Stopping
class EarlyStopping:
    def __init__(self, patience: int = 10, min_delta: float = 0.0001):
        self.patience = patience
        self.min_delta = min_delta
        self.best_loss = float('inf')
        self.counter = 0
        
    def check(self, loss: float) -> bool:
        if loss < self.best_loss - self.min_delta:
            self.best_loss = loss
            self.counter = 0
            return False
        self.counter += 1
        return self.counter >= self.patience

# UPGRADE 291: Gradient Clipping
class GradientClipping:
    def __init__(self, max_norm: float = 1.0):
        self.max_norm = max_norm
        
    def clip(self, grads: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        total_norm = np.sqrt(sum(np.sum(g ** 2) for g in grads.values()))
        if total_norm > self.max_norm:
            scale = self.max_norm / total_norm
            return {k: g * scale for k, g in grads.items()}
        return grads

# UPGRADE 292: Weight Initialization
class WeightInitialization:
    @staticmethod
    def xavier(shape: Tuple[int, ...]) -> np.ndarray:
        fan_in, fan_out = shape[0], shape[1] if len(shape) > 1 else shape[0]
        std = np.sqrt(2.0 / (fan_in + fan_out))
        return np.random.randn(*shape) * std
    
    @staticmethod
    def he(shape: Tuple[int, ...]) -> np.ndarray:
        fan_in = shape[0]
        std = np.sqrt(2.0 / fan_in)
        return np.random.randn(*shape) * std
    
    @staticmethod
    def orthogonal(shape: Tuple[int, ...]) -> np.ndarray:
        flat_shape = (shape[0], np.prod(shape[1:]))
        a = np.random.randn(*flat_shape)
        u, _, v = np.linalg.svd(a, full_matrices=False)
        q = u if u.shape == flat_shape else v
        return q.reshape(shape)

# UPGRADE 293: Data Augmentation
class DataAugmentation:
    def __init__(self):
        self.augmentations = []
        
    def add_noise(self, data: np.ndarray, std: float = 0.01) -> np.ndarray:
        return data + np.random.randn(*data.shape) * std
    
    def scale(self, data: np.ndarray, factor_range: Tuple[float, float] = (0.9, 1.1)) -> np.ndarray:
        factor = np.random.uniform(*factor_range)
        return data * factor
    
    def shift(self, data: np.ndarray, max_shift: int = 5) -> np.ndarray:
        shift = np.random.randint(-max_shift, max_shift + 1)
        return np.roll(data, shift, axis=0)

# UPGRADE 294: Mini-Batch Generator
class MiniBatchGenerator:
    def __init__(self, batch_size: int = 32, shuffle: bool = True):
        self.batch_size = batch_size
        self.shuffle = shuffle
        
    def generate(self, X: List, y: List) -> List[Tuple[List, List]]:
        indices = list(range(len(X)))
        if self.shuffle: np.random.shuffle(indices)
        batches = []
        for i in range(0, len(X), self.batch_size):
            batch_idx = indices[i:i + self.batch_size]
            batches.append(([X[j] for j in batch_idx], [y[j] for j in batch_idx]))
        return batches

# UPGRADE 295: Training Loop Manager
class TrainingLoopManager:
    def __init__(self):
        self.history: Dict[str, List[float]] = {'loss': [], 'val_loss': []}
        self.epoch = 0
        
    def log(self, loss: float, val_loss: float = None):
        self.history['loss'].append(loss)
        if val_loss is not None:
            self.history['val_loss'].append(val_loss)
        self.epoch += 1
        
    def get_best_epoch(self) -> int:
        if not self.history['val_loss']: return len(self.history['loss']) - 1
        return int(np.argmin(self.history['val_loss']))

# UPGRADE 296: Model Checkpoint
class ModelCheckpoint:
    def __init__(self, save_best_only: bool = True):
        self.save_best_only = save_best_only
        self.best_loss = float('inf')
        self.checkpoints: List[Dict] = []
        
    def save(self, model_state: Dict, loss: float) -> bool:
        if self.save_best_only and loss >= self.best_loss:
            return False
        self.best_loss = min(self.best_loss, loss)
        self.checkpoints.append({'state': model_state.copy(), 'loss': loss})
        return True
    
    def load_best(self) -> Dict:
        if not self.checkpoints: return {}
        return min(self.checkpoints, key=lambda x: x['loss'])['state']

# UPGRADE 297: Metrics Calculator
class MetricsCalculator:
    @staticmethod
    def accuracy(y_true: List, y_pred: List) -> float:
        return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)
    
    @staticmethod
    def precision(y_true: List, y_pred: List, positive: int = 1) -> float:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != positive and p == positive)
        return tp / (tp + fp) if (tp + fp) > 0 else 0
    
    @staticmethod
    def recall(y_true: List, y_pred: List, positive: int = 1) -> float:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p == positive)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == positive and p != positive)
        return tp / (tp + fn) if (tp + fn) > 0 else 0
    
    @staticmethod
    def f1_score(y_true: List, y_pred: List, positive: int = 1) -> float:
        p = MetricsCalculator.precision(y_true, y_pred, positive)
        r = MetricsCalculator.recall(y_true, y_pred, positive)
        return 2 * p * r / (p + r) if (p + r) > 0 else 0

# UPGRADE 298: Confusion Matrix
class ConfusionMatrix:
    def __init__(self, n_classes: int):
        self.n_classes = n_classes
        self.matrix = np.zeros((n_classes, n_classes), dtype=int)
        
    def update(self, y_true: int, y_pred: int):
        self.matrix[y_true, y_pred] += 1
        
    def get_matrix(self) -> np.ndarray:
        return self.matrix
    
    def get_accuracy(self) -> float:
        return np.trace(self.matrix) / self.matrix.sum()

# UPGRADE 299: ROC Curve Calculator
class ROCCurveCalculator:
    def calculate(self, y_true: List[int], y_scores: List[float]) -> Dict[str, List[float]]:
        thresholds = sorted(set(y_scores), reverse=True)
        tpr, fpr = [], []
        for thresh in thresholds:
            y_pred = [1 if s >= thresh else 0 for s in y_scores]
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
            tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
            tpr.append(tp / (tp + fn) if (tp + fn) > 0 else 0)
            fpr.append(fp / (fp + tn) if (fp + tn) > 0 else 0)
        return {'tpr': tpr, 'fpr': fpr, 'thresholds': thresholds}
    
    def auc(self, fpr: List[float], tpr: List[float]) -> float:
        return sum((fpr[i] - fpr[i-1]) * (tpr[i] + tpr[i-1]) / 2 for i in range(1, len(fpr)))

# UPGRADE 300: Feature Importance Calculator
class FeatureImportanceCalculator:
    def __init__(self):
        self.importances: Dict[str, float] = {}
        
    def permutation_importance(self, model, X: List[Dict], y: List[float], metric_func) -> Dict[str, float]:
        baseline = metric_func(y, [model.predict(x) for x in X])
        for feature in X[0].keys():
            X_permuted = [{**x, feature: np.random.choice([xi[feature] for xi in X])} for x in X]
            permuted_score = metric_func(y, [model.predict(x) for x in X_permuted])
            self.importances[feature] = baseline - permuted_score
        return self.importances
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        return sorted(self.importances.items(), key=lambda x: -x[1])[:n]
