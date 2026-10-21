"""Compatibility shim — the Scientific Reasoning Engine is canonical at
``trading_bot.core.csc.scientific_reasoning`` (the CSC's hypothesis
lifecycle tracker). This module re-exports it for legacy import paths.
"""
from trading_bot.core.csc.scientific_reasoning import *  # noqa: F401,F403
from trading_bot.core.csc.scientific_reasoning import (  # noqa: F401
    HypothesisLineage, HypothesisState, PromotionLevel, ScientificEvidence,
    ScientificHypothesis, ScientificReasoningEngine)
