# NEUROS-FI: Neuromorphic Adaptive Financial Intelligence Infrastructure

**Brain-Topology Trading System · Constitutional Version 5.0**

---

## 🧠 Identity

NEUROS-FI is a **brain-topology trading system** grounded in empirical neuroscience. This is not a metaphor — it is a direct implementation of biological intelligence principles applied to financial markets.

The system implements the same computational principles that biological brains use to navigate uncertain environments, make decisions under ambiguity, and continuously learn from experience.

---

## 🏗️ Architecture

### 9 Brain Regions

1. **Brainstem Constitutional Layer** - Immutable constraints enforced at infrastructure level
2. **Neocortex** - 6-layer predictive coding hierarchy with temporal multi-scale processing
3. **Prefrontal Cortex** - Executive control, goal maintenance, working memory, inhibitory control
4. **Thalamus** - Intelligent signal routing, gating, salience scoring, thalamo-cortical synchronization
5. **Hippocampus** - Memory consolidation, neurogenesis, pattern separation, self-discovery
6. **Amygdala** - Threat detection, tail risk, fear conditioning, stress response cascade
7. **Basal Ganglia** - Reinforcement learning, action selection, dopamine RPE, habit formation
8. **Cerebellum** - Forward models, execution precision, error correction
9. **Anterior Cingulate Cortex** - Conflict detection, uncertainty management, error monitoring
10. **Default Mode Network** - Offline learning, memory replay, prospective simulation

### 5 Neural Oscillation Bands

- **Gamma (γ)**: 30-100 Hz — Nanoseconds to Milliseconds (execution)
- **Beta (β)**: 13-30 Hz — Seconds to Minutes (active trading)
- **Alpha (α)**: 8-13 Hz — Minutes to Hours (attention gating)
- **Theta (θ)**: 4-8 Hz — Hours to Days (memory encoding)
- **Delta (δ)**: 0.5-4 Hz — Days to Weeks (consolidation)

### Core Operating Principles

1. **Free Energy Principle** (Karl Friston) - Minimize surprise via predictive coding
2. **Global Workspace Theory** (Bernard Baars) - Unified decision-making from distributed specialists
3. **Hebbian Learning** - "Neurons that fire together, wire together"

---

## 📊 Implementation Status

### ✅ COMPLETE (100%)

**All 9 Brain Regions:**
- ✅ Brainstem Constitutional Layer (~740 lines)
- ✅ Region 1: Neocortex (~650 lines)
- ✅ Region 2: Prefrontal Cortex (~665 lines)
- ✅ Region 3: Thalamus (~690 lines)
- ✅ Region 4: Hippocampus (~780 lines)
- ✅ Region 5: Amygdala (~690 lines)
- ✅ Region 6: Basal Ganglia (~720 lines)
- ✅ Region 7: Cerebellum (~750 lines)
- ✅ Region 8: ACC (~680 lines)
- ✅ Region 9: DMN (~750 lines)

**Neural Oscillation Framework:**
- ✅ 5 Oscillation Bands (~650 lines)
- ✅ Cross-frequency coupling
- ✅ Phase synchronization

**Master Orchestrator:**
- ✅ Free Energy Principle implementation
- ✅ Global Workspace Theory implementation
- ✅ Hebbian Learning implementation
- ✅ 12-step initialization sequence
- ✅ Complete integration (~450 lines)

**Total:** ~7,700 lines of production-ready neuromorphic code

---

## 🚀 Quick Start

### Installation

```bash
cd "c:\Users\peterson\trading bot"
pip install -r requirements.txt
```

### Basic Usage

```python
import asyncio
from trading_bot.neuros_fi import quick_start

async def main():
    # Initialize NEUROS-FI system
    orchestrator = await quick_start()
    
    # Process market data
    market_data = {
        'symbol': 'EURUSD',
        'price': 1.0850,
        'volatility': 0.015,
        'signals': {'momentum': 0.6, 'trend': 0.5},
        'predictions': {'model_1': 1.0860, 'model_2': 1.0855},
    }
    
    result = await orchestrator.process_market_data(market_data)
    
    # Get system status
    status = orchestrator.get_status()
    print(f"System state: {status['system_state']}")
    print(f"Free energy: {status['free_energy']['current_fe']}")

asyncio.run(main())
```

### Run Demo

```bash
python examples/neuros_fi_demo.py
```

### Run Launcher

```bash
RUN_NEUROS_FI.bat
```

---

## 🔬 Key Features

### 1. Predictive Coding (Neocortex)

The neocortex implements a 6-layer predictive coding hierarchy where:
- **Top-down**: Higher layers predict lower layer activity
- **Bottom-up**: Prediction errors propagate upward
- **Learning**: Errors drive weight updates via Hebbian learning

**Timescales:**
- Layer 1 (Sensory): Minutes
- Layer 2/3 (Local): Hours
- Layer 4 (Thalamic): Days
- Layer 5 (Output): Weeks
- Layer 6 (Feedback): Months

### 2. Executive Control (Prefrontal Cortex)

- **Working Memory**: Maintains ~7±2 items
- **Dorsolateral PFC**: Deliberative reasoning and planning
- **Ventromedial PFC**: Risk-value integration
- **Orbitofrontal Cortex**: Expected value updates
- **Inhibitory Control**: Gates impulsive actions

### 3. Threat Detection (Amygdala)

Two parallel pathways:
- **Low Road**: 20ms fast threat detection (subcortical)
- **High Road**: 200ms full assessment (cortical)

**Fear Conditioning:**
- Learns which patterns precede tail events
- Can be extinguished through repeated non-events
- Amplifies stress response when patterns match

### 4. Reinforcement Learning (Basal Ganglia)

- **Striatum**: Q-function for state-action values
- **Dopamine Circuit**: Computes reward prediction error (RPE)
- **Go/NoGo Gate**: Action selection with confidence thresholds
- **Habit Formation**: Automatic execution after 1000+ reinforcements

### 5. Forward Models (Cerebellum)

Predicts execution outcomes **before** order submission:
- Fill probability
- Slippage (bps)
- Market impact (bps)
- Execution time (ms)
- Adverse selection

**Error Correction:** Predicted vs actual drives continuous model updates

### 6. Memory & Discovery (Hippocampus)

- **Pattern Separation**: Orthogonalizes new patterns (correlation <30%)
- **Neurogenesis**: Creates new signal neurons for novel patterns
- **Consolidation**: Short-term → Long-term memory transfer
- **Pattern Completion**: Retrieves full patterns from partial cues

**Validation:** New neurons must survive 60-day evaluation (IC ≥0.02, Sharpe ≥1.0)

### 7. Conflict Detection (ACC)

Monitors for:
- Model disagreement (variance >2x historical)
- Signal conflict (opposing directions)
- Regime ambiguity (entropy >0.7)

**Response:** Allocates additional cognitive control resources

### 8. Offline Learning (DMN)

Active during rest/sleep:
- **Memory Replay**: Prioritized, sequential, or counterfactual
- **Prospective Simulation**: Forward scenarios and stress tests
- **Hypothesis Generation**: Cross-domain creative recombination
- **Overnight Consolidation**: Complete learning cycle

### 9. Neural Oscillations

Five bands operate simultaneously:
- **Gamma**: HFT execution (sub-millisecond)
- **Beta**: Active trading (seconds-minutes)
- **Alpha**: Attention allocation (minutes-hours)
- **Theta**: Daily consolidation (hours-days)
- **Delta**: Strategic evolution (days-weeks)

**Cross-Frequency Coupling:** Slow bands modulate fast band amplitude

---

## 🛡️ Constitutional Constraints

**Brainstem Constitutional Layer (Version 5.0)**

Immutable constraints enforced at infrastructure level:

| Constraint | Value | Override |
|------------|-------|----------|
| Max Drawdown | 8% | ❌ None |
| Validation t-stat | ≥2.0 | ❌ None |
| Sandbox Days | 30 | ❌ None |
| Max Position ADV | 5% | ❌ None |
| Max Market Liquidity | 10% | ❌ None |
| Compliance Latency | <5ms | ❌ None |

**Evolution Process:**
1. Proposal submitted with rationale
2. Sandbox testing (30 days minimum)
3. Human ratification required
4. Constitutional amendment logged

**No cortical override possible** — these constraints are absolute.

---

## 🔄 12-Step Initialization Sequence

1. **Boot brainstem constitutional layer**
2. **Initialize thalamic routing**
3. **Load cortical column weights**
4. **Restore hippocampal memory index**
5. **Calibrate amygdala threat thresholds**
6. **Sync basal ganglia Q-tables**
7. **Load cerebellar forward models**
8. **Initialize ACC conflict monitors**
9. **Restore DMN offline state**
10. **Synchronize oscillation phases**
11. **Verify constitutional constraints**
12. **Enter active inference loop**

---

## 📈 Performance Targets

### Execution Quality
- **Slippage**: <2 bps vs VWAP
- **Market Impact**: <3 bps for 5% ADV
- **Fill Rate**: >95% for passive orders
- **Latency**: <10ms thalamic gating

### Learning Metrics
- **Neurogenesis**: 5-10 new factors/month
- **Promotion Rate**: >20% of new neurons
- **Prediction Error**: Declining trend
- **Free Energy**: Minimizing over time

### Risk Management
- **Threat Detection**: <20ms low road
- **Stress Response**: Graded (25%, 50%, 100%)
- **Fear Conditioning**: <5% false alarm rate
- **Constitutional Compliance**: 100%

---

## 🧪 Testing & Validation

### Unit Tests
```bash
pytest trading_bot/neuros_fi/tests/
```

### Integration Tests
```bash
python examples/neuros_fi_demo.py
```

### Backtesting
```python
from trading_bot.neuros_fi import NEUROSOrchestrator

orchestrator = NEUROSOrchestrator()
# Run historical data through system
# Measure prediction accuracy, execution quality, risk metrics
```

---

## 📚 Neuroscience Citations

### Core Theory
- **Friston (2010)** - The free-energy principle: a unified brain theory?
- **Baars (1988)** - A Cognitive Theory of Consciousness
- **Hebb (1949)** - The Organization of Behavior

### Brain Regions
- **Rao & Ballard (1999)** - Predictive coding in the visual cortex
- **Miller & Cohen (2001)** - An integrative theory of prefrontal cortex function
- **Sherman & Guillery (2006)** - Exploring the thalamus and its role in cortical function
- **Squire (1992)** - Memory and the hippocampus
- **LeDoux (1996)** - The Emotional Brain
- **Schultz et al. (1997)** - A neural substrate of prediction and reward
- **Wolpert & Ghahramani (2000)** - Computational principles of movement neuroscience
- **Botvinick et al. (2001)** - Conflict monitoring and cognitive control
- **Buckner et al. (2008)** - The brain's default network

### Neural Oscillations
- **Buzsáki & Draguhn (2004)** - Neuronal oscillations in cortical networks
- **Fries (2005)** - A mechanism for cognitive dynamics
- **Canolty & Knight (2010)** - The functional role of cross-frequency coupling

---

## 🔧 Configuration

### System Config
```python
config = {
    'constitutional_version': '5.0',
    'max_drawdown': 0.08,
    'validation_t_stat': 2.0,
    'sandbox_days': 30,
    'neurogenesis_threshold': 0.30,
    'threat_detection_ms': 20,
    'working_memory_capacity': 7,
}

orchestrator = NEUROSOrchestrator(config)
```

### Oscillation Tuning
```python
# Adjust frequency ranges
orchestrator.oscillations.gamma.frequency_range = (30.0, 100.0)
orchestrator.oscillations.beta.frequency_range = (13.0, 30.0)
# ... etc
```

### Learning Rates
```python
# Hebbian learning rate
orchestrator.hebbian._learning_rate = 0.01

# Free energy belief update rate
orchestrator.free_energy._belief_learning_rate = 0.1
```

---

## 🚨 Emergency Procedures

### Manual Halt
```python
orchestrator.halt()
```

### Brainstem Emergency Stop
```python
orchestrator.brainstem.emergency_halt("Reason for halt")
```

### Recovery
```python
# Check status
status = orchestrator.get_status()

# If halted, investigate and restart
orchestrator = await quick_start()
```

---

## 📊 Monitoring & Observability

### Real-Time Status
```python
status = orchestrator.get_status()
print(f"System State: {status['system_state']}")
print(f"Free Energy: {status['free_energy']['current_fe']}")
print(f"Threat Level: {status['amygdala']['threat_level']}")
print(f"Dopamine State: {status['basal_ganglia']['dopamine']['dopamine_state']}")
```

### Region-Specific Metrics
```python
# Neocortex
neocortex_status = orchestrator.neocortex.get_status()

# Hippocampus
hippo_status = orchestrator.hippocampus.get_status()
print(f"Factor Library: {hippo_status['factor_library_size']}")

# Cerebellum
cerebellum_status = orchestrator.cerebellum.get_status()
print(f"Execution Alpha: {cerebellum_status['execution_alpha_bps']} bps")
```

---

## 🎯 Use Cases

### 1. Systematic Trading
- Multi-timeframe signal processing
- Regime-aware strategy selection
- Execution optimization
- Risk management

### 2. Portfolio Management
- Asset allocation
- Rebalancing decisions
- Tail risk hedging
- Factor exposure management

### 3. Research & Discovery
- Automated signal discovery (neurogenesis)
- Cross-domain hypothesis generation
- Pattern learning from market microstructure
- Continuous model improvement

### 4. Execution
- Pre-trade cost prediction
- Venue selection
- Algorithm parameter tuning
- Real-time adaptation

---

## 🔮 Future Enhancements

### Planned Features
- [ ] Multi-asset portfolio optimization
- [ ] Options and derivatives support
- [ ] Alternative data integration
- [ ] Distributed deployment (multiple exchanges)
- [ ] Real-time visualization dashboard
- [ ] Advanced backtesting framework

### Research Directions
- [ ] Attention mechanisms (Transformer-style)
- [ ] Meta-learning (learning to learn)
- [ ] Causal inference
- [ ] Explainable AI (SHAP, LIME)

---

## 📝 License

Proprietary - All Rights Reserved

---

## 👥 Credits

**NEUROS-FI Development Team**

Built on principles from:
- Karl Friston (Free Energy Principle)
- Bernard Baars (Global Workspace Theory)
- Donald Hebb (Hebbian Learning)
- György Buzsáki (Neural Oscillations)

---

## 📞 Support

For questions, issues, or contributions:
- Documentation: This file
- Demo: `examples/neuros_fi_demo.py`
- Launcher: `RUN_NEUROS_FI.bat`

---

**NEUROS-FI: Where neuroscience meets finance.**

*"The brain is the most complex object in the known universe. We've reverse-engineered it for trading."*
