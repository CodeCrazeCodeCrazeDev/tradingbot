"""
Explainability module for trading models

Provides SHAP-based feature attribution and trade explanations.
Explainability module for model interpretability
"""

from .shap_explainer import TradingExplainer, TradeAutopsy
from .lime_explainer import LIMEExplainer, TradingLIMEExplainer
from trading_bot.ml.shap_explainer import SHAPExplainer

__all__ = [
    'TradingExplainer',
    'TradeAutopsy',
    'LIMEExplainer',
    'TradingLIMEExplainer',
    'SHAPExplainer',
]
