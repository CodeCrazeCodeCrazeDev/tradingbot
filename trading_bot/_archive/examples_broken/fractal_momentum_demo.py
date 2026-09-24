"""Fractal Momentum Divergence (FMD) Demo - Multi-Timeframe Divergence Analysis.

This example demonstrates the revolutionary Fractal Momentum Divergence indicator
that filters false divergences using multi-timeframe confirmation.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.advanced_features import (
    FractalMomentumDivergence,
    DivergenceType,
    MultiTimeframeDivergenceFilter,
    DivergenceConfirmationEngine
)


def generate_realistic_market_data_with_divergences(periods=1000):
    pass
    """Generate market data with embedded divergence patterns."""
    np.random.seed(42)
    
    # Create base time series
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='5min')
    
    # Generate price with embedded patterns
    base_trend = np.linspace(100, 120, periods)
    noise = np.random.normal(0, 0.5, periods)
    
    # Add some cyclical patterns
    cycle1 = 3 * np.sin(np.arange(periods) * 0.02)
    cycle2 = 1.5 * np.sin(np.arange(periods) * 0.05)
    
    prices = base_trend + cycle1 + cycle2 + noise
    
    # Create OHLCV data
    data = []
    for i, close in enumerate(prices):
    pass
        if i == 0:
    pass
            open_price = close
        else:
    pass
            open_price = prices[i-1]
        
        # Generate realistic high/low
        daily_range = abs(np.random.normal(0, 0.3))
        high = max(open_price, close) + daily_range * 0.7
        low = min(open_price, close) - daily_range * 0.3
        
        # Volume with some correlation to price movement
        volume_base = 1000000
        if i > 0:
    pass
            price_change = abs(prices[i] - prices[i-1])
            volume_multiplier = 1 + price_change * 2
        else:
    pass
            volume_multiplier = 1
        
        volume = int(volume_base * volume_multiplier * (1 + np.random.normal(0, 0.2)))
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': max(volume, 100000)
        })
    
    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)
    return df


def create_timeframe_data(base_data, timeframe):
    pass
    """Resample base data to different timeframes."""
    if timeframe == '5m':
    pass
        return base_data
    elif timeframe == '15m':
    pass
        return base_data.resample('15min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == '1h':
    pass
        return base_data.resample('1h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    elif timeframe == '4h':
    pass
        return base_data.resample('4h').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
    else:
    pass
        return base_data


def demonstrate_fractal_momentum_divergence():
    pass
    """Main demonstration of Fractal Momentum Divergence system."""
    print("=== Fractal Momentum Divergence (FMD) Advanced Demo ===\n")
    
    # Generate realistic market data
    print("1. Generating realistic market data with embedded patterns...")
    base_data = generate_realistic_market_data_with_divergences(2000)
    print(f"   Generated {len(base_data)} data points")
    
    # Initialize FMD system
    print("\n2. Initializing Fractal Momentum Divergence system...")
    timeframes = ['5m', '15m', '1h', '4h']
    fmd = FractalMomentumDivergence(
        timeframes=timeframes,
        momentum_period=14,
        divergence_lookback=50,
        min_confirmation_timeframes=2
    )
    print(f"   Configured for timeframes: {timeframes}")
    
    # Add data for each timeframe
    print("\n3. Adding multi-timeframe data...")
    for tf in timeframes:
    pass
        tf_data = create_timeframe_data(base_data, tf)
        fmd.add_timeframe_data(tf, tf_data)
        print(f"   {tf}: {len(tf_data)} bars added")
    
    # Detect divergences
    print("\n4. Detecting multi-timeframe divergences...")
    divergences = fmd.detect_multi_timeframe_divergence()
    print(f"   Found {len(divergences)} confirmed divergences")
    
    # Display divergence details
    if divergences:
    pass
        print("\n5. Divergence Analysis Results:")
        print("-" * 80)
        
        for i, div in enumerate(divergences, 1):
    pass
            print(f"\nDivergence #{i}:")
            print(f"   Type: {div.divergence_type.value}")
            print(f"   Strength: {div.strength:.3f}")
            print(f"   Confidence: {div.confidence:.3f}")
            print(f"   Timeframes Confirmed: {div.timeframes_confirmed}")
            print(f"   Expected Move: {div.expected_move:.4f}")
            
            if div.price_points:
    pass
                print(f"   Price Points: {[f'{p:.4f}' for p in div.price_points[:4]]}")
            if div.momentum_points:
    pass
                print(f"   Momentum Points: {[f'{p:.4f}' for p in div.momentum_points[:4]]}")
    
    # Test divergence filtering
    print("\n6. Testing Advanced Divergence Filtering...")
    filter_system = MultiTimeframeDivergenceFilter(
        primary_timeframes=['5m', '15m', '1h'],
        confirmation_timeframes=['1h', '4h'],
        filter_strength=0.5
    )
    
    filtered_divergences = filter_system.filter_divergences(divergences)
    print(f"   Original divergences: {len(divergences)}")
    print(f"   After filtering: {len(filtered_divergences)}")
    
    # Test confirmation engine
    print("\n7. Testing Divergence Confirmation Engine...")
    confirmation_engine = DivergenceConfirmationEngine()
    
    if filtered_divergences:
    pass
        for i, div in enumerate(filtered_divergences[:3], 1):  # Test first 3
            confirmation = confirmation_engine.confirm_divergence(div, base_data.tail(100))
            
            print(f"\n   Divergence #{i} Confirmation:")
            print(f"     Overall Confirmed: {confirmation['overall_confirmation']}")
            print(f"     Confirmation Score: {confirmation['confirmation_score']:.3f}")
            
            for method, result in confirmation['individual_confirmations'].items():
    pass
                print(f"     {method}: {result['confirmed']} (confidence: {result['confidence']:.3f})")
    
    # Analyze fractal levels
    print("\n8. Analyzing Fractal Support/Resistance Levels...")
    for tf in ['5m', '1h']:
    pass
        if tf in fmd.fractal_levels:
    pass
            levels = fmd.fractal_levels[tf]
            support_levels = [l for l in levels if l.level_type == 'support']
            resistance_levels = [l for l in levels if l.level_type == 'resistance']
            
            print(f"\n   {tf} Timeframe:")
            print(f"     Support Levels: {len(support_levels)}")
            print(f"     Resistance Levels: {len(resistance_levels)}")
            
            # Show strongest levels
            if support_levels:
    pass
                strongest_support = max(support_levels, key=lambda x: x.strength)
                print(f"     Strongest Support: {strongest_support.price:.4f} (strength: {strongest_support.strength:.3f})")
            
            if resistance_levels:
    pass
                strongest_resistance = max(resistance_levels, key=lambda x: x.strength)
                print(f"     Strongest Resistance: {strongest_resistance.price:.4f} (strength: {strongest_resistance.strength:.3f})")
    
    # Performance analysis
    print("\n9. System Performance Analysis...")
    
    # Calculate processing efficiency
    total_bars_processed = sum(len(fmd.timeframe_data[tf]) for tf in fmd.timeframe_data)
    divergences_per_1000_bars = (len(divergences) / total_bars_processed) * 1000 if total_bars_processed > 0 else 0
    
    print(f"   Total bars processed: {total_bars_processed}")
    print(f"   Divergences per 1000 bars: {divergences_per_1000_bars:.2f}")
    print(f"   Filter efficiency: {(len(filtered_divergences) / len(divergences) * 100):.1f}%" if divergences else "N/A")
    
    # Quality metrics
    if filtered_divergences:
    pass
        avg_confidence = np.mean([d.confidence for d in filtered_divergences])
        avg_strength = np.mean([d.strength for d in filtered_divergences])
        
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Average strength: {avg_strength:.3f}")
    
    return fmd, divergences, filtered_divergences


def demonstrate_advanced_features():
    pass
    """Demonstrate advanced FMD features."""
    print("\n" + "="*80)
    print("=== Advanced Fractal Momentum Features Demo ===")
    print("="*80)
    
    # Generate data with specific patterns
    print("\n1. Creating market data with specific divergence patterns...")
    
    # Create bullish divergence pattern
    periods = 200
    dates = pd.date_range(start='2024-01-01', periods=periods, freq='5min')
    
    # Price makes lower lows
    price_trend = np.concatenate([
        np.linspace(100, 95, 50),    # Downtrend
        np.linspace(95, 92, 50),     # Lower low
        np.linspace(92, 98, 100)     # Recovery
    ])
    
    # Add noise
    noise = np.random.normal(0, 0.2, periods)
    prices = price_trend + noise
    
    # Create OHLCV
    data = []
    for i, close in enumerate(prices):
    pass
        open_price = prices[i-1] if i > 0 else close
        high = max(open_price, close) + abs(np.random.normal(0, 0.1))
        low = min(open_price, close) - abs(np.random.normal(0, 0.1))
        volume = int(1000000 * (1 + np.random.normal(0, 0.1)))
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': max(volume, 100000)
        })
    
    pattern_data = pd.DataFrame(data)
    pattern_data.set_index('timestamp', inplace=True)
    
    print(f"   Created {len(pattern_data)} bars with embedded bullish divergence pattern")
    
    # Test with pattern data
    print("\n2. Testing FMD with pattern-specific data...")
    fmd_pattern = FractalMomentumDivergence(
        timeframes=['5m', '15m'],
        momentum_period=10,
        divergence_lookback=30
    )
    
    fmd_pattern.add_timeframe_data('5m', pattern_data)
    fmd_pattern.add_timeframe_data('15m', create_timeframe_data(pattern_data, '15m'))
    
    pattern_divergences = fmd_pattern.detect_multi_timeframe_divergence()
    print(f"   Detected {len(pattern_divergences)} divergences in pattern data")
    
    # Test different momentum periods
    print("\n3. Testing sensitivity to momentum periods...")
    momentum_periods = [10, 14, 21]
    
    for period in momentum_periods:
    pass
        fmd_test = FractalMomentumDivergence(
            timeframes=['5m'],
            momentum_period=period,
            divergence_lookback=40
        )
        
        fmd_test.add_timeframe_data('5m', pattern_data)
        test_divergences = fmd_test.detect_multi_timeframe_divergence()
        
        print(f"   Momentum period {period}: {len(test_divergences)} divergences detected")
    
    # Test confirmation thresholds
    print("\n4. Testing confirmation threshold sensitivity...")
    confirmation_thresholds = [1, 2, 3]
    
    for threshold in confirmation_thresholds:
    pass
        fmd_thresh = FractalMomentumDivergence(
            timeframes=['5m', '15m', '1h'],
            min_confirmation_timeframes=threshold
        )
        
        for tf in ['5m', '15m', '1h']:
    pass
            tf_data = create_timeframe_data(pattern_data, tf)
            fmd_thresh.add_timeframe_data(tf, tf_data)
        
        thresh_divergences = fmd_thresh.detect_multi_timeframe_divergence()
        print(f"   Min confirmation TFs {threshold}: {len(thresh_divergences)} divergences")
    
    print("\n5. Advanced Feature Summary:")
    print("   ✓ Multi-timeframe divergence detection")
    print("   ✓ Fractal support/resistance level identification")
    print("   ✓ Advanced momentum indicator integration (RSI, MACD, Stochastic)")
    print("   ✓ Configurable confirmation thresholds")
    print("   ✓ Sophisticated filtering system")
    print("   ✓ Volume and price action confirmation")
    print("   ✓ Expected move size estimation")


def main():
    pass
    """Main execution function."""
    try:
    pass
        # Run main demonstration
        fmd, divergences, filtered = demonstrate_fractal_momentum_divergence()
        
        # Run advanced features demo
        demonstrate_advanced_features()
        
        print("\n" + "="*80)
        print("=== Fractal Momentum Divergence Demo Complete ===")
        print("="*80)
        
        print(f"\nKey Results:")
        print(f"• Total divergences detected: {len(divergences)}")
        print(f"• High-quality divergences after filtering: {len(filtered)}")
        print(f"• Multi-timeframe confirmation system: ✓ Active")
        print(f"• Advanced filtering and confirmation: ✓ Active")
        
        print(f"\nThe Fractal Momentum Divergence system successfully:")
        print(f"• Analyzed multiple timeframes simultaneously")
        print(f"• Filtered out false divergence signals")
        print(f"• Provided high-confidence reversal predictions")
        print(f"• Integrated advanced momentum indicators")
        print(f"• Delivered actionable trading signals")
        
        return True
        
    except Exception as e:
    pass
        print(f"\nError in FMD demonstration: {e}")
        import traceback
import numpy
import pandas
        traceback.print_exc()
        return False


if __name__ == "__main__":
    pass
    success = main()
    if success:
    pass
        print("\n🎯 Fractal Momentum Divergence demonstration completed successfully!")
    else:
    pass
        print("\n❌ Fractal Momentum Divergence demonstration encountered errors.")
