import logging
logger = logging.getLogger(__name__)
"""On-Chain Analytics Module for Crypto Trading

This module analyzes blockchain data to detect whale movements, miner activity,
DeFi protocol stats, and other on-chain signals for crypto trading.
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
try:
    import requests
except ImportError:
    requests = None
from datetime import datetime, timedelta
import json
from loguru import logger
import numpy
import pandas


@dataclass
class OnChainSignal:
    """Signal generated from on-chain data."""
    asset: str  # Cryptocurrency symbol
    timestamp: datetime
    signal_type: str  # 'bullish', 'bearish', 'neutral'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    source: str  # Type of on-chain data (e.g., 'whale_movement', 'miner_activity')
    metadata: Dict[str, Any]


class OnChainAnalytics:
    """Analyzes blockchain data for trading signals."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the on-chain analytics system.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_keys = self.config.get('api_keys', {})
        
        # Initialize data source handlers
        self.handlers = {
            'whale_tracker': WhaleTracker(self.config.get('whale_tracker_config', {})),
            'miner_analytics': MinerAnalytics(self.config.get('miner_analytics_config', {})),
            'defi_monitor': DeFiMonitor(self.config.get('defi_monitor_config', {})),
            'exchange_flow': ExchangeFlow(self.config.get('exchange_flow_config', {})),
            'network_health': NetworkHealth(self.config.get('network_health_config', {}))
        }
        
        # Configure enabled data sources
        self.enabled_sources = self.config.get('enabled_sources', list(self.handlers.keys()))
        
        logger.info(f"OnChainAnalytics initialized with sources: {self.enabled_sources}")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get on-chain signals for specified crypto assets.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        all_signals = []
        
        for source_name in self.enabled_sources:
            if source_name in self.handlers:
                try:
                    handler = self.handlers[source_name]
                    signals = handler.get_signals(assets)
                    all_signals.extend(signals)
                    logger.info(f"Collected {len(signals)} signals from {source_name}")
                except Exception as e:
                    logger.error(f"Error collecting signals from {source_name}: {e}")
        
        return all_signals
    
    def get_aggregated_signal(self, asset: str, signals: List[OnChainSignal]) -> Dict[str, Any]:
        """Aggregate multiple on-chain signals for a single asset.
        
        Args:
            asset: Cryptocurrency symbol
            signals: List of on-chain signals
            
        Returns:
            Aggregated signal information
        """
        asset_signals = [s for s in signals if s.asset == asset]
        
        if not asset_signals:
            return {
                'asset': asset,
                'signal': 'neutral',
                'strength': 0.0,
                'confidence': 0.0,
                'sources': []
            }
        
        # Calculate weighted average of signal strengths
        # Positive for bullish, negative for bearish
        weighted_strength = 0.0
        total_confidence = 0.0
        
        for signal in asset_signals:
            sign = 1.0 if signal.signal_type == 'bullish' else (-1.0 if signal.signal_type == 'bearish' else 0.0)
            weighted_strength += sign * signal.strength * signal.confidence
            total_confidence += signal.confidence
        
        if total_confidence > 0:
            weighted_strength /= total_confidence
        
        # Determine overall signal
        if weighted_strength > 0.3:
            overall_signal = 'bullish'
        elif weighted_strength < -0.3:
            overall_signal = 'bearish'
        else:
            overall_signal = 'neutral'
        
        return {
            'asset': asset,
            'signal': overall_signal,
            'strength': abs(weighted_strength),
            'confidence': total_confidence / len(asset_signals) if asset_signals else 0.0,
            'sources': [{'source': s.source, 'type': s.signal_type, 'strength': s.strength} for s in asset_signals]
        }


class WhaleTracker:
    """Tracks large wallet movements (whales) on blockchain."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the whale tracker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.min_transaction_value = self.config.get('min_transaction_value', 1000000)  # $1M USD
        self.lookback_hours = self.config.get('lookback_hours', 24)
        
        # Known exchange wallets to filter out internal transfers
        self.exchange_wallets = self.config.get('exchange_wallets', {
            'BTC': [
                '1NDyJtNTjmwk5xPNhjgAMu4HDHigtobu1s',  # Binance
                '3Nxwenay9Z8Lc9JBiywExpnEFiLp6Afp8v',  # Bitstamp
                # Add more exchange wallets as needed
            ],
            'ETH': [
                '0x28c6c06298d514db089934071355e5743bf21d60',  # Binance
                '0x21a31ee1afc51d94c2efccaa2092ad1028285549',  # Binance
                # Add more exchange wallets as needed
            ]
        })
        
        logger.info("WhaleTracker initialized")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get signals from whale movements.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        signals = []
        
        for asset in assets:
            try:
                # In a real implementation, this would call blockchain APIs
                # For demonstration, we'll simulate whale movement data
                
                # Simulate whale transactions
                whale_transactions = self._simulate_whale_transactions(asset)
                
                if not whale_transactions:
                    continue
                
                # Analyze whale movements
                net_flow = sum(tx['amount'] for tx in whale_transactions)
                total_volume = sum(abs(tx['amount']) for tx in whale_transactions)
                
                # Calculate signal based on net flow
                if total_volume > 0:
                    flow_ratio = net_flow / total_volume
                    
                    # Generate signal based on flow ratio
                    if abs(flow_ratio) > 0.2:  # Significant imbalance
                        signal_type = 'bullish' if flow_ratio > 0 else 'bearish'
                        strength = min(1.0, abs(flow_ratio) * 2)
                        
                        signals.append(OnChainSignal(
                            asset=asset,
                            timestamp=datetime.now(),
                            signal_type=signal_type,
                            strength=strength,
                            confidence=0.8,  # Whale movements are strong signals
                            source='whale_movement',
                            metadata={
                                'net_flow': net_flow,
                                'total_volume': total_volume,
                                'flow_ratio': flow_ratio,
                                'transaction_count': len(whale_transactions),
                                'largest_transaction': max(abs(tx['amount']) for tx in whale_transactions)
                            }
                        ))
                
            except Exception as e:
                logger.error(f"Error analyzing whale movements for {asset}: {e}")
        
        return signals
    
    def _simulate_whale_transactions(self, asset: str) -> List[Dict[str, Any]]:
        """Simulate whale transactions for demonstration purposes.
        
        In a real implementation, this would fetch data from blockchain APIs.
        """
        # Simulate 3-8 whale transactions
        num_transactions = np.random.randint(3, 9)
        transactions = []
        
        for _ in range(num_transactions):
            # Simulate transaction amount (1-10M USD)
            amount = np.random.uniform(1, 10) * 1000000
            
            # Randomly make it positive (inflow) or negative (outflow)
            if np.random.random() < 0.5:
                amount = -amount
            
            # Simulate transaction time within lookback period
            hours_ago = np.random.uniform(0, self.lookback_hours)
            timestamp = datetime.now() - timedelta(hours=hours_ago)
            
            transactions.append({
                'timestamp': timestamp,
                'amount': amount,
                'from_address': f'0x{np.random.randint(0, 16**40):040x}',
                'to_address': f'0x{np.random.randint(0, 16**40):040x}'
            })
        
        return transactions


class MinerAnalytics:
    """Analyzes miner behavior and hash rate changes."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the miner analytics.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.lookback_days = self.config.get('lookback_days', 7)
        
        logger.info("MinerAnalytics initialized")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get signals from miner activity.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        signals = []
        
        for asset in assets:
            # Only analyze PoW cryptocurrencies
            if asset not in ['BTC', 'ETH', 'LTC', 'XMR', 'BCH', 'ZEC']:
                continue
            try:
            
                # In a real implementation, this would call blockchain APIs
                # For demonstration, we'll simulate miner data
                
                # Simulate hash rate and miner outflow data
                hash_rate_change = np.random.uniform(-0.15, 0.15)  # -15% to +15%
                miner_outflow_change = np.random.uniform(-0.2, 0.2)  # -20% to +20%
                
                # Hash rate increase is generally bullish (more security)
                # Miner outflow increase is generally bearish (selling pressure)
                
                # Combined signal
                combined_signal = hash_rate_change - miner_outflow_change
                
                if abs(combined_signal) > 0.1:  # Significant change
                    signal_type = 'bullish' if combined_signal > 0 else 'bearish'
                    strength = min(1.0, abs(combined_signal) * 3)
                    
                    signals.append(OnChainSignal(
                        asset=asset,
                        timestamp=datetime.now(),
                        signal_type=signal_type,
                        strength=strength,
                        confidence=0.7,
                        source='miner_activity',
                        metadata={
                            'hash_rate_change': hash_rate_change,
                            'miner_outflow_change': miner_outflow_change,
                            'combined_signal': combined_signal
                        }
                    ))
                
            except Exception as e:
                logger.error(f"Error analyzing miner activity for {asset}: {e}")
        
        return signals


class DeFiMonitor:
    """Monitors DeFi protocols and liquidity pools."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the DeFi monitor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        
        logger.info("DeFiMonitor initialized")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get signals from DeFi protocols.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        signals = []
        
        # Filter for assets that are commonly used in DeFi
        defi_assets = [a for a in assets if a in ['ETH', 'BTC', 'LINK', 'UNI', 'AAVE', 'MKR', 'SNX', 'COMP']]
        
        for asset in defi_assets:
            try:
                # In a real implementation, this would call DeFi protocol APIs
                # For demonstration, we'll simulate DeFi data
                
                # Simulate TVL (Total Value Locked) change
                tvl_change = np.random.uniform(-0.1, 0.2)  # -10% to +20%
                
                # Simulate yield change
                yield_change = np.random.uniform(-0.05, 0.1)  # -5% to +10%
                
                # Combined signal (TVL increase and yield increase are bullish)
                combined_signal = tvl_change + yield_change
                
                if abs(combined_signal) > 0.1:  # Significant change
                    signal_type = 'bullish' if combined_signal > 0 else 'bearish'
                    strength = min(1.0, abs(combined_signal) * 4)
                    
                    signals.append(OnChainSignal(
                        asset=asset,
                        timestamp=datetime.now(),
                        signal_type=signal_type,
                        strength=strength,
                        confidence=0.6,
                        source='defi_activity',
                        metadata={
                            'tvl_change': tvl_change,
                            'yield_change': yield_change,
                            'combined_signal': combined_signal
                        }
                    ))
                
            except Exception as e:
                logger.error(f"Error analyzing DeFi activity for {asset}: {e}")
        
        return signals


class ExchangeFlow:
    """Analyzes cryptocurrency flows to and from exchanges."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the exchange flow analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        self.lookback_hours = self.config.get('lookback_hours', 24)
        
        logger.info("ExchangeFlow initialized")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get signals from exchange flows.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        signals = []
        
        for asset in assets:
            try:
                # In a real implementation, this would call blockchain APIs
                # For demonstration, we'll simulate exchange flow data
                
                # Simulate net flow (negative means outflow from exchanges, generally bullish)
                net_flow = np.random.uniform(-0.05, 0.05)  # -5% to +5% of circulating supply
                
                # Simulate exchange balance change
                balance_change = np.random.uniform(-0.03, 0.03)  # -3% to +3%
                
                # Combined signal (outflow from exchanges is bullish)
                combined_signal = -(net_flow + balance_change)
                
                if abs(combined_signal) > 0.02:  # Significant change
                    signal_type = 'bullish' if combined_signal > 0 else 'bearish'
                    strength = min(1.0, abs(combined_signal) * 20)
                    
                    signals.append(OnChainSignal(
                        asset=asset,
                        timestamp=datetime.now(),
                        signal_type=signal_type,
                        strength=strength,
                        confidence=0.75,
                        source='exchange_flow',
                        metadata={
                            'net_flow': net_flow,
                            'balance_change': balance_change,
                            'combined_signal': combined_signal
                        }
                    ))
                
            except Exception as e:
                logger.error(f"Error analyzing exchange flows for {asset}: {e}")
        
        return signals


class NetworkHealth:
    """Analyzes blockchain network health metrics."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the network health analyzer.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.api_key = self.config.get('api_key', '')
        
        logger.info("NetworkHealth initialized")
    
    def get_signals(self, assets: List[str]) -> List[OnChainSignal]:
        """Get signals from network health metrics.
        
        Args:
            assets: List of cryptocurrency symbols
            
        Returns:
            List of on-chain signals
        """
        signals = []
        
        for asset in assets:
            try:
                # In a real implementation, this would call blockchain APIs
                # For demonstration, we'll simulate network health data
                
                # Simulate transaction count change
                tx_count_change = np.random.uniform(-0.1, 0.2)  # -10% to +20%
                
                # Simulate active addresses change
                active_addr_change = np.random.uniform(-0.1, 0.15)  # -10% to +15%
                
                # Simulate fee levels change
                fee_change = np.random.uniform(-0.2, 0.3)  # -20% to +30%
                
                # Combined signal (more transactions and active addresses are bullish, higher fees can be mixed)
                combined_signal = tx_count_change + active_addr_change - (fee_change * 0.2)
                
                if abs(combined_signal) > 0.1:  # Significant change
                    signal_type = 'bullish' if combined_signal > 0 else 'bearish'
                    strength = min(1.0, abs(combined_signal) * 3)
                    
                    signals.append(OnChainSignal(
                        asset=asset,
                        timestamp=datetime.now(),
                        signal_type=signal_type,
                        strength=strength,
                        confidence=0.65,
                        source='network_health',
                        metadata={
                            'tx_count_change': tx_count_change,
                            'active_addr_change': active_addr_change,
                            'fee_change': fee_change,
                            'combined_signal': combined_signal
                        }
                    ))
                
            except Exception as e:
                logger.error(f"Error analyzing network health for {asset}: {e}")
        
        return signals
