"""
Offline RL Dataset Builder

Converts historical trade logs to RL dataset format for offline training.
"""

import os
import json
import logging
import numpy as np
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class OfflineRLDataset:
    """Offline RL dataset for training and evaluation."""
    states: np.ndarray
    actions: np.ndarray
    rewards: np.ndarray
    next_states: np.ndarray
    dones: np.ndarray
    info: Dict[str, Any]
    feature_names: List[str]
    action_names: List[str]
    
    @property
    def num_samples(self) -> int:
        """Get number of samples in dataset."""
        return len(self.states)
    
    def split(self, train_ratio=0.7, val_ratio=0.15) -> Tuple['OfflineRLDataset', 'OfflineRLDataset', 'OfflineRLDataset']:
        """
        Split dataset into train, validation, and test sets.
        
        Args:
            train_ratio: Ratio of training data
            val_ratio: Ratio of validation data
        
        Returns:
            Tuple of (train, val, test) datasets
        """
        n = self.num_samples
        train_idx = int(n * train_ratio)
        val_idx = train_idx + int(n * val_ratio)
        
        # Create train dataset
        train = OfflineRLDataset(
            states=self.states[:train_idx],
            actions=self.actions[:train_idx],
            rewards=self.rewards[:train_idx],
            next_states=self.next_states[:train_idx],
            dones=self.dones[:train_idx],
            info={k: v[:train_idx] for k, v in self.info.items()},
            feature_names=self.feature_names,
            action_names=self.action_names
        )
        
        # Create validation dataset
        val = OfflineRLDataset(
            states=self.states[train_idx:val_idx],
            actions=self.actions[train_idx:val_idx],
            rewards=self.rewards[train_idx:val_idx],
            next_states=self.next_states[train_idx:val_idx],
            dones=self.dones[train_idx:val_idx],
            info={k: v[train_idx:val_idx] for k, v in self.info.items()},
            feature_names=self.feature_names,
            action_names=self.action_names
        )
        
        # Create test dataset
        test = OfflineRLDataset(
            states=self.states[val_idx:],
            actions=self.actions[val_idx:],
            rewards=self.rewards[val_idx:],
            next_states=self.next_states[val_idx:],
            dones=self.dones[val_idx:],
            info={k: v[val_idx:] for k, v in self.info.items()},
            feature_names=self.feature_names,
            action_names=self.action_names
        )
        
        logger.info(f"Split dataset: train={train.num_samples}, val={val.num_samples}, test={test.num_samples}")
        
        return train, val, test
    
    def to_d3rlpy(self):
        """
        Convert to d3rlpy dataset format.
        
        Returns:
            d3rlpy MDPDataset
        """
        try:
            from d3rlpy.dataset import MDPDataset
            return MDPDataset(
                observations=self.states,
                actions=self.actions,
                rewards=self.rewards,
                terminals=self.dones,
                episode_terminals=self.dones
            )
        except ImportError:
            logger.error("d3rlpy not installed. Please install with: pip install d3rlpy")
            return None
    
    def save(self, file_path: str):
        """
        Save dataset to file.
        
        Args:
            file_path: Path to save file
        """
        data = {
            'states': self.states,
            'actions': self.actions,
            'rewards': self.rewards,
            'next_states': self.next_states,
            'dones': self.dones,
            'info': self.info,
            'feature_names': self.feature_names,
            'action_names': self.action_names
        }
        
        np.savez_compressed(file_path, **data)
        logger.info(f"Dataset saved to {file_path}")
    
    @classmethod
    def load(cls, file_path: str) -> 'OfflineRLDataset':
        """
        Load dataset from file.
        
        Args:
            file_path: Path to load file
        
        Returns:
            OfflineRLDataset
        """
        data = np.load(file_path, allow_pickle=True)
        
        dataset = cls(
            states=data['states'],
            actions=data['actions'],
            rewards=data['rewards'],
            next_states=data['next_states'],
            dones=data['dones'],
            info=data['info'].item(),
            feature_names=data['feature_names'].tolist(),
            action_names=data['action_names'].tolist()
        )
        
        logger.info(f"Dataset loaded from {file_path}: {dataset.num_samples} samples")
        return dataset


def build_dataset_from_trades(
    trades_dir: str,
    feature_names: Optional[List[str]] = None,
    min_samples: int = 1000,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> OfflineRLDataset:
    """
    Build offline RL dataset from trade logs.
    
    Args:
        trades_dir: Directory with trade logs
        feature_names: List of features to include (None for all)
        min_samples: Minimum number of samples required
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        OfflineRLDataset
    """
    logger.info(f"Building offline RL dataset from {trades_dir}")
    
    # Parse date range
    if start_date:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    else:
        start_dt = datetime.now() - timedelta(days=180)  # Default: last 6 months
    
    if end_date:
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    else:
        end_dt = datetime.now()
    
    logger.info(f"Date range: {start_dt.date()} to {end_dt.date()}")
    
    # Find trade log files
    trades_path = Path(trades_dir)
    log_files = list(trades_path.glob("trades_*.jsonl"))
    
    if not log_files:
        logger.error(f"No trade logs found in {trades_dir}")
        raise ValueError(f"No trade logs found in {trades_dir}")
    
    # Load and process trades
    all_trades = []
    for log_file in log_files:
        # Extract date from filename
        try:
            file_date = datetime.strptime(log_file.stem.split('_')[1], "%Y%m%d")
            if file_date < start_dt or file_date > end_dt:
                continue
        except Exception:
            # If can't parse date, include file
            pass
        
        logger.info(f"Processing {log_file}")
        
        # Load trades from file
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    trade = json.loads(line)
                    all_trades.append(trade)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in {log_file}")
    
    logger.info(f"Loaded {len(all_trades)} trades")
    
    if len(all_trades) < min_samples:
        logger.warning(f"Only {len(all_trades)} trades found, minimum required: {min_samples}")
        if len(all_trades) == 0:
            raise ValueError("No trades found in specified date range")
    
    # Extract features, actions, rewards
    states = []
    actions = []
    rewards = []
    next_states = []
    dones = []
    timestamps = []
    symbols = []
    trade_ids = []
    
    # Determine action mapping
    action_map = {'long': 0, 'short': 1, 'hold': 2}
    action_names = ['long', 'short', 'hold']
    
    # Determine feature names if not provided
    if not feature_names and all_trades:
        # Use features from first trade
        first_trade = all_trades[0]
        if 'inputs' in first_trade and 'features' in first_trade['inputs']:
            feature_names = list(first_trade['inputs']['features'].keys())
        else:
            logger.error("Could not determine feature names from trades")
            raise ValueError("Could not determine feature names from trades")
    
    # Process each trade
    for trade in all_trades:
        # Skip trades without required fields
        if not all(k in trade for k in ['inputs', 'model_outputs', 'outcome']):
            continue
        
        # Extract state (features)
        if 'features' in trade['inputs']:
            # Extract specified features or all features
            if feature_names:
                state = [trade['inputs']['features'].get(f, 0.0) for f in feature_names]
            else:
                state = list(trade['inputs']['features'].values())
                feature_names = list(trade['inputs']['features'].keys())
        else:
            continue
        
        # Extract action
        if 'policy' in trade['model_outputs']:
            action = action_map.get(trade['model_outputs']['policy'], 2)  # Default to 'hold'
        else:
            continue
        
        # Extract reward
        if 'pnl' in trade['outcome']:
            reward = float(trade['outcome']['pnl'])
        else:
            continue
        
        # For simplicity, use same state as next_state
        # In a real implementation, you would have the actual next state
        next_state = state
        
        # All trades are terminal states in this dataset
        done = True
        
        # Store metadata
        timestamp = trade.get('timestamp', '')
        symbol = trade.get('symbol', '')
        trade_id = trade.get('trade_id', '')
        
        # Append to lists
        states.append(state)
        actions.append(action)
        rewards.append(reward)
        next_states.append(next_state)
        dones.append(done)
        timestamps.append(timestamp)
        symbols.append(symbol)
        trade_ids.append(trade_id)
    
    # Convert to numpy arrays
    states_array = np.array(states, dtype=np.float32)
    actions_array = np.array(actions, dtype=np.int32)
    rewards_array = np.array(rewards, dtype=np.float32)
    next_states_array = np.array(next_states, dtype=np.float32)
    dones_array = np.array(dones, dtype=np.bool_)
    
    # Create info dict
    info = {
        'timestamps': np.array(timestamps),
        'symbols': np.array(symbols),
        'trade_ids': np.array(trade_ids)
    }
    
    # Create dataset
    dataset = OfflineRLDataset(
        states=states_array,
        actions=actions_array,
        rewards=rewards_array,
        next_states=next_states_array,
        dones=dones_array,
        info=info,
        feature_names=feature_names,
        action_names=action_names
    )
    
    logger.info(f"Created dataset with {dataset.num_samples} samples")
    logger.info(f"Features: {feature_names}")
    logger.info(f"Actions: {action_names}")
    
    return dataset


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    # Build dataset from trades
    dataset = build_dataset_from_trades(
        trades_dir="logs/structured_trades",
        start_date="2025-01-01",
        end_date="2025-10-01"
    )
    
    # Split dataset
    train, val, test = dataset.split()
    
    # Save datasets
    os.makedirs("data/offline_rl", exist_ok=True)
    train.save("data/offline_rl/train.npz")
    val.save("data/offline_rl/val.npz")
    test.save("data/offline_rl/test.npz")
