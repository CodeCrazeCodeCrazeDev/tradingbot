"""
Improvement Agent Demo
======================

Demonstrates the autonomous improvement agent capabilities.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.improvement_agent import (
    ImprovementAgent,
    AgentConfig,
    AgentMode,
    AgentState,
    AgentInterface,
    AnalysisDepth,
)


def main():
    """Run the improvement agent demo."""
    print("=" * 60)
    print("AUTONOMOUS IMPROVEMENT AGENT DEMO")
    print("=" * 60)
    print()
    
    # Path to analyze
    root_path = Path(__file__).parent.parent / "trading_bot"
    print(f"Target: {root_path}")
    print()
    
    # Create agent in observe mode (safe - no changes)
    config = AgentConfig(
        mode=AgentMode.OBSERVE,
        analysis_depth=AnalysisDepth.SHALLOW,  # Shallow for demo
    )
    
    agent = ImprovementAgent(str(root_path), config)
    interface = AgentInterface(agent)
    
    # Step 1: Analyze codebase
    print("Step 1: Analyzing codebase...")
    print("-" * 40)
    
    try:
        snapshot = agent.analyze_codebase()
        print(f"  Files analyzed: {snapshot.total_files}")
        print(f"  Lines of code: {snapshot.total_lines}")
        print(f"  Modules: {snapshot.total_modules}")
        print(f"  Overall quality: {snapshot.overall_quality:.1f}/100")
        print()
    except Exception as e:
        print(f"  Analysis error: {e}")
        print()
    
    # Step 2: Detect weaknesses
    print("Step 2: Detecting weaknesses...")
    print("-" * 40)
    
    try:
        report = agent.detect_weaknesses()
        print(f"  Total weaknesses: {report.total_weaknesses}")
        print(f"  Critical: {report.critical_count}")
        print(f"  High: {report.high_count}")
        print(f"  Medium: {report.medium_count}")
        print(f"  Low: {report.low_count}")
        print()
        
        # Show top 5 weaknesses
        print("  Top 5 weaknesses:")
        for i, w in enumerate(report.weaknesses[:5], 1):
            print(f"    {i}. [{w.severity.value.upper()}] {w.title}")
            print(f"       File: {Path(w.file_path).name}")
        print()
    except Exception as e:
        print(f"  Detection error: {e}")
        print()
    
    # Step 3: Show status
    print("Step 3: Agent Status")
    print("-" * 40)
    interface.print_status()
    print()
    
    # Step 4: Generate observation report
    print("Step 4: Observation Report")
    print("-" * 40)
    obs = interface.get_observation_report()
    print(f"  State: {obs.agent_state}")
    print(f"  Files: {obs.files_analyzed}")
    print(f"  Weaknesses: {obs.weaknesses_found}")
    print()
    
    # Summary
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print()
    print("To run the full improvement cycle with proposals:")
    print("  python -m trading_bot.improvement_agent.run_agent --interactive")
    print()
    print("Or use the batch file:")
    print("  RUN_IMPROVEMENT_AGENT.bat")
    print()


if __name__ == "__main__":
    main()
