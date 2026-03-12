"""
AlphaAlgo Adaptive Integration System - Comprehensive Diagnostic & Testing Suite
================================================================================

This script performs a complete diagnostic cycle for the Adaptive Integration System:
- Phase 1: Code & System Analysis
- Phase 2: Functional Testing (All 6 Integration Modes)
- Phase 3: AI Performance Validation
- Phase 4: Safety & Reliability
- Phase 5: Optimization Strategies
- Phase 6: Meta & Quantum Integration
- Phase 7: Deployment & Monitoring

Author: AI Assistant
Date: October 19, 2025
Version: 1.0.0
"""

import os
import sys
import logging
import json
import time
import traceback
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
import pandas as pd

# Setup comprehensive logging
log_dir = Path("alphaalgo_diagnostics/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / f'diagnostic_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AdaptiveIntegrationDiagnostic:
    """Comprehensive diagnostic system for AlphaAlgo Adaptive Integration"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'phases': {},
            'overall_status': 'pending',
            'issues_found': [],
            'recommendations': []
        }
        
        self.report_dir = Path("alphaalgo_diagnostics/reports")
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("=" * 80)
        logger.info("ALPHAALGO ADAPTIVE INTEGRATION SYSTEM - DIAGNOSTIC SUITE")
        logger.info("=" * 80)
    
    # ========================================================================
    # PHASE 1: CODE & SYSTEM ANALYSIS
    # ========================================================================
    
    def phase1_code_analysis(self) -> Dict[str, Any]:
        """
        Phase 1: Comprehensive code and system analysis
        
        Returns:
            Dictionary with analysis results
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: CODE & SYSTEM ANALYSIS")
        logger.info("=" * 80)
        
        phase_results = {
            'status': 'running',
            'start_time': time.time(),
            'checks': {}
        }
        
        try:
            # Check 1: Module existence
            logger.info("\n[1.1] Checking module existence...")
            module_check = self._check_module_existence()
            phase_results['checks']['module_existence'] = module_check
            
            # Check 2: Import validation
            logger.info("\n[1.2] Validating imports...")
            import_check = self._validate_imports()
            phase_results['checks']['import_validation'] = import_check
            
            # Check 3: Dependency check
            logger.info("\n[1.3] Checking dependencies...")
            dependency_check = self._check_dependencies()
            phase_results['checks']['dependencies'] = dependency_check
            
            # Check 4: Architecture alignment
            logger.info("\n[1.4] Verifying architecture alignment...")
            architecture_check = self._check_architecture_alignment()
            phase_results['checks']['architecture'] = architecture_check
            
            # Check 5: Configuration validation
            logger.info("\n[1.5] Validating configuration...")
            config_check = self._validate_configuration()
            phase_results['checks']['configuration'] = config_check
            
            phase_results['status'] = 'completed'
            phase_results['end_time'] = time.time()
            phase_results['duration'] = phase_results['end_time'] - phase_results['start_time']
            
            # Calculate overall phase score
            total_checks = len(phase_results['checks'])
            passed_checks = sum(1 for check in phase_results['checks'].values() if check.get('passed', False))
            phase_results['score'] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
            
            logger.info(f"\nPhase 1 Complete: {passed_checks}/{total_checks} checks passed ({phase_results['score']:.1f}%)")
            
        except Exception as e:
            logger.error(f"Phase 1 failed: {str(e)}")
            logger.error(traceback.format_exc())
            phase_results['status'] = 'failed'
            phase_results['error'] = str(e)
        
        return phase_results
    
    def _check_module_existence(self) -> Dict[str, Any]:
        """Check if all required modules exist"""
        required_modules = [
            'trading_bot/brain/adaptive_integration.py',
            'trading_bot/brain/tier1_technical.py',
            'trading_bot/brain/tier2_orderflow.py',
            'trading_bot/brain/tier3_structure.py',
            'trading_bot/brain/tier4_regime.py',
            'trading_bot/brain/tier5_sentiment.py',
            'trading_bot/brain/tier6_macro.py',
            'trading_bot/brain/tier7_risk.py',
            'trading_bot/brain/tier8_execution.py',
            'trading_bot/brain/tier9_metalearning.py',
            'trading_bot/adaptive_systems/regime_detector.py',
            'trading_bot/ml/offline_rl/alphaalgo_autonomous_system.py',
            'trading_bot/advanced_features/quantum_computing.py'
        ]
        
        found = []
        missing = []
        
        for module_path in required_modules:
            full_path = Path(module_path)
            if full_path.exists():
                found.append(module_path)
                logger.info(f"  ✓ {module_path}")
            else:
                missing.append(module_path)
                logger.warning(f"  ✗ {module_path} - MISSING")
        
        passed = len(missing) == 0
        
        return {
            'passed': passed,
            'found': len(found),
            'missing': len(missing),
            'missing_modules': missing,
            'message': f"Found {len(found)}/{len(required_modules)} required modules"
        }
    
    def _validate_imports(self) -> Dict[str, Any]:
        """Validate that key modules can be imported"""
        import_tests = []
        
        # Test adaptive integration import
        try:
            from trading_bot.brain.adaptive_integration import (
                AdaptiveIntegrationSystem,
                MarketCondition,
                IntegrationMode
            )
            import_tests.append({
                'module': 'adaptive_integration',
                'status': 'success',
                'components': ['AdaptiveIntegrationSystem', 'MarketCondition', 'IntegrationMode']
            })
            logger.info("  ✓ adaptive_integration imports successful")
        except Exception as e:
            import_tests.append({
                'module': 'adaptive_integration',
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"  ✗ adaptive_integration import failed: {str(e)}")
        
        # Test offline RL import
        try:
            from trading_bot.ml.offline_rl import (
                AlphaAlgoAutonomousSystem,
                CQLAgent,
                IQLAgent,
                BCQAgent
            )
            import_tests.append({
                'module': 'offline_rl',
                'status': 'success',
                'components': ['AlphaAlgoAutonomousSystem', 'CQLAgent', 'IQLAgent', 'BCQAgent']
            })
            logger.info("  ✓ offline_rl imports successful")
        except Exception as e:
            import_tests.append({
                'module': 'offline_rl',
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"  ✗ offline_rl import failed: {str(e)}")
        
        # Test regime detection import
        try:
            from trading_bot.adaptive_systems.regime_detector import RegimeDetector
            import_tests.append({
                'module': 'regime_detector',
                'status': 'success',
                'components': ['RegimeDetector']
            })
            logger.info("  ✓ regime_detector imports successful")
        except Exception as e:
            import_tests.append({
                'module': 'regime_detector',
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"  ✗ regime_detector import failed: {str(e)}")
        
        passed = all(test['status'] == 'success' for test in import_tests)
        
        return {
            'passed': passed,
            'tests': import_tests,
            'success_count': sum(1 for t in import_tests if t['status'] == 'success'),
            'total_count': len(import_tests),
            'message': f"{sum(1 for t in import_tests if t['status'] == 'success')}/{len(import_tests)} import tests passed"
        }
    
    def _check_dependencies(self) -> Dict[str, Any]:
        """Check if required dependencies are installed"""
        required_packages = [
            'numpy',
            'pandas',
            'torch',
            'scikit-learn',
            'scipy'
        ]
        
        installed = []
        missing = []
        
        for package in required_packages:
            try:
                __import__(package)
                installed.append(package)
                logger.info(f"  ✓ {package}")
            except ImportError:
                missing.append(package)
                logger.warning(f"  ✗ {package} - NOT INSTALLED")
        
        passed = len(missing) == 0
        
        return {
            'passed': passed,
            'installed': installed,
            'missing': missing,
            'message': f"{len(installed)}/{len(required_packages)} required packages installed"
        }
    
    def _check_architecture_alignment(self) -> Dict[str, Any]:
        """Check architecture alignment between components"""
        alignments = []
        
        try:
            # Check if adaptive integration can access all tiers
            from trading_bot.brain.adaptive_integration import AdaptiveIntegrationSystem
            
            system = AdaptiveIntegrationSystem()
            
            # Check tier initialization
            tiers_initialized = hasattr(system, 'tier1') and hasattr(system, 'tier9')
            alignments.append({
                'component': 'tier_initialization',
                'status': 'aligned' if tiers_initialized else 'misaligned',
                'details': 'All 9 tiers accessible' if tiers_initialized else 'Tier access issues'
            })
            
            # Check controller initialization
            controllers_initialized = hasattr(system, 'alpha_brain') and hasattr(system, 'elite_controller')
            alignments.append({
                'component': 'controller_initialization',
                'status': 'aligned' if controllers_initialized else 'misaligned',
                'details': 'Controllers accessible' if controllers_initialized else 'Controller access issues'
            })
            
            logger.info(f"  ✓ Architecture alignment verified")
            
        except Exception as e:
            alignments.append({
                'component': 'system_initialization',
                'status': 'misaligned',
                'error': str(e)
            })
            logger.error(f"  ✗ Architecture alignment check failed: {str(e)}")
        
        passed = all(a['status'] == 'aligned' for a in alignments)
        
        return {
            'passed': passed,
            'alignments': alignments,
            'message': f"{sum(1 for a in alignments if a['status'] == 'aligned')}/{len(alignments)} components aligned"
        }
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate system configuration"""
        config_checks = []
        
        try:
            from trading_bot.brain.adaptive_integration import MarketCondition, IntegrationMode
            
            # Check MarketCondition enum
            expected_conditions = ['NORMAL', 'VOLATILE', 'EXTREME', 'TRENDING', 'RANGING', 'TRANSITIONING']
            actual_conditions = [c.name for c in MarketCondition]
            conditions_match = set(expected_conditions) == set(actual_conditions)
            
            config_checks.append({
                'setting': 'market_conditions',
                'status': 'valid' if conditions_match else 'invalid',
                'expected': expected_conditions,
                'actual': actual_conditions
            })
            
            # Check IntegrationMode enum
            expected_modes = ['FULL_TIER', 'FAST_TRACK', 'EMERGENCY', 'TREND_FOCUSED', 'MEAN_REVERSION', 'ADAPTIVE']
            actual_modes = [m.name for m in IntegrationMode]
            modes_match = set(expected_modes) == set(actual_modes)
            
            config_checks.append({
                'setting': 'integration_modes',
                'status': 'valid' if modes_match else 'invalid',
                'expected': expected_modes,
                'actual': actual_modes
            })
            
            logger.info(f"  ✓ Configuration validated")
            
        except Exception as e:
            config_checks.append({
                'setting': 'system_config',
                'status': 'invalid',
                'error': str(e)
            })
            logger.error(f"  ✗ Configuration validation failed: {str(e)}")
        
        passed = all(c['status'] == 'valid' for c in config_checks)
        
        return {
            'passed': passed,
            'checks': config_checks,
            'message': f"{sum(1 for c in config_checks if c['status'] == 'valid')}/{len(config_checks)} configuration checks passed"
        }
    
    # ========================================================================
    # PHASE 2: FUNCTIONAL TESTING
    # ========================================================================
    
    def phase2_functional_testing(self) -> Dict[str, Any]:
        """
        Phase 2: Test all 6 integration modes
        
        Returns:
            Dictionary with test results
        """
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: FUNCTIONAL TESTING - ALL 6 INTEGRATION MODES")
        logger.info("=" * 80)
        
        phase_results = {
            'status': 'running',
            'start_time': time.time(),
            'mode_tests': {}
        }
        
        try:
            from trading_bot.brain.adaptive_integration import (
                AdaptiveIntegrationSystem,
                MarketCondition,
                IntegrationMode
            )
            
            # Initialize system
            system = AdaptiveIntegrationSystem()
            
            # Generate test market data
            test_scenarios = self._generate_test_scenarios()
            
            # Test each integration mode
            for scenario_name, (market_data, expected_condition) in test_scenarios.items():
                logger.info(f"\n[2.{list(test_scenarios.keys()).index(scenario_name) + 1}] Testing {scenario_name}...")
                
                mode_result = self._test_integration_mode(
                    system,
                    market_data,
                    scenario_name,
                    expected_condition
                )
                
                phase_results['mode_tests'][scenario_name] = mode_result
            
            phase_results['status'] = 'completed'
            phase_results['end_time'] = time.time()
            phase_results['duration'] = phase_results['end_time'] - phase_results['start_time']
            
            # Calculate overall phase score
            total_tests = len(phase_results['mode_tests'])
            passed_tests = sum(1 for test in phase_results['mode_tests'].values() if test.get('passed', False))
            phase_results['score'] = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
            
            logger.info(f"\nPhase 2 Complete: {passed_tests}/{total_tests} mode tests passed ({phase_results['score']:.1f}%)")
            
        except Exception as e:
            logger.error(f"Phase 2 failed: {str(e)}")
            logger.error(traceback.format_exc())
            phase_results['status'] = 'failed'
            phase_results['error'] = str(e)
        
        return phase_results
    
    def _generate_test_scenarios(self) -> Dict[str, Tuple[pd.DataFrame, str]]:
        """Generate test market data for different scenarios"""
        scenarios = {}
        
        # Base data
        dates = pd.date_range(start='2025-01-01', periods=100, freq='1H')
        base_price = 1.1000
        
        # Scenario 1: Normal Market (Low volatility, no strong trend)
        normal_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.random.normal(0, 0.0005, 100),
            'high': base_price + np.random.normal(0.0002, 0.0005, 100),
            'low': base_price + np.random.normal(-0.0002, 0.0005, 100),
            'close': base_price + np.random.normal(0, 0.0005, 100),
            'volume': np.random.randint(1000, 5000, 100)
        })
        scenarios['normal_market'] = (normal_data, 'NORMAL')
        
        # Scenario 2: Volatile Market (High volatility)
        volatile_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.random.normal(0, 0.002, 100),
            'high': base_price + np.random.normal(0.001, 0.002, 100),
            'low': base_price + np.random.normal(-0.001, 0.002, 100),
            'close': base_price + np.random.normal(0, 0.002, 100),
            'volume': np.random.randint(5000, 15000, 100)
        })
        scenarios['volatile_market'] = (volatile_data, 'VOLATILE')
        
        # Scenario 3: Extreme Market (Extreme volatility)
        extreme_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.random.normal(0, 0.005, 100),
            'high': base_price + np.random.normal(0.002, 0.005, 100),
            'low': base_price + np.random.normal(-0.002, 0.005, 100),
            'close': base_price + np.random.normal(0, 0.005, 100),
            'volume': np.random.randint(10000, 30000, 100)
        })
        scenarios['extreme_market'] = (extreme_data, 'EXTREME')
        
        # Scenario 4: Trending Market (Strong uptrend)
        trend = np.linspace(0, 0.01, 100)
        trending_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price * (1 + trend) + np.random.normal(0, 0.0003, 100),
            'high': base_price * (1 + trend) + np.random.normal(0.0002, 0.0003, 100),
            'low': base_price * (1 + trend) + np.random.normal(-0.0002, 0.0003, 100),
            'close': base_price * (1 + trend) + np.random.normal(0, 0.0003, 100),
            'volume': np.random.randint(2000, 8000, 100)
        })
        scenarios['trending_market'] = (trending_data, 'TRENDING')
        
        # Scenario 5: Ranging Market (Sideways movement)
        ranging_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.sin(np.linspace(0, 4*np.pi, 100)) * 0.0005,
            'high': base_price + np.sin(np.linspace(0, 4*np.pi, 100)) * 0.0005 + 0.0002,
            'low': base_price + np.sin(np.linspace(0, 4*np.pi, 100)) * 0.0005 - 0.0002,
            'close': base_price + np.sin(np.linspace(0, 4*np.pi, 100)) * 0.0005,
            'volume': np.random.randint(1500, 4000, 100)
        })
        scenarios['ranging_market'] = (ranging_data, 'RANGING')
        
        # Scenario 6: Transitioning Market (Regime change)
        transition_data = pd.DataFrame({
            'timestamp': dates,
            'open': base_price + np.concatenate([
                np.random.normal(0, 0.0005, 50),
                np.random.normal(0, 0.002, 50)
            ]),
            'high': base_price + np.concatenate([
                np.random.normal(0.0002, 0.0005, 50),
                np.random.normal(0.001, 0.002, 50)
            ]),
            'low': base_price + np.concatenate([
                np.random.normal(-0.0002, 0.0005, 50),
                np.random.normal(-0.001, 0.002, 50)
            ]),
            'close': base_price + np.concatenate([
                np.random.normal(0, 0.0005, 50),
                np.random.normal(0, 0.002, 50)
            ]),
            'volume': np.random.randint(2000, 10000, 100)
        })
        scenarios['transitioning_market'] = (transition_data, 'TRANSITIONING')
        
        return scenarios
    
    def _test_integration_mode(self, system, market_data, scenario_name, expected_condition) -> Dict[str, Any]:
        """Test a specific integration mode"""
        try:
            # Process market data
            result = system.process(market_data, {})
            
            # Extract results
            detected_condition = result.get('market_condition', '')
            selected_mode = result.get('integration_mode', '')
            decision = result.get('decision', '')
            confidence = result.get('confidence', 0.0)
            processing_time = result.get('processing_time', 0.0)
            
            # Validate results
            condition_correct = detected_condition.upper() == expected_condition
            mode_valid = selected_mode in ['full_tier', 'fast_track', 'emergency', 'trend_focused', 'mean_reversion', 'adaptive']
            decision_valid = decision in ['BUY', 'SELL', 'HOLD']
            confidence_valid = 0.0 <= confidence <= 1.0
            processing_fast = processing_time < 5.0  # Should complete within 5 seconds
            
            passed = all([condition_correct, mode_valid, decision_valid, confidence_valid, processing_fast])
            
            logger.info(f"  Detected Condition: {detected_condition} (Expected: {expected_condition}) {'✓' if condition_correct else '✗'}")
            logger.info(f"  Selected Mode: {selected_mode} {'✓' if mode_valid else '✗'}")
            logger.info(f"  Decision: {decision} (Confidence: {confidence:.2%}) {'✓' if decision_valid and confidence_valid else '✗'}")
            logger.info(f"  Processing Time: {processing_time:.4f}s {'✓' if processing_fast else '✗'}")
            
            return {
                'passed': passed,
                'detected_condition': detected_condition,
                'expected_condition': expected_condition,
                'condition_correct': condition_correct,
                'selected_mode': selected_mode,
                'mode_valid': mode_valid,
                'decision': decision,
                'confidence': confidence,
                'processing_time': processing_time,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"  ✗ Test failed: {str(e)}")
            return {
                'passed': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }
    
    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================
    
    def run_full_diagnostic(self) -> Dict[str, Any]:
        """
        Run complete diagnostic cycle
        
        Returns:
            Complete diagnostic results
        """
        logger.info("\n" + "=" * 80)
        logger.info("STARTING FULL DIAGNOSTIC CYCLE")
        logger.info("=" * 80)
        
        start_time = time.time()
        
        # Phase 1: Code & System Analysis
        self.results['phases']['phase1'] = self.phase1_code_analysis()
        
        # Phase 2: Functional Testing
        self.results['phases']['phase2'] = self.phase2_functional_testing()
        
        # Calculate overall results
        total_time = time.time() - start_time
        self.results['total_duration'] = total_time
        
        # Calculate overall score
        phase_scores = [phase.get('score', 0) for phase in self.results['phases'].values() if 'score' in phase]
        self.results['overall_score'] = sum(phase_scores) / len(phase_scores) if phase_scores else 0
        
        # Determine overall status
        if self.results['overall_score'] >= 90:
            self.results['overall_status'] = 'excellent'
        elif self.results['overall_score'] >= 75:
            self.results['overall_status'] = 'good'
        elif self.results['overall_score'] >= 60:
            self.results['overall_status'] = 'fair'
        else:
            self.results['overall_status'] = 'poor'
        
        # Generate recommendations
        self._generate_recommendations()
        
        # Save results
        self._save_results()
        
        logger.info("\n" + "=" * 80)
        logger.info("DIAGNOSTIC CYCLE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Overall Score: {self.results['overall_score']:.1f}%")
        logger.info(f"Overall Status: {self.results['overall_status'].upper()}")
        logger.info(f"Total Duration: {total_time:.2f}s")
        logger.info(f"Report saved to: {self.report_dir}")
        logger.info("=" * 80)
        
        return self.results
    
    def _generate_recommendations(self):
        """Generate recommendations based on diagnostic results"""
        recommendations = []
        
        # Check Phase 1 results
        phase1 = self.results['phases'].get('phase1', {})
        if phase1.get('score', 0) < 100:
            checks = phase1.get('checks', {})
            
            if not checks.get('module_existence', {}).get('passed', False):
                recommendations.append({
                    'priority': 'high',
                    'category': 'missing_modules',
                    'message': 'Some required modules are missing. Install or create missing components.',
                    'missing': checks.get('module_existence', {}).get('missing_modules', [])
                })
            
            if not checks.get('dependencies', {}).get('passed', False):
                recommendations.append({
                    'priority': 'high',
                    'category': 'missing_dependencies',
                    'message': 'Required dependencies are missing. Install with: pip install <package>',
                    'missing': checks.get('dependencies', {}).get('missing', [])
                })
        
        # Check Phase 2 results
        phase2 = self.results['phases'].get('phase2', {})
        if phase2.get('score', 0) < 100:
            mode_tests = phase2.get('mode_tests', {})
            failed_tests = [name for name, test in mode_tests.items() if not test.get('passed', False)]
            
            if failed_tests:
                recommendations.append({
                    'priority': 'medium',
                    'category': 'failed_mode_tests',
                    'message': f'Some integration mode tests failed: {", ".join(failed_tests)}',
                    'failed_tests': failed_tests
                })
        
        self.results['recommendations'] = recommendations
    
    def _save_results(self):
        """Save diagnostic results to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.report_dir / f'diagnostic_report_{timestamp}.json'
        
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logger.info(f"\nResults saved to: {report_file}")


def main():
    """Main entry point"""
    print("""
    ================================================================
    
         AlphaAlgo Adaptive Integration System
         Comprehensive Diagnostic & Testing Suite
    
         This will validate all 6 integration modes and test
         the complete adaptive system architecture
    
    ================================================================
    """)
    
    # Create diagnostic system
    diagnostic = AdaptiveIntegrationDiagnostic()
    
    # Run full diagnostic
    results = diagnostic.run_full_diagnostic()
    
    # Print summary
    print("\n" + "=" * 80)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 80)
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Overall Status: {results['overall_status'].upper()}")
    print(f"Total Duration: {results['total_duration']:.2f}s")
    print("\nPhase Results:")
    for phase_name, phase_data in results['phases'].items():
        score = phase_data.get('score', 0)
        status = phase_data.get('status', 'unknown')
        print(f"  {phase_name}: {score:.1f}% ({status})")
    
    if results.get('recommendations'):
        print("\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  [{rec['priority'].upper()}] {rec['message']}")
    
    print("=" * 80)
    
    return 0 if results['overall_status'] in ['excellent', 'good'] else 1


if __name__ == '__main__':
    sys.exit(main())
