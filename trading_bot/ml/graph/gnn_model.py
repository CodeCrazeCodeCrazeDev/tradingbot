"""
Graph Neural Networks for Cross-Asset Modeling

Models spillovers and correlations between currency pairs using GNNs.
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
import numpy

logger = logging.getLogger(__name__)


class GraphAttentionLayer(nn.Module):
    """Graph Attention Layer (GAT)"""
    
    def __init__(self, in_features: int, out_features: int, n_heads: int = 4, dropout: float = 0.1):
        super().__init__()
        self.n_heads = n_heads
        self.out_features = out_features
        
        # Multi-head attention
        self.W = nn.Linear(in_features, out_features * n_heads, bias=False)
        self.a = nn.Parameter(torch.zeros(size=(2 * out_features, 1)))
        
        self.dropout = nn.Dropout(dropout)
        self.leakyrelu = nn.LeakyReLU(0.2)
    
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Node features [n_nodes, in_features]
            adj: Adjacency matrix [n_nodes, n_nodes]
        """
        n_nodes = x.size(0)
        
        # Linear transformation
        h = self.W(x)  # [n_nodes, out_features * n_heads]
        h = h.view(n_nodes, self.n_heads, self.out_features)
        
        # Attention mechanism
        h_i = h.repeat(1, n_nodes, 1).view(n_nodes * n_nodes, self.n_heads, self.out_features)
        h_j = h.repeat(n_nodes, 1, 1)
        
        # Concatenate and compute attention scores
        a_input = torch.cat([h_i, h_j], dim=-1)
        e = self.leakyrelu(torch.matmul(a_input, self.a).squeeze(-1))
        
        # Mask attention scores with adjacency matrix
        e = e.view(n_nodes, n_nodes, self.n_heads)
        zero_vec = -9e15 * torch.ones_like(e)
        attention = torch.where(adj.unsqueeze(-1) > 0, e, zero_vec)
        
        # Softmax
        attention = F.softmax(attention, dim=1)
        attention = self.dropout(attention)
        
        # Aggregate
        h_prime = torch.matmul(attention.transpose(1, 2), h)  # [n_nodes, n_heads, out_features]
        h_prime = h_prime.mean(dim=1)  # Average over heads
        
        return h_prime


class AssetGNN(nn.Module):
    """
    Graph Neural Network for asset price prediction
    
    Architecture:
    - Input: Node features (price, volume, RSI, MACD per asset)
    - GNN layers: 3 layers of Graph Attention
    - Output: Predicted returns for each asset
    """
    
    def __init__(
        self,
        in_features: int = 10,
        hidden_features: int = 32,
        out_features: int = 1,
        n_heads: int = 4,
        n_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.layers = nn.ModuleList()
        
        # First layer
        self.layers.append(
            GraphAttentionLayer(in_features, hidden_features, n_heads, dropout)
        )
        
        # Hidden layers
        for _ in range(n_layers - 2):
            self.layers.append(
                GraphAttentionLayer(hidden_features, hidden_features, n_heads, dropout)
            )
        
        # Output layer
        self.layers.append(
            GraphAttentionLayer(hidden_features, out_features, 1, dropout)
        )
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, adj: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: Node features [n_nodes, in_features]
            adj: Adjacency matrix [n_nodes, n_nodes]
            
        Returns:
            Predicted returns [n_nodes, 1]
        """
        for i, layer in enumerate(self.layers[:-1]):
            x = layer(x, adj)
            x = F.relu(x)
            x = self.dropout(x)
        
        # Output layer
        x = self.layers[-1](x, adj)
        
        return x


class AssetGraph:
    """Build dynamic asset correlation graph"""
    
    def __init__(self, symbols: List[str]):
        self.symbols = symbols
        self.n_assets = len(symbols)
        self.symbol_to_idx = {s: i for i, s in enumerate(symbols)}
    
    def build_correlation_graph(
        self,
        price_data: Dict[str, np.ndarray],
        window: int = 30
    ) -> torch.Tensor:
        """
        Build correlation-based adjacency matrix
        
        Args:
            price_data: Dict mapping symbol to price array
            window: Rolling window for correlation
            
        Returns:
            Adjacency matrix [n_assets, n_assets]
        """
        # Compute returns
        returns = {}
        for symbol, prices in price_data.items():
            returns[symbol] = np.diff(prices) / prices[:-1]
        
        # Compute correlation matrix
        corr_matrix = np.zeros((self.n_assets, self.n_assets))
        
        for i, sym1 in enumerate(self.symbols):
            for j, sym2 in enumerate(self.symbols):
                if i == j:
                    corr_matrix[i, j] = 1.0
                else:
                    r1 = returns[sym1][-window:]
                    r2 = returns[sym2][-window:]
                    corr = np.corrcoef(r1, r2)[0, 1]
                    corr_matrix[i, j] = abs(corr)  # Use absolute correlation
        
        # Threshold to create sparse graph
        threshold = 0.3
        adj_matrix = (corr_matrix > threshold).astype(float)
        
        return torch.FloatTensor(adj_matrix)
    
    def build_feature_matrix(
        self,
        market_data: Dict[str, Dict[str, float]]
    ) -> torch.Tensor:
        """
        Build node feature matrix
        
        Args:
            market_data: Dict mapping symbol to features dict
            
        Returns:
            Feature matrix [n_assets, n_features]
        """
        features = []
        
        for symbol in self.symbols:
            data = market_data.get(symbol, {})
            
            # Extract features
            feat = [
                data.get('price', 0),
                data.get('volume', 0),
                data.get('rsi', 50),
                data.get('macd', 0),
                data.get('atr', 0),
                data.get('bb_upper', 0),
                data.get('bb_lower', 0),
                data.get('volume_ratio', 1),
                data.get('spread', 0),
                data.get('volatility', 0)
            ]
            
            features.append(feat)
        
        return torch.FloatTensor(features)


class SpilloverPredictor:
    """Predict how one asset affects others"""
    
    def __init__(self, gnn_model: AssetGNN, asset_graph: AssetGraph):
        self.model = gnn_model
        self.graph = asset_graph
    
    def predict_spillover(
        self,
        source_symbol: str,
        source_move: float,
        market_data: Dict[str, Dict[str, float]],
        price_data: Dict[str, np.ndarray]
    ) -> Dict[str, float]:
        """
        Predict impact of source asset move on other assets
        
        Args:
            source_symbol: Symbol of source asset
            source_move: Expected move in source asset (e.g., 0.01 = 1%)
            market_data: Current market data
            price_data: Historical price data
            
        Returns:
            Dict mapping symbol to predicted impact
        """
        # Build graph
        adj = self.graph.build_correlation_graph(price_data)
        features = self.graph.build_feature_matrix(market_data)
        
        # Modify source asset feature to simulate move
        source_idx = self.graph.symbol_to_idx[source_symbol]
        features_modified = features.clone()
        features_modified[source_idx, 0] *= (1 + source_move)
        
        # Predict with and without modification
        self.model.eval()
        with torch.no_grad():
            pred_baseline = self.model(features, adj)
            pred_modified = self.model(features_modified, adj)
        
        # Compute spillover (difference)
        spillover = (pred_modified - pred_baseline).squeeze().numpy()
        
        # Create result dict
        result = {}
        for i, symbol in enumerate(self.graph.symbols):
            if symbol != source_symbol:
                result[symbol] = float(spillover[i])
        
        logger.info(
            f"Spillover from {source_symbol} ({source_move:+.2%}): "
            f"{len([v for v in result.values() if abs(v) > 0.001])} assets affected"
        )
        
        return result
    
    def suggest_hedge(
        self,
        position_symbol: str,
        position_size: float,
        market_data: Dict[str, Dict[str, float]],
        price_data: Dict[str, np.ndarray]
    ) -> Tuple[str, float]:
        """
        Suggest hedge for existing position
        
        Args:
            position_symbol: Symbol of current position
            position_size: Size of position (lots)
            market_data: Current market data
            price_data: Historical price data
            
        Returns:
            Tuple of (hedge_symbol, hedge_size)
        """
        # Predict spillover from adverse move
        spillover = self.predict_spillover(
            position_symbol,
            -0.01,  # Simulate 1% adverse move
            market_data,
            price_data
        )
        
        # Find asset with strongest negative correlation
        best_hedge = None
        best_correlation = 0
        
        for symbol, impact in spillover.items():
            if impact < best_correlation:
                best_correlation = impact
                best_hedge = symbol
        
        if best_hedge:
            # Calculate hedge size (proportional to correlation)
            hedge_size = position_size * abs(best_correlation) / 0.01
            
            logger.info(
                f"Hedge suggestion: {hedge_size:.2f} lots {best_hedge} "
                f"for {position_size:.2f} lots {position_symbol}"
            )
            
            return best_hedge, hedge_size
        
        return None, 0.0


def train_gnn(
    model: AssetGNN,
    train_data: List[Tuple[torch.Tensor, torch.Tensor, torch.Tensor]],
    epochs: int = 100,
    learning_rate: float = 1e-3
) -> dict:
    """
    Train GNN model
    
    Args:
        model: AssetGNN model
        train_data: List of (features, adj, targets)
        epochs: Number of epochs
        learning_rate: Learning rate
        
    Returns:
        Training history
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    criterion = nn.MSELoss()
    
    history = {'loss': []}
    
    for epoch in range(epochs):
        epoch_loss = 0.0
        
        for features, adj, targets in train_data:
            optimizer.zero_grad()
            
            predictions = model(features, adj)
            loss = criterion(predictions, targets)
            
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
        
        avg_loss = epoch_loss / len(train_data)
        history['loss'].append(avg_loss)
        
        if (epoch + 1) % 10 == 0:
            logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.6f}")
    
    return history


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Define assets
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD']
    
    # Create graph
    asset_graph = AssetGraph(symbols)
    
    # Create sample data
    logger.info("Creating sample data...")
    price_data = {
        symbol: np.random.randn(100).cumsum() + 100
        for symbol in symbols
    }
    
    market_data = {
        symbol: {
            'price': price_data[symbol][-1],
            'volume': 1000,
            'rsi': 50 + np.random.randn() * 10,
            'macd': np.random.randn() * 0.001,
            'atr': 0.001,
            'bb_upper': price_data[symbol][-1] * 1.01,
            'bb_lower': price_data[symbol][-1] * 0.99,
            'volume_ratio': 1.0,
            'spread': 0.0001,
            'volatility': 0.01
        }
        for symbol in symbols
    }
    
    # Build graph
    adj = asset_graph.build_correlation_graph(price_data)
    features = asset_graph.build_feature_matrix(market_data)
    
    logger.info(f"Graph: {len(symbols)} nodes, {adj.sum().item():.0f} edges")
    
    # Create model
    model = AssetGNN(in_features=10, hidden_features=32, n_heads=4)
    
    # Create training data
    train_data = []
    for _ in range(50):
        # Random features and targets
        feat = torch.randn(len(symbols), 10)
        targets = torch.randn(len(symbols), 1)
        train_data.append((feat, adj, targets))
    
    # Train
    logger.info("\nTraining GNN...")
    history = train_gnn(model, train_data, epochs=50)
    
    # Test spillover prediction
    logger.info("\nTesting spillover prediction...")
    predictor = SpilloverPredictor(model, asset_graph)
    
    spillover = predictor.predict_spillover(
        'EURUSD',
        0.01,  # 1% move
        market_data,
        price_data
    )
    
    logger.info("\nSpillover effects:")
    for symbol, impact in spillover.items():
        logger.info(f"  {symbol}: {impact:+.4f}")
    
    # Test hedge suggestion
    logger.info("\nHedge suggestion:")
    hedge_symbol, hedge_size = predictor.suggest_hedge(
        'EURUSD',
        1.0,  # 1 lot position
        market_data,
        price_data
    )
    
    if hedge_symbol:
        logger.info(f"  Hedge with {hedge_size:.2f} lots {hedge_symbol}")
    
    print("\n" + "="*60)
    logger.info("GNN IMPLEMENTATION COMPLETE!")
    print("="*60)
