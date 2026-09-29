#!/usr/bin/env python3
"""
AlphaAlgo Hedge Fund AI - Comprehensive Demo
=============================================
Demonstrates all hedge fund capabilities.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_fund_management():
    pass
    """Demo fund management capabilities"""
    print("\n" + "=" * 60)
    print("1. FUND MANAGEMENT DEMO")
    print("=" * 60)
    
    from trading_bot.hedge_fund import (
        FundManager, InvestorType, InvestorClass, LockupPeriod
    )
    
    # Create fund
    fund = FundManager({
        'fund_name': 'AlphaAlgo Quantitative Fund',
        'initial_nav': 1000.0
    })
    
    print(f"\nFund Created: {fund.fund_name}")
    print(f"Initial NAV: ${fund.current_nav_per_share:,.2f}")
    
    # Add investors
    print("\nAdding Investors...")
    
    investors = [
        ("Pension Fund Alpha", InvestorType.INSTITUTIONAL, InvestorClass.CLASS_B, 50_000_000),
        ("Family Office Beta", InvestorType.FAMILY_OFFICE, InvestorClass.CLASS_A, 25_000_000),
        ("Endowment Gamma", InvestorType.INSTITUTIONAL, InvestorClass.CLASS_B, 15_000_000),
        ("HNW Individual Delta", InvestorType.HIGH_NET_WORTH, InvestorClass.CLASS_C, 5_000_000),
        ("Seed Investor", InvestorType.SEED, InvestorClass.SEED, 5_000_000),
    ]
    
    for name, inv_type, share_class, amount in investors:
    pass
        investor = fund.add_investor(
            name=name,
            investor_type=inv_type,
            share_class=share_class,
            initial_investment=amount,
            lockup_period=LockupPeriod.HARD_1_YEAR
        )
        print(f"  Added: {name} - ${amount:,.0f} ({share_class.value})")
    
    # Fund summary
    summary = fund.get_fund_summary()
    print(f"\nFund Summary:")
    print(f"  Total AUM: ${summary['metrics']['total_aum']:,.2f}")
    print(f"  Total Investors: {summary['investors']['total']}")
    print(f"  By Class: {summary['investors']['by_class']}")
    
    return fund


async def demo_multi_strategy():
    pass
    """Demo multi-strategy engine"""
    print("\n" + "=" * 60)
    print("2. MULTI-STRATEGY ENGINE DEMO")
    print("=" * 60)
    
        MultiStrategyEngine, StrategyType
    )
    
    # Create engine
    engine = MultiStrategyEngine({
        'total_capital': 100_000_000,
        'max_gross_exposure': 2.0
    })
    
    # Create default strategies
    engine.create_default_strategies()
    
    print(f"\nStrategies Created: {len(engine.strategies)}")
    for sid, strategy in engine.strategies.items():
    pass
        print(f"  {strategy.name}: {strategy.allocation.target_allocation*100:.0f}% allocation")
    
    # Allocate capital
    allocations = engine.allocate_capital()
    print(f"\nCapital Allocated: ${sum(allocations.values()):,.0f}")
    
    # Generate signals
    market_data = {
        'prices': {
            'AAPL': {'price': 150, 'returns_5d': 0.02, 'returns_20d': 0.05, 'returns_60d': 0.10, 'rsi': 55, 'bb_position': 0.6},
            'GOOGL': {'price': 140, 'returns_5d': 0.01, 'returns_20d': 0.03, 'returns_60d': 0.08, 'rsi': 60, 'bb_position': 0.7},
            'MSFT': {'price': 380, 'returns_5d': -0.01, 'returns_20d': -0.02, 'returns_60d': 0.05, 'rsi': 45, 'bb_position': 0.4},
            'AMZN': {'price': 175, 'returns_5d': 0.03, 'returns_20d': 0.08, 'returns_60d': 0.15, 'rsi': 65, 'bb_position': 0.8},
            'NVDA': {'price': 480, 'returns_5d': 0.05, 'returns_20d': 0.12, 'returns_60d': 0.25, 'rsi': 72, 'bb_position': 0.9},
            'META': {'price': 350, 'returns_5d': -0.02, 'returns_20d': 0.01, 'returns_60d': 0.05, 'rsi': 48, 'bb_position': 0.5},
        },
        'sectors': {
            'AAPL': 'Technology', 'GOOGL': 'Technology', 'MSFT': 'Technology',
            'AMZN': 'Consumer', 'NVDA': 'Technology', 'META': 'Technology'
        }
    }
    
    signals = engine.generate_signals(market_data)
    print(f"\nSignals Generated:")
    for strategy_id, strategy_signals in signals.items():
    pass
        strategy = engine.strategies[strategy_id]
        print(f"  {strategy.name}: {len(strategy_signals)} signals")
    
    # Aggregate signals
    aggregated = engine.aggregate_signals(signals)
    print(f"\nAggregated Signals:")
    for symbol, data in sorted(aggregated.items(), key=lambda x: abs(x[1]['net_weight']), reverse=True)[:5]:
    pass
        print(f"  {symbol}: {data['direction']} (conviction: {data['conviction']:.2f})")
    
    return engine


async def demo_risk_management():
    pass
    """Demo institutional risk management"""
    print("\n" + "=" * 60)
    print("3. INSTITUTIONAL RISK MANAGEMENT DEMO")
    print("=" * 60)
    
        InstitutionalRiskManager, StressScenario
    )
    
    # Create risk manager
    risk_mgr = InstitutionalRiskManager({
        'max_var_95': 0.02,
        'max_drawdown': 0.15
    })
    
    # Sample positions
    positions = {
        'AAPL': {'quantity': 10000, 'current_price': 150, 'asset_class': 'equity', 'avg_volume': 50000000},
        'GOOGL': {'quantity': 5000, 'current_price': 140, 'asset_class': 'equity', 'avg_volume': 20000000},
        'MSFT': {'quantity': -3000, 'current_price': 380, 'asset_class': 'equity', 'avg_volume': 30000000},
        'AMZN': {'quantity': 8000, 'current_price': 175, 'asset_class': 'equity', 'avg_volume': 40000000},
    }
    
    portfolio_value = sum(abs(p['quantity']) * p['current_price'] for p in positions.values())
    
    # VaR calculation
    print(f"\nPortfolio Value: ${portfolio_value:,.0f}")
    
    var_95 = risk_mgr.var_engine.calculate_parametric_var(
        portfolio_value, 0.15, 0.95, 1
    )
    print(f"\n95% 1-Day VaR: ${var_95.var_amount:,.0f} ({var_95.var_percentage*100:.2f}%)")
    print(f"Expected Shortfall: ${var_95.expected_shortfall:,.0f}")
    
    var_99 = risk_mgr.var_engine.calculate_parametric_var(
        portfolio_value, 0.15, 0.99, 1
    )
    print(f"99% 1-Day VaR: ${var_99.var_amount:,.0f} ({var_99.var_percentage*100:.2f}%)")
    
    # Stress tests
    print("\nStress Test Results:")
    for scenario in [StressScenario.MARKET_CRASH_2008, StressScenario.COVID_CRASH_2020, StressScenario.VOLATILITY_SPIKE]:
    pass
        result = risk_mgr.stress_engine.run_stress_test(scenario, positions, portfolio_value)
        print(f"  {scenario.value}: {result.impact_percentage*100:.1f}% impact ({result.risk_level.value})")
    
    # Full risk assessment
    print("\nFull Risk Assessment:")
    assessment = risk_mgr.run_full_risk_assessment(positions, portfolio_value, 0.15)
    print(f"  Overall Risk Level: {assessment['overall_risk_level'].value}")
    print(f"  Active Alerts: {len(assessment['risk_alerts'])}")
    
    return risk_mgr


async def demo_performance_attribution():
    pass
    """Demo performance attribution"""
    print("\n" + "=" * 60)
    print("4. PERFORMANCE ATTRIBUTION DEMO")
    print("=" * 60)
    
    from trading_bot.hedge_fund import PerformanceAttributor
    import numpy as np
    
    # Create attributor
    attributor = PerformanceAttributor({'risk_free_rate': 0.05})
    
    # Generate sample returns
    np.random.seed(42)
    daily_returns = np.random.normal(0.0005, 0.015, 252)  # 1 year of daily returns
    benchmark_returns = np.random.normal(0.0003, 0.012, 252)
    
    # Calculate metrics
    metrics = attributor.calculate_risk_adjusted_metrics(
        daily_returns, benchmark_returns,
        date.today() - timedelta(days=252), date.today()
    )
    
    print(f"\nRisk-Adjusted Metrics:")
    print(f"  Total Return: {metrics.total_return*100:.2f}%")
    print(f"  Annualized Return: {metrics.annualized_return*100:.2f}%")
    print(f"  Volatility: {metrics.volatility*100:.2f}%")
    print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
    print(f"  Sortino Ratio: {metrics.sortino_ratio:.2f}")
    print(f"  Max Drawdown: {metrics.max_drawdown*100:.2f}%")
    print(f"  Information Ratio: {metrics.information_ratio:.2f}")
    
    # Benchmark comparison
    print("\nBenchmark Comparisons:")
    for bench_id in ['SPY', 'ABSOLUTE_8']:
    pass
        comparison = attributor.benchmark_tracker.get_benchmark_comparison(
            daily_returns, bench_id
        )
        if comparison:
    pass
            print(f"  vs {comparison.get('benchmark', bench_id)}:")
            for key, value in comparison.items():
    pass
                if key != 'benchmark':
    pass
                    print(f"    {key}: {value}")
    
    return attributor


async def demo_compliance():
    pass
    """Demo compliance and regulatory"""
    print("\n" + "=" * 60)
    print("5. COMPLIANCE & REGULATORY DEMO")
    print("=" * 60)
    
    from trading_bot.hedge_fund import ComplianceEngine
    
    # Create compliance engine
    compliance = ComplianceEngine({'fund_name': 'AlphaAlgo Fund'})
    
    # Pre-trade compliance check
    print("\nPre-Trade Compliance Check:")
    
    order = {
        'symbol': 'AAPL',
        'side': 'buy',
        'quantity': 50000,
        'price': 150,
        'sector': 'Technology'
    }
    
    portfolio = {
        'positions': {
            'AAPL': {'value': 1_000_000},
            'GOOGL': {'value': 800_000}
        },
        'total_value': 10_000_000,
        'sector_exposures': {'Technology': 0.20},
        'leverage': 1.2
    }
    
    approved, warnings, violations = compliance.trade_compliance.pre_trade_check(
        order, portfolio
    )
    
    print(f"  Order: Buy 50,000 AAPL @ $150")
    print(f"  Approved: {approved}")
    if warnings:
    pass
        print(f"  Warnings: {warnings}")
    if violations:
    pass
        print(f"  Violations: {violations}")
    
    # Compliance summary
    summary = compliance.get_compliance_summary()
    print(f"\nCompliance Summary:")
    print(f"  Overall Status: {summary['overall_status']}")
    print(f"  Restrictions: {summary['restrictions_count']}")
    print(f"  Upcoming Filings: {len(summary['upcoming_filings'])}")
    
    # Filing calendar
    print("\nUpcoming Regulatory Filings:")
    for filing in summary['upcoming_filings']:
    pass
        print(f"  {filing['form']} ({filing['period']}): Due in {filing['days_until']} days")
    
    return compliance


async def demo_prime_broker():
    pass
    """Demo prime broker interface"""
    print("\n" + "=" * 60)
    print("6. PRIME BROKER DEMO")
    print("=" * 60)
    
    from trading_bot.hedge_fund import PrimeBrokerInterface
    
    # Create prime broker interface
    pb = PrimeBrokerInterface({
        'name': 'AlphaAlgo Prime',
        'credit_limit': 200_000_000
    })
    
    # Deposit cash
    print("\nCash Management:")
    pb.cash_management.deposit(50_000_000, 'USD', 'Initial deposit')
    print(f"  Deposited: $50,000,000")
    print(f"  Balance: ${pb.cash_management.get_balance():,.0f}")
    
    # Securities lending
    print("\nSecurities Lending:")
    
    # Check availability
    status, rate, available = pb.securities_lending.check_availability('TSLA', 10000)
    print(f"  TSLA Locate: {status.value}, Rate: {rate*100:.2f}%, Available: {available:,}")
    
    # Borrow securities
    loan = pb.securities_lending.borrow_securities('TSLA', 5000)
    if loan:
    pass
        print(f"  Borrowed: 5,000 TSLA @ {loan.borrow_rate*100:.2f}%")
        print(f"  Collateral: ${loan.collateral_amount:,.0f}")
    
    # Margin calculation
    print("\nMargin Calculation:")
    positions = {
        'AAPL': {'quantity': 10000, 'price': 150, 'asset_class': 'equity'},
        'TSLA': {'quantity': -5000, 'price': 250, 'asset_class': 'equity'},
    }
    
    margin_req = pb.margin_calculator.calculate_margin_requirement(positions)
    print(f"  Total Margin Requirement: ${margin_req['total_requirement']:,.0f}")
    
    buying_power = pb.margin_calculator.calculate_buying_power(50_000_000, margin_req['total_requirement'])
    print(f"  Standard Buying Power: ${buying_power['standard_buying_power']:,.0f}")
    print(f"  Day Trading Buying Power: ${buying_power['day_trading_buying_power']:,.0f}")
    
    return pb


async def demo_full_orchestrator():
    pass
    """Demo the full hedge fund orchestrator"""
    print("\n" + "=" * 60)
    print("7. FULL HEDGE FUND ORCHESTRATOR DEMO")
    print("=" * 60)
    
    from trading_bot.hedge_fund import HedgeFundOrchestrator, create_hedge_fund
    
    # Create fund
    fund = create_hedge_fund({
        'fund_name': 'AlphaAlgo Quantitative Fund',
        'initial_capital': 100_000_000
    })
    
    print(f"\nFund Created: {fund.config.fund_name}")
    print(f"Initial Capital: ${fund.config.initial_capital:,.0f}")
    
    # Add investors
    print("\nAdding Investors...")
    
    result = fund.add_investor(
        name="Institutional Investor A",
        investor_type="INSTITUTIONAL",
        share_class="CLASS_B",
        investment_amount=30_000_000
    )
    print(f"  Added Institutional A: {result}")
    
    result = fund.add_investor(
        name="Family Office B",
        investor_type="FAMILY_OFFICE",
        share_class="CLASS_A",
        investment_amount=20_000_000
    )
    print(f"  Added Family Office B: {result}")
    
    # Generate signals
    print("\nGenerating Signals...")
    market_data = {
        'prices': {
            'AAPL': {'price': 150, 'returns_20d': 0.05, 'returns_60d': 0.10, 'rsi': 55},
            'GOOGL': {'price': 140, 'returns_20d': 0.03, 'returns_60d': 0.08, 'rsi': 60},
            'MSFT': {'price': 380, 'returns_20d': -0.02, 'returns_60d': 0.05, 'rsi': 45},
        }
    }
    signals = fund.generate_signals(market_data)
    print(f"  Total Signals: {signals['total_signals']}")
    print(f"  High Conviction: {signals['high_conviction']}")
    
    # Get metrics
    print("\nFund Metrics:")
    metrics = fund.get_fund_metrics()
    print(f"  AUM: ${metrics['fund']['total_aum']:,.0f}")
    print(f"  Investors: {metrics['fund']['num_investors']}")
    print(f"  Strategies: {metrics['strategies']['total_strategies']}")
    
    # Get status
    print("\nFund Status:")
    status = fund.get_status()
    for key, value in status.items():
    pass
        print(f"  {key}: {value}")
    
    return fund


async def main():
    pass
    """Run all demos"""
    print("\n" + "=" * 60)
    print("ALPHAALGO HEDGE FUND AI - COMPREHENSIVE DEMO")
    print("=" * 60)
    print("\nThis demo showcases all hedge fund capabilities.")
    print("=" * 60)
    
    try:
    pass
        # Run all demos
        await demo_fund_management()
        await demo_multi_strategy()
        await demo_risk_management()
        await demo_performance_attribution()
        await demo_compliance()
        await demo_prime_broker()
        await demo_full_orchestrator()
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE")
        print("=" * 60)
        print("\nThe AlphaAlgo Hedge Fund AI is ready for deployment!")
        print("\nTo start the fund:")
        print("  python run_hedge_fund.py --interactive")
        print("  or")
        print("  RUN_HEDGE_FUND.bat")
        print("=" * 60)
        
    except Exception as e:
    pass
        print(f"\nError during demo: {e}")
        import traceback
import datetime
import numpy
        traceback.print_exc()


if __name__ == "__main__":
    pass
    asyncio.run(main())
