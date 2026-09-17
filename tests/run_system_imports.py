"""
System Import Validation Script
Tests all major components to identify import issues
"""

import sys
import traceback

def test_import(module_name, description):
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

def test_from_import(module_name, items, description):
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

print("=" * 80)
print("ALPHAALGO SYSTEM IMPORT VALIDATION")
print("=" * 80)
print()

results = []

# Test Data Layer
print("Testing Data Layer...")
print("-" * 80)
results.append(test_from_import("trading_bot.data", 
    ["MarketDataStream", "TimeSeriesDB", "RealTimeProcessor", "PipelineMonitor"],
    "Data Layer Components"))
print()

# Test Intelligence Layer - Brain
print("Testing Intelligence Layer - Brain...")
print("-" * 80)
results.append(test_from_import("trading_bot.brain", 
    ["EliteBrainController"],
    "Elite Brain Controller"))
results.append(test_from_import("trading_bot.brain", 
    ["Tier1TechnicalAnalysis", "Tier2OrderFlowIntelligence", "Tier3MarketStructure"],
    "Brain Tiers 1-3"))
results.append(test_from_import("trading_bot.brain", 
    ["Tier4RegimeDetection", "Tier5SentimentAnalysis", "Tier6MacroAnalysis"],
    "Brain Tiers 4-6"))
results.append(test_from_import("trading_bot.brain", 
    ["Tier7RiskManagement", "Tier8ExecutionIntelligence", "Tier9MetaLearning"],
    "Brain Tiers 7-9"))
print()

# Test Intelligence Layer - Agents
print("Testing Intelligence Layer - Agents...")
print("-" * 80)
results.append(test_from_import("agents.coordinator", 
    ["MultiAgentCoordinator"],
    "Multi-Agent Coordinator"))
results.append(test_from_import("agents.specialized_agents", 
    ["TrendFollowingAgent", "MeanReversionAgent", "VolatilityAgent"],
    "Specialized Agents"))
print()

# Test ML Pipeline
print("Testing ML Pipeline...")
print("-" * 80)
results.append(test_from_import("ml.pipeline", 
    ["MLPipeline"],
    "ML Pipeline"))
print()

# Test Risk Management Layer
print("Testing Risk Management Layer...")
print("-" * 80)
results.append(test_from_import("trading_bot.risk", 
    ["UnifiedRiskManager"],
    "Unified Risk Manager"))
results.append(test_from_import("risk_management", 
    ["RiskEngine", "PortfolioManager"],
    "Risk Engine & Portfolio Manager"))
print()

# Test Execution Layer
print("Testing Execution Layer...")
print("-" * 80)
results.append(test_from_import("broker.broker_interface", 
    ["BrokerInterface"],
    "Broker Interface"))
results.append(test_from_import("trading.order_execution", 
    ["OrderExecutionManager"],
    "Order Execution Manager"))
print()

# Test Advanced Features
print("Testing Advanced Features...")
print("-" * 80)
results.append(test_from_import("trading_bot.advanced_features.liquidity_holography", 
    ["LiquidityHolographyEngine", "LiquidityGravityWell"],
    "Liquidity Holography"))
results.append(test_from_import("trading_bot.advanced_features.institutional_footprint", 
    ["InstitutionalFootprintDNA"],
    "Institutional Footprint"))
print()

# Test Explainability
print("Testing Explainability...")
print("-" * 80)
results.append(test_from_import("explainability", 
    ["ExplainableAI"],
    "Explainable AI"))
print()

# Test Infrastructure
print("Testing Infrastructure...")
print("-" * 80)
results.append(test_from_import("infrastructure", 
    ["HealthCheck"],
    "Health Check"))
print()

# Summary
print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
passed = sum(results)
total = len(results)
failed = total - passed

print(f"Total Tests: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Success Rate: {(passed/total)*100:.1f}%")
print()

if failed == 0:
    print("SUCCESS! ALL IMPORTS WORKING! System is ready to run.")
    sys.exit(0)
else:
    print("WARNING: Some imports failed. Please fix the issues above.")
    sys.exit(1)
