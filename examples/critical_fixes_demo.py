"""
Critical Fixes Demo
===================

Demonstrates all critical fix components addressing the 1,000 questions.

This demo shows:
1. Position State Manager - Position reconciliation
2. Real-Time Risk Calculator - Risk monitoring
3. Multi-Layer Kill Switch - Emergency shutdown
4. Data Validator - Data quality checks
5. Execution Quality Monitor - Execution tracking
6. Silent Failure Detector - Component monitoring
7. Config Integrity Monitor - Configuration validation
8. Regulatory Compliance - Compliance checks
9. Master Safety Orchestrator - Unified safety system
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockBrokerAdapter:
    """Mock broker adapter for demonstration"""
    
    def __init__(self):
        self.positions = []
        self.orders = []
        self.equity = 10000.0
    
    async def get_positions(self) -> List[Dict]:
        """Get open positions"""
        return self.positions
    
    async def close_position(self, ticket: str, use_market_order: bool = False) -> bool:
        """Close a position"""
        self.positions = [p for p in self.positions if p.get('ticket') != ticket]
        logger.info(f"Closed position {ticket}")
        return True
    
    def add_position(self, position: Dict):
        """Add a mock position"""
        self.positions.append(position)


async def demo_position_state_manager():
    """Demo: Position State Manager (Q22, Q21, Q2)"""
    print("\n" + "="*60)
    print("DEMO: Position State Manager")
    print("Addresses: Q22 (reconciliation), Q21 (storage), Q2 (race conditions)")
    print("="*60)
    
    from trading_bot.critical_fixes import PositionStateManager, PositionState
    from trading_bot.critical_fixes.position_state_manager import PositionStatus
    
    broker = MockBrokerAdapter()
    
    # Add a mock broker position
    broker.add_position({
        'ticket': '12345',
        'symbol': 'EURUSD',
        'quantity': 0.1,
        'direction': 'long',
        'entry_price': 1.1000,
        'current_price': 1.1050,
        'profit': 50.0
    })
    
    manager = PositionStateManager(
        broker_adapter=broker,
        db_path="demo_positions.db",
        reconciliation_interval=10,
        auto_correct=True
    )
    
    # Add a local position
    position = PositionState(
        position_id="local_001",
        symbol="EURUSD",
        direction="long",
        quantity=0.1,
        entry_price=1.1000,
        current_price=1.1050,
        unrealized_pnl=50.0,
        realized_pnl=0,
        stop_loss=1.0950,
        take_profit=1.1100,
        opened_at=datetime.now(),
        last_updated=datetime.now(),
        status=PositionStatus.OPEN,
        broker_ticket="12345"
    )
    
    success = manager.add_position(position, owner="demo")
    print(f"✓ Added position: {success}")
    
    # Perform reconciliation
    result = await manager.reconcile()
    print(f"✓ Reconciliation: {result.matched} matched, {len(result.discrepancies)} discrepancies")
    
    # Get status
    status = manager.get_reconciliation_status()
    print(f"✓ Status: {status['statistics']['total_reconciliations']} total reconciliations")
    
    return manager


async def demo_realtime_risk_calculator():
    """Demo: Real-Time Risk Calculator (Q401, Q402, Q411, Q421)"""
    print("\n" + "="*60)
    print("DEMO: Real-Time Risk Calculator")
    print("Addresses: Q401 (real-time risk), Q402 (error handling), Q411 (portfolio risk), Q421 (drawdown)")
    print("="*60)
    
    from trading_bot.critical_fixes import RealtimeRiskCalculator, RiskLimits
    
    limits = RiskLimits(
        max_risk_per_trade=0.02,
        max_drawdown=0.20,
        max_portfolio_risk=0.05,
        emergency_shutdown_drawdown=0.25
    )
    
    calculator = RealtimeRiskCalculator(limits=limits)
    
    # Simulate equity updates
    for equity in [10000, 9800, 9600, 9500, 9700, 9900, 10100]:
        calculator.update_equity(equity)
    
    # Calculate risk with positions
    positions = [
        {
            'position_id': '001',
            'symbol': 'EURUSD',
            'direction': 'long',
            'quantity': 0.1,
            'entry_price': 1.1000,
            'current_price': 1.1050,
            'stop_loss': 1.0950
        },
        {
            'position_id': '002',
            'symbol': 'GBPUSD',
            'direction': 'long',
            'quantity': 0.05,
            'entry_price': 1.2500,
            'current_price': 1.2480,
            'stop_loss': 1.2450
        }
    ]
    
    metrics = calculator.calculate_risk(equity=10000, positions=positions)
    
    print(f"✓ Current drawdown: {metrics.current_drawdown:.2%}")
    print(f"✓ Risk level: {metrics.overall_risk_level.value}")
    print(f"✓ VaR 95%: {metrics.portfolio_var_95:.2%}")
    print(f"✓ Position count: {metrics.position_count}")
    
    # Check if can open new position
    can_open, reason = calculator.can_open_position(
        symbol='USDJPY',
        quantity=0.1,
        price=150.00,
        stop_loss=149.50,
        equity=10000
    )
    print(f"✓ Can open new position: {can_open} ({reason})")
    
    return calculator


async def demo_multi_layer_kill_switch():
    """Demo: Multi-Layer Kill Switch (Q891, Q901, Q892, Q903)"""
    print("\n" + "="*60)
    print("DEMO: Multi-Layer Kill Switch")
    print("Addresses: Q891 (triggers), Q901 (multiple switches), Q892 (speed), Q903 (bypass prevention)")
    print("="*60)
    
    from trading_bot.critical_fixes import MultiLayerKillSwitch, KillSwitchLevel
    from trading_bot.critical_fixes.multi_layer_kill_switch import KillSwitchTrigger
    
    broker = MockBrokerAdapter()
    broker.add_position({'ticket': '001', 'symbol': 'EURUSD', 'volume': 0.1})
    
    kill_switch = MultiLayerKillSwitch(
        broker_adapter=broker,
        db_path="demo_kill_switch.db",
        heartbeat_timeout=30
    )
    
    print(f"✓ Initial state: active={kill_switch.is_active}, level={kill_switch.current_level.name}")
    print(f"✓ Can trade: {kill_switch.can_trade}")
    
    # Send heartbeat
    kill_switch.heartbeat()
    print("✓ Heartbeat sent")
    
    # Activate SOFT level
    event = await kill_switch.activate(
        KillSwitchLevel.SOFT,
        KillSwitchTrigger.MANUAL_CODE,
        "Demo activation",
        "demo_script"
    )
    
    print(f"✓ Activated: level={event.level.name}, shutdown_time={event.time_to_shutdown_ms:.0f}ms")
    print(f"✓ Can trade: {kill_switch.can_trade}")
    print(f"✓ Can open positions: {kill_switch.can_open_positions}")
    
    # Get status
    status = kill_switch.get_status()
    print(f"✓ Status: {status['current_level']}")
    
    return kill_switch


async def demo_data_validator():
    """Demo: Data Validator (Q71, Q62, Q91)"""
    print("\n" + "="*60)
    print("DEMO: Data Validator")
    print("Addresses: Q71 (price spikes), Q62 (staleness), Q91 (corruption)")
    print("="*60)
    
    from trading_bot.critical_fixes import DataValidator
    
    validator = DataValidator(
        max_price_change_pct=0.10,
        max_staleness_seconds=5,
        max_spread_pct=0.05
    )
    
    # Valid tick
    report = validator.validate_tick(
        symbol='EURUSD',
        bid=1.1000,
        ask=1.1002,
        timestamp=datetime.now(),
        volume=100
    )
    print(f"✓ Valid tick: quality={report.quality_level.value}, score={report.quality_score:.0f}")
    
    # Stale tick
    report = validator.validate_tick(
        symbol='EURUSD',
        bid=1.1000,
        ask=1.1002,
        timestamp=datetime.now() - timedelta(seconds=10),
        volume=100
    )
    print(f"✓ Stale tick: quality={report.quality_level.value}, issues={len(report.issues)}")
    
    # Inverted spread (error)
    report = validator.validate_tick(
        symbol='EURUSD',
        bid=1.1010,
        ask=1.1000,  # bid > ask = error
        timestamp=datetime.now(),
        volume=100
    )
    print(f"✓ Inverted spread: quality={report.quality_level.value}, usable={report.is_usable}")
    
    # Get statistics
    stats = validator.get_statistics()
    print(f"✓ Statistics: {stats['total_validated']} validated, {stats['total_issues']} issues")
    
    return validator


async def demo_execution_quality_monitor():
    """Demo: Execution Quality Monitor (Q141, Q142, Q161)"""
    print("\n" + "="*60)
    print("DEMO: Execution Quality Monitor")
    print("Addresses: Q141 (quality measurement), Q142 (slippage model), Q161 (market impact)")
    print("="*60)
    
    from trading_bot.critical_fixes import ExecutionQualityMonitor
    
    monitor = ExecutionQualityMonitor(commission_rate=0.0001)
    
    # Record order sent
    monitor.record_order_sent(
        order_id='order_001',
        symbol='EURUSD',
        direction='buy',
        quantity=0.1,
        expected_price=1.1000,
        order_type='market',
        venue='broker_1'
    )
    
    # Record execution (with slippage)
    record = monitor.record_execution(
        order_id='order_001',
        execution_id='exec_001',
        executed_price=1.1003,  # 3 pips slippage
        executed_quantity=0.1
    )
    
    if record:
        print(f"✓ Execution recorded: slippage={record.slippage_bps:.1f} bps, latency={record.latency_ms:.0f}ms")
    
    # Get expected slippage
    expected = monitor.get_expected_slippage('EURUSD', 'market')
    print(f"✓ Expected slippage model: {expected['expected_slippage_bps']:.1f} bps (confidence: {expected['confidence']})")
    
    # Get metrics
    metrics = monitor.get_metrics('hourly')
    print(f"✓ Hourly metrics: {metrics.total_executions} executions, quality={metrics.execution_quality.value}")
    
    return monitor


async def demo_silent_failure_detector():
    """Demo: Silent Failure Detector (Q851, Q852, Q853)"""
    print("\n" + "="*60)
    print("DEMO: Silent Failure Detector")
    print("Addresses: Q851 (silent failures), Q852 (accumulation), Q853 (corruption)")
    print("="*60)
    
    from trading_bot.critical_fixes import SilentFailureDetector
    
    detector = SilentFailureDetector(
        heartbeat_timeout=10,
        auto_remediate=False
    )
    
    # Register components
    detector.register_component(
        component_id='data_feed',
        name='Market Data Feed',
        heartbeat_interval=5,
        output_interval=1,
        expected_throughput=60  # 60 ticks per minute
    )
    
    detector.register_component(
        component_id='strategy',
        name='Trading Strategy',
        heartbeat_interval=10,
        output_interval=30
    )
    
    # Send heartbeats
    detector.heartbeat('data_feed')
    detector.heartbeat('strategy')
    print("✓ Heartbeats sent")
    
    # Record outputs
    detector.record_output('data_feed', {'price': 1.1000}, latency_ms=5)
    detector.record_output('strategy', {'signal': 'buy'}, latency_ms=100)
    print("✓ Outputs recorded")
    
    # Record state snapshot
    detector.record_state_snapshot('strategy', {
        'positions': 2,
        'equity': 10000,
        'signals_today': 5
    })
    print("✓ State snapshot recorded")
    
    # Get health
    health = detector.get_component_health('data_feed')
    if health:
        print(f"✓ Data feed health: {health.status.value}")
    
    # Get statistics
    stats = detector.get_statistics()
    print(f"✓ Statistics: {stats['components_monitored']} components monitored")
    
    return detector


async def demo_config_integrity_monitor():
    """Demo: Configuration Integrity Monitor (Q781, Q791, Q789)"""
    print("\n" + "="*60)
    print("DEMO: Configuration Integrity Monitor")
    print("Addresses: Q781 (management), Q791 (validation), Q789 (tampering)")
    print("="*60)
    
    from trading_bot.critical_fixes import ConfigIntegrityMonitor
    
    monitor = ConfigIntegrityMonitor()
    
    # Validate a configuration
    test_config = {
        'max_risk_per_trade': 0.02,
        'max_drawdown': 0.20,
        'max_leverage': 2.0,
        'emergency_shutdown_drawdown': 0.25,
        'max_position_size': 0.10,
        'max_open_positions': 10,
        'trading_enabled': True,
        'trading_mode': 'paper',
        'kill_switch_enabled': True
    }
    
    errors = monitor.validate_config(test_config)
    print(f"✓ Validation: {len(errors)} errors")
    
    # Try to update a parameter
    success, error = monitor.update_parameter('max_risk_per_trade', 0.03, source='demo')
    print(f"✓ Update max_risk_per_trade: success={success}")
    
    # Try to update immutable parameter
    success, error = monitor.update_parameter('emergency_shutdown_drawdown', 0.50, source='demo')
    print(f"✓ Update immutable param: success={success}, error={error}")
    
    # Check integrity
    is_valid, issues = monitor.check_integrity()
    print(f"✓ Integrity check: valid={is_valid}")
    
    # Get status
    status = monitor.get_status()
    print(f"✓ Status: version={status['current_version']}, params={status['parameters_count']}")
    
    return monitor


async def demo_regulatory_compliance():
    """Demo: Regulatory Compliance Monitor (Q931, Q941, Q961)"""
    print("\n" + "="*60)
    print("DEMO: Regulatory Compliance Monitor")
    print("Addresses: Q931 (regulations), Q941 (broker constraints), Q961 (reporting)")
    print("="*60)
    
    from trading_bot.critical_fixes import RegulatoryComplianceMonitor
    from trading_bot.critical_fixes.regulatory_compliance import RegulatoryRegime, BrokerConstraint
    
    # Add broker constraints
    constraints = [
        BrokerConstraint(
            constraint_id='max_order',
            name='Maximum Order Value',
            description='Maximum single order value',
            constraint_type='max_order_value',
            value=100000
        )
    ]
    
    compliance = RegulatoryComplianceMonitor(
        regime=RegulatoryRegime.SEC,
        broker_constraints=constraints,
        db_path="demo_compliance.db"
    )
    
    # Pre-trade compliance check
    can_trade, violations = compliance.check_pre_trade(
        symbol='AAPL',
        direction='buy',
        quantity=100,
        price=150.00,
        equity=30000,  # Above PDT threshold
        existing_position=0
    )
    print(f"✓ Pre-trade check: can_trade={can_trade}, violations={len(violations)}")
    
    # Record a trade
    report = compliance.record_trade(
        trade_id='trade_001',
        symbol='AAPL',
        direction='buy',
        quantity=100,
        price=150.00,
        venue='NYSE',
        order_type='market',
        execution_time_ms=50
    )
    print(f"✓ Trade recorded: {report.report_id}")
    
    # Get compliance status
    status = compliance.get_compliance_status()
    print(f"✓ Compliance status: compliant={status['is_compliant']}, rules={status['enabled_rules']}")
    
    # Get rules
    rules = compliance.get_rules()
    print(f"✓ Rules loaded: {len(rules)}")
    
    return compliance


async def demo_master_orchestrator():
    """Demo: Master Safety Orchestrator (Integration)"""
    print("\n" + "="*60)
    print("DEMO: Master Safety Orchestrator")
    print("Integrates all safety components into unified system")
    print("="*60)
    
    from trading_bot.critical_fixes import MasterSafetyOrchestrator
    
    broker = MockBrokerAdapter()
    
    config = {
        'max_risk_per_trade': 0.02,
        'max_drawdown': 0.20,
        'emergency_shutdown_drawdown': 0.25,
        'max_open_positions': 10,
        'equity': 10000
    }
    
    orchestrator = MasterSafetyOrchestrator(
        broker_adapter=broker,
        config=config,
        db_path="demo_safety_data"
    )
    
    # Note: In production, you would call await orchestrator.start()
    # For demo, we'll just show the components
    
    print("✓ Orchestrator initialized with all components:")
    print("  - Position State Manager")
    print("  - Real-Time Risk Calculator")
    print("  - Multi-Layer Kill Switch")
    print("  - Data Validator")
    print("  - Execution Quality Monitor")
    print("  - Silent Failure Detector")
    print("  - Config Integrity Monitor")
    
    # Validate market data
    report = orchestrator.validate_market_data(
        symbol='EURUSD',
        bid=1.1000,
        ask=1.1002,
        timestamp=datetime.now()
    )
    print(f"✓ Data validation: quality={report.quality_level.value}")
    
    # Update equity
    orchestrator.update_equity(10000)
    print("✓ Equity updated")
    
    # Get status
    status = orchestrator.get_status()
    print(f"✓ Status: running={status['running']}, emergency={status['emergency_mode']}")
    
    return orchestrator


async def main():
    """Run all demos"""
    print("\n" + "#"*60)
    print("# CRITICAL FIXES DEMONSTRATION")
    print("# Based on 1,000 Critical Questions for AI Trading Systems")
    print("#"*60)
    
    try:
        # Run each demo
        await demo_position_state_manager()
        await demo_realtime_risk_calculator()
        await demo_multi_layer_kill_switch()
        await demo_data_validator()
        await demo_execution_quality_monitor()
        await demo_silent_failure_detector()
        await demo_config_integrity_monitor()
        await demo_regulatory_compliance()
        await demo_master_orchestrator()
        
        print("\n" + "="*60)
        print("ALL DEMOS COMPLETED SUCCESSFULLY")
        print("="*60)
        
        print("\n📋 SUMMARY OF CRITICAL FIXES:")
        print("  ✅ Q22: Position reconciliation with broker")
        print("  ✅ Q401: Real-time risk calculation")
        print("  ✅ Q421: Maximum drawdown enforcement")
        print("  ✅ Q891: Emergency shutdown triggers")
        print("  ✅ Q901: Multiple independent kill-switches")
        print("  ✅ Q71: Price spike detection (error vs. real)")
        print("  ✅ Q62: Stale data detection")
        print("  ✅ Q141: Execution quality measurement")
        print("  ✅ Q851: Silent failure detection")
        print("  ✅ Q781: Configuration integrity")
        print("  ✅ Q931: Regulatory compliance")
        
        print("\n⚠️  CRITICAL REMINDERS:")
        print("  1. ALWAYS call pre_trade_check() before executing trades")
        print("  2. NEVER disable the kill switch")
        print("  3. NEVER exceed ABSOLUTE_MAX_DRAWDOWN (30%)")
        print("  4. Monitor safety status continuously")
        
    except Exception as e:
        logger.error(f"Demo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
