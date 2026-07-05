"""
Hedge Fund AI Orchestrator
==========================
Master orchestrator for the complete hedge fund AI system.
Coordinates all components into a unified institutional-grade platform.
"""

import logging
import asyncio
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
import uuid

logger = logging.getLogger(__name__)

# Import all hedge fund components
from .fund_management import (
    FundManager, Investor, InvestorType, InvestorClass,
    Subscription, Redemption, FeeStructure, FundMetrics, LockupPeriod
)
from .multi_strategy import (
    MultiStrategyEngine, Strategy, StrategyType, StrategyAllocation,
    StrategyPerformance, StrategyRotator
)
from .portfolio_construction import (
    InstitutionalPortfolioConstructor, FactorModel, FactorExposure,
    RiskBudget, RebalanceEngine, TradingCost
)
from .institutional_risk import (
    InstitutionalRiskManager, VaREngine, StressTestEngine,
    ScenarioAnalysis, LiquidityRisk, CounterpartyRisk, MarginManager
)
from .performance_attribution import (
    PerformanceAttributor, BrinsonAttribution, FactorAttribution,
    RiskAdjustedMetrics, PeerComparison, BenchmarkTracker
)
from .compliance_regulatory import (
    ComplianceEngine, RegulatoryReporter, Form13F, FormPF,
    AMLMonitor, TradeCompliance, InvestmentRestrictions
)
from .prime_broker import (
    PrimeBrokerInterface, MarginCalculator, SecuritiesLending,
    CashManagement, Custody
)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class FundState(Enum):
    """Fund operational state"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    TRADING = "trading"
    REBALANCING = "rebalancing"
    RISK_OFF = "risk_off"
    EMERGENCY = "emergency"
    CLOSED = "closed"


class TradingSession(Enum):
    """Trading session"""
    PRE_MARKET = "pre_market"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"


@dataclass
class FundConfig:
    """Hedge fund configuration"""
    fund_name: str = "AlphaAlgo Hedge Fund"
    fund_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    base_currency: str = "USD"
    initial_capital: float = 100_000_000  # $100M
    
    # Strategy allocation
    strategy_allocation: Dict[str, float] = field(default_factory=dict)
    
    # Risk limits
    max_gross_exposure: float = 2.0  # 200%
    max_net_exposure: float = 0.5  # 50%
    max_single_position: float = 0.05  # 5%
    max_sector_exposure: float = 0.25  # 25%
    max_drawdown: float = 0.15  # 15%
    var_limit_95: float = 0.02  # 2%
    
    # Fee structure
    management_fee: float = 0.02  # 2%
    performance_fee: float = 0.20  # 20%
    hurdle_rate: float = 0.05  # 5%
    
    # Operational
    trading_hours: Dict[str, str] = field(default_factory=lambda: {
        'start': '09:30', 'end': '16:00', 'timezone': 'US/Eastern'
    })
    rebalance_frequency: str = "weekly"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fund_name': self.fund_name,
            'fund_id': self.fund_id,
            'base_currency': self.base_currency,
            'initial_capital': self.initial_capital,
            'risk_limits': {
                'max_gross_exposure': self.max_gross_exposure,
                'max_net_exposure': self.max_net_exposure,
                'max_single_position': self.max_single_position,
                'max_sector_exposure': self.max_sector_exposure,
                'max_drawdown': self.max_drawdown,
                'var_limit_95': self.var_limit_95
            },
            'fees': {
                'management': self.management_fee,
                'performance': self.performance_fee,
                'hurdle': self.hurdle_rate
            }
        }


class HedgeFundOrchestrator:
    """
    Master Hedge Fund AI Orchestrator
    
    Coordinates all hedge fund operations:
    - Fund management and investor relations
    - Multi-strategy trading
    - Portfolio construction and optimization
    - Institutional risk management
    - Performance attribution
    - Compliance and regulatory
    - Prime broker integration
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = FundConfig(**(config or {}))
        
        # Initialize all components
        self._initialize_components()
        
        # Fund state
        self.state = FundState.INITIALIZING
        self.session = TradingSession.CLOSED
        
        # Positions and portfolio
        self.positions: Dict[str, Dict[str, Any]] = {}
        self.portfolio_value = self.config.initial_capital
        self.cash = self.config.initial_capital
        
        # Performance tracking
        self.daily_returns: List[float] = []
        self.nav_history: List[Dict[str, Any]] = []
        
        # Trading state
        self.pending_orders: List[Dict[str, Any]] = []
        self.executed_trades: List[Dict[str, Any]] = []
        
        # Background tasks
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        logger.info(f"Hedge Fund Orchestrator initialized: {self.config.fund_name}")
    
    def _initialize_components(self):
        """Initialize all hedge fund components"""
        # Fund Management
        self.fund_manager = FundManager({
            'fund_name': self.config.fund_name,
            'fund_id': self.config.fund_id,
            'initial_nav': 1000.0
        })
        
        # Multi-Strategy Engine
        self.strategy_engine = MultiStrategyEngine({
            'total_capital': self.config.initial_capital,
            'max_gross_exposure': self.config.max_gross_exposure,
            'max_net_exposure': self.config.max_net_exposure
        })
        
        # Portfolio Construction
        self.portfolio_constructor = InstitutionalPortfolioConstructor({
            'max_position': self.config.max_single_position,
            'max_sector': self.config.max_sector_exposure,
            'target_volatility': 0.10
        })
        
        # Risk Management
        self.risk_manager = InstitutionalRiskManager({
            'max_var_95': self.config.var_limit_95,
            'max_drawdown': self.config.max_drawdown,
            'max_leverage': self.config.max_gross_exposure
        })
        
        # Performance Attribution
        self.performance_attributor = PerformanceAttributor({
            'risk_free_rate': 0.05
        })
        
        # Compliance
        self.compliance_engine = ComplianceEngine({
            'fund_name': self.config.fund_name
        })
        
        # Prime Broker
        self.prime_broker = PrimeBrokerInterface({
            'name': 'AlphaAlgo Prime',
            'credit_limit': self.config.initial_capital * 2
        })
        
        logger.info("All hedge fund components initialized")
    
    async def start(self):
        """Start the hedge fund operations"""
        logger.info("Starting Hedge Fund AI...")
        
        self._running = True
        self.state = FundState.ACTIVE
        
        # Create default strategies if none exist
        if not self.strategy_engine.strategies:
            self.strategy_engine.create_default_strategies()
        
        # Allocate capital to strategies
        self.strategy_engine.allocate_capital()
        
        # Start background tasks
        self._tasks = [
            asyncio.create_task(self._risk_monitoring_loop()),
            asyncio.create_task(self._rebalancing_loop()),
            asyncio.create_task(self._compliance_loop()),
            asyncio.create_task(self._nav_calculation_loop())
        ]
        
        logger.info("Hedge Fund AI started successfully")
    
    async def stop(self):
        """Stop the hedge fund operations"""
        logger.info("Stopping Hedge Fund AI...")
        
        self._running = False
        
        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
        
        self.state = FundState.CLOSED
        logger.info("Hedge Fund AI stopped")
    
    async def _risk_monitoring_loop(self):
        """Continuous risk monitoring"""
        while self._running:
            try:
                # Run risk assessment
                risk_assessment = self.risk_manager.run_full_risk_assessment(
                    self.positions,
                    self.portfolio_value,
                    self._calculate_portfolio_volatility()
                )
                
                # Check for risk breaches
                if risk_assessment['overall_risk_level'].value in ['high', 'critical']:
                    await self._handle_risk_breach(risk_assessment)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _rebalancing_loop(self):
        """Periodic portfolio rebalancing"""
        while self._running:
            try:
                # Check if rebalancing needed
                if self._should_rebalance():
                    await self._execute_rebalance()
                
                await asyncio.sleep(3600)  # Check every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Rebalancing error: {e}")
                await asyncio.sleep(3600)
    
    async def _compliance_loop(self):
        """Continuous compliance monitoring"""
        while self._running:
            try:
                # Run compliance check
                compliance_result = self.compliance_engine.run_compliance_check(
                    {'positions': self.positions, 'total_value': self.portfolio_value},
                    self.pending_orders
                )
                
                # Handle violations
                if compliance_result['overall_status'].value == 'violation':
                    await self._handle_compliance_violation(compliance_result)
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Compliance monitoring error: {e}")
                await asyncio.sleep(300)
    
    async def _nav_calculation_loop(self):
        """Daily NAV calculation"""
        while self._running:
            try:
                # Calculate NAV
                total_nav, nav_per_share = self.fund_manager.update_nav(
                    self.positions,
                    self.cash
                )
                
                self.portfolio_value = total_nav
                
                # Record daily return
                if len(self.nav_history) > 0:
                    prev_nav = self.nav_history[-1]['nav']
                    daily_return = (total_nav - prev_nav) / prev_nav
                    self.daily_returns.append(daily_return)
                
                self.nav_history.append({
                    'date': date.today().isoformat(),
                    'nav': total_nav,
                    'nav_per_share': nav_per_share
                })
                
                await asyncio.sleep(86400)  # Once per day
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"NAV calculation error: {e}")
                await asyncio.sleep(86400)
    
    def _calculate_portfolio_volatility(self) -> float:
        """Calculate portfolio volatility"""
        if not NUMPY_AVAILABLE or len(self.daily_returns) < 20:
            return 0.15  # Default 15%
        
        return np.std(self.daily_returns) * np.sqrt(252)
    
    def _should_rebalance(self) -> bool:
        """Check if rebalancing is needed"""
        # Check allocation drift
        for strategy in self.strategy_engine.strategies.values():
            if strategy.allocation.needs_rebalance:
                return True
        return False
    
    async def _execute_rebalance(self):
        """Execute portfolio rebalance"""
        logger.info("Executing portfolio rebalance...")
        
        self.state = FundState.REBALANCING
        
        # Get market regime
        market_regime = self._detect_market_regime()
        
        # Rebalance strategies
        rebalance_trades = self.strategy_engine.rebalance(market_regime)
        
        # Generate portfolio trades
        prices = {s: p.get('current_price', 100) for s, p in self.positions.items()}
        portfolio_trades = self.portfolio_constructor.generate_rebalance_trades(
            self.portfolio_value,
            prices
        )
        
        # Execute trades
        for trade in portfolio_trades:
            await self._execute_trade(trade)
        
        self.state = FundState.ACTIVE
        logger.info("Rebalance complete")
    
    def _detect_market_regime(self) -> str:
        """Detect current market regime"""
        if not NUMPY_AVAILABLE or len(self.daily_returns) < 20:
            return 'ranging'
        
        recent_returns = np.array(self.daily_returns[-20:])
        volatility = np.std(recent_returns) * np.sqrt(252)
        trend = np.mean(recent_returns) * 252
        
        if volatility > 0.30:
            return 'volatile'
        elif trend > 0.10:
            return 'trending_up'
        elif trend < -0.10:
            return 'trending_down'
        else:
            return 'ranging'
    
    async def _handle_risk_breach(self, risk_assessment: Dict[str, Any]):
        """Handle risk limit breach"""
        logger.warning(f"Risk breach detected: {risk_assessment['overall_risk_level']}")
        
        self.state = FundState.RISK_OFF
        
        # Reduce exposure
        for alert in risk_assessment['risk_alerts']:
            if alert['severity'] in ['HIGH', 'CRITICAL']:
                # Implement risk reduction
                await self._reduce_risk_exposure()
        
        self.state = FundState.ACTIVE
    
    async def _handle_compliance_violation(self, compliance_result: Dict[str, Any]):
        """Handle compliance violation"""
        logger.warning(f"Compliance violation: {compliance_result['overall_status']}")
        
        # Cancel violating orders
        for check in compliance_result['order_checks']:
            if not check['approved']:
                order = check['order']
                self.pending_orders = [
                    o for o in self.pending_orders
                    if o.get('order_id') != order.get('order_id')
                ]
    
    async def _reduce_risk_exposure(self):
        """Reduce portfolio risk exposure"""
        logger.info("Reducing risk exposure...")
        
        # Close largest positions first
        sorted_positions = sorted(
            self.positions.items(),
            key=lambda x: abs(x[1].get('value', 0)),
            reverse=True
        )
        
        for symbol, pos in sorted_positions[:5]:  # Reduce top 5
            quantity = pos.get('quantity', 0)
            if quantity != 0:
                # Create closing trade
                trade = {
                    'symbol': symbol,
                    'side': 'sell' if quantity > 0 else 'buy',
                    'quantity': abs(quantity) * 0.5,  # Reduce by 50%
                    'reason': 'risk_reduction'
                }
                await self._execute_trade(trade)
    
    async def _execute_trade(self, trade: Dict[str, Any]):
        """Execute a trade"""
        symbol = trade['symbol']
        side = trade['side']
        quantity = trade['quantity']
        
        # Pre-trade compliance check
        approved, warnings, violations = self.compliance_engine.trade_compliance.pre_trade_check(
            trade,
            {'positions': self.positions, 'total_value': self.portfolio_value}
        )
        
        if not approved:
            logger.warning(f"Trade rejected: {violations}")
            return
        
        # Execute via prime broker
        price = self.positions.get(symbol, {}).get('current_price', 100)
        
        if side == 'sell_short':
            result = self.prime_broker.execute_short_sale(symbol, int(quantity), price)
        else:
            result = {'success': True, 'price': price}
        
        if result.get('success'):
            # Update position
            self._update_position(symbol, side, quantity, price)
            
            # Record trade
            self.executed_trades.append({
                'trade_id': str(uuid.uuid4())[:8],
                'timestamp': datetime.now(),
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'value': quantity * price
            })
            
            logger.info(f"Executed: {side} {quantity} {symbol} @ {price}")
    
    def _update_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float
    ):
        """Update position after trade"""
        if symbol not in self.positions:
            self.positions[symbol] = {
                'symbol': symbol,
                'quantity': 0,
                'cost_basis': 0,
                'current_price': price
            }
        
        pos = self.positions[symbol]
        
        if side == 'buy':
            pos['quantity'] += quantity
            pos['cost_basis'] += quantity * price
            self.cash -= quantity * price
        elif side in ['sell', 'sell_short']:
            pos['quantity'] -= quantity
            pos['cost_basis'] -= quantity * price
            self.cash += quantity * price
        
        pos['current_price'] = price
        pos['value'] = pos['quantity'] * price
        
        # Remove empty positions
        if pos['quantity'] == 0:
            del self.positions[symbol]
    
    # ==================== Public API ====================
    
    def add_investor(
        self,
        name: str,
        investor_type: str,
        share_class: str,
        investment_amount: float,
        lockup_period: str = "HARD_1_YEAR"
    ) -> Dict[str, Any]:
        """Add a new investor to the fund"""
        # Screen investor
        is_clear, concerns = self.compliance_engine.screen_investor({
            'name': name,
            'investment_amount': investment_amount
        })
        
        if not is_clear:
            return {'success': False, 'error': 'Investor screening failed', 'concerns': concerns}
        
        # Add investor
        investor = self.fund_manager.add_investor(
            name=name,
            investor_type=InvestorType[investor_type.upper()],
            share_class=InvestorClass[share_class.upper()],
            initial_investment=investment_amount,
            lockup_period=LockupPeriod[lockup_period]
        )
        
        # Update cash
        self.cash += investment_amount
        self.portfolio_value += investment_amount
        
        # Deposit with prime broker
        self.prime_broker.cash_management.deposit(investment_amount, 'USD', f'Subscription: {name}')
        
        return {
            'success': True,
            'investor_id': investor.investor_id,
            'shares': investor.current_shares,
            'nav_per_share': self.fund_manager.current_nav_per_share
        }
    
    def process_redemption(
        self,
        investor_id: str,
        amount: Optional[float] = None,
        full_redemption: bool = False
    ) -> Dict[str, Any]:
        """Process investor redemption"""
        redemption = self.fund_manager.process_redemption(
            investor_id=investor_id,
            amount=amount,
            full_redemption=full_redemption
        )
        
        if redemption:
            # Update cash
            self.cash -= redemption.net_amount
            
            return {
                'success': True,
                'redemption_id': redemption.redemption_id,
                'gross_amount': redemption.gross_amount,
                'fees': redemption.redemption_fee + redemption.performance_fee,
                'net_amount': redemption.net_amount
            }
        
        return {'success': False, 'error': 'Redemption failed'}
    
    def generate_signals(
        self,
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate trading signals from all strategies"""
        # Generate signals from each strategy
        all_signals = self.strategy_engine.generate_signals(market_data)
        
        # Aggregate signals
        aggregated = self.strategy_engine.aggregate_signals(all_signals)
        
        # Filter by conviction
        high_conviction = {
            symbol: data for symbol, data in aggregated.items()
            if data['conviction'] > 0.3
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_signals': len(aggregated),
            'high_conviction': len(high_conviction),
            'signals': high_conviction
        }
    
    def get_fund_metrics(self) -> Dict[str, Any]:
        """Get comprehensive fund metrics"""
        # Fund metrics
        fund_metrics = self.fund_manager.get_fund_metrics()
        
        # Risk metrics
        risk_summary = self.risk_manager.get_risk_summary()
        
        # Strategy summary
        strategy_summary = self.strategy_engine.get_strategy_summary()
        
        # Portfolio exposure
        exposure = self.strategy_engine.get_portfolio_exposure()
        
        # Performance metrics
        if NUMPY_AVAILABLE and len(self.daily_returns) > 0:
            returns_array = np.array(self.daily_returns)
            perf_metrics = self.performance_attributor.calculate_risk_adjusted_metrics(
                returns_array
            )
        else:
            perf_metrics = None
        
        return {
            'fund': fund_metrics.to_dict(),
            'risk': risk_summary,
            'strategies': strategy_summary,
            'exposure': exposure,
            'performance': perf_metrics.to_dict() if perf_metrics else None,
            'state': self.state.value,
            'session': self.session.value
        }
    
    def get_investor_report(self, investor_id: str) -> Dict[str, Any]:
        """Get investor-specific report"""
        return self.fund_manager.get_investor_report(investor_id)
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get compliance status"""
        return self.compliance_engine.get_compliance_summary()
    
    def get_prime_broker_summary(self) -> Dict[str, Any]:
        """Get prime broker account summary"""
        return self.prime_broker.get_account_summary(self.positions)
    
    def generate_regulatory_filings(self) -> Dict[str, Any]:
        """Generate regulatory filings"""
        # Prepare holdings
        holdings = {}
        for symbol, pos in self.positions.items():
            holdings[symbol] = {
                'name': symbol,
                'cusip': '',  # Would need CUSIP lookup
                'value': pos.get('value', 0),
                'shares': pos.get('quantity', 0),
                'asset_class': 'equity'
            }
        
        # Generate 13F
        quarter = f"{date.today().year}-Q{(date.today().month - 1) // 3 + 1}"
        form_13f = self.compliance_engine.regulatory_reporter.generate_form_13f(
            holdings, quarter
        )
        
        # Generate Form PF
        fund_metrics = {
            'aum': self.portfolio_value,
            'gav': self.portfolio_value * 1.5,  # Gross with leverage
            'nav': self.portfolio_value,
            'borrowings': self.portfolio_value * 0.5,
            'investor_count': len(self.fund_manager.investors),
            'strategy': 'Multi-Strategy',
            'geography': 'Global'
        }
        
        risk_metrics = {
            'var_95': 0.02,
            'max_drawdown': 0.15,
            'leverage': 1.5
        }
        
        form_pf = self.compliance_engine.regulatory_reporter.generate_form_pf(
            fund_metrics, risk_metrics, [], quarter
        )
        
        return {
            'form_13f': {
                'period': form_13f.report_period,
                'total_value': form_13f.total_value,
                'num_holdings': len(form_13f.holdings)
            },
            'form_pf': form_pf.to_dict()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall fund status"""
        return {
            'fund_name': self.config.fund_name,
            'fund_id': self.config.fund_id,
            'state': self.state.value,
            'session': self.session.value,
            'aum': self.portfolio_value,
            'cash': self.cash,
            'positions_count': len(self.positions),
            'investors_count': len(self.fund_manager.investors),
            'strategies_count': len(self.strategy_engine.strategies),
            'pending_orders': len(self.pending_orders),
            'executed_trades_today': len([
                t for t in self.executed_trades
                if t['timestamp'].date() == date.today()
            ]),
            'compliance_status': self.compliance_engine.overall_status.value,
            'risk_level': self.risk_manager.current_risk_level.value
        }


# ==================== Quick Start Functions ====================

def create_hedge_fund(config: Optional[Dict[str, Any]] = None) -> HedgeFundOrchestrator:
    """Create a new hedge fund instance"""
    return HedgeFundOrchestrator(config)


async def quick_start(config: Optional[Dict[str, Any]] = None) -> HedgeFundOrchestrator:
    """Quick start a hedge fund"""
    fund = create_hedge_fund(config)
    await fund.start()
    return fund


# Demo function
async def demo():
    """Demo the hedge fund system"""
    print("=" * 60)
    logger.info("ALPHAALGO HEDGE FUND AI - DEMO")
    print("=" * 60)
    
    # Create fund
    fund = create_hedge_fund({
        'fund_name': 'AlphaAlgo Quantitative Fund',
        'initial_capital': 100_000_000
    })
    
    # Add investors
    logger.info("\n1. Adding Investors...")
    
    result = fund.add_investor(
        name="Institutional Investor A",
        investor_type="INSTITUTIONAL",
        share_class="CLASS_B",
        investment_amount=25_000_000
    )
    logger.info(f"   Added: {result}")
    
    result = fund.add_investor(
        name="Family Office B",
        investor_type="FAMILY_OFFICE",
        share_class="CLASS_A",
        investment_amount=10_000_000
    )
    logger.info(f"   Added: {result}")
    
    # Get fund metrics
    logger.info("\n2. Fund Metrics...")
    metrics = fund.get_fund_metrics()
    logger.info(f"   AUM: ${metrics['fund']['total_aum']:,.2f}")
    logger.info(f"   Investors: {metrics['fund']['num_investors']}")
    logger.info(f"   Strategies: {metrics['strategies']['total_strategies']}")
    
    # Generate signals
    logger.info("\n3. Generating Signals...")
    market_data = {
        'prices': {
            'AAPL': {'price': 150, 'returns_20d': 0.05, 'returns_60d': 0.10, 'rsi': 55},
            'GOOGL': {'price': 140, 'returns_20d': 0.03, 'returns_60d': 0.08, 'rsi': 60},
            'MSFT': {'price': 380, 'returns_20d': -0.02, 'returns_60d': 0.05, 'rsi': 45},
            'AMZN': {'price': 175, 'returns_20d': 0.08, 'returns_60d': 0.15, 'rsi': 65}
        }
    }
    signals = fund.generate_signals(market_data)
    logger.info(f"   Total Signals: {signals['total_signals']}")
    logger.info(f"   High Conviction: {signals['high_conviction']}")
    
    # Compliance status
    logger.info("\n4. Compliance Status...")
    compliance = fund.get_compliance_status()
    logger.info(f"   Status: {compliance['overall_status']}")
    logger.info(f"   Restrictions: {compliance['restrictions_count']}")
    
    # Prime broker summary
    logger.info("\n5. Prime Broker Summary...")
    pb_summary = fund.get_prime_broker_summary()
    logger.info(f"   Net Liquidation: ${pb_summary['net_liquidation_value']:,.2f}")
    logger.info(f"   Buying Power: ${pb_summary['buying_power']['standard_buying_power']:,.2f}")
    
    # Fund status
    logger.info("\n6. Fund Status...")
    status = fund.get_status()
    for key, value in status.items():
        logger.info(f"   {key}: {value}")
    
    print("\n" + "=" * 60)
    logger.info("DEMO COMPLETE")
    print("=" * 60)
    
    return fund


if __name__ == "__main__":
    asyncio.run(demo())
