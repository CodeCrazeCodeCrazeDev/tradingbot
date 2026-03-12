"""
Generate comprehensive missing module integration report.
Cross-references all trading_bot/* packages against the three runtime entrypoints.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import json

# Paths
ROOT = Path(r"c:\Users\peterson\trading bot")
TRADING_BOT_DIR = ROOT / "trading_bot"
MAIN_PY = ROOT / "main.py"
BACKGROUND_SERVICES_PY = ROOT / "background_services.py"
SCHEDULED_JOBS_PY = ROOT / "scheduled_jobs_runner.py"

def get_all_packages() -> List[str]:
    """Get all top-level packages under trading_bot/."""
    packages = []
    if not TRADING_BOT_DIR.exists():
        return packages
    
    for item in TRADING_BOT_DIR.iterdir():
        if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
            packages.append(item.name)
    
    return sorted(packages)

def check_references(package_name: str, file_path: Path) -> Dict[str, any]:
    """Check if a package is referenced in a file."""
    if not file_path.exists():
        return {"referenced": False, "lines": [], "import_count": 0}
    
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return {"referenced": False, "lines": [], "import_count": 0, "error": str(e)}
    
    # Search patterns
    patterns = [
        rf'\bfrom\s+trading_bot\.{package_name}\b',
        rf'\bfrom\s+{package_name}\b',
        rf'\bimport\s+{package_name}\b',
        rf'\b{package_name}\.',
        rf'"{package_name}"',
        rf"'{package_name}'",
    ]
    
    lines_found = []
    for i, line in enumerate(content.split('\n'), 1):
        for pattern in patterns:
            if re.search(pattern, line, re.IGNORECASE):
                lines_found.append((i, line.strip()))
                break
    
    return {
        "referenced": len(lines_found) > 0,
        "lines": lines_found,
        "import_count": len(lines_found)
    }

def categorize_integration(package: str, main_ref: Dict, bg_ref: Dict, sched_ref: Dict) -> str:
    """Categorize integration status."""
    main_has = main_ref["referenced"]
    bg_has = bg_ref["referenced"]
    sched_has = sched_ref["referenced"]
    
    if not main_has and not bg_has and not sched_has:
        return "NOT_INTEGRATED"
    elif main_has and bg_has and sched_has:
        return "FULLY_INTEGRATED"
    elif main_has or bg_has or sched_has:
        return "PARTIALLY_INTEGRATED"
    else:
        return "UNKNOWN"

def generate_report():
    """Generate the comprehensive missing integration report."""
    print("=" * 80)
    print("MISSING MODULE INTEGRATION AUDIT REPORT")
    print("=" * 80)
    print()
    
    packages = get_all_packages()
    print(f"Found {len(packages)} packages under trading_bot/\n")
    
    # Analyze each package
    results = {}
    for pkg in packages:
        main_ref = check_references(pkg, MAIN_PY)
        bg_ref = check_references(pkg, BACKGROUND_SERVICES_PY)
        sched_ref = check_references(pkg, SCHEDULED_JOBS_PY)
        
        category = categorize_integration(pkg, main_ref, bg_ref, sched_ref)
        
        results[pkg] = {
            "category": category,
            "main": main_ref,
            "background": bg_ref,
            "scheduled": sched_ref
        }
    
    # Categorize results
    not_integrated = []
    partially_integrated = []
    fully_integrated = []
    
    for pkg, data in results.items():
        if data["category"] == "NOT_INTEGRATED":
            not_integrated.append(pkg)
        elif data["category"] == "PARTIALLY_INTEGRATED":
            partially_integrated.append(pkg)
        elif data["category"] == "FULLY_INTEGRATED":
            fully_integrated.append(pkg)
    
    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total packages: {len(packages)}")
    print(f"  - NOT INTEGRATED (missing from all 3 entrypoints): {len(not_integrated)}")
    print(f"  - PARTIALLY INTEGRATED (in 1-2 entrypoints): {len(partially_integrated)}")
    print(f"  - FULLY INTEGRATED (in all 3 entrypoints): {len(fully_integrated)}")
    print()
    
    # Print NOT INTEGRATED (highest priority)
    print("=" * 80)
    print("NOT INTEGRATED MODULES (MISSING FROM ALL 3 ENTRYPOINTS)")
    print("=" * 80)
    for pkg in not_integrated:
        print(f"  - {pkg}")
    print()
    
    # Print PARTIALLY INTEGRATED
    print("=" * 80)
    print("PARTIALLY INTEGRATED MODULES")
    print("=" * 80)
    for pkg in partially_integrated:
        data = results[pkg]
        in_main = "Y" if data["main"]["referenced"] else "N"
        in_bg = "Y" if data["background"]["referenced"] else "N"
        in_sched = "Y" if data["scheduled"]["referenced"] else "N"
        print(f"  - {pkg:40s} [main:{in_main} bg:{in_bg} sched:{in_sched}]")
    print()
    
    # Detailed report for NOT INTEGRATED
    print("=" * 80)
    print("DETAILED ANALYSIS: NOT INTEGRATED MODULES")
    print("=" * 80)
    for pkg in not_integrated:
        print(f"\n{pkg}:")
        print(f"  Location: trading_bot/{pkg}/")
        print(f"  Status: NOT referenced in main.py, background_services.py, or scheduled_jobs_runner.py")
        print(f"  Recommendation: Add to background_services.py or main.py based on module purpose")
    
    # Save JSON report
    report_path = ROOT / "MISSING_INTEGRATION_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": len(packages),
                "not_integrated": len(not_integrated),
                "partially_integrated": len(partially_integrated),
                "fully_integrated": len(fully_integrated)
            },
            "not_integrated": not_integrated,
            "partially_integrated": partially_integrated,
            "fully_integrated": fully_integrated,
            "details": results
        }, f, indent=2)
    
    print(f"\n\nDetailed JSON report saved to: {report_path}")
    
    # Save markdown report
    md_path = ROOT / "MISSING_INTEGRATION_REPORT.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write("# Missing Module Integration Report\n\n")
        f.write(f"**Generated:** {Path(__file__).name}\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total packages:** {len(packages)}\n")
        f.write(f"- **NOT INTEGRATED:** {len(not_integrated)}\n")
        f.write(f"- **PARTIALLY INTEGRATED:** {len(partially_integrated)}\n")
        f.write(f"- **FULLY INTEGRATED:** {len(fully_integrated)}\n\n")
        
        f.write("## Not Integrated Modules (Priority 1)\n\n")
        f.write("These modules exist but are NOT referenced in any of the 3 entrypoints:\n\n")
        for pkg in not_integrated:
            f.write(f"- `trading_bot/{pkg}/`\n")
        
        f.write("\n## Partially Integrated Modules (Priority 2)\n\n")
        f.write("| Module | main.py | background_services.py | scheduled_jobs_runner.py |\n")
        f.write("|--------|---------|------------------------|---------------------------|\n")
        for pkg in partially_integrated:
            data = results[pkg]
            in_main = "✓" if data["main"]["referenced"] else "✗"
            in_bg = "✓" if data["background"]["referenced"] else "✗"
            in_sched = "✓" if data["scheduled"]["referenced"] else "✗"
            f.write(f"| `{pkg}` | {in_main} | {in_bg} | {in_sched} |\n")
        
        f.write("\n## Integration Recommendations\n\n")
        f.write("### High Priority (Not Integrated)\n\n")
        
        high_value = ["intelligence_core", "anti_rogue_ai", "skills", "surveillance", 
                      "voice_assistant", "mobile", "mobile_app"]
        
        for pkg in not_integrated:
            if pkg in high_value:
                f.write(f"#### `{pkg}`\n")
                f.write(f"- **Action:** Add as background service\n")
                f.write(f"- **Reason:** High-value autonomous capability\n\n")
    
    print(f"Markdown report saved to: {md_path}")
    print("\n" + "=" * 80)
    print("REPORT GENERATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    generate_report()
