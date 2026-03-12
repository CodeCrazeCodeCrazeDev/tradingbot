"""
Prime Broker Interface
======================
Prime brokerage services integration:
- Margin and financing
- Securities lending
- Cash management
- Custody services
- Trade execution
- Reporting
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class BorrowStatus(Enum):
    """Securities lending status"""
    AVAILABLE = "available"
    HARD_TO_BORROW = "hard_to_borrow"
    SPECIAL = "special"
    UNAVAILABLE = "unavailable"


class CashMovementType(Enum):
    """Cash movement types"""
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    MARGIN_CALL = "margin_call"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    SETTLEMENT = "settlement"


@dataclass
class SecuritiesLoan:
    """Securities lending position"""
    loan_id: str
    symbol: str
    quantity: int
    borrow_rate: float  # Annual rate
    start_date: date
    collateral_amount: float
    collateral_type: str  # cash, securities
    status: str  # active, recalled, returned
    
    @property
    def daily_cost(self) -> float:
        """Calculate daily borrow cost"""
        return self.quantity * self.borrow_rate / 365
    
    @property
    def days_borrowed(self) -> int:
        return (date.today() - self.start_date).days
    
    @property
    def total_cost(self) -> float:
        return self.daily_cost * self.days_borrowed


@dataclass
class MarginLoan:
    """Margin loan position"""
    loan_id: str
    principal: float
    interest_rate: float  # Annual
    start_date: date
    collateral_value: float
    loan_to_value: float
    status: str  # active, called, paid
    
    @property
    def accrued_interest(self) -> float:
        days = (date.today() - self.start_date).days
        return self.principal * self.interest_rate * days / 365


@dataclass
class CashMovement:
    """Cash movement record"""
    movement_id: str
    movement_type: CashMovementType
    amount: float
    currency: str
    value_date: date
    description: str
    status: str  # pending, settled, failed


class SecuritiesLending:
    """
    Securities Lending Service
    Manages short selling and stock borrowing
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Borrow rates by difficulty
        self.base_rates = {
            BorrowStatus.AVAILABLE: 0.005,  # 0.5%
            BorrowStatus.HARD_TO_BORROW: 0.05,  # 5%
            BorrowStatus.SPECIAL: 0.20,  # 20%
        }
        
        # Active loans
        self.active_loans: Dict[str, SecuritiesLoan] = {}
        
        # Locate inventory (what's available to borrow)
        self.inventory: Dict[str, Dict[str, Any]] = {}
        
        # History
        self.loan_history: List[SecuritiesLoan] = []
        
        logger.info("Securities Lending initialized")
    
    def check_availability(
        self,
        symbol: str,
        quantity: int
    ) -> Tuple[BorrowStatus, float, int]:
        """
        Check borrow availability
        Returns: (status, rate, available_quantity)
        """
        if symbol not in self.inventory:
            # Simulate inventory
            self.inventory[symbol] = {
                'available': 100000,
                'status': BorrowStatus.AVAILABLE,
                'rate': self.base_rates[BorrowStatus.AVAILABLE]
            }
        
        inv = self.inventory[symbol]
        status = inv['status']
        rate = inv['rate']
        available = inv['available']
        
        if quantity > available:
            if available > 0:
                status = BorrowStatus.HARD_TO_BORROW
                rate = self.base_rates[BorrowStatus.HARD_TO_BORROW]
            else:
                status = BorrowStatus.UNAVAILABLE
                rate = 0
        
        return status, rate, min(quantity, available)
    
    def request_locate(
        self,
        symbol: str,
        quantity: int
    ) -> Dict[str, Any]:
        """Request locate for short selling"""
        status, rate, available = self.check_availability(symbol, quantity)
        
        locate = {
            'locate_id': str(uuid.uuid4())[:8],
            'symbol': symbol,
            'requested_quantity': quantity,
            'available_quantity': available,
            'status': status.value,
            'borrow_rate': rate,
            'valid_until': datetime.now() + timedelta(hours=24),
            'approved': status != BorrowStatus.UNAVAILABLE
        }
        
        return locate
    
    def borrow_securities(
        self,
        symbol: str,
        quantity: int,
        collateral_type: str = 'cash'
    ) -> Optional[SecuritiesLoan]:
        """Borrow securities for short selling"""
        status, rate, available = self.check_availability(symbol, quantity)
        
        if status == BorrowStatus.UNAVAILABLE or available < quantity:
            logger.warning(f"Cannot borrow {quantity} shares of {symbol}")
            return None
        
        # Calculate collateral (102% for cash, 105% for securities)
        collateral_pct = 1.02 if collateral_type == 'cash' else 1.05
        price = self.inventory[symbol].get('price', 100)  # Would get from market data
        collateral = quantity * price * collateral_pct
        
        loan = SecuritiesLoan(
            loan_id=str(uuid.uuid4())[:8],
            symbol=symbol,
            quantity=quantity,
            borrow_rate=rate,
            start_date=date.today(),
            collateral_amount=collateral,
            collateral_type=collateral_type,
            status='active'
        )
        
        # Update inventory
        self.inventory[symbol]['available'] -= quantity
        
        # Store loan
        self.active_loans[loan.loan_id] = loan
        
        logger.info(f"Borrowed {quantity} shares of {symbol} at {rate*100:.2f}%")
        return loan
    
    def return_securities(
        self,
        loan_id: str
    ) -> Dict[str, Any]:
        """Return borrowed securities"""
        if loan_id not in self.active_loans:
            return {'success': False, 'error': 'Loan not found'}
        
        loan = self.active_loans[loan_id]
        
        # Calculate final cost
        total_cost = loan.total_cost
        
        # Update inventory
        if loan.symbol in self.inventory:
            self.inventory[loan.symbol]['available'] += loan.quantity
        
        # Update loan status
        loan.status = 'returned'
        
        # Move to history
        self.loan_history.append(loan)
        del self.active_loans[loan_id]
        
        return {
            'success': True,
            'loan_id': loan_id,
            'symbol': loan.symbol,
            'quantity': loan.quantity,
            'days_borrowed': loan.days_borrowed,
            'total_cost': total_cost,
            'collateral_returned': loan.collateral_amount
        }
    
    def get_borrow_costs(self) -> Dict[str, Any]:
        """Get current borrow costs"""
        total_daily = sum(loan.daily_cost for loan in self.active_loans.values())
        total_accrued = sum(loan.total_cost for loan in self.active_loans.values())
        
        return {
            'active_loans': len(self.active_loans),
            'total_borrowed_value': sum(
                loan.quantity * self.inventory.get(loan.symbol, {}).get('price', 100)
                for loan in self.active_loans.values()
            ),
            'daily_borrow_cost': total_daily,
            'total_accrued_cost': total_accrued,
            'total_collateral': sum(loan.collateral_amount for loan in self.active_loans.values())
        }


class MarginCalculator:
    """
    Margin Calculator
    Calculates margin requirements and buying power
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Margin rates by asset class
        self.margin_rates = {
            'equity': {'initial': 0.50, 'maintenance': 0.25},
            'option': {'initial': 1.00, 'maintenance': 1.00},
            'futures': {'initial': 0.10, 'maintenance': 0.05},
            'forex': {'initial': 0.02, 'maintenance': 0.01},
            'crypto': {'initial': 0.50, 'maintenance': 0.40},
            'bond': {'initial': 0.10, 'maintenance': 0.05}
        }
        
        # Portfolio margin (for qualified accounts)
        self.portfolio_margin_enabled = config.get('portfolio_margin', False)
        
        # Active margin loans
        self.margin_loans: Dict[str, MarginLoan] = {}
        
        logger.info("Margin Calculator initialized")
    
    def calculate_margin_requirement(
        self,
        positions: Dict[str, Dict[str, Any]],
        margin_type: str = 'initial'
    ) -> Dict[str, Any]:
        """Calculate margin requirement for positions"""
        total_requirement = 0
        position_requirements = {}
        
        for symbol, pos in positions.items():
            quantity = abs(pos.get('quantity', 0))
            price = pos.get('price', 0)
            asset_class = pos.get('asset_class', 'equity')
            
            position_value = quantity * price
            
            # Get margin rate
            rates = self.margin_rates.get(asset_class, self.margin_rates['equity'])
            rate = rates['initial'] if margin_type == 'initial' else rates['maintenance']
            
            # Short positions may have higher requirements
            if pos.get('quantity', 0) < 0:
                rate = min(rate * 1.5, 1.0)  # 50% higher for shorts, max 100%
            
            requirement = position_value * rate
            position_requirements[symbol] = {
                'value': position_value,
                'rate': rate,
                'requirement': requirement
            }
            
            total_requirement += requirement
        
        return {
            'total_requirement': total_requirement,
            'margin_type': margin_type,
            'positions': position_requirements
        }
    
    def calculate_buying_power(
        self,
        equity: float,
        current_margin_used: float
    ) -> Dict[str, Any]:
        """Calculate available buying power"""
        # Standard margin (2:1 for equities)
        standard_bp = (equity - current_margin_used) * 2
        
        # Day trading buying power (4:1 for pattern day traders)
        day_trading_bp = (equity - current_margin_used) * 4
        
        # Portfolio margin buying power (if enabled)
        portfolio_bp = (equity - current_margin_used) * 6.67 if self.portfolio_margin_enabled else 0
        
        return {
            'equity': equity,
            'margin_used': current_margin_used,
            'available_margin': equity - current_margin_used,
            'standard_buying_power': max(0, standard_bp),
            'day_trading_buying_power': max(0, day_trading_bp),
            'portfolio_margin_buying_power': max(0, portfolio_bp)
        }
    
    def check_margin_call(
        self,
        equity: float,
        positions: Dict[str, Dict[str, Any]]
    ) -> Tuple[bool, float]:
        """Check if margin call is triggered"""
        maintenance = self.calculate_margin_requirement(positions, 'maintenance')
        maintenance_req = maintenance['total_requirement']
        
        is_margin_call = equity < maintenance_req
        shortfall = max(0, maintenance_req - equity)
        
        return is_margin_call, shortfall
    
    def request_margin_loan(
        self,
        amount: float,
        collateral_value: float,
        interest_rate: Optional[float] = None
    ) -> Optional[MarginLoan]:
        """Request margin loan"""
        # Default rate based on amount
        if interest_rate is None:
            if amount < 100000:
                interest_rate = 0.08  # 8%
            elif amount < 1000000:
                interest_rate = 0.065  # 6.5%
            else:
                interest_rate = 0.05  # 5%
        
        # Check LTV
        ltv = amount / collateral_value if collateral_value > 0 else 1
        if ltv > 0.7:  # Max 70% LTV
            logger.warning(f"LTV too high: {ltv*100:.1f}%")
            return None
        
        loan = MarginLoan(
            loan_id=str(uuid.uuid4())[:8],
            principal=amount,
            interest_rate=interest_rate,
            start_date=date.today(),
            collateral_value=collateral_value,
            loan_to_value=ltv,
            status='active'
        )
        
        self.margin_loans[loan.loan_id] = loan
        logger.info(f"Margin loan approved: ${amount:,.2f} at {interest_rate*100:.2f}%")
        
        return loan


class CashManagement:
    """
    Cash Management Service
    Manages cash balances and movements
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Cash balances by currency
        self.balances: Dict[str, float] = {'USD': 0}
        
        # Pending movements
        self.pending_movements: List[CashMovement] = []
        
        # Movement history
        self.movement_history: List[CashMovement] = []
        
        # Interest rates for cash
        self.interest_rates = {
            'USD': 0.04,  # 4%
            'EUR': 0.03,
            'GBP': 0.045,
            'JPY': 0.001
        }
        
        logger.info("Cash Management initialized")
    
    def get_balance(self, currency: str = 'USD') -> float:
        """Get cash balance"""
        return self.balances.get(currency, 0)
    
    def deposit(
        self,
        amount: float,
        currency: str = 'USD',
        description: str = ''
    ) -> CashMovement:
        """Process deposit"""
        movement = CashMovement(
            movement_id=str(uuid.uuid4())[:8],
            movement_type=CashMovementType.DEPOSIT,
            amount=amount,
            currency=currency,
            value_date=date.today(),
            description=description or 'Cash deposit',
            status='settled'
        )
        
        self.balances[currency] = self.balances.get(currency, 0) + amount
        self.movement_history.append(movement)
        
        logger.info(f"Deposited {currency} {amount:,.2f}")
        return movement
    
    def withdraw(
        self,
        amount: float,
        currency: str = 'USD',
        description: str = ''
    ) -> Optional[CashMovement]:
        """Process withdrawal"""
        if self.balances.get(currency, 0) < amount:
            logger.warning(f"Insufficient balance for withdrawal")
            return None
        
        movement = CashMovement(
            movement_id=str(uuid.uuid4())[:8],
            movement_type=CashMovementType.WITHDRAWAL,
            amount=amount,
            currency=currency,
            value_date=date.today(),
            description=description or 'Cash withdrawal',
            status='pending'
        )
        
        self.balances[currency] -= amount
        self.pending_movements.append(movement)
        
        logger.info(f"Withdrawal initiated: {currency} {amount:,.2f}")
        return movement
    
    def calculate_interest(self, days: int = 30) -> Dict[str, float]:
        """Calculate interest earned on cash balances"""
        interest = {}
        
        for currency, balance in self.balances.items():
            rate = self.interest_rates.get(currency, 0.02)
            daily_interest = balance * rate / 365
            interest[currency] = daily_interest * days
        
        return interest
    
    def get_cash_summary(self) -> Dict[str, Any]:
        """Get cash summary"""
        return {
            'balances': self.balances.copy(),
            'total_usd': sum(self.balances.values()),  # Simplified, would need FX rates
            'pending_movements': len(self.pending_movements),
            'pending_amount': sum(m.amount for m in self.pending_movements),
            'interest_rates': self.interest_rates
        }


class Custody:
    """
    Custody Service
    Asset safekeeping and corporate actions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Held assets
        self.holdings: Dict[str, Dict[str, Any]] = {}
        
        # Corporate actions
        self.corporate_actions: List[Dict[str, Any]] = []
        
        # Custody fees
        self.custody_fee_rate = config.get('custody_fee', 0.0005)  # 5bps
        
        logger.info("Custody Service initialized")
    
    def record_holding(
        self,
        symbol: str,
        quantity: float,
        acquisition_date: date,
        cost_basis: float
    ):
        """Record asset holding"""
        self.holdings[symbol] = {
            'symbol': symbol,
            'quantity': quantity,
            'acquisition_date': acquisition_date,
            'cost_basis': cost_basis,
            'last_updated': datetime.now()
        }
    
    def process_corporate_action(
        self,
        action_type: str,
        symbol: str,
        details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process corporate action"""
        action = {
            'action_id': str(uuid.uuid4())[:8],
            'type': action_type,
            'symbol': symbol,
            'details': details,
            'record_date': details.get('record_date', date.today()),
            'ex_date': details.get('ex_date'),
            'pay_date': details.get('pay_date'),
            'status': 'pending'
        }
        
        # Process based on type
        if action_type == 'dividend':
            if symbol in self.holdings:
                holding = self.holdings[symbol]
                dividend_amount = holding['quantity'] * details.get('amount_per_share', 0)
                action['dividend_amount'] = dividend_amount
        
        elif action_type == 'split':
            if symbol in self.holdings:
                ratio = details.get('ratio', 1)
                self.holdings[symbol]['quantity'] *= ratio
                self.holdings[symbol]['cost_basis'] /= ratio
        
        elif action_type == 'merger':
            # Handle merger conversion
            pass
        
        self.corporate_actions.append(action)
        return action
    
    def calculate_custody_fees(
        self,
        total_aum: float,
        days: int = 30
    ) -> float:
        """Calculate custody fees"""
        annual_fee = total_aum * self.custody_fee_rate
        return annual_fee * days / 365
    
    def get_holdings_report(self) -> Dict[str, Any]:
        """Get holdings report"""
        return {
            'total_positions': len(self.holdings),
            'holdings': self.holdings.copy(),
            'pending_corporate_actions': [
                a for a in self.corporate_actions if a['status'] == 'pending'
            ]
        }


class PrimeBrokerInterface:
    """
    Master Prime Broker Interface
    Integrates all prime brokerage services
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Services
        self.securities_lending = SecuritiesLending(config.get('lending', {}))
        self.margin_calculator = MarginCalculator(config.get('margin', {}))
        self.cash_management = CashManagement(config.get('cash', {}))
        self.custody = Custody(config.get('custody', {}))
        
        # Prime broker details
        self.pb_name = config.get('name', 'AlphaAlgo Prime')
        self.pb_id = config.get('id', str(uuid.uuid4())[:8])
        
        # Relationship details
        self.credit_limit = config.get('credit_limit', 100_000_000)
        self.margin_rate = config.get('margin_rate', 0.05)  # 5%
        
        logger.info(f"Prime Broker Interface initialized: {self.pb_name}")
    
    def get_account_summary(
        self,
        positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get comprehensive account summary"""
        # Calculate position values
        long_value = sum(
            p['quantity'] * p.get('price', 0)
            for p in positions.values()
            if p.get('quantity', 0) > 0
        )
        short_value = sum(
            abs(p['quantity']) * p.get('price', 0)
            for p in positions.values()
            if p.get('quantity', 0) < 0
        )
        
        # Cash
        cash = self.cash_management.get_cash_summary()
        
        # Margin
        margin_req = self.margin_calculator.calculate_margin_requirement(positions)
        
        # Borrow costs
        borrow_costs = self.securities_lending.get_borrow_costs()
        
        # Net liquidation value
        nlv = cash['total_usd'] + long_value - short_value
        
        # Buying power
        buying_power = self.margin_calculator.calculate_buying_power(
            nlv, margin_req['total_requirement']
        )
        
        return {
            'prime_broker': self.pb_name,
            'account_id': self.pb_id,
            'timestamp': datetime.now().isoformat(),
            'positions': {
                'long_value': long_value,
                'short_value': short_value,
                'gross_value': long_value + short_value,
                'net_value': long_value - short_value
            },
            'cash': cash,
            'margin': {
                'requirement': margin_req['total_requirement'],
                'used': margin_req['total_requirement'],
                'available': nlv - margin_req['total_requirement']
            },
            'buying_power': buying_power,
            'borrow_costs': borrow_costs,
            'net_liquidation_value': nlv,
            'credit_limit': self.credit_limit,
            'credit_used': margin_req['total_requirement'],
            'credit_available': self.credit_limit - margin_req['total_requirement']
        }
    
    def execute_short_sale(
        self,
        symbol: str,
        quantity: int,
        price: float
    ) -> Dict[str, Any]:
        """Execute short sale with locate and borrow"""
        # Request locate
        locate = self.securities_lending.request_locate(symbol, quantity)
        
        if not locate['approved']:
            return {
                'success': False,
                'error': 'Locate not approved',
                'locate': locate
            }
        
        # Borrow securities
        loan = self.securities_lending.borrow_securities(symbol, quantity)
        
        if not loan:
            return {
                'success': False,
                'error': 'Borrow failed',
                'locate': locate
            }
        
        return {
            'success': True,
            'locate': locate,
            'loan': {
                'loan_id': loan.loan_id,
                'quantity': loan.quantity,
                'borrow_rate': loan.borrow_rate,
                'collateral': loan.collateral_amount
            },
            'execution': {
                'symbol': symbol,
                'side': 'sell_short',
                'quantity': quantity,
                'price': price,
                'value': quantity * price
            }
        }
    
    def cover_short(
        self,
        loan_id: str,
        price: float
    ) -> Dict[str, Any]:
        """Cover short position and return securities"""
        result = self.securities_lending.return_securities(loan_id)
        
        if result['success']:
            result['cover_price'] = price
            result['cover_value'] = result['quantity'] * price
        
        return result
    
    def get_financing_summary(self) -> Dict[str, Any]:
        """Get financing summary"""
        borrow = self.securities_lending.get_borrow_costs()
        margin_loans = self.margin_calculator.margin_loans
        
        total_margin_interest = sum(
            loan.accrued_interest for loan in margin_loans.values()
        )
        
        return {
            'securities_lending': borrow,
            'margin_loans': {
                'count': len(margin_loans),
                'total_principal': sum(l.principal for l in margin_loans.values()),
                'total_accrued_interest': total_margin_interest
            },
            'total_financing_cost': borrow['total_accrued_cost'] + total_margin_interest
        }
