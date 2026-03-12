"""
Unified Opportunity Scanner Interface
Integrates all opportunity scanners with the optimized data pipeline
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

# Import opportunity scanners (optional - will use if available)
try:
    from trading_bot.opportunity_scanner.momentum_capture import MomentumCapture
except ImportError:
    MomentumCapture = None

try:
    from trading_bot.opportunity_scanner.volatility_trading import VolatilityTrading
except ImportError:
    VolatilityTrading = None

try:
    from trading_bot.opportunity_scanner.flow_analysis import FlowAnalysis
except ImportError:
    FlowAnalysis = None
# Import data pipeline components (optional)
    from trading_bot.database.data_streaming import MarketDataStream
except ImportError:
    MarketDataStream = None

try:
    from trading_bot.database.real_time_processor import DataProcessor
except ImportError:
    DataProcessor = None

try:
    from trading_bot.database.market_microstructure import MarketMicrostructure
except ImportError:
    MarketMicrostructure = None

try:
    from trading_bot.database.order_flow_processor import OrderFlowProcessor
except ImportError:
    OrderFlowProcessor = None

logger = logging.getLogger(__name__)

@dataclass
class OpportunityData:
    """Trading opportunity data"""
    id: str
    timestamp: datetime
    symbol: str
    type: str  # 'momentum', 'volatility', 'flow', etc.
    direction: str  # 'buy', 'sell'
    confidence: float
    expected_return: float
    risk_score: float
    timeframe: str
    entry_price: float
    stop_loss: float
    take_profit: float
    metadata: Dict[str, Any]

class UnifiedScanner:
    async def scan_all_opportunities(self, market_data: dict) -> list:
        """Scan all opportunities for all symbols in the provided market_data dict."""
        results = []
        for symbol, symbol_data in market_data.items():
            opps = await self.scan_opportunities(symbol, symbol_data)
            results.extend(opps)
        return results

    """
    Unified scanner that integrates all opportunity types
    Features:
    - Parallel scanning
    - Real-time data integration
    - Opportunity prioritization
    - Signal aggregation
    - Performance optimization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize scanners
        self.momentum_scanner = MomentumCapture(config) if MomentumCapture else None
        self.volatility_scanner = VolatilityTrading(config) if VolatilityTrading else None
        self.flow_scanner = FlowAnalysis(config) if FlowAnalysis else None
        
        # Initialize data pipeline components
        self.market_stream = None
        self.data_processor = None
        self.microstructure = None
        self.order_flow = None
        
        # Thread pool for parallel scanning
        self.executor = ThreadPoolExecutor(
            max_workers=config.get('scanner_workers', 8)
        )
        
        # Opportunity tracking
        self.opportunities: Dict[str, Dict[str, OpportunityData]] = {}
        self.opportunity_history: Dict[str, List[OpportunityData]] = {}
        
        # Performance metrics
        self.scan_times: Dict[str, List[float]] = {
            'momentum': [],
            'volatility': [],
            'flow': []
        }
        
        logger.info("Unified scanner initialized")
    
    async def initialize(self, 
                       market_stream: MarketDataStream,
                       data_processor: DataProcessor,
                       microstructure: MarketMicrostructure,
                       order_flow: OrderFlowProcessor):
        """Initialize scanner with data pipeline components"""
        self.market_stream = market_stream
        self.data_processor = data_processor
        self.microstructure = microstructure
        self.order_flow = order_flow
        
        # Initialize scanners with data pipeline
        if self.momentum_scanner:
            await self.momentum_scanner.initialize(market_stream, data_processor)
        if self.volatility_scanner:
            await self.volatility_scanner.initialize(market_stream, data_processor)
        if self.flow_scanner:
            await self.flow_scanner.initialize(market_stream, data_processor)
        
        logger.info("Unified scanner connected to data pipeline")
    
    async def scan_opportunities(self, 
                               symbol: str, 
                               market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for all opportunity types in parallel"""
        start_time = datetime.now()
        
        try:
            # Run scanners in parallel
            momentum_task = self._scan_momentum(symbol, market_data)
            volatility_task = self._scan_volatility(symbol, market_data)
            flow_task = self._scan_flow(symbol, market_data)
            
            # Gather results
            momentum_opps, volatility_opps, flow_opps = await asyncio.gather(
                momentum_task, volatility_task, flow_task
            )
            
            # Combine opportunities
            all_opportunities = momentum_opps + volatility_opps + flow_opps
            
            # Filter and prioritize
            filtered_opps = self._filter_opportunities(all_opportunities)
            
            # Update tracking
            self._update_opportunity_tracking(symbol, filtered_opps)
            
            # Update metrics
            scan_time = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Scan completed in {scan_time:.3f}s with {len(filtered_opps)} opportunities")
            
            return filtered_opps
            
        except Exception as e:
            logger.error(f"Error scanning opportunities for {symbol}: {e}")
            return []
    
    async def _scan_momentum(self, 
                           symbol: str, 
                           market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for momentum opportunities"""
        start_time = datetime.now()
        
        try:
            # Return empty list if momentum_scanner is None
            if not self.momentum_scanner:
                return []
                
            # Get microstructure data
            micro_data = self.microstructure.get_metrics(symbol)
            
            # Scan for momentum opportunities
            momentum_opps = await self.momentum_scanner.scan_opportunities(
                symbol, market_data, micro_data
            )
            
            # Convert to OpportunityData
            opportunities = []
            for opp in momentum_opps:
                opportunities.append(OpportunityData(
                    id=f"MOM_{symbol}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    type='momentum',
                    direction=opp.get('direction', 'buy'),
                    confidence=opp.get('confidence', 0.5),
                    expected_return=opp.get('expected_return', 0.01),
                    risk_score=opp.get('risk_score', 0.5),
                    timeframe=opp.get('timeframe', '5m'),
                    entry_price=opp.get('entry_price', market_data.get('price', 0)),
                    stop_loss=opp.get('stop_loss', 0),
                    take_profit=opp.get('take_profit', 0),
                    metadata=opp
                ))
            
            # Update metrics
            scan_time = (datetime.now() - start_time).total_seconds()
            self.scan_times['momentum'].append(scan_time)
            if len(self.scan_times['momentum']) > 1000:
                self.scan_times['momentum'] = self.scan_times['momentum'][-1000:]
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning momentum opportunities: {e}")
            return []
    
    async def _scan_volatility(self, 
                             symbol: str, 
                             market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for volatility opportunities"""
        start_time = datetime.now()
        
        try:
            # Return empty list if volatility_scanner is None
            if not self.volatility_scanner:
                return []
                
            # Get order flow data
            flow_data = self.order_flow.get_order_flow_stats(symbol)
            
            # Scan for volatility opportunities
            volatility_opps = await self.volatility_scanner.scan_opportunities(
                symbol, market_data, flow_data
            )
            
            # Convert to OpportunityData
            opportunities = []
            for opp in volatility_opps:
                opportunities.append(OpportunityData(
                    id=f"VOL_{symbol}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    type='volatility',
                    direction=opp.get('direction', 'buy'),
                    confidence=opp.get('confidence', 0.5),
                    expected_return=opp.get('expected_return', 0.01),
                    risk_score=opp.get('risk_score', 0.5),
                    timeframe=opp.get('timeframe', '5m'),
                    entry_price=opp.get('entry_price', market_data.get('price', 0)),
                    stop_loss=opp.get('stop_loss', 0),
                    take_profit=opp.get('take_profit', 0),
                    metadata=opp
                ))
            
            # Update metrics
            scan_time = (datetime.now() - start_time).total_seconds()
            self.scan_times['volatility'].append(scan_time)
            if len(self.scan_times['volatility']) > 1000:
                self.scan_times['volatility'] = self.scan_times['volatility'][-1000:]
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning volatility opportunities: {e}")
            return []
    
    async def _scan_flow(self, 
                       symbol: str, 
                       market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan for flow-based opportunities"""
        start_time = datetime.now()
        
        try:
            # Return empty list if flow_scanner is None
            if not self.flow_scanner:
                return []
                
            # Get microstructure and order flow data
            micro_data = self.microstructure.get_metrics(symbol)
            flow_data = self.order_flow.get_order_flow_stats(symbol)
            
            # Scan for flow opportunities
            flow_opps = await self.flow_scanner.scan_opportunities(
                symbol, market_data, micro_data, flow_data
            )
            
            # Convert to OpportunityData
            opportunities = []
            for opp in flow_opps:
                opportunities.append(OpportunityData(
                    id=f"FLOW_{symbol}_{datetime.now().timestamp()}",
                    timestamp=datetime.now(),
                    symbol=symbol,
                    type='flow',
                    direction=opp.get('direction', 'buy'),
                    confidence=opp.get('confidence', 0.5),
                    expected_return=opp.get('expected_return', 0.01),
                    risk_score=opp.get('risk_score', 0.5),
                    timeframe=opp.get('timeframe', '5m'),
                    entry_price=opp.get('entry_price', market_data.get('price', 0)),
                    stop_loss=opp.get('stop_loss', 0),
                    take_profit=opp.get('take_profit', 0),
                    metadata=opp
                ))
            
            # Update metrics
            scan_time = (datetime.now() - start_time).total_seconds()
            self.scan_times['flow'].append(scan_time)
            if len(self.scan_times['flow']) > 1000:
                self.scan_times['flow'] = self.scan_times['flow'][-1000:]
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error scanning flow opportunities: {e}")
            return []
    
    def _filter_opportunities(self, 
                            opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Filter and prioritize opportunities"""
        if not opportunities:
            return []
        
        # Filter by confidence
        min_confidence = self.config.get('min_opportunity_confidence', 0.7)
        filtered = [opp for opp in opportunities if opp.confidence >= min_confidence]
        
        # Filter by risk score
        max_risk = self.config.get('max_opportunity_risk', 0.7)
        filtered = [opp for opp in filtered if opp.risk_score <= max_risk]
        
        # Sort by expected return / risk (Sharpe-like ratio)
        filtered.sort(
            key=lambda x: x.expected_return / max(x.risk_score, 0.01),
            reverse=True
        )
        
        # Limit number of opportunities
        max_opps = self.config.get('max_opportunities', 5)
        return filtered[:max_opps]
    
    def _update_opportunity_tracking(self, 
                                   symbol: str, 
                                   opportunities: List[OpportunityData]):
        """Update opportunity tracking"""
        # Initialize tracking if needed
        if symbol not in self.opportunities:
            self.opportunities[symbol] = {}
        if symbol not in self.opportunity_history:
            self.opportunity_history[symbol] = []
        
        # Update active opportunities
        for opp in opportunities:
            self.opportunities[symbol][opp.id] = opp
            self.opportunity_history[symbol].append(opp)
        
        # Limit history size
        max_history = self.config.get('max_opportunity_history', 1000)
        if len(self.opportunity_history[symbol]) > max_history:
            self.opportunity_history[symbol] = self.opportunity_history[symbol][-max_history:]
    
    def get_active_opportunities(self, symbol: str) -> List[OpportunityData]:
        """Get active opportunities for symbol"""
        if symbol not in self.opportunities:
            return []
        
        return list(self.opportunities[symbol].values())
    
    def get_opportunity_metrics(self) -> Dict[str, Any]:
        """Get opportunity scanning metrics"""
        metrics = {
            'scan_times': {
                'momentum': np.mean(self.scan_times['momentum']) if self.scan_times['momentum'] else 0,
                'volatility': np.mean(self.scan_times['volatility']) if self.scan_times['volatility'] else 0,
                'flow': np.mean(self.scan_times['flow']) if self.scan_times['flow'] else 0
            },
            'opportunity_counts': {
                symbol: len(opps) for symbol, opps in self.opportunities.items()
            },
            'opportunity_types': self._count_opportunity_types()
        }
        
        return metrics
    
    def _count_opportunity_types(self) -> Dict[str, int]:
        """Count opportunities by type"""
        type_counts = {'momentum': 0, 'volatility': 0, 'flow': 0}
        
        for symbol_opps in self.opportunities.values():
            for opp in symbol_opps.values():
                if opp.type in type_counts:
                    type_counts[opp.type] += 1
        
        return type_counts
