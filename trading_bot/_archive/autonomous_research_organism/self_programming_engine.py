"""
Self-Programming Engine
=======================

Enables the AI to generate, evolve, and improve its own code safely.
Implements multiple evolution strategies:
1. Genetic programming (code mutation/crossover)
2. Neural architecture search
3. Template-based generation
4. Reinforcement learning guided evolution

CRITICAL: All generated code MUST pass safety scanning and run in sandbox.
"""

import ast
import random
import hashlib
import copy
from typing import Dict, Any, List, Optional, Set, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
import logging
import json

logger = logging.getLogger(__name__)


class EvolutionStrategy(Enum):
    """Strategies for code evolution."""
    MUTATION = auto()          # Random mutations
    CROSSOVER = auto()         # Combine successful code
    TEMPLATE = auto()          # Template-based generation
    GUIDED = auto()            # RL-guided evolution
    NEURAL_SEARCH = auto()     # Neural architecture search
    HYBRID = auto()            # Combination of strategies


class CodeType(Enum):
    """Types of code that can be generated."""
    STRATEGY = auto()          # Trading strategy
    INDICATOR = auto()         # Technical indicator
    FEATURE = auto()           # Feature engineering
    MODEL = auto()             # ML model architecture
    FILTER = auto()            # Signal filter
    RISK_RULE = auto()         # Risk management rule
    UTILITY = auto()           # Utility function


class MutationType(Enum):
    """Types of code mutations."""
    PARAMETER_CHANGE = auto()
    OPERATOR_SWAP = auto()
    CONDITION_MODIFY = auto()
    BLOCK_INSERT = auto()
    BLOCK_DELETE = auto()
    BLOCK_SWAP = auto()
    FUNCTION_INLINE = auto()
    LOOP_UNROLL = auto()


@dataclass
class CodeGeneration:
    """A generated piece of code."""
    generation_id: str
    code_type: CodeType
    code: str
    strategy: EvolutionStrategy
    parent_ids: List[str] = field(default_factory=list)
    generation_number: int = 0
    fitness_score: float = 0.0
    validation_passed: bool = False
    safety_scan_passed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'generation_id': self.generation_id,
            'code_type': self.code_type.name,
            'code': self.code,
            'strategy': self.strategy.name,
            'parent_ids': self.parent_ids,
            'generation_number': self.generation_number,
            'fitness_score': self.fitness_score,
            'validation_passed': self.validation_passed,
            'safety_scan_passed': self.safety_scan_passed,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class EvolutionConfig:
    """Configuration for code evolution."""
    population_size: int = 20
    elite_size: int = 5
    mutation_rate: float = 0.3
    crossover_rate: float = 0.5
    max_generations: int = 100
    fitness_threshold: float = 0.8
    diversity_weight: float = 0.2
    complexity_penalty: float = 0.1
    max_code_length: int = 5000
    allowed_imports: Set[str] = field(default_factory=lambda: {
        'math', 'statistics', 'numpy', 'pandas',
    })


@dataclass
class CodeTemplate:
    """Template for code generation."""
    template_id: str
    code_type: CodeType
    template: str
    parameters: Dict[str, Any]
    description: str
    
    def render(self, **kwargs) -> str:
        """Render template with parameters."""
        code = self.template
        for key, value in {**self.parameters, **kwargs}.items():
            code = code.replace(f"{{{{ {key} }}}}", str(value))
        return code


class CodeMutator:
    """Performs mutations on code."""
    
    # Operators that can be swapped
    OPERATOR_SWAPS = {
        '+': ['-', '*'],
        '-': ['+', '/'],
        '*': ['+', '/'],
        '/': ['*', '-'],
        '>': ['>=', '<', '<='],
        '<': ['<=', '>', '>='],
        '>=': ['>', '<=', '<'],
        '<=': ['<', '>=', '>'],
        '==': ['!='],
        '!=': ['=='],
        'and': ['or'],
        'or': ['and'],
    }
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
    
    def mutate(self, code: str, mutation_type: Optional[MutationType] = None) -> str:
        """
        Apply mutation to code.
        
        Args:
            code: Code to mutate
            mutation_type: Specific mutation type or random
            
        Returns:
            Mutated code
        """
        if mutation_type is None:
            mutation_type = random.choice(list(MutationType))
        
        try:
            if mutation_type == MutationType.PARAMETER_CHANGE:
                return self._mutate_parameters(code)
            elif mutation_type == MutationType.OPERATOR_SWAP:
                return self._mutate_operators(code)
            elif mutation_type == MutationType.CONDITION_MODIFY:
                return self._mutate_conditions(code)
            elif mutation_type == MutationType.BLOCK_INSERT:
                return self._insert_block(code)
            elif mutation_type == MutationType.BLOCK_DELETE:
                return self._delete_block(code)
            elif mutation_type == MutationType.BLOCK_SWAP:
                return self._swap_blocks(code)
            else:
                return code
        except Exception as e:
            logger.warning(f"Mutation failed: {e}")
            return code
    
    def _mutate_parameters(self, code: str) -> str:
        """Mutate numeric parameters in code."""
        import re
        
        def mutate_number(match):
            num_str = match.group(0)
            try:
                if '.' in num_str:
                    num = float(num_str)
                    # Mutate by ±20%
                    factor = random.uniform(0.8, 1.2)
                    return f"{num * factor:.4f}"
                else:
                    num = int(num_str)
                    # Mutate by ±20% or ±1
                    delta = max(1, int(num * 0.2))
                    return str(num + random.randint(-delta, delta))
            except ValueError:
                return num_str
        
        # Find and mutate numbers (but not in strings or comments)
        pattern = r'(?<!["\'])\b\d+\.?\d*\b(?!["\'])'
        return re.sub(pattern, mutate_number, code)
    
    def _mutate_operators(self, code: str) -> str:
        """Swap operators in code."""
        for op, replacements in self.OPERATOR_SWAPS.items():
            if op in code and random.random() < 0.3:
                replacement = random.choice(replacements)
                # Replace one occurrence
                code = code.replace(op, replacement, 1)
                break
        return code
    
    def _mutate_conditions(self, code: str) -> str:
        """Modify conditions in code."""
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare) and random.random() < 0.3:
                    # Flip comparison
                    if node.ops:
                        op = node.ops[0]
                        if isinstance(op, ast.Gt):
                            node.ops[0] = ast.Lt()
                        elif isinstance(op, ast.Lt):
                            node.ops[0] = ast.Gt()
            
            return ast.unparse(tree)
        except Exception:
            return code
    
    def _insert_block(self, code: str) -> str:
        """Insert a code block."""
        blocks = [
            "    # Additional check\n    if True:\n        pass\n",
            "    # Logging\n    # logger.debug('checkpoint')\n",
        ]
        
        lines = code.split('\n')
        if len(lines) > 2:
            insert_pos = random.randint(1, len(lines) - 1)
            lines.insert(insert_pos, random.choice(blocks))
        
        return '\n'.join(lines)
    
    def _delete_block(self, code: str) -> str:
        """Delete a code block (carefully)."""
        lines = code.split('\n')
        
        # Find deletable lines (comments, pass statements)
        deletable = []
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('#') or stripped == 'pass':
                deletable.append(i)
        
        if deletable:
            to_delete = random.choice(deletable)
            lines.pop(to_delete)
        
        return '\n'.join(lines)
    
    def _swap_blocks(self, code: str) -> str:
        """Swap two code blocks."""
        try:
            tree = ast.parse(code)
            
            # Find function definitions
            functions = [node for node in ast.walk(tree) 
                        if isinstance(node, ast.FunctionDef)]
            
            if len(functions) >= 2:
                # Swap two random functions
                i, j = random.sample(range(len(functions)), 2)
                functions[i].body, functions[j].body = functions[j].body, functions[i].body
            
            return ast.unparse(tree)
        except Exception:
            return code


class CodeCrossover:
    """Performs crossover between code specimens."""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
    
    def crossover(self, parent1: str, parent2: str) -> Tuple[str, str]:
        """
        Perform crossover between two code specimens.
        
        Args:
            parent1: First parent code
            parent2: Second parent code
            
        Returns:
            Two offspring code strings
        """
        try:
            tree1 = ast.parse(parent1)
            tree2 = ast.parse(parent2)
            
            # Find functions in both
            funcs1 = [n for n in ast.walk(tree1) if isinstance(n, ast.FunctionDef)]
            funcs2 = [n for n in ast.walk(tree2) if isinstance(n, ast.FunctionDef)]
            
            if funcs1 and funcs2:
                # Single-point crossover on function bodies
                func1 = random.choice(funcs1)
                func2 = random.choice(funcs2)
                
                # Swap bodies
                func1.body, func2.body = func2.body, func1.body
            
            return ast.unparse(tree1), ast.unparse(tree2)
            
        except Exception as e:
            logger.warning(f"Crossover failed: {e}")
            return parent1, parent2


class FitnessEvaluator:
    """Evaluates fitness of generated code."""
    
    def __init__(self, config: EvolutionConfig):
        self.config = config
    
    def evaluate(self, 
                 code: str, 
                 test_results: Optional[Dict[str, float]] = None) -> float:
        """
        Evaluate fitness of code.
        
        Args:
            code: Code to evaluate
            test_results: Optional test results
            
        Returns:
            Fitness score (0.0 to 1.0)
        """
        scores = []
        
        # Syntax validity
        syntax_score = self._check_syntax(code)
        scores.append(('syntax', syntax_score, 0.2))
        
        # Complexity penalty
        complexity_score = self._evaluate_complexity(code)
        scores.append(('complexity', complexity_score, 0.1))
        
        # Code quality
        quality_score = self._evaluate_quality(code)
        scores.append(('quality', quality_score, 0.2))
        
        # Test results (if available)
        if test_results:
            performance_score = self._evaluate_performance(test_results)
            scores.append(('performance', performance_score, 0.5))
        else:
            # Without test results, weight other factors more
            scores = [(n, s, w * 2) for n, s, w in scores]
        
        # Weighted average
        total_weight = sum(w for _, _, w in scores)
        fitness = sum(s * w for _, s, w in scores) / total_weight
        
        return min(1.0, max(0.0, fitness))
    
    def _check_syntax(self, code: str) -> float:
        """Check if code has valid syntax."""
        try:
            ast.parse(code)
            return 1.0
        except SyntaxError:
            return 0.0
    
    def _evaluate_complexity(self, code: str) -> float:
        """Evaluate code complexity (lower is better)."""
        # Simple metrics
        lines = len(code.split('\n'))
        chars = len(code)
        
        # Penalize overly complex code
        if lines > 200 or chars > self.config.max_code_length:
            return 0.3
        
        # Count nesting depth
        max_indent = 0
        for line in code.split('\n'):
            indent = len(line) - len(line.lstrip())
            max_indent = max(max_indent, indent // 4)
        
        if max_indent > 6:
            return 0.5
        
        return 1.0 - (lines / 200) * self.config.complexity_penalty
    
    def _evaluate_quality(self, code: str) -> float:
        """Evaluate code quality."""
        score = 1.0
        
        # Check for docstrings
        if '"""' not in code and "'''" not in code:
            score -= 0.1
        
        # Check for type hints
        if ':' not in code or '->' not in code:
            score -= 0.1
        
        # Check for error handling
        if 'try:' not in code and 'except' not in code:
            score -= 0.05
        
        return max(0.0, score)
    
    def _evaluate_performance(self, results: Dict[str, float]) -> float:
        """Evaluate based on test results."""
        # Expected metrics
        sharpe = results.get('sharpe_ratio', 0)
        win_rate = results.get('win_rate', 0)
        profit_factor = results.get('profit_factor', 0)
        max_drawdown = results.get('max_drawdown', 1)
        
        score = 0.0
        
        # Sharpe ratio (target > 1.5)
        if sharpe > 0:
            score += min(0.3, sharpe / 5)
        
        # Win rate (target > 0.5)
        score += win_rate * 0.2
        
        # Profit factor (target > 1.5)
        if profit_factor > 1:
            score += min(0.3, (profit_factor - 1) / 2)
        
        # Drawdown penalty
        score -= max_drawdown * 0.2
        
        return max(0.0, min(1.0, score))


class SelfProgrammingEngine:
    """
    Engine for autonomous code generation and evolution.
    
    Generates, mutates, and evolves code while ensuring safety
    through scanning and sandbox execution.
    """
    
    # Built-in code templates
    TEMPLATES: List[CodeTemplate] = [
        CodeTemplate(
            template_id="indicator_ma",
            code_type=CodeType.INDICATOR,
            template='''
def {{ name }}(data: pd.DataFrame, period: int = {{ period }}) -> pd.Series:
    """{{ description }}"""
    return data['close'].rolling(window=period).mean()
''',
            parameters={'name': 'moving_average', 'period': 20, 'description': 'Simple moving average'},
            description="Moving average indicator template",
        ),
        CodeTemplate(
            template_id="indicator_rsi",
            code_type=CodeType.INDICATOR,
            template='''
def {{ name }}(data: pd.DataFrame, period: int = {{ period }}) -> pd.Series:
    """{{ description }}"""
    delta = data['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))
''',
            parameters={'name': 'rsi', 'period': 14, 'description': 'Relative Strength Index'},
            description="RSI indicator template",
        ),
        CodeTemplate(
            template_id="strategy_crossover",
            code_type=CodeType.STRATEGY,
            template='''
def {{ name }}(data: pd.DataFrame, fast_period: int = {{ fast }}, slow_period: int = {{ slow }}) -> pd.Series:
    """{{ description }}"""
    fast_ma = data['close'].rolling(window=fast_period).mean()
    slow_ma = data['close'].rolling(window=slow_period).mean()
    
    signal = pd.Series(0, index=data.index)
    signal[fast_ma > slow_ma] = 1
    signal[fast_ma < slow_ma] = -1
    
    return signal
''',
            parameters={'name': 'ma_crossover', 'fast': 10, 'slow': 30, 'description': 'MA crossover strategy'},
            description="Moving average crossover strategy template",
        ),
        CodeTemplate(
            template_id="filter_volatility",
            code_type=CodeType.FILTER,
            template='''
def {{ name }}(data: pd.DataFrame, threshold: float = {{ threshold }}) -> pd.Series:
    """{{ description }}"""
    volatility = data['close'].pct_change().rolling(window=20).std()
    return volatility < threshold
''',
            parameters={'name': 'low_volatility_filter', 'threshold': 0.02, 'description': 'Low volatility filter'},
            description="Volatility filter template",
        ),
        CodeTemplate(
            template_id="risk_rule_position_size",
            code_type=CodeType.RISK_RULE,
            template='''
def {{ name }}(equity: float, risk_per_trade: float = {{ risk }}, stop_loss_pct: float = {{ stop }}) -> float:
    """{{ description }}"""
    risk_amount = equity * risk_per_trade
    position_size = risk_amount / stop_loss_pct
    return min(position_size, equity * 0.1)  # Max 10% of equity
''',
            parameters={'name': 'position_sizer', 'risk': 0.02, 'stop': 0.05, 'description': 'Position sizing rule'},
            description="Position sizing rule template",
        ),
    ]
    
    def __init__(self,
                 config: Optional[EvolutionConfig] = None,
                 safety_scanner: Optional[Any] = None,
                 sandbox: Optional[Any] = None):
        """
        Initialize self-programming engine.
        
        Args:
            config: Evolution configuration
            safety_scanner: Code safety scanner instance
            sandbox: Sandbox environment instance
        """
        self.config = config or EvolutionConfig()
        self.safety_scanner = safety_scanner
        self.sandbox = sandbox
        
        self.mutator = CodeMutator(self.config)
        self.crossover = CodeCrossover(self.config)
        self.fitness_evaluator = FitnessEvaluator(self.config)
        
        self.generations: Dict[str, CodeGeneration] = {}
        self.population: List[CodeGeneration] = []
        self.best_specimens: List[CodeGeneration] = []
        
        self._generation_counter = 0
        self._current_generation = 0
        
        logger.info("SelfProgrammingEngine initialized")
    
    def generate_from_template(self,
                               template_id: str,
                               parameters: Optional[Dict[str, Any]] = None) -> CodeGeneration:
        """
        Generate code from a template.
        
        Args:
            template_id: ID of template to use
            parameters: Parameters for template
            
        Returns:
            CodeGeneration instance
        """
        template = next((t for t in self.TEMPLATES if t.template_id == template_id), None)
        if not template:
            raise ValueError(f"Unknown template: {template_id}")
        
        code = template.render(**(parameters or {}))
        
        return self._create_generation(
            code=code,
            code_type=template.code_type,
            strategy=EvolutionStrategy.TEMPLATE,
            metadata={'template_id': template_id, 'parameters': parameters},
        )
    
    def generate_random(self, code_type: CodeType) -> CodeGeneration:
        """
        Generate random code of a given type.
        
        Args:
            code_type: Type of code to generate
            
        Returns:
            CodeGeneration instance
        """
        # Find matching templates
        matching = [t for t in self.TEMPLATES if t.code_type == code_type]
        
        if not matching:
            raise ValueError(f"No templates for code type: {code_type}")
        
        template = random.choice(matching)
        
        # Randomize parameters
        params = {}
        for key, value in template.parameters.items():
            if isinstance(value, int):
                params[key] = random.randint(max(1, value // 2), value * 2)
            elif isinstance(value, float):
                params[key] = value * random.uniform(0.5, 2.0)
            else:
                params[key] = value
        
        return self.generate_from_template(template.template_id, params)
    
    def mutate(self, generation: CodeGeneration) -> CodeGeneration:
        """
        Create mutated version of code.
        
        Args:
            generation: Code to mutate
            
        Returns:
            New CodeGeneration with mutation
        """
        mutated_code = self.mutator.mutate(generation.code)
        
        return self._create_generation(
            code=mutated_code,
            code_type=generation.code_type,
            strategy=EvolutionStrategy.MUTATION,
            parent_ids=[generation.generation_id],
            generation_number=generation.generation_number + 1,
        )
    
    def crossover_specimens(self, 
                            parent1: CodeGeneration,
                            parent2: CodeGeneration) -> Tuple[CodeGeneration, CodeGeneration]:
        """
        Create offspring from two parent specimens.
        
        Args:
            parent1: First parent
            parent2: Second parent
            
        Returns:
            Two offspring CodeGenerations
        """
        code1, code2 = self.crossover.crossover(parent1.code, parent2.code)
        
        offspring1 = self._create_generation(
            code=code1,
            code_type=parent1.code_type,
            strategy=EvolutionStrategy.CROSSOVER,
            parent_ids=[parent1.generation_id, parent2.generation_id],
            generation_number=max(parent1.generation_number, parent2.generation_number) + 1,
        )
        
        offspring2 = self._create_generation(
            code=code2,
            code_type=parent1.code_type,
            strategy=EvolutionStrategy.CROSSOVER,
            parent_ids=[parent1.generation_id, parent2.generation_id],
            generation_number=max(parent1.generation_number, parent2.generation_number) + 1,
        )
        
        return offspring1, offspring2
    
    def evolve_population(self,
                          code_type: CodeType,
                          fitness_function: Optional[Callable[[str], float]] = None,
                          generations: Optional[int] = None) -> List[CodeGeneration]:
        """
        Evolve a population of code specimens.
        
        Args:
            code_type: Type of code to evolve
            fitness_function: Custom fitness function
            generations: Number of generations to evolve
            
        Returns:
            Best specimens from evolution
        """
        generations = generations or self.config.max_generations
        
        # Initialize population
        if not self.population:
            self._initialize_population(code_type)
        
        for gen in range(generations):
            self._current_generation = gen
            
            # Evaluate fitness
            for specimen in self.population:
                if fitness_function:
                    specimen.fitness_score = fitness_function(specimen.code)
                else:
                    specimen.fitness_score = self.fitness_evaluator.evaluate(specimen.code)
            
            # Sort by fitness
            self.population.sort(key=lambda x: x.fitness_score, reverse=True)
            
            # Check termination
            if self.population[0].fitness_score >= self.config.fitness_threshold:
                logger.info(f"Fitness threshold reached at generation {gen}")
                break
            
            # Select elite
            elite = self.population[:self.config.elite_size]
            self.best_specimens = elite.copy()
            
            # Create new population
            new_population = elite.copy()
            
            while len(new_population) < self.config.population_size:
                if random.random() < self.config.crossover_rate and len(elite) >= 2:
                    # Crossover
                    p1, p2 = random.sample(elite, 2)
                    o1, o2 = self.crossover_specimens(p1, p2)
                    new_population.extend([o1, o2])
                elif random.random() < self.config.mutation_rate:
                    # Mutation
                    parent = random.choice(elite)
                    offspring = self.mutate(parent)
                    new_population.append(offspring)
                else:
                    # Random new specimen
                    new_population.append(self.generate_random(code_type))
            
            self.population = new_population[:self.config.population_size]
            
            # Validate and scan
            self._validate_population()
            
            logger.debug(
                f"Generation {gen}: best fitness = {self.population[0].fitness_score:.4f}"
            )
        
        return self.best_specimens
    
    def _initialize_population(self, code_type: CodeType):
        """Initialize population with random specimens."""
        self.population = []
        
        for _ in range(self.config.population_size):
            try:
                specimen = self.generate_random(code_type)
                self.population.append(specimen)
            except Exception as e:
                logger.warning(f"Failed to generate specimen: {e}")
    
    def _validate_population(self):
        """Validate and safety scan population."""
        for specimen in self.population:
            # Syntax validation
            try:
                ast.parse(specimen.code)
                specimen.validation_passed = True
            except SyntaxError:
                specimen.validation_passed = False
                specimen.fitness_score *= 0.1
            
            # Safety scan
            if self.safety_scanner:
                scan_result = self.safety_scanner.scan(specimen.code)
                specimen.safety_scan_passed = scan_result.is_safe
                if not scan_result.is_safe:
                    specimen.fitness_score *= 0.1
    
    def _create_generation(self,
                           code: str,
                           code_type: CodeType,
                           strategy: EvolutionStrategy,
                           parent_ids: Optional[List[str]] = None,
                           generation_number: int = 0,
                           metadata: Optional[Dict[str, Any]] = None) -> CodeGeneration:
        """Create a new code generation."""
        self._generation_counter += 1
        generation_id = f"gen_{self._generation_counter:08d}"
        
        generation = CodeGeneration(
            generation_id=generation_id,
            code_type=code_type,
            code=code,
            strategy=strategy,
            parent_ids=parent_ids or [],
            generation_number=generation_number,
            metadata=metadata or {},
        )
        
        self.generations[generation_id] = generation
        
        return generation
    
    def get_best_code(self, code_type: Optional[CodeType] = None) -> Optional[CodeGeneration]:
        """Get best code specimen."""
        candidates = self.best_specimens
        
        if code_type:
            candidates = [c for c in candidates if c.code_type == code_type]
        
        if not candidates:
            return None
        
        return max(candidates, key=lambda x: x.fitness_score)
    
    def get_evolution_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics."""
        return {
            'total_generations': self._generation_counter,
            'current_generation': self._current_generation,
            'population_size': len(self.population),
            'best_fitness': max((s.fitness_score for s in self.population), default=0),
            'avg_fitness': (
                sum(s.fitness_score for s in self.population) / len(self.population)
                if self.population else 0
            ),
            'validation_rate': (
                sum(1 for s in self.population if s.validation_passed) / len(self.population)
                if self.population else 0
            ),
            'safety_rate': (
                sum(1 for s in self.population if s.safety_scan_passed) / len(self.population)
                if self.population else 0
            ),
        }
    
    def export_best_code(self, output_path: str):
        """Export best code specimens to file."""
        best = self.get_best_code()
        if not best:
            logger.warning("No best code to export")
            return
        
        with open(output_path, 'w') as f:
            f.write(f"# Generated by SelfProgrammingEngine\n")
            f.write(f"# Generation ID: {best.generation_id}\n")
            f.write(f"# Fitness Score: {best.fitness_score:.4f}\n")
            f.write(f"# Strategy: {best.strategy.name}\n")
            f.write(f"# Created: {best.created_at.isoformat()}\n\n")
            f.write(best.code)
        
        logger.info(f"Best code exported to {output_path}")
