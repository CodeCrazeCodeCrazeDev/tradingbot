"""
GitHub Repository Scanner - Command Line Interface

Usage:
    python scripts/scan_github_repos.py
    
This will scan GitHub for institutional-grade trading infrastructure repositories.

Author: AlphaAlgo Team
Date: 2026-01-29
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.sentient_core.institutional_github_scout import (
    InstitutionalGitHubScout,
    RepoCategory,
    Recommendation,
)


def print_banner():
    """Print banner"""
    print("\n" + "=" * 70)
    print("  ALPHAALGO INSTITUTIONAL GITHUB SCOUT")
    print("  Trading Infrastructure Repository Discovery")
    print("=" * 70)
    print("\nMISSION: Discover high-quality trading repos")
    print("SCOPE: execution | risk | backtesting | stats | portfolio")
    print("STANDARDS: Institutional-grade only\n")


def print_restrictions():
    """Print hard restrictions"""
    print("HARD RESTRICTIONS:")
    print("  [X] NO terminal commands")
    print("  [X] NO dependency installation")
    print("  [X] NO code execution")
    print("  [X] NO automatic integration")
    print("  [X] NO production modifications")
    print("  [OK] TRADING-ONLY scope")
    print("  [OK] Manual review required")
    print()


async def main():
    """Main entry point"""
    print_banner()
    print_restrictions()
    
    # Create scout
    scout = InstitutionalGitHubScout({
        'min_stars': 50,
        'min_forks': 10,
    })
    
    print("Scanning GitHub for trading infrastructure repositories...")
    print("(Applying strict quality gates and safety filters)\n")
    
    # Run scan
    repos = await scout.scan_github(max_results=5)
    
    # Format and display results
    output = scout.format_scan_results(repos)
    print(output)
    
    # Show integration proposals for accepted repos
    if repos:
        print("\n" + "=" * 70)
        print("INTEGRATION PROPOSALS (PATCH-ONLY)")
        print("=" * 70)
        
        for repo in repos:
            if repo.recommendation == Recommendation.ACCEPT:
                print(scout.generate_integration_proposal(repo))
                print("-" * 70)
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("SCAN SUMMARY")
    print("=" * 70)
    print(f"Repositories analyzed: {len(repos)}")
    print(f"Accepted: {sum(1 for r in repos if r.recommendation == Recommendation.ACCEPT)}")
    print(f"Investigate: {sum(1 for r in repos if r.recommendation == Recommendation.INVESTIGATE)}")
    print(f"Rejected: {sum(1 for r in repos if r.recommendation == Recommendation.REJECT)}")
    
    if repos:
        print("\nCategories found:")
        categories = {}
        for repo in repos:
            categories[repo.category.value] = categories.get(repo.category.value, 0) + 1
        for cat, count in sorted(categories.items()):
            print(f"  - {cat}: {count}")
    
    print("\nNOTE: All integrations require manual review and approval.")
    print("      No code has been executed or installed.")


if __name__ == "__main__":
    asyncio.run(main())
