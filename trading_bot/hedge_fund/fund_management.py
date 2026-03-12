"""
Fund Management Core
====================
Complete hedge fund management including:
- Investor management (subscriptions, redemptions, capital calls)
- NAV calculation (daily, weekly, monthly)
- Fee structures (management fees, performance fees, hurdle rates)
- High water mark tracking
- Side pockets for illiquid investments
- Multi-class share structure
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
from decimal import Decimal, ROUND_HALF_UP
import json
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class InvestorClass(Enum):
    """Investor share classes with different fee structures"""
    CLASS_A = "class_a"  # Founders class - lowest fees
    CLASS_B = "class_b"  # Institutional - standard fees
    CLASS_C = "class_c"  # High net worth - higher fees
    CLASS_D = "class_d"  # Retail qualified - highest fees
    SEED = "seed"  # Seed investors - special terms


class InvestorType(Enum):
    """Types of investors"""
    INSTITUTIONAL = "institutional"  # Pension funds, endowments
    FAMILY_OFFICE = "family_office"
    HIGH_NET_WORTH = "high_net_worth"
    FUND_OF_FUNDS = "fund_of_funds"
    SOVEREIGN_WEALTH = "sovereign_wealth"
    SEED = "seed"
    INTERNAL = "internal"  # GP capital


class LockupPeriod(Enum):
    """Lockup periods for investments"""
    NONE = 0
    SOFT_90_DAYS = 90
    HARD_1_YEAR = 365
    HARD_2_YEARS = 730
    HARD_3_YEARS = 1095


class RedemptionFrequency(Enum):
    """How often investors can redeem"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


@dataclass
class FeeStructure:
    """Fee structure for a share class"""
    management_fee: float = 0.02  # 2% annual
    performance_fee: float = 0.20  # 20% of profits
    hurdle_rate: float = 0.0  # Minimum return before perf fee
    hurdle_type: str = "hard"  # "hard" or "soft"
    high_water_mark: bool = True
    crystallization_frequency: str = "annual"  # When perf fees are locked in
    redemption_fee: float = 0.0  # Early redemption penalty
    admin_fee: float = 0.001  # 0.1% admin/custody
    
    def calculate_management_fee(self, nav: float, days: int = 365) -> float:
        """Calculate management fee for period"""
        daily_rate = self.management_fee / 365
        return nav * daily_rate * days
    
    def calculate_performance_fee(
        self,
        current_nav: float,
        high_water_mark: float,
        hurdle_nav: float
    ) -> float:
        """Calculate performance fee with HWM and hurdle"""
        if current_nav <= high_water_mark:
            return 0.0
        
        profit = current_nav - high_water_mark
        
        if self.hurdle_rate > 0:
            hurdle_amount = hurdle_nav * self.hurdle_rate
            if self.hurdle_type == "hard":
                # Only pay on profits above hurdle
                profit = max(0, profit - hurdle_amount)
            # Soft hurdle: pay on all profits if above hurdle
        
        return profit * self.performance_fee


@dataclass
class HighWaterMark:
    """Track high water mark for performance fees"""
    investor_id: str
    hwm_value: float
    hwm_date: date
    last_crystallization: date
    history: List[Tuple[date, float]] = field(default_factory=list)
    
    def update(self, new_nav: float, as_of_date: date) -> bool:
        """Update HWM if new NAV is higher"""
        if new_nav > self.hwm_value:
            self.history.append((self.hwm_date, self.hwm_value))
            self.hwm_value = new_nav
            self.hwm_date = as_of_date
            return True
        return False


@dataclass
class Investor:
    """Investor in the fund"""
    investor_id: str
    name: str
    investor_type: InvestorType
    share_class: InvestorClass
    initial_investment: float
    investment_date: date
    current_shares: float
    current_nav: float
    high_water_mark: HighWaterMark
    lockup_period: LockupPeriod
    lockup_end_date: Optional[date]
    redemption_frequency: RedemptionFrequency
    notice_period_days: int = 45
    side_pocket_allocation: float = 0.0
    is_accredited: bool = True
    is_qualified_purchaser: bool = True
    kyc_verified: bool = True
    aml_cleared: bool = True
    tax_id: str = ""
    country: str = "US"
    contact_email: str = ""
    
    @property
    def is_locked(self) -> bool:
        """Check if investor is still in lockup"""
        if self.lockup_end_date is None:
            return False
        return date.today() < self.lockup_end_date
    
    @property
    def total_return(self) -> float:
        """Calculate total return since investment"""
        if self.initial_investment == 0:
            return 0.0
        return (self.current_nav - self.initial_investment) / self.initial_investment
    
    @property
    def days_invested(self) -> int:
        """Days since initial investment"""
        return (date.today() - self.investment_date).days
    
    def can_redeem(self, amount: float) -> Tuple[bool, str]:
        """Check if investor can redeem"""
        if self.is_locked:
            return False, f"Investor locked until {self.lockup_end_date}"
        
        if amount > self.current_nav - self.side_pocket_allocation:
            return False, "Redemption exceeds available balance (excluding side pocket)"
        
        return True, "Redemption allowed"


@dataclass
class Subscription:
    """Subscription (investment) into the fund"""
    subscription_id: str
    investor_id: str
    amount: float
    subscription_date: date
    effective_date: date
    nav_per_share: float
    shares_issued: float
    share_class: InvestorClass
    status: str = "pending"  # pending, approved, settled, rejected
    wire_reference: str = ""
    approved_by: str = ""
    approved_date: Optional[date] = None
    notes: str = ""
    
    @classmethod
    def create(
        cls,
        investor_id: str,
        amount: float,
        nav_per_share: float,
        share_class: InvestorClass,
        subscription_date: Optional[date] = None,
        effective_date: Optional[date] = None
    ) -> 'Subscription':
        """Create a new subscription"""
        sub_date = subscription_date or date.today()
        eff_date = effective_date or sub_date
        shares = amount / nav_per_share
        
        return cls(
            subscription_id=str(uuid.uuid4())[:8],
            investor_id=investor_id,
            amount=amount,
            subscription_date=sub_date,
            effective_date=eff_date,
            nav_per_share=nav_per_share,
            shares_issued=shares,
            share_class=share_class
        )


@dataclass
class Redemption:
    """Redemption (withdrawal) from the fund"""
    redemption_id: str
    investor_id: str
    shares_redeemed: float
    redemption_date: date
    effective_date: date
    nav_per_share: float
    gross_amount: float
    redemption_fee: float
    performance_fee: float
    net_amount: float
    status: str = "pending"  # pending, approved, in_process, paid, rejected
    payment_date: Optional[date] = None
    wire_reference: str = ""
    reason: str = ""
    
    @classmethod
    def create(
        cls,
        investor_id: str,
        shares: float,
        nav_per_share: float,
        fee_structure: FeeStructure,
        high_water_mark: float,
        redemption_date: Optional[date] = None
    ) -> 'Redemption':
        """Create a new redemption"""
        red_date = redemption_date or date.today()
        gross = shares * nav_per_share
        
        # Calculate fees
        red_fee = gross * fee_structure.redemption_fee
        perf_fee = fee_structure.calculate_performance_fee(
            nav_per_share, high_water_mark, high_water_mark
        ) * shares
        
        net = gross - red_fee - perf_fee
        
        return cls(
            redemption_id=str(uuid.uuid4())[:8],
            investor_id=investor_id,
            shares_redeemed=shares,
            redemption_date=red_date,
            effective_date=red_date + timedelta(days=3),  # T+3 settlement
            nav_per_share=nav_per_share,
            gross_amount=gross,
            redemption_fee=red_fee,
            performance_fee=perf_fee,
            net_amount=net
        )


@dataclass
class FundMetrics:
    """Fund-level metrics"""
    total_aum: float
    nav_per_share: float
    total_shares: float
    mtd_return: float
    qtd_return: float
    ytd_return: float
    itd_return: float  # Inception to date
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    volatility: float
    beta: float
    alpha: float
    num_investors: int
    gross_exposure: float
    net_exposure: float
    leverage: float
    cash_percentage: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_aum': round(self.total_aum, 2),
            'nav_per_share': round(self.nav_per_share, 4),
            'total_shares': round(self.total_shares, 4),
            'mtd_return': round(self.mtd_return * 100, 2),
            'qtd_return': round(self.qtd_return * 100, 2),
            'ytd_return': round(self.ytd_return * 100, 2),
            'itd_return': round(self.itd_return * 100, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'sortino_ratio': round(self.sortino_ratio, 2),
            'max_drawdown': round(self.max_drawdown * 100, 2),
            'current_drawdown': round(self.current_drawdown * 100, 2),
            'volatility': round(self.volatility * 100, 2),
            'beta': round(self.beta, 2),
            'alpha': round(self.alpha * 100, 2),
            'num_investors': self.num_investors,
            'gross_exposure': round(self.gross_exposure * 100, 2),
            'net_exposure': round(self.net_exposure * 100, 2),
            'leverage': round(self.leverage, 2),
            'cash_percentage': round(self.cash_percentage * 100, 2)
        }


class NAVCalculator:
    """
    Net Asset Value Calculator
    Handles daily NAV calculation with proper accounting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.nav_history: List[Dict[str, Any]] = []
        self.pricing_sources: Dict[str, str] = {}
        
    def calculate_nav(
        self,
        positions: Dict[str, Dict[str, Any]],
        cash: float,
        accrued_fees: float,
        accrued_expenses: float,
        total_shares: float,
        as_of_date: Optional[date] = None
    ) -> Tuple[float, float, Dict[str, Any]]:
        """
        Calculate fund NAV
        
        Returns:
            Tuple of (total_nav, nav_per_share, breakdown)
        """
        as_of = as_of_date or date.today()
        
        # Calculate position values
        long_value = 0.0
        short_value = 0.0
        unrealized_pnl = 0.0
        
        position_values = {}
        for symbol, pos in positions.items():
            quantity = pos.get('quantity', 0)
            price = pos.get('current_price', 0)
            cost_basis = pos.get('cost_basis', 0)
            
            market_value = quantity * price
            pnl = market_value - cost_basis
            
            if quantity > 0:
                long_value += market_value
            else:
                short_value += abs(market_value)
            
            unrealized_pnl += pnl
            position_values[symbol] = {
                'quantity': quantity,
                'price': price,
                'market_value': market_value,
                'cost_basis': cost_basis,
                'unrealized_pnl': pnl
            }
        
        # Calculate gross and net exposure
        gross_exposure = long_value + short_value
        net_exposure = long_value - short_value
        
        # Total assets
        total_assets = long_value + cash
        
        # Total liabilities (short positions + accrued fees/expenses)
        total_liabilities = short_value + accrued_fees + accrued_expenses
        
        # Net Asset Value
        total_nav = total_assets - total_liabilities
        
        # NAV per share
        nav_per_share = total_nav / total_shares if total_shares > 0 else 0
        
        breakdown = {
            'as_of_date': as_of.isoformat(),
            'long_value': round(long_value, 2),
            'short_value': round(short_value, 2),
            'cash': round(cash, 2),
            'gross_exposure': round(gross_exposure, 2),
            'net_exposure': round(net_exposure, 2),
            'total_assets': round(total_assets, 2),
            'total_liabilities': round(total_liabilities, 2),
            'accrued_fees': round(accrued_fees, 2),
            'accrued_expenses': round(accrued_expenses, 2),
            'unrealized_pnl': round(unrealized_pnl, 2),
            'total_nav': round(total_nav, 2),
            'nav_per_share': round(nav_per_share, 4),
            'total_shares': round(total_shares, 4),
            'position_values': position_values
        }
        
        # Store in history
        self.nav_history.append(breakdown)
        
        return total_nav, nav_per_share, breakdown
    
    def calculate_returns(
        self,
        current_nav: float,
        period_start_nav: float
    ) -> float:
        """Calculate return for period"""
        if period_start_nav == 0:
            return 0.0
        return (current_nav - period_start_nav) / period_start_nav
    
    def get_nav_series(self) -> pd.DataFrame:
        """Get NAV history as DataFrame"""
        if not NUMPY_AVAILABLE:
            return None
        
        if not self.nav_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.nav_history)
        df['as_of_date'] = pd.to_datetime(df['as_of_date'])
        df.set_index('as_of_date', inplace=True)
        return df


class FundManager:
    """
    Master Fund Manager
    Handles all fund operations including:
    - Investor management
    - Subscriptions and redemptions
    - NAV calculation
    - Fee accrual and crystallization
    - Reporting
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Fund details
        self.fund_name = config.get('fund_name', 'AlphaAlgo Hedge Fund')
        self.fund_id = config.get('fund_id', str(uuid.uuid4())[:8])
        self.inception_date = config.get('inception_date', date.today())
        self.base_currency = config.get('base_currency', 'USD')
        self.initial_nav = config.get('initial_nav', 1000.0)
        
        # Fee structures by share class
        self.fee_structures: Dict[InvestorClass, FeeStructure] = {
            InvestorClass.CLASS_A: FeeStructure(
                management_fee=0.01, performance_fee=0.10, hurdle_rate=0.05
            ),
            InvestorClass.CLASS_B: FeeStructure(
                management_fee=0.015, performance_fee=0.15, hurdle_rate=0.04
            ),
            InvestorClass.CLASS_C: FeeStructure(
                management_fee=0.02, performance_fee=0.20, hurdle_rate=0.0
            ),
            InvestorClass.CLASS_D: FeeStructure(
                management_fee=0.025, performance_fee=0.25, hurdle_rate=0.0
            ),
            InvestorClass.SEED: FeeStructure(
                management_fee=0.005, performance_fee=0.05, hurdle_rate=0.0
            )
        }
        
        # Investors
        self.investors: Dict[str, Investor] = {}
        
        # Transactions
        self.subscriptions: List[Subscription] = []
        self.redemptions: List[Redemption] = []
        
        # NAV
        self.nav_calculator = NAVCalculator()
        self.current_nav_per_share = self.initial_nav
        self.total_shares = 0.0
        self.total_aum = 0.0
        
        # Accruals
        self.accrued_management_fees = 0.0
        self.accrued_performance_fees = 0.0
        self.accrued_expenses = 0.0
        
        # Side pockets
        self.side_pocket_assets: Dict[str, Dict[str, Any]] = {}
        
        # History
        self.nav_history: List[Dict[str, Any]] = []
        self.fee_history: List[Dict[str, Any]] = []
        
        logger.info(f"Fund Manager initialized: {self.fund_name}")
    
    def add_investor(
        self,
        name: str,
        investor_type: InvestorType,
        share_class: InvestorClass,
        initial_investment: float,
        lockup_period: LockupPeriod = LockupPeriod.HARD_1_YEAR,
        redemption_frequency: RedemptionFrequency = RedemptionFrequency.QUARTERLY
    ) -> Investor:
        """Add a new investor to the fund"""
        investor_id = str(uuid.uuid4())[:8]
        investment_date = date.today()
        
        # Calculate shares
        shares = initial_investment / self.current_nav_per_share
        
        # Calculate lockup end
        lockup_end = None
        if lockup_period != LockupPeriod.NONE:
            lockup_end = investment_date + timedelta(days=lockup_period.value)
        
        # Create high water mark
        hwm = HighWaterMark(
            investor_id=investor_id,
            hwm_value=self.current_nav_per_share,
            hwm_date=investment_date,
            last_crystallization=investment_date
        )
        
        investor = Investor(
            investor_id=investor_id,
            name=name,
            investor_type=investor_type,
            share_class=share_class,
            initial_investment=initial_investment,
            investment_date=investment_date,
            current_shares=shares,
            current_nav=initial_investment,
            high_water_mark=hwm,
            lockup_period=lockup_period,
            lockup_end_date=lockup_end,
            redemption_frequency=redemption_frequency
        )
        
        self.investors[investor_id] = investor
        self.total_shares += shares
        self.total_aum += initial_investment
        
        # Create subscription record
        subscription = Subscription.create(
            investor_id=investor_id,
            amount=initial_investment,
            nav_per_share=self.current_nav_per_share,
            share_class=share_class
        )
        subscription.status = "settled"
        self.subscriptions.append(subscription)
        
        logger.info(f"Added investor {name} with ${initial_investment:,.2f}")
        return investor
    
    def process_subscription(
        self,
        investor_id: str,
        amount: float
    ) -> Optional[Subscription]:
        """Process additional subscription from existing investor"""
        if investor_id not in self.investors:
            logger.error(f"Investor {investor_id} not found")
            return None
        
        investor = self.investors[investor_id]
        
        # Create subscription
        subscription = Subscription.create(
            investor_id=investor_id,
            amount=amount,
            nav_per_share=self.current_nav_per_share,
            share_class=investor.share_class
        )
        
        # Update investor
        investor.current_shares += subscription.shares_issued
        investor.current_nav += amount
        
        # Update fund totals
        self.total_shares += subscription.shares_issued
        self.total_aum += amount
        
        subscription.status = "settled"
        self.subscriptions.append(subscription)
        
        logger.info(f"Processed subscription of ${amount:,.2f} for {investor.name}")
        return subscription
    
    def process_redemption(
        self,
        investor_id: str,
        shares: Optional[float] = None,
        amount: Optional[float] = None,
        full_redemption: bool = False
    ) -> Optional[Redemption]:
        """Process redemption request"""
        if investor_id not in self.investors:
            logger.error(f"Investor {investor_id} not found")
            return None
        
        investor = self.investors[investor_id]
        
        # Check if can redeem
        can_redeem, reason = investor.can_redeem(
            investor.current_nav if full_redemption else (amount or 0)
        )
        if not can_redeem:
            logger.warning(f"Redemption denied: {reason}")
            return None
        
        # Determine shares to redeem
        if full_redemption:
            shares_to_redeem = investor.current_shares
        elif shares:
            shares_to_redeem = shares
        elif amount:
            shares_to_redeem = amount / self.current_nav_per_share
        else:
            logger.error("Must specify shares, amount, or full_redemption")
            return None
        
        # Get fee structure
        fee_structure = self.fee_structures[investor.share_class]
        
        # Create redemption
        redemption = Redemption.create(
            investor_id=investor_id,
            shares=shares_to_redeem,
            nav_per_share=self.current_nav_per_share,
            fee_structure=fee_structure,
            high_water_mark=investor.high_water_mark.hwm_value
        )
        
        # Update investor
        investor.current_shares -= shares_to_redeem
        investor.current_nav = investor.current_shares * self.current_nav_per_share
        
        # Update fund totals
        self.total_shares -= shares_to_redeem
        self.total_aum -= redemption.gross_amount
        
        redemption.status = "approved"
        self.redemptions.append(redemption)
        
        # Remove investor if full redemption
        if full_redemption or investor.current_shares <= 0:
            del self.investors[investor_id]
            logger.info(f"Investor {investor.name} fully redeemed")
        
        logger.info(f"Processed redemption of {shares_to_redeem:.4f} shares for {investor.name}")
        return redemption
    
    def update_nav(
        self,
        positions: Dict[str, Dict[str, Any]],
        cash: float
    ) -> Tuple[float, float]:
        """Update fund NAV based on current positions"""
        # Calculate accrued fees
        self._accrue_fees()
        
        # Calculate NAV
        total_nav, nav_per_share, breakdown = self.nav_calculator.calculate_nav(
            positions=positions,
            cash=cash,
            accrued_fees=self.accrued_management_fees + self.accrued_performance_fees,
            accrued_expenses=self.accrued_expenses,
            total_shares=self.total_shares
        )
        
        self.current_nav_per_share = nav_per_share
        self.total_aum = total_nav
        
        # Update investor NAVs and HWMs
        for investor in self.investors.values():
            investor.current_nav = investor.current_shares * nav_per_share
            investor.high_water_mark.update(nav_per_share, date.today())
        
        # Store history
        self.nav_history.append({
            'date': date.today().isoformat(),
            'nav_per_share': nav_per_share,
            'total_aum': total_nav,
            'total_shares': self.total_shares
        })
        
        return total_nav, nav_per_share
    
    def _accrue_fees(self):
        """Accrue management and performance fees"""
        # Daily management fee accrual
        for investor in self.investors.values():
            fee_structure = self.fee_structures[investor.share_class]
            daily_mgmt_fee = fee_structure.calculate_management_fee(
                investor.current_nav, days=1
            )
            self.accrued_management_fees += daily_mgmt_fee
    
    def crystallize_fees(self) -> Dict[str, float]:
        """Crystallize performance fees (typically annual)"""
        total_perf_fees = 0.0
        
        for investor in self.investors.values():
            fee_structure = self.fee_structures[investor.share_class]
            
            # Calculate performance fee
            perf_fee = fee_structure.calculate_performance_fee(
                self.current_nav_per_share,
                investor.high_water_mark.hwm_value,
                investor.high_water_mark.hwm_value
            ) * investor.current_shares
            
            if perf_fee > 0:
                total_perf_fees += perf_fee
                
                # Update HWM
                investor.high_water_mark.update(
                    self.current_nav_per_share, date.today()
                )
                investor.high_water_mark.last_crystallization = date.today()
        
        # Reset accrued performance fees
        crystallized = {
            'management_fees': self.accrued_management_fees,
            'performance_fees': total_perf_fees,
            'total': self.accrued_management_fees + total_perf_fees,
            'date': date.today().isoformat()
        }
        
        self.fee_history.append(crystallized)
        self.accrued_management_fees = 0.0
        self.accrued_performance_fees = 0.0
        
        logger.info(f"Crystallized fees: ${crystallized['total']:,.2f}")
        return crystallized
    
    def get_fund_metrics(self) -> FundMetrics:
        """Get comprehensive fund metrics"""
        # Calculate returns
        if len(self.nav_history) > 0:
            nav_series = [h['nav_per_share'] for h in self.nav_history]
            
            # MTD
            mtd_start = self._get_period_start_nav('mtd')
            mtd_return = (self.current_nav_per_share - mtd_start) / mtd_start if mtd_start else 0
            
            # QTD
            qtd_start = self._get_period_start_nav('qtd')
            qtd_return = (self.current_nav_per_share - qtd_start) / qtd_start if qtd_start else 0
            
            # YTD
            ytd_start = self._get_period_start_nav('ytd')
            ytd_return = (self.current_nav_per_share - ytd_start) / ytd_start if ytd_start else 0
            
            # ITD
            itd_return = (self.current_nav_per_share - self.initial_nav) / self.initial_nav
            
            # Calculate volatility and ratios
            if NUMPY_AVAILABLE and len(nav_series) > 1:
                returns = np.diff(nav_series) / nav_series[:-1]
                volatility = np.std(returns) * np.sqrt(252)
                
                # Sharpe (assuming 5% risk-free rate)
                excess_return = np.mean(returns) * 252 - 0.05
                sharpe = excess_return / volatility if volatility > 0 else 0
                
                # Sortino
                downside_returns = returns[returns < 0]
                downside_vol = np.std(downside_returns) * np.sqrt(252) if len(downside_returns) > 0 else 0.0001
                sortino = excess_return / downside_vol
                
                # Max drawdown
                cumulative = np.cumprod(1 + returns)
                running_max = np.maximum.accumulate(cumulative)
                drawdowns = (cumulative - running_max) / running_max
                max_drawdown = np.min(drawdowns)
                current_drawdown = drawdowns[-1] if len(drawdowns) > 0 else 0
            else:
                volatility = 0
                sharpe = 0
                sortino = 0
                max_drawdown = 0
                current_drawdown = 0
        else:
            mtd_return = qtd_return = ytd_return = itd_return = 0
            volatility = sharpe = sortino = max_drawdown = current_drawdown = 0
        
        return FundMetrics(
            total_aum=self.total_aum,
            nav_per_share=self.current_nav_per_share,
            total_shares=self.total_shares,
            mtd_return=mtd_return,
            qtd_return=qtd_return,
            ytd_return=ytd_return,
            itd_return=itd_return,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            max_drawdown=max_drawdown,
            current_drawdown=current_drawdown,
            volatility=volatility,
            beta=1.0,  # Would need benchmark data
            alpha=0.0,  # Would need benchmark data
            num_investors=len(self.investors),
            gross_exposure=1.0,  # Would need position data
            net_exposure=1.0,  # Would need position data
            leverage=1.0,  # Would need position data
            cash_percentage=0.1  # Would need position data
        )
    
    def _get_period_start_nav(self, period: str) -> float:
        """Get NAV at start of period"""
        today = date.today()
        
        if period == 'mtd':
            target = today.replace(day=1)
        elif period == 'qtd':
            quarter_start_month = ((today.month - 1) // 3) * 3 + 1
            target = today.replace(month=quarter_start_month, day=1)
        elif period == 'ytd':
            target = today.replace(month=1, day=1)
        else:
            return self.initial_nav
        
        # Find closest NAV to target date
        for entry in self.nav_history:
            entry_date = date.fromisoformat(entry['date'])
            if entry_date >= target:
                return entry['nav_per_share']
        
        return self.initial_nav
    
    def get_investor_report(self, investor_id: str) -> Dict[str, Any]:
        """Generate investor-specific report"""
        if investor_id not in self.investors:
            return {}
        
        investor = self.investors[investor_id]
        fee_structure = self.fee_structures[investor.share_class]
        
        return {
            'investor_id': investor.investor_id,
            'name': investor.name,
            'share_class': investor.share_class.value,
            'initial_investment': investor.initial_investment,
            'current_nav': investor.current_nav,
            'current_shares': investor.current_shares,
            'total_return': investor.total_return,
            'total_return_pct': f"{investor.total_return * 100:.2f}%",
            'days_invested': investor.days_invested,
            'is_locked': investor.is_locked,
            'lockup_end_date': investor.lockup_end_date.isoformat() if investor.lockup_end_date else None,
            'high_water_mark': investor.high_water_mark.hwm_value,
            'fee_structure': {
                'management_fee': f"{fee_structure.management_fee * 100:.1f}%",
                'performance_fee': f"{fee_structure.performance_fee * 100:.0f}%",
                'hurdle_rate': f"{fee_structure.hurdle_rate * 100:.1f}%"
            }
        }
    
    def get_fund_summary(self) -> Dict[str, Any]:
        """Get fund summary"""
        metrics = self.get_fund_metrics()
        
        return {
            'fund_name': self.fund_name,
            'fund_id': self.fund_id,
            'inception_date': self.inception_date.isoformat(),
            'base_currency': self.base_currency,
            'metrics': metrics.to_dict(),
            'investors': {
                'total': len(self.investors),
                'by_class': self._count_by_class(),
                'by_type': self._count_by_type()
            },
            'fees': {
                'accrued_management': self.accrued_management_fees,
                'accrued_performance': self.accrued_performance_fees,
                'total_accrued': self.accrued_management_fees + self.accrued_performance_fees
            }
        }
    
    def _count_by_class(self) -> Dict[str, int]:
        """Count investors by share class"""
        counts = {}
        for investor in self.investors.values():
            class_name = investor.share_class.value
            counts[class_name] = counts.get(class_name, 0) + 1
        return counts
    
    def _count_by_type(self) -> Dict[str, int]:
        """Count investors by type"""
        counts = {}
        for investor in self.investors.values():
            type_name = investor.investor_type.value
            counts[type_name] = counts.get(type_name, 0) + 1
        return counts
