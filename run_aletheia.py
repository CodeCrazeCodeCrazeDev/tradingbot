"""
Quick start script for Aletheia Autonomous Research System
Run this to test the implementation
"""

import asyncio
import sys
from pathlib import Path

# Add trading_bot to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from examples.aletheia_demo import main

if __name__ == "__main__":
    print("=" * 70)
    print("ALETHEIA AUTONOMOUS RESEARCH SYSTEM - QUICK START")
    print("=" * 70)
    print("\nThis script will run the comprehensive demo of the Aletheia system.")
    print("Components being tested:")
    print("  1. Three-subagent architecture (Generator-Verifier-Reviser)")
    print("  2. Autonomous research framework")
    print("  3. Governance integration with AlphaAlgo")
    print("  4. Human-AI collaboration interface")
    print("  5. 200 Aletheia principles")
    print("  6. Tool integration system")
    print("  7. Comprehensive testing framework")
    print("\n" + "=" * 70)
    
    try:
        asyncio.run(main())
        print("\n" + "=" * 70)
        print("SUCCESS! Aletheia system is fully operational.")
        print("=" * 70)
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
