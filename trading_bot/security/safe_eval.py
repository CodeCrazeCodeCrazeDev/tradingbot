"""
Safe Expression Evaluator - AlphaAlgo UCA V5
Alternative to eval() for secure formula computation.
"""

import ast
import operator
import math
from typing import Any, Dict

class SafeEvaluator:
    ALLOWED_OPS = {
        ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
        ast.Div: operator.truediv, ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg,
        ast.UAdd: operator.pos, ast.Lt: operator.lt, ast.LtE: operator.le,
        ast.Gt: operator.gt, ast.GtE: operator.ge, ast.Eq: operator.eq,
        ast.NotEq: operator.ne, ast.And: lambda a, b: a and b,
        ast.Or: lambda a, b: a or b, ast.Not: operator.not_,
    }

    ALLOWED_FUNCS = {
        'abs': abs, 'min': min, 'max': max, 'round': round, 'sum': sum, 'len': len,
        'sqrt': math.sqrt, 'exp': math.exp, 'log': math.log, 'sin': math.sin, 'cos': math.cos
    }

    def eval(self, expr: str, context: Dict[str, Any] = None) -> Any:
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree.body, context or {})
        except Exception as e:
            raise ValueError(f"Safe eval failed: {e}")

    def _eval_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Name):
            if node.id.startswith("__"):
                raise NameError(f"Access to private names not allowed: {node.id}")
            return context[node.id]
        elif isinstance(node, ast.BinOp):
            return self.ALLOWED_OPS[type(node.op)](self._eval_node(node.left, context), self._eval_node(node.right, context))
        elif isinstance(node, ast.UnaryOp):
            return self.ALLOWED_OPS[type(node.op)](self._eval_node(node.operand, context))
        elif isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise TypeError("Only direct function calls by name are allowed")
            if node.func.id not in self.ALLOWED_FUNCS:
                raise NameError(f"Function {node.func.id} is not allowed")
            return self.ALLOWED_FUNCS[node.func.id](*[self._eval_node(a, context) for a in node.args])
        elif isinstance(node, ast.Subscript):
            val = self._eval_node(node.value, context)
            slc = self._eval_node(node.slice, context)
            if isinstance(slc, str) and (slc.startswith("__") or "class" in slc):
                raise KeyError("Access to special/dunder keys not allowed")
            return val[slc]
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                raise AttributeError(f"Access to dunder attributes not allowed: {node.attr}")
            val = self._eval_node(node.value, context)
            return getattr(val, node.attr)
        elif isinstance(node, (ast.List, ast.Tuple)):
            return [self._eval_node(e, context) for e in node.elts]
        else:
            raise TypeError(f"Unsupported node: {type(node)}")

def safe_eval(expr: str, context: Dict[str, Any] = None) -> Any:
    return SafeEvaluator().eval(expr, context)
