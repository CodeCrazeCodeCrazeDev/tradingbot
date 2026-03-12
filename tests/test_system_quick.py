"""
Quick System Test - Validates AlphaAlgo can initialize without errors
"""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system():
    """Test system initialization"""
    
    print("="*80)
    print("ALPHAALGO QUICK SYSTEM TEST")
    print("="*80)
    print()
    
    # Test 1: Import all core modules
    print("[1/5] Testing imports...")
    try:
        from trading_bot.data import MarketDataStream, TimeSeriesDB
        from trading_bot.brain import EliteBrainController
        from agents.coordinator import MultiAgentCoordinator
        from risk_management import RiskEngine
        print("  [OK] All imports successful")
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        return False
    
    # Test 2: Initialize Data Layer
    print("[2/5] Testing Data Layer...")
    try:
        config = {'simulate_data': True, 'use_redis': False}
        stream = MarketDataStream(config)
        print("  [OK] Data Layer initialized")
    except Exception as e:
        print(f"  [FAIL] Data Layer error: {e}")
        return False
    
    # Test 3: Initialize Brain
    print("[3/5] Testing Brain Layer...")
    try:
        brain = EliteBrainController()
        print("  [OK] Brain Layer initialized")
    except Exception as e:
        print(f"  [FAIL] Brain Layer error: {e}")
        return False
    
    # Test 4: Initialize Agents
    print("[4/5] Testing Agent System...")
    try:
        from agents.specialized_agents import TrendFollowingAgent, MeanReversionAgent
        agents = {
            'trend_follower': TrendFollowingAgent(),
            'mean_reverter': MeanReversionAgent()
        }
        coordinator = MultiAgentCoordinator(agents)
        print("  [OK] Agent System initialized")
    except Exception as e:
        print(f"  [FAIL] Agent System error: {e}")
        return False
    
    # Test 5: Initialize Risk Management
    print("[5/5] Testing Risk Management...")
    try:
        risk_engine = RiskEngine()
        print("  [OK] Risk Management initialized")
    except Exception as e:
        print(f"  [FAIL] Risk Management error: {e}")
        return False
    
    print()
    print("="*80)
    print("ALL TESTS PASSED - SYSTEM IS OPERATIONAL!")
    print("="*80)
    return True

if __name__ == "__main__":
    result = asyncio.run(test_system())
    exit(0 if result else 1)
