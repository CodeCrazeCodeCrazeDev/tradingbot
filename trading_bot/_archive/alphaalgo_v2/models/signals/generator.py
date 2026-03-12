"""
AlphaAlgo V2 Signal Generator

Base signal generator with technical analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid
import pandas as pd
import numpy as np

from ...core.interfaces import ISignalGenerator
from ...core.types import Signal, SignalType, MarketData
from ...core.constants import DEFAULT_CONFIDENCE_THRESHOLD
import asyncio
import numpy
import pandas

logger = logging.getLogger(__name__)


class SignalGenerator(ISignalGenerator):
    """
    Technical analysis-based signal generator
    
    Uses:
    - Moving average crossovers
    - RSI overbought/oversold
    - MACD signals
    - Support/resistance levels
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self._name = self.config.get("name", "technical")
        self._confidence_threshold = self.config.get(
            "confidence_threshold",
            DEFAULT_CONFIDENCE_THRESHOLD
        )
        
        # Indicator parameters
        self._fast_ma = self.config.get("fast_ma", 10)
        self._slow_ma = self.config.get("slow_ma", 20)
        self._rsi_period = self.config.get("rsi_period", 14)
        self._rsi_overbought = self.config.get("rsi_overbought", 70)
        self._rsi_oversold = self.config.get("rsi_oversold", 30)
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def confidence_threshold(self) -> float:
        return self._confidence_threshold
    
    async def generate(
        self,
        symbol: str,
        data: MarketData,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Signal]:
        """
        Generate trading signal
        
        Args:
            symbol: Trading symbol
            data: Market data
            context: Additional context
            
        Returns:
            Signal if conditions met, None otherwise
        """
        df = data.ohlcv
        if df is None or len(df) < self._slow_ma + 5:
            return None
        
        # Calculate indicators
        indicators = self._calculate_indicators(df)
        
        # Generate signal
        signal_type, confidence = self._evaluate_conditions(indicators)
        
        if signal_type == SignalType.HOLD or confidence < self._confidence_threshold:
            return None
        
        # Calculate stop loss and take profit
        current_price = float(df['close'].iloc[-1])
        atr = self._calculate_atr(df)
        
        if signal_type == SignalType.BUY:
            stop_loss = current_price - (atr * 2)
            take_profit = current_price + (atr * 3)
        else:
            stop_loss = current_price + (atr * 2)
            take_profit = current_price - (atr * 3)
        
        return Signal(
            id=str(uuid.uuid4()),
            symbol=symbol,
            signal_type=signal_type,
            price=current_price,
            confidence=confidence,
            stop_loss=stop_loss,
            take_profit=take_profit,
            timeframe=data.timeframe,
            source=self._name,
            metadata={
                "indicators": indicators,
                "atr": atr,
            },
            expires_at=datetime.now() + timedelta(minutes=30),
        )
    
    def get_confidence(self, signal: Signal) -> float:
        """Get signal confidence"""
        return signal.confidence
    
    async def validate(self, signal: Signal) -> bool:
        """Validate signal"""
        # Check not expired
        if signal.is_expired:
            return False
        
        # Check confidence threshold
        if signal.confidence < self._confidence_threshold:
            return False
        
        # Check risk/reward ratio
        if signal.risk_reward_ratio and signal.risk_reward_ratio < 1.0:
            return False
        
        return True
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators"""
        close = df['close']
        
        # Moving averages
        fast_ma = close.rolling(self._fast_ma).mean().iloc[-1]
        slow_ma = close.rolling(self._slow_ma).mean().iloc[-1]
        
        # RSI
        rsi = self._calculate_rsi(close, self._rsi_period)
        
        # MACD
        macd, signal_line, histogram = self._calculate_macd(close)
        
        # Trend
        trend = "up" if fast_ma > slow_ma else "down"
        
        return {
            "fast_ma": fast_ma,
            "slow_ma": slow_ma,
            "rsi": rsi,
            "macd": macd,
            "macd_signal": signal_line,
            "macd_histogram": histogram,
            "trend": trend,
            "close": float(close.iloc[-1]),
        }
    
    def _evaluate_conditions(
        self,
        indicators: Dict[str, float]
    ) -> tuple[SignalType, float]:
        """Evaluate trading conditions"""
        signals = []
        
        # MA crossover
        if indicators["fast_ma"] > indicators["slow_ma"]:
            signals.append(("buy", 0.3))
        else:
            signals.append(("sell", 0.3))
        
        # RSI
        rsi = indicators["rsi"]
        if rsi < self._rsi_oversold:
            signals.append(("buy", 0.25))
        elif rsi > self._rsi_overbought:
            signals.append(("sell", 0.25))
        
        # MACD
        if indicators["macd_histogram"] > 0:
            signals.append(("buy", 0.2))
        else:
            signals.append(("sell", 0.2))
        
        # Aggregate signals
        buy_score = sum(w for s, w in signals if s == "buy")
        sell_score = sum(w for s, w in signals if s == "sell")
        
        if buy_score > sell_score and buy_score >= 0.5:
            return SignalType.BUY, min(buy_score, 1.0)
        elif sell_score > buy_score and sell_score >= 0.5:
            return SignalType.SELL, min(sell_score, 1.0)
        else:
            return SignalType.HOLD, 0.0
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """Calculate RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else 50.0
    
    def _calculate_macd(
        self,
        prices: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> tuple[float, float, float]:
        """Calculate MACD"""
        exp1 = prices.ewm(span=fast, adjust=False).mean()
        exp2 = prices.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line
        
        return (
            float(macd.iloc[-1]),
            float(signal_line.iloc[-1]),
            float(histogram.iloc[-1]),
        )
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        
        return float(atr) if not pd.isna(atr) else 0.0
