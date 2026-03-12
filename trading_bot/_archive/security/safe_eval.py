"""
import os
Safe Expression Evaluator

This module provides safe alternatives to eval() and exec() to prevent code injection.
"""

import ast
import operator
import math
import logging
from typing import Any, Callable, Dict
from typing import List
from typing import Tuple

logger = logging.getLogger(__name__)


class SafeEvaluator:
    """
    Safe expression evaluator that prevents code injection
    
    Only allows:
    - Basic arithmetic operations (+, -, *, /, %, **)
    - Comparison operations (<, >, <=, >=, ==, !=)
    - Logical operations (and, or, not)
    - Whitelisted functions (abs, min, max, round, etc.)
    - Constants (numbers, strings, booleans)
    """
    
    # Allowed operators
    ALLOWED_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
        
        # Comparison
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        
        # Logical
        ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b,
        ast.Not: operator.not_,
    }
    
    # Allowed functions
    ALLOWED_FUNCS = {
        # Math functions
        'abs': abs,
        'min': min,
        'max': max,
        'round': round,
        'sum': sum,
        'len': len,
        
        # Math module functions
        'sqrt': math.sqrt,
        'pow': math.pow,
        'exp': math.exp,
        'log': math.log,
        'log10': math.log10,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'floor': math.floor,
        'ceil': math.ceil,
        
        # Type conversions
        'int': int,
        'float': float,
        'str': str,
        'bool': bool,
    }
    
    def __init__(self, additional_funcs: Dict[str, Callable] = None):
        """
        Initialize safe evaluator
        
        Args:
            additional_funcs: Additional functions to whitelist
        """
        self.allowed_funcs = self.ALLOWED_FUNCS.copy()
        if additional_funcs:
            self.allowed_funcs.update(additional_funcs)
    
    def eval(self, expr: str, context: Dict[str, Any] = None) -> Any:
        """
        Safely evaluate expression
        
        Args:
            expr: Expression to evaluate
            context: Variables available in expression
        
        Returns:
            Result of evaluation
        
        Raises:
            ValueError: If expression contains disallowed operations
            SyntaxError: If expression has syntax errors
        """
        try:
            # Parse expression
            tree = ast.parse(expr, mode='eval')
            
            # Evaluate
            return self._eval_node(tree.body, context or {})
            
        except SyntaxError as e:
            raise SyntaxError(f"Invalid expression syntax: {e}")
        except Exception as e:
            raise ValueError(f"Expression evaluation failed: {e}")
    
    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """Recursively evaluate AST node"""
        
        # Constants
        if isinstance(node, ast.Constant):
            return node.value
        
        # Variables
        elif isinstance(node, ast.Name):
            if node.id in context:
                return context[node.id]
            else:
                raise NameError(f"Variable '{node.id}' not defined")
        
        # Binary operations (e.g., a + b)
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left, context)
            right = self._eval_node(node.right, context)
            op = self.ALLOWED_OPS.get(type(node.op))
            
            if not op:
                raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            
            return op(left, right)
        
        # Unary operations (e.g., -a)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand, context)
            op = self.ALLOWED_OPS.get(type(node.op))
            
            if not op:
                raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            
            return op(operand)
        
        # Comparison operations (e.g., a < b)
        elif isinstance(node, ast.Compare):
            left = self._eval_node(node.left, context)
            
            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator, context)
                op_func = self.ALLOWED_OPS.get(type(op))
                
                if not op_func:
                    raise ValueError(f"Operation {type(op).__name__} not allowed")
                
                if not op_func(left, right):
                    return False
                
                left = right
            
            return True
        
        # Boolean operations (e.g., a and b)
        elif isinstance(node, ast.BoolOp):
            op = self.ALLOWED_OPS.get(type(node.op))
            if not op:
                raise ValueError(f"Operation {type(node.op).__name__} not allowed")
            
            values = [self._eval_node(v, context) for v in node.values]
            
            # Short-circuit evaluation
            if isinstance(node.op, ast.And):
                for v in values:
                    if not v:
                        return False
                return True
            elif isinstance(node.op, ast.Or):
                for v in values:
                    if v:
                        return True
                return False
        
        # Function calls
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls allowed")
            
            func_name = node.func.id
            if func_name not in self.allowed_funcs:
                raise ValueError(f"Function '{func_name}' not allowed")
            
            # Evaluate arguments
            args = [self._eval_node(arg, context) for arg in node.args]
            kwargs = {
                kw.arg: self._eval_node(kw.value, context)
                for kw in node.keywords
            }
            
            # Call function
            return self.allowed_funcs[func_name](*args, **kwargs)
        
        # Subscript (e.g., a[0])
        elif isinstance(node, ast.Subscript):
            value = self._eval_node(node.value, context)
            index = self._eval_node(node.slice, context)
            return value[index]
        
        # List/Tuple
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [self._eval_node(elt, context) for elt in node.elts]
        
        # Dict
        elif isinstance(node, ast.Dict):
            return {
                self._eval_node(k, context): self._eval_node(v, context)
                for k, v in zip(node.keys, node.values)
            }
        
        else:
            raise ValueError(f"Node type {type(node).__name__} not allowed")


def safe_eval(expr: str, context: Dict[str, Any] = None) -> Any:
    """
    Convenience function for safe evaluation
    
    Args:
        expr: Expression to evaluate
        context: Variables available in expression
    
    Returns:
        Result of evaluation
    """
    evaluator = SafeEvaluator()
    return evaluator.eval(expr, context)


def replace_eval_in_code(code: str) -> str:
    """
    Replace eval() calls with safe_eval() in code
    
    Args:
        code: Source code
    
    Returns:
        Modified code with safe_eval
    """
    # Simple replacement (may need manual review)
    code = code.replace('eval(', 'safe_eval(')
    
    # Add import if not present
    if 'from trading_bot.security.safe_eval import safe_eval' not in code:
        import_line = 'from trading_bot.security.safe_eval import safe_eval\n'
        
        # Find first import
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                lines.insert(i, import_line)
                break
        else:
            # No imports found, add at top
            lines.insert(0, import_line)
        
        code = '\n'.join(lines)
    
    return code


# Example usage and tests
if __name__ == '__main__':
    evaluator = SafeEvaluator()
    
    # Test basic arithmetic
    assert evaluator.eval('2 + 3') == 5
    assert evaluator.eval('10 - 4') == 6
    assert evaluator.eval('3 * 4') == 12
    assert evaluator.eval('15 / 3') == 5
    assert evaluator.eval('2 ** 3') == 8
    
    # Test with context
    context = {'x': 10, 'y': 5}
    assert evaluator.eval('x + y', context) == 15
    assert evaluator.eval('x * y', context) == 50
    
    # Test functions
    assert evaluator.eval('abs(-5)') == 5
    assert evaluator.eval('max(1, 2, 3)') == 3
    assert evaluator.eval('round(3.7)') == 4
    
    # Test comparisons
    assert evaluator.eval('5 > 3') == True
    assert evaluator.eval('10 <= 10') == True
    
    # Test that dangerous operations fail
    try:
        evaluator.eval('__import__("os").system("ls")')
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
    
    logger.info("All tests passed!")


# Export
__all__ = [
    'SafeEvaluator',
    'safe_eval',
    'replace_eval_in_code'
]
