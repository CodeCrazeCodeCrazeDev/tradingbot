"""Advanced Features Demo for Elite Trading Bot.

This demo showcases all the advanced features implemented:
- Sentiment Analysis AI
- Institutional Order Flow Detection
- Multi-Timeframe Intelligence
- Trade Heatmaps
- Security System
- Performance Attribution
- Gamified Dashboard
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
import matplotlib.pyplot as plt

# Import the advanced features
from trading_bot.ml.sentiment import SentimentAnalyzer, SentimentSource, MarketRegime
from trading_bot.analysis.institutional_order_flow import InstitutionalOrderFlowDetector, OrderType
from trading_bot.analysis.multi_timeframe_intelligence import MultiTimeframeIntelligence, TimeFrame, TrendDirection
from trading_bot.analysis.trade_heatmap import TradeHeatmap, HeatmapType
from trading_bot.security.security_system import SecuritySystem, SecurityLevel
from trading_bot.dashboard.performance_attribution import PerformanceAttributionSystem, AttributionFactor
from trading_bot.dashboard.gamified_dashboard import GamifiedDashboard
from trading_bot.adaptive_systems.adaptive_risk import AdaptiveRiskManager
from trading_bot.adaptive_systems.market_regime import MarketRegimeDetector
import numpy
import pandas


class AdvancedFeaturesDemo:
    """Comprehensive demo of all advanced trading bot features."""
    
    def __init__(self):
        """Initialize all advanced systems."""
        print("🚀 Initializing Elite Trading Bot Advanced Features Demo")
        
        # Initialize sentiment analysis
        self.sentiment_analyzer = SentimentAnalyzer({
            'real_time_enabled': True,
            'adaptive_learning': True,
            'fraud_detection': True
        })
        
        # Initialize order flow detection
        self.order_flow_detector = InstitutionalOrderFlowDetector({
            'min_block_volume': 100,
            'iceberg_threshold': 0.7
        })
        
        # Initialize multi-timeframe intelligence
        self.mtf_intelligence = MultiTimeframeIntelligence({
            'timeframes': [TimeFrame.M5, TimeFrame.M15, TimeFrame.H1, TimeFrame.H4],
            'confluence_threshold': 0.05
        })
        
        # Initialize trade heatmap
        self.trade_heatmap = TradeHeatmap({
            'price_resolution': 100,
            'color_map': 'viridis'
        })
        
        # Initialize security system
        self.security_system = SecuritySystem({
            'security_level': 'HIGH',
            'enable_heartbeat': True,
            'fraud_detector_config': {'anomaly_threshold': 0.8}
        })
        
        # Initialize performance attribution
        self.performance_attribution = PerformanceAttributionSystem({
            'min_sample_size': 5,
            'lookback_days': 30
        })
        
        # Initialize gamified dashboard
        self.gamified_dashboard = GamifiedDashboard()
        
        # Initialize risk management
        self.risk_manager = AdaptiveRiskManager({
            'base_risk_per_trade': 0.02,
            'max_drawdown': 0.15
        })
        
        # Initialize regime detector
        self.regime_detector = MarketRegimeDetector({
            'lookback_period': 100,
            'volatility_window': 20
        })
        
        print("✅ All systems initialized successfully!")
    
    def generate_sample_data(self) -> Dict[str, pd.DataFrame]:
        """Generate sample market data for demonstration."""
        print("📊 Generating sample market data...")
        
        # Generate sample OHLCV data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='1H')
        np.random.seed(42)  # For reproducible results
        
        # Generate realistic price movements
        initial_price = 1.1000
        returns = np.random.normal(0, 0.001, len(dates))  # 0.1% hourly volatility
        prices = initial_price * np.exp(np.cumsum(returns))
        
        # Create OHLCV data
        data = []
        for i, (date, price) in enumerate(zip(dates, prices)):
            high = price * (1 + abs(np.random.normal(0, 0.0005)))
            low = price * (1 - abs(np.random.normal(0, 0.0005)))
            open_price = prices[i-1] if i > 0 else price
            close_price = price
            volume = np.random.randint(1000, 10000)
            
            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close_price,
                'volume': volume,
                'buy_volume': volume * np.random.uniform(0.4, 0.6),
                'sell_volume': volume * np.random.uniform(0.4, 0.6)
            })
        
        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        
        # Create different timeframe data
        timeframe_data = {
            TimeFrame.M5: df.resample('5T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'buy_volume': 'sum',
                'sell_volume': 'sum'
            }).dropna(),
            TimeFrame.M15: df.resample('15T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'buy_volume': 'sum',
                'sell_volume': 'sum'
            }).dropna(),
            TimeFrame.H1: df.resample('1H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'buy_volume': 'sum',
                'sell_volume': 'sum'
            }).dropna(),
            TimeFrame.H4: df.resample('4H').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                'buy_volume': 'sum',
                'sell_volume': 'sum'
            }).dropna()
        }
        
        print(f"✅ Generated data for {len(timeframe_data)} timeframes")
        return timeframe_data
    
    def demo_sentiment_analysis(self):
        """Demonstrate sentiment analysis capabilities."""
        print("\n🧠 SENTIMENT ANALYSIS DEMO")
        print("=" * 50)
        
        # Analyze news sentiment
        news_sentiment = self.sentiment_analyzer.analyze_news('EURUSD', days=2)
        print(f"📰 News Sentiment: {news_sentiment['sentiment']} "
              f"(Score: {news_sentiment['score']:.2f}, "
              f"Confidence: {news_sentiment['confidence']:.1f}%)")
        
        # Analyze social media sentiment
        social_sentiment = self.sentiment_analyzer.analyze_social_media('EURUSD', hours=12)
        print(f"📱 Social Media Sentiment: {social_sentiment['sentiment']} "
              f"(Score: {social_sentiment['score']:.2f}, "
              f"Confidence: {social_sentiment['confidence']:.1f}%)")
        
        # Get overall market mood
        market_mood = self.sentiment_analyzer.get_market_mood('EURUSD', MarketRegime.TRENDING_BULL)
        print(f"🎯 Market Mood: {market_mood['mood']} "
              f"(Score: {market_mood['score']:.2f}, "
              f"Confidence: {market_mood['confidence']:.1f}%)")
        
        print(f"🔍 Manipulation Probability: {market_mood['manipulation_probability']:.2%}")
    
    def demo_order_flow_detection(self, market_data: pd.DataFrame):
        """Demonstrate institutional order flow detection."""
        print("\n🏛️ INSTITUTIONAL ORDER FLOW DETECTION DEMO")
        print("=" * 50)
        
        # Detect iceberg orders
        iceberg_signals = self.order_flow_detector.detect_iceberg_orders(market_data)
        print(f"🧊 Detected {len(iceberg_signals)} iceberg order patterns")
        
        for signal in iceberg_signals[:3]:  # Show first 3
            print(f"   • Price: {signal.price_level:.5f}, "
                  f"Volume: {signal.volume:.0f}, "
                  f"Confidence: {signal.confidence:.2f}")
        
        # Analyze volume profile
        volume_profile = self.order_flow_detector.analyze_volume_profile(market_data)
        if volume_profile['status'] == 'success':
            print(f"📊 Volume Profile Analysis:")
            print(f"   • Point of Control: {volume_profile['poc']:.5f}")
            print(f"   • Value Area: {volume_profile['value_area_low']:.5f} - {volume_profile['value_area_high']:.5f}")
            print(f"   • High Volume Nodes: {len(volume_profile['high_volume_nodes'])}")
        
        # Detect stop hunts
        stop_hunts = self.order_flow_detector.detect_stop_hunts(market_data)
        print(f"🎯 Detected {len(stop_hunts)} stop hunting patterns")
        
        # Detect liquidity pools
        liquidity_pools = self.order_flow_detector.detect_liquidity_pools(market_data)
        if liquidity_pools['status'] == 'success':
            print(f"💧 Liquidity Analysis:")
            print(f"   • Support Pools: {len(liquidity_pools['support_pools'])}")
            print(f"   • Resistance Pools: {len(liquidity_pools['resistance_pools'])}")
    
    def demo_multi_timeframe_intelligence(self, timeframe_data: Dict[TimeFrame, pd.DataFrame]):
        """Demonstrate multi-timeframe intelligence."""
        print("\n⏰ MULTI-TIMEFRAME INTELLIGENCE DEMO")
        print("=" * 50)
        
        # Analyze all timeframes
        analyses = self.mtf_intelligence.analyze_all_timeframes(timeframe_data)
        
        print(f"📈 Timeframe Analysis Results:")
        for tf, analysis in analyses.items():
            print(f"   • {tf.value}: {analysis.trend.name} "
                  f"(Strength: {analysis.strength:.2f})")
        
        # Get trend alignment
        alignment = self.mtf_intelligence.get_trend_alignment(analyses)
        print(f"🎯 Trend Alignment: {alignment['direction'].name} "
              f"({alignment['weighted_alignment']:.1%})")
        
        # Find confluence zones
        confluence_zones = self.mtf_intelligence.find_confluence_zones(analyses)
        print(f"🔗 Confluence Zones: {len(confluence_zones)}")
        
        for zone in confluence_zones[:3]:  # Show top 3
            print(f"   • Price: {zone['price']:.5f}, "
                  f"Type: {zone['type']}, "
                  f"Strength: {zone['strength']:.2f}")
        
        # Evaluate entry quality
        current_price = timeframe_data[TimeFrame.H1]['close'].iloc[-1]
        entry_quality = self.mtf_intelligence.get_entry_quality(current_price, analyses)
        print(f"✨ Entry Quality at {current_price:.5f}: "
              f"{entry_quality['quality']:.2f} "
              f"(Confidence: {entry_quality['confidence']:.2f})")
    
    def demo_trade_heatmaps(self, market_data: pd.DataFrame):
        """Demonstrate trade heatmap generation."""
        print("\n🔥 TRADE HEATMAP DEMO")
        print("=" * 50)
        
        # Generate liquidity heatmap
        liquidity_heatmap = self.trade_heatmap.generate_liquidity_heatmap(market_data)
        if 'error' not in liquidity_heatmap:
            print(f"💧 Liquidity Heatmap: {len(liquidity_heatmap['zones'])} zones identified")
        
        # Generate stop cluster heatmap
        stop_heatmap = self.trade_heatmap.generate_stop_cluster_heatmap(market_data)
        if 'error' not in stop_heatmap:
            print(f"🎯 Stop Cluster Heatmap: {len(stop_heatmap['zones'])} clusters identified")
        
        # Generate imbalance heatmap
        imbalance_heatmap = self.trade_heatmap.generate_imbalance_heatmap(market_data)
        if 'error' not in imbalance_heatmap:
            print(f"⚖️ Imbalance Heatmap: {len(imbalance_heatmap['zones'])} imbalance zones")
        
        # Generate multi-factor heatmap
        multi_heatmap = self.trade_heatmap.generate_multi_factor_heatmap(market_data)
        if 'error' not in multi_heatmap:
            print(f"🌈 Multi-Factor Heatmap: Combined analysis complete")
            print(f"   • Total zones: {len(multi_heatmap['zones'])}")
    
    def demo_security_system(self):
        """Demonstrate security system capabilities."""
        print("\n🔒 SECURITY SYSTEM DEMO")
        print("=" * 50)
        
        # Send heartbeat
        self.security_system.send_heartbeat()
        print("💓 Heartbeat sent")
        
        # Check for fraud in sample trade
        sample_trade = {
            'symbol': 'EURUSD',
            'size': 1.0,
            'price': 1.1000,
            'timestamp': datetime.now(),
            'type': 'market'
        }
        
        fraud_detected = self.security_system.check_for_fraud(sample_trade)
        print(f"🕵️ Fraud Detection: {'⚠️ FRAUD DETECTED' if fraud_detected else '✅ Clean'}")
        
        # Encrypt sample trade log
        encrypted_log = self.security_system.encrypt_trade_log(sample_trade)
        print(f"🔐 Trade Log Encrypted: {len(encrypted_log)} characters")
        
        # Decrypt the log
        decrypted_log = self.security_system.decrypt_trade_log(encrypted_log)
        integrity_verified = decrypted_log.get('_integrity_verified', False)
        print(f"🔓 Trade Log Decrypted: {'✅ Integrity Verified' if integrity_verified else '⚠️ Integrity Check Failed'}")
        
        # Get security status
        security_status = self.security_system.get_security_status()
        print(f"📊 Security Status:")
        print(f"   • Level: {security_status['security_level']}")
        print(f"   • Failsafe: {'🔴 ACTIVE' if security_status['failsafe_active'] else '🟢 Inactive'}")
        print(f"   • Alerts: {security_status['unresolved_alerts']} unresolved")
    
    def demo_performance_attribution(self):
        """Demonstrate performance attribution system."""
        print("\n📊 PERFORMANCE ATTRIBUTION DEMO")
        print("=" * 50)
        
        # Add sample trades
        sample_trades = [
            {
                'trade_id': 'T001',
                'symbol': 'EURUSD',
                'entry_time': datetime.now() - timedelta(hours=2),
                'exit_time': datetime.now() - timedelta(hours=1),
                'entry_price': 1.1000,
                'exit_price': 1.1020,
                'position_size': 1.0,
                'direction': 'long',
                'pnl': 200.0,
                'pnl_percent': 1.82,
                'strategy': 'trend_following',
                'market_regime': MarketRegime.TRENDING_BULL,
                'timeframe': '1h'
            },
            {
                'trade_id': 'T002',
                'symbol': 'GBPUSD',
                'entry_time': datetime.now() - timedelta(hours=4),
                'exit_time': datetime.now() - timedelta(hours=3),
                'entry_price': 1.2500,
                'exit_price': 1.2480,
                'position_size': 0.8,
                'direction': 'long',
                'pnl': -160.0,
                'pnl_percent': -1.60,
                'strategy': 'mean_reversion',
                'market_regime': MarketRegime.RANGING,
                'timeframe': '4h'
            }
        ]
        
        for trade in sample_trades:
            self.performance_attribution.add_trade(trade)
        
        # Get overall performance
        overall_perf = self.performance_attribution.get_overall_performance()
        if overall_perf.get('status') != 'no_data':
            print(f"📈 Overall Performance:")
            print(f"   • Total Trades: {overall_perf['total_trades']}")
            print(f"   • Win Rate: {overall_perf['win_rate']:.1%}")
            print(f"   • Net Profit: ${overall_perf['net_profit']:.2f}")
            print(f"   • Profit Factor: {overall_perf['profit_factor']:.2f}")
        
        # Get strategy attribution
        strategy_perf = self.performance_attribution.get_strategy_performance()
        if strategy_perf.get('attribution'):
            print(f"🎯 Strategy Attribution:")
            for strategy, metrics in strategy_perf['attribution'].items():
                print(f"   • {strategy}: ${metrics['net_profit']:.2f} "
                      f"({metrics['win_rate']:.1%} win rate)")
    
    def demo_gamified_dashboard(self):
        """Demonstrate gamified dashboard system."""
        print("\n🎮 GAMIFIED DASHBOARD DEMO")
        print("=" * 50)
        
        # Simulate some trades
        sample_results = [
            {'pnl': 150.0, 'symbol': 'EURUSD'},
            {'pnl': 200.0, 'symbol': 'GBPUSD'},
            {'pnl': -100.0, 'symbol': 'USDJPY'},
            {'pnl': 300.0, 'symbol': 'EURUSD'},
            {'pnl': 250.0, 'symbol': 'AUDUSD'}
        ]
        
        for result in sample_results:
            self.gamified_dashboard.update_trade_result(result)
        
        # Get dashboard data
        dashboard_data = self.gamified_dashboard.get_dashboard_data()
        
        print(f"🏆 Trading Stats:")
        stats = dashboard_data['stats']
        print(f"   • Level: {dashboard_data['gamification']['level']}")
        print(f"   • Total Points: {dashboard_data['gamification']['total_points']}")
        print(f"   • Win Rate: {stats['win_rate']:.1f}%")
        print(f"   • Current Streak: {stats['current_streak']}")
        print(f"   • Net Profit: ${stats['net_profit']:.2f}")
        
        print(f"🏅 Achievements:")
        print(f"   • Unlocked: {dashboard_data['achievements']['unlocked']}/{dashboard_data['achievements']['total']}")
        
        for achievement in dashboard_data['achievements']['recent']:
            print(f"   • {achievement['name']} ({achievement['badge_level']}) - {achievement['points']} pts")
    
    def demo_risk_management(self, market_data: pd.DataFrame):
        """Demonstrate adaptive risk management."""
        print("\n⚖️ ADAPTIVE RISK MANAGEMENT DEMO")
        print("=" * 50)
        
        # Detect market regime
        regime_signal = self.regime_detector.detect_regime(market_data)
        print(f"📊 Market Regime: {regime_signal.regime.value} "
              f"(Confidence: {regime_signal.confidence:.2f})")
        
        # Calculate position size
        entry_price = market_data['close'].iloc[-1]
        stop_loss = entry_price * 0.99  # 1% stop loss
        
        position_size = self.risk_manager.calculate_position_size(
            'EURUSD', entry_price, stop_loss, regime_signal.regime
        )
        print(f"💰 Position Size: {position_size:.4f} lots")
        
        # Adjust stop loss based on regime
        adjusted_stop = self.risk_manager.adjust_stop_loss(
            'EURUSD', entry_price, stop_loss, regime_signal.regime
        )
        print(f"🛑 Adjusted Stop Loss: {adjusted_stop:.5f}")
        
        # Calculate take profit
        take_profit = self.risk_manager.adjust_take_profit(
            'EURUSD', entry_price, adjusted_stop, regime_signal.regime
        )
        print(f"🎯 Take Profit: {take_profit:.5f}")
        
        # Check if position can be opened
        can_open = self.risk_manager.can_open_position('EURUSD', regime_signal.regime)
        print(f"✅ Can Open Position: {'Yes' if can_open else 'No'}")
        
        # Get risk summary
        risk_summary = self.risk_manager.get_risk_summary()
        print(f"📋 Risk Summary:")
        print(f"   • Account Balance: ${risk_summary['account_balance']:.2f}")
        print(f"   • Current Drawdown: {risk_summary['current_drawdown']:.2%}")
        print(f"   • Open Positions: {risk_summary['open_positions']}")
    
    async def run_full_demo(self):
        """Run the complete demonstration of all features."""
        print("🎯 ELITE TRADING BOT - ADVANCED FEATURES DEMONSTRATION")
        print("=" * 60)
        
        # Generate sample data
        timeframe_data = self.generate_sample_data()
        h1_data = timeframe_data[TimeFrame.H1]
        
        # Run all demos
        self.demo_sentiment_analysis()
        self.demo_order_flow_detection(h1_data)
        self.demo_multi_timeframe_intelligence(timeframe_data)
        self.demo_trade_heatmaps(h1_data)
        self.demo_security_system()
        self.demo_performance_attribution()
        self.demo_gamified_dashboard()
        self.demo_risk_management(h1_data)
        
        print("\n🎉 DEMONSTRATION COMPLETE!")
        print("=" * 60)
        print("All advanced features have been successfully demonstrated.")
        print("The Elite Trading Bot is ready for professional trading!")


def main():
    """Main function to run the demo."""
    demo = AdvancedFeaturesDemo()
    
    # Run the demo
    asyncio.run(demo.run_full_demo())


if __name__ == "__main__":
    main()
