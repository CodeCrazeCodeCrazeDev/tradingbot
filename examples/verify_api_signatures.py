"""
API Signature Verification
Verifies that method signatures match between components
"""

import inspect
import logging
import importlib
import sys
import os
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path
import asyncio

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api_verification.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class APIVerifier:
    """
    Verifies API signatures between components
    """
    
    def __init__(self):
        self.issues = []
        self.verified_pairs = []
    
    def verify_signature(self, caller_module: str, caller_method: str, 
                        callee_module: str, callee_method: str) -> bool:
        """
        Verify that the signature of caller_method matches callee_method
        
        Args:
            caller_module: Module containing the caller method
            caller_method: Method that calls another method
            callee_module: Module containing the called method
            callee_method: Method being called
            
        Returns:
            True if signatures are compatible, False otherwise
        """
        logger.info(f"Verifying {caller_module}.{caller_method} -> {callee_module}.{callee_method}")
        
        try:
            # Import modules
            caller_mod = importlib.import_module(caller_module)
            callee_mod = importlib.import_module(callee_module)
            
            # Get methods
            caller = self._get_method(caller_mod, caller_method)
            callee = self._get_method(callee_mod, callee_method)
            
            if not caller or not callee:
                self.issues.append({
                    'type': 'missing_method',
                    'caller': f"{caller_module}.{caller_method}",
                    'callee': f"{callee_module}.{callee_method}",
                    'error': f"Method not found: {'caller' if not caller else 'callee'}"
                })
                return False
            
            # Get signatures
            caller_sig = inspect.signature(caller)
            callee_sig = inspect.signature(callee)
            
            # Check if caller is async but callee is not
            caller_is_async = inspect.iscoroutinefunction(caller)
            callee_is_async = inspect.iscoroutinefunction(callee)
            
            if caller_is_async and not callee_is_async:
                self.issues.append({
                    'type': 'async_mismatch',
                    'caller': f"{caller_module}.{caller_method} (async)",
                    'callee': f"{callee_module}.{callee_method} (sync)",
                    'error': "Caller is async but callee is not"
                })
                return False
            
            # Check parameter compatibility
            caller_params = list(caller_sig.parameters.values())
            callee_params = list(callee_sig.parameters.values())
            
            # Remove 'self' parameter if present
            if caller_params and caller_params[0].name == 'self':
                caller_params = caller_params[1:]
            if callee_params and callee_params[0].name == 'self':
                callee_params = callee_params[1:]
            
            # Check if callee requires more parameters than caller provides
            if len(caller_params) < len([p for p in callee_params if p.default == inspect.Parameter.empty]):
                self.issues.append({
                    'type': 'parameter_count',
                    'caller': f"{caller_module}.{caller_method}{caller_sig}",
                    'callee': f"{callee_module}.{callee_method}{callee_sig}",
                    'error': "Caller provides fewer parameters than callee requires"
                })
                return False
            
            # Check parameter types
            for i, callee_param in enumerate(callee_params):
                if i >= len(caller_params):
                    # Extra parameters in callee must have defaults
                    if callee_param.default == inspect.Parameter.empty:
                        self.issues.append({
                            'type': 'missing_parameter',
                            'caller': f"{caller_module}.{caller_method}{caller_sig}",
                            'callee': f"{callee_module}.{callee_method}{callee_sig}",
                            'error': f"Callee requires parameter {callee_param.name} but caller doesn't provide it"
                        })
                        return False
                else:
                    caller_param = caller_params[i]
                    
                    # Check parameter annotations if present
                    if (callee_param.annotation != inspect.Parameter.empty and
                        caller_param.annotation != inspect.Parameter.empty and
                        callee_param.annotation != caller_param.annotation):
                        self.issues.append({
                            'type': 'type_mismatch',
                            'caller': f"{caller_module}.{caller_method}",
                            'callee': f"{callee_module}.{callee_method}",
                            'error': f"Type mismatch for parameter {callee_param.name}: "
                                    f"{caller_param.annotation} vs {callee_param.annotation}"
                        })
                        return False
            
            # Check return type
            if (caller_sig.return_annotation != inspect.Signature.empty and
                callee_sig.return_annotation != inspect.Signature.empty and
                caller_sig.return_annotation != callee_sig.return_annotation):
                self.issues.append({
                    'type': 'return_type_mismatch',
                    'caller': f"{caller_module}.{caller_method}",
                    'callee': f"{callee_module}.{callee_method}",
                    'error': f"Return type mismatch: {caller_sig.return_annotation} vs {callee_sig.return_annotation}"
                })
                return False
            
            # All checks passed
            self.verified_pairs.append({
                'caller': f"{caller_module}.{caller_method}",
                'callee': f"{callee_module}.{callee_method}",
                'async_status': f"{'async' if caller_is_async else 'sync'} -> {'async' if callee_is_async else 'sync'}"
            })
            return True
            
        except Exception as e:
            self.issues.append({
                'type': 'exception',
                'caller': f"{caller_module}.{caller_method}",
                'callee': f"{callee_module}.{callee_method}",
                'error': str(e)
            })
            logger.error(f"Error verifying {caller_module}.{caller_method} -> {callee_module}.{callee_method}: {e}")
            return False
    
    def _get_method(self, module, method_path: str) -> Optional[Callable]:
        """Get method from module by path"""
        parts = method_path.split('.')
        obj = module
        
        for part in parts:
            try:
                obj = getattr(obj, part)
            except AttributeError:
                return None
        
        return obj
    
    def verify_trading_engine_apis(self):
        """Verify APIs used by trading engine"""
        # Verify scanner interface
        self.verify_signature(
            'trading_bot.trading_engine', 'TradingEngine._process_opportunities',
            'trading_bot.opportunity_scanner.scanner_interface', 'UnifiedScanner.scan_opportunities'
        )
        
        # Verify market microstructure
        self.verify_signature(
            'trading_bot.opportunity_scanner.scanner_interface', 'UnifiedScanner._scan_momentum',
            'trading_bot.database.market_microstructure', 'MarketMicrostructure.get_metrics'
        )
        
        # Verify order flow
        self.verify_signature(
            'trading_bot.opportunity_scanner.scanner_interface', 'UnifiedScanner._scan_flow',
            'trading_bot.database.order_flow_processor', 'OrderFlowProcessor.get_order_flow_stats'
        )
        
        # Verify analytics processor
        self.verify_signature(
            'trading_bot.trading_engine', 'TradingEngine._signal_generation_loop',
            'trading_bot.database.analytics_processor', 'AnalyticsProcessor.process_data'
        )
        
        # Verify signal processor
        self.verify_signature(
            'trading_bot.trading_engine', 'TradingEngine._signal_generation_loop',
            'trading_bot.database.signal_processor', 'SignalProcessor.process_analytics'
        )
        
        # Verify execution engine
        self.verify_signature(
            'trading_bot.trading_engine', 'TradingEngine._execute_signal',
            'trading_bot.orchestrator.execution_engine', 'ExecutionEngine.execute_order'
        )
    
    def generate_report(self):
        """Generate verification report"""
        # Create report directory
        Path("reports").mkdir(exist_ok=True)
        
        # Generate report
        report = {
            'verified_pairs': self.verified_pairs,
            'issues': self.issues,
            'summary': {
                'total_verified': len(self.verified_pairs),
                'total_issues': len(self.issues),
                'issue_types': {}
            }
        }
        
        # Count issue types
        for issue in self.issues:
            issue_type = issue['type']
            report['summary']['issue_types'][issue_type] = report['summary']['issue_types'].get(issue_type, 0) + 1
        
        # Generate markdown report
        md_report = """# API Signature Verification Report

## Summary
"""
        
        if report['issues']:
            md_report += f"⚠️ **{len(report['issues'])} issues found**\n\n"
            
            # Add issue type summary
            md_report += "### Issue Types\n"
            for issue_type, count in report['summary']['issue_types'].items():
                md_report += f"- {issue_type}: {count}\n"
            
            # Add detailed issues
            md_report += "\n### Detailed Issues\n"
            for i, issue in enumerate(report['issues']):
                md_report += f"""
#### Issue {i+1}: {issue['type']}
- Caller: `{issue['caller']}`
- Callee: `{issue['callee']}`
- Error: {issue['error']}
"""
        else:
            md_report += f"✅ **All {len(report['verified_pairs'])} API signatures verified successfully**\n"
        
        # Add verified pairs
        md_report += "\n## Verified API Pairs\n"
        for pair in report['verified_pairs']:
            md_report += f"- `{pair['caller']}` → `{pair['callee']}` ({pair['async_status']})\n"
        
        # Save report
        with open("reports/api_verification_report.md", "w") as f:
            f.write(md_report)
        
        logger.info(f"API verification report generated with {len(report['issues'])} issues")
        
        return report

def main():
    # Add project root to path
    project_root = str(Path(__file__).parent.parent)
    sys.path.insert(0, project_root)
    
    # Create verifier
    verifier = APIVerifier()
    
    # Verify trading engine APIs
    verifier.verify_trading_engine_apis()
    
    # Generate report
    report = verifier.generate_report()
    
    # Print summary
    if report['issues']:
        print(f"⚠️ {len(report['issues'])} API signature issues found. See reports/api_verification_report.md for details.")
    else:
        print(f"✅ All {len(report['verified_pairs'])} API signatures verified successfully.")

if __name__ == "__main__":
    main()
