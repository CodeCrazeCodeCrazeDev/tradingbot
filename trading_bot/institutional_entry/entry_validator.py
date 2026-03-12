"""
Elite Trading Bot - Entry Validator

This module provides validation capabilities for entry triggers,
filtering out false signals and ensuring high-quality trade entries.
"""

import enum
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .wyckoff_ict_fusion import EntryTrigger, EntryType
from enum import Enum
import numpy
import pandas

# Configure logging
logger = logging.getLogger(__name__)


class ValidationResult(enum.Enum):
    """Results of entry validation."""
    VALID = "valid"                 # Entry is valid
    INVALID = "invalid"             # Entry is invalid
    NEEDS_CONFIRMATION = "needs_confirmation"  # Entry needs additional confirmation
    DEFER = "defer"                 # Defer decision to other validators


@dataclass
class ValidationRule:
    """Rule for validating entry triggers."""
    name: str
    description: str
    validator_func: Callable[[EntryTrigger, Dict[str, Any]], ValidationResult]
    entry_types: Optional[Set[EntryType]] = None  # None means all types
    priority: int = 0  # Higher priority rules are evaluated first
    
    def validate(self, 
                trigger: EntryTrigger, 
                context: Dict[str, Any]) -> ValidationResult:
        """
        Validate an entry trigger against this rule.
        
        Args:
            trigger: Entry trigger to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult
        """
        # Check if rule applies to this entry type
        try:
            if self.entry_types is not None and trigger.entry_type not in self.entry_types:
                return ValidationResult.DEFER
            
            # Apply validation function
            return self.validator_func(trigger, context)
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class FalseSignalFilter:
    """
    Filters out false signals based on market conditions and price action.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize false signal filter.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            logger.info("FalseSignalFilter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "min_volume_threshold": 1.2,  # Minimum volume multiple for confirmation
                "min_candle_body_ratio": 0.5,  # Minimum ratio of body to total candle height
                "max_wick_ratio": 0.3,  # Maximum ratio of wick to total candle height
                "min_confirmation_candles": 2,  # Minimum number of confirmation candles
                "liquidity_trap_threshold": 0.2,  # % beyond key level for liquidity trap detection
                "enable_volume_filter": True,  # Enable volume-based filtering
                "enable_price_action_filter": True,  # Enable price action filtering
                "enable_liquidity_trap_filter": True,  # Enable liquidity trap detection
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def filter_false_signals(self, 
                           trigger: EntryTrigger, 
                           data: Dict[str, pd.DataFrame]) -> bool:
        """
        Filter out false signals.
        
        Args:
            trigger: Entry trigger to validate
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            True if signal is valid, False if it's a false signal
        """
        # Get data for trigger timeframe
        try:
            if trigger.timeframe not in data or data[trigger.timeframe].empty:
                logger.warning(f"No data for timeframe {trigger.timeframe}")
                return False
            
            df = data[trigger.timeframe]
        
            # Apply filters based on configuration
            if self.config["enable_volume_filter"] and 'volume' in df.columns:
                if not self._validate_volume(trigger, df):
                    logger.info("Entry trigger %s failed volume validation", trigger.id)
                    return False
                
            if self.config["enable_price_action_filter"]:
                if not self._validate_price_action(trigger, df):
                    logger.info("Entry trigger %s failed price action validation", trigger.id)
                    return False
                
            if self.config["enable_liquidity_trap_filter"]:
                if self._detect_liquidity_trap(trigger, df):
                    logger.info("Entry trigger %s detected as liquidity trap", trigger.id)
                    return False
        
            return True
        except Exception as e:
            logger.error(f"Error in filter_false_signals: {e}")
            raise
    
    def _validate_volume(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Validate entry based on volume.
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if volume is valid, False otherwise
        """
        # Find candle closest to trigger time
        try:
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < 0 or closest_idx >= len(df):
                return False
            
            # Get volume for trigger candle and previous candles
            trigger_volume = df.iloc[closest_idx]['volume']
            avg_volume = df.iloc[max(0, closest_idx-10):closest_idx]['volume'].mean()
        
            # Check if volume is sufficient
            if avg_volume > 0:
                volume_ratio = trigger_volume / avg_volume
                return volume_ratio >= self.config["min_volume_threshold"]
        
            return False
        except Exception as e:
            logger.error(f"Error in _validate_volume: {e}")
            raise
    
    def _validate_price_action(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Validate entry based on price action.
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if price action is valid, False otherwise
        """
        # Find candle closest to trigger time
        try:
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < 0 or closest_idx >= len(df) - 1:
                return False
            
            # Get trigger candle and next candle
            trigger_candle = df.iloc[closest_idx]
            next_candle = df.iloc[closest_idx + 1]
        
            # Calculate candle properties
            trigger_body = abs(trigger_candle['close'] - trigger_candle['open'])
            trigger_range = trigger_candle['high'] - trigger_candle['low']
        
            if trigger_range > 0:
                body_ratio = trigger_body / trigger_range
            
                # For long entries
                if trigger.direction == "long":
                    # Check for bullish candle
                    is_bullish = trigger_candle['close'] > trigger_candle['open']
                
                    # Check for confirmation in next candle
                    next_confirmation = next_candle['close'] > next_candle['open']
                
                    # Check body ratio
                    valid_body = body_ratio >= self.config["min_candle_body_ratio"]
                
                    # Check bottom wick (should be small for valid long entry)
                    bottom_wick = (trigger_candle['open'] if is_bullish else trigger_candle['close']) - trigger_candle['low']
                    bottom_wick_ratio = bottom_wick / trigger_range if trigger_range > 0 else 1.0
                    valid_wick = bottom_wick_ratio <= self.config["max_wick_ratio"]
                
                    return is_bullish and next_confirmation and valid_body and valid_wick
                
                # For short entries
                else:
                    # Check for bearish candle
                    is_bearish = trigger_candle['close'] < trigger_candle['open']
                
                    # Check for confirmation in next candle
                    next_confirmation = next_candle['close'] < next_candle['open']
                
                    # Check body ratio
                    valid_body = body_ratio >= self.config["min_candle_body_ratio"]
                
                    # Check top wick (should be small for valid short entry)
                    top_wick = trigger_candle['high'] - (trigger_candle['close'] if is_bearish else trigger_candle['open'])
                    top_wick_ratio = top_wick / trigger_range if trigger_range > 0 else 1.0
                    valid_wick = top_wick_ratio <= self.config["max_wick_ratio"]
                
                    return is_bearish and next_confirmation and valid_body and valid_wick
        
            return False
        except Exception as e:
            logger.error(f"Error in _validate_price_action: {e}")
            raise
    
    def _detect_liquidity_trap(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Detect liquidity traps (false breakouts designed to trap traders).
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if liquidity trap detected, False otherwise
        """
        # Find candle closest to trigger time
        try:
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < 0 or closest_idx >= len(df) - 3:
                return False
            
            # Get key price levels based on entry type
            key_level = None
        
            if trigger.entry_type == EntryType.SPRING:
                # Key level is the low of the spring
                key_level = trigger.price
            
            elif trigger.entry_type == EntryType.UPTHRUST:
                # Key level is the high of the upthrust
                key_level = trigger.price
            
            elif trigger.entry_type == EntryType.ORDER_BLOCK_MITIGATION:
                # Key level depends on direction
                if trigger.direction == "long":
                    key_level = trigger.order_blocks[0].low if trigger.order_blocks else None
                else:
                    key_level = trigger.order_blocks[0].high if trigger.order_blocks else None
                
            elif trigger.entry_type == EntryType.FAIR_VALUE_GAP_FILL:
                # Key level depends on direction
                if trigger.direction == "long":
                    key_level = trigger.fair_value_gaps[0].low if trigger.fair_value_gaps else None
                else:
                    key_level = trigger.fair_value_gaps[0].high if trigger.fair_value_gaps else None
        
            if key_level is None:
                return False
            
            # Check for liquidity trap
            threshold = key_level * self.config["liquidity_trap_threshold"]
        
            # For long entries
            if trigger.direction == "long":
                # Check if price briefly went below key level then reversed
                trap_detected = False
            
                for i in range(closest_idx, min(closest_idx + 3, len(df))):
                    if df.iloc[i]['low'] < key_level - threshold:
                        # Price went below key level
                        if i < len(df) - 1 and df.iloc[i+1]['close'] > key_level:
                            # Then quickly reversed
                            trap_detected = True
                            break
            
                return trap_detected
            
            # For short entries
            else:
                # Check if price briefly went above key level then reversed
                trap_detected = False
            
                for i in range(closest_idx, min(closest_idx + 3, len(df))):
                    if df.iloc[i]['high'] > key_level + threshold:
                        # Price went above key level
                        if i < len(df) - 1 and df.iloc[i+1]['close'] < key_level:
                            # Then quickly reversed
                            trap_detected = True
                            break
            
                return trap_detected
        except Exception as e:
            logger.error(f"Error in _detect_liquidity_trap: {e}")
            raise


class MarketStructureValidator:
    """
    Validates entry triggers based on market structure.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize market structure validator.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            logger.info("MarketStructureValidator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "swing_window": 5,  # Window for detecting swing highs/lows
                "trend_sma_period": 50,  # Period for trend SMA
                "min_structure_points": 3,  # Minimum number of structure points
                "enable_trend_filter": True,  # Enable trend-based filtering
                "enable_structure_filter": True,  # Enable structure-based filtering
                "enable_momentum_filter": True,  # Enable momentum-based filtering
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def validate_market_structure(self, 
                                trigger: EntryTrigger, 
                                data: Dict[str, pd.DataFrame]) -> bool:
        """
        Validate entry based on market structure.
        
        Args:
            trigger: Entry trigger to validate
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            True if market structure is valid, False otherwise
        """
        # Get data for trigger timeframe
        try:
            if trigger.timeframe not in data or data[trigger.timeframe].empty:
                logger.warning(f"No data for timeframe {trigger.timeframe}")
                return False
            
            df = data[trigger.timeframe]
        
            # Apply filters based on configuration
            if self.config["enable_trend_filter"]:
                if not self._validate_trend_alignment(trigger, df):
                    logger.info("Entry trigger %s failed trend alignment validation", trigger.id)
                    return False
                
            if self.config["enable_structure_filter"]:
                if not self._validate_market_structure(trigger, df):
                    logger.info("Entry trigger %s failed market structure validation", trigger.id)
                    return False
                
            if self.config["enable_momentum_filter"]:
                if not self._validate_momentum(trigger, df):
                    logger.info("Entry trigger %s failed momentum validation", trigger.id)
                    return False
        
            return True
        except Exception as e:
            logger.error(f"Error in validate_market_structure: {e}")
            raise
    
    def _validate_trend_alignment(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Validate entry based on trend alignment.
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if trend is aligned with entry direction, False otherwise
        """
        # Calculate trend using SMA
        try:
            df = df.copy()
            df['sma'] = df['close'].rolling(window=self.config["trend_sma_period"]).mean()
        
            # Find candle closest to trigger time
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < 0 or closest_idx >= len(df):
                return False
            
            # Get current price and SMA
            current_price = df.iloc[closest_idx]['close']
            current_sma = df.iloc[closest_idx]['sma']
        
            # Check trend alignment
            if trigger.direction == "long":
                # For long entries, price should be above SMA
                return current_price > current_sma
            else:
                # For short entries, price should be below SMA
                return current_price < current_sma
        except Exception as e:
            logger.error(f"Error in _validate_trend_alignment: {e}")
            raise
    
    def _validate_market_structure(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Validate entry based on market structure.
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if market structure is valid, False otherwise
        """
        # Calculate swing highs and lows
        try:
            df = df.copy()
            window = self.config["swing_window"]
        
            # Detect swing highs and lows
            df['swing_high'] = df['high'].rolling(window=2*window+1, center=True).apply(
                lambda x: x[window] == max(x), raw=True
            )
            df['swing_low'] = df['low'].rolling(window=2*window+1, center=True).apply(
                lambda x: x[window] == min(x), raw=True
            )
        
            # Find candle closest to trigger time
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < window or closest_idx >= len(df) - window:
                return False
            
            # Get recent swing points
            recent_df = df.iloc[max(0, closest_idx-30):closest_idx+1]
        
            # For long entries
            if trigger.direction == "long":
                # Check for higher lows (bullish structure)
                swing_lows = recent_df[recent_df['swing_low'] == True]
            
                if len(swing_lows) >= self.config["min_structure_points"]:
                    # Check if recent swing lows are making higher lows
                    recent_swing_lows = swing_lows.tail(self.config["min_structure_points"])
                    lows = recent_swing_lows['low'].values
                
                    # Check if lows are increasing
                    is_higher_lows = all(lows[i] <= lows[i+1] for i in range(len(lows)-1))
                
                    return is_higher_lows
        
            # For short entries
            else:
                # Check for lower highs (bearish structure)
                swing_highs = recent_df[recent_df['swing_high'] == True]
            
                if len(swing_highs) >= self.config["min_structure_points"]:
                    # Check if recent swing highs are making lower highs
                    recent_swing_highs = swing_highs.tail(self.config["min_structure_points"])
                    highs = recent_swing_highs['high'].values
                
                    # Check if highs are decreasing
                    is_lower_highs = all(highs[i] >= highs[i+1] for i in range(len(highs)-1))
                
                    return is_lower_highs
        
            return False
        except Exception as e:
            logger.error(f"Error in _validate_market_structure: {e}")
            raise
    
    def _validate_momentum(self, trigger: EntryTrigger, df: pd.DataFrame) -> bool:
        """
        Validate entry based on momentum.
        
        Args:
            trigger: Entry trigger to validate
            df: OHLCV DataFrame
            
        Returns:
            True if momentum is valid, False otherwise
        """
        # Calculate momentum indicators
        try:
            df = df.copy()
        
            # Calculate RSI if not already present
            if 'rsi' not in df.columns:
                delta = df['close'].diff()
                gain = delta.where(delta > 0, 0)
                loss = -delta.where(delta < 0, 0)
            
                avg_gain = gain.rolling(window=14).mean()
                avg_loss = loss.rolling(window=14).mean()
            
                rs = avg_gain / avg_loss
                df['rsi'] = 100 - (100 / (1 + rs))
        
            # Calculate MACD if not already present
            if 'macd' not in df.columns:
                ema12 = df['close'].ewm(span=12, adjust=False).mean()
                ema26 = df['close'].ewm(span=26, adjust=False).mean()
                df['macd'] = ema12 - ema26
                df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
                df['macd_hist'] = df['macd'] - df['macd_signal']
        
            # Find candle closest to trigger time
            trigger_time = trigger.timestamp
            closest_idx = df.index.get_indexer([trigger_time], method='nearest')[0]
        
            if closest_idx < 14 or closest_idx >= len(df):
                return False
            
            # Get momentum values
            rsi = df.iloc[closest_idx]['rsi']
            macd = df.iloc[closest_idx]['macd']
            macd_signal = df.iloc[closest_idx]['macd_signal']
            macd_hist = df.iloc[closest_idx]['macd_hist']
        
            # Check momentum alignment
            if trigger.direction == "long":
                # For long entries, RSI should be above 40 and MACD histogram should be positive or crossing
                rsi_valid = rsi > 40
                macd_valid = macd_hist > 0 or (macd_hist > df.iloc[closest_idx-1]['macd_hist'])
            
                return rsi_valid and macd_valid
            else:
                # For short entries, RSI should be below 60 and MACD histogram should be negative or crossing
                rsi_valid = rsi < 60
                macd_valid = macd_hist < 0 or (macd_hist < df.iloc[closest_idx-1]['macd_hist'])
            
                return rsi_valid and macd_valid
        except Exception as e:
            logger.error(f"Error in _validate_momentum: {e}")
            raise


class EntryValidator:
    """
    Validates entry triggers using multiple validation rules and filters.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize entry validator.
        
        Args:
            config: Optional configuration dictionary
        """
        try:
            self.config = config or {}
            self._init_default_config()
        
            # Initialize components
            self.false_signal_filter = FalseSignalFilter(self.config.get("false_signal_filter_config"))
            self.market_structure_validator = MarketStructureValidator(self.config.get("market_structure_validator_config"))
        
            # Validation rules
            self.validation_rules: List[ValidationRule] = []
            self._init_default_rules()
        
            logger.info("EntryValidator initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _init_default_config(self):
        """Initialize default configuration if not provided."""
        try:
            defaults = {
                "min_confidence_threshold": 0.6,  # Minimum confidence for valid entry
                "min_confirmations": 2,  # Minimum number of confirmations
                "enable_false_signal_filter": True,  # Enable false signal filtering
                "enable_market_structure_validator": True,  # Enable market structure validation
                "enable_volume_confirmation": True,  # Enable volume confirmation
                "enable_multi_timeframe_alignment": True,  # Enable multi-timeframe alignment
            }
        
            for key, value in defaults.items():
                if key not in self.config:
                    self.config[key] = value
        except Exception as e:
            logger.error(f"Error in _init_default_config: {e}")
            raise
    
    def _init_default_rules(self):
        """Initialize default validation rules."""
        # Confidence threshold rule
        try:
            self.add_rule(ValidationRule(
                name="confidence_threshold",
                description="Validates that entry trigger confidence is above minimum threshold",
                validator_func=self._validate_confidence,
                priority=10
            ))
        
            # Confirmation count rule
            self.add_rule(ValidationRule(
                name="confirmation_count",
                description="Validates that entry trigger has minimum number of confirmations",
                validator_func=self._validate_confirmations,
                priority=9
            ))
        
            # Volume confirmation rule
            if self.config["enable_volume_confirmation"]:
                self.add_rule(ValidationRule(
                    name="volume_confirmation",
                    description="Validates that entry has volume confirmation",
                    validator_func=self._validate_volume_confirmation,
                    priority=8
                ))
        
            # Multi-timeframe alignment rule
            if self.config["enable_multi_timeframe_alignment"]:
                self.add_rule(ValidationRule(
                    name="multi_timeframe_alignment",
                    description="Validates that multiple timeframes are aligned with entry direction",
                    validator_func=self._validate_multi_timeframe_alignment,
                    priority=7
                ))
        except Exception as e:
            logger.error(f"Error in _init_default_rules: {e}")
            raise
    
    def add_rule(self, rule: ValidationRule):
        """
        Add a validation rule.
        
        Args:
            rule: Validation rule to add
        """
        try:
            self.validation_rules.append(rule)
        
            # Sort rules by priority (descending)
            self.validation_rules.sort(key=lambda x: x.priority, reverse=True)
        except Exception as e:
            logger.error(f"Error in add_rule: {e}")
            raise
    
    def validate_entry(self, 
                     trigger: EntryTrigger, 
                     data: Dict[str, pd.DataFrame]) -> Tuple[bool, str]:
        """
        Validate an entry trigger.
        
        Args:
            trigger: Entry trigger to validate
            data: Dictionary of timeframe -> OHLCV DataFrame
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Apply validation rules
        try:
            for rule in self.validation_rules:
                result = rule.validate(trigger, {"data": data})
            
                if result == ValidationResult.INVALID:
                    return False, f"Failed validation rule: {rule.name} - {rule.description}"
                elif result == ValidationResult.NEEDS_CONFIRMATION:
                    return False, f"Needs additional confirmation: {rule.name} - {rule.description}"
                elif result == ValidationResult.VALID:
                    # Rule explicitly validated the trigger
                    continue
                # DEFER means continue to next rule
        
            # Apply false signal filter
            if self.config["enable_false_signal_filter"]:
                if not self.false_signal_filter.filter_false_signals(trigger, data):
                    return False, "Failed false signal filter"
        
            # Apply market structure validator
            if self.config["enable_market_structure_validator"]:
                if not self.market_structure_validator.validate_market_structure(trigger, data):
                    return False, "Failed market structure validation"
        
            return True, "Entry trigger is valid"
        except Exception as e:
            logger.error(f"Error in validate_entry: {e}")
            raise
    
    def _validate_confidence(self, 
                           trigger: EntryTrigger, 
                           context: Dict[str, Any]) -> ValidationResult:
        """
        Validate entry trigger confidence.
        
        Args:
            trigger: Entry trigger to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult
        """
        try:
            if trigger.confidence >= self.config["min_confidence_threshold"]:
                return ValidationResult.DEFER  # Continue to next rule
            else:
                return ValidationResult.INVALID
        except Exception as e:
            logger.error(f"Error in _validate_confidence: {e}")
            raise
    
    def _validate_confirmations(self, 
                              trigger: EntryTrigger, 
                              context: Dict[str, Any]) -> ValidationResult:
        """
        Validate entry trigger confirmations.
        
        Args:
            trigger: Entry trigger to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult
        """
        try:
            if len(trigger.confirmations) >= self.config["min_confirmations"]:
                return ValidationResult.DEFER  # Continue to next rule
            else:
                return ValidationResult.NEEDS_CONFIRMATION
        except Exception as e:
            logger.error(f"Error in _validate_confirmations: {e}")
            raise
    
    def _validate_volume_confirmation(self, 
                                    trigger: EntryTrigger, 
                                    context: Dict[str, Any]) -> ValidationResult:
        """
        Validate volume confirmation.
        
        Args:
            trigger: Entry trigger to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult
        """
        # Check if trigger has volume confirmation
        try:
            if trigger.volume_confirmation:
                return ValidationResult.DEFER  # Continue to next rule
        
            # Check if volume confirmation is required for this entry type
            volume_required_types = {
                EntryType.SPRING, 
                EntryType.UPTHRUST,
                EntryType.LAST_POINT_OF_SUPPORT,
                EntryType.LAST_POINT_OF_SUPPLY,
                EntryType.ORDER_BLOCK_MITIGATION
            }
        
            if trigger.entry_type in volume_required_types:
                return ValidationResult.NEEDS_CONFIRMATION
            else:
                return ValidationResult.DEFER  # Continue to next rule
        except Exception as e:
            logger.error(f"Error in _validate_volume_confirmation: {e}")
            raise
    
    def _validate_multi_timeframe_alignment(self, 
                                          trigger: EntryTrigger, 
                                          context: Dict[str, Any]) -> ValidationResult:
        """
        Validate multi-timeframe alignment.
        
        Args:
            trigger: Entry trigger to validate
            context: Additional context for validation
            
        Returns:
            ValidationResult
        """
        # Check if trigger has multi-timeframe alignment
        try:
            if trigger.multi_timeframe_aligned:
                return ValidationResult.DEFER  # Continue to next rule
        
            # Check if MTF alignment is required for this entry type
            mtf_required_types = {
                EntryType.SPRING, 
                EntryType.UPTHRUST,
                EntryType.LAST_POINT_OF_SUPPORT,
                EntryType.LAST_POINT_OF_SUPPLY
            }
        
            if trigger.entry_type in mtf_required_types:
                return ValidationResult.NEEDS_CONFIRMATION
            else:
                return ValidationResult.DEFER  # Continue to next rule
        except Exception as e:
            logger.error(f"Error in _validate_multi_timeframe_alignment: {e}")
            raise
