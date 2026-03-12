"""
Phase 5: Meta-Learning - Self-Rewriting Code
Neural program synthesis for trading strategies
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
import ast
import inspect
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CodeFragment:
    """Code fragment with metadata."""
    code: str
    purpose: str
    performance: float = 0.0
    complexity: float = 0.0
    generation: int = 0


class CodeGenerator(nn.Module):
    """
    Neural program synthesis model.
    Generates trading strategy code.
    """
    
    def __init__(
        self,
        vocab_size: int = 1000,
        embedding_dim: int = 128,
        hidden_dim: int = 256,
        num_layers: int = 4
    ):
        super().__init__()
        
        # Embeddings
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        
        # LSTM for code generation
        self.lstm = nn.LSTM(
            input_size=embedding_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True
        )
        
        # Output layer
        self.output = nn.Linear(hidden_dim, vocab_size)
        
        # Code templates
        self.templates = {
            'strategy': """
def analyze_market(self, data: Dict) -> str:
    \"\"\"
    Analyze market data and generate trading signal.
    \"\"\"
    {analysis_code}
    
    {decision_code}
    
    return signal
""",
            'indicator': """
def calculate_{name}(self, data: np.ndarray) -> float:
    \"\"\"
    Calculate {name} indicator.
    \"\"\"
    {calculation_code}
    
    return value
"""
        }
        
        logger.info("✅ Code Generator initialized")
    
    def forward(
        self,
        x: torch.Tensor,
        hidden: Optional[Tuple[torch.Tensor, torch.Tensor]] = None
    ) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """Forward pass for code generation."""
        # Embed input
        embedded = self.embedding(x)
        
        # LSTM
        output, hidden = self.lstm(embedded, hidden)
        
        # Project to vocabulary
        logits = self.output(output)
        
        return logits, hidden
    
    def generate_strategy(
        self,
        template_vars: Dict[str, str]
    ) -> CodeFragment:
        """Generate complete trading strategy."""
        # Fill template
        code = self.templates['strategy'].format(**template_vars)
        
        # Add metadata
        fragment = CodeFragment(
            code=code,
            purpose="Trading strategy implementation",
            complexity=self._calculate_complexity(code)
        )
        
        return fragment
    
    def generate_indicator(
        self,
        name: str,
        calculation_code: str
    ) -> CodeFragment:
        """Generate technical indicator."""
        code = self.templates['indicator'].format(
            name=name,
            calculation_code=calculation_code
        )
        
        fragment = CodeFragment(
            code=code,
            purpose=f"Technical indicator: {name}",
            complexity=self._calculate_complexity(code)
        )
        
        return fragment
    
    def _calculate_complexity(self, code: str) -> float:
        """Calculate code complexity score."""
        try:
            tree = ast.parse(code)
            
            # Count nodes
            node_count = len([node for node in ast.walk(tree)])
            
            # Count unique operations
            ops = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.operator):
                    ops.add(type(node).__name__)
            
            # Complexity score
            score = node_count * (1 + len(ops) / 10)
            return float(score)
            
        except Exception as e:
            logger.error(f"Error calculating complexity: {e}")
            return 0.0


class SelfRewritingSystem:
    """
    System that can modify its own trading strategies.
    Uses neural program synthesis and evolution.
    """
    
    def __init__(self):
        self.code_generator = CodeGenerator()
        self.code_fragments = []
        self.generation = 0
        
        # Performance tracking
        self.performance_history = []
        
        logger.info("✅ Self-Rewriting System initialized")
    
    def generate_initial_code(self):
        """Generate initial set of code fragments."""
        # Basic strategy
        strategy = self.code_generator.generate_strategy({
            'analysis_code': """
# Calculate indicators
rsi = self.calculate_rsi(data['prices'])
macd = self.calculate_macd(data['prices'])
sma_20 = np.mean(data['prices'][-20:])
sma_50 = np.mean(data['prices'][-50:])
""",
            'decision_code': """
# Make trading decision
if rsi < 30 and macd > 0:
    signal = 'BUY'
elif rsi > 70 and macd < 0:
    signal = 'SELL'
else:
    signal = 'HOLD'
"""
        })
        
        # Technical indicators
        rsi = self.code_generator.generate_indicator(
            'rsi',
            """
# Calculate RSI
delta = np.diff(data)
gains = np.maximum(delta, 0)
losses = -np.minimum(delta, 0)

avg_gain = np.mean(gains[-14:])
avg_loss = np.mean(losses[-14:])

if avg_loss == 0:
    value = 100
else:
    rs = avg_gain / avg_loss
    value = 100 - (100 / (1 + rs))
"""
        )
        
        macd = self.code_generator.generate_indicator(
            'macd',
            """
# Calculate MACD
ema_12 = np.mean(data[-12:])
ema_26 = np.mean(data[-26:])
value = ema_12 - ema_26
"""
        )
        
        # Add to collection
        self.code_fragments.extend([strategy, rsi, macd])
        
        logger.info("📝 Generated initial code fragments:")
        logger.info(f"   Strategy: {len(strategy.code)} chars")
        logger.info(f"   RSI: {len(rsi.code)} chars")
        logger.info(f"   MACD: {len(macd.code)} chars")
    
    def evolve_code(
        self,
        performance_data: Dict[str, float],
        num_generations: int = 10
    ):
        """
        Evolve code based on performance.
        
        Args:
            performance_data: Performance metrics for current code
            num_generations: Number of evolution generations
        """
        logger.info(f"🧬 Evolving code for {num_generations} generations")
        
        for gen in range(num_generations):
            self.generation += 1
            
            # Update performance scores
            for fragment in self.code_fragments:
                if fragment.purpose in performance_data:
                    fragment.performance = performance_data[fragment.purpose]
            
            # Sort by performance
            self.code_fragments.sort(key=lambda x: x.performance, reverse=True)
            
            # Keep best performing fragments
            best_fragments = self.code_fragments[:2]
            
            # Generate variations
            new_fragments = []
            for fragment in best_fragments:
                # Create modified version
                if 'strategy' in fragment.purpose.lower():
                    new_fragment = self._modify_strategy(fragment)
                else:
                    new_fragment = self._modify_indicator(fragment)
                
                new_fragments.append(new_fragment)
            
            # Update collection
            self.code_fragments = best_fragments + new_fragments
            
            # Record statistics
            stats = self._get_generation_stats()
            self.performance_history.append(stats)
            
            logger.info(f"\nGeneration {self.generation}:")
            logger.info(f"Best performance: {stats['best_performance']:.4f}")
            logger.info(f"Avg complexity: {stats['avg_complexity']:.2f}")
            logger.info(f"Fragments: {stats['num_fragments']}")
    
    def _modify_strategy(self, fragment: CodeFragment) -> CodeFragment:
        """Create modified version of strategy."""
        # Add more sophisticated analysis
        template_vars = {
            'analysis_code': """
# Calculate technical indicators
rsi = self.calculate_rsi(data['prices'])
macd = self.calculate_macd(data['prices'])
sma_20 = np.mean(data['prices'][-20:])
sma_50 = np.mean(data['prices'][-50:])

# Calculate volatility
returns = np.diff(np.log(data['prices']))
volatility = np.std(returns) * np.sqrt(252)

# Volume analysis
volume_sma = np.mean(data['volumes'][-20:])
volume_ratio = data['volumes'][-1] / volume_sma
""",
            'decision_code': """
# Multi-factor decision making
signal = 'HOLD'
confidence = 0.0

# Trend following
if sma_20 > sma_50:
    trend = 'UP'
    confidence += 0.3
else:
    trend = 'DOWN'
    confidence += 0.3

# RSI signals
if rsi < 30 and trend == 'UP':
    signal = 'BUY'
    confidence += 0.3
elif rsi > 70 and trend == 'DOWN':
    signal = 'SELL'
    confidence += 0.3

# MACD confirmation
if macd > 0 and signal == 'BUY':
    confidence += 0.2
elif macd < 0 and signal == 'SELL':
    confidence += 0.2

# Volume confirmation
if volume_ratio > 1.5:
    confidence += 0.2

# Risk adjustment
if volatility > 0.02:  # High volatility
    confidence *= 0.8
"""
        }
        
        # Generate new version
        new_fragment = self.code_generator.generate_strategy(template_vars)
        new_fragment.generation = self.generation
        
        return new_fragment
    
    def _modify_indicator(self, fragment: CodeFragment) -> CodeFragment:
        """Create modified version of indicator."""
        if 'rsi' in fragment.purpose.lower():
            # Enhanced RSI
            calculation_code = """
# Enhanced RSI with volume weighting
delta = np.diff(data)
volume = data['volumes'][1:]  # Align with delta

gains = np.maximum(delta, 0) * volume
losses = -np.minimum(delta, 0) * volume

avg_gain = np.mean(gains[-14:])
avg_loss = np.mean(losses[-14:])

if avg_loss == 0:
    value = 100
else:
    rs = avg_gain / avg_loss
    value = 100 - (100 / (1 + rs))

# Add trend adaptation
sma_20 = np.mean(data[-20:])
sma_50 = np.mean(data[-50:])
trend_factor = sma_20 / sma_50

# Adjust RSI based on trend
value = value * trend_factor
"""
            name = 'enhanced_rsi'
            
        else:
            # Enhanced MACD
            calculation_code = """
# Enhanced MACD with adaptive periods
volatility = np.std(np.diff(np.log(data[-30:])))


# Adjust periods based on volatility
fast_period = int(12 * (1 + volatility))
slow_period = int(26 * (1 + volatility))

# Calculate exponential moving averages
fast_ema = data[-fast_period:].ewm(span=fast_period).mean()
slow_ema = data[-slow_period:].ewm(span=slow_period).mean()

# MACD line
value = fast_ema[-1] - slow_ema[-1]

# Add volume weighting
volume_sma = np.mean(data['volumes'][-20:])
volume_factor = data['volumes'][-1] / volume_sma
value = value * volume_factor
"""
            name = 'enhanced_macd'
        
        # Generate new version
        new_fragment = self.code_generator.generate_indicator(
            name,
            calculation_code
        )
        new_fragment.generation = self.generation
        
        return new_fragment
    
    def _get_generation_stats(self) -> Dict:
        """Calculate statistics for current generation."""
        performances = [f.performance for f in self.code_fragments]
        complexities = [f.complexity for f in self.code_fragments]
        
        return {
            'generation': self.generation,
            'best_performance': max(performances),
            'avg_performance': np.mean(performances),
            'avg_complexity': np.mean(complexities),
            'num_fragments': len(self.code_fragments)
        }
    
    def get_best_code(self) -> CodeFragment:
        """Get best performing code fragment."""
        return max(self.code_fragments, key=lambda x: x.performance)
    
    def save_state(self, filepath: str):
        """Save system state."""
        state = {
            'code_fragments': self.code_fragments,
            'generation': self.generation,
            'performance_history': self.performance_history
        }
        torch.save(state, filepath)
        logger.info(f"💾 Self-Rewriting System state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load system state."""
        state = torch.load(filepath)
        
        self.code_fragments = state['code_fragments']
        self.generation = state['generation']
        self.performance_history = state['performance_history']
        
        logger.info(f"📂 Self-Rewriting System state loaded from {filepath}")
        logger.info(f"   Generation: {self.generation}")
        logger.info(f"   Code fragments: {len(self.code_fragments)}")
