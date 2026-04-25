"""
Unified Meta-Intelligence Demo
================================

Complete demonstration of the unified meta-intelligence layer with:
- ANY frontier model support (OpenAI, Anthropic, Google, etc.)
- Local SQLite storage
- Economic objectives: PNL, Sharpe, risk-adjusted returns, latency, throughput
- Millisecond-scale real-time processing
- ANY task categories (fully generic)
"""

import asyncio
import os
import logging
from datetime import datetime

from trading_bot.neuros_evolution import (
    # Main interface
    create_meta_intelligence,
    UnifiedMetaIntelligence,
    
    # Frontier models (ANY provider)
    ModelProvider,
    ModelConfig,
    
    # Economic objectives
    EconomicObjectiveLibrary,
    get_objective,
    TradingMetrics,
    
    # Generic categories
    TaskCategory,
    register_category,
    detect_category,
)

logging.basicConfig(level=logging.INFO)


# ==========================================
# 1. ECONOMIC OBJECTIVE (Your Trading Goals)
# ==========================================

def my_custom_economic_objective(metrics: dict) -> float:
    """
    Define what "better" means for YOUR trading system.
    
    The meta-intelligence layer will:
    - Route to capabilities that maximize this score
    - Distill behaviors that improve this score
    - Deploy only if this score improves
    - Keep only what maintains/improves this score
    """
    # PNL (40% weight) - normalized to 0-1
    pnl_score = min(1.0, max(0, metrics.get('pnl_pct', 0)) / 100)
    
    # Sharpe ratio (25% weight) - >2 is excellent
    sharpe = metrics.get('sharpe_ratio', 0)
    sharpe_score = min(1.0, sharpe / 2.5)
    
    # Risk-adjusted: Inverse of drawdown (15% weight)
    drawdown = metrics.get('max_drawdown_pct', 0)
    drawdown_score = max(0, 1 - drawdown / 0.20)
    
    # Latency (10% weight) - exponential decay from 0ms
    latency_ms = metrics.get('latency_ms', 100)
    latency_score = max(0, 1 - latency_ms / 10)  # 10ms = 0 score
    
    # Throughput (10% weight) - tasks per second
    throughput = metrics.get('throughput', 0)
    throughput_score = min(1.0, throughput / 1000)
    
    # Combined weighted score
    total = (
        0.40 * pnl_score +
        0.25 * sharpe_score +
        0.15 * drawdown_score +
        0.10 * latency_score +
        0.10 * throughput_score
    )
    
    return total


# ==========================================
# 2. CAPABILITY IMPLEMENTATIONS
# ==========================================

async def ultra_fast_signal_generator(input_data: dict) -> dict:
    """
    Ultra-fast signal generation capability.
    Target: < 2ms execution time.
    """
    symbol = input_data.get('symbol', 'UNKNOWN')
    price = input_data.get('price', 0)
    
    # Simulated ultra-fast logic (sub-millisecond in reality)
    momentum = input_data.get('momentum', 0.5)
    
    signal = 'BUY' if momentum > 0.6 else 'SELL' if momentum < 0.4 else 'HOLD'
    confidence = 0.7 + abs(momentum - 0.5)
    
    return {
        'symbol': symbol,
        'signal': signal,
        'confidence': round(confidence, 3),
        'timestamp': datetime.utcnow().isoformat(),
        'latency_achieved_ms': 0.5  # Sub-millisecond
    }


async def risk_calculator(input_data: dict) -> dict:
    """
    Risk calculation capability.
    """
    position = input_data.get('position_size', 0)
    price = input_data.get('price', 0)
    volatility = input_data.get('volatility', 0.1)
    
    notional = position * price
    var_95 = notional * volatility * 1.645  # 95% VaR
    
    return {
        'var_95': var_95,
        'risk_score': min(1.0, var_95 / 10000),
        'max_position': position * (1 - volatility),
        'recommended_action': 'REDUCE' if volatility > 0.3 else 'HOLD'
    }


async def portfolio_optimizer(input_data: dict) -> dict:
    """
    Portfolio optimization capability.
    """
    assets = input_data.get('assets', [])
    target_return = input_data.get('target_return', 0.1)
    
    # Simplified optimization
    allocations = {asset: 1.0 / len(assets) for asset in assets} if assets else {}
    
    return {
        'allocations': allocations,
        'expected_return': target_return,
        'expected_volatility': 0.15,
        'sharpe': target_return / 0.15 if target_return > 0 else 0
    }


def any_custom_task(input_data: dict) -> dict:
    """
    Generic task handler - ANY task type is supported.
    """
    return {
        'processed': True,
        'input_received': list(input_data.keys()),
        'output': f"Processed {len(input_data)} fields",
        'generic': True
    }


# ==========================================
# 3. MAIN DEMONSTRATIONS
# ==========================================

async def demo_any_frontier_models():
    """
    Demonstrate connecting to ANY frontier model.
    
    Supports: OpenAI, Anthropic, Google, Cohere, Mistral, Groq, Together, Local, Custom
    """
    print("\n" + "="*60)
    print("DEMO: ANY FRONTIER MODELS")
    print("="*60)
    
    # Create meta-intelligence layer with SQLite storage
    meta = create_meta_intelligence(
        data_dir="./demo_any_frontier",
        objective_preset="comprehensive",  # Or 'hft', 'alpha', 'risk_parity', etc.
        custom_objective=my_custom_economic_objective
    )
    
    # Add ANY frontier models (uncomment the ones you have API keys for)
    
    # OpenAI
    # meta.add_frontier_model(
    #     provider="openai",
    #     model_id="gpt-4o",
    #     api_key=os.getenv("OPENAI_API_KEY"),
    #     default_for_categories=["analysis", "generation", "classification"]
    # )
    
    # Anthropic
    # meta.add_frontier_model(
    #     provider="anthropic",
    #     model_id="claude-3-opus-20240229",
    #     api_key=os.getenv("ANTHROPIC_API_KEY"),
    #     default_for_categories=["analysis", "reasoning", "coding"]
    # )
    
    # Google
    # meta.add_frontier_model(
    #     provider="google",
    #     model_id="gemini-1.5-pro",
    #     api_key=os.getenv("GOOGLE_API_KEY"),
    #     default_for_categories=["multimodal", "summarization"]
    # )
    
    # Local model (e.g., via llama.cpp or similar)
    # meta.add_frontier_model(
    #     provider="local",
    #     model_id="llama-3-70b",
    #     base_url="http://localhost:8000/v1",
    #     default_for_categories=["general"]
    # )
    
    # Custom API endpoint
    # meta.add_frontier_model(
    #     provider="custom",
    #     model_id="my-custom-model",
    #     base_url="https://api.mycompany.com/v1",
    #     api_key=os.getenv("CUSTOM_API_KEY"),
    #     default_for_categories=["specialized"]
    # )
    
    print("\nSupported frontier model providers:")
    print("  - OpenAI (GPT-4, GPT-3.5, etc.)")
    print("  - Anthropic (Claude 3, etc.)")
    print("  - Google (Gemini, etc.)")
    print("  - Cohere")
    print("  - Mistral")
    print("  - Groq")
    print("  - Together AI")
    print("  - Local models (llama.cpp, etc.)")
    print("  - Custom API endpoints")
    
    print("\nModel connector stats:", meta.connector.get_connector_stats())
    
    return meta


async def demo_millisecond_routing(meta: UnifiedMetaIntelligence):
    """
    Demonstrate millisecond-scale task routing.
    """
    print("\n" + "="*60)
    print("DEMO: MILLISECOND ROUTING")
    print("="*60)
    
    # Register capabilities with different performance profiles
    meta.register_capability(
        capability_id="ultra_fast_signal",
        implementation=ultra_fast_signal_generator,
        category="signal_generation",
        performance_score=0.95,
        latency_ms=0.5
    )
    
    meta.register_capability(
        capability_id="standard_risk",
        implementation=risk_calculator,
        category="risk_management",
        performance_score=0.85,
        latency_ms=2.0
    )
    
    meta.register_capability(
        capability_id="portfolio_opt",
        implementation=portfolio_optimizer,
        category="optimization",
        performance_score=0.80,
        latency_ms=5.0
    )
    
    # Process tasks with millisecond deadlines
    tasks = [
        {
            'task_type': 'generate_signal',
            'input_data': {'symbol': 'BTC/USD', 'price': 45000, 'momentum': 0.75},
            'max_latency_ms': 5  # 5ms deadline
        },
        {
            'task_type': 'calculate_risk',
            'input_data': {'position_size': 10, 'price': 45000, 'volatility': 0.25},
            'max_latency_ms': 10  # 10ms deadline
        },
        {
            'task_type': 'optimize_portfolio',
            'input_data': {'assets': ['BTC', 'ETH', 'SOL'], 'target_return': 0.15},
            'max_latency_ms': 20  # 20ms deadline
        }
    ]
    
    print("\nProcessing tasks with millisecond deadlines:")
    for i, task in enumerate(tasks, 1):
        result = await meta.process(
            task_type=task['task_type'],
            input_data=task['input_data'],
            max_latency_ms=task['max_latency_ms']
        )
        
        print(f"\nTask {i}: {task['task_type']}")
        print(f"  Success: {result.success}")
        print(f"  Total Latency: {result.total_latency_ms:.2f}ms")
        print(f"  Routing Time: {result.routing_time_ms:.2f}ms")
        print(f"  Capability Used: {result.capability_used}")
        print(f"  Economic Score: {result.economic_score:.3f}")
    
    # Show router stats
    stats = meta.router.get_stats()
    print("\n" + "-"*40)
    print("Router Performance:")
    print(f"  Total Routes: {stats['total_routes']}")
    print(f"  Cache Hit Rate: {stats['cache_hit_rate']:.1%}")
    print(f"  Avg Decision Time: {stats['avg_decision_time_ms']:.3f}ms")
    print(f"  Target: < 1ms routing")


async def demo_economic_objectives():
    """
    Demonstrate economic objective optimization.
    """
    print("\n" + "="*60)
    print("DEMO: ECONOMIC OBJECTIVES")
    print("="*60)
    
    # Create meta-intelligence with different objective presets
    presets = ['comprehensive', 'hft', 'alpha', 'risk_parity', 'throughput', 'latency']
    
    print("\nAvailable objective presets:")
    for preset in presets:
        obj_fn = get_objective(preset)
        
        # Test with sample metrics
        test_metrics = {
            'pnl_pct': 15,
            'sharpe_ratio': 1.8,
            'max_drawdown_pct': 0.08,
            'latency_ms': 3,
            'throughput': 500,
            'win_rate': 0.65
        }
        
        score = obj_fn(test_metrics)
        print(f"  {preset:20s}: score={score:.3f}")
    
    # Show custom objective
    print("\nCustom objective (your trading goals):")
    custom_score = my_custom_economic_objective(test_metrics)
    print(f"  Score: {custom_score:.3f}")
    print(f"  Weights: PNL=40%, Sharpe=25%, Drawdown=15%, Latency=10%, Throughput=10%")
    
    # Create meta-intelligence with custom objective
    meta = create_meta_intelligence(
        data_dir="./demo_economic",
        custom_objective=my_custom_economic_objective
    )
    
    print("\nMeta-intelligence initialized with custom objective")
    print("It will now optimize for YOUR specific trading goals")


async def demo_any_task_categories(meta: UnifiedMetaIntelligence):
    """
    Demonstrate ANY task category support.
    """
    print("\n" + "="*60)
    print("DEMO: ANY TASK CATEGORIES")
    print("="*60)
    
    # Define ANY custom categories - no limits
    categories = [
        TaskCategory(
            name="sentiment_analysis",
            description="Analyze sentiment from text",
            input_schema={"text": "str", "source": "str"},
            output_schema={"sentiment": "str", "score": "float"},
            required_tags=["nlp"],
            typical_latency_ms=5
        ),
        TaskCategory(
            name="order_execution",
            description="Execute trading orders optimally",
            input_schema={"order_type": "str", "size": "float", "price": "float"},
            output_schema={"execution_price": "float", "slippage_bps": "float"},
            required_tags=["execution"],
            typical_latency_ms=1  # Ultra-low latency
        ),
        TaskCategory(
            name="anomaly_detection",
            description="Detect anomalies in market data",
            input_schema={"data_series": "list", "threshold": "float"},
            output_schema={"anomalies": "list", "severity": "float"},
            required_tags=["detection"],
            typical_latency_ms=10
        ),
        TaskCategory(
            name="compliance_check",
            description="Check regulatory compliance",
            input_schema={"trade_data": "dict", "regulations": "list"},
            output_schema={"compliant": "bool", "violations": "list"},
            required_tags=["compliance"],
            typical_latency_ms=50
        ),
        # ANY other category you need...
        TaskCategory(
            name="my_custom_strategy",
            description="Your proprietary strategy",
            input_schema={"my_param1": "float", "my_param2": "str"},
            output_schema={"result": "any"},
            typical_latency_ms=3
        )
    ]
    
    # Register categories
    for cat in categories:
        meta.define_category(
            name=cat.name,
            input_schema=cat.input_schema,
            output_schema=cat.output_schema,
            description=cat.description
        )
    
    print("\nRegistered custom categories:")
    for cat in categories:
        print(f"  - {cat.name}: {cat.description}")
    
    # Auto-detect category from task
    print("\nAuto-detection examples:")
    
    test_tasks = [
        ("analyze_sentiment", {"text": "Market is bullish", "source": "twitter"}),
        ("execute_market_order", {"order_type": "market", "size": 1.5, "price": 45000}),
        ("detect_anomaly", {"data_series": [1, 2, 3, 100], "threshold": 0.95}),
        ("my_weird_task", {"my_param1": 0.5, "my_param2": "test"}),
    ]
    
    for task_type, input_data in test_tasks:
        detected = detect_category(task_type, input_data)
        print(f"  {task_type:25s} -> {detected[0][0] if detected else 'general'} (conf: {detected[0][1] if detected else 0:.2f})")
    
    # Register a generic handler
    meta.register_capability(
        capability_id="generic_handler",
        implementation=any_custom_task,
        category="general",
        performance_score=0.6,
        latency_ms=1.0
    )
    
    print("\nANY task category can be processed - the system is fully generic")


async def demo_sqlite_storage(meta: UnifiedMetaIntelligence):
    """
    Demonstrate local SQLite storage.
    """
    print("\n" + "="*60)
    print("DEMO: LOCAL SQLITE STORAGE")
    print("="*60)
    
    # Storage is automatic - show what gets stored
    print("\nSQLite database stores:")
    print("  - Capability records (performance, latency, reliability)")
    print("  - Routing decisions (for learning)")
    print("  - Performance metrics (time-series)")
    print("  - Usage statistics")
    
    # Get stats
    stats = meta.get_stats()
    
    print("\nRegistry stats:")
    print(f"  Indexed categories: {stats['router']['indexed_categories']}")
    print(f"  Cached capabilities: {stats['router']['cached_capabilities']}")
    
    print("\nCategory stats:")
    print(f"  Total categories: {stats['categories']['total']}")
    print(f"  Popular: {stats['categories']['popular']}")
    
    print("\nObjective stats:")
    obj_stats = stats['objective']
    print(f"  Samples: {obj_stats.get('samples', 0)}")
    print(f"  Best score: {obj_stats.get('best_score', 0):.3f}")
    print(f"  Trend: {obj_stats.get('trend', 'unknown')}")
    
    print("\nAll data persisted locally in SQLite - no external dependencies")


async def demo_complete_workflow():
    """
    Demonstrate complete workflow.
    """
    print("\n" + "="*60)
    print("DEMO: COMPLETE WORKFLOW")
    print("="*60)
    
    # 1. Create meta-intelligence layer
    meta = create_meta_intelligence(
        data_dir="./demo_complete",
        objective_preset="hft"  # High-frequency trading optimized
    )
    
    print("\n1. Meta-intelligence layer created")
    print(f"   Data directory: {meta.data_dir}")
    print(f"   Objective: HFT (latency-minimized)")
    
    # 2. Add frontier models (simulated)
    print("\n2. Frontier models configured:")
    print("   - GPT-4 for complex analysis")
    print("   - Claude for reasoning tasks")
    print("   - Gemini for multimodal tasks")
    print("   - Local LLM for low-latency tasks")
    
    # 3. Register distilled capabilities
    print("\n3. Registering distilled capabilities...")
    meta.register_capability(
        capability_id="signal_gen_v1",
        implementation=ultra_fast_signal_generator,
        category="signal_generation",
        performance_score=0.92,
        latency_ms=0.5
    )
    meta.register_capability(
        capability_id="risk_calc_v1",
        implementation=risk_calculator,
        category="risk_management",
        performance_score=0.88,
        latency_ms=2.0
    )
    
    # 4. Process tasks
    print("\n4. Processing tasks with intelligent routing...")
    
    high_priority_tasks = [
        {
            'task_type': 'generate_signal',
            'input_data': {'symbol': 'BTC/USD', 'price': 50000, 'momentum': 0.8},
            'max_latency_ms': 2  # Ultra-tight deadline
        },
        {
            'task_type': 'calculate_risk',
            'input_data': {'position_size': 5, 'price': 50000, 'volatility': 0.2},
            'max_latency_ms': 5
        }
    ]
    
    for task in high_priority_tasks:
        result = await meta.process(
            task_type=task['task_type'],
            input_data=task['input_data'],
            max_latency_ms=task['max_latency_ms']
        )
        
        print(f"\n   Task: {task['task_type']}")
        print(f"   -> Routed to: {result.capability_used or result.frontier_model_used}")
        print(f"   -> Latency: {result.total_latency_ms:.2f}ms (target: {task['max_latency_ms']}ms)")
        print(f"   -> Economic score: {result.economic_score:.3f}")
    
    # 5. Show recommendations
    print("\n5. System recommendations:")
    recs = meta.get_recommendations()
    for rec in recs:
        print(f"   - {rec}")
    
    print("\n" + "="*60)
    print("DEMO COMPLETE")
    print("="*60)
    print("\nThe meta-intelligence layer provides:")
    print("  ✓ ANY frontier model support")
    print("  ✓ Local SQLite storage")
    print("  ✓ Economic objective optimization (PNL, Sharpe, latency, throughput)")
    print("  ✓ Millisecond-scale routing")
    print("  ✓ ANY task category support")
    print("  ✓ Continuous self-improvement")


async def main():
    """Run all demonstrations"""
    print("\n" + "="*70)
    print("  UNIFIED META-INTELLIGENCE LAYER - COMPLETE DEMONSTRATION")
    print("="*70)
    print("\n  Features:")
    print("    • Connect to ANY frontier model (OpenAI, Anthropic, Google, etc.)")
    print("    • Local SQLite storage - no external dependencies")
    print("    • Optimize for PNL, Sharpe, risk-adjusted returns, latency, throughput")
    print("    • Millisecond-scale real-time routing and execution")
    print("    • ANY task category - fully generic and extensible")
    print("="*70)
    
    # Run demos
    meta = await demo_any_frontier_models()
    await demo_millisecond_routing(meta)
    await demo_economic_objectives()
    await demo_any_task_categories(meta)
    await demo_sqlite_storage(meta)
    await demo_complete_workflow()


if __name__ == "__main__":
    asyncio.run(main())
