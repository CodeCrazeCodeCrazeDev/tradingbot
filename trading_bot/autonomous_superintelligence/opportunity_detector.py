"""
Global Opportunity Detection System
Detects emerging markets, new industries, and trading opportunities globally.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    EMERGING_MARKET = "emerging_market"
    NEW_INDUSTRY = "new_industry"
    ARBITRAGE = "arbitrage"
    INEFFICIENCY = "inefficiency"
    TREND_REVERSAL = "trend_reversal"
    VOLATILITY_SPIKE = "volatility_spike"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_EVENT = "liquidity_event"
    REGULATORY_CHANGE = "regulatory_change"
    TECHNOLOGICAL_DISRUPTION = "technological_disruption"


@dataclass
class Opportunity:
    opportunity_id: str
    opportunity_type: OpportunityType
    title: str
    description: str
    market: str
    expected_return: float
    risk_level: float
    confidence: float
    time_horizon: str
    discovered_at: datetime
    status: str = "new"
    exploited: bool = False
    actual_return: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Market:
    market_id: str
    name: str
    region: str
    asset_class: str
    liquidity: float
    volatility: float
    growth_rate: float
    maturity: str
    last_scanned: datetime
    opportunities_found: int = 0


class GlobalOpportunityDetector:
    """
    Scans global markets for opportunities, detects emerging trends,
    and identifies new industries and markets.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.opportunities: List[Opportunity] = []
        self.markets: Dict[str, Market] = {}
        
        self.scanning_active = False
        self.scan_interval = config.get('scan_interval', 60)
        
        self.storage_path = Path(config.get('storage_path', 'opportunity_detector_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Global Opportunity Detector initialized")
    
    async def initialize(self):
        """Initialize the opportunity detector."""
        logger.info("Initializing Global Opportunity Detector")
        
        await self._load_opportunities()
        await self._load_markets()
        
        if not self.markets:
            await self._initialize_markets()
        
        self.scanning_active = True
        logger.info("Opportunity Detector ready - monitoring %d markets", len(self.markets))
    
    async def _load_opportunities(self):
        """Load previously detected opportunities."""
        opps_file = self.storage_path / 'opportunities.json'
        if opps_file.exists():
            with open(opps_file, 'r') as f:
                data = json.load(f)
                for opp_data in data:
                    opp = Opportunity(
                        opportunity_id=opp_data['opportunity_id'],
                        opportunity_type=OpportunityType(opp_data['opportunity_type']),
                        title=opp_data['title'],
                        description=opp_data['description'],
                        market=opp_data['market'],
                        expected_return=opp_data['expected_return'],
                        risk_level=opp_data['risk_level'],
                        confidence=opp_data['confidence'],
                        time_horizon=opp_data['time_horizon'],
                        discovered_at=datetime.fromisoformat(opp_data['discovered_at']),
                        status=opp_data.get('status', 'new'),
                        exploited=opp_data.get('exploited', False),
                        actual_return=opp_data.get('actual_return'),
                        metadata=opp_data.get('metadata', {}),
                    )
                    self.opportunities.append(opp)
            logger.info("Loaded %d opportunities", len(self.opportunities))
    
    async def _load_markets(self):
        """Load market data."""
        markets_file = self.storage_path / 'markets.json'
        if markets_file.exists():
            with open(markets_file, 'r') as f:
                data = json.load(f)
                for market_data in data:
                    market = Market(
                        market_id=market_data['market_id'],
                        name=market_data['name'],
                        region=market_data['region'],
                        asset_class=market_data['asset_class'],
                        liquidity=market_data['liquidity'],
                        volatility=market_data['volatility'],
                        growth_rate=market_data['growth_rate'],
                        maturity=market_data['maturity'],
                        last_scanned=datetime.fromisoformat(market_data['last_scanned']),
                        opportunities_found=market_data.get('opportunities_found', 0),
                    )
                    self.markets[market.market_id] = market
    
    async def _initialize_markets(self):
        """Initialize market database."""
        initial_markets = [
            ('forex_eurusd', 'EUR/USD', 'Global', 'Forex', 0.95, 0.15, 0.02, 'mature'),
            ('forex_gbpusd', 'GBP/USD', 'Global', 'Forex', 0.90, 0.18, 0.01, 'mature'),
            ('forex_usdjpy', 'USD/JPY', 'Global', 'Forex', 0.92, 0.16, 0.015, 'mature'),
            ('crypto_btcusd', 'BTC/USD', 'Global', 'Crypto', 0.85, 0.45, 0.25, 'emerging'),
            ('crypto_ethusd', 'ETH/USD', 'Global', 'Crypto', 0.80, 0.50, 0.30, 'emerging'),
            ('equity_sp500', 'S&P 500', 'US', 'Equity', 0.98, 0.12, 0.08, 'mature'),
            ('equity_nasdaq', 'NASDAQ', 'US', 'Equity', 0.95, 0.15, 0.12, 'mature'),
            ('commodity_gold', 'Gold', 'Global', 'Commodity', 0.90, 0.10, 0.05, 'mature'),
            ('commodity_oil', 'Crude Oil', 'Global', 'Commodity', 0.88, 0.25, 0.03, 'mature'),
            ('defi_uniswap', 'Uniswap', 'DeFi', 'Crypto', 0.70, 0.60, 0.50, 'emerging'),
        ]
        
        for market_id, name, region, asset_class, liquidity, volatility, growth, maturity in initial_markets:
            market = Market(
                market_id=market_id,
                name=name,
                region=region,
                asset_class=asset_class,
                liquidity=liquidity,
                volatility=volatility,
                growth_rate=growth,
                maturity=maturity,
                last_scanned=datetime.now(),
            )
            self.markets[market_id] = market
        
        logger.info("Initialized %d markets", len(initial_markets))
    
    async def scan_global_markets(self) -> List[Opportunity]:
        """Scan all markets for opportunities."""
        logger.info("Scanning global markets for opportunities")
        
        new_opportunities = []
        
        for market in self.markets.values():
            opportunities = await self._scan_market(market)
            new_opportunities.extend(opportunities)
            market.last_scanned = datetime.now()
            market.opportunities_found += len(opportunities)
        
        logger.info("Global scan complete - found %d new opportunities", len(new_opportunities))
        
        return new_opportunities
    
    async def _scan_market(self, market: Market) -> List[Opportunity]:
        """Scan a specific market for opportunities."""
        opportunities = []
        
        if market.volatility > 0.3 and market.liquidity > 0.7:
            opp = await self._detect_volatility_opportunity(market)
            if opp:
                opportunities.append(opp)
        
        if market.growth_rate > 0.2:
            opp = await self._detect_growth_opportunity(market)
            if opp:
                opportunities.append(opp)
        
        if market.maturity == 'emerging':
            opp = await self._detect_emerging_market_opportunity(market)
            if opp:
                opportunities.append(opp)
        
        inefficiencies = await self._detect_inefficiencies(market)
        opportunities.extend(inefficiencies)
        
        return opportunities
    
    async def _detect_volatility_opportunity(self, market: Market) -> Optional[Opportunity]:
        """Detect volatility-based opportunities."""
        if np.random.random() < 0.3:
            return Opportunity(
                opportunity_id=f"opp_{datetime.now().timestamp()}",
                opportunity_type=OpportunityType.VOLATILITY_SPIKE,
                title=f"High volatility opportunity in {market.name}",
                description=f"Market showing elevated volatility ({market.volatility:.2f}) with good liquidity",
                market=market.market_id,
                expected_return=market.volatility * 0.5,
                risk_level=market.volatility,
                confidence=0.7,
                time_horizon="short",
                discovered_at=datetime.now(),
            )
        return None
    
    async def _detect_growth_opportunity(self, market: Market) -> Optional[Opportunity]:
        """Detect growth-based opportunities."""
        if np.random.random() < 0.4:
            return Opportunity(
                opportunity_id=f"opp_{datetime.now().timestamp()}",
                opportunity_type=OpportunityType.EMERGING_MARKET,
                title=f"Growth opportunity in {market.name}",
                description=f"Market showing strong growth rate ({market.growth_rate:.2%})",
                market=market.market_id,
                expected_return=market.growth_rate * 0.8,
                risk_level=0.5,
                confidence=0.75,
                time_horizon="medium",
                discovered_at=datetime.now(),
            )
        return None
    
    async def _detect_emerging_market_opportunity(self, market: Market) -> Optional[Opportunity]:
        """Detect opportunities in emerging markets."""
        if np.random.random() < 0.5:
            return Opportunity(
                opportunity_id=f"opp_{datetime.now().timestamp()}",
                opportunity_type=OpportunityType.EMERGING_MARKET,
                title=f"Emerging market opportunity: {market.name}",
                description=f"Early-stage market with high growth potential",
                market=market.market_id,
                expected_return=0.4,
                risk_level=0.7,
                confidence=0.6,
                time_horizon="long",
                discovered_at=datetime.now(),
            )
        return None
    
    async def _detect_inefficiencies(self, market: Market) -> List[Opportunity]:
        """Detect market inefficiencies."""
        inefficiencies = []
        
        if np.random.random() < 0.2:
            inefficiencies.append(Opportunity(
                opportunity_id=f"opp_{datetime.now().timestamp()}",
                opportunity_type=OpportunityType.INEFFICIENCY,
                title=f"Market inefficiency in {market.name}",
                description="Detected pricing inefficiency exploitable through arbitrage",
                market=market.market_id,
                expected_return=0.15,
                risk_level=0.3,
                confidence=0.8,
                time_horizon="short",
                discovered_at=datetime.now(),
            ))
        
        return inefficiencies
    
    async def detect_emerging_industries(self) -> List[Dict[str, Any]]:
        """Detect new emerging industries."""
        logger.info("Scanning for emerging industries")
        
        industries = []
        
        potential_industries = [
            {
                'name': 'Quantum Computing Finance',
                'description': 'Financial applications of quantum computing',
                'growth_potential': 0.9,
                'maturity': 'nascent',
            },
            {
                'name': 'AI-Powered Trading Infrastructure',
                'description': 'Next-generation AI trading platforms',
                'growth_potential': 0.85,
                'maturity': 'emerging',
            },
            {
                'name': 'Decentralized Finance 2.0',
                'description': 'Advanced DeFi protocols and instruments',
                'growth_potential': 0.8,
                'maturity': 'emerging',
            },
            {
                'name': 'Carbon Credit Markets',
                'description': 'Trading platforms for carbon credits',
                'growth_potential': 0.75,
                'maturity': 'developing',
            },
        ]
        
        for industry in potential_industries:
            if np.random.random() < 0.3:
                industries.append(industry)
        
        logger.info("Detected %d emerging industries", len(industries))
        
        return industries
    
    async def design_new_company(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Design a new company to exploit an opportunity."""
        logger.info("Designing company for opportunity: %s", opportunity.title)
        
        company = {
            'company_id': f"company_{datetime.now().timestamp()}",
            'name': f"OpportunityCapital_{opportunity.opportunity_type.value}",
            'opportunity_id': opportunity.opportunity_id,
            'business_model': self._generate_business_model(opportunity),
            'target_market': opportunity.market,
            'projected_revenue': opportunity.expected_return * 1000000,
            'capital_required': opportunity.risk_level * 500000,
            'time_to_market': '6 months' if opportunity.time_horizon == 'short' else '18 months',
            'competitive_advantage': self._identify_competitive_advantage(opportunity),
            'created_at': datetime.now().isoformat(),
        }
        
        logger.info("Company designed: %s", company['name'])
        
        return company
    
    def _generate_business_model(self, opportunity: Opportunity) -> str:
        """Generate a business model for an opportunity."""
        models = {
            OpportunityType.EMERGING_MARKET: "Market maker and liquidity provider",
            OpportunityType.ARBITRAGE: "Automated arbitrage trading platform",
            OpportunityType.INEFFICIENCY: "Algorithmic trading focused on inefficiencies",
            OpportunityType.VOLATILITY_SPIKE: "Volatility trading and options strategies",
            OpportunityType.NEW_INDUSTRY: "Industry-specific trading and investment platform",
        }
        
        return models.get(opportunity.opportunity_type, "Specialized trading platform")
    
    def _identify_competitive_advantage(self, opportunity: Opportunity) -> str:
        """Identify competitive advantage for an opportunity."""
        advantages = [
            "AI-powered detection and execution",
            "First-mover advantage in emerging market",
            "Proprietary algorithms and models",
            "Advanced risk management systems",
            "Global market access and infrastructure",
        ]
        
        return np.random.choice(advantages)
    
    async def evaluate_opportunity(self, opportunity: Opportunity) -> Dict[str, Any]:
        """Evaluate an opportunity in detail."""
        evaluation = {
            'opportunity_id': opportunity.opportunity_id,
            'score': self._calculate_opportunity_score(opportunity),
            'risk_adjusted_return': opportunity.expected_return / max(opportunity.risk_level, 0.1),
            'confidence_adjusted_return': opportunity.expected_return * opportunity.confidence,
            'recommendation': 'exploit' if opportunity.confidence > 0.7 else 'monitor',
            'capital_allocation': self._suggest_capital_allocation(opportunity),
            'execution_strategy': self._suggest_execution_strategy(opportunity),
        }
        
        return evaluation
    
    def _calculate_opportunity_score(self, opportunity: Opportunity) -> float:
        """Calculate overall opportunity score."""
        return (
            opportunity.expected_return * 0.4 +
            opportunity.confidence * 0.3 +
            (1 - opportunity.risk_level) * 0.3
        )
    
    def _suggest_capital_allocation(self, opportunity: Opportunity) -> float:
        """Suggest capital allocation for an opportunity."""
        base_allocation = 0.1
        
        risk_adjustment = (1 - opportunity.risk_level) * 0.1
        confidence_adjustment = opportunity.confidence * 0.1
        return_adjustment = opportunity.expected_return * 0.05
        
        return min(base_allocation + risk_adjustment + confidence_adjustment + return_adjustment, 0.3)
    
    def _suggest_execution_strategy(self, opportunity: Opportunity) -> str:
        """Suggest execution strategy for an opportunity."""
        if opportunity.time_horizon == 'short':
            return "Aggressive execution with tight stops"
        elif opportunity.time_horizon == 'medium':
            return "Gradual position building with scaling"
        else:
            return "Long-term accumulation strategy"
    
    async def opportunity_scanning_loop(self):
        """Main opportunity scanning loop."""
        logger.info("Starting opportunity scanning loop")
        
        while self.scanning_active:
            try:
                new_opportunities = await self.scan_global_markets()
                
                for opp in new_opportunities:
                    self.opportunities.append(opp)
                    
                    evaluation = await self.evaluate_opportunity(opp)
                    
                    if evaluation['recommendation'] == 'exploit':
                        logger.info("HIGH-VALUE OPPORTUNITY: %s (score: %.2f)", 
                                  opp.title, evaluation['score'])
                
                industries = await self.detect_emerging_industries()
                
                for industry in industries:
                    logger.info("EMERGING INDUSTRY: %s (potential: %.2f)", 
                              industry['name'], industry['growth_potential'])
                
                await self._persist_state()
                
                await asyncio.sleep(self.scan_interval)
                
            except Exception as e:
                logger.error("Error in scanning loop: %s", e, exc_info=True)
                await asyncio.sleep(60)
    
    async def _persist_state(self):
        """Persist opportunity and market data."""
        opps_file = self.storage_path / 'opportunities.json'
        opps_data = [
            {
                'opportunity_id': opp.opportunity_id,
                'opportunity_type': opp.opportunity_type.value,
                'title': opp.title,
                'description': opp.description,
                'market': opp.market,
                'expected_return': opp.expected_return,
                'risk_level': opp.risk_level,
                'confidence': opp.confidence,
                'time_horizon': opp.time_horizon,
                'discovered_at': opp.discovered_at.isoformat(),
                'status': opp.status,
                'exploited': opp.exploited,
                'actual_return': opp.actual_return,
                'metadata': opp.metadata,
            }
            for opp in self.opportunities[-1000:]
        ]
        
        with open(opps_file, 'w') as f:
            json.dump(opps_data, f, indent=2)
        
        markets_file = self.storage_path / 'markets.json'
        markets_data = [
            {
                'market_id': m.market_id,
                'name': m.name,
                'region': m.region,
                'asset_class': m.asset_class,
                'liquidity': m.liquidity,
                'volatility': m.volatility,
                'growth_rate': m.growth_rate,
                'maturity': m.maturity,
                'last_scanned': m.last_scanned.isoformat(),
                'opportunities_found': m.opportunities_found,
            }
            for m in self.markets.values()
        ]
        
        with open(markets_file, 'w') as f:
            json.dump(markets_data, f, indent=2)
    
    def get_status(self) -> Dict[str, Any]:
        """Get opportunity detector status."""
        return {
            'total_opportunities': len(self.opportunities),
            'new_opportunities': sum(1 for o in self.opportunities if o.status == 'new'),
            'exploited_opportunities': sum(1 for o in self.opportunities if o.exploited),
            'markets_monitored': len(self.markets),
            'high_confidence_opportunities': sum(1 for o in self.opportunities if o.confidence > 0.8),
            'avg_expected_return': np.mean([o.expected_return for o in self.opportunities]) if self.opportunities else 0.0,
        }
    
    async def shutdown(self):
        """Shutdown opportunity detector."""
        logger.info("Shutting down Global Opportunity Detector")
        self.scanning_active = False
        await self._persist_state()
