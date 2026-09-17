"""
Advanced Vision-Flow Orchestrator
==================================

Integrates MICROFISH, OPENCLAW, OPENCLIP, and DeepFlow2.0 into a unified
analysis system for comprehensive market intelligence.

This orchestrator combines:
- MICROFISH: Micro-pattern detection in market microstructure
- OPENCLAW: Advanced feature extraction and selection
- OPENCLIP: Vision-language chart analysis
- DeepFlow2.0: Optical flow-based price movement analysis
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
import logging
import asyncio
from enum import Enum

from .microfish import MICROFISH, MicroFishConfig
from .openclaw import OPENCLAW, OpenClawConfig
from .openclip_trading import OPENCLIP, OpenCLIPConfig
from .deepflow2 import DeepFlow2, DeepFlowConfig

logger = logging.getLogger(__name__)


class SignalStrength(Enum):
    """Signal strength levels."""
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NEUTRAL = "neutral"


@dataclass
class UnifiedSignal:
    """Unified trading signal from all systems."""
    action: str  # BUY, SELL, HOLD
    strength: SignalStrength
    confidence: float
    components: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    microfish_config: Optional[MicroFishConfig] = None
    openclaw_config: Optional[OpenClawConfig] = None
    openclip_config: Optional[OpenCLIPConfig] = None
    deepflow_config: Optional[DeepFlowConfig] = None
    
    signal_weights: Dict[str, float] = field(default_factory=lambda: {
        'microfish': 0.25,
        'openclaw': 0.20,
        'openclip': 0.25,
        'deepflow': 0.30
    })
    
    min_confidence: float = 0.6
    enable_microfish: bool = True
    enable_openclaw: bool = True
    enable_openclip: bool = True
    enable_deepflow: bool = True
    device: str = "cuda" if torch.cuda.is_available() else "cpu"


class AdvancedVisionFlowOrchestrator:
    """
    Orchestrates MICROFISH, OPENCLAW, OPENCLIP, and DeepFlow2.0
    for comprehensive market analysis.
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.device = self.config.device
        
        self.microfish: Optional[MICROFISH] = None
        self.openclaw: Optional[OPENCLAW] = None
        self.openclip: Optional[OPENCLIP] = None
        self.deepflow: Optional[DeepFlow2] = None
        
        self._initialize_systems()
        
        self.signal_history: List[UnifiedSignal] = []
        self.running = False
        
        logger.info("🎯 Advanced Vision-Flow Orchestrator initialized")
    
    def _initialize_systems(self):
        """Initialize all subsystems."""
        if self.config.enable_microfish:
            self.microfish = MICROFISH(self.config.microfish_config)
            logger.info("   ✓ MICROFISH enabled")
        
        if self.config.enable_openclaw:
            self.openclaw = OPENCLAW(self.config.openclaw_config)
            logger.info("   ✓ OPENCLAW enabled")
        
        if self.config.enable_openclip:
            self.openclip = OPENCLIP(self.config.openclip_config)
            logger.info("   ✓ OPENCLIP enabled")
        
        if self.config.enable_deepflow:
            self.deepflow = DeepFlow2(self.config.deepflow_config)
            logger.info("   ✓ DeepFlow2.0 enabled")
    
    async def start(self):
        """Start all subsystems."""
        self.running = True
        
        tasks = []
        if self.microfish:
            tasks.append(self.microfish.start())
        if self.openclaw:
            tasks.append(self.openclaw.start())
        if self.openclip:
            tasks.append(self.openclip.start())
        if self.deepflow:
            tasks.append(self.deepflow.start())
        
        await asyncio.gather(*tasks)
        logger.info("🎯 Orchestrator started")
    
    async def stop(self):
        """Stop all subsystems."""
        self.running = False
        
        tasks = []
        if self.microfish:
            tasks.append(self.microfish.stop())
        if self.openclaw:
            tasks.append(self.openclaw.stop())
        if self.openclip:
            tasks.append(self.openclip.stop())
        if self.deepflow:
            tasks.append(self.deepflow.stop())
        
        await asyncio.gather(*tasks)
        logger.info("🎯 Orchestrator stopped")
    
    def analyze(
        self,
        price_data: Optional[np.ndarray] = None,
        tick_data: Optional[Dict] = None,
        order_flow: Optional[np.ndarray] = None,
        chart_image: Optional[np.ndarray] = None,
        text_descriptions: Optional[List[str]] = None,
        feature_data: Optional[Dict[str, np.ndarray]] = None
    ) -> UnifiedSignal:
        """
        Run comprehensive analysis using all available systems.
        
        Args:
            price_data: OHLCV data [length, 5]
            tick_data: Tick-level data for MICROFISH
            order_flow: Order flow data for MICROFISH
            chart_image: Chart image for OPENCLIP
            text_descriptions: Text descriptions for OPENCLIP
            feature_data: Multi-source features for OPENCLAW
        
        Returns:
            Unified trading signal
        """
        components = {}
        signals = []
        weights = []
        
        if self.microfish and tick_data:
            micro_result = self._analyze_microfish(tick_data, order_flow)
            components['microfish'] = micro_result
            if micro_result.get('signal') is not None:
                signals.append(micro_result['signal'])
                weights.append(self.config.signal_weights['microfish'])
        
        if self.openclaw and feature_data:
            claw_result = self._analyze_openclaw(feature_data)
            components['openclaw'] = claw_result
        
        if self.openclip and chart_image is not None:
            clip_result = self._analyze_openclip(chart_image, text_descriptions)
            components['openclip'] = clip_result
            if clip_result.get('signal'):
                signal_map = {'BUY': 1, 'SELL': -1, 'HOLD': 0}
                signals.append(signal_map.get(clip_result['signal']['action'], 0))
                weights.append(self.config.signal_weights['openclip'])
        
        if self.deepflow and price_data is not None:
            flow_result = self._analyze_deepflow(price_data)
            components['deepflow'] = flow_result
            if flow_result.get('signals'):
                signal_map = {
                    'strong_buy': 1.0, 'buy': 0.5,
                    'strong_sell': -1.0, 'sell': -0.5,
                    'hold': 0
                }
                signals.append(signal_map.get(flow_result['signals']['signal'], 0))
                weights.append(self.config.signal_weights['deepflow'])
        
        unified = self._combine_signals(signals, weights, components)
        self.signal_history.append(unified)
        
        return unified
    
    def _analyze_microfish(
        self, 
        tick_data: Dict,
        order_flow: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Run MICROFISH analysis."""
        result = {
            'patterns': [],
            'signal': None,
            'anomalies': []
        }
        
        pattern = self.microfish.process_tick(tick_data)
        if pattern:
            result['patterns'].append({
                'type': pattern.pattern_type.value,
                'confidence': pattern.confidence,
                'direction': pattern.direction
            })
            result['signal'] = pattern.direction
        
        if order_flow is not None:
            flow_analysis = self.microfish.analyze_order_flow(order_flow)
            result['order_flow'] = flow_analysis
        
        micro_signals = self.microfish.get_micro_signals()
        result['aggregated'] = micro_signals
        
        return result
    
    def _analyze_openclaw(
        self, 
        feature_data: Dict[str, np.ndarray]
    ) -> Dict[str, Any]:
        """Run OPENCLAW analysis."""
        extraction = self.openclaw.extract_features(feature_data, return_details=True)
        
        quality = self.openclaw.assess_feature_quality(extraction['features'])
        
        return {
            'features': extraction['features'],
            'importance': extraction['importance_scores'],
            'quality': quality,
            'num_features': extraction['num_features']
        }
    
    def _analyze_openclip(
        self,
        chart_image: np.ndarray,
        descriptions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run OPENCLIP analysis."""
        if descriptions is None:
            descriptions = [
                "bullish breakout pattern forming",
                "bearish reversal signal",
                "consolidation before move",
                "strong uptrend continuation",
                "downtrend with selling pressure"
            ]
        
        analysis = self.openclip.analyze_chart(chart_image, descriptions)
        
        return {
            'patterns': analysis.get('patterns', []),
            'pattern_confidence': analysis.get('pattern_confidence', 0),
            'text_matches': analysis.get('text_similarities', []),
            'signal': analysis.get('signal')
        }
    
    def _analyze_deepflow(self, price_data: np.ndarray) -> Dict[str, Any]:
        """Run DeepFlow2.0 analysis."""
        flow_estimate = self.deepflow.estimate_flow(price_data)
        
        divergence = self.deepflow.analyze_flow_divergence(price_data)
        
        anomalies = self.deepflow.detect_flow_anomalies(price_data)
        
        signals = self.deepflow.get_flow_signals(price_data)
        
        return {
            'flow': flow_estimate,
            'divergence': divergence,
            'anomalies': anomalies,
            'signals': signals
        }
    
    def _combine_signals(
        self,
        signals: List[float],
        weights: List[float],
        components: Dict[str, Any]
    ) -> UnifiedSignal:
        """Combine signals from all systems."""
        if not signals:
            return UnifiedSignal(
                action='HOLD',
                strength=SignalStrength.NEUTRAL,
                confidence=0.0,
                components=components
            )
        
        weights = np.array(weights)
        weights = weights / weights.sum()
        
        weighted_signal = np.sum(np.array(signals) * weights)
        
        confidences = []
        if 'microfish' in components:
            agg = components['microfish'].get('aggregated', {})
            confidences.append(agg.get('confidence', 0.5))
        if 'openclip' in components:
            confidences.append(components['openclip'].get('pattern_confidence', 0.5))
        if 'deepflow' in components:
            sigs = components['deepflow'].get('signals', {})
            confidences.append(sigs.get('confidence', 0.5))
        
        avg_confidence = np.mean(confidences) if confidences else 0.5
        
        if weighted_signal > 0.5:
            action = 'BUY'
            strength = SignalStrength.VERY_STRONG if weighted_signal > 0.75 else SignalStrength.STRONG
        elif weighted_signal > 0.2:
            action = 'BUY'
            strength = SignalStrength.MODERATE if weighted_signal > 0.35 else SignalStrength.WEAK
        elif weighted_signal < -0.5:
            action = 'SELL'
            strength = SignalStrength.VERY_STRONG if weighted_signal < -0.75 else SignalStrength.STRONG
        elif weighted_signal < -0.2:
            action = 'SELL'
            strength = SignalStrength.MODERATE if weighted_signal < -0.35 else SignalStrength.WEAK
        else:
            action = 'HOLD'
            strength = SignalStrength.NEUTRAL
        
        return UnifiedSignal(
            action=action,
            strength=strength,
            confidence=float(avg_confidence),
            components=components,
            metadata={
                'weighted_signal': float(weighted_signal),
                'num_signals': len(signals),
                'weights_used': weights.tolist()
            }
        )
    
    def get_realtime_analysis(self) -> Dict[str, Any]:
        """Get real-time analysis from all systems."""
        result = {}
        
        if self.microfish:
            result['microfish'] = self.microfish.get_micro_signals()
        
        if self.deepflow:
            flow = self.deepflow.get_realtime_flow()
            if flow:
                result['deepflow'] = flow
        
        if self.signal_history:
            result['last_signal'] = {
                'action': self.signal_history[-1].action,
                'strength': self.signal_history[-1].strength.value,
                'confidence': self.signal_history[-1].confidence
            }
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all systems."""
        status = {
            'running': self.running,
            'systems': {}
        }
        
        if self.microfish:
            status['systems']['microfish'] = self.microfish.get_status()
        if self.openclaw:
            status['systems']['openclaw'] = self.openclaw.get_status()
        if self.openclip:
            status['systems']['openclip'] = self.openclip.get_status()
        if self.deepflow:
            status['systems']['deepflow'] = self.deepflow.get_status()
        
        status['signal_history_size'] = len(self.signal_history)
        
        return status
    
    def save(self, base_path: str):
        """Save all system weights."""
        if self.microfish:
            self.microfish.save(f"{base_path}_microfish.pt")
        if self.openclaw:
            self.openclaw.save(f"{base_path}_openclaw.pt")
        if self.openclip:
            self.openclip.save(f"{base_path}_openclip.pt")
        if self.deepflow:
            self.deepflow.save(f"{base_path}_deepflow.pt")
        
        logger.info(f"🎯 All systems saved to {base_path}_*.pt")
    
    def load(self, base_path: str):
        """Load all system weights."""
        if self.microfish:
            self.microfish.load(f"{base_path}_microfish.pt")
        if self.openclaw:
            self.openclaw.load(f"{base_path}_openclaw.pt")
        if self.openclip:
            self.openclip.load(f"{base_path}_openclip.pt")
        if self.deepflow:
            self.deepflow.load(f"{base_path}_deepflow.pt")
        
        logger.info(f"🎯 All systems loaded from {base_path}_*.pt")


__all__ = [
    'AdvancedVisionFlowOrchestrator',
    'OrchestratorConfig',
    'UnifiedSignal',
    'SignalStrength'
]
