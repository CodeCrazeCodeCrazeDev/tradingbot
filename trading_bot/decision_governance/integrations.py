"""
DGS Integration Examples

Integration patterns for popular trading frameworks and platforms.
"""

from typing import Dict, List, Optional, Any, Callable
import asyncio
import logging

logger = logging.getLogger(__name__)


class BacktraderIntegration:
    """
    Integration with Backtrader backtesting framework.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        self.decisions = []
    
    def create_strategy(self):
        """Create a Backtrader strategy that uses DGS"""
        
        # This would be used as:
        #
        # class DGSStrategy(bt.Strategy):
        #     def __init__(self):
        #         self.dgs = dgs_integration.create_strategy()
        #     
        #     def next(self):
        #         signal = self.generate_signal()
        #         decision = self.dgs.evaluate(signal)
        #         if decision == 'APPROVE':
        #             self.execute_trade()
        
        return DGSBacktraderStrategy(self.dgs)


class DGSBacktraderStrategy:
    """Backtrader strategy wrapper for DGS"""
    
    def __init__(self, dgs):
        self.dgs = dgs
        self.pending_decisions = {}
    
    async def evaluate(self, data: Dict[str, Any]) -> str:
        """Evaluate market data and return decision"""
        
        signal = {
            'source': 'backtrader_strategy',
            'direction': data.get('direction', 'hold'),
            'confidence': data.get('confidence', 0.5),
            'size': data.get('size', 1.0),
            'timestamp': data.get('datetime'),
            'rationale': data.get('rationale', ''),
            'evidence': data.get('indicators', [])
        }
        
        market_data = {
            'price': data.get('close', 0),
            'volume': data.get('volume', 0),
            'open': data.get('open', 0),
            'high': data.get('high', 0),
            'low': data.get('low', 0)
        }
        
        try:
            from ..core_types import GovernanceDecision
            
            decision, record, _ = await self.dgs.evaluate_trade_signal(
                signal=signal,
                symbol=data.get('symbol', 'UNKNOWN'),
                market_data=market_data
            )
            
            return decision.value
            
        except Exception as e:
            logger.error(f"Backtrader integration error: {e}")
            return "abstain"


class ZiplineIntegration:
    """
    Integration with Zipline algorithmic trading library.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
    
    def create_trading_algorithm(self) -> Callable:
        """Create a Zipline trading algorithm using DGS"""
        
        def initialize(context):
            """Zipline initialize function"""
            context.dgs = self.dgs
            context.pending_orders = {}
        
        def handle_data(context, data):
            """Zipline handle_data function"""
            
            for asset in context.portfolio.positions.keys():
                # Generate signal
                signal = generate_signal_zipline(context, data, asset)
                
                # Evaluate with DGS
                asyncio.run(evaluate_signal_dgs(context.dgs, signal, asset))
        
        return initialize, handle_data


def generate_signal_zipline(context, data, asset) -> Dict:
    """Generate trading signal for Zipline"""
    
    # Example signal generation
    price_history = data.history(asset, 'price', 20, '1d')
    
    if len(price_history) < 20:
        return {'direction': 'hold', 'confidence': 0}
    
    # Simple moving average crossover
    sma_10 = price_history[-10:].mean()
    sma_20 = price_history.mean()
    
    if sma_10 > sma_20 * 1.01:  # 1% buffer
        return {
            'direction': 'buy',
            'confidence': 0.7,
            'rationale': 'SMA10 > SMA20',
            'indicators': [f'SMA10: {sma_10:.2f}', f'SMA20: {sma_20:.2f}']
        }
    elif sma_10 < sma_20 * 0.99:
        return {
            'direction': 'sell',
            'confidence': 0.7,
            'rationale': 'SMA10 < SMA20',
            'indicators': [f'SMA10: {sma_10:.2f}', f'SMA20: {sma_20:.2f}']
        }
    
    return {'direction': 'hold', 'confidence': 0.5}


async def evaluate_signal_dgs(dgs, signal, asset):
    """Evaluate signal using DGS in Zipline context"""
    
    try:
        decision, record, _ = await dgs.evaluate_trade_signal(
            signal=signal,
            symbol=str(asset),
            market_data={}
        )
        
        return decision.value
    except Exception as e:
        logger.error(f"Zipline DGS evaluation error: {e}")
        return "abstain"


class CCXTIntegration:
    """
    Integration with CCXT cryptocurrency trading library.
    """
    
    def __init__(self, dgs_instance, exchange_id: str = 'binance'):
        self.dgs = dgs_instance
        self.exchange_id = exchange_id
    
    async def execute_trade_with_governance(
        self,
        symbol: str,
        side: str,
        amount: float,
        ccxt_exchange: Any
    ) -> Dict[str, Any]:
        """
        Execute trade through CCXT with DGS governance.
        
        Args:
            symbol: Trading pair (e.g., 'BTC/USDT')
            side: 'buy' or 'sell'
            amount: Order size
            ccxt_exchange: CCXT exchange instance
            
        Returns:
            Execution result with governance decision
        """
        
        # Fetch market data
        ticker = await ccxt_exchange.fetch_ticker(symbol)
        orderbook = await ccxt_exchange.fetch_order_book(symbol)
        
        # Create signal
        signal = {
            'source': 'ccxt_trader',
            'direction': side,
            'confidence': 0.7,  # Would come from strategy
            'size': amount,
            'rationale': 'CCXT trading signal'
        }
        
        market_data = {
            'price': ticker['last'],
            'volume': ticker['quoteVolume'],
            'bid': ticker['bid'],
            'ask': ticker['ask'],
            'spread': (ticker['ask'] - ticker['bid']) / ticker['last'] * 10000,
            'order_book': {
                'bids': orderbook['bids'][:5],
                'asks': orderbook['asks'][:5]
            },
            'volatility': self._estimate_volatility(ticker)
        }
        
        # Evaluate with DGS
        from ..core_types import GovernanceDecision
        
        decision, record, metadata = await self.dgs.evaluate_trade_signal(
            signal=signal,
            symbol=symbol,
            market_data=market_data
        )
        
        # Execute if approved
        if decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
            adjusted_size = record.risk_adjusted_size * amount
            
            try:
                order = await ccxt_exchange.create_market_buy_order(
                    symbol, adjusted_size
                ) if side == 'buy' else await ccxt_exchange.create_market_sell_order(
                    symbol, adjusted_size
                )
                
                # Record outcome
                await self.dgs.record_trade_outcome(
                    decision_id=record.id,
                    pnl=0,  # Will be updated later
                    slippage=0,
                    fill_behavior='full',
                    market_context={'exchange': self.exchange_id}
                )
                
                return {
                    'success': True,
                    'governance_decision': decision.value,
                    'adjusted_size': adjusted_size,
                    'order': order
                }
                
            except Exception as e:
                logger.error(f"CCXT execution error: {e}")
                return {
                    'success': False,
                    'governance_decision': decision.value,
                    'error': str(e)
                }
        
        return {
            'success': False,
            'governance_decision': decision.value,
            'reason': record.decision_reasoning
        }
    
    def _estimate_volatility(self, ticker: Dict) -> float:
        """Estimate volatility from ticker data"""
        
        high = ticker.get('high', ticker['last'])
        low = ticker.get('low', ticker['last'])
        
        if high > low:
            return (high - low) / ticker['last']
        
        return 0.02  # Default 2%


class IBIntegration:
    """
    Integration with Interactive Brokers API.
    """
    
    def __init__(self, dgs_instance, host: str = '127.0.0.1', port: int = 7497):
        self.dgs = dgs_instance
        self.host = host
        self.port = port
    
    async def submit_order_with_governance(
        self,
        contract: Any,  # IB contract
        action: str,  # 'BUY' or 'SELL'
        quantity: float,
        ib_client: Any
    ) -> Dict[str, Any]:
        """
        Submit order to IB with DGS governance.
        """
        
        # Get market data
        market_data = await self._fetch_ib_market_data(ib_client, contract)
        
        # Create signal
        signal = {
            'source': 'ib_trader',
            'direction': action.lower(),
            'confidence': 0.75,
            'size': quantity,
            'rationale': 'IB trading signal'
        }
        
        symbol = contract.symbol if hasattr(contract, 'symbol') else str(contract)
        
        # Evaluate with DGS
        from ..core_types import GovernanceDecision
        
        decision, record, metadata = await self.dgs.evaluate_trade_signal(
            signal=signal,
            symbol=symbol,
            market_data=market_data
        )
        
        if decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
            adjusted_quantity = int(record.risk_adjusted_size * quantity)
            
            if adjusted_quantity > 0:
                # Create IB order
                order = self._create_ib_order(action, adjusted_quantity)
                
                # Submit order
                trade = ib_client.placeOrder(contract, order)
                
                return {
                    'success': True,
                    'governance_decision': decision.value,
                    'adjusted_quantity': adjusted_quantity,
                    'trade': trade
                }
        
        return {
            'success': False,
            'governance_decision': decision.value,
            'reason': record.decision_reasoning
        }
    
    async def _fetch_ib_market_data(
        self,
        ib_client: Any,
        contract: Any
    ) -> Dict[str, Any]:
        """Fetch market data from IB"""
        
        # Qualify contract
        qualified_contracts = ib_client.reqContractDetails(contract)
        
        if qualified_contracts:
            qc = qualified_contracts[0]
            
            return {
                'price': 0,  # Would get from market data
                'volume': 0,
                'bid': 0,
                'ask': 0,
                'min_tick': qc.minTick,
                'market_name': qc.marketName
            }
        
        return {}
    
    def _create_ib_order(self, action: str, quantity: int) -> Any:
        """Create IB order object"""
        
        # This would use ib_insync MarketOrder
        # from ib_insync import MarketOrder
        # return MarketOrder(action, quantity)
        
        return {'action': action, 'quantity': quantity}


class AlpacaIntegration:
    """
    Integration with Alpaca trading API.
    """
    
    def __init__(self, dgs_instance, api_key: str, secret_key: str):
        self.dgs = dgs_instance
        self.api_key = api_key
        self.secret_key = secret_key
    
    async def submit_order_with_governance(
        self,
        symbol: str,
        side: str,
        qty: float,
        alpaca_api: Any
    ) -> Dict[str, Any]:
        """
        Submit order to Alpaca with DGS governance.
        """
        
        # Get account and position info
        account = alpaca_api.get_account()
        positions = alpaca_api.list_positions()
        
        # Calculate portfolio context
        portfolio_value = float(account.portfolio_value)
        current_position = next(
            (p for p in positions if p.symbol == symbol),
            None
        )
        
        # Get market data
        bars = alpaca_api.get_bars(symbol, '1Min', limit=10)
        
        market_data = {
            'price': bars[-1].close if bars else 0,
            'volume': bars[-1].volume if bars else 0,
            'portfolio_value': portfolio_value,
            'current_position': float(current_position.qty) if current_position else 0
        }
        
        # Create signal
        signal = {
            'source': 'alpaca_trader',
            'direction': side,
            'confidence': 0.7,
            'size': qty,
            'rationale': 'Alpaca trading signal'
        }
        
        # Evaluate with DGS
        from ..core_types import GovernanceDecision
        
        decision, record, metadata = await self.dgs.evaluate_trade_signal(
            signal=signal,
            symbol=symbol,
            market_data=market_data
        )
        
        if decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
            adjusted_qty = record.risk_adjusted_size * qty
            
            # Submit order
            order = alpaca_api.submit_order(
                symbol=symbol,
                qty=adjusted_qty,
                side=side,
                type='market',
                time_in_force='day'
            )
            
            return {
                'success': True,
                'governance_decision': decision.value,
                'adjusted_qty': adjusted_qty,
                'order': order
            }
        
        return {
            'success': False,
            'governance_decision': decision.value,
            'reason': record.decision_reasoning
        }


class CustomIntegrationTemplate:
    """
    Template for creating custom trading framework integrations.
    """
    
    def __init__(self, dgs_instance):
        self.dgs = dgs_instance
        self.setup()
    
    def setup(self):
        """Override this to perform setup"""
        pass
    
    def create_signal_from_framework_data(
        self,
        framework_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Convert framework-specific data to DGS signal format.
        
        Override this method for your framework.
        """
        
        return {
            'source': 'custom_framework',
            'direction': framework_data.get('signal_direction', 'hold'),
            'confidence': framework_data.get('confidence', 0.5),
            'size': framework_data.get('position_size', 1.0),
            'timestamp': framework_data.get('timestamp'),
            'rationale': framework_data.get('strategy_rationale', ''),
            'evidence': framework_data.get('indicators', []),
            'assumptions': framework_data.get('assumptions', []),
            'invalidation_conditions': framework_data.get('exit_conditions', [])
        }
    
    async def execute_with_governance(
        self,
        symbol: str,
        framework_signal: Dict[str, Any],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute trade with DGS governance.
        
        This is the main integration point.
        """
        
        # Convert to DGS signal
        signal = self.create_signal_from_framework_data(framework_signal)
        
        # Evaluate
        decision, record, metadata = await self.dgs.evaluate_trade_signal(
            signal=signal,
            symbol=symbol,
            market_data=market_data
        )
        
        # Execute if approved
        from ..core_types import GovernanceDecision
        
        if decision in [GovernanceDecision.APPROVE, GovernanceDecision.RESIZE]:
            # Execute through your framework
            execution_result = await self.execute_through_framework(
                symbol=symbol,
                side=signal['direction'],
                size=record.risk_adjusted_size * signal['size'],
                decision_record=record
            )
            
            return {
                'success': execution_result.get('success', False),
                'governance_decision': decision.value,
                'decision_id': record.id,
                'execution': execution_result
            }
        
        return {
            'success': False,
            'governance_decision': decision.value,
            'decision_id': record.id,
            'reason': record.decision_reasoning
        }
    
    async def execute_through_framework(
        self,
        symbol: str,
        side: str,
        size: float,
        decision_record: Any
    ) -> Dict[str, Any]:
        """
        Execute trade through your specific framework.
        
        Override this method to implement framework-specific execution.
        """
        
        # Placeholder - implement for your framework
        logger.info(f"Would execute {side} {size} {symbol}")
        
        return {'success': True, 'symbol': symbol, 'side': side, 'size': size}
    
    async def record_outcome(
        self,
        decision_id: str,
        framework_execution_result: Dict[str, Any]
    ) -> None:
        """
        Record trade outcome from framework execution.
        
        Call this after trade completion.
        """
        
        pnl = framework_execution_result.get('pnl', 0)
        slippage = framework_execution_result.get('slippage', 0)
        
        await self.dgs.record_trade_outcome(
            decision_id=decision_id,
            pnl=pnl,
            slippage=slippage,
            fill_behavior=framework_execution_result.get('fill_type', 'full'),
            market_context=framework_execution_result.get('market_context', {})
        )
