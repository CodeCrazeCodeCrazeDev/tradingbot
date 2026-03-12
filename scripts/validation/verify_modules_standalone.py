"""
Verify Each Module Runs Standalone
Tests all trading bot modules for standalone functionality
"""

import os
import sys
import io
import importlib
import traceback
from pathlib import Path
from datetime import datetime
import json

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class ModuleVerifier:
    """Verify all modules can run standalone"""
    
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
        # Critical modules that MUST work
        self.critical_modules = [
            'trading_bot.data.mt5_interface',
            'trading_bot.strategy.strategy_engine',
            'trading_bot.risk.risk_manager',
            'trading_bot.execution.paper_executor',
            'trading_bot.execution.live_executor',
        ]
        
        # Important modules
        self.important_modules = [
            'trading_bot.analysis.liquidity',
            'trading_bot.analysis.market_structure',
            'trading_bot.analysis.price_action',
            'trading_bot.analytics.performance',
            'trading_bot.backtesting.backtester',
        ]
        
        # ML modules
        self.ml_modules = [
            'trading_bot.ml.online_learning',
            'trading_bot.ml.explainable_ai',
            'trading_bot.ml.rl_environment',
            'trading_bot.ml.pattern_recognition',
        ]
        
        # Risk modules
        self.risk_modules = [
            'trading_bot.risk_management.position_sizing',
            'trading_bot.risk_management.black_swan_protection',
            'trading_bot.risk_management.drawdown_ladder',
        ]
        
        # Opportunity scanners
        self.scanner_modules = [
            'trading_bot.opportunity_scanner.market_inefficiency',
            'trading_bot.opportunity_scanner.arbitrage_detection',
            'trading_bot.opportunity_scanner.scanner_interface',
        ]
        
        # Advanced features
        self.advanced_modules = [
            'trading_bot.advanced_features.blockchain_validation',
            'trading_bot.advanced_features.quantum_computing',
        ]
    
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def print_section(self, text: str):
        """Print section header"""
        print(f"\n{'-'*80}")
        print(f"  {text}")
        print(f"{'-'*80}")
    
    def test_module(self, module_name: str, critical: bool = False) -> tuple:
        """Test if module can be imported standalone"""
        try:
            # Try to import
            module = importlib.import_module(module_name)
            
            # Check if module has expected attributes
            has_classes = any(
                isinstance(getattr(module, attr), type) 
                for attr in dir(module) 
                if not attr.startswith('_')
            )
            
            if has_classes:
                return True, "OK", None
            else:
                return True, "WARNING", "No classes found"
                
        except ImportError as e:
            error_msg = str(e)
            if "No module named" in error_msg:
                return False, "MISSING", error_msg
            else:
                return False, "IMPORT_ERROR", error_msg
        except Exception as e:
            return False, "ERROR", str(e)
    
    def test_module_group(self, modules: list, group_name: str, critical: bool = False):
        """Test a group of modules"""
        self.print_section(f"Testing {group_name}")
        
        passed = 0
        failed = 0
        warnings = 0
        
        for module_name in modules:
            success, status, error = self.test_module(module_name, critical)
            
            if success and status == "OK":
                print(f"    ✅ {module_name}")
                self.results['passed'].append(module_name)
                passed += 1
            elif success and status == "WARNING":
                print(f"    ⚠️ {module_name}: {error}")
                self.results['warnings'].append({'module': module_name, 'issue': error})
                warnings += 1
            else:
                icon = "🔴" if critical else "❌"
                print(f"    {icon} {module_name}")
                print(f"       Error: {error[:100]}")
                self.results['failed'].append({'module': module_name, 'error': error})
                failed += 1
        
        print(f"\n  Summary: {passed} passed, {failed} failed, {warnings} warnings")
        
        return passed, failed, warnings
    
    def run_all_tests(self):
        """Run all module tests"""
        self.print_header("MODULE STANDALONE VERIFICATION")
        
        print(f"  Testing all trading bot modules...")
        print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Test critical modules
        c_pass, c_fail, c_warn = self.test_module_group(
            self.critical_modules, 
            "CRITICAL MODULES (MUST WORK)", 
            critical=True
        )
        
        # Test important modules
        i_pass, i_fail, i_warn = self.test_module_group(
            self.important_modules,
            "IMPORTANT MODULES"
        )
        
        # Test ML modules
        ml_pass, ml_fail, ml_warn = self.test_module_group(
            self.ml_modules,
            "ML MODULES"
        )
        
        # Test risk modules
        r_pass, r_fail, r_warn = self.test_module_group(
            self.risk_modules,
            "RISK MANAGEMENT MODULES"
        )
        
        # Test scanner modules
        s_pass, s_fail, s_warn = self.test_module_group(
            self.scanner_modules,
            "OPPORTUNITY SCANNER MODULES"
        )
        
        # Test advanced modules
        a_pass, a_fail, a_warn = self.test_module_group(
            self.advanced_modules,
            "ADVANCED FEATURE MODULES"
        )
        
        # Generate report
        self.generate_report(
            c_pass, c_fail, c_warn,
            i_pass, i_fail, i_warn,
            ml_pass, ml_fail, ml_warn,
            r_pass, r_fail, r_warn,
            s_pass, s_fail, s_warn,
            a_pass, a_fail, a_warn
        )
    
    def generate_report(self, *args):
        """Generate final report"""
        self.print_header("MODULE VERIFICATION REPORT")
        
        # Calculate totals
        total_passed = len(self.results['passed'])
        total_failed = len(self.results['failed'])
        total_warnings = len(self.results['warnings'])
        total_tested = total_passed + total_failed + total_warnings
        
        print(f"  Verification Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"\n  RESULTS:")
        print(f"    Total Modules Tested: {total_tested}")
        print(f"    Passed: {total_passed} ✅")
        print(f"    Failed: {total_failed} ❌")
        print(f"    Warnings: {total_warnings} ⚠️")
        
        if total_tested > 0:
            success_rate = (total_passed / total_tested) * 100
            print(f"\n  SUCCESS RATE: {success_rate:.1f}%")
        
        # Show failed modules
        if total_failed > 0:
            print(f"\n  FAILED MODULES:")
            for item in self.results['failed'][:10]:
                print(f"    ❌ {item['module']}")
                print(f"       {item['error'][:100]}")
        
        # Show warnings
        if total_warnings > 0:
            print(f"\n  WARNINGS:")
            for item in self.results['warnings'][:10]:
                print(f"    ⚠️ {item['module']}: {item['issue']}")
        
        # Overall status
        print(f"\n  OVERALL STATUS:")
        if total_failed == 0 and total_warnings == 0:
            print(f"    [SUCCESS] All modules verified! ✅")
            status = "SUCCESS"
        elif total_failed == 0:
            print(f"    [WARNING] All modules work with warnings ⚠️")
            status = "WARNING"
        else:
            print(f"    [FAILED] {total_failed} modules failed ❌")
            status = "FAILED"
        
        # Save report
        report = {
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'total_tested': total_tested,
            'passed': total_passed,
            'failed': total_failed,
            'warnings': total_warnings,
            'success_rate': (total_passed / total_tested * 100) if total_tested > 0 else 0,
            'results': self.results
        }
        
        with open('module_verification_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n  Report saved to: module_verification_report.json")
        
        return status


def main():
    """Main entry point"""
    verifier = ModuleVerifier()
    status = verifier.run_all_tests()
    
    print(f"\n{'='*80}")
    print("VERIFICATION COMPLETE".center(80))
    print(f"{'='*80}\n")
    
    # Exit with appropriate code
    if status == "SUCCESS":
        sys.exit(0)
    elif status == "WARNING":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
