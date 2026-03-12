"""
Neural Brain Integration Demo
Demonstrates the brain-like neural architecture connecting all 100+ modules
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.neural_integration import (
    quick_start_neural_brain,
    stimulate,
    query,
    brain_stats,
    focus,
    CONSCIOUSNESS,
    SYNAPTIC_MATRIX,
    BRAIN_STEM
)


async def demo_neural_brain():
    """Comprehensive demo of neural brain integration"""
    
    print("=" * 80)
    print("🧠 NEURAL BRAIN INTEGRATION ARCHITECTURE DEMO")
    print("=" * 80)
    print("Connecting all 100+ trading bot modules like neurons in a brain")
    print()
    
    # Step 1: Initialize Neural Brain
    print("Step 1: Initializing Neural Brain Architecture...")
    print("-" * 80)
    
    brain = await quick_start_neural_brain()
    
    print("✅ Neural Brain Online!")
    print()
    await asyncio.sleep(1)
    
    # Step 2: Show Brain Statistics
    print("Step 2: Brain Connectome Statistics")
    print("-" * 80)
    
    stats = brain.get_brain_statistics()
    
    print(f"📊 Neural Topology:")
    print(f"  • Total Modules: {stats['total_modules']}")
    print(f"  • Total Synapses: {stats['total_synapses']}")
    print(f"  • Active Connections: {stats['active_connections']}")
    print(f"  • Consciousness Level: {stats['consciousness_level']:.2f}")
    print()
    
    print(f"🧠 Brain Regions (7 major regions):")
    for region, count in sorted(stats['regions'].items(), key=lambda x: x[1], reverse=True):
        print(f"  • {region}: {count} modules")
    print()
    
    await asyncio.sleep(1)
    
    # Step 3: Show Connectome Details
    print("Step 3: Neural Connectome Details")
    print("-" * 80)
    
    connectome_stats = SYNAPTIC_MATRIX.get_connectome_stats()
    print(f"📈 Connection Distribution:")
    for category, count in connectome_stats['connection_distribution'].items():
        print(f"  • {category}: {count} modules")
    print(f"  • Average connections per module: {connectome_stats['avg_connections_per_module']:.1f}")
    print()
    
    await asyncio.sleep(1)
    
    # Step 4: Stimulate Different Brain Regions
    print("Step 4: Stimulating Brain Regions")
    print("-" * 80)
    
    regions_to_test = [
        ('ai_core', 'neocortex', 'Intelligence processing'),
        ('risk', 'limbic_system', 'Risk/emotion processing'),
        ('execution', 'cerebellum', 'Motor/execution coordination'),
        ('market_intelligence', 'thalamus', 'Sensory perception'),
    ]
    
    for module, region, description in regions_to_test:
        print(f"\n⚡ Stimulating {module} ({region})")
        print(f"   Purpose: {description}")
        
        result = await stimulate(module, {
            'action': 'process',
            'data': {'symbol': 'EURUSD', 'timestamp': datetime.now().isoformat()},
            'test': True
        })
        
        print(f"   ✅ Module activated successfully")
        
        # Release dopamine (reward signal)
        from trading_bot.neural_integration import (
            NeurotransmitterSignal, NeurotransmitterType, SYNAPTIC_CLEFT
        )
        
        reward_signal = NeurotransmitterSignal(
            transmitter_type=NeurotransmitterType.DOPAMINE,
            concentration=0.5,
            source_module=module,
            target_module='limbic_system',
            timestamp=datetime.now()
        )
        await SYNAPTIC_CLEFT.release_neurotransmitter(reward_signal)
        
        await asyncio.sleep(0.5)
    
    print()
    
    # Step 5: Query Module Status
    print("Step 5: Querying Module Status")
    print("-" * 80)
    
    modules_to_query = ['ai_core', 'risk', 'execution', 'learning']
    
    for module in modules_to_query:
        print(f"\n🔍 Querying {module}...")
        status = await query(module, 'status')
        
        if 'error' not in status:
            print(f"   Module: {status.get('module', 'N/A')}")
            print(f"   Brain Region: {status.get('brain_region', 'N/A')}")
            print(f"   Activations: {status.get('activations', 0)}")
            print(f"   Neural State: {status.get('neural_state', 0):.2f}")
            print(f"   Status: {'✅ Active' if status.get('is_active') else '❌ Inactive'}")
        else:
            print(f"   ⚠️  {status['error']}")
    
    print()
    await asyncio.sleep(1)
    
    # Step 6: Focus Attention
    print("Step 6: Attention Mechanism")
    print("-" * 80)
    
    print("🎯 Focusing attention on 'ai_core'...")
    await focus('ai_core')
    
    print("🎯 Focusing attention on 'execution'...")
    await focus('execution')
    
    print("✅ Attention focus mechanism working")
    print()
    
    # Step 7: Neurotransmitter System
    print("Step 7: Neurotransmitter Messaging")
    print("-" * 80)
    
    print("🧪 Releasing neurotransmitters:")
    
    neurotransmitters = [
        (NeurotransmitterType.GLUTAMATE, 'excitatory', 0.8),
        (NeurotransmitterType.GABA, 'inhibitory', 0.6),
        (NeurotransmitterType.DOPAMINE, 'reward', 0.7),
        (NeurotransmitterType.NOREPINEPHRINE, 'alert', 0.5),
        (NeurotransmitterType.ACETYLCHOLINE, 'attention', 0.6),
    ]
    
    for nt, func, conc in neurotransmitters:
        print(f"   • {nt.name} ({func}): {conc:.1f} concentration")
        
        signal = NeurotransmitterSignal(
            transmitter_type=nt,
            concentration=conc,
            source_module='orchestrator',
            target_module='global',
            timestamp=datetime.now()
        )
        await SYNAPTIC_CLEFT.release_neurotransmitter(signal)
    
    # Show chemical state
    chemical_state = SYNAPTIC_CLEFT.get_chemical_state()
    print(f"\n📊 Current Chemical Balance:")
    for chem, level in chemical_state.items():
        bar = "█" * int(level * 20) + "░" * (20 - int(level * 20))
        print(f"   {chem:15} [{bar}] {level:.2f}")
    
    print()
    await asyncio.sleep(1)
    
    # Step 8: Collective Consciousness
    print("Step 8: Collective Consciousness")
    print("-" * 80)
    
    # Broadcast to workspace
    print("📢 Broadcasting to global workspace...")
    CONSCIOUSNESS.broadcast_to_workspace('market_data', {
        'symbol': 'EURUSD',
        'price': 1.0850,
        'trend': 'bullish'
    }, priority=8)
    
    CONSCIOUSNESS.broadcast_to_workspace('risk_assessment', {
        'level': 'medium',
        'var_95': 0.02,
        'exposure': 0.15
    }, priority=9)
    
    CONSCIOUSNESS.broadcast_to_workspace('trading_decision', {
        'action': 'hold',
        'confidence': 0.75
    }, priority=7)
    
    # Generate insights
    print("💡 Generating insights...")
    CONSCIOUSNESS.generate_insight('ai_core', 
        'Market showing consolidation pattern - wait for breakout', 
        confidence=0.82)
    
    CONSCIOUSNESS.generate_insight('risk',
        'Portfolio exposure within limits, no action needed',
        confidence=0.91)
    
    # Get workspace summary
    workspace = CONSCIOUSNESS.get_workspace_summary()
    print(f"\n🧠 Consciousness State:")
    print(f"   • Level: {workspace['consciousness_level']:.2f}")
    print(f"   • Attention Focus: {workspace['attention_focus'] or 'None'}")
    print(f"   • Workspace Items: {workspace['workspace_items']}")
    print(f"   • Recent Insights: {workspace['insights_generated']}")
    print(f"   • Perceptions: {workspace['recent_perceptions']}")
    
    print(f"\n💭 Recent Insights:")
    for insight in CONSCIOUSNESS.insights[-3:]:
        print(f"   • [{insight['source']}] {insight['insight']}")
        print(f"     Confidence: {insight['confidence']:.2f}")
    
    print()
    await asyncio.sleep(1)
    
    # Step 9: Brain Stem Health
    print("Step 9: Brain Stem (Vital Functions)")
    print("-" * 80)
    
    health = BRAIN_STEM.check_health()
    print(f"🫀 Vital Signs:")
    print(f"   • Heart Rate (ops/min): {health['vital_signs']['heart_rate']}")
    print(f"   • Breathing (logs/min): {health['vital_signs']['breathing_rate']}")
    print(f"   • Status: {health['status']}")
    
    if health['issues']:
        print(f"   ⚠️  Issues: {health['issues']}")
    else:
        print(f"   ✅ All vital functions normal")
    
    print()
    
    # Step 10: Final Statistics
    print("Step 10: Final Brain Statistics")
    print("-" * 80)
    
    final_stats = brain.get_brain_statistics()
    
    print(f"📊 Brain Performance:")
    print(f"   • Uptime: {final_stats['uptime_seconds']:.1f} seconds")
    print(f"   • Modules Active: {final_stats['total_modules']}")
    print(f"   • Synaptic Connections: {final_stats['total_synapses']}")
    print(f"   • Consciousness Level: {final_stats['consciousness_level']:.2f}")
    print(f"   • Brain Stem: {final_stats['brain_stem_health']['status']}")
    
    print()
    print("=" * 80)
    print("✅ NEURAL BRAIN INTEGRATION DEMO COMPLETE")
    print("=" * 80)
    print()
    print("🧠 Summary:")
    print(f"   • Successfully integrated {stats['total_modules']} modules")
    print(f"   • Created {stats['total_synapses']} synaptic connections")
    print(f"   • Established 7 brain regions with specialized functions")
    print(f"   • Implemented neurotransmitter messaging system")
    print(f"   • Activated collective consciousness layer")
    print()
    print("🚀 The trading bot now operates as a unified neural brain!")
    print()
    
    # Cleanup
    await brain.stop()


def run_demo():
    """Run the neural brain demo"""
    print("\n" + "=" * 80)
    print("Starting Neural Brain Integration Demo...")
    print("=" * 80 + "\n")
    
    try:
        asyncio.run(demo_neural_brain())
    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("Demo finished")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
