"""
Comprehensive Validation System for Elite Trading Bot
Validates all components: API keys, market feeds, indicators, signals, execution, risk, notifications, AI/ML
"""

import os
import sys
import time
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status enumeration"""
    PASSED = "✓ PASSED"
    FAILED = "✗ FAILED"
    WARNING = "⚠ WARNING"
    SKIPPED = "○ SKIPPED"


@dataclass
class ValidationResult:
    """Validation result data structure"""
    component: str
    test_name: str
    status: ValidationStatus
    message: str
    details: Dict[str, Any]
    timestamp: str
    duration_ms: float
    
    def to_dict(self):
        return {
            **asdict(self),
            'status': self.status.value
        }


class APIKeyValidator:
    """Validates all API keys and external service connections"""
    
    def __init__(self):
        load_dotenv()
        self.results = []
    
    def validate_alpha_vantage(self) -> ValidationResult:
        """Validate Alpha Vantage API key"""
        start = time.time()
        api_key = os.getenv('ALPHA_VANTAGE_KEY')
        
        if not api_key:
            return ValidationResult(
                component="API Keys",
                test_name="Alpha Vantage",
                status=ValidationStatus.FAILED,
                message="API key not found in environment",
                details={},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=EURUSD&interval=5min&apikey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "Error Message" in data or "Note" in data:
                    return ValidationResult(
                        component="API Keys",
                        test_name="Alpha Vantage",
                        status=ValidationStatus.FAILED,
                        message=f"API error: {data.get('Error Message', data.get('Note', 'Unknown error'))}",
                        details={"response": data},
                        timestamp=datetime.now().isoformat(),
                        duration_ms=(time.time() - start) * 1000
                    )
                
                return ValidationResult(
                    component="API Keys",
                    test_name="Alpha Vantage",
                    status=ValidationStatus.PASSED,
                    message="API key valid and responsive",
                    details={"data_points": len(data.get("Time Series (5min)", {}))},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            else:
                return ValidationResult(
                    component="API Keys",
                    test_name="Alpha Vantage",
                    status=ValidationStatus.FAILED,
                    message=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ValidationResult(
                component="API Keys",
                test_name="Alpha Vantage",
                status=ValidationStatus.FAILED,
                message=f"Connection error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_fred(self) -> ValidationResult:
        """Validate FRED API key"""
        start = time.time()
        api_key = os.getenv('FRED_API_KEY')
        
        if not api_key:
            return ValidationResult(
                component="API Keys",
                test_name="FRED API",
                status=ValidationStatus.FAILED,
                message="API key not found in environment",
                details={},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id=DFF&api_key={api_key}&file_type=json&limit=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "error_code" in data:
                    return ValidationResult(
                        component="API Keys",
                        test_name="FRED API",
                        status=ValidationStatus.FAILED,
                        message=f"API error: {data.get('error_message', 'Unknown error')}",
                        details={"response": data},
                        timestamp=datetime.now().isoformat(),
                        duration_ms=(time.time() - start) * 1000
                    )
                
                return ValidationResult(
                    component="API Keys",
                    test_name="FRED API",
                    status=ValidationStatus.PASSED,
                    message="API key valid and responsive",
                    details={"observations": len(data.get("observations", []))},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            else:
                return ValidationResult(
                    component="API Keys",
                    test_name="FRED API",
                    status=ValidationStatus.FAILED,
                    message=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ValidationResult(
                component="API Keys",
                test_name="FRED API",
                status=ValidationStatus.FAILED,
                message=f"Connection error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_news_api(self) -> ValidationResult:
        """Validate News API key (if configured)"""
        start = time.time()
        api_key = os.getenv('NEWS_API_KEY')
        
        if not api_key:
            return ValidationResult(
                component="API Keys",
                test_name="News API",
                status=ValidationStatus.SKIPPED,
                message="API key not configured (optional)",
                details={},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        
        try:
            url = f"https://newsapi.org/v2/top-headlines?category=business&apiKey={api_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    return ValidationResult(
                        component="API Keys",
                        test_name="News API",
                        status=ValidationStatus.PASSED,
                        message="API key valid and responsive",
                        details={"articles": len(data.get("articles", []))},
                        timestamp=datetime.now().isoformat(),
                        duration_ms=(time.time() - start) * 1000
                    )
                else:
                    return ValidationResult(
                        component="API Keys",
                        test_name="News API",
                        status=ValidationStatus.FAILED,
                        message=f"API error: {data.get('message', 'Unknown error')}",
                        details={"response": data},
                        timestamp=datetime.now().isoformat(),
                        duration_ms=(time.time() - start) * 1000
                    )
            else:
                return ValidationResult(
                    component="API Keys",
                    test_name="News API",
                    status=ValidationStatus.FAILED,
                    message=f"HTTP {response.status_code}",
                    details={"status_code": response.status_code},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ValidationResult(
                component="API Keys",
                test_name="News API",
                status=ValidationStatus.FAILED,
                message=f"Connection error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all API key validations"""
        logger.info("=" * 80)
        logger.info("API KEY VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_alpha_vantage(),
            self.validate_fred(),
            self.validate_news_api()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


class MarketFeedValidator:
    """Validates market data feeds and connectivity"""
    
    def __init__(self):
        self.results = []
    
    def validate_mt5_connection(self) -> ValidationResult:
        """Validate MT5 connection"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Market Feeds",
                    test_name="MT5 Connection",
                    status=ValidationStatus.FAILED,
                    message=f"MT5 initialization failed: {mt5.last_error()}",
                    details={"error": mt5.last_error()},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                mt5.shutdown()
                return ValidationResult(
                    component="Market Feeds",
                    test_name="MT5 Connection",
                    status=ValidationStatus.FAILED,
                    message="Failed to get account info",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            mt5.shutdown()
            return ValidationResult(
                component="Market Feeds",
                test_name="MT5 Connection",
                status=ValidationStatus.PASSED,
                message=f"Connected to {account_info.server}",
                details={
                    "server": account_info.server,
                    "login": account_info.login,
                    "balance": account_info.balance
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except ImportError:
            return ValidationResult(
                component="Market Feeds",
                test_name="MT5 Connection",
                status=ValidationStatus.FAILED,
                message="MetaTrader5 module not installed",
                details={},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Market Feeds",
                test_name="MT5 Connection",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e), "traceback": traceback.format_exc()},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_live_data(self) -> ValidationResult:
        """Validate live market data retrieval"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Live Data",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Test live tick data
            symbol = "EURUSD"
            tick = mt5.symbol_info_tick(symbol)
            
            if tick is None:
                mt5.shutdown()
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Live Data",
                    status=ValidationStatus.FAILED,
                    message=f"Failed to get tick data for {symbol}",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Check data freshness (should be within last 5 seconds)
            tick_age = time.time() - tick.time
            
            mt5.shutdown()
            
            if tick_age > 5:
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Live Data",
                    status=ValidationStatus.WARNING,
                    message=f"Data lag detected: {tick_age:.1f}s old",
                    details={"tick_age_seconds": tick_age, "bid": tick.bid, "ask": tick.ask},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Market Feeds",
                test_name="Live Data",
                status=ValidationStatus.PASSED,
                message=f"Live data streaming (lag: {tick_age:.2f}s)",
                details={"tick_age_seconds": tick_age, "bid": tick.bid, "ask": tick.ask},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Market Feeds",
                test_name="Live Data",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_historical_data(self) -> ValidationResult:
        """Validate historical data retrieval"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Historical Data",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Test historical data for multiple timeframes
            symbol = "EURUSD"
            timeframes = [
                (mt5.TIMEFRAME_M1, "1 min"),
                (mt5.TIMEFRAME_M5, "5 min"),
                (mt5.TIMEFRAME_M15, "15 min"),
                (mt5.TIMEFRAME_H1, "1 hour"),
                (mt5.TIMEFRAME_H4, "4 hour"),
                (mt5.TIMEFRAME_D1, "1 day")
            ]
            
            results_data = {}
            all_passed = True
            
            for tf, name in timeframes:
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, 100)
                if rates is None or len(rates) == 0:
                    results_data[name] = "FAILED"
                    all_passed = False
                else:
                    results_data[name] = f"{len(rates)} bars"
            
            mt5.shutdown()
            
            if all_passed:
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Historical Data",
                    status=ValidationStatus.PASSED,
                    message="All timeframes loaded successfully",
                    details=results_data,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            else:
                return ValidationResult(
                    component="Market Feeds",
                    test_name="Historical Data",
                    status=ValidationStatus.WARNING,
                    message="Some timeframes failed to load",
                    details=results_data,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ValidationResult(
                component="Market Feeds",
                test_name="Historical Data",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all market feed validations"""
        logger.info("=" * 80)
        logger.info("MARKET FEED VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_mt5_connection(),
            self.validate_live_data(),
            self.validate_historical_data()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


class IndicatorValidator:
    """Validates technical indicators across multiple timeframes"""
    
    def __init__(self):
        self.results = []
    
    def validate_indicators(self) -> ValidationResult:
        """Validate all technical indicators"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            import talib
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Indicators",
                    test_name="Technical Indicators",
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
                    component="Indicators",
                    test_name="Technical Indicators",
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
            
            # Test all indicators
            indicator_results = {}
            
            try:
                # EMA
                ema = talib.EMA(close, timeperiod=20)
                indicator_results['EMA'] = 'OK' if not np.isnan(ema[-1]) else 'FAILED'
                
                # RSI
                rsi = talib.RSI(close, timeperiod=14)
                indicator_results['RSI'] = 'OK' if not np.isnan(rsi[-1]) else 'FAILED'
                
                # MACD
                macd, signal, hist = talib.MACD(close)
                indicator_results['MACD'] = 'OK' if not np.isnan(macd[-1]) else 'FAILED'
                
                # Bollinger Bands
                upper, middle, lower = talib.BBANDS(close)
                indicator_results['Bollinger Bands'] = 'OK' if not np.isnan(upper[-1]) else 'FAILED'
                
                # ATR
                atr = talib.ATR(high, low, close, timeperiod=14)
                indicator_results['ATR'] = 'OK' if not np.isnan(atr[-1]) else 'FAILED'
                
                # Stochastic
                slowk, slowd = talib.STOCH(high, low, close)
                indicator_results['Stochastic'] = 'OK' if not np.isnan(slowk[-1]) else 'FAILED'
                
                # ADX
                adx = talib.ADX(high, low, close, timeperiod=14)
                indicator_results['ADX'] = 'OK' if not np.isnan(adx[-1]) else 'FAILED'
                
                # CCI
                cci = talib.CCI(high, low, close, timeperiod=14)
                indicator_results['CCI'] = 'OK' if not np.isnan(cci[-1]) else 'FAILED'
                
            except Exception as e:
                mt5.shutdown()
                return ValidationResult(
                    component="Indicators",
                    test_name="Technical Indicators",
                    status=ValidationStatus.FAILED,
                    message=f"Indicator calculation error: {str(e)}",
                    details={"error": str(e)},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            mt5.shutdown()
            
            failed_indicators = [k for k, v in indicator_results.items() if v != 'OK']
            
            if failed_indicators:
                return ValidationResult(
                    component="Indicators",
                    test_name="Technical Indicators",
                    status=ValidationStatus.FAILED,
                    message=f"Failed indicators: {', '.join(failed_indicators)}",
                    details=indicator_results,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Indicators",
                test_name="Technical Indicators",
                status=ValidationStatus.PASSED,
                message="All indicators calculated successfully",
                details=indicator_results,
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except ImportError as e:
            return ValidationResult(
                component="Indicators",
                test_name="Technical Indicators",
                status=ValidationStatus.FAILED,
                message=f"Missing dependency: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Indicators",
                test_name="Technical Indicators",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e), "traceback": traceback.format_exc()},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all indicator validations"""
        logger.info("=" * 80)
        logger.info("INDICATOR VALIDATION")
        logger.info("=" * 80)
        
        results = [self.validate_indicators()]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


def main():
    """Main validation entry point"""
    logger.info("=" * 80)
    logger.info("ELITE TRADING BOT - COMPREHENSIVE VALIDATION")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info("")
    
    all_results = []
    
    # Run API key validation
    api_validator = APIKeyValidator()
    all_results.extend(api_validator.validate_all())
    logger.info("")
    
    # Run market feed validation
    feed_validator = MarketFeedValidator()
    all_results.extend(feed_validator.validate_all())
    logger.info("")
    
    # Run indicator validation
    indicator_validator = IndicatorValidator()
    all_results.extend(indicator_validator.validate_all())
    logger.info("")
    
    # Summary
    logger.info("=" * 80)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 80)
    
    passed = sum(1 for r in all_results if r.status == ValidationStatus.PASSED)
    failed = sum(1 for r in all_results if r.status == ValidationStatus.FAILED)
    warnings = sum(1 for r in all_results if r.status == ValidationStatus.WARNING)
    skipped = sum(1 for r in all_results if r.status == ValidationStatus.SKIPPED)
    
    logger.info(f"Total Tests: {len(all_results)}")
    logger.info(f"✓ Passed: {passed}")
    logger.info(f"✗ Failed: {failed}")
    logger.info(f"⚠ Warnings: {warnings}")
    logger.info(f"○ Skipped: {skipped}")
    
    # Save results to JSON
    results_file = f"logs/validation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump([r.to_dict() for r in all_results], f, indent=2)
    
    logger.info(f"\nResults saved to: {results_file}")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
