@echo off
REM Hivemind & Perplexity V2 System Launcher
REM Advanced AI Systems for Trading Intelligence

echo ================================================================================
echo HIVEMIND ^& PERPLEXITY V2 - ADVANCED AI SYSTEMS
echo ================================================================================
echo.
echo HIVEMIND V2 Features:
echo   - Neural Mesh Network (telepathic node communication)
echo   - Quantum Entanglement (synchronized decision making)
echo   - Collective Consciousness (unified awareness)
echo.
echo PERPLEXITY V2 Features:
echo   - Deep Research Engine (multi-source synthesis)
echo   - Reasoning Chains (step-by-step logic)
echo   - Knowledge Graph (connected intelligence)
echo.
echo ================================================================================
echo.

REM Resolve Python launcher
set "PY_CMD=python"
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        pause
        exit /b 1
    )
    set "PY_CMD=py"
)

echo Select System:
echo.
echo === HIVEMIND V2 ===
echo [1] Neural Mesh Network Demo
echo [2] Quantum Entanglement Demo
echo [3] Collective Consciousness Demo
echo [4] Full Hivemind V2 System
echo.
echo === PERPLEXITY V2 ===
echo [5] Deep Research Engine Demo
echo [6] Reasoning Chains Demo
echo [7] Knowledge Graph Demo
echo [8] Full Perplexity V2 System
echo.
echo === COMBINED ===
echo [9] Interactive Demo (All Systems)
echo [0] Exit
echo.

set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto neural_mesh
if "%choice%"=="2" goto quantum
if "%choice%"=="3" goto consciousness
if "%choice%"=="4" goto hivemind_full
if "%choice%"=="5" goto research
if "%choice%"=="6" goto reasoning
if "%choice%"=="7" goto knowledge
if "%choice%"=="8" goto perplexity_full
if "%choice%"=="9" goto interactive
if "%choice%"=="0" goto end

echo Invalid choice.
pause
goto :eof

:neural_mesh
echo.
echo ================================================================================
echo Neural Mesh Network - Telepathic Communication
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.hivemind import create_neural_mesh, SignalType
    mesh, comm = create_neural_mesh([\"tech\", \"fund\", \"sent\"], True)
    print(f\"Mesh: {mesh.get_mesh_topology()[\"num_nodes\"]} nodes, {mesh.get_mesh_topology()[\"num_links\"]} links\")
    await comm.broadcast_thought(\"node_tech_0\", \"RSI oversold\", \"analysis\", 0.8)
    mesh.process_signals()
    consensus = await comm.reach_consensus(\"decision\", [\"buy\", \"sell\", \"hold\"])
    print(f\"Consensus: {consensus[\"winner\"].upper()} ({consensus[\"confidence\"]:.1%%})\")
asyncio.run(demo())
''')"
pause
goto :eof

:quantum
echo.
echo ================================================================================
echo Quantum Entanglement - Synchronized Decisions
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.hivemind import create_quantum_entanglement
    engine, bridge = create_quantum_entanglement([\"tech\", \"fund\", \"risk\"])
    await bridge.initialize_quantum_nodes([\"tech\", \"fund\", \"risk\"])
    await bridge.apply_node_analysis(\"tech\", {\"signal\": 0.6, \"confidence\": 0.8})
    await bridge.apply_node_analysis(\"fund\", {\"signal\": 0.4, \"confidence\": 0.7})
    decision = await bridge.get_quantum_decision()
    print(f\"Quantum Decision: {decision[\"action\"].upper()} ({decision[\"confidence\"]:.1%%})\")
    print(f\"Vote distribution: {decision[\"vote_distribution\"]}\")
asyncio.run(demo())
''')"
pause
goto :eof

:consciousness
echo.
echo ================================================================================
echo Collective Consciousness - Unified Awareness
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
from trading_bot.hivemind import create_collective_consciousness
consciousness = create_collective_consciousness()
consciousness.receive_perception(\"price\", {\"trend\": \"up\"}, \"tech\", 0.8)
consciousness.receive_perception(\"news\", {\"sentiment\": \"positive\"}, \"fund\", 0.7)
result = consciousness.process_perceptions()
print(f\"Level: {result[\"consciousness_level\"]}, Emotion: {result[\"emotional_state\"]}\")
decision = consciousness.make_collective_decision([\"buy\", \"sell\", \"hold\"])
print(f\"Decision: {decision[\"decision\"].upper()} ({decision[\"confidence\"]:.1%%})\")
''')"
pause
goto :eof

:hivemind_full
echo.
echo ================================================================================
echo Full Hivemind V2 System
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.hivemind import create_hivemind_v2, HivemindConfig
    config = HivemindConfig(sync_interval_seconds=60)
    hive = create_hivemind_v2(config)
    await hive.start()
    await hive.perceive(\"analysis\", {\"trend\": \"bullish\"}, \"tech\", 0.8)
    decision = await hive.make_decision(\"EURUSD\")
    print(f\"\\n{decision.get_summary()}\")
    await hive.stop()
asyncio.run(demo())
''')"
pause
goto :eof

:research
echo.
echo ================================================================================
echo Deep Research Engine - Multi-Source Synthesis
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.perplexity_trading import create_deep_research_engine, ResearchDepth
    engine = create_deep_research_engine()
    result = await engine.research(\"EURUSD analysis\", ResearchDepth.QUICK)
    print(f\"Findings: {len(result.findings)}\")
    for f in result.findings[:3]:
        print(f\"  - {f.content[:60]}... (conf: {f.confidence:.1%%})\")
asyncio.run(demo())
''')"
pause
goto :eof

:reasoning
echo.
echo ================================================================================
echo Reasoning Chains - Step-by-Step Logic
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.perplexity_trading import create_reasoning_chain_engine
    engine = create_reasoning_chain_engine()
    chain = await engine.reason(\"Should I buy EURUSD?\", use_tree=True)
    print(f\"Thoughts: {chain.total_thoughts}, Verified: {chain.verified_thoughts}\")
    print(f\"Conclusion: {chain.conclusion}\")
    print(f\"Confidence: {chain.final_confidence:.1%%}\")
asyncio.run(demo())
''')"
pause
goto :eof

:knowledge
echo.
echo ================================================================================
echo Knowledge Graph - Connected Intelligence
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
from trading_bot.perplexity_trading import create_knowledge_graph
graph, reasoner = create_knowledge_graph(populate=True)
stats = graph.get_statistics()
print(f\"Entities: {stats[\"total_entities\"]}, Relations: {stats[\"total_relations\"]}\")
answer = reasoner.answer_question(\"What does RSI indicate?\")
print(f\"Q: What does RSI indicate?\")
print(f\"A: {answer[\"answer\"]}\")
''')"
pause
goto :eof

:perplexity_full
echo.
echo ================================================================================
echo Full Perplexity V2 System
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
async def demo():
    from trading_bot.perplexity_trading import create_perplexity_v2, PerplexityConfig
    config = PerplexityConfig()
    orch = create_perplexity_v2(config)
    await orch.initialize()
    decision = await orch.query(\"Analyze EURUSD for trading\")
    print(f\"\\nAction: {decision.action.upper()}\")
    print(f\"Confidence: {decision.confidence:.1%%}\")
    print(f\"Citations: {len(decision.citations)}\")
asyncio.run(demo())
''')"
pause
goto :eof

:interactive
echo.
echo ================================================================================
echo Interactive Demo - All Systems
echo ================================================================================
echo.
%PY_CMD% examples/hivemind_perplexity_v2_demo.py
goto end

:end
echo.
echo ================================================================================
echo Session Complete
echo ================================================================================
pause
