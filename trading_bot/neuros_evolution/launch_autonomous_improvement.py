#!/usr/bin/env python3
"""
Autonomous Self-Improvement Launcher
Launches the complete recursive self-improvement system
"""

import asyncio
import logging
import sys
import os
from pathlib import Path
import argparse
from datetime import datetime

# Add the neuros_evolution directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from continuous_orchestrator import ContinuousOrchestrator, OrchestrationConfig
from recursive_self_improvement import RecursiveSelfImprovementSystem
from plotcode_integration import EnhancedRecursiveSelfImprovement
from self_diagnosis_engine import EnhancedSelfDiagnosis
from code_evolution_engine import CodeEvolutionEngine

def setup_logging(log_level="INFO", log_file=None):
    """Setup comprehensive logging"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )

def create_config(args) -> OrchestrationConfig:
    """Create configuration from command line arguments"""
    return OrchestrationConfig(
        loop_interval_seconds=args.loop_interval,
        max_concurrent_evolutions=args.max_concurrent,
        scp_remote_host=args.scp_host,
        scp_remote_path=args.scp_path,
        email_notifications=args.email_notifications,
        email_recipients=args.email_recipients.split(',') if args.email_recipients else None,
        webhook_url=args.webhook_url,
        health_check_interval=args.health_interval,
        emergency_threshold=args.emergency_threshold,
        improvement_threshold=args.improvement_threshold,
        max_daily_evolutions=args.max_daily_evolutions
    )

async def run_continuous_orchestration(config: OrchestrationConfig, codebase_path: str):
    """Run continuous orchestration"""
    print("🚀 Starting Continuous Recursive Self-Improvement System")
    print("=" * 60)
    
    orchestrator = ContinuousOrchestrator(codebase_path, config)
    
    try:
        # Print startup information
        print(f"📁 Codebase Path: {codebase_path}")
        print(f"⏱️  Loop Interval: {config.loop_interval_seconds} seconds")
        print(f"🎯 Improvement Threshold: {config.improvement_threshold}%")
        print(f"🚨 Emergency Threshold: {config.emergency_threshold}%")
        print(f"📊 Max Daily Evolutions: {config.max_daily_evolutions}")
        print(f"🔄 Max Concurrent Evolutions: {config.max_concurrent_evolutions}")
        
        if config.scp_remote_host:
            print(f"🌐 Remote Backup: {config.scp_remote_host}:{config.scp_remote_path}")
        
        if config.email_notifications:
            print(f"📧 Email Notifications: Enabled")
            if config.email_recipients:
                print(f"   Recipients: {', '.join(config.email_recipients)}")
        
        if config.webhook_url:
            print(f"🔗 Webhook: {config.webhook_url}")
        
        print("\n🤖 Autonomous agents are now in control...")
        print("   They will visually test, audit, and improve the system continuously.")
        print("   You are no longer the bottleneck! 🎉")
        print("\n" + "=" * 60)
        
        # Start the orchestration
        await orchestrator.start_continuous_orchestration()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Received interrupt signal. Shutting down gracefully...")
        await orchestrator.stop_continuous_orchestration()
        print("✅ System stopped safely.")
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        await orchestrator.stop_continuous_orchestration()
        sys.exit(1)

async def run_single_evolution(codebase_path: str, app_url: str = None):
    """Run a single evolution cycle"""
    print("🔄 Running Single Evolution Cycle")
    print("=" * 40)
    
    system = RecursiveSelfImprovementSystem(codebase_path, app_url)
    
    try:
        await system.start_recursive_improvement_loop()
        
        # Print results
        summary = system.get_improvement_summary()
        print("\n📊 Evolution Results:")
        print(f"   Total Iterations: {summary['total_iterations']}")
        print(f"   Current UX Score: {summary['latest_ux_score']:.1f}")
        print(f"   Improvement Gain: {summary['improvement_gain']:.1f}")
        
    except Exception as e:
        print(f"❌ Evolution failed: {e}")
        sys.exit(1)

async def run_visual_testing(codebase_path: str, app_url: str = None):
    """Run visual testing only"""
    print("👁️  Running Visual Testing Only")
    print("=" * 35)
    
    from plotcode_integration import PlotCodeVisualTester
    
    tester = PlotCodeVisualTester()
    
    try:
        # Create test cases
        test_cases = [
            {
                'test_id': 'basic_functionality',
                'description': 'Test basic functionality',
                'visual_elements_to_check': ['button', 'input', 'navigation'],
                'expected_behaviors': ['responsive', 'interactive'],
                'user_interactions': [
                    {'action': 'click', 'element': 'button'},
                    {'action': 'type', 'element': 'input', 'text': 'test'}
                ]
            }
        ]
        
        # Convert to PlotCodeTestCase objects
        from plotcode_integration import PlotCodeTestCase
        plotcode_cases = [
            PlotCodeTestCase(
                test_id=case['test_id'],
                description=case['description'],
                visual_elements_to_check=case['visual_elements_to_check'],
                expected_behaviors=case['expected_behaviors'],
                user_interactions=case['user_interactions']
            ) for case in test_cases
        ]
        
        # Run tests
        results = await tester.test_with_plotcode(plotcode_cases)
        
        # Print results
        print("\n📊 Visual Testing Results:")
        print(f"   Test Session: {results['test_session_id']}")
        print(f"   Total Tests: {len(results['test_results'])}")
        passed_tests = sum(1 for test in results['test_results'] if test.get('passed', False))
        print(f"   Passed: {passed_tests}")
        print(f"   Failed: {len(results['test_results']) - passed_tests}")
        print(f"   Visual Issues: {len(results['visual_issues'])}")
        
        if results['visual_issues']:
            print("\n⚠️  Visual Issues Found:")
            for issue in results['visual_issues'][:5]:  # Show first 5
                print(f"   - {issue}")
        
    except Exception as e:
        print(f"❌ Visual testing failed: {e}")
        sys.exit(1)

async def run_health_diagnosis(codebase_path: str):
    """Run health diagnosis only"""
    print("🏥 Running System Health Diagnosis")
    print("=" * 40)
    
    diagnosis = EnhancedSelfDiagnosis(codebase_path)
    
    try:
        health_report = await diagnosis.diagnosis_engine.comprehensive_self_diagnosis()
        
        print("\n📊 Health Diagnosis Results:")
        print(f"   Overall Health Score: {health_report.overall_health_score:.1f}/100")
        print(f"   Critical Issues: {len(health_report.critical_issues)}")
        print(f"   Warnings: {len(health_report.warnings)}")
        print(f"   Performance Bottlenecks: {len(health_report.performance_bottlenecks)}")
        print(f"   Evolution Readiness: {health_report.evolution_readiness:.1f}%")
        
        if health_report.critical_issues:
            print("\n🚨 Critical Issues:")
            for issue in health_report.critical_issues]:
                print(f"   - {issue}")
        
        if health_report.warnings:
            print("\n⚠️  Warnings:")
            for warning in health_report.warnings[:3]:  # Show first 3
                print(f"   - {warning}")
        
        # Show top metrics
        print("\n📈 Key Metrics:")
        for metric in health_report.metrics[:5]:
            status_emoji = "✅" if metric.status == "pass" else "⚠️" if metric.status == "warning" else "🚨"
            print(f"   {status_emoji} {metric.name}: {metric.value:.1f} ({metric.status})")
        
    except Exception as e:
        print(f"❌ Health diagnosis failed: {e}")
        sys.exit(1)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Autonomous Recursive Self-Improvement System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start continuous autonomous improvement
  python launch_autonomous_improvement.py --mode continuous
  
  # Run single evolution cycle
  python launch_autonomous_improvement.py --mode single --app-url http://localhost:8080
  
  # Run visual testing only
  python launch_autonomous_improvement.py --mode visual --app-url http://localhost:8080
  
  # Run health diagnosis only
  python launch_autonomous_improvement.py --mode health
  
  # Continuous mode with custom configuration
  python launch_autonomous_improvement.py --mode continuous \\
    --loop-interval 600 --improvement-threshold 85 \\
    --scp-host user@server.com --scp-path /backups/ \\
    --email-notifications --email-recipients admin@company.com
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['continuous', 'single', 'visual', 'health'],
        default='continuous',
        help='Operation mode (default: continuous)'
    )
    
    parser.add_argument(
        '--codebase-path',
        default='.',
        help='Path to codebase (default: current directory)'
    )
    
    parser.add_argument(
        '--app-url',
        help='Application URL for testing (e.g., http://localhost:8080)'
    )
    
    # Continuous mode configuration
    parser.add_argument(
        '--loop-interval',
        type=int,
        default=300,
        help='Loop interval in seconds (default: 300)'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=3,
        help='Maximum concurrent evolutions (default: 3)'
    )
    
    parser.add_argument(
        '--improvement-threshold',
        type=float,
        default=80.0,
        help='UX score improvement threshold (default: 80.0)'
    )
    
    parser.add_argument(
        '--emergency-threshold',
        type=float,
        default=50.0,
        help='Health score emergency threshold (default: 50.0)'
    )
    
    parser.add_argument(
        '--max-daily-evolutions',
        type=int,
        default=10,
        help='Maximum evolutions per day (default: 10)'
    )
    
    parser.add_argument(
        '--health-interval',
        type=int,
        default=60,
        help='Health check interval in seconds (default: 60)'
    )
    
    # SCP configuration
    parser.add_argument(
        '--scp-host',
        help='SCP remote host (user@server.com)'
    )
    
    parser.add_argument(
        '--scp-path',
        default='/backups/trading_bot/',
        help='SCP remote path (default: /backups/trading_bot/)'
    )
    
    # Notification configuration
    parser.add_argument(
        '--email-notifications',
        action='store_true',
        help='Enable email notifications'
    )
    
    parser.add_argument(
        '--email-recipients',
        help='Comma-separated list of email recipients'
    )
    
    parser.add_argument(
        '--webhook-url',
        help='Webhook URL for notifications'
    )
    
    # Logging configuration
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        help='Log file path'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    
    # Print startup banner
    print("🤖 Autonomous Recursive Self-Improvement System")
    print("=" * 50)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Mode: {args.mode}")
    print(f"📁 Codebase: {args.codebase_path}")
    
    # Run the appropriate mode
    try:
        if args.mode == 'continuous':
            config = create_config(args)
            asyncio.run(run_continuous_orchestration(config, args.codebase_path))
        
        elif args.mode == 'single':
            asyncio.run(run_single_evolution(args.codebase_path, args.app_url))
        
        elif args.mode == 'visual':
            asyncio.run(run_visual_testing(args.codebase_path, args.app_url))
        
        elif args.mode == 'health':
            asyncio.run(run_health_diagnosis(args.codebase_path))
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! The autonomous agents will miss you.")
        sys.exit(0)
    
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
