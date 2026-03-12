import logging
"""
Market Intelligence and Price Movement Analysis System - Example Usage

This example demonstrates how to use the comprehensive Market Intelligence system
integrated into the trading bot framework.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger

# Add the trading bot to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trading_bot.data import MT5Interface
from trading_bot.market_intelligence import (
    MarketDataMonitor,
    EconomicIndicatorMonitor,
    NewsAndSentimentMonitor,
    PricePatternRecognition,
    MomentumIndicators,
    VolatilityMeasures,
    IntermarketAnalysis,
    LiquidityAnalysis,
    RiskIndicators,
    MarketEventDetector,
    EconomicEventDetector,
    AnomalyDetector,
    WyckoffAccumulationDetector,
    WyckoffDistributionAnalyzer,
    VolumeAnalysis,
    OrderBlockAnalysis,
    LiquidityPoolDetector,
    SmartMoneyConceptsAnalyzer,
    MarketStructureAnalysis,
    PremiumDiscountZones,
    ImbalanceAnalysis,
    TimeAnalysisComponents,
    PriceAnalysis,
    VolumePriceAnalysis
)


class MarketIntelligenceDemo:
    pass
    """Demonstration of the Market Intelligence system."""
    
    def __init__(self):
    pass
        """Initialize the demo with all components."""
        logger.info("Initializing Market Intelligence Demo")
        
        # Initialize MT5 interface
        self.mt5 = MT5Interface()
        
        # Initialize monitoring components
        self.data_monitor = MarketDataMonitor(self.mt5)
        self.economic_monitor = EconomicIndicatorMonitor()
        self.news_monitor = NewsAndSentimentMonitor()
        
        # Initialize technical analysis components
        self.pattern_recognition = PricePatternRecognition()
        self.momentum_indicators = MomentumIndicators()
        self.volatility_measures = VolatilityMeasures()
        
        # Initialize market context components
        self.intermarket_analysis = IntermarketAnalysis()
        self.liquidity_analysis = LiquidityAnalysis()
        self.risk_indicators = RiskIndicators()
        
        # Initialize event detection components
        self.market_event_detector = MarketEventDetector()
        self.economic_event_detector = EconomicEventDetector()
        self.anomaly_detector = AnomalyDetector()
        
        # Initialize Wyckoff analysis components
        self.wyckoff_accumulation = WyckoffAccumulationDetector()
        self.wyckoff_distribution = WyckoffDistributionAnalyzer()
        self.volume_analysis = VolumeAnalysis()
        
        # Initialize liquidity analysis components
        self.order_block_analysis = OrderBlockAnalysis()
        self.liquidity_pool_detector = LiquidityPoolDetector()
        self.smc_analyzer = SmartMoneyConceptsAnalyzer()
        
        # Initialize pattern recognition components
        self.market_structure = MarketStructureAnalysis()
        self.premium_discount = PremiumDiscountZones()
        self.imbalance_analysis = ImbalanceAnalysis()
        
        # Initialize time/price analysis components
        self.time_analysis = TimeAnalysisComponents()
        self.price_analysis = PriceAnalysis()
        self.volume_price_analysis = VolumePriceAnalysis()
        
        logger.info("Market Intelligence Demo initialized successfully")
    
    def run_comprehensive_analysis(self, symbol: str = "EURUSD", 
                                 timeframe: str = "H1", 
                                 periods: int = 1000):
    pass
        """Run a comprehensive market analysis demonstration.
        
        Args:
    pass
            symbol: Trading symbol to analyze
            timeframe: Timeframe for analysis
            periods: Number of periods to analyze
        """
        logger.info(f"Starting comprehensive analysis for {symbol} {timeframe}")
        
        try:
    pass
            # 1. Get market data
            df = self.mt5.get_ohlc(symbol, timeframe, periods)
            if df is None or df.empty:
    pass
                logger.error("Failed to retrieve market data")
                return
            
            logger.info(f"Retrieved {len(df)} periods of data for {symbol}")
            
            # 2. Real-time data monitoring demonstration
            self._demonstrate_data_monitoring(symbol, df)
            
            # 3. Technical analysis demonstration
            self._demonstrate_technical_analysis(df)
            
            # 4. Market context analysis demonstration
            self._demonstrate_market_context(df)
            
            # 5. Event detection demonstration
            self._demonstrate_event_detection(df)
            
            # 6. Wyckoff analysis demonstration
            self._demonstrate_wyckoff_analysis(df)
            
            # 7. Liquidity analysis demonstration
            self._demonstrate_liquidity_analysis(df)
            
            # 8. Pattern recognition demonstration
            self._demonstrate_pattern_recognition(df)
            
            # 9. Time/price analysis demonstration
            self._demonstrate_time_price_analysis(df)
            
            # 10. Generate comprehensive market report
            self._generate_market_report(symbol, df)
            
            logger.info("Comprehensive analysis completed successfully")
            
    pass
            logger.error(f"Error in comprehensive analysis: {e}")
    
    def _demonstrate_data_monitoring(self, symbol: str, df: pd.DataFrame):
    pass
        """Demonstrate real-time data monitoring capabilities."""
        logger.info("=== Data Monitoring Demonstration ===")
        
        # Volume spike detection
        if 'volume' in df.columns:
    pass
            volume_spikes = self.data_monitor.detect_volume_spikes(
                symbol, "H1", threshold=2.0, lookback=20
            )
            logger.info(f"Detected {len(volume_spikes)} volume spikes")
            
            for spike in volume_spikes[-3:]:  # Show last 3 spikes
                logger.info(f"Volume spike at {spike['timestamp']}: "
                          f"{spike['ratio']:.2f}x average volume")
        
        # Price action summary
        price_summary = self.data_monitor.get_price_action_summary(symbol, "H1", 10)
        if price_summary:
    pass
            logger.info(f"Price action summary: {price_summary['trend']} trend, "
                       f"{price_summary['price_change_pct']:.2f}% change")
        
        # Economic indicators
        self.economic_monitor.update_economic_calendar()
        high_impact_events = self.economic_monitor.get_high_impact_events(7)
        logger.info(f"Found {len(high_impact_events)} high-impact events in next 7 days")
        
        # News sentiment
        sentiment_summary = self.news_monitor.get_sentiment_summary(symbol)
        if sentiment_summary:
    pass
            logger.info(f"Market sentiment for {symbol}: "
                       f"{sentiment_summary['sentiment_category']} "
                       f"(score: {sentiment_summary['overall_sentiment']:.2f})")
    
    def _demonstrate_technical_analysis(self, df: pd.DataFrame):
    pass
        """Demonstrate technical analysis capabilities."""
        logger.info("=== Technical Analysis Demonstration ===")
        
        # Candlestick patterns
        patterns = self.pattern_recognition.detect_candlestick_patterns(df)
        for pattern_name, pattern_data in patterns.items():
    pass
            recent_signals = pattern_data.tail(10).sum()
            if recent_signals > 0:
    pass
                logger.info(f"Recent {pattern_name} signals: {recent_signals}")
        
        # Momentum indicators
        rsi = self.momentum_indicators.calculate_rsi(df['close'])
        current_rsi = rsi.iloc[-1]
        logger.info(f"Current RSI: {current_rsi:.2f}")
        
        macd_data = self.momentum_indicators.calculate_macd(df['close'])
        current_macd = macd_data['macd'].iloc[-1]
        current_signal = macd_data['signal'].iloc[-1]
        logger.info(f"Current MACD: {current_macd:.5f}, Signal: {current_signal:.5f}")
        
        # Volatility measures
        atr = self.volatility_measures.calculate_atr(df['high'], df['low'], df['close'])
        current_atr = atr.iloc[-1]
        logger.info(f"Current ATR: {current_atr:.5f}")
        
        bb_data = self.volatility_measures.calculate_bollinger_bands(df['close'])
        current_price = df['close'].iloc[-1]
        upper_band = bb_data['upper'].iloc[-1]
        lower_band = bb_data['lower'].iloc[-1]
        
        if current_price > upper_band:
    pass
            bb_position = "above upper band (overbought)"
        elif current_price < lower_band:
    pass
            bb_position = "below lower band (oversold)"
        else:
    pass
            bb_position = "within bands"
        
        logger.info(f"Bollinger Bands position: {bb_position}")
    
    def _demonstrate_market_context(self, df: pd.DataFrame):
    pass
        """Demonstrate market context analysis."""
        logger.info("=== Market Context Analysis Demonstration ===")
        
        # Risk indicators
        returns = df['close'].pct_change().dropna()
        
        var_5pct = self.risk_indicators.calculate_var(returns, 0.05)
        logger.info(f"5% Value at Risk: {var_5pct:.5f}")
        
        expected_shortfall = self.risk_indicators.calculate_expected_shortfall(returns, 0.05)
        logger.info(f"Expected Shortfall: {expected_shortfall:.5f}")
        
        max_dd_info = self.risk_indicators.calculate_maximum_drawdown(df['close'])
        logger.info(f"Maximum Drawdown: {max_dd_info['max_drawdown']:.2%}")
        
        sharpe_ratio = self.risk_indicators.calculate_sharpe_ratio(returns)
        logger.info(f"Sharpe Ratio: {sharpe_ratio:.2f}")
        
        # Liquidity analysis
        if 'volume' in df.columns:
    pass
            volume_profile = self.liquidity_analysis.analyze_volume_profile(
                df['close'], df['volume']
            )
            logger.info(f"Identified {len(volume_profile['high_volume_nodes'])} "
                       f"high volume nodes")
    
    def _demonstrate_event_detection(self, df: pd.DataFrame):
    pass
        """Demonstrate event detection capabilities."""
        logger.info("=== Event Detection Demonstration ===")
        
        # Price gaps
        price_gaps = self.market_event_detector.detect_price_gaps(df, 0.005)
        logger.info(f"Detected {len(price_gaps)} price gaps")
        
        # Volume spikes
        if 'volume' in df.columns:
    pass
            volume_spikes = self.market_event_detector.detect_volume_spikes(
                df['volume'], multiplier=3.0
            )
            logger.info(f"Detected {len(volume_spikes)} volume spikes")
        
        # Volatility breakouts
        returns = df['close'].pct_change()
        vol_breakouts = self.market_event_detector.detect_volatility_breakouts(returns)
        logger.info(f"Detected {len(vol_breakouts)} volatility breakouts")
        
        # Momentum shifts
        momentum_shifts = self.market_event_detector.detect_momentum_shifts(df['close'])
        logger.info(f"Detected {len(momentum_shifts)} momentum shifts")
        
        # Anomaly detection
        features_df = pd.DataFrame({
            'returns': df['close'].pct_change(),
            'volume': df.get('volume', pd.Series(index=df.index, dtype=float)),
            'range': df['high'] - df['low']
        }).fillna(0)
        
        anomalies = self.anomaly_detector.detect_statistical_anomalies(features_df)
        anomaly_count = anomalies.sum() if not anomalies.empty else 0
        logger.info(f"Detected {anomaly_count} statistical anomalies")
    
    def _demonstrate_wyckoff_analysis(self, df: pd.DataFrame):
    pass
        """Demonstrate Wyckoff analysis capabilities."""
        logger.info("=== Wyckoff Analysis Demonstration ===")
        
        # Accumulation detection
        accumulation_phases = self.wyckoff_accumulation.detect_accumulation_phase(df)
        logger.info(f"Detected {len(accumulation_phases)} accumulation phases")
        
        # Distribution detection
        distribution_phases = self.wyckoff_distribution.detect_distribution_phase(df)
        logger.info(f"Detected {len(distribution_phases)} distribution phases")
        
        # Volume analysis
        if 'volume' in df.columns:
    pass
            vsa_analysis = self.volume_analysis.analyze_volume_spread_analysis(df)
            
            climax_volume = vsa_analysis['climax_volume'].sum()
            professional_money = vsa_analysis['professional_money'].sum()
            weak_demand = vsa_analysis['weak_demand'].sum()
            
            logger.info(f"VSA signals - Climax: {climax_volume}, "
                       f"Professional: {professional_money}, "
                       f"Weak demand: {weak_demand}")
            
            # Volume climax detection
            volume_climax = self.volume_analysis.detect_volume_climax(df)
            logger.info(f"Detected {len(volume_climax)} volume climax events")
    
    def _demonstrate_liquidity_analysis(self, df: pd.DataFrame):
    pass
        """Demonstrate liquidity analysis capabilities."""
        logger.info("=== Liquidity Analysis Demonstration ===")
        
        # Order block detection
        order_blocks = self.order_block_analysis.detect_order_blocks(df)
        logger.info(f"Detected {len(order_blocks)} order blocks")
        
        bullish_blocks = sum(1 for block in order_blocks if block['type'].value == 'bullish')
        bearish_blocks = sum(1 for block in order_blocks if block['type'].value == 'bearish')
        logger.info(f"Bullish order blocks: {bullish_blocks}, Bearish: {bearish_blocks}")
        
        # Liquidity pool detection
        liquidity_pools = self.liquidity_pool_detector.detect_equal_highs_lows(df)
        logger.info(f"Detected {len(liquidity_pools)} liquidity pools")
        
        support_pools = sum(1 for pool in liquidity_pools if pool['type'] == 'support')
        resistance_pools = sum(1 for pool in liquidity_pools if pool['type'] == 'resistance')
        logger.info(f"Support pools: {support_pools}, Resistance pools: {resistance_pools}")
        
        # Smart Money Concepts
        bos_patterns = self.smc_analyzer.detect_break_of_structure(df)
        logger.info(f"Detected {len(bos_patterns)} Break of Structure patterns")
        
        choch_patterns = self.smc_analyzer.detect_change_of_character(df)
        logger.info(f"Detected {len(choch_patterns)} Change of Character patterns")
        
        # Premium/Discount zones
        pd_zones = self.smc_analyzer.detect_premium_discount_zones(df)
        current_zone = pd_zones.get('current_zone', 'unknown')
        logger.info(f"Current price zone: {current_zone}")
    
    def _demonstrate_pattern_recognition(self, df: pd.DataFrame):
    pass
        """Demonstrate pattern recognition capabilities."""
        logger.info("=== Pattern Recognition Demonstration ===")
        
        # Market structure analysis
        structure_analysis = self.market_structure.detect_market_structure(df)
        current_structure = structure_analysis.get('current_structure', 'unknown')
        trend = structure_analysis.get('trend_analysis', {}).get('trend', 'unknown')
        logger.info(f"Market structure: {current_structure}, Trend: {trend}")
        
        # Fair value zones
        fv_zones = self.premium_discount.calculate_fair_value_zones(df)
        current_zone = fv_zones.get('current_zone', 'unknown')
        distance_from_fv = fv_zones.get('distance_from_fair_value', 0) * 100
        logger.info(f"Fair value zone: {current_zone}, "
                   f"Distance from FV: {distance_from_fv:.2f}%")
        
        # Imbalance analysis
        fair_value_gaps = self.imbalance_analysis.detect_fair_value_gaps(df)
        logger.info(f"Detected {len(fair_value_gaps)} Fair Value Gaps")
        
        bullish_fvg = sum(1 for gap in fair_value_gaps if gap['type'] == 'bullish_fvg')
        bearish_fvg = sum(1 for gap in fair_value_gaps if gap['type'] == 'bearish_fvg')
        logger.info(f"Bullish FVGs: {bullish_fvg}, Bearish FVGs: {bearish_fvg}")
    
    def _demonstrate_time_price_analysis(self, df: pd.DataFrame):
    pass
        """Demonstrate time and price analysis capabilities."""
        logger.info("=== Time/Price Analysis Demonstration ===")
        
        # Session patterns
        session_patterns = self.time_analysis.analyze_session_patterns(df)
        for session, stats in session_patterns.items():
    pass
            if stats.get('total_sessions', 0) > 0:
    pass
                avg_vol = stats.get('avg_volatility', 0) * 100
                logger.info(f"{session.capitalize()} session avg volatility: {avg_vol:.3f}%")
        
        # Day of week patterns
        dow_patterns = self.time_analysis.analyze_day_of_week_patterns(df)
        for day, stats in dow_patterns.items():
    pass
            if stats.get('total_days', 0) > 10:  # Only show days with sufficient data
                avg_return = stats.get('avg_return', 0) * 100
                logger.info(f"{day} avg return: {avg_return:.3f}%")
        
        # Price level analysis
        pivot_levels = self.price_analysis.calculate_price_levels(df, 'pivot')
        current_price = df['close'].iloc[-1]
        pivot = pivot_levels.get('pivot', 0)
        logger.info(f"Current price: {current_price:.5f}, Pivot: {pivot:.5f}")
        
        # Volume-Price analysis
        if 'volume' in df.columns:
    pass
            vwap = self.volume_price_analysis.calculate_vwap(df, period=20)
            current_vwap = vwap.iloc[-1]
            logger.info(f"20-period VWAP: {current_vwap:.5f}")
            
            obv = self.volume_price_analysis.calculate_on_balance_volume(df)
            obv_trend = "bullish" if obv.iloc[-1] > obv.iloc[-10] else "bearish"
            logger.info(f"OBV trend (10 periods): {obv_trend}")
    
    def _generate_market_report(self, symbol: str, df: pd.DataFrame):
    pass
        """Generate a comprehensive market intelligence report."""
        logger.info("=== Comprehensive Market Intelligence Report ===")
        
        current_price = df['close'].iloc[-1]
        price_change = df['close'].pct_change().iloc[-1] * 100
        
        logger.info(f"Symbol: {symbol}")
        logger.info(f"Current Price: {current_price:.5f}")
        logger.info(f"Last Change: {price_change:+.2f}%")
        logger.info(f"Analysis Period: {df.index[0]} to {df.index[-1]}")
        logger.info(f"Total Periods Analyzed: {len(df)}")
        
        # Risk assessment
        returns = df['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized volatility
        sharpe = self.risk_indicators.calculate_sharpe_ratio(returns)
        
        logger.info(f"Annualized Volatility: {volatility:.2f}%")
        logger.info(f"Sharpe Ratio: {sharpe:.2f}")
        
        # Market structure summary
        structure_analysis = self.market_structure.detect_market_structure(df)
        trend = structure_analysis.get('trend_analysis', {}).get('trend', 'unknown')
        logger.info(f"Overall Trend: {trend}")
        
        # Key levels
        pivot_levels = self.price_analysis.calculate_price_levels(df, 'pivot')
        r1 = pivot_levels.get('resistance_levels', {}).get('R1', 0)
        s1 = pivot_levels.get('support_levels', {}).get('S1', 0)
        logger.info(f"Key Resistance (R1): {r1:.5f}")
        logger.info(f"Key Support (S1): {s1:.5f}")
        
        logger.info("=== End of Market Intelligence Report ===")


def main():
    pass
    """Main function to run the Market Intelligence demonstration."""
    logger.info("Starting Market Intelligence System Demonstration")
    
    # Create demo instance
    demo = MarketIntelligenceDemo()
    
    # Run comprehensive analysis for multiple symbols
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]
    
    for symbol in symbols:
    pass
        logger.info(f"\n{'='*50}")
        logger.info(f"Analyzing {symbol}")
        logger.info(f"{'='*50}")
        
        demo.run_comprehensive_analysis(symbol, "H1", 500)
        
        # Add a small delay between symbols
        import time
import numpy
import pandas

logger = logging.getLogger(__name__)

        time.sleep(2)
    
    logger.info("\nMarket Intelligence System Demonstration completed!")


if __name__ == "__main__":
    pass
    main()
