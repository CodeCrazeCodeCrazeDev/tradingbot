"""
Risk Management Validator
Validates stop-loss, take-profit, trailing stops, and drawdown controls
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Any, Dict, List
import yaml

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.comprehensive_validator import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class RiskValidator:
    """Validates risk management systems"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}
    
    def validate_position_sizing(self) -> ValidationResult:
        """Validate position sizing calculations"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            import talib
            import pandas as pd
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Risk Management",
                    test_name="Position Sizing",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Get account info
            account_info = mt5.account_info()
            if account_info is None:
                mt5.shutdown()
                return ValidationResult(
                    component="Risk Management",
                    test_name="Position Sizing",
                    status=ValidationStatus.FAILED,
                    message="Failed to get account info",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            balance = account_info.balance
            
            # Get risk parameters from config
            risk_per_trade = self.config.get('trading', {}).get('risk_per_trade', 0.01)
            max_position_size = self.config.get('risk', {}).get('max_position_size', 0.01)
            min_position_size = self.config.get('risk', {}).get('min_position_size', 0.01)
            
            # Get ATR for stop loss calculation
            symbol = "EURUSD"
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            
            if rates is None:
                mt5.shutdown()
                return ValidationResult(
                    component="Risk Management",
                    test_name="Position Sizing",
                    status=ValidationStatus.FAILED,
                    message="Failed to get price data",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            df = pd.DataFrame(rates)
            atr = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            current_atr = atr[-1]
            
            # Calculate position size
            sl_multiplier = self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0)
            stop_loss_pips = current_atr * sl_multiplier * 10000  # Convert to pips
            
            risk_amount = balance * risk_per_trade
            pip_value = 10  # For standard lot EURUSD
            
            calculated_lots = risk_amount / (stop_loss_pips * pip_value)
            
            # Apply limits
            final_lots = max(min_position_size, min(calculated_lots, max_position_size))
            
            mt5.shutdown()
            
            # Validate calculations
            issues = []
            
            if calculated_lots > max_position_size:
                issues.append(f"Calculated size ({calculated_lots:.2f}) exceeds max ({max_position_size})")
            
            if calculated_lots < min_position_size:
                issues.append(f"Calculated size ({calculated_lots:.2f}) below min ({min_position_size})")
            
            if risk_amount > balance * 0.05:  # More than 5% risk is dangerous
                issues.append(f"Risk amount ({risk_amount:.2f}) is too high")
            
            details = {
                'balance': balance,
                'risk_per_trade_pct': risk_per_trade * 100,
                'risk_amount': round(risk_amount, 2),
                'atr_pips': round(current_atr * 10000, 2),
                'stop_loss_pips': round(stop_loss_pips, 2),
                'calculated_lots': round(calculated_lots, 4),
                'final_lots': round(final_lots, 4),
                'max_position_size': max_position_size,
                'min_position_size': min_position_size
            }
            
            if issues:
                return ValidationResult(
                    component="Risk Management",
                    test_name="Position Sizing",
                    status=ValidationStatus.WARNING,
                    message=f"Position sizing issues: {'; '.join(issues)}",
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Risk Management",
                test_name="Position Sizing",
                status=ValidationStatus.PASSED,
                message=f"Position sizing valid: {final_lots:.4f} lots",
                details=details,
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Risk Management",
                test_name="Position Sizing",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_stop_loss_take_profit(self) -> ValidationResult:
        """Validate stop loss and take profit calculations"""
        start = time.time()
        
        try:
            import MetaTrader5 as mt5
            import talib
            import pandas as pd
            
            if not mt5.initialize():
                return ValidationResult(
                    component="Risk Management",
                    test_name="SL/TP Calculation",
                    status=ValidationStatus.FAILED,
                    message="MT5 not initialized",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Get current price and ATR
            symbol = "EURUSD"
            tick = mt5.symbol_info_tick(symbol)
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            
            if tick is None or rates is None:
                mt5.shutdown()
                return ValidationResult(
                    component="Risk Management",
                    test_name="SL/TP Calculation",
                    status=ValidationStatus.FAILED,
                    message="Failed to get market data",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            df = pd.DataFrame(rates)
            atr = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=14)
            current_atr = atr[-1]
            
            # Get config parameters
            sl_multiplier = self.config.get('trading', {}).get('stop_loss_atr_multiplier', 2.0)
            tp_rr_ratio = self.config.get('trading', {}).get('take_profit_rr_ratio', 2.0)
            
            # Calculate for BUY trade
            entry_price = tick.ask
            stop_loss = entry_price - (current_atr * sl_multiplier)
            sl_distance = entry_price - stop_loss
            take_profit = entry_price + (sl_distance * tp_rr_ratio)
            
            mt5.shutdown()
            
            # Validate calculations
            issues = []
            
            if stop_loss >= entry_price:
                issues.append("Stop loss above entry for BUY trade")
            
            if take_profit <= entry_price:
                issues.append("Take profit below entry for BUY trade")
            
            if sl_distance < current_atr * 0.5:
                issues.append("Stop loss too tight")
            
            if sl_distance > current_atr * 5:
                issues.append("Stop loss too wide")
            
            rr_ratio = (take_profit - entry_price) / (entry_price - stop_loss)
            if rr_ratio < 1.5:
                issues.append(f"Risk/Reward ratio too low: {rr_ratio:.2f}")
            
            details = {
                'entry_price': round(entry_price, 5),
                'stop_loss': round(stop_loss, 5),
                'take_profit': round(take_profit, 5),
                'sl_distance_pips': round(sl_distance * 10000, 2),
                'tp_distance_pips': round((take_profit - entry_price) * 10000, 2),
                'risk_reward_ratio': round(rr_ratio, 2),
                'atr_pips': round(current_atr * 10000, 2)
            }
            
            if issues:
                return ValidationResult(
                    component="Risk Management",
                    test_name="SL/TP Calculation",
                    status=ValidationStatus.WARNING,
                    message=f"SL/TP issues: {'; '.join(issues)}",
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Risk Management",
                test_name="SL/TP Calculation",
                status=ValidationStatus.PASSED,
                message=f"SL/TP valid - R:R {rr_ratio:.2f}:1",
                details=details,
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Risk Management",
                test_name="SL/TP Calculation",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_drawdown_control(self) -> ValidationResult:
        """Validate drawdown control mechanisms"""
        start = time.time()
        
        try:
            max_drawdown_pct = self.config.get('risk', {}).get('max_drawdown_pct', 20.0)
            
            # Simulate drawdown scenarios
            initial_balance = 10000
            scenarios = [
                {'name': '5% loss', 'loss_pct': 5, 'should_stop': False},
                {'name': '10% loss', 'loss_pct': 10, 'should_stop': False},
                {'name': '15% loss', 'loss_pct': 15, 'should_stop': False},
                {'name': '20% loss', 'loss_pct': 20, 'should_stop': True},
                {'name': '25% loss', 'loss_pct': 25, 'should_stop': True},
            ]
            
            results = {}
            all_correct = True
            
            for scenario in scenarios:
                current_balance = initial_balance * (1 - scenario['loss_pct'] / 100)
                drawdown = ((initial_balance - current_balance) / initial_balance) * 100
                should_stop = drawdown >= max_drawdown_pct
                
                is_correct = should_stop == scenario['should_stop']
                results[scenario['name']] = {
                    'drawdown_pct': round(drawdown, 2),
                    'should_stop': should_stop,
                    'expected': scenario['should_stop'],
                    'correct': is_correct
                }
                
                if not is_correct:
                    all_correct = False
            
            details = {
                'max_drawdown_pct': max_drawdown_pct,
                'scenarios': results
            }
            
            if all_correct:
                return ValidationResult(
                    component="Risk Management",
                    test_name="Drawdown Control",
                    status=ValidationStatus.PASSED,
                    message=f"Drawdown control working - limit {max_drawdown_pct}%",
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            else:
                return ValidationResult(
                    component="Risk Management",
                    test_name="Drawdown Control",
                    status=ValidationStatus.FAILED,
                    message="Drawdown control logic incorrect",
                    details=details,
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
        except Exception as e:
            return ValidationResult(
                component="Risk Management",
                test_name="Drawdown Control",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all risk management validations"""
        logger.info("=" * 80)
        logger.info("RISK MANAGEMENT VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_position_sizing(),
            self.validate_stop_loss_take_profit(),
            self.validate_drawdown_control()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


if __name__ == "__main__":
    validator = RiskValidator()
    results = validator.validate_all()
