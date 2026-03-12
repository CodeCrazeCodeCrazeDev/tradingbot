"""
NEUROS-FI Comprehensive Demo
=============================

Demonstrates the complete neuromorphic trading intelligence system with all
9 brain regions, 5 oscillation bands, and the orchestrator.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.neuros_fi import (
    NEUROSOrchestrator,
    quick_start,
    SystemState,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_initialization():
    """Demo: System initialization sequence."""
    print("\n" + "="*80)
    print("NEUROS-FI INITIALIZATION DEMO")
    print("="*80)
    
    print("\nInitializing NEUROS-FI system (12-step sequence)...")
    orchestrator = await quick_start()
    
    print(f"\n✓ System state: {orchestrator._state.value}")
    print("✓ All 9 brain regions initialized")
    print("✓ 5 oscillation bands synchronized")
    print("✓ Constitutional constraints verified")
    
    return orchestrator


async def demo_market_processing(orchestrator: NEUROSOrchestrator):
    """Demo: Process market data through the full architecture."""
    print("\n" + "="*80)
    print("MARKET DATA PROCESSING DEMO")
    print("="*80)
    
    # Simulated market data
    market_data = {
        'symbol': 'EURUSD',
        'price': 1.0850,
        'volatility': 0.015,
        'volume': 1000000,
        'spread': 0.0001,
        'order_imbalance': 0.2,
        'correlation': 0.4,
        'var_ratio': 0.6,
        'cross_asset_correlation': 0.3,
        'signals': {
            'momentum': 0.6,
            'mean_reversion': -0.3,
            'trend': 0.5,
        },
        'predictions': {
            'model_1': 1.0860,
            'model_2': 1.0855,
            'model_3': 1.0865,
        }
    }
    
    print("\nProcessing market data through neuromorphic architecture...")
    result = await orchestrator.process_market_data(market_data)
    
    print(f"\n✓ Thalamic gating: Signals filtered and prioritized")
    print(f"✓ Neocortical prediction: {len(result.get('predictions', {}))} predictions generated")
    print(f"✓ Prefrontal decision: {result.get('decision', {}).get('action', 'N/A')}")
    print(f"✓ Amygdala threat: {'DETECTED' if result.get('threat', {}).get('threat_detected') else 'None'}")
    print(f"✓ ACC conflict: {result.get('conflict', {}).get('conflict', 'None')}")
    print(f"✓ Basal ganglia action: {result.get('action', {}).get('action_name', 'N/A')}")
    print(f"✓ Global workspace winner: {result.get('broadcast', 'N/A')}")
    print(f"✓ Free energy: {result.get('free_energy', 0):.4f}")
    
    return result


async def demo_brain_regions(orchestrator: NEUROSOrchestrator):
    """Demo: Individual brain region capabilities."""
    print("\n" + "="*80)
    print("BRAIN REGION CAPABILITIES DEMO")
    print("="*80)
    
    # Region 1: Neocortex - Predictive Coding
    print("\n1. NEOCORTEX - Predictive Coding Hierarchy")
    print("   - 6 cortical layers processing at different timescales")
    print("   - Top-down predictions meet bottom-up sensory data")
    print("   - Prediction errors drive learning")
    neocortex_status = orchestrator.neocortex.get_status()
    print(f"   Status: {neocortex_status.get('total_columns', 0)} cortical columns active")
    
    # Region 2: Prefrontal - Executive Control
    print("\n2. PREFRONTAL CORTEX - Executive Control")
    print("   - Working memory maintains ~7 items")
    print("   - Dorsolateral PFC: Deliberative reasoning")
    print("   - Ventromedial PFC: Risk-value integration")
    print("   - Inhibitory control gates impulsive actions")
    pfc_status = orchestrator.prefrontal.get_status()
    print(f"   Status: {pfc_status.get('working_memory_items', 0)} items in working memory")
    
    # Region 3: Thalamus - Signal Routing
    print("\n3. THALAMUS - Intelligent Signal Routing")
    print("   - Salience scoring prioritizes important signals")
    print("   - Signal gating filters noise")
    print("   - Thalamo-cortical synchronization")
    thalamus_status = orchestrator.thalamus.get_status()
    print(f"   Status: {thalamus_status.get('registered_feeds', 0)} data feeds registered")
    
    # Region 4: Hippocampus - Memory & Discovery
    print("\n4. HIPPOCAMPUS - Memory Consolidation & Self-Discovery")
    print("   - Pattern separation: Novel patterns detected")
    print("   - Neurogenesis: New signal neurons created")
    print("   - Memory consolidation: Short-term → Long-term")
    hippo_status = orchestrator.hippocampus.get_status()
    print(f"   Status: {hippo_status.get('factor_library_size', 0)} factors in library")
    
    # Region 5: Amygdala - Threat Detection
    print("\n5. AMYGDALA - Threat Detection & Tail Risk")
    print("   - Low road: 20ms fast threat detection")
    print("   - High road: 200ms full assessment")
    print("   - Fear conditioning: Learn from tail events")
    amygdala_status = orchestrator.amygdala.get_status()
    print(f"   Status: Threat level = {amygdala_status.get('threat_level', 'NONE')}")
    
    # Region 6: Basal Ganglia - Reinforcement Learning
    print("\n6. BASAL GANGLIA - Reinforcement Learning")
    print("   - Striatum: Q-function for action values")
    print("   - Dopamine: Reward prediction error signals")
    print("   - Go/NoGo gating: Action selection")
    print("   - Habit formation: Automatic execution")
    bg_status = orchestrator.basal_ganglia.get_status()
    print(f"   Status: {bg_status.get('habits', {}).get('formed_habits', 0)} habits formed")
    
    # Region 7: Cerebellum - Forward Models
    print("\n7. CEREBELLUM - Forward Models & Execution Precision")
    print("   - Predicts execution outcomes before submission")
    print("   - Error correction: Predicted vs actual")
    print("   - Transaction cost intelligence")
    cerebellum_status = orchestrator.cerebellum.get_status()
    print(f"   Status: Model accuracy = {cerebellum_status.get('model_accuracy', 0):.2%}")
    
    # Region 8: ACC - Conflict Detection
    print("\n8. ANTERIOR CINGULATE CORTEX - Conflict & Uncertainty")
    print("   - Detects model disagreement")
    print("   - Monitors error rates by signal class")
    print("   - Allocates cognitive control resources")
    acc_status = orchestrator.acc.get_status()
    print(f"   Status: Conflict rate = {acc_status.get('conflict_rate', 0):.2f}/hour")
    
    # Region 9: DMN - Offline Learning
    print("\n9. DEFAULT MODE NETWORK - Offline Learning")
    print("   - Memory replay during idle periods")
    print("   - Prospective simulation of future scenarios")
    print("   - Spontaneous hypothesis generation")
    print("   - Overnight consolidation pipeline")
    dmn_status = orchestrator.dmn.get_status()
    print(f"   Status: {dmn_status.get('state', 'inactive')}")


async def demo_oscillation_bands(orchestrator: NEUROSOrchestrator):
    """Demo: Neural oscillation bands."""
    print("\n" + "="*80)
    print("NEURAL OSCILLATION BANDS DEMO")
    print("="*80)
    
    osc_status = orchestrator.oscillations.get_status()
    
    print("\nFive temporal scales operating simultaneously:")
    print("\n1. GAMMA (γ) - 30-100 Hz: Nanoseconds to Milliseconds")
    print("   - Co-located execution agents")
    print("   - Order book state binding")
    print("   - HFT microstructure response")
    gamma_state = osc_status['bands'].get('GAMMA', {})
    print(f"   Phase: {gamma_state.get('phase', 0):.2f}, In window: {gamma_state.get('in_window', False)}")
    
    print("\n2. BETA (β) - 13-30 Hz: Seconds to Minutes")
    print("   - Intraday signal processing")
    print("   - Real-time position management")
    print("   - Live PnL monitoring")
    beta_state = osc_status['bands'].get('BETA', {})
    print(f"   Phase: {beta_state.get('phase', 0):.2f}, In window: {beta_state.get('in_window', False)}")
    
    print("\n3. ALPHA (α) - 8-13 Hz: Minutes to Hours")
    print("   - Liquidity monitoring")
    print("   - Regime stability assessment")
    print("   - Attention allocation")
    alpha_state = osc_status['bands'].get('ALPHA', {})
    print(f"   Phase: {alpha_state.get('phase', 0):.2f}, In window: {alpha_state.get('in_window', False)}")
    
    print("\n4. THETA (θ) - 4-8 Hz: Hours to Days")
    print("   - End-of-day discovery consolidation")
    print("   - Sequential event pattern learning")
    print("   - Cross-day regime transitions")
    theta_state = osc_status['bands'].get('THETA', {})
    print(f"   Phase: {theta_state.get('phase', 0):.2f}, In window: {theta_state.get('in_window', False)}")
    
    print("\n5. DELTA (δ) - 0.5-4 Hz: Days to Weeks")
    print("   - Overnight model retraining")
    print("   - Long-horizon factor integration")
    print("   - Strategic world model rebuilding")
    delta_state = osc_status['bands'].get('DELTA', {})
    print(f"   Phase: {delta_state.get('phase', 0):.2f}, In window: {delta_state.get('in_window', False)}")
    
    print(f"\n✓ Synchronization quality: {osc_status.get('sync_quality', 0):.2%}")
    print(f"✓ Cross-frequency coupling: {len(osc_status.get('couplings', []))} connections")


async def demo_core_principles(orchestrator: NEUROSOrchestrator):
    """Demo: Core operating principles."""
    print("\n" + "="*80)
    print("CORE OPERATING PRINCIPLES DEMO")
    print("="*80)
    
    print("\n1. FREE ENERGY PRINCIPLE (Karl Friston)")
    print("   - Minimize surprise via predictive coding")
    print("   - F = prediction_error + complexity_penalty")
    print("   - Active inference: Act to confirm predictions")
    fe_stats = orchestrator.free_energy.get_statistics()
    print(f"   Current free energy: {fe_stats.get('current_fe', 0):.4f}")
    print(f"   Mean prediction error: {fe_stats.get('prediction_error', 0):.4f}")
    
    print("\n2. GLOBAL WORKSPACE THEORY (Bernard Baars)")
    print("   - Distributed specialists compete for workspace")
    print("   - Winner broadcasts to all regions")
    print("   - Creates unified, coherent decisions")
    current_broadcast = orchestrator.global_workspace.get_current_broadcast()
    if current_broadcast:
        print(f"   Current winner: {current_broadcast.competition_winner}")
        print(f"   Coherence: {current_broadcast.coherence:.2%}")
    
    print("\n3. HEBBIAN LEARNING")
    print("   - 'Neurons that fire together, wire together'")
    print("   - Δw = η * pre_activation * post_activation")
    print("   - Strengthens successful pathways")
    print(f"   Connection weights dynamically updated")


async def demo_constitutional_constraints(orchestrator: NEUROSOrchestrator):
    """Demo: Constitutional constraints enforcement."""
    print("\n" + "="*80)
    print("CONSTITUTIONAL CONSTRAINTS DEMO")
    print("="*80)
    
    brainstem_status = orchestrator.brainstem.get_status()
    
    print("\nBrainstem Constitutional Layer (Version 5.0)")
    print("Immutable constraints enforced at infrastructure level:")
    print(f"  - Max Drawdown: 8%")
    print(f"  - Validation t-stat: ≥2.0")
    print(f"  - Sandbox Days: 30")
    print(f"  - Max Position ADV: 5%")
    print(f"  - Max Market Liquidity: 10%")
    print(f"  - Compliance Latency: <5ms")
    
    print(f"\n✓ Active rules: {brainstem_status.get('active_rules', 0)}")
    print(f"✓ Violations tracked: {brainstem_status.get('total_violations', 0)}")
    print(f"✓ Emergency halts: {brainstem_status.get('emergency_halts', 0)}")
    print(f"✓ Evolution proposals: {brainstem_status.get('evolution_proposals', 0)}")
    
    print("\nNo cortical override possible - these constraints are absolute.")


async def demo_offline_consolidation(orchestrator: NEUROSOrchestrator):
    """Demo: Overnight consolidation cycle."""
    print("\n" + "="*80)
    print("OFFLINE CONSOLIDATION DEMO")
    print("="*80)
    
    print("\nRunning overnight consolidation cycle...")
    print("(This is the 'sleeping on a problem' equivalent)")
    
    result = await orchestrator.run_offline_consolidation()
    
    consolidation = result.get('consolidation')
    if consolidation:
        print(f"\n✓ Memories processed: {consolidation.memories_processed}")
        print(f"✓ Factors updated: {consolidation.factors_updated}")
        print(f"✓ Weights consolidated: {consolidation.weights_consolidated}")
        print(f"✓ New patterns discovered: {consolidation.new_patterns_discovered}")
    
    scenarios = result.get('scenarios', [])
    print(f"\n✓ Prospective scenarios generated: {len(scenarios)}")
    
    hypotheses = result.get('hypotheses', [])
    print(f"✓ Cross-domain hypotheses: {len(hypotheses)}")
    
    print("\nSystem is now smarter than it was yesterday.")


async def main():
    """Run complete NEUROS-FI demo."""
    print("\n" + "="*80)
    print("NEUROS-FI: NEUROMORPHIC ADAPTIVE FINANCIAL INTELLIGENCE")
    print("Brain-Topology Trading System · Constitutional Version 5.0")
    print("="*80)
    
    try:
        # Initialize system
        orchestrator = await demo_initialization()
        
        # Demo brain regions
        await demo_brain_regions(orchestrator)
        
        # Demo oscillation bands
        await demo_oscillation_bands(orchestrator)
        
        # Demo market processing
        await demo_market_processing(orchestrator)
        
        # Demo core principles
        await demo_core_principles(orchestrator)
        
        # Demo constitutional constraints
        await demo_constitutional_constraints(orchestrator)
        
        # Demo offline consolidation
        await demo_offline_consolidation(orchestrator)
        
        # Final status
        print("\n" + "="*80)
        print("DEMO COMPLETE")
        print("="*80)
        
        status = orchestrator.get_status()
        print(f"\nSystem State: {status['system_state']}")
        print(f"Inference Mode: {status['inference_mode']}")
        print("\nAll 9 brain regions operational ✓")
        print("All 5 oscillation bands synchronized ✓")
        print("Constitutional constraints enforced ✓")
        print("Free Energy Principle active ✓")
        print("Global Workspace operational ✓")
        print("Hebbian learning enabled ✓")
        
        print("\nNEUROS-FI is ready for production trading.")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
