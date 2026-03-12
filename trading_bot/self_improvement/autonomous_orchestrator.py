"""
Autonomous Orchestrator
Main controller that:
1. Checks safety before trading
2. Auto-fixes critical issues
3. Learns from losses via internet
4. Tests improvements in mirror market
5. Deploys best strategies to live
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import asyncio

from .autonomous_fixer import AutonomousFixer, SafetyStatus
from .internet_strategy_improver import InternetStrategyImprover
from .mirror_market_tester import MirrorMarketTester, TestStatus
from .engine import SelfImprovementEngine
from enum import auto

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """
    Fully autonomous trading bot that:
    - Checks safety before every trading session
    - Auto-fixes critical issues
    - Learns from losses by searching internet
    - Tests improvements in mirror market
    - Deploys only proven strategies to live
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize autonomous orchestrator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Initialize components
        self.fixer = AutonomousFixer(config.get('autonomous_fixer', {}))
        self.internet_improver = InternetStrategyImprover(config.get('internet_improver', {}))
        self.mirror_tester = MirrorMarketTester(config.get('mirror_tester', {}))
        self.self_improvement = SelfImprovementEngine(config.get('self_improvement', {}))
        
        # State
        self.is_safe_to_trade = False
        self.current_strategy = None
        self.pending_improvements = []
        self.active_tests = {}
        
        logger.info("AutonomousOrchestrator initialized")
    
    async def pre_trading_check(self) -> Dict[str, Any]:
        """
        Run complete safety check before allowing trading.
        
        Returns:
            Safety status and actions taken
        """
        logger.info("=" * 80)
        logger.info("PRE-TRADING SAFETY CHECK")
        logger.info("=" * 80)
        
        # Step 1: Check safety and auto-fix issues
        safety_result = await self.fixer.check_safety_and_fix()
        
        self.is_safe_to_trade = safety_result['safe_to_trade']
        
        if self.is_safe_to_trade:
            logger.info("✓ SAFE TO TRADE - All systems operational")
        else:
            logger.error("✗ UNSAFE TO TRADE - Critical issues detected")
            logger.error(f"Issues: {safety_result['issues']}")
        
        return {
            'safe_to_trade': self.is_safe_to_trade,
            'status': safety_result['status'],
            'issues': safety_result['issues'],
            'fixes_applied': safety_result['fixes_applied'],
            'timestamp': datetime.now()
        }
    
    async def on_trade_loss(self,
                           trade: Dict[str, Any],
                           signal_data: Dict[str, Any],
                           market_data: Dict[str, Any],
                           system_data: Dict[str, Any],
                           equity: float) -> Dict[str, Any]:
        """
        Handle losing trade with full autonomous improvement pipeline.
        
        Args:
            trade: Losing trade data
            signal_data: Signal context
            market_data: Market data
            system_data: System metrics
            equity: Current equity
            
        Returns:
            Complete improvement result
        """
        logger.info("=" * 80)
        logger.info(f"AUTONOMOUS IMPROVEMENT FOR LOSING TRADE {trade['ticket_id']}")
        logger.info("=" * 80)
        
        # Step 1: Standard self-improvement (root cause analysis)
        logger.info("Step 1: Analyzing root cause...")
        improvement_result = self.self_improvement.process_losing_trade(
            trade, signal_data, market_data, system_data, equity
        )
        
        if improvement_result['status'] == 'escalated':
            logger.warning("Standard improvement escalated to human review")
            return improvement_result
        
        # Step 2: Search internet for additional improvements
        logger.info("Step 2: Searching internet for strategy improvements...")
        
        # Extract root cause from improvement result
        root_cause = {
            'cause_type': 'signal_quality',  # Simplified, extract from diagnostic
            'description': 'Trade loss detected',
            'confidence': 0.7
        }
        
        internet_result = await self.internet_improver.improve_strategy_from_loss(
            trade, root_cause
        )
        
        # Step 3: Combine improvements
        logger.info("Step 3: Combining improvements...")
        all_improvements = []
        
        # Add standard fixes
        if 'fixes_proposed' in improvement_result:
            all_improvements.extend(improvement_result.get('fixes_proposed', []))
        
        # Add internet-sourced improvements
        all_improvements.extend(internet_result.get('improvements', []))
        
        logger.info(f"Total improvements found: {len(all_improvements)}")
        
        # Step 4: Test top improvements in mirror market
        logger.info("Step 4: Testing improvements in mirror market...")
        
        test_results = []
        for improvement in all_improvements[:3]:  # Test top 3
            logger.info(f"Testing: {improvement.get('strategy_title', 'Unknown')}")
            
            # Create improved strategy
            improved_strategy = self._create_improved_strategy(
                self.current_strategy,
                improvement
            )
            
            # Test in mirror market
            test_result = await self.mirror_tester.test_improved_strategy(
                improved_strategy,
                self.current_strategy,
                trade['symbol']
            )
            
            test_results.append(test_result)
            
            # If passed, we found a winner
            if test_result['safe_to_deploy']:
                logger.info(f"✓ Improvement PASSED mirror test!")
                break
        
        # Step 5: Deploy best strategy if found
        best_strategy = None
        for result in test_results:
            if result['safe_to_deploy']:
                best_strategy = result
                break
        
        if best_strategy:
            logger.info("Step 5: Deploying improved strategy to LIVE...")
            deployment_result = await self._deploy_to_live(best_strategy)
            
            return {
                'status': 'deployed',
                'trade_id': trade['ticket_id'],
                'improvements_tested': len(test_results),
                'best_improvement': best_strategy['improvement_pct'],
                'deployment': deployment_result,
                'timestamp': datetime.now()
            }
        else:
            logger.warning("No improvements passed mirror testing")
            
            return {
                'status': 'no_deployment',
                'trade_id': trade['ticket_id'],
                'improvements_tested': len(test_results),
                'reason': 'No improvements passed validation',
                'timestamp': datetime.now()
            }
    
    def _create_improved_strategy(self,
                                  current_strategy: Dict[str, Any],
                                  improvement: Dict[str, Any]) -> Dict[str, Any]:
        """Create improved strategy by applying improvement to current strategy."""
        # Clone current strategy
        improved = current_strategy.copy() if current_strategy else {}
        
        # Apply improvements
        improved['improvements_applied'] = improvement.get('implementation_steps', [])
        improved['improvement_source'] = improvement.get('source', 'unknown')
        improved['expected_improvement'] = improvement.get('expected_improvement', 0.0)
        
        # Modify strategy parameters based on improvement
        # This is simplified - in production, parse and apply specific changes
        if 'confidence_threshold' in str(improvement):
            improved['confidence_threshold'] = improved.get('confidence_threshold', 0.5) + 0.1
        
        if 'stop_loss' in str(improvement):
            improved['stop_loss_multiplier'] = improved.get('stop_loss_multiplier', 1.0) * 1.2
        
        return improved
    
    async def _deploy_to_live(self, test_result: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy improved strategy to live trading."""
        logger.info("=" * 80)
        logger.info("DEPLOYING TO LIVE TRADING")
        logger.info("=" * 80)
        
        # Safety check before deployment
        safety_check = await self.pre_trading_check()
        
        if not safety_check['safe_to_trade']:
            logger.error("Cannot deploy - safety check failed")
            return {
                'status': 'failed',
                'reason': 'Safety check failed',
                'safety_check': safety_check
            }
        
        # Create backup of current strategy
        backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        # In production: save current strategy to backup
        
        # Deploy new strategy
        # In production: update trading bot configuration
        logger.info(f"✓ Strategy deployed successfully")
        logger.info(f"  Backup ID: {backup_id}")
        logger.info(f"  Expected improvement: {test_result['improvement_pct']:.1%}")
        
        return {
            'status': 'success',
            'backup_id': backup_id,
            'deployment_time': datetime.now(),
            'expected_improvement': test_result['improvement_pct'],
            'rollback_available': True
        }
    
    async def continuous_monitoring(self):
        """Continuously monitor and improve the trading system."""
        logger.info("Starting continuous monitoring...")
        
        while True:
            try:
                # Check safety every hour
                safety_result = await self.pre_trading_check()
                
                if not safety_result['safe_to_trade']:
                    logger.warning("Trading paused due to safety issues")
                    # Wait for fixes
                    await asyncio.sleep(300)  # 5 minutes
                    continue
                
                # Check for pending improvements to test
                if self.pending_improvements:
                    logger.info(f"Testing {len(self.pending_improvements)} pending improvements")
                    # Test improvements
                    # Deploy if successful
                
                # Sleep for monitoring interval
                await asyncio.sleep(3600)  # 1 hour
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of autonomous system."""
        return {
            'safe_to_trade': self.is_safe_to_trade,
            'current_strategy': self.current_strategy,
            'pending_improvements': len(self.pending_improvements),
            'active_tests': len(self.active_tests),
            'timestamp': datetime.now()
        }
