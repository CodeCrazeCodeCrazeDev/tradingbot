#!/usr/bin/env python
"""
Advanced Risk Management Example

This script demonstrates the advanced risk management capabilities of the Elite Trading Bot,
including portfolio risk management, position sizing, and drawdown control.
"""

import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("advanced_risk_management")


class AdvancedRiskManager:
    """Advanced risk management system"""
    
    def __init__(self, config=None):
        """Initialize the risk manager"""
        self.config = config or {}
        logger.info("Initializing Advanced Risk Manager")
        
        # Default settings
        self.account_balance = self.config.get('account_balance', 100000)
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.01)  # 1% of account
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.05)  # 5% of account
        self.max_correlation = self.config.get('max_correlation', 0.7)
        self.max_drawdown = self.config.get('max_drawdown', 0.15)  # 15% max drawdown
        self.position_sizing_method = self.config.get('position_sizing_method', 'kelly')
        
        # Portfolio state
        self.positions = {}
        self.historical_equity = []
        self.peak_equity = self.account_balance
        self.current_drawdown = 0.0
    
    def calculate_position_size(self, symbol: str, entry_price: float, stop_loss: float, 
                              win_rate: float, reward_risk_ratio: float) -> dict:
        """
        Calculate optimal position size using different methods
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_loss: Stop loss price
            win_rate: Historical win rate (0-1)
            reward_risk_ratio: Reward to risk ratio
            
        Returns:
            Position sizing recommendations
        """
        logger.info(f"Calculating position size for {symbol}")
        
        # Calculate risk amount in account currency
        risk_amount = self.account_balance * self.max_risk_per_trade
        
        # Calculate risk in price terms
        price_risk = abs(entry_price - stop_loss)
        
        # Calculate position size based on fixed risk
        fixed_risk_size = risk_amount / price_risk
        
        # Calculate Kelly position size
        # f* = (p * b - q) / b
        # where p = win rate, q = 1 - p, b = reward/risk ratio
        kelly_fraction = (win_rate * reward_risk_ratio - (1 - win_rate)) / reward_risk_ratio
        
        # Limit Kelly to avoid over-betting
        kelly_fraction = max(0, min(kelly_fraction, 0.5))  # Half-Kelly for safety
        
        kelly_size = (self.account_balance * kelly_fraction) / price_risk
        
        # Calculate optimal f position size
        # Simplified version of optimal f
        optimal_f = win_rate - (1 / reward_risk_ratio)
        optimal_f = max(0, min(optimal_f, 0.5))  # Limit to 0.5
        
        optimal_f_size = (self.account_balance * optimal_f) / price_risk
        
        # Select position size based on method
        if self.position_sizing_method == 'fixed_risk':
            recommended_size = fixed_risk_size
            method = 'fixed_risk'
        elif self.position_sizing_method == 'kelly':
            recommended_size = kelly_size
            method = 'kelly'
        elif self.position_sizing_method == 'optimal_f':
            recommended_size = optimal_f_size
            method = 'optimal_f'
        else:
            # Default to fixed risk
            recommended_size = fixed_risk_size
            method = 'fixed_risk'
        
        # Round to 2 decimal places
        recommended_size = round(recommended_size, 2)
        
        return {
            'symbol': symbol,
            'entry_price': entry_price,
            'stop_loss': stop_loss,
            'risk_amount': risk_amount,
            'price_risk': price_risk,
            'fixed_risk_size': round(fixed_risk_size, 2),
            'kelly_fraction': kelly_fraction,
            'kelly_size': round(kelly_size, 2),
            'optimal_f': optimal_f,
            'optimal_f_size': round(optimal_f_size, 2),
            'recommended_size': recommended_size,
            'method': method
        }
    
    def check_portfolio_risk(self, new_position: dict) -> dict:
        """
        Check if adding a new position would exceed portfolio risk limits
        
        Args:
            new_position: New position details
            
        Returns:
            Risk check results
        """
        logger.info("Checking portfolio risk")
        
        # Calculate current portfolio risk
        current_risk = sum(pos['risk_amount'] for pos in self.positions.values())
        current_risk_pct = current_risk / self.account_balance
        
        # Calculate new risk
        new_risk = current_risk + new_position['risk_amount']
        new_risk_pct = new_risk / self.account_balance
        
        # Check if new risk exceeds limit
        exceeds_limit = new_risk_pct > self.max_portfolio_risk
        
        # Calculate correlation risk
        correlation_risk = self._calculate_correlation_risk(new_position)
        
        # Check drawdown
        drawdown_risk = self.current_drawdown > self.max_drawdown
        
        # Overall risk assessment
        if exceeds_limit:
            risk_level = 'high'
            approved = False
            reason = f"Portfolio risk ({new_risk_pct:.2%}) would exceed limit ({self.max_portfolio_risk:.2%})"
        elif correlation_risk['high_correlation']:
            risk_level = 'elevated'
            approved = False
            reason = f"High correlation with existing positions: {correlation_risk['correlated_symbols']}"
        elif drawdown_risk:
            risk_level = 'elevated'
            approved = False
            reason = f"Current drawdown ({self.current_drawdown:.2%}) exceeds limit ({self.max_drawdown:.2%})"
        else:
            risk_level = 'acceptable'
            approved = True
            reason = "Within risk parameters"
        
        return {
            'current_risk_pct': current_risk_pct,
            'new_risk_pct': new_risk_pct,
            'max_risk_pct': self.max_portfolio_risk,
            'exceeds_limit': exceeds_limit,
            'correlation_risk': correlation_risk,
            'drawdown_risk': drawdown_risk,
            'risk_level': risk_level,
            'approved': approved,
            'reason': reason
        }
    
    def _calculate_correlation_risk(self, new_position: dict) -> dict:
        """
        Calculate correlation risk with existing positions
        
        Args:
            new_position: New position details
            
        Returns:
            Correlation risk assessment
        """
        # This is a simplified version - in a real system, would use actual correlation data
        
        # Define correlation groups
        correlation_groups = {
            'majors': ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD'],
            'euro_pairs': ['EURUSD', 'EURGBP', 'EURJPY', 'EURCHF', 'EURAUD'],
            'pound_pairs': ['GBPUSD', 'EURGBP', 'GBPJPY', 'GBPCHF', 'GBPAUD'],
            'commodity_currencies': ['AUDUSD', 'NZDUSD', 'USDCAD']
        }
        
        # Check if new position is in the same group as existing positions
        new_symbol = new_position['symbol']
        correlated_symbols = []
        
        for group_name, symbols in correlation_groups.items():
            if new_symbol in symbols:
                # Check if any existing positions are in the same group
                for pos_symbol in self.positions:
                    if pos_symbol in symbols and pos_symbol != new_symbol:
                        correlated_symbols.append(pos_symbol)
        
        high_correlation = len(correlated_symbols) > 0
        
        return {
            'high_correlation': high_correlation,
            'correlated_symbols': correlated_symbols,
            'correlation_groups': [group for group, symbols in correlation_groups.items() if new_symbol in symbols]
        }
    
    def update_account_equity(self, equity: float) -> dict:
        """
        Update account equity and calculate drawdown
        
        Args:
            equity: Current account equity
            
        Returns:
            Updated equity metrics
        """
        logger.info(f"Updating account equity: {equity}")
        
        # Store historical equity
        self.historical_equity.append({
            'timestamp': datetime.now(),
            'equity': equity
        })
        
        # Update peak equity if current equity is higher
        if equity > self.peak_equity:
            self.peak_equity = equity
        
        # Calculate current drawdown
        self.current_drawdown = (self.peak_equity - equity) / self.peak_equity if self.peak_equity > 0 else 0
        
        # Check if drawdown exceeds limit
        drawdown_exceeded = self.current_drawdown > self.max_drawdown
        
        return {
            'equity': equity,
            'peak_equity': self.peak_equity,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'drawdown_exceeded': drawdown_exceeded
        }
    
    def calculate_var(self, confidence_level: float = 0.95, time_horizon: int = 1) -> dict:
        """
        Calculate Value at Risk (VaR) for the portfolio
        
        Args:
            confidence_level: Confidence level (0-1)
            time_horizon: Time horizon in days
            
        Returns:
            VaR metrics
        """
        logger.info(f"Calculating VaR at {confidence_level:.0%} confidence")
        
        # Need at least 30 data points for meaningful VaR
        if len(self.historical_equity) < 30:
            return {
                'var': None,
                'cvar': None,
                'reason': "Insufficient historical data"
            }
        
        # Extract equity values
        equity_values = [entry['equity'] for entry in self.historical_equity]
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(equity_values)):
            returns.append((equity_values[i] - equity_values[i-1]) / equity_values[i-1])
        
        # Convert to numpy array
        returns = np.array(returns)
        
        # Calculate VaR
        var_percentile = 1 - confidence_level
        var = np.percentile(returns, var_percentile * 100) * self.account_balance
        
        # Calculate Conditional VaR (Expected Shortfall)
        cvar_returns = returns[returns <= np.percentile(returns, var_percentile * 100)]
        cvar = np.mean(cvar_returns) * self.account_balance if len(cvar_returns) > 0 else var
        
        # Scale to time horizon
        var = var * np.sqrt(time_horizon)
        cvar = cvar * np.sqrt(time_horizon)
        
        return {
            'var': abs(var),
            'cvar': abs(cvar),
            'confidence_level': confidence_level,
            'time_horizon': time_horizon
        }
    
    def add_position(self, position: dict) -> bool:
        """
        Add a position to the portfolio
        
        Args:
            position: Position details
            
        Returns:
            True if position was added
        """
        # Check portfolio risk
        risk_check = self.check_portfolio_risk(position)
        
        if not risk_check['approved']:
            logger.warning(f"Position rejected: {risk_check['reason']}")
            return False
        
        # Add position
        self.positions[position['symbol']] = position
        logger.info(f"Position added: {position['symbol']}")
        
        return True
    
    def close_position(self, symbol: str, exit_price: float) -> dict:
        """
        Close a position
        
        Args:
            symbol: Symbol to close
            exit_price: Exit price
            
        Returns:
            Position result
        """
        if symbol not in self.positions:
            logger.warning(f"Position not found: {symbol}")
            return None
        
        position = self.positions[symbol]
        
        # Calculate profit/loss
        if position.get('direction', 'buy').lower() == 'buy':
            pnl = (exit_price - position['entry_price']) * position['recommended_size']
        else:
            pnl = (position['entry_price'] - exit_price) * position['recommended_size']
        
        # Update account balance
        self.account_balance += pnl
        
        # Update equity
        equity_update = self.update_account_equity(self.account_balance)
        
        # Remove position
        del self.positions[symbol]
        
        result = {
            'symbol': symbol,
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'size': position['recommended_size'],
            'pnl': pnl,
            'return_pct': pnl / self.account_balance,
            'account_balance': self.account_balance,
            'current_drawdown': equity_update['current_drawdown']
        }
        
        logger.info(f"Position closed: {symbol}, P&L: {pnl:.2f}")
        
        return result
    
    def get_portfolio_status(self) -> dict:
        """
        Get current portfolio status
        
        Returns:
            Portfolio status
        """
        # Calculate total exposure
        total_exposure = sum(pos['recommended_size'] * pos['entry_price'] for pos in self.positions.values())
        exposure_pct = total_exposure / self.account_balance if self.account_balance > 0 else 0
        
        # Calculate total risk
        total_risk = sum(pos['risk_amount'] for pos in self.positions.values())
        risk_pct = total_risk / self.account_balance if self.account_balance > 0 else 0
        
        # Calculate VaR
        var_metrics = self.calculate_var()
        
        return {
            'account_balance': self.account_balance,
            'peak_equity': self.peak_equity,
            'current_drawdown': self.current_drawdown,
            'position_count': len(self.positions),
            'positions': self.positions,
            'total_exposure': total_exposure,
            'exposure_pct': exposure_pct,
            'total_risk': total_risk,
            'risk_pct': risk_pct,
            'var_metrics': var_metrics
        }
    
    def visualize_risk_metrics(self, save_path: str = None):
        """
        Visualize risk metrics
        
        Args:
            save_path: Path to save the visualization
        """
        logger.info("Visualizing risk metrics")
        
        # Create figure with subplots
        fig, axs = plt.subplots(3, 1, figsize=(10, 15))
        
        # Plot equity curve
        if self.historical_equity:
            timestamps = [entry['timestamp'] for entry in self.historical_equity]
            equity_values = [entry['equity'] for entry in self.historical_equity]
            
            axs[0].set_title('Equity Curve')
            axs[0].plot(timestamps, equity_values, label='Equity')
            axs[0].axhline(y=self.peak_equity, color='green', linestyle='--', label='Peak Equity')
            axs[0].axhline(y=self.peak_equity * (1 - self.max_drawdown), color='red', linestyle='--', label='Max Drawdown Limit')
            axs[0].legend()
            axs[0].grid(True)
            
            # Plot drawdown
            drawdowns = [(self.peak_equity - eq) / self.peak_equity for eq in equity_values]
            
            axs[1].set_title('Drawdown')
            axs[1].plot(timestamps, drawdowns, color='red')
            axs[1].axhline(y=self.max_drawdown, color='red', linestyle='--', label='Max Drawdown Limit')
            axs[1].fill_between(timestamps, drawdowns, 0, color='red', alpha=0.3)
            axs[1].set_ylim(0, max(drawdowns) * 1.2 if drawdowns else 0.2)
            axs[1].legend()
            axs[1].grid(True)
        else:
            axs[0].set_title('Equity Curve (No Data)')
            axs[1].set_title('Drawdown (No Data)')
        
        # Plot position risk
        if self.positions:
            symbols = list(self.positions.keys())
            risk_amounts = [pos['risk_amount'] for pos in self.positions.values()]
            
            axs[2].set_title('Position Risk')
            bars = axs[2].bar(symbols, risk_amounts)
            
            # Add risk percentage labels
            for i, bar in enumerate(bars):
                risk_pct = risk_amounts[i] / self.account_balance
                axs[2].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                           f'{risk_pct:.1%}', ha='center')
            
            axs[2].axhline(y=self.account_balance * self.max_risk_per_trade, color='red', linestyle='--', label='Max Risk Per Trade')
            axs[2].legend()
            axs[2].grid(True)
        else:
            axs[2].set_title('Position Risk (No Positions)')
        
        # Adjust layout
        plt.tight_layout()
        
        # Save or show
        if save_path:
            plt.savefig(save_path)
            logger.info(f"Visualization saved to {save_path}")
        else:
            plt.show()


async def simulate_trading():
    """Simulate trading to demonstrate risk management"""
    logger.info("Starting trading simulation")
    
    # Initialize risk manager
    risk_manager = AdvancedRiskManager({
        'account_balance': 100000,
        'max_risk_per_trade': 0.01,
        'max_portfolio_risk': 0.05,
        'max_drawdown': 0.15,
        'position_sizing_method': 'kelly'
    })
    
    # Create output directory
    output_dir = Path("examples/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Simulate trading
    symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD']
    
    # Simulate account equity changes
    for i in range(30):
        # Random equity change (-2% to +2%)
        change_pct = np.random.normal(0.001, 0.01)  # Slight positive bias
        new_equity = risk_manager.account_balance * (1 + change_pct)
        risk_manager.update_account_equity(new_equity)
        
        # Simulate a day passing
        await asyncio.sleep(0.1)
    
    # Open positions
    for symbol in symbols[:3]:  # Open positions for first 3 symbols
        # Calculate position size
        entry_price = 1.0 + np.random.random() * 0.5  # Random price between 1.0 and 1.5
        stop_loss = entry_price * (1 - 0.01)  # 1% stop loss
        win_rate = 0.55  # 55% win rate
        reward_risk_ratio = 1.5  # 1.5:1 reward to risk
        
        position = risk_manager.calculate_position_size(
            symbol=symbol,
            entry_price=entry_price,
            stop_loss=stop_loss,
            win_rate=win_rate,
            reward_risk_ratio=reward_risk_ratio
        )
        
        # Add direction
        position['direction'] = 'buy'
        
        # Try to add position
        added = risk_manager.add_position(position)
        
        if added:
            logger.info(f"Position opened: {symbol}, Size: {position['recommended_size']}")
        else:
            logger.warning(f"Failed to open position: {symbol}")
    
    # Get portfolio status
    status = risk_manager.get_portfolio_status()
    
    logger.info("Portfolio Status:")
    logger.info(f"Account Balance: ${status['account_balance']:.2f}")
    logger.info(f"Current Drawdown: {status['current_drawdown']:.2%}")
    logger.info(f"Position Count: {status['position_count']}")
    logger.info(f"Total Exposure: ${status['total_exposure']:.2f} ({status['exposure_pct']:.2%})")
    logger.info(f"Total Risk: ${status['total_risk']:.2f} ({status['risk_pct']:.2%})")
    
    if status['var_metrics']['var'] is not None:
        logger.info(f"Value at Risk (95%): ${status['var_metrics']['var']:.2f}")
        logger.info(f"Conditional VaR: ${status['var_metrics']['cvar']:.2f}")
    
    # Try to open a position that would exceed risk limits
    risky_position = risk_manager.calculate_position_size(
        symbol='USDCHF',
        entry_price=1.2,
        stop_loss=1.15,  # Wide stop loss
        win_rate=0.5,
        reward_risk_ratio=1.0
    )
    risky_position['direction'] = 'buy'
    
    # Force higher risk amount
    risky_position['risk_amount'] = risk_manager.account_balance * 0.04  # 4% risk
    
    added = risk_manager.add_position(risky_position)
    
    if not added:
        logger.info("Successfully rejected high-risk position")
    
    # Close a position
    if 'EURUSD' in risk_manager.positions:
        position = risk_manager.positions['EURUSD']
        exit_price = position['entry_price'] * 1.02  # 2% profit
        
        result = risk_manager.close_position('EURUSD', exit_price)
        
        logger.info(f"Closed position: EURUSD, P&L: ${result['pnl']:.2f}")
    
    # Visualize risk metrics
    risk_manager.visualize_risk_metrics(save_path="examples/output/risk_metrics.png")
    logger.info("Risk visualization saved to examples/output/risk_metrics.png")
    
    logger.info("Trading simulation completed")


async def main():
    """Main function"""
    logger.info("Starting Advanced Risk Management Example")
    
    try:
        await simulate_trading()
    except Exception as e:
        logger.exception(f"Error in simulation: {e}")
    
    logger.info("Advanced Risk Management Example completed")


if __name__ == "__main__":
    asyncio.run(main())
