"""
AADS MODULE 5 — ALPHAEVOLVE: Code Evolution Engine

Inspired by Google DeepMind's AlphaEvolve. The system does not just tune
parameters — it writes new signal logic as code, tests it, and evolves
the code itself across generations.

Program Synthesis Loop:
1. LLM generates Python signal functions
2. Evolutionary algorithm selects, mutates, and improves the code
3. Best code gets compiled and deployed as live signal

Code Mutation Operators:
- Feature mutation: replace one technical indicator with a novel combination
- Regime conditioning: add regime filter that wasn't in parent
- Lag exploration: try different lookback windows
- Cross-asset transfer: adapt a signal from one asset class to another
- Ensemble injection: combine two underperforming signals into one
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Tuple
from datetime import datetime
from enum import Enum
import uuid
import logging
import hashlib
import ast
import textwrap
import re

logger = logging.getLogger(__name__)


class MutationType(Enum):
    """Types of code mutations"""
    FEATURE_MUTATION = "feature_mutation"
    REGIME_CONDITIONING = "regime_conditioning"
    LAG_EXPLORATION = "lag_exploration"
    CROSS_ASSET_TRANSFER = "cross_asset_transfer"
    ENSEMBLE_INJECTION = "ensemble_injection"
    PARAMETER_TWEAK = "parameter_tweak"
    LOGIC_INVERSION = "logic_inversion"


class SignalStatus(Enum):
    """Status of an evolved signal"""
    CANDIDATE = "candidate"
    TESTING = "testing"
    VALIDATED = "validated"
    DEPLOYED = "deployed"
    RETIRED = "retired"
    REJECTED = "rejected"


@dataclass
class EvolvedSignal:
    """An evolved signal with its code and metadata"""
    signal_id: str
    code: str
    function_name: str
    generation: int
    parent_id: Optional[str]
    mutation_type: Optional[MutationType]
    
    # Performance metrics
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_return: float = 0.0
    
    # Validation
    is_safe: bool = False
    is_vectorized: bool = False
    has_lookahead: bool = False
    
    # Status
    status: SignalStatus = SignalStatus.CANDIDATE
    created_at: datetime = field(default_factory=datetime.now)
    
    # Lineage
    rejection_reason: Optional[str] = None
    improvement_pct: float = 0.0
    
    def get_code_hash(self) -> str:
        """Get hash of the code for deduplication"""
        return hashlib.sha256(self.code.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'function_name': self.function_name,
            'generation': self.generation,
            'parent_id': self.parent_id,
            'mutation_type': self.mutation_type.value if self.mutation_type else None,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'status': self.status.value,
            'is_safe': self.is_safe,
            'code_hash': self.get_code_hash()
        }


@dataclass
class EvolutionContext:
    """Context provided to the LLM for signal generation"""
    regime: str  # "bull", "bear", "high_vol", "low_vol"
    asset_class: str  # "equity", "crypto", "forex", "commodity"
    timeframe: str  # "intraday", "daily", "weekly"
    available_features: List[str]
    previous_best_code: Optional[str] = None
    previous_best_sharpe: float = 0.0
    rejection_history: List[Dict[str, str]] = field(default_factory=list)


class CodeSafetyChecker:
    """
    Validates generated code for safety before execution.
    
    Checks for:
    - No dangerous imports
    - No file/network operations
    - No exec/eval
    - Proper function signature
    - Vectorized operations
    - No lookahead bias
    """
    
    FORBIDDEN_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'requests', 'urllib',
        'pickle', 'shelve', 'sqlite3', 'shutil', 'pathlib',
        '__builtins__', 'builtins', 'importlib'
    }
    
    FORBIDDEN_CALLS = {
        'exec', 'eval', 'compile', 'open', 'input', '__import__',
        'getattr', 'setattr', 'delattr', 'globals', 'locals'
    }
    
    ALLOWED_IMPORTS = {
        'numpy', 'np', 'pandas', 'pd', 'math', 'statistics',
        'scipy', 'sklearn', 'ta', 'talib'
    }
    
    def check(self, code: str) -> Tuple[bool, List[str]]:
        """Check code safety, return (is_safe, errors)"""
        errors = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]
        
        # Check imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] in self.FORBIDDEN_IMPORTS:
                        errors.append(f"Forbidden import: {alias.name}")
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in self.FORBIDDEN_IMPORTS:
                    errors.append(f"Forbidden import from: {node.module}")
            
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.FORBIDDEN_CALLS:
                        errors.append(f"Forbidden call: {node.func.id}")
        
        # Check function signature
        func_defs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        if not func_defs:
            errors.append("No function definition found")
        else:
            func = func_defs[0]
            args = [a.arg for a in func.args.args]
            if 'data' not in args and 'df' not in args:
                errors.append("Function must accept 'data' or 'df' parameter")
        
        return len(errors) == 0, errors
    
    def check_vectorization(self, code: str) -> bool:
        """Check if code uses vectorized operations"""
        # Look for loop patterns that suggest non-vectorized code
        loop_patterns = [
            r'for\s+\w+\s+in\s+range\s*\(',
            r'for\s+i\s*,',
            r'\.iterrows\(\)',
            r'\.itertuples\(\)',
            r'while\s+',
        ]
        
        for pattern in loop_patterns:
            if re.search(pattern, code):
                return False
        
        return True
    
    def check_lookahead(self, code: str) -> bool:
        """Check for potential lookahead bias"""
        # Look for patterns that might indicate lookahead
        lookahead_patterns = [
            r'\.shift\s*\(\s*-',  # Negative shift
            r'\.iloc\s*\[\s*\d+\s*:\s*\]',  # Forward slicing
            r'future',  # Variable names suggesting future data
        ]
        
        for pattern in lookahead_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                return True
        
        return False


class AlphaEvolveEngine:
    """
    LLM-driven code evolution engine for signal generation.
    
    Generates Python signal functions, tests them, and evolves
    the code itself across generations.
    """
    
    SYSTEM_PROMPT = """You are a quantitative researcher writing Python signal functions.
Given: current market context, past signal code, performance metrics.
Task: write ONE improved signal function.

Rules:
- Function signature: def signal(data: pd.DataFrame) -> pd.Series
- Returns values in [-1, 1] (short to long)
- No lookahead: only use data available at each timestamp
- Must be vectorized (no loops over rows)
- Include docstring explaining the alpha intuition
- Use only: numpy, pandas, math, scipy, sklearn, ta

Previous best signal (Sharpe {previous_sharpe:.2f}):
{previous_best_code}

Rejection history (signals that failed):
{rejection_history}

Market regime context:
{regime_context}

Write a better signal:
"""
    
    MUTATION_PROMPTS = {
        MutationType.FEATURE_MUTATION: """
Mutate this signal by replacing one technical indicator with a novel combination.
Keep the core logic but use different features.

Original signal:
{code}

Write the mutated signal:
""",
        MutationType.REGIME_CONDITIONING: """
Add a regime filter to this signal that wasn't in the original.
The signal should behave differently in different market regimes.

Original signal:
{code}

Write the regime-conditioned signal:
""",
        MutationType.LAG_EXPLORATION: """
Modify this signal to explore different lookback windows.
Try a different time horizon that might capture the alpha better.

Original signal:
{code}

Write the signal with modified lookback:
""",
        MutationType.CROSS_ASSET_TRANSFER: """
Adapt this signal from {source_asset} to work on {target_asset}.
Adjust parameters and logic for the new asset class.

Original signal:
{code}

Write the adapted signal:
""",
        MutationType.ENSEMBLE_INJECTION: """
Combine these two signals into one ensemble signal.
Use intelligent weighting based on regime or confidence.

Signal A:
{code_a}

Signal B:
{code_b}

Write the ensemble signal:
"""
    }
    
    def __init__(self, llm_client: Optional[Any] = None):
        self.llm_client = llm_client
        self.safety_checker = CodeSafetyChecker()
        
        self.signals: Dict[str, EvolvedSignal] = {}
        self.generation = 0
        self.best_signal: Optional[EvolvedSignal] = None
        self.rejection_history: List[Dict[str, str]] = []
        
        # Seed signals
        self._initialize_seed_signals()
        
        logger.info("AlphaEvolveEngine initialized")
    
    def _initialize_seed_signals(self) -> None:
        """Initialize with seed signal templates"""
        
        seed_signals = [
            # Momentum signal
            """
def signal_momentum(data: pd.DataFrame) -> pd.Series:
    \"\"\"
    Momentum signal based on price returns.
    Long when recent returns are positive, short when negative.
    \"\"\"
    returns = data['close'].pct_change(20)
    signal = returns / returns.rolling(60).std()
    return signal.clip(-1, 1)
""",
            # Mean reversion signal
            """
def signal_mean_reversion(data: pd.DataFrame) -> pd.Series:
    \"\"\"
    Mean reversion signal based on z-score.
    Long when price is below mean, short when above.
    \"\"\"
    ma = data['close'].rolling(20).mean()
    std = data['close'].rolling(20).std()
    zscore = (data['close'] - ma) / std
    return (-zscore / 3).clip(-1, 1)
""",
            # Volume breakout signal
            """
def signal_volume_breakout(data: pd.DataFrame) -> pd.Series:
    \"\"\"
    Volume breakout signal.
    Long on high volume up moves, short on high volume down moves.
    \"\"\"
    vol_ratio = data['volume'] / data['volume'].rolling(20).mean()
    price_change = data['close'].pct_change()
    signal = np.sign(price_change) * (vol_ratio - 1)
    return signal.clip(-1, 1)
""",
            # RSI signal
            """
def signal_rsi(data: pd.DataFrame) -> pd.Series:
    \"\"\"
    RSI-based signal.
    Long when oversold, short when overbought.
    \"\"\"
    delta = data['close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    signal = (50 - rsi) / 50
    return signal.clip(-1, 1)
"""
        ]
        
        for i, code in enumerate(seed_signals):
            signal = EvolvedSignal(
                signal_id=str(uuid.uuid4()),
                code=textwrap.dedent(code).strip(),
                function_name=f"seed_signal_{i}",
                generation=0,
                parent_id=None,
                mutation_type=None,
                status=SignalStatus.VALIDATED
            )
            self.signals[signal.signal_id] = signal
        
        logger.info(f"Initialized {len(seed_signals)} seed signals")
    
    def generate_signal(self, context: EvolutionContext) -> Optional[EvolvedSignal]:
        """
        Generate a new signal using LLM.
        
        If no LLM client is available, uses template-based generation.
        """
        
        # Format prompt
        prompt = self.SYSTEM_PROMPT.format(
            previous_sharpe=context.previous_best_sharpe,
            previous_best_code=context.previous_best_code or "None",
            rejection_history=self._format_rejections(context.rejection_history[-5:]),
            regime_context=f"Regime: {context.regime}, Asset: {context.asset_class}, Timeframe: {context.timeframe}"
        )
        
        # Generate code
        if self.llm_client:
            try:
                code = self._call_llm(prompt)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                code = self._template_generate(context)
        else:
            code = self._template_generate(context)
        
        if not code:
            return None
        
        # Safety check
        is_safe, errors = self.safety_checker.check(code)
        if not is_safe:
            logger.warning(f"Generated code failed safety check: {errors}")
            self.rejection_history.append({
                "code": code[:200],
                "reason": "; ".join(errors)
            })
            return None
        
        # Create signal
        signal = EvolvedSignal(
            signal_id=str(uuid.uuid4()),
            code=code,
            function_name=self._extract_function_name(code),
            generation=self.generation + 1,
            parent_id=self.best_signal.signal_id if self.best_signal else None,
            mutation_type=None,
            is_safe=True,
            is_vectorized=self.safety_checker.check_vectorization(code),
            has_lookahead=self.safety_checker.check_lookahead(code)
        )
        
        if signal.has_lookahead:
            signal.status = SignalStatus.REJECTED
            signal.rejection_reason = "Potential lookahead bias detected"
            self.rejection_history.append({
                "code": code[:200],
                "reason": "Lookahead bias"
            })
            return None
        
        self.signals[signal.signal_id] = signal
        return signal
    
    def mutate_signal(
        self,
        signal: EvolvedSignal,
        mutation_type: MutationType,
        **kwargs
    ) -> Optional[EvolvedSignal]:
        """Apply a specific mutation to a signal"""
        
        prompt_template = self.MUTATION_PROMPTS.get(mutation_type)
        if not prompt_template:
            return None
        
        # Format prompt based on mutation type
        if mutation_type == MutationType.CROSS_ASSET_TRANSFER:
            prompt = prompt_template.format(
                code=signal.code,
                source_asset=kwargs.get("source_asset", "equity"),
                target_asset=kwargs.get("target_asset", "crypto")
            )
        elif mutation_type == MutationType.ENSEMBLE_INJECTION:
            signal_b = kwargs.get("signal_b")
            if not signal_b:
                return None
            prompt = prompt_template.format(
                code_a=signal.code,
                code_b=signal_b.code
            )
        else:
            prompt = prompt_template.format(code=signal.code)
        
        # Generate mutated code
        if self.llm_client:
            try:
                code = self._call_llm(prompt)
            except Exception as e:
                logger.error(f"LLM mutation failed: {e}")
                code = self._template_mutate(signal, mutation_type)
        else:
            code = self._template_mutate(signal, mutation_type)
        
        if not code:
            return None
        
        # Safety check
        is_safe, errors = self.safety_checker.check(code)
        if not is_safe:
            return None
        
        # Create mutated signal
        mutated = EvolvedSignal(
            signal_id=str(uuid.uuid4()),
            code=code,
            function_name=self._extract_function_name(code),
            generation=signal.generation + 1,
            parent_id=signal.signal_id,
            mutation_type=mutation_type,
            is_safe=True,
            is_vectorized=self.safety_checker.check_vectorization(code),
            has_lookahead=self.safety_checker.check_lookahead(code)
        )
        
        if mutated.has_lookahead:
            return None
        
        self.signals[mutated.signal_id] = mutated
        return mutated
    
    def evaluate_signal(
        self,
        signal: EvolvedSignal,
        backtest_fn: Callable[[str], Dict[str, float]]
    ) -> bool:
        """
        Evaluate a signal using the provided backtest function.
        
        Returns True if signal passes validation gates.
        """
        
        try:
            results = backtest_fn(signal.code)
            
            signal.sharpe_ratio = results.get("sharpe_ratio", 0)
            signal.max_drawdown = results.get("max_drawdown", 0)
            signal.win_rate = results.get("win_rate", 0)
            signal.total_return = results.get("total_return", 0)
            
            # Validation gates
            passes = (
                signal.sharpe_ratio > 1.0 and
                abs(signal.max_drawdown) < 0.15 and
                signal.win_rate > 0.50
            )
            
            if passes:
                signal.status = SignalStatus.VALIDATED
                
                # Check if better than current best
                if self.best_signal is None or signal.sharpe_ratio > self.best_signal.sharpe_ratio:
                    signal.improvement_pct = (
                        (signal.sharpe_ratio - self.best_signal.sharpe_ratio) / self.best_signal.sharpe_ratio
                        if self.best_signal and self.best_signal.sharpe_ratio > 0
                        else 1.0
                    )
                    self.best_signal = signal
                    logger.info(f"New best signal: {signal.signal_id[:8]} Sharpe={signal.sharpe_ratio:.2f}")
            else:
                signal.status = SignalStatus.REJECTED
                signal.rejection_reason = f"Failed gates: Sharpe={signal.sharpe_ratio:.2f}, DD={signal.max_drawdown:.2%}, WR={signal.win_rate:.2%}"
                self.rejection_history.append({
                    "code": signal.code[:200],
                    "reason": signal.rejection_reason
                })
            
            return passes
            
        except Exception as e:
            signal.status = SignalStatus.REJECTED
            signal.rejection_reason = f"Backtest error: {str(e)}"
            return False
    
    def evolve_generation(
        self,
        context: EvolutionContext,
        backtest_fn: Callable[[str], Dict[str, float]],
        population_size: int = 10
    ) -> List[EvolvedSignal]:
        """
        Evolve one generation of signals.
        
        1. Generate new signals
        2. Mutate existing signals
        3. Evaluate all candidates
        4. Select survivors
        """
        
        self.generation += 1
        candidates = []
        
        # Update context with best signal info
        if self.best_signal:
            context.previous_best_code = self.best_signal.code
            context.previous_best_sharpe = self.best_signal.sharpe_ratio
        context.rejection_history = self.rejection_history[-10:]
        
        # Generate new signals
        for _ in range(population_size // 2):
            signal = self.generate_signal(context)
            if signal:
                candidates.append(signal)
        
        # Mutate existing signals
        validated_signals = [
            s for s in self.signals.values()
            if s.status == SignalStatus.VALIDATED
        ]
        
        if validated_signals:
            for mutation_type in [
                MutationType.FEATURE_MUTATION,
                MutationType.LAG_EXPLORATION,
                MutationType.REGIME_CONDITIONING
            ]:
                parent = validated_signals[self.generation % len(validated_signals)]
                mutated = self.mutate_signal(parent, mutation_type)
                if mutated:
                    candidates.append(mutated)
        
        # Evaluate all candidates
        validated = []
        for candidate in candidates:
            if self.evaluate_signal(candidate, backtest_fn):
                validated.append(candidate)
        
        logger.info(f"Generation {self.generation}: {len(candidates)} candidates, {len(validated)} validated")
        
        return validated
    
    def deploy_best_signal(self) -> Optional[EvolvedSignal]:
        """Deploy the best validated signal"""
        if self.best_signal and self.best_signal.status == SignalStatus.VALIDATED:
            self.best_signal.status = SignalStatus.DEPLOYED
            logger.info(f"Deployed signal: {self.best_signal.signal_id[:8]}")
            return self.best_signal
        return None
    
    def compile_signal(self, signal: EvolvedSignal) -> Optional[Callable]:
        """Compile signal code into executable function"""
        
        if not signal.is_safe:
            return None
        
        try:
            # Create isolated namespace
            namespace = {
                'np': __import__('numpy'),
                'pd': __import__('pandas'),
                'math': __import__('math'),
            }
            
            exec(signal.code, namespace)
            
            # Find the function
            func_name = signal.function_name
            if func_name in namespace:
                return namespace[func_name]
            
            # Try to find any function
            for name, obj in namespace.items():
                if callable(obj) and not name.startswith('_'):
                    return obj
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to compile signal: {e}")
            return None
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM to generate code"""
        if self.llm_client:
            response = self.llm_client.generate(prompt)
            # Extract code from response
            code = self._extract_code(response)
            return code
        return ""
    
    def _template_generate(self, context: EvolutionContext) -> str:
        """Template-based signal generation (fallback when no LLM)"""
        
        templates = {
            "bull": """
def signal_bull_momentum(data: pd.DataFrame) -> pd.Series:
    \"\"\"Bull market momentum signal.\"\"\"
    fast_ma = data['close'].rolling(10).mean()
    slow_ma = data['close'].rolling(30).mean()
    signal = (fast_ma - slow_ma) / slow_ma
    return signal.clip(-1, 1)
""",
            "bear": """
def signal_bear_defensive(data: pd.DataFrame) -> pd.Series:
    \"\"\"Bear market defensive signal.\"\"\"
    vol = data['close'].pct_change().rolling(20).std()
    vol_ma = vol.rolling(60).mean()
    signal = -(vol - vol_ma) / vol_ma
    return signal.clip(-1, 1)
""",
            "high_vol": """
def signal_vol_regime(data: pd.DataFrame) -> pd.Series:
    \"\"\"High volatility regime signal.\"\"\"
    returns = data['close'].pct_change()
    vol = returns.rolling(10).std()
    signal = -returns / vol
    return signal.clip(-1, 1)
"""
        }
        
        return textwrap.dedent(templates.get(context.regime, templates["bull"])).strip()
    
    def _template_mutate(self, signal: EvolvedSignal, mutation_type: MutationType) -> str:
        """Template-based mutation (fallback when no LLM)"""
        
        code = signal.code
        
        if mutation_type == MutationType.LAG_EXPLORATION:
            # Change lookback windows
            code = re.sub(r'rolling\((\d+)\)', lambda m: f'rolling({int(m.group(1)) * 2})', code)
        
        elif mutation_type == MutationType.FEATURE_MUTATION:
            # Swap indicators
            code = code.replace('rolling(20).mean()', 'ewm(span=20).mean()')
        
        elif mutation_type == MutationType.REGIME_CONDITIONING:
            # Add volatility filter
            code = code.replace(
                'return signal.clip(-1, 1)',
                'vol_filter = data["close"].pct_change().rolling(20).std() < 0.03\n    signal = signal.where(vol_filter, 0)\n    return signal.clip(-1, 1)'
            )
        
        return code
    
    def _extract_code(self, response: str) -> str:
        """Extract Python code from LLM response"""
        # Look for code blocks
        code_match = re.search(r'```python\n(.*?)```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # Look for function definition
        func_match = re.search(r'(def signal.*?(?=\ndef |\Z))', response, re.DOTALL)
        if func_match:
            return func_match.group(1).strip()
        
        return response.strip()
    
    def _extract_function_name(self, code: str) -> str:
        """Extract function name from code"""
        match = re.search(r'def\s+(\w+)\s*\(', code)
        if match:
            return match.group(1)
        return "unknown_signal"
    
    def _format_rejections(self, rejections: List[Dict[str, str]]) -> str:
        """Format rejection history for prompt"""
        if not rejections:
            return "None"
        
        lines = []
        for r in rejections:
            lines.append(f"- {r.get('reason', 'Unknown')}")
        return "\n".join(lines)
    
    def get_evolution_stats(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            'generation': self.generation,
            'total_signals': len(self.signals),
            'validated_signals': sum(1 for s in self.signals.values() if s.status == SignalStatus.VALIDATED),
            'deployed_signals': sum(1 for s in self.signals.values() if s.status == SignalStatus.DEPLOYED),
            'rejected_signals': sum(1 for s in self.signals.values() if s.status == SignalStatus.REJECTED),
            'best_signal': self.best_signal.to_dict() if self.best_signal else None,
            'rejection_count': len(self.rejection_history)
        }


# Singleton instance
_alpha_evolve_engine: Optional[AlphaEvolveEngine] = None


def get_alpha_evolve_engine() -> AlphaEvolveEngine:
    """Get the global AlphaEvolve engine instance"""
    global _alpha_evolve_engine
    if _alpha_evolve_engine is None:
        _alpha_evolve_engine = AlphaEvolveEngine()
    return _alpha_evolve_engine
