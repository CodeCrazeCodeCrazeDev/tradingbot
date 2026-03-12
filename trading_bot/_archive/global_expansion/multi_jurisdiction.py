"""
Global Expansion and Multi-Jurisdiction Trading
Implements cross-jurisdiction risk modeling, multi-currency support, global market access
"""

import numpy as np
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
import asyncio
from typing import Union
import numpy

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


logger = logging.getLogger(__name__)



class Jurisdiction(Enum):
    """Trading jurisdictions"""
    US = "us"
    UK = "uk"
    EU = "eu"
    ASIA_PACIFIC = "asia_pacific"
    MIDDLE_EAST = "middle_east"
    LATAM = "latam"


class MarketStatus(Enum):
    """Market trading status"""
    PRE_MARKET = "pre_market"
    OPEN = "open"
    CLOSED = "closed"
    HOLIDAY = "holiday"
    HALTED = "halted"


@dataclass
class TradingHours:
    """Trading hours for a market"""
    market: str
    timezone: str
    open_time: time
    close_time: time
    pre_market_start: Optional[time]
    after_hours_end: Optional[time]
    trading_days: Set[int]  # 0=Monday, 6=Sunday


@dataclass
class RegulatoryRequirement:
    """Regulatory requirement for jurisdiction"""
    jurisdiction: Jurisdiction
    requirement_type: str
    description: str
    mandatory: bool
    penalty: str


@dataclass
class CurrencyPair:
    """Currency pair information"""
    base: str
    quote: str
    rate: float
    bid: float
    ask: float
    spread: float
    last_updated: datetime


class MultiJurisdictionRiskModeler:
    """Cross-jurisdiction risk modeling"""
    
    def __init__(self):
        self.jurisdictions: Dict[Jurisdiction, Dict] = {}
        self.regulatory_requirements: Dict[Jurisdiction, List[RegulatoryRequirement]] = {}
        self._initialize_jurisdictions()
        
    def _initialize_jurisdictions(self):
        """Initialize jurisdiction configurations"""
        
        # United States
        self.jurisdictions[Jurisdiction.US] = {
            'regulators': ['SEC', 'CFTC', 'FINRA'],
            'max_leverage': 50,  # Forex
            'pattern_day_trader_rule': True,
            'min_account_equity': 25000,  # PDT rule
            'tax_rate': 0.37,  # Max federal rate
            'reporting_requirements': ['Form 1099', '8949', 'Schedule D'],
            'restrictions': ['wash_sale_rule', 'mark_to_market_election']
        }
        
        # United Kingdom
        self.jurisdictions[Jurisdiction.UK] = {
            'regulators': ['FCA'],
            'max_leverage': 30,  # Retail
            'pattern_day_trader_rule': False,
            'min_account_equity': 0,
            'tax_rate': 0.45,  # Max rate
            'reporting_requirements': ['Self Assessment'],
            'restrictions': ['negative_balance_protection']
        }
        
        # European Union
        self.jurisdictions[Jurisdiction.EU] = {
            'regulators': ['ESMA', 'MiFID II'],
            'max_leverage': 30,  # Retail
            'pattern_day_trader_rule': False,
            'min_account_equity': 0,
            'tax_rate': 0.50,  # Varies by country
            'reporting_requirements': ['MiFID II reporting'],
            'restrictions': ['negative_balance_protection', 'no_bonus_restrictions']
        }
        
        # Asia Pacific
        self.jurisdictions[Jurisdiction.ASIA_PACIFIC] = {
            'regulators': ['ASIC', 'MAS', 'JFSA'],
            'max_leverage': 100,  # Varies
            'pattern_day_trader_rule': False,
            'min_account_equity': 0,
            'tax_rate': 0.30,  # Average
            'reporting_requirements': ['Local tax forms'],
            'restrictions': []
        }
        
    async def assess_jurisdiction_risk(
        self,
        jurisdiction: Jurisdiction,
        trade: Dict,
        account: Dict
    ) -> Dict:
        """Assess risk for trading in specific jurisdiction"""
        
        if jurisdiction not in self.jurisdictions:
            return {'error': 'Unknown jurisdiction'}
        
        config = self.jurisdictions[jurisdiction]
        risks = []
        
        # Check leverage limits
        requested_leverage = trade.get('leverage', 1)
        if requested_leverage > config['max_leverage']:
            risks.append({
                'type': 'leverage_violation',
                'severity': 'high',
                'limit': config['max_leverage'],
                'requested': requested_leverage
            })
        
        # Check PDT rule (US only)
        if config.get('pattern_day_trader_rule'):
            day_trades = account.get('day_trades_this_week', 0)
            equity = account.get('equity', 0)
            
            if day_trades >= 3 and equity < config['min_account_equity']:
                risks.append({
                    'type': 'pdt_violation',
                    'severity': 'critical',
                    'required_equity': config['min_account_equity'],
                    'current_equity': equity
                })
        
        # Check regulatory compliance
        for req in self.regulatory_requirements.get(jurisdiction, []):
            if req.mandatory and not account.get(f'compliant_{req.requirement_type}', False):
                risks.append({
                    'type': 'regulatory_violation',
                    'severity': 'high',
                    'requirement': req.description,
                    'penalty': req.penalty
                })
        
        # Calculate overall risk score
        risk_score = len([r for r in risks if r['severity'] in ['high', 'critical']]) / 10
        
        return {
            'jurisdiction': jurisdiction.value,
            'risks': risks,
            'risk_score': min(risk_score, 1.0),
            'compliant': len(risks) == 0,
            'regulators': config['regulators']
        }
    
    async def optimize_jurisdiction_allocation(
        self,
        capital: float,
        available_jurisdictions: List[Jurisdiction]
    ) -> Dict:
        """Optimize capital allocation across jurisdictions"""
        
        # Score each jurisdiction
        scores = {}
        for jurisdiction in available_jurisdictions:
            if jurisdiction not in self.jurisdictions:
                continue
            
            config = self.jurisdictions[jurisdiction]
            
            # Scoring factors
            leverage_score = config['max_leverage'] / 100  # Higher leverage = higher score
            tax_score = 1 - config['tax_rate']  # Lower tax = higher score
            regulatory_score = 1 - len(config['restrictions']) / 10  # Fewer restrictions = higher score
            
            scores[jurisdiction] = (leverage_score + tax_score + regulatory_score) / 3
        
        # Normalize scores to allocations
        total_score = sum(scores.values())
        allocations = {
            j: (score / total_score) * capital
            for j, score in scores.items()
        }
        
        return {
            'allocations': allocations,
            'scores': scores,
            'total_capital': capital
        }


class MultiCurrencyManager:
    """Multi-currency portfolio management"""
    
    def __init__(self):
        self.currencies: Set[str] = {'USD', 'EUR', 'GBP', 'JPY', 'CHF', 'AUD', 'CAD', 'CNY'}
        self.exchange_rates: Dict[tuple, CurrencyPair] = {}
        self.base_currency: str = 'USD'
        self._initialize_rates()
        
    def _initialize_rates(self):
        """Initialize exchange rates"""
        # Simplified rates (would fetch from API in production)
        rates = {
            ('EUR', 'USD'): 1.10,
            ('GBP', 'USD'): 1.27,
            ('USD', 'JPY'): 150.0,
            ('USD', 'CHF'): 0.88,
            ('AUD', 'USD'): 0.65,
            ('USD', 'CAD'): 1.36,
            ('USD', 'CNY'): 7.25,
        }
        
        for (base, quote), rate in rates.items():
            bid = rate * 0.9995  # 5 pip spread
            ask = rate * 1.0005
            
            self.exchange_rates[(base, quote)] = CurrencyPair(
                base=base,
                quote=quote,
                rate=rate,
                bid=bid,
                ask=ask,
                spread=ask - bid,
                last_updated=datetime.now()
            )
            
            # Add reverse pair
            self.exchange_rates[(quote, base)] = CurrencyPair(
                base=quote,
                quote=base,
                rate=1/rate,
                bid=1/ask,
                ask=1/bid,
                spread=(1/bid) - (1/ask),
                last_updated=datetime.now()
            )
    
    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str
    ) -> float:
        """Convert amount between currencies"""
        
        if from_currency == to_currency:
            return amount
        
        # Direct conversion
        if (from_currency, to_currency) in self.exchange_rates:
            pair = self.exchange_rates[(from_currency, to_currency)]
            return amount * pair.rate
        
        # Conversion through base currency
        if from_currency != self.base_currency:
            amount = self.convert(amount, from_currency, self.base_currency)
            from_currency = self.base_currency
        
        if to_currency != self.base_currency:
            return self.convert(amount, self.base_currency, to_currency)
        
        return amount
    
    async def calculate_portfolio_value(
        self,
        positions: List[Dict],
        target_currency: str = 'USD'
    ) -> Dict:
        """Calculate total portfolio value in target currency"""
        
        total_value = 0
        currency_breakdown = {}
        
        for pos in positions:
            currency = pos.get('currency', 'USD')
            value = pos.get('value', 0)
            
            # Convert to target currency
            converted_value = self.convert(value, currency, target_currency)
            total_value += converted_value
            
            # Track by currency
            if currency not in currency_breakdown:
                currency_breakdown[currency] = 0
            currency_breakdown[currency] += value
        
        return {
            'total_value': total_value,
            'currency': target_currency,
            'breakdown': currency_breakdown,
            'num_currencies': len(currency_breakdown)
        }
    
    async def hedge_currency_risk(
        self,
        exposure: Dict[str, float],
        target_currency: str = 'USD'
    ) -> Dict:
        """Calculate currency hedging requirements"""
        
        hedges = {}
        
        for currency, amount in exposure.items():
            if currency == target_currency:
                continue
            
            # Calculate hedge amount
            hedge_amount = amount * 0.8  # 80% hedge ratio
            
            # Get exchange rate
            if (currency, target_currency) in self.exchange_rates:
                pair = self.exchange_rates[(currency, target_currency)]
                
                hedges[currency] = {
                    'amount': hedge_amount,
                    'pair': f"{currency}/{target_currency}",
                    'rate': pair.rate,
                    'cost': hedge_amount * pair.spread
                }
        
        total_cost = sum(h['cost'] for h in hedges.values())
        
        return {
            'hedges': hedges,
            'total_cost': total_cost,
            'hedge_ratio': 0.8
        }


class GlobalMarketAccessManager:
    """Global market access and trading hours"""
    
    def __init__(self):
        self.markets: Dict[str, TradingHours] = {}
        self._initialize_markets()
        
    def _initialize_markets(self):
        """Initialize global market trading hours"""
        
        # US Markets
        self.markets['NYSE'] = TradingHours(
            market='NYSE',
            timezone='America/New_York',
            open_time=time(9, 30),
            close_time=time(16, 0),
            pre_market_start=time(4, 0),
            after_hours_end=time(20, 0),
            trading_days={0, 1, 2, 3, 4}  # Mon-Fri
        )
        
        # London Stock Exchange
        self.markets['LSE'] = TradingHours(
            market='LSE',
            timezone='Europe/London',
            open_time=time(8, 0),
            close_time=time(16, 30),
            pre_market_start=None,
            after_hours_end=None,
            trading_days={0, 1, 2, 3, 4}
        )
        
        # Tokyo Stock Exchange
        self.markets['TSE'] = TradingHours(
            market='TSE',
            timezone='Asia/Tokyo',
            open_time=time(9, 0),
            close_time=time(15, 0),
            pre_market_start=None,
            after_hours_end=None,
            trading_days={0, 1, 2, 3, 4}
        )
        
        # Hong Kong Stock Exchange
        self.markets['HKEX'] = TradingHours(
            market='HKEX',
            timezone='Asia/Hong_Kong',
            open_time=time(9, 30),
            close_time=time(16, 0),
            pre_market_start=None,
            after_hours_end=None,
            trading_days={0, 1, 2, 3, 4}
        )
        
        # Forex (24/5)
        self.markets['FOREX'] = TradingHours(
            market='FOREX',
            timezone='UTC',
            open_time=time(22, 0),  # Sunday 22:00 UTC
            close_time=time(22, 0),  # Friday 22:00 UTC
            pre_market_start=None,
            after_hours_end=None,
            trading_days={0, 1, 2, 3, 4, 6}  # Sun-Fri
        )
        
        # Crypto (24/7)
        self.markets['CRYPTO'] = TradingHours(
            market='CRYPTO',
            timezone='UTC',
            open_time=time(0, 0),
            close_time=time(23, 59),
            pre_market_start=None,
            after_hours_end=None,
            trading_days={0, 1, 2, 3, 4, 5, 6}  # All days
        )
    
    def get_market_status(
        self,
        market: str,
        current_time: Optional[datetime] = None
    ) -> MarketStatus:
        """Get current market status"""
        
        if market not in self.markets:
            return MarketStatus.CLOSED
        
        if current_time is None:
            current_time = datetime.now()
        
        hours = self.markets[market]
        current_day = current_time.weekday()
        current_time_only = current_time.time()
        
        # Check if trading day
        if current_day not in hours.trading_days:
            return MarketStatus.CLOSED
        
        # Check if within trading hours
        if hours.open_time <= current_time_only <= hours.close_time:
            return MarketStatus.OPEN
        
        # Check pre-market
        if hours.pre_market_start and hours.pre_market_start <= current_time_only < hours.open_time:
            return MarketStatus.PRE_MARKET
        
        return MarketStatus.CLOSED
    
    async def find_open_markets(
        self,
        current_time: Optional[datetime] = None
    ) -> List[str]:
        """Find all currently open markets"""
        
        open_markets = []
        
        for market in self.markets:
            status = self.get_market_status(market, current_time)
            if status == MarketStatus.OPEN:
                open_markets.append(market)
        
        return open_markets
    
    async def calculate_global_trading_window(self) -> Dict:
        """Calculate 24-hour global trading coverage"""
        
        # Simulate 24 hours
        coverage = []
        
        for hour in range(24):
            test_time = datetime.now().replace(hour=hour, minute=0, second=0)
            open_markets = await self.find_open_markets(test_time)
            
            coverage.append({
                'hour': hour,
                'open_markets': open_markets,
                'num_markets': len(open_markets)
            })
        
        # Calculate statistics
        hours_with_coverage = sum(1 for c in coverage if c['num_markets'] > 0)
        avg_markets_open = np.mean([c['num_markets'] for c in coverage])
        
        return {
            'coverage': coverage,
            'hours_with_coverage': hours_with_coverage,
            'coverage_percentage': hours_with_coverage / 24,
            'avg_markets_open': avg_markets_open
        }


class GlobalExpansionOrchestrator:
    """Unified global expansion management"""
    
    def __init__(self):
        self.risk_modeler = MultiJurisdictionRiskModeler()
        self.currency_manager = MultiCurrencyManager()
        self.market_access = GlobalMarketAccessManager()
        
    async def execute_global_trade(
        self,
        trade: Dict,
        account: Dict
    ) -> Dict:
        """Execute trade with global considerations"""
        
        # 1. Determine jurisdiction
        jurisdiction = Jurisdiction(trade.get('jurisdiction', 'us'))
        
        # 2. Assess jurisdiction risk
        jurisdiction_risk = await self.risk_modeler.assess_jurisdiction_risk(
            jurisdiction,
            trade,
            account
        )
        
        if not jurisdiction_risk['compliant']:
            return {
                'status': 'rejected',
                'reason': 'jurisdiction_compliance',
                'risks': jurisdiction_risk['risks']
            }
        
        # 3. Check market status
        market = trade.get('market', 'NYSE')
        market_status = self.market_access.get_market_status(market)
        
        if market_status != MarketStatus.OPEN:
            return {
                'status': 'rejected',
                'reason': 'market_closed',
                'market_status': market_status.value
            }
        
        # 4. Handle currency conversion
        trade_currency = trade.get('currency', 'USD')
        account_currency = account.get('currency', 'USD')
        
        if trade_currency != account_currency:
            converted_amount = self.currency_manager.convert(
                trade.get('amount', 0),
                trade_currency,
                account_currency
            )
            trade['converted_amount'] = converted_amount
        
        # 5. Calculate hedging requirements
        if trade.get('hedge_currency', False):
            hedge = await self.currency_manager.hedge_currency_risk(
                {trade_currency: trade.get('amount', 0)},
                account_currency
            )
            trade['hedge'] = hedge
        
        return {
            'status': 'approved',
            'jurisdiction_risk': jurisdiction_risk,
            'market_status': market_status.value,
            'trade': trade,
            'timestamp': datetime.now()
        }
    
    async def get_global_status(self) -> Dict:
        """Get comprehensive global trading status"""
        
        # Open markets
        open_markets = await self.market_access.find_open_markets()
        
        # Trading window coverage
        coverage = await self.market_access.calculate_global_trading_window()
        
        # Supported jurisdictions
        jurisdictions = list(self.risk_modeler.jurisdictions.keys())
        
        # Supported currencies
        currencies = list(self.currency_manager.currencies)
        
        return {
            'open_markets': open_markets,
            'coverage': coverage,
            'jurisdictions': [j.value for j in jurisdictions],
            'currencies': currencies,
            'total_markets': len(self.market_access.markets),
            'timestamp': datetime.now()
        }
