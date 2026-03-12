"""
Signal Logic Validator
Validates buy/sell signal generation and ensures no conflicts across modules
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Any, Dict, List
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np

from validation.comprehensive_validator import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class SignalValidator:
    """Validates signal generation logic"""
    
    def __init__(self):
        self.results = []
    
    def validate_signal_consistency(self) -> ValidationResult:
        """Validate that signals are consistent and not conflicting"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            import talib
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Signal Logic",
                    test_name="Signal Consistency",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Get test data
            symbol = "EURUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 200)
            
            if rates is None or len(rates) == 0:
                mt5.shutdown()
                return ValidationResult(
                    component="Signal Logic",
                    test_name="Signal Consistency",
                    status=ValidationStatus.FAILED,
                    message="Failed to get price data",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            df = pd.DataFrame(rates)
            close = df['close'].values
            high = df['high'].values
            low = df['low'].values
            
            # Generate signals from multiple strategies
            signals = {}
            
            # 1. EMA Crossover
            ema_fast = talib.EMA(close, timeperiod=12)
            ema_slow = talib.EMA(close, timeperiod=26)
            if ema_fast[-1] > ema_slow[-1] and ema_fast[-2] <= ema_slow[-2]:
                signals['EMA_Crossover'] = 'BUY'
            elif ema_fast[-1] < ema_slow[-1] and ema_fast[-2] >= ema_slow[-2]:
                signals['EMA_Crossover'] = 'SELL'
            else:
                signals['EMA_Crossover'] = 'NEUTRAL'
            
            # 2. RSI
            rsi = talib.RSI(close, timeperiod=14)
            if rsi[-1] < 30:
                signals['RSI'] = 'BUY'
            elif rsi[-1] > 70:
                signals['RSI'] = 'SELL'
            else:
                signals['RSI'] = 'NEUTRAL'
            
            # 3. MACD
            macd, signal_line, hist = talib.MACD(close)
            if macd[-1] > signal_line[-1] and macd[-2] <= signal_line[-2]:
                signals['MACD'] = 'BUY'
            elif macd[-1] < signal_line[-1] and macd[-2] >= signal_line[-2]:
                signals['MACD'] = 'SELL'
            else:
                signals['MACD'] = 'NEUTRAL'
            
            # 4. Bollinger Bands
            upper, middle, lower = talib.BBANDS(close)
            if close[-1] < lower[-1]:
                signals['Bollinger'] = 'BUY'
            elif close[-1] > upper[-1]:
                signals['Bollinger'] = 'SELL'
            else:
                signals['Bollinger'] = 'NEUTRAL'
            
            # 5. Stochastic
            slowk, slowd = talib.STOCH(high, low, close)
            if slowk[-1] < 20 and slowk[-1] > slowd[-1]:
                signals['Stochastic'] = 'BUY'
            elif slowk[-1] > 80 and slowk[-1] < slowd[-1]:
                signals['Stochastic'] = 'SELL'
            else:
                signals['Stochastic'] = 'NEUTRAL'
            
            mt5.shutdown()
            
            # Check for conflicts
            buy_signals = sum(1 for s in signals.values() if s == 'BUY')
            sell_signals = sum(1 for s in signals.values() if s == 'SELL')
            neutral_signals = sum(1 for s in signals.values() if s == 'NEUTRAL')
            
            # Determine overall signal
            if buy_signals > sell_signals:
                overall = 'BUY'
                confidence = buy_signals / len(signals) * 100
            elif sell_signals > buy_signals:
                overall = 'SELL'
                confidence = sell_signals / len(signals) * 100
            else:
                overall = 'NEUTRAL'
                confidence = neutral_signals / len(signals) * 100
            
            # Check for conflicts (both BUY and SELL signals present)
            has_conflict = buy_signals > 0 and sell_signals > 0
            
            details = {
                'signals': signals,
                'buy_count': buy_signals,
                'sell_count': sell_signals,
                'neutral_count': neutral_signals,
                'overall_signal': overall,
                'confidence': f"{confidence:.1f}%",
                'has_conflict': has_conflict
            }
            
            if has_conflict and confidence < 60:
                return ValidationResult(
                    component="Signal Logic",
                    test_name="Signal Consistency",
                    status=ValidationStatus.WARNING,
                    message=f"Signal conflict detected - {overall} with {confidence:.1f}% confidence",
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Signal Logic",
                test_name="Signal Consistency",
                status=ValidationStatus.PASSED,
                message=f"Signals consistent - {overall} with {confidence:.1f}% confidence",
                details=details,
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Signal Logic",
                test_name="Signal Consistency",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_signal_timing(self) -> ValidationResult:
        """Validate signal generation timing and latency"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            import talib
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Signal Logic",
                    test_name="Signal Timing",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Measure signal generation time
            symbol = "EURUSD"
            
            timings = []
            for _ in range(10):
                iter_start = time.time()
                
                rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
                if rates is None:
                    continue
                
                df = pd.DataFrame(rates)
                close = df['close'].values
                
                # Calculate indicators
                ema = talib.EMA(close, timeperiod=20)
                rsi = talib.RSI(close, timeperiod=14)
                macd, signal, hist = talib.MACD(close)
                
                iter_time = (time.time() - iter_start) * 1000
                timings.append(iter_time)
            
            mt5.shutdown()
            
            if not timings:
                return ValidationResult(
                    component="Signal Logic",
                    test_name="Signal Timing",
                    status=ValidationStatus.FAILED,
                    message="Failed to measure signal timing",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            avg_time = np.mean(timings)
            max_time = np.max(timings)
            min_time = np.min(timings)
            
            # Signal generation should be under 100ms for real-time trading
            if avg_time > 100:
                status = ValidationStatus.WARNING
                message = f"Signal generation slow: {avg_time:.1f}ms average"
            else:
                status = ValidationStatus.PASSED
                message = f"Signal generation fast: {avg_time:.1f}ms average"
            
            return ValidationResult(
                component="Signal Logic",
                test_name="Signal Timing",
                status=status,
                message=message,
                details={
                    'average_ms': round(avg_time, 2),
                    'min_ms': round(min_time, 2),
                    'max_ms': round(max_time, 2),
                    'iterations': len(timings)
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Signal Logic",
                test_name="Signal Timing",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all signal validations"""
        logger.info("=" * 80)
        logger.info("SIGNAL LOGIC VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_signal_consistency(),
            self.validate_signal_timing()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


if __name__ == "__main__":
    validator = SignalValidator()
    results = validator.validate_all()
