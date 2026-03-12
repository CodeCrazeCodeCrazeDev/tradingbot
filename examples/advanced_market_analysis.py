#!/usr/bin/env python
"""
Advanced Market Analysis Example

This script demonstrates the advanced market analysis capabilities of the Elite Trading Bot,
including market microstructure analysis, order flow processing, and integrated market analysis.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Import core components
from trading_bot.core.analysis_orchestrator import AnalysisOrchestrator
from trading_bot.data.market_data_stream import MarketDataStream
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("advanced_market_analysis")

# Configuration
CONFIG = {
    "data_stream": {
        "simulate_data": True
    },
    "analysis": {
        "min_confidence": 60.0
    }
}


class MarketMicrostructureAnalyzer:
    """Advanced market microstructure analysis"""
    
    def __init__(self):
        """Initialize the analyzer"""
        logger.info("Initializing Market Microstructure Analyzer")
    
    async def analyze_order_flow(self, data: pd.DataFrame) -> dict:
        """
        Analyze order flow volume profiling
        
        Args:
            data: OHLCV data with volume
            
        Returns:
            Analysis results
        """
        logger.info("Analyzing order flow volume profiling")
        
        # Calculate volume profile
        price_volume = {}
        for _, row in data.iterrows():
            # Simulate price points between low and high
            price_range = np.linspace(row['low'], row['high'], 10)
            volume_per_point = row['volume'] / len(price_range)
            
            for price in price_range:
                price_rounded = round(price, 4)
                if price_rounded in price_volume:
                    price_volume[price_rounded] += volume_per_point
                else:
                    price_volume[price_rounded] = volume_per_point
        
        # Find liquidity zones (areas with high volume)
        sorted_prices = sorted(price_volume.items(), key=lambda x: x[1], reverse=True)
        liquidity_zones = []
        
        # Take top 20% as liquidity zones
        threshold = sorted_prices[0][1] * 0.2
        for price, volume in sorted_prices:
            if volume > threshold:
                liquidity_zones.append({
                    'price': price,
                    'volume': volume
                })
        
        # Calculate price impact model
        # Simple model: impact = k * sqrt(volume)
        k = 0.0001  # Impact factor
        price_impact = {}
        for price, volume in price_volume.items():
            price_impact[price] = k * np.sqrt(volume)
        
        # Detect trade clustering
        clusters = []
        window_size = 5
        for i in range(len(data) - window_size):
            window = data.iloc[i:i+window_size]
            if window['volume'].std() / window['volume'].mean() > 1.5:
                clusters.append({
                    'start_time': window.index[0],
                    'end_time': window.index[-1],
                    'avg_volume': window['volume'].mean(),
                    'volume_std': window['volume'].std()
                })
        
        # Track institutional activity
        institutional_activity = []
        volume_threshold = data['volume'].quantile(0.8)
        for i, row in data.iterrows():
            if row['volume'] > volume_threshold:
                price_change = row['close'] - row['open']
                institutional_activity.append({
                    'time': i,
                    'volume': row['volume'],
                    'price_change': price_change,
                    'impact': abs(price_change) / row['volume'] if row['volume'] > 0 else 0
                })
        
        return {
            'volume_profile': price_volume,
            'liquidity_zones': liquidity_zones,
            'price_impact': price_impact,
            'trade_clusters': clusters,
            'institutional_activity': institutional_activity
        }
    
    async def detect_liquidity_zones(self, data: pd.DataFrame) -> dict:
        """
        Detect liquidity zones
        
        Args:
            data: OHLCV data
            
        Returns:
            Detected liquidity zones
        """
        logger.info("Detecting liquidity zones")
        
        # Calculate volume profile
        volume_profile = {}
        for _, row in data.iterrows():
            # Create price buckets
            bucket_size = 0.0005  # 0.5 pips
            low_bucket = int(row['low'] / bucket_size) * bucket_size
            high_bucket = int(row['high'] / bucket_size) * bucket_size + bucket_size
            
            buckets = np.arange(low_bucket, high_bucket, bucket_size)
            volume_per_bucket = row['volume'] / len(buckets)
            
            for bucket in buckets:
                bucket_rounded = round(bucket, 4)
                if bucket_rounded in volume_profile:
                    volume_profile[bucket_rounded] += volume_per_bucket
                else:
                    volume_profile[bucket_rounded] = volume_per_bucket
        
        # Identify high volume nodes
        mean_volume = np.mean(list(volume_profile.values()))
        std_volume = np.std(list(volume_profile.values()))
        
        high_volume_nodes = {}
        for price, volume in volume_profile.items():
            if volume > mean_volume + std_volume:
                high_volume_nodes[price] = volume
        
        # Cluster nearby high volume nodes into zones
        zones = []
        sorted_prices = sorted(high_volume_nodes.keys())
        
        if sorted_prices:
            current_zone = {
                'start': sorted_prices[0],
                'end': sorted_prices[0],
                'volume': high_volume_nodes[sorted_prices[0]]
            }
            
            for i in range(1, len(sorted_prices)):
                price = sorted_prices[i]
                prev_price = sorted_prices[i-1]
                
                # If prices are close, extend current zone
                if price - prev_price < 0.002:  # 2 pips
                    current_zone['end'] = price
                    current_zone['volume'] += high_volume_nodes[price]
                else:
                    # Save current zone and start a new one
                    zones.append(current_zone)
                    current_zone = {
                        'start': price,
                        'end': price,
                        'volume': high_volume_nodes[price]
                    }
            
            # Add the last zone
            zones.append(current_zone)
        
        return {
            'volume_profile': volume_profile,
            'high_volume_nodes': high_volume_nodes,
            'liquidity_zones': zones
        }


class OrderFlowProcessor:
    """Advanced order flow processing"""
    
    def __init__(self):
        """Initialize the processor"""
        logger.info("Initializing Order Flow Processor")
    
    async def analyze_volume_delta(self, data: pd.DataFrame) -> dict:
        """
        Analyze volume delta
        
        Args:
            data: OHLCV data
            
        Returns:
            Volume delta analysis
        """
        logger.info("Analyzing volume delta")
        
        # Calculate volume delta
        # Positive delta: buying pressure
        # Negative delta: selling pressure
        delta = []
        
        for _, row in data.iterrows():
            # Simulate volume delta based on price movement
            if row['close'] > row['open']:
                # Bullish candle: more buying than selling
                buy_volume = row['volume'] * (0.5 + 0.5 * (row['close'] - row['open']) / (row['high'] - row['low']))
                sell_volume = row['volume'] - buy_volume
            else:
                # Bearish candle: more selling than buying
                sell_volume = row['volume'] * (0.5 + 0.5 * (row['open'] - row['close']) / (row['high'] - row['low']))
                buy_volume = row['volume'] - sell_volume
            
            delta.append({
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'delta': buy_volume - sell_volume,
                'delta_ratio': (buy_volume - sell_volume) / row['volume'] if row['volume'] > 0 else 0
            })
        
        # Calculate cumulative delta
        cumulative_delta = 0
        cum_delta = []
        
        for d in delta:
            cumulative_delta += d['delta']
            cum_delta.append(cumulative_delta)
        
        return {
            'delta': delta,
            'cumulative_delta': cum_delta
        }
    
    async def detect_price_absorption(self, data: pd.DataFrame) -> dict:
        """
        Detect price absorption patterns
        
        Args:
            data: OHLCV data
            
        Returns:
            Detected absorption patterns
        """
        logger.info("Detecting price absorption patterns")
        
        absorption_patterns = []
        
        # Look for price absorption patterns
        # 1. High volume but small price movement
        # 2. Multiple tests of the same level with decreasing volume
        
        # Calculate average true range for volatility reference
        atr = []
        for i in range(1, len(data)):
            tr1 = data['high'].iloc[i] - data['low'].iloc[i]
            tr2 = abs(data['high'].iloc[i] - data['close'].iloc[i-1])
            tr3 = abs(data['low'].iloc[i] - data['close'].iloc[i-1])
            atr.append(max(tr1, tr2, tr3))
        
        avg_atr = np.mean(atr) if atr else 0
        
        # Detect high volume with small price movement
        for i in range(len(data)):
            row = data.iloc[i]
            price_range = row['high'] - row['low']
            
            # If price range is small relative to ATR but volume is high
            if price_range < 0.5 * avg_atr and row['volume'] > data['volume'].quantile(0.7):
                absorption_patterns.append({
                    'type': 'high_volume_small_range',
                    'time': row.name,
                    'price': row['close'],
                    'volume': row['volume'],
                    'price_range': price_range
                })
        
        # Detect multiple tests of the same level
        price_levels = {}
        level_precision = 0.001  # 1 pip
        
        for i, row in data.iterrows():
            # Round prices to nearest level
            high_level = round(row['high'] / level_precision) * level_precision
            low_level = round(row['low'] / level_precision) * level_precision
            
            # Track tests of high level
            if high_level in price_levels:
                price_levels[high_level].append({
                    'time': i,
                    'price': row['high'],
                    'volume': row['volume']
                })
            else:
                price_levels[high_level] = [{
                    'time': i,
                    'price': row['high'],
                    'volume': row['volume']
                }]
            
            # Track tests of low level
            if low_level in price_levels:
                price_levels[low_level].append({
                    'time': i,
                    'price': row['low'],
                    'volume': row['volume']
                })
            else:
                price_levels[low_level] = [{
                    'time': i,
                    'price': row['low'],
                    'volume': row['volume']
                }]
        
        # Find levels with multiple tests and decreasing volume
        for level, tests in price_levels.items():
            if len(tests) >= 3:
                # Check if volume is decreasing
                volumes = [test['volume'] for test in tests]
                if volumes[0] > volumes[-1] and volumes[1] > volumes[-1]:
                    absorption_patterns.append({
                        'type': 'multiple_tests_decreasing_volume',
                        'price_level': level,
                        'tests': tests,
                        'test_count': len(tests)
                    })
        
        return {
            'absorption_patterns': absorption_patterns,
            'price_levels': price_levels
        }
    
    async def detect_exhaustion(self, data: pd.DataFrame) -> dict:
        """
        Detect exhaustion patterns
        
        Args:
            data: OHLCV data
            
        Returns:
            Detected exhaustion patterns
        """
        logger.info("Detecting exhaustion patterns")
        
        exhaustion_patterns = []
        
        # Calculate volume moving average
        volume_ma = data['volume'].rolling(window=5).mean()
        
        # Look for volume climax
        for i in range(5, len(data)):
            row = data.iloc[i]
            
            # Volume spike
            if row['volume'] > 2 * volume_ma.iloc[i]:
                # Check if it's a potential exhaustion
                price_change = row['close'] - row['open']
                price_position = (row['close'] - row['low']) / (row['high'] - row['low']) if row['high'] != row['low'] else 0.5
                
                # Bullish exhaustion: high volume, long upper wick
                if price_change > 0 and price_position < 0.3:
                    exhaustion_patterns.append({
                        'type': 'bullish_exhaustion',
                        'time': row.name,
                        'price': row['close'],
                        'volume': row['volume'],
                        'volume_ratio': row['volume'] / volume_ma.iloc[i],
                        'price_position': price_position
                    })
                
                # Bearish exhaustion: high volume, long lower wick
                elif price_change < 0 and price_position > 0.7:
                    exhaustion_patterns.append({
                        'type': 'bearish_exhaustion',
                        'time': row.name,
                        'price': row['close'],
                        'volume': row['volume'],
                        'volume_ratio': row['volume'] / volume_ma.iloc[i],
                        'price_position': price_position
                    })
        
        return {
            'exhaustion_patterns': exhaustion_patterns
        }


class IntegratedMarketAnalyzer:
    """Integrated market analyzer"""
    
    def __init__(self):
        """Initialize the analyzer"""
        logger.info("Initializing Integrated Market Analyzer")
        self.microstructure = MarketMicrostructureAnalyzer()
        self.order_flow = OrderFlowProcessor()
    
    async def analyze(self, data: pd.DataFrame) -> dict:
        """
        Perform comprehensive market analysis
        
        Args:
            data: OHLCV data
            
        Returns:
            Comprehensive analysis results
        """
        logger.info("Performing comprehensive market analysis")
        
        # Perform individual analyses
        microstructure_results = await self.microstructure.analyze_order_flow(data)
        liquidity_zones = await self.microstructure.detect_liquidity_zones(data)
        volume_delta = await self.order_flow.analyze_volume_delta(data)
        absorption_patterns = await self.order_flow.detect_price_absorption(data)
        exhaustion_patterns = await self.order_flow.detect_exhaustion(data)
        
        # Combine signals
        signals = []
        
        # Check for strong buying pressure
        if volume_delta['cumulative_delta'][-1] > 0 and volume_delta['delta'][-1]['delta_ratio'] > 0.6:
            signals.append({
                'type': 'strong_buying_pressure',
                'confidence': 0.8,
                'direction': 1,  # Buy
                'evidence': {
                    'cumulative_delta': volume_delta['cumulative_delta'][-1],
                    'delta_ratio': volume_delta['delta'][-1]['delta_ratio']
                }
            })
        
        # Check for strong selling pressure
        elif volume_delta['cumulative_delta'][-1] < 0 and volume_delta['delta'][-1]['delta_ratio'] < -0.6:
            signals.append({
                'type': 'strong_selling_pressure',
                'confidence': 0.8,
                'direction': -1,  # Sell
                'evidence': {
                    'cumulative_delta': volume_delta['cumulative_delta'][-1],
                    'delta_ratio': volume_delta['delta'][-1]['delta_ratio']
                }
            })
        
        # Check for absorption at support
        current_price = data['close'].iloc[-1]
        for pattern in absorption_patterns['absorption_patterns']:
            if pattern['type'] == 'high_volume_small_range':
                if abs(current_price - pattern['price']) < 0.001:
                    signals.append({
                        'type': 'absorption_at_support',
                        'confidence': 0.7,
                        'direction': 1,  # Buy
                        'evidence': pattern
                    })
        
        # Check for exhaustion
        for pattern in exhaustion_patterns['exhaustion_patterns']:
            if pattern['type'] == 'bullish_exhaustion':
                signals.append({
                    'type': 'bullish_exhaustion',
                    'confidence': 0.75,
                    'direction': -1,  # Sell (counter-trend)
                    'evidence': pattern
                })
            elif pattern['type'] == 'bearish_exhaustion':
                signals.append({
                    'type': 'bearish_exhaustion',
                    'confidence': 0.75,
                    'direction': 1,  # Buy (counter-trend)
                    'evidence': pattern
                })
        
        # Check for price approaching liquidity zone
        for zone in liquidity_zones['liquidity_zones']:
            zone_mid = (zone['start'] + zone['end']) / 2
            if abs(current_price - zone_mid) < 0.002:  # Within 2 pips
                if current_price < zone_mid:
                    signals.append({
                        'type': 'approaching_liquidity_zone',
                        'confidence': 0.65,
                        'direction': -1,  # Sell into liquidity
                        'evidence': {
                            'zone': zone,
                            'current_price': current_price,
                            'distance': abs(current_price - zone_mid)
                        }
                    })
                else:
                    signals.append({
                        'type': 'approaching_liquidity_zone',
                        'confidence': 0.65,
                        'direction': 1,  # Buy into liquidity
                        'evidence': {
                            'zone': zone,
                            'current_price': current_price,
                            'distance': abs(current_price - zone_mid)
                        }
                    })
        
        # Calculate market state
        bullish_signals = [s for s in signals if s['direction'] > 0]
        bearish_signals = [s for s in signals if s['direction'] < 0]
        
        bullish_confidence = sum(s['confidence'] for s in bullish_signals) / len(bullish_signals) if bullish_signals else 0
        bearish_confidence = sum(s['confidence'] for s in bearish_signals) / len(bearish_signals) if bearish_signals else 0
        
        if bullish_confidence > bearish_confidence:
            market_state = 'bullish'
            bias = bullish_confidence - bearish_confidence
        elif bearish_confidence > bullish_confidence:
            market_state = 'bearish'
            bias = bearish_confidence - bullish_confidence
        else:
            market_state = 'neutral'
            bias = 0
        
        # Combine all results
        return {
            'microstructure': microstructure_results,
            'liquidity_zones': liquidity_zones,
            'volume_delta': volume_delta,
            'absorption_patterns': absorption_patterns,
            'exhaustion_patterns': exhaustion_patterns,
            'signals': signals,
            'market_state': {
                'state': market_state,
                'bias': bias,
                'bullish_confidence': bullish_confidence,
                'bearish_confidence': bearish_confidence
            }
        }
    
    def visualize_analysis(self, data: pd.DataFrame, analysis_results: dict, save_path: str = None):
        """
        Visualize analysis results
        
        Args:
            data: OHLCV data
            analysis_results: Analysis results
            save_path: Path to save the visualization
        """
        logger.info("Visualizing analysis results")
        
        # Create figure with subplots
        fig, axs = plt.subplots(4, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [3, 1, 1, 1]})
        
        # Plot price chart
        axs[0].set_title('Price Chart with Liquidity Zones')
        axs[0].plot(data.index, data['close'], label='Close Price')
        
        # Plot liquidity zones
        for zone in analysis_results['liquidity_zones']['liquidity_zones']:
            zone_mid = (zone['start'] + zone['end']) / 2
            axs[0].axhspan(zone['start'], zone['end'], alpha=0.3, color='green', label=f'Liquidity Zone ({zone_mid:.4f})')
        
        # Plot institutional activity
        for activity in analysis_results['microstructure']['institutional_activity']:
            if activity['price_change'] > 0:
                axs[0].scatter(activity['time'], data.loc[activity['time'], 'close'], 
                               marker='^', color='green', s=activity['volume']/10, 
                               label='Institutional Buy' if 'inst_buy' not in locals() else "")
                locals()['inst_buy'] = True
            else:
                axs[0].scatter(activity['time'], data.loc[activity['time'], 'close'], 
                               marker='v', color='red', s=activity['volume']/10, 
                               label='Institutional Sell' if 'inst_sell' not in locals() else "")
                locals()['inst_sell'] = True
        
        # Plot absorption patterns
        for pattern in analysis_results['absorption_patterns']['absorption_patterns']:
            if pattern['type'] == 'high_volume_small_range':
                axs[0].scatter(pattern['time'], pattern['price'], marker='o', color='purple', s=100, 
                               label='Absorption Pattern' if 'absorption' not in locals() else "")
                locals()['absorption'] = True
        
        # Plot exhaustion patterns
        for pattern in analysis_results['exhaustion_patterns']['exhaustion_patterns']:
            if pattern['type'] == 'bullish_exhaustion':
                axs[0].scatter(pattern['time'], pattern['price'], marker='*', color='blue', s=150, 
                               label='Bullish Exhaustion' if 'bull_exhaust' not in locals() else "")
                locals()['bull_exhaust'] = True
            elif pattern['type'] == 'bearish_exhaustion':
                axs[0].scatter(pattern['time'], pattern['price'], marker='*', color='orange', s=150, 
                               label='Bearish Exhaustion' if 'bear_exhaust' not in locals() else "")
                locals()['bear_exhaust'] = True
        
        axs[0].legend()
        axs[0].grid(True)
        
        # Plot volume
        axs[1].set_title('Volume')
        axs[1].bar(data.index, data['volume'], color='blue', alpha=0.6)
        axs[1].grid(True)
        
        # Plot volume delta
        delta_values = [d['delta'] for d in analysis_results['volume_delta']['delta']]
        colors = ['green' if d > 0 else 'red' for d in delta_values]
        
        axs[2].set_title('Volume Delta')
        axs[2].bar(data.index, delta_values, color=colors, alpha=0.6)
        axs[2].plot(data.index, analysis_results['volume_delta']['cumulative_delta'], color='black', label='Cumulative Delta')
        axs[2].axhline(y=0, color='gray', linestyle='-', alpha=0.3)
        axs[2].legend()
        axs[2].grid(True)
        
        # Plot signals
        axs[3].set_title('Market State and Signals')
        
        # Plot market state as background color
        market_state = analysis_results['market_state']['state']
        bias = analysis_results['market_state']['bias']
        
        if market_state == 'bullish':
            axs[3].axhspan(0, 1, alpha=bias, color='green')
        elif market_state == 'bearish':
            axs[3].axhspan(0, 1, alpha=bias, color='red')
        
        # Plot signals
        for i, signal in enumerate(analysis_results['signals']):
            color = 'green' if signal['direction'] > 0 else 'red'
            axs[3].bar(i, signal['confidence'], color=color, alpha=0.7)
            axs[3].text(i, signal['confidence'] + 0.05, signal['type'], ha='center', rotation=90, fontsize=8)
        
        axs[3].set_ylim(0, 1.2)
        axs[3].set_xlim(-1, len(analysis_results['signals']))
        axs[3].grid(True)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Visualization saved to {save_path}")
        else:
            plt.show()


async def main():
    """Main function"""
    logger.info("Starting Advanced Market Analysis Example")
    
    # Create output directory
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize components
    data_stream = MarketDataStream(CONFIG.get("data_stream", {}))
    analyzer = IntegratedMarketAnalyzer()
    
    try:
        # Connect to data stream
        await data_stream.connect()
        
        # Get OHLCV data
        symbol = "EURUSD"
        timeframe = "M15"
        
        logger.info(f"Getting OHLCV data for {symbol} {timeframe}")
        ohlcv_data = await data_stream.get_ohlcv(symbol, timeframe, 100)
        
        if ohlcv_data is None or len(ohlcv_data) == 0:
            logger.error("Failed to get OHLCV data")
            return
        
        logger.info(f"Got {len(ohlcv_data)} bars of OHLCV data")
        
        # Perform analysis
        analysis_results = await analyzer.analyze(ohlcv_data)
        
        # Print summary
        logger.info("Analysis Summary:")
        logger.info(f"Market State: {analysis_results['market_state']['state']} (Bias: {analysis_results['market_state']['bias']:.2f})")
        logger.info(f"Detected {len(analysis_results['liquidity_zones']['liquidity_zones'])} liquidity zones")
        logger.info(f"Detected {len(analysis_results['absorption_patterns']['absorption_patterns'])} absorption patterns")
        logger.info(f"Detected {len(analysis_results['exhaustion_patterns']['exhaustion_patterns'])} exhaustion patterns")
        logger.info(f"Generated {len(analysis_results['signals'])} trading signals")
        
        # Print signals
        logger.info("Trading Signals:")
        for signal in analysis_results['signals']:
            direction = "BUY" if signal['direction'] > 0 else "SELL"
            logger.info(f"  {direction} signal: {signal['type']} (Confidence: {signal['confidence']:.2f})")
        
        # Visualize analysis
        analyzer.visualize_analysis(ohlcv_data, analysis_results, save_path="examples/output/market_analysis.png")
        logger.info("Analysis visualization saved to examples/output/market_analysis.png")
        
    except Exception as e:
        logger.exception(f"Error in analysis: {e}")
    finally:
        # Disconnect from data stream
        await data_stream.disconnect()
    
    logger.info("Advanced Market Analysis Example completed")


if __name__ == "__main__":
    asyncio.run(main())
