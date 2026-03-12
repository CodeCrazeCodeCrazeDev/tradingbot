"""
Skill #7: Auction Market Theory Engine
======================================

Implements Auction Market Theory concepts: value area, POC,
balance/imbalance, and market facilitation.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuctionState(Enum):
    """Current auction state."""
    BALANCE = "balance"  # Price rotating within value
    IMBALANCE = "imbalance"  # Price seeking new value
    BREAKOUT = "breakout"  # Strong directional move
    INITIATIVE = "initiative"  # Aggressive buying/selling
    RESPONSIVE = "responsive"  # Reactive to value


class ParticipantType(Enum):
    """Type of market participant activity."""
    OTHER_TIMEFRAME_BUYER = "otf_buyer"
    OTHER_TIMEFRAME_SELLER = "otf_seller"
    DAY_TIMEFRAME = "day_timeframe"
    MIXED = "mixed"


class MarketFacilitation(Enum):
    """Market facilitation index state."""
    GREEN = "green"  # Volume up, MFI up - trend continuation
    FADE = "fade"  # Volume down, MFI up - weak move
    FAKE = "fake"  # Volume up, MFI down - distribution
    SQUAT = "squat"  # Volume down, MFI down - consolidation


@dataclass
class ValueReference:
    """Reference value levels."""
    developing_vah: float
    developing_val: float
    developing_poc: float
    prior_vah: float
    prior_val: float
    prior_poc: float
    weekly_vah: float
    weekly_val: float
    weekly_poc: float


@dataclass
class AuctionRotation:
    """Single auction rotation."""
    start_price: float
    end_price: float
    start_time: datetime
    end_time: datetime
    direction: str  # 'up' or 'down'
    bars: int
    volume: float
    is_complete: bool


@dataclass
class MarketContext:
    """Current market context."""
    auction_state: AuctionState
    participant_type: ParticipantType
    facilitation: MarketFacilitation
    is_one_timeframe: bool
    is_two_timeframe: bool
    excess_high: bool
    excess_low: bool
    poor_high: bool
    poor_low: bool


@dataclass
class AuctionAnalysisResult:
    """Complete auction market analysis."""
    value_reference: ValueReference
    current_context: MarketContext
    rotations: List[AuctionRotation]
    balance_target_high: float
    balance_target_low: float
    initiative_activity: str
    responsive_activity: str
    trading_recommendation: str
    confidence: float


class AuctionMarketTheoryEngine:
    """
    Advanced Auction Market Theory Analysis System.
    
    Analyzes market structure using auction theory principles.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.value_area_pct = self.config.get('value_area_pct', 0.70)
        self.rotation_threshold = self.config.get('rotation_threshold', 0.002)
        self.prior_value: Optional[ValueReference] = None
        self.rotations: List[AuctionRotation] = []
        
        logger.info("AuctionMarketTheoryEngine initialized")
    
    def analyze(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        timestamps: List[datetime],
        prior_session_data: Optional[Dict] = None
    ) -> AuctionAnalysisResult:
        """
        Perform complete auction market analysis.
        
        Args:
            highs: Array of high prices
            lows: Array of low prices
            closes: Array of close prices
            volumes: Array of volumes
            timestamps: List of timestamps
            prior_session_data: Optional prior session value area data
            
        Returns:
            AuctionAnalysisResult with complete analysis
        """
        # Calculate value reference levels
        value_reference = self._calculate_value_reference(
            highs, lows, closes, volumes, prior_session_data
        )
        
        # Identify auction rotations
        rotations = self._identify_rotations(highs, lows, closes, timestamps)
        
        # Determine market context
        current_context = self._determine_context(
            closes[-1], value_reference, rotations, highs, lows, volumes
        )
        
        # Calculate balance targets
        balance_high, balance_low = self._calculate_balance_targets(
            value_reference, rotations
        )
        
        # Identify initiative activity
        initiative = self._identify_initiative_activity(
            closes[-1], value_reference, rotations
        )
        
        # Identify responsive activity
        responsive = self._identify_responsive_activity(
            closes[-1], value_reference
        )
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            current_context, value_reference, closes[-1]
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(current_context, rotations)
        
        return AuctionAnalysisResult(
            value_reference=value_reference,
            current_context=current_context,
            rotations=rotations,
            balance_target_high=balance_high,
            balance_target_low=balance_low,
            initiative_activity=initiative,
            responsive_activity=responsive,
            trading_recommendation=recommendation,
            confidence=confidence
        )
    
    def _calculate_value_reference(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray,
        prior_data: Optional[Dict]
    ) -> ValueReference:
        """Calculate value area reference levels."""
        # Calculate developing value area
        dev_poc, dev_vah, dev_val = self._calculate_value_area(
            highs, lows, closes, volumes
        )
        
        # Prior session values (use provided or estimate)
        if prior_data:
            prior_poc = prior_data.get('poc', dev_poc)
            prior_vah = prior_data.get('vah', dev_vah)
            prior_val = prior_data.get('val', dev_val)
        else:
            # Estimate from first half of data
            half = len(highs) // 2
            if half > 10:
                prior_poc, prior_vah, prior_val = self._calculate_value_area(
                    highs[:half], lows[:half], closes[:half], volumes[:half]
                )
            else:
                prior_poc, prior_vah, prior_val = dev_poc, dev_vah, dev_val
        
        # Weekly values (estimate from full data)
        weekly_poc, weekly_vah, weekly_val = dev_poc, dev_vah, dev_val
        
        return ValueReference(
            developing_vah=dev_vah,
            developing_val=dev_val,
            developing_poc=dev_poc,
            prior_vah=prior_vah,
            prior_val=prior_val,
            prior_poc=prior_poc,
            weekly_vah=weekly_vah,
            weekly_val=weekly_val,
            weekly_poc=weekly_poc
        )
    
    def _calculate_value_area(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        volumes: np.ndarray
    ) -> Tuple[float, float, float]:
        """Calculate POC, VAH, VAL using volume profile."""
        # Create price levels
        price_min = np.min(lows)
        price_max = np.max(highs)
        
        tick_size = self._get_tick_size(price_min)
        num_levels = max(1, int((price_max - price_min) / tick_size))
        
        # Build volume profile
        volume_profile = np.zeros(num_levels)
        
        for i in range(len(highs)):
            low_idx = int((lows[i] - price_min) / tick_size)
            high_idx = int((highs[i] - price_min) / tick_size)
            
            low_idx = max(0, min(low_idx, num_levels - 1))
            high_idx = max(0, min(high_idx, num_levels - 1))
            
            # Distribute volume across touched levels
            levels_touched = high_idx - low_idx + 1
            vol_per_level = volumes[i] / levels_touched if levels_touched > 0 else 0
            
            for j in range(low_idx, high_idx + 1):
                if 0 <= j < num_levels:
                    volume_profile[j] += vol_per_level
        
        # Find POC (highest volume level)
        poc_idx = np.argmax(volume_profile)
        poc = price_min + poc_idx * tick_size
        
        # Calculate value area (70% of volume)
        total_volume = np.sum(volume_profile)
        target_volume = total_volume * self.value_area_pct
        
        # Expand from POC
        va_volume = volume_profile[poc_idx]
        upper_idx = poc_idx
        lower_idx = poc_idx
        
        while va_volume < target_volume:
            upper_vol = volume_profile[upper_idx + 1] if upper_idx + 1 < num_levels else 0
            lower_vol = volume_profile[lower_idx - 1] if lower_idx - 1 >= 0 else 0
            
            if upper_vol == 0 and lower_vol == 0:
                break
            
            if upper_vol >= lower_vol:
                upper_idx = min(upper_idx + 1, num_levels - 1)
                va_volume += upper_vol
            else:
                lower_idx = max(lower_idx - 1, 0)
                va_volume += lower_vol
        
        vah = price_min + upper_idx * tick_size
        val = price_min + lower_idx * tick_size
        
        return poc, vah, val
    
    def _get_tick_size(self, price: float) -> float:
        """Get appropriate tick size for price level."""
        if price < 1:
            return 0.0001
        elif price < 10:
            return 0.001
        elif price < 100:
            return 0.01
        elif price < 1000:
            return 0.1
        else:
            return 1.0
    
    def _identify_rotations(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        timestamps: List[datetime]
    ) -> List[AuctionRotation]:
        """Identify auction rotations (price swings)."""
        rotations = []
        
        if len(closes) < 3:
            return rotations
        
        # Find swing points
        direction = None
        rotation_start = 0
        rotation_price = closes[0]
        
        for i in range(1, len(closes)):
            price_change = (closes[i] - rotation_price) / rotation_price
            
            if direction is None:
                if price_change > self.rotation_threshold:
                    direction = 'up'
                elif price_change < -self.rotation_threshold:
                    direction = 'down'
            else:
                # Check for rotation completion
                if direction == 'up' and price_change < -self.rotation_threshold:
                    # Up rotation complete
                    rotations.append(AuctionRotation(
                        start_price=closes[rotation_start],
                        end_price=closes[i - 1],
                        start_time=timestamps[rotation_start],
                        end_time=timestamps[i - 1],
                        direction='up',
                        bars=i - rotation_start,
                        volume=0,  # Would need volume data
                        is_complete=True
                    ))
                    rotation_start = i - 1
                    rotation_price = closes[i - 1]
                    direction = 'down'
                    
                elif direction == 'down' and price_change > self.rotation_threshold:
                    # Down rotation complete
                    rotations.append(AuctionRotation(
                        start_price=closes[rotation_start],
                        end_price=closes[i - 1],
                        start_time=timestamps[rotation_start],
                        end_time=timestamps[i - 1],
                        direction='down',
                        bars=i - rotation_start,
                        volume=0,
                        is_complete=True
                    ))
                    rotation_start = i - 1
                    rotation_price = closes[i - 1]
                    direction = 'up'
        
        # Add current incomplete rotation
        if direction and rotation_start < len(closes) - 1:
            rotations.append(AuctionRotation(
                start_price=closes[rotation_start],
                end_price=closes[-1],
                start_time=timestamps[rotation_start],
                end_time=timestamps[-1],
                direction=direction,
                bars=len(closes) - rotation_start,
                volume=0,
                is_complete=False
            ))
        
        return rotations
    
    def _determine_context(
        self,
        current_price: float,
        value_ref: ValueReference,
        rotations: List[AuctionRotation],
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray
    ) -> MarketContext:
        """Determine current market context."""
        # Auction state
        if value_ref.developing_val <= current_price <= value_ref.developing_vah:
            auction_state = AuctionState.BALANCE
        elif current_price > value_ref.developing_vah:
            if current_price > value_ref.prior_vah:
                auction_state = AuctionState.BREAKOUT
            else:
                auction_state = AuctionState.IMBALANCE
        else:
            if current_price < value_ref.prior_val:
                auction_state = AuctionState.BREAKOUT
            else:
                auction_state = AuctionState.IMBALANCE
        
        # Participant type
        participant_type = self._identify_participant_type(
            current_price, value_ref, rotations
        )
        
        # Market facilitation
        facilitation = self._calculate_facilitation(highs, lows, volumes)
        
        # One/Two timeframe
        is_one_tf = self._is_one_timeframe(rotations)
        is_two_tf = not is_one_tf
        
        # Excess and poor structure
        excess_high = self._has_excess(highs, is_high=True)
        excess_low = self._has_excess(lows, is_high=False)
        poor_high = self._has_poor_structure(highs, is_high=True)
        poor_low = self._has_poor_structure(lows, is_high=False)
        
        return MarketContext(
            auction_state=auction_state,
            participant_type=participant_type,
            facilitation=facilitation,
            is_one_timeframe=is_one_tf,
            is_two_timeframe=is_two_tf,
            excess_high=excess_high,
            excess_low=excess_low,
            poor_high=poor_high,
            poor_low=poor_low
        )
    
    def _identify_participant_type(
        self,
        current_price: float,
        value_ref: ValueReference,
        rotations: List[AuctionRotation]
    ) -> ParticipantType:
        """Identify dominant participant type."""
        # Above value = OTF buyers
        if current_price > value_ref.developing_vah:
            return ParticipantType.OTHER_TIMEFRAME_BUYER
        
        # Below value = OTF sellers
        if current_price < value_ref.developing_val:
            return ParticipantType.OTHER_TIMEFRAME_SELLER
        
        # Within value = day timeframe
        if rotations:
            up_rotations = sum(1 for r in rotations if r.direction == 'up')
            down_rotations = sum(1 for r in rotations if r.direction == 'down')
            
            if up_rotations > down_rotations * 1.5:
                return ParticipantType.OTHER_TIMEFRAME_BUYER
            elif down_rotations > up_rotations * 1.5:
                return ParticipantType.OTHER_TIMEFRAME_SELLER
        
        return ParticipantType.DAY_TIMEFRAME
    
    def _calculate_facilitation(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        volumes: np.ndarray
    ) -> MarketFacilitation:
        """Calculate Market Facilitation Index state."""
        if len(highs) < 2:
            return MarketFacilitation.SQUAT
        
        # Current and previous MFI
        current_range = highs[-1] - lows[-1]
        prev_range = highs[-2] - lows[-2]
        
        current_vol = volumes[-1]
        prev_vol = volumes[-2]
        
        mfi_up = current_range > prev_range
        vol_up = current_vol > prev_vol
        
        if mfi_up and vol_up:
            return MarketFacilitation.GREEN
        elif mfi_up and not vol_up:
            return MarketFacilitation.FADE
        elif not mfi_up and vol_up:
            return MarketFacilitation.FAKE
        else:
            return MarketFacilitation.SQUAT
    
    def _is_one_timeframe(self, rotations: List[AuctionRotation]) -> bool:
        """Check if market is in one-timeframe mode (trending)."""
        if len(rotations) < 3:
            return False
        
        recent = rotations[-3:]
        directions = [r.direction for r in recent]
        
        # One timeframe = all rotations in same direction
        return len(set(directions)) == 1
    
    def _has_excess(self, prices: np.ndarray, is_high: bool) -> bool:
        """Check for excess (single print at extreme)."""
        if len(prices) < 3:
            return False
        
        if is_high:
            extreme = np.max(prices)
            count = np.sum(prices >= extreme * 0.999)
        else:
            extreme = np.min(prices)
            count = np.sum(prices <= extreme * 1.001)
        
        return count == 1
    
    def _has_poor_structure(self, prices: np.ndarray, is_high: bool) -> bool:
        """Check for poor structure (multiple touches at extreme)."""
        if len(prices) < 3:
            return False
        
        if is_high:
            extreme = np.max(prices)
            count = np.sum(prices >= extreme * 0.998)
        else:
            extreme = np.min(prices)
            count = np.sum(prices <= extreme * 1.002)
        
        return count >= 3
    
    def _calculate_balance_targets(
        self,
        value_ref: ValueReference,
        rotations: List[AuctionRotation]
    ) -> Tuple[float, float]:
        """Calculate balance area targets."""
        # Balance targets are typically value area extensions
        va_range = value_ref.developing_vah - value_ref.developing_val
        
        balance_high = value_ref.developing_vah + va_range * 0.5
        balance_low = value_ref.developing_val - va_range * 0.5
        
        return balance_high, balance_low
    
    def _identify_initiative_activity(
        self,
        current_price: float,
        value_ref: ValueReference,
        rotations: List[AuctionRotation]
    ) -> str:
        """Identify initiative (aggressive) activity."""
        if current_price > value_ref.prior_vah:
            return "Initiative buying above prior value - bullish"
        elif current_price < value_ref.prior_val:
            return "Initiative selling below prior value - bearish"
        else:
            return "No clear initiative activity"
    
    def _identify_responsive_activity(
        self,
        current_price: float,
        value_ref: ValueReference
    ) -> str:
        """Identify responsive (reactive) activity."""
        if abs(current_price - value_ref.prior_vah) < (value_ref.prior_vah - value_ref.prior_val) * 0.1:
            return "Responsive selling at prior VAH"
        elif abs(current_price - value_ref.prior_val) < (value_ref.prior_vah - value_ref.prior_val) * 0.1:
            return "Responsive buying at prior VAL"
        else:
            return "No clear responsive activity"
    
    def _generate_recommendation(
        self,
        context: MarketContext,
        value_ref: ValueReference,
        current_price: float
    ) -> str:
        """Generate trading recommendation."""
        recommendations = []
        
        # Based on auction state
        if context.auction_state == AuctionState.BALANCE:
            recommendations.append(
                f"BALANCE: Fade extremes. Buy near VAL ({value_ref.developing_val:.4f}), "
                f"sell near VAH ({value_ref.developing_vah:.4f})"
            )
        elif context.auction_state == AuctionState.BREAKOUT:
            if current_price > value_ref.developing_vah:
                recommendations.append("BREAKOUT UP: Follow the trend, buy pullbacks")
            else:
                recommendations.append("BREAKOUT DOWN: Follow the trend, sell rallies")
        elif context.auction_state == AuctionState.IMBALANCE:
            recommendations.append("IMBALANCE: Price seeking new value, be patient")
        
        # Based on participant type
        if context.participant_type == ParticipantType.OTHER_TIMEFRAME_BUYER:
            recommendations.append("OTF BUYERS active - bullish bias")
        elif context.participant_type == ParticipantType.OTHER_TIMEFRAME_SELLER:
            recommendations.append("OTF SELLERS active - bearish bias")
        
        # Based on structure
        if context.poor_high:
            recommendations.append("POOR HIGH: Likely to be revisited")
        if context.poor_low:
            recommendations.append("POOR LOW: Likely to be revisited")
        if context.excess_high:
            recommendations.append("EXCESS HIGH: Strong rejection, unlikely to break")
        if context.excess_low:
            recommendations.append("EXCESS LOW: Strong rejection, unlikely to break")
        
        return " | ".join(recommendations) if recommendations else "No clear signal"
    
    def _calculate_confidence(
        self,
        context: MarketContext,
        rotations: List[AuctionRotation]
    ) -> float:
        """Calculate confidence in the analysis."""
        confidence = 0.5
        
        # Clear auction state adds confidence
        if context.auction_state in [AuctionState.BALANCE, AuctionState.BREAKOUT]:
            confidence += 0.15
        
        # One timeframe adds confidence
        if context.is_one_timeframe:
            confidence += 0.1
        
        # Good structure adds confidence
        if context.excess_high or context.excess_low:
            confidence += 0.1
        
        # More rotations = more data = more confidence
        if len(rotations) >= 5:
            confidence += 0.1
        
        return min(1.0, confidence)
