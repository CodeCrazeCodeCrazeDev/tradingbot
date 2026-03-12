"""
from dataclasses import field
Schema Integration
Integrates Pydantic models with the trading system for data validation
"""

import logging
from typing import Dict, Any, Optional, Union, List
from datetime import datetime

from trading_bot.models.data_models import (
    MarketTick, OHLCBar, OrderFlowSnapshot, MicrostructureMetrics,
    AnalyticsResult, TradingSignal, OpportunityData, TradeResult
)

logger = logging.getLogger(__name__)

class SchemaValidator:
    """
    Validates data against Pydantic schemas
    Provides graceful fallbacks for invalid data
    """
    
    @staticmethod
    def validate_market_tick(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate market tick data"""
        try:
            validated = MarketTick(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Market tick validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Ensure price exists
                if 'price' not in data and 'close' in data:
                    data['price'] = data['close']
                elif 'price' not in data and 'bid' in data and 'ask' in data:
                    data['price'] = (data['bid'] + data['ask']) / 2
                
                # Ensure timestamp is datetime
                if 'timestamp' in data and not isinstance(data['timestamp'], datetime):
                    data['timestamp'] = datetime.now()
                
                validated = MarketTick(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Market tick validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_ohlc_bar(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate OHLC bar data"""
        try:
            validated = OHLCBar(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"OHLC bar validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'price' not in data and 'close' in data:
                    data['price'] = data['close']
                
                # Ensure OHLC values make sense
                if 'high' in data and 'low' in data:
                    if data['high'] < data['low']:
                        data['high'], data['low'] = data['low'], data['high']
                
                validated = OHLCBar(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"OHLC bar validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_order_flow(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate order flow data"""
        try:
            validated = OrderFlowSnapshot(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Order flow validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                for field in ['imbalance_ratio', 'pressure_score', 'momentum_score']:
                    if field in data:
                        # Clamp to valid range
                        data[field] = max(-1.0, min(1.0, data[field]))
                
                for field in ['exhaustion_level', 'absorption_score']:
                    if field in data:
                        # Clamp to valid range
                        data[field] = max(0.0, min(1.0, data[field]))
                
                validated = OrderFlowSnapshot(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Order flow validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_microstructure(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate microstructure data"""
        try:
            validated = MicrostructureMetrics(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Microstructure validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'liquidity_score' in data:
                    # Clamp to valid range
                    data['liquidity_score'] = max(0.0, min(1.0, data['liquidity_score']))
                
                validated = MicrostructureMetrics(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Microstructure validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_analytics(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate analytics data"""
        try:
            validated = AnalyticsResult(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Analytics validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'confidence' in data:
                    # Clamp to valid range
                    data['confidence'] = max(0.0, min(1.0, data['confidence']))
                
                validated = AnalyticsResult(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Analytics validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_trading_signal(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trading signal data"""
        try:
            validated = TradingSignal(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Trading signal validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'direction' in data:
                    # Normalize direction
                    data['direction'] = data['direction'].lower()
                    if data['direction'] not in ['buy', 'sell']:
                        data['direction'] = 'buy'  # Default to buy
                
                # Fix stop loss and take profit
                if 'direction' in data and 'entry_price' in data:
                    if data['direction'] == 'buy':
                        if 'stop_loss' in data and data['stop_loss'] >= data['entry_price']:
                            data['stop_loss'] = data['entry_price'] * 0.99  # 1% below
                        if 'take_profit' in data and data['take_profit'] <= data['entry_price']:
                            data['take_profit'] = data['entry_price'] * 1.02  # 2% above
                    else:  # sell
                        if 'stop_loss' in data and data['stop_loss'] <= data['entry_price']:
                            data['stop_loss'] = data['entry_price'] * 1.01  # 1% above
                        if 'take_profit' in data and data['take_profit'] >= data['entry_price']:
                            data['take_profit'] = data['entry_price'] * 0.98  # 2% below
                
                validated = TradingSignal(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Trading signal validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_opportunity(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate opportunity data"""
        try:
            validated = OpportunityData(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Opportunity validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'confidence' in data:
                    # Clamp to valid range
                    data['confidence'] = max(0.0, min(1.0, data['confidence']))
                
                if 'risk_score' in data:
                    # Clamp to valid range
                    data['risk_score'] = max(0.0, min(1.0, data['risk_score']))
                
                validated = OpportunityData(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Opportunity validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
    
    @staticmethod
    def validate_trade_result(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate trade result data"""
        try:
            validated = TradeResult(**data).dict()
            return validated
        except Exception as e:
            logger.warning(f"Trade result validation failed: {e}")
            try:
            # Attempt to fix and retry
                # Fix common issues
                if 'status' in data and data['status'] not in ['active', 'closed']:
                    data['status'] = 'active'
                
                validated = TradeResult(**data).dict()
                return validated
            except Exception as e2:
                logger.error(f"Trade result validation failed after fix attempt: {e2}")
                # Return original data as fallback
                return data
