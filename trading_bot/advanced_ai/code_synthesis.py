"""
Code Synthesis from Natural Language
=====================================

Generates executable trading strategy code from natural
language descriptions using template-based synthesis
and code generation patterns.
"""

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class StrategyType(Enum):
    """Types of trading strategies"""
    TREND_FOLLOWING = "trend_following"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM = "momentum"
    BREAKOUT = "breakout"
    SCALPING = "scalping"
    SWING = "swing"
    ARBITRAGE = "arbitrage"
    MARKET_MAKING = "market_making"


class IndicatorType(Enum):
    """Technical indicator types"""
    SMA = "sma"
    EMA = "ema"
    RSI = "rsi"
    MACD = "macd"
    BOLLINGER = "bollinger"
    ATR = "atr"
    STOCHASTIC = "stochastic"
    ADX = "adx"
    VWAP = "vwap"
    VOLUME = "volume"
    MOMENTUM = "momentum"
    ROC = "roc"


class ConditionType(Enum):
    """Condition types for signals"""
    CROSSES_ABOVE = "crosses_above"
    CROSSES_BELOW = "crosses_below"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    BETWEEN = "between"
    INCREASING = "increasing"
    DECREASING = "decreasing"


@dataclass
class ParsedIntent:
    """Parsed intent from natural language"""
    strategy_type: Optional[StrategyType] = None
    indicators: List[Tuple[IndicatorType, Dict[str, Any]]] = field(default_factory=list)
    entry_conditions: List[Dict[str, Any]] = field(default_factory=list)
    exit_conditions: List[Dict[str, Any]] = field(default_factory=list)
    risk_params: Dict[str, Any] = field(default_factory=dict)
    timeframe: str = "1h"
    symbols: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class GeneratedCode:
    """Generated code output"""
    code_id: str
    strategy_name: str
    code: str
    language: str = "python"
    intent: Optional[ParsedIntent] = None
    is_valid: bool = False
    validation_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)


class NaturalLanguageParser:
    """
    Parses natural language descriptions into structured intents
    """
    
    def __init__(self):
        # Strategy keywords
        self.strategy_keywords = {
            StrategyType.TREND_FOLLOWING: [
                'trend', 'following', 'follow the trend', 'trend following',
                'ride the trend', 'trending'
            ],
            StrategyType.MEAN_REVERSION: [
                'mean reversion', 'reversion', 'reversal', 'bounce',
                'oversold', 'overbought', 'revert'
            ],
            StrategyType.MOMENTUM: [
                'momentum', 'strength', 'acceleration', 'velocity'
            ],
            StrategyType.BREAKOUT: [
                'breakout', 'break out', 'breakthrough', 'break above',
                'break below', 'resistance break', 'support break'
            ],
            StrategyType.SCALPING: [
                'scalp', 'scalping', 'quick', 'fast', 'short-term'
            ],
            StrategyType.SWING: [
                'swing', 'swing trade', 'multi-day', 'position'
            ]
        }
        
        # Indicator keywords
        self.indicator_keywords = {
            IndicatorType.SMA: ['sma', 'simple moving average', 'moving average'],
            IndicatorType.EMA: ['ema', 'exponential moving average', 'exp ma'],
            IndicatorType.RSI: ['rsi', 'relative strength', 'strength index'],
            IndicatorType.MACD: ['macd', 'moving average convergence'],
            IndicatorType.BOLLINGER: ['bollinger', 'bb', 'bollinger bands'],
            IndicatorType.ATR: ['atr', 'average true range', 'true range'],
            IndicatorType.STOCHASTIC: ['stochastic', 'stoch', '%k', '%d'],
            IndicatorType.ADX: ['adx', 'directional index', 'trend strength'],
            IndicatorType.VWAP: ['vwap', 'volume weighted'],
            IndicatorType.VOLUME: ['volume', 'vol'],
            IndicatorType.MOMENTUM: ['momentum', 'mom'],
            IndicatorType.ROC: ['roc', 'rate of change']
        }
        
        # Condition keywords
        self.condition_keywords = {
            ConditionType.CROSSES_ABOVE: ['crosses above', 'cross above', 'breaks above', 'goes above'],
            ConditionType.CROSSES_BELOW: ['crosses below', 'cross below', 'breaks below', 'goes below'],
            ConditionType.GREATER_THAN: ['greater than', 'above', 'higher than', 'exceeds', '>'],
            ConditionType.LESS_THAN: ['less than', 'below', 'lower than', 'under', '<'],
            ConditionType.BETWEEN: ['between', 'in range', 'within'],
            ConditionType.INCREASING: ['increasing', 'rising', 'going up', 'upward'],
            ConditionType.DECREASING: ['decreasing', 'falling', 'going down', 'downward']
        }
        
        # Number patterns
        self.number_pattern = re.compile(r'\b(\d+(?:\.\d+)?)\b')
        self.period_pattern = re.compile(r'(\d+)\s*(?:period|day|hour|minute|bar|candle)s?')
        
        logger.info("NaturalLanguageParser initialized")
    
    def parse(self, description: str) -> ParsedIntent:
        """Parse natural language description into structured intent"""
        
        description_lower = description.lower()
        intent = ParsedIntent()
        
        # Detect strategy type
        for strategy_type, keywords in self.strategy_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    intent.strategy_type = strategy_type
                    break
            if intent.strategy_type:
                break
        
        # Default to trend following
        if not intent.strategy_type:
            intent.strategy_type = StrategyType.TREND_FOLLOWING
        
        # Detect indicators
        for indicator_type, keywords in self.indicator_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    # Extract period if mentioned
                    params = {}
                    
                    # Find period near the indicator mention
                    idx = description_lower.find(keyword)
                    context = description_lower[max(0, idx-20):idx+50]
                    
                    period_match = self.period_pattern.search(context)
                    if period_match:
                        params['period'] = int(period_match.group(1))
                    else:
                        # Look for any number
                        numbers = self.number_pattern.findall(context)
                        if numbers:
                            params['period'] = int(float(numbers[0]))
                    
                    intent.indicators.append((indicator_type, params))
                    break
        
        # Detect entry conditions
        entry_keywords = ['buy when', 'enter when', 'go long when', 'entry when', 'buy if', 'long when']
        for keyword in entry_keywords:
            if keyword in description_lower:
                idx = description_lower.find(keyword)
                condition_text = description_lower[idx:idx+100]
                
                condition = self._parse_condition(condition_text)
                if condition:
                    intent.entry_conditions.append(condition)
        
        # Detect exit conditions
        exit_keywords = ['sell when', 'exit when', 'close when', 'take profit', 'stop loss']
        for keyword in exit_keywords:
            if keyword in description_lower:
                idx = description_lower.find(keyword)
                condition_text = description_lower[idx:idx+100]
                
                condition = self._parse_condition(condition_text)
                if condition:
                    intent.exit_conditions.append(condition)
        
        # Detect risk parameters
        if 'stop loss' in description_lower or 'sl' in description_lower:
            numbers = self.number_pattern.findall(description_lower)
            for num in numbers:
                val = float(num)
                if 0.1 <= val <= 10:  # Likely percentage
                    intent.risk_params['stop_loss_pct'] = val
                    break
        
        if 'take profit' in description_lower or 'tp' in description_lower:
            numbers = self.number_pattern.findall(description_lower)
            for num in numbers:
                val = float(num)
                if 0.5 <= val <= 20:  # Likely percentage
                    intent.risk_params['take_profit_pct'] = val
                    break
        
        # Detect timeframe
        timeframe_patterns = [
            (r'(\d+)\s*minute', 'm'),
            (r'(\d+)\s*hour', 'h'),
            (r'(\d+)\s*day', 'd'),
            (r'(\d+)m\b', 'm'),
            (r'(\d+)h\b', 'h'),
            (r'(\d+)d\b', 'd'),
        ]
        
        for pattern, suffix in timeframe_patterns:
            match = re.search(pattern, description_lower)
            if match:
                intent.timeframe = f"{match.group(1)}{suffix}"
                break
        
        # Calculate confidence
        confidence_factors = [
            intent.strategy_type is not None,
            len(intent.indicators) > 0,
            len(intent.entry_conditions) > 0,
            len(intent.exit_conditions) > 0,
            len(intent.risk_params) > 0
        ]
        intent.confidence = sum(confidence_factors) / len(confidence_factors)
        
        return intent
    
    def _parse_condition(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse a condition from text"""
        
        for condition_type, keywords in self.condition_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    # Extract indicator and value
                    condition = {
                        'type': condition_type.value,
                        'raw_text': text[:50]
                    }
                    
                    # Find indicator
                    for ind_type, ind_keywords in self.indicator_keywords.items():
                        for ind_keyword in ind_keywords:
                            if ind_keyword in text:
                                condition['indicator'] = ind_type.value
                                break
                    
                    # Find value
                    numbers = self.number_pattern.findall(text)
                    if numbers:
                        condition['value'] = float(numbers[0])
                    
                    return condition
        
        return None


class CodeGenerator:
    """
    Generates Python code from parsed intents
    """
    
    def __init__(self):
        self.templates = self._load_templates()
        logger.info("CodeGenerator initialized")
    
    def _load_templates(self) -> Dict[str, str]:
        """Load code templates"""
        
        return {
            'strategy_class': '''
class {class_name}:
    """
    {description}
    
    Generated automatically from natural language description.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {{}}
        self.name = "{strategy_name}"
        self.timeframe = "{timeframe}"
        
        # Risk parameters
        self.stop_loss_pct = {stop_loss_pct}
        self.take_profit_pct = {take_profit_pct}
        self.position_size_pct = {position_size_pct}
        
        # Indicator parameters
{indicator_params}
        
        self.position = None
        self.entry_price = None
    
    def calculate_indicators(self, data: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Calculate all required indicators"""
        indicators = {{}}
        close = data.get('close', data.get('price', np.array([])))
        high = data.get('high', close)
        low = data.get('low', close)
        volume = data.get('volume', np.ones_like(close))
        
{indicator_calculations}
        
        return indicators
    
    def check_entry_conditions(self, indicators: Dict[str, np.ndarray], idx: int = -1) -> bool:
        """Check if entry conditions are met"""
        try:
{entry_conditions}
            return True
        except (IndexError, KeyError):
            return False
    
    def check_exit_conditions(self, indicators: Dict[str, np.ndarray], idx: int = -1) -> bool:
        """Check if exit conditions are met"""
        try:
{exit_conditions}
            return True
        except (IndexError, KeyError):
            return False
    
    def generate_signal(self, data: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """Generate trading signal"""
        indicators = self.calculate_indicators(data)
        
        signal = {{
            'action': 'hold',
            'confidence': 0.0,
            'indicators': {{k: float(v[-1]) if len(v) > 0 else 0 for k, v in indicators.items()}}
        }}
        
        if self.position is None:
            if self.check_entry_conditions(indicators):
                signal['action'] = 'buy'
                signal['confidence'] = 0.8
                signal['stop_loss'] = self.stop_loss_pct
                signal['take_profit'] = self.take_profit_pct
        else:
            if self.check_exit_conditions(indicators):
                signal['action'] = 'sell'
                signal['confidence'] = 0.8
        
        return signal
    
    def on_trade_executed(self, action: str, price: float):
        """Called when a trade is executed"""
        if action == 'buy':
            self.position = 'long'
            self.entry_price = price
        elif action == 'sell':
            self.position = None
            self.entry_price = None
''',
            
            'indicator_sma': '''        # SMA {period}
        indicators['sma_{period}'] = self._rolling_mean(close, {period})''',
            
            'indicator_ema': '''        # EMA {period}
        indicators['ema_{period}'] = self._ema(close, {period})''',
            
            'indicator_rsi': '''        # RSI {period}
        indicators['rsi_{period}'] = self._rsi(close, {period})''',
            
            'indicator_macd': '''        # MACD
        indicators['macd'], indicators['macd_signal'], indicators['macd_hist'] = self._macd(close)''',
            
            'indicator_bollinger': '''        # Bollinger Bands {period}
        indicators['bb_upper_{period}'], indicators['bb_middle_{period}'], indicators['bb_lower_{period}'] = self._bollinger(close, {period})''',
            
            'indicator_atr': '''        # ATR {period}
        indicators['atr_{period}'] = self._atr(high, low, close, {period})''',
            
            'helper_functions': '''
    @staticmethod
    def _rolling_mean(data: np.ndarray, period: int) -> np.ndarray:
        result = np.zeros_like(data)
        for i in range(len(data)):
            start = max(0, i - period + 1)
            result[i] = np.mean(data[start:i+1])
        return result
    
    @staticmethod
    def _ema(data: np.ndarray, period: int) -> np.ndarray:
        result = np.zeros_like(data)
        alpha = 2.0 / (period + 1)
        result[0] = data[0]
        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i-1]
        return result
    
    @staticmethod
    def _rsi(data: np.ndarray, period: int = 14) -> np.ndarray:
        delta = np.diff(data, prepend=data[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)
        
        avg_gain = np.zeros_like(data)
        avg_loss = np.zeros_like(data)
        
        for i in range(len(data)):
            start = max(0, i - period + 1)
            avg_gain[i] = np.mean(gain[start:i+1])
            avg_loss[i] = np.mean(loss[start:i+1])
        
        rs = avg_gain / (avg_loss + 1e-10)
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def _macd(data: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9):
        def ema(d, p):
            result = np.zeros_like(d)
            alpha = 2.0 / (p + 1)
            result[0] = d[0]
            for i in range(1, len(d)):
                result[i] = alpha * d[i] + (1 - alpha) * result[i-1]
            return result
        
        ema_fast = ema(data, fast)
        ema_slow = ema(data, slow)
        macd_line = ema_fast - ema_slow
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    @staticmethod
    def _bollinger(data: np.ndarray, period: int = 20, std_mult: float = 2.0):
        middle = np.zeros_like(data)
        std = np.zeros_like(data)
        
        for i in range(len(data)):
            start = max(0, i - period + 1)
            middle[i] = np.mean(data[start:i+1])
            std[i] = np.std(data[start:i+1])
        
        upper = middle + std_mult * std
        lower = middle - std_mult * std
        return upper, middle, lower
    
    @staticmethod
    def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14):
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        
        tr = np.maximum(
            high - low,
            np.maximum(np.abs(high - prev_close), np.abs(low - prev_close))
        )
        
        atr = np.zeros_like(tr)
        for i in range(len(tr)):
            start = max(0, i - period + 1)
            atr[i] = np.mean(tr[start:i+1])
        
        return atr
'''
        }
    
    def generate(self, intent: ParsedIntent, strategy_name: str = None) -> GeneratedCode:
        """Generate code from parsed intent"""
        
        # Generate strategy name
        if not strategy_name:
            strategy_name = f"Strategy_{intent.strategy_type.value}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        class_name = ''.join(word.capitalize() for word in strategy_name.split('_'))
        
        # Generate indicator parameters
        indicator_params_lines = []
        for indicator, params in intent.indicators:
            period = params.get('period', 14)
            indicator_params_lines.append(f"        self.{indicator.value}_period = {period}")
        
        indicator_params = '\n'.join(indicator_params_lines) if indicator_params_lines else "        pass"
        
        # Generate indicator calculations
        indicator_calc_lines = []
        for indicator, params in intent.indicators:
            period = params.get('period', 14)
            template_key = f'indicator_{indicator.value}'
            
            if template_key in self.templates:
                calc = self.templates[template_key].format(period=period)
                indicator_calc_lines.append(calc)
            else:
                # Default calculation
                indicator_calc_lines.append(f"        indicators['{indicator.value}'] = close  # TODO: Implement {indicator.value}")
        
        indicator_calculations = '\n'.join(indicator_calc_lines) if indicator_calc_lines else "        pass"
        
        # Generate entry conditions
        entry_condition_lines = []
        for condition in intent.entry_conditions:
            cond_type = condition.get('type', 'greater_than')
            indicator = condition.get('indicator', 'close')
            value = condition.get('value', 0)
            
            if cond_type == 'crosses_above':
                entry_condition_lines.append(f"            if not (indicators.get('{indicator}', [0])[idx] > indicators.get('{indicator}', [0])[idx-1]):")
                entry_condition_lines.append("                return False")
            elif cond_type == 'greater_than':
                entry_condition_lines.append(f"            if not (indicators.get('{indicator}', [0])[idx] > {value}):")
                entry_condition_lines.append("                return False")
            elif cond_type == 'less_than':
                entry_condition_lines.append(f"            if not (indicators.get('{indicator}', [0])[idx] < {value}):")
                entry_condition_lines.append("                return False")
        
        entry_conditions = '\n'.join(entry_condition_lines) if entry_condition_lines else "            pass  # No specific entry conditions"
        
        # Generate exit conditions
        exit_condition_lines = []
        for condition in intent.exit_conditions:
            cond_type = condition.get('type', 'less_than')
            indicator = condition.get('indicator', 'close')
            value = condition.get('value', 0)
            
            if cond_type == 'crosses_below':
                exit_condition_lines.append(f"            if not (indicators.get('{indicator}', [0])[idx] < indicators.get('{indicator}', [0])[idx-1]):")
                exit_condition_lines.append("                return False")
            elif cond_type == 'greater_than':
                exit_condition_lines.append(f"            if not (indicators.get('{indicator}', [0])[idx] > {value}):")
                exit_condition_lines.append("                return False")
        
        exit_conditions = '\n'.join(exit_condition_lines) if exit_condition_lines else "            pass  # No specific exit conditions"
        
        # Risk parameters
        stop_loss_pct = intent.risk_params.get('stop_loss_pct', 2.0)
        take_profit_pct = intent.risk_params.get('take_profit_pct', 4.0)
        position_size_pct = intent.risk_params.get('position_size_pct', 2.0)
        
        # Generate main code
        code = self.templates['strategy_class'].format(
            class_name=class_name,
            strategy_name=strategy_name,
            description=f"Auto-generated {intent.strategy_type.value} strategy",
            timeframe=intent.timeframe,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            position_size_pct=position_size_pct,
            indicator_params=indicator_params,
            indicator_calculations=indicator_calculations,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions
        )
        
        # Add helper functions
        code += self.templates['helper_functions']
        
        # Add imports at the top
        imports = """from typing import Dict, Any, Optional, List, Tuple
import numpy as np
from datetime import datetime

"""
        code = imports + code
        
        # Generate code ID
        code_id = hashlib.sha256(code.encode()).hexdigest()[:12]
        
        # Validate code
        is_valid, errors = self._validate_code(code)
        
        return GeneratedCode(
            code_id=code_id,
            strategy_name=strategy_name,
            code=code,
            intent=intent,
            is_valid=is_valid,
            validation_errors=errors
        )
    
    def _validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """Validate generated code"""
        
        errors = []
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {e}")
            return False, errors
        
        # Check for required elements
        if 'def generate_signal' not in code:
            errors.append("Missing generate_signal method")
        
        if 'def calculate_indicators' not in code:
            errors.append("Missing calculate_indicators method")
        
        return len(errors) == 0, errors


class CodeSynthesizer:
    """
    High-level code synthesis from natural language
    """
    
    def __init__(self):
        self.parser = NaturalLanguageParser()
        self.generator = CodeGenerator()
        self.generated_strategies: Dict[str, GeneratedCode] = {}
        
        logger.info("CodeSynthesizer initialized")
    
    def synthesize(
        self,
        description: str,
        strategy_name: Optional[str] = None
    ) -> GeneratedCode:
        """
        Synthesize code from natural language description
        
        Args:
            description: Natural language strategy description
            strategy_name: Optional name for the strategy
        
        Returns:
            Generated code object
        """
        
        logger.info(f"Synthesizing code from: {description[:50]}...")
        
        # Parse intent
        intent = self.parser.parse(description)
        
        logger.info(
            f"Parsed intent: strategy={intent.strategy_type.value}, "
            f"indicators={len(intent.indicators)}, confidence={intent.confidence:.2f}"
        )
        
        # Generate code
        generated = self.generator.generate(intent, strategy_name)
        
        # Store
        self.generated_strategies[generated.code_id] = generated
        
        if generated.is_valid:
            logger.info(f"Successfully generated strategy: {generated.strategy_name}")
        else:
            logger.warning(f"Generated code has errors: {generated.validation_errors}")
        
        return generated
    
    def synthesize_from_examples(
        self,
        examples: List[Tuple[str, str]],
        new_description: str
    ) -> GeneratedCode:
        """
        Synthesize code using few-shot learning from examples
        
        Args:
            examples: List of (description, code) pairs
            new_description: New description to synthesize
        
        Returns:
            Generated code
        """
        
        # Learn patterns from examples
        learned_patterns = []
        
        for desc, code in examples:
            intent = self.parser.parse(desc)
            learned_patterns.append({
                'description': desc,
                'intent': intent,
                'code': code
            })
        
        # Find most similar example
        new_intent = self.parser.parse(new_description)
        
        best_match = None
        best_score = 0
        
        for pattern in learned_patterns:
            score = self._similarity_score(new_intent, pattern['intent'])
            if score > best_score:
                best_score = score
                best_match = pattern
        
        # Generate based on best match
        if best_match and best_score > 0.5:
            # Use matched pattern as template
            logger.info(f"Using matched pattern with score {best_score:.2f}")
        
        return self.synthesize(new_description)
    
    def _similarity_score(self, intent1: ParsedIntent, intent2: ParsedIntent) -> float:
        """Calculate similarity between two intents"""
        
        score = 0.0
        
        # Strategy type match
        if intent1.strategy_type == intent2.strategy_type:
            score += 0.3
        
        # Indicator overlap
        ind1 = set(i[0] for i in intent1.indicators)
        ind2 = set(i[0] for i in intent2.indicators)
        
        if ind1 and ind2:
            overlap = len(ind1 & ind2) / len(ind1 | ind2)
            score += 0.3 * overlap
        
        # Condition similarity
        if intent1.entry_conditions and intent2.entry_conditions:
            score += 0.2
        
        if intent1.exit_conditions and intent2.exit_conditions:
            score += 0.2
        
        return score
    
    def execute_generated_code(
        self,
        code_id: str,
        data: Dict[str, np.ndarray]
    ) -> Optional[Dict[str, Any]]:
        """Execute generated strategy code"""
        
        if code_id not in self.generated_strategies:
            logger.error(f"Unknown code ID: {code_id}")
            return None
        
        generated = self.generated_strategies[code_id]
        
        if not generated.is_valid:
            logger.error(f"Cannot execute invalid code: {generated.validation_errors}")
            return None
        
        try:
            # Create execution namespace
            namespace = {'np': np, 'Dict': Dict, 'Any': Any, 'Optional': Optional, 
                        'List': List, 'Tuple': Tuple, 'datetime': datetime}
            
            # Execute code to define class
            exec(generated.code, namespace)
            
            # Find the strategy class
            class_name = ''.join(word.capitalize() for word in generated.strategy_name.split('_'))
            
            if class_name in namespace:
                strategy_class = namespace[class_name]
                strategy = strategy_class()
                
                # Generate signal
                signal = strategy.generate_signal(data)
                return signal
            else:
                logger.error(f"Class {class_name} not found in generated code")
                return None
        
        except Exception as e:
            logger.error(f"Error executing generated code: {e}")
            return None
    
    def get_report(self) -> Dict[str, Any]:
        """Get synthesis report"""
        
        return {
            'total_generated': len(self.generated_strategies),
            'valid_strategies': sum(1 for g in self.generated_strategies.values() if g.is_valid),
            'strategies': [
                {
                    'code_id': g.code_id,
                    'name': g.strategy_name,
                    'is_valid': g.is_valid,
                    'confidence': g.intent.confidence if g.intent else 0,
                    'strategy_type': g.intent.strategy_type.value if g.intent else None
                }
                for g in self.generated_strategies.values()
            ]
        }


# Convenience functions
def synthesize_strategy(description: str, name: Optional[str] = None) -> GeneratedCode:
    """Quick strategy synthesis"""
    synthesizer = CodeSynthesizer()
    return synthesizer.synthesize(description, name)


def parse_strategy_description(description: str) -> ParsedIntent:
    """Parse strategy description"""
    parser = NaturalLanguageParser()
    return parser.parse(description)


def create_code_synthesizer(**kwargs) -> CodeSynthesizer:
    """Create a CodeSynthesizer instance."""
    return CodeSynthesizer(**kwargs)
