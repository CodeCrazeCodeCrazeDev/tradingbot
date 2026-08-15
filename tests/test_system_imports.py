"""
System Import Validation Script
Tests all major components to identify import issues
"""

import sys
import traceback
from pathlib import Path

# Add project root to path so imports resolve to the real package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

def run_import(module_name, description):
    """Test importing a module"""
    try:
        exec(f"import {module_name}")
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[FAIL] {description}")
        print(f"  Error: {str(e)}")
        traceback.print_exc()
        return False

def run_from_import(module_name, items, description):
    """Test importing specific items from a module"""
    try:
        items_str = ", ".join(items)
        exec(f"from {module_name} import {items_str}")
        print(f"[OK] {description}")
        return True
    except Exception as e:
        print(f"[FAIL] {description}")
        print(f"  Error: {str(e)}")
        traceback.print_exc()
        return False

def test_all_imports():
    """Proper test case for all system imports"""
    results = []

    # Test Data Layer
    results.append(run_from_import("trading_bot.data",
        ["MarketDataStream", "TimeSeriesDB", "RealTimeProcessor", "PipelineMonitor"],
        "Data Layer Components"))

    # Test Intelligence Layer - Brain
    results.append(run_from_import("trading_bot.brain",
        ["EliteBrainController"],
        "Elite Brain Controller"))
    results.append(run_from_import("trading_bot.brain",
        ["Tier1TechnicalAnalysis", "Tier2OrderFlowIntelligence", "Tier3MarketStructure"],
        "Brain Tiers 1-3"))
    results.append(run_from_import("trading_bot.brain",
        ["Tier4RegimeDetection", "Tier5SentimentAnalysis", "Tier6MacroAnalysis"],
        "Brain Tiers 4-6"))
    results.append(run_from_import("trading_bot.brain",
        ["Tier7RiskManagement", "Tier8ExecutionIntelligence", "Tier9MetaLearning"],
        "Brain Tiers 7-9"))

    # Test ML Pipeline
    results.append(run_from_import("trading_bot.ml.pipeline",
        ["MLPipeline"],
        "ML Pipeline"))

    # Test Risk Management Layer
    results.append(run_from_import("trading_bot.risk",
        ["UnifiedRiskManager"],
        "Unified Risk Manager"))

    # Test Execution Layer
    results.append(run_from_import("broker.broker_interface",
        ["BrokerInterface"],
        "Broker Interface"))

    # Test Advanced Features
    results.append(run_from_import("trading_bot.advanced_features.liquidity_holography",
        ["LiquidityHolographyEngine", "LiquidityGravityWell"],
        "Liquidity Holography"))
    results.append(run_from_import("trading_bot.advanced_features.institutional_footprint",
        ["InstitutionalFootprintDNA"],
        "Institutional Footprint"))

    assert all(results), "Some system imports failed! Run script manually or check the log trace."
