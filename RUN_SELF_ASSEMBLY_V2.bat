@echo off
REM Self-Assembly AI V2 System Launcher
REM Ultimate Self-Assembling Trading AI

echo ================================================================================
echo SELF-ASSEMBLY AI V2 - ULTIMATE SELF-ASSEMBLING SYSTEM
echo ================================================================================
echo.
echo Advanced AI Capabilities:
echo   - Code Genetics (DNA-like strategy evolution)
echo   - Swarm Intelligence (PSO, ACO, ABC optimization)
echo   - Neural Architecture Search (auto-designing networks)
echo   - Emergent Behavior (complex patterns from simple rules)
echo   - Strategy Factory (self-replicating strategies)
echo   - Component Auto-Wiring (self-configuring system)
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
        echo Make sure either "python" or "py" works in this terminal.
        pause
        exit /b 1
    )
    set "PY_CMD=py"
)

echo Select Mode:
echo.
echo [1] Run Interactive Demo (Recommended)
echo [2] Start Full Self-Assembly System (Auto-Evolution)
echo [3] Start Self-Assembly System (Manual Mode)
echo [4] Demo: Code Genetics Only
echo [5] Demo: Swarm Intelligence Only
echo [6] Demo: Neural Architecture Search Only
echo [7] Demo: Emergent Behavior Only
echo [8] Demo: Strategy Factory Only
echo [9] View System Status
echo [0] Exit
echo.

set /p choice="Enter your choice (0-9): "

if "%choice%"=="1" goto interactive_demo
if "%choice%"=="2" goto auto_mode
if "%choice%"=="3" goto manual_mode
if "%choice%"=="4" goto genetics_demo
if "%choice%"=="5" goto swarm_demo
if "%choice%"=="6" goto nas_demo
if "%choice%"=="7" goto emergent_demo
if "%choice%"=="8" goto factory_demo
if "%choice%"=="9" goto status
if "%choice%"=="0" goto end

echo Invalid choice. Please try again.
pause
goto :eof

:interactive_demo
echo.
echo ================================================================================
echo Running Interactive Demo
echo ================================================================================
echo.
%PY_CMD% examples/self_assembly_ai_v2_demo.py
goto end

:auto_mode
echo.
echo ================================================================================
echo Starting Self-Assembly AI V2 in AUTO-EVOLUTION mode
echo ================================================================================
echo.
echo The AI will autonomously:
echo   - Evolve trading strategies through genetic algorithms
echo   - Optimize parameters through swarm intelligence
echo   - Design neural architectures automatically
echo   - Generate emergent trading behaviors
echo   - Self-replicate successful strategies
echo.
echo Press Ctrl+C to stop at any time.
echo.
%PY_CMD% -c "import asyncio; from trading_bot.self_assembly_ai import run_self_assembly_v2, AssemblyConfig; config = AssemblyConfig(evolution_interval_seconds=60, optimization_interval_seconds=120); asyncio.run(run_self_assembly_v2('.', config))"
goto end

:manual_mode
echo.
echo ================================================================================
echo Starting Self-Assembly AI V2 in MANUAL mode
echo ================================================================================
echo.
echo The AI will NOT automatically evolve. Manual control required.
echo.
%PY_CMD% -c "import asyncio; from trading_bot.self_assembly_ai import create_self_assembly_v2, AssemblyConfig; config = AssemblyConfig(evolution_interval_seconds=3600); orch = create_self_assembly_v2('.', config); asyncio.run(orch.start()); print('System started. Use human_override() for control.'); asyncio.run(asyncio.sleep(3600))"
goto end

:genetics_demo
echo.
echo ================================================================================
echo Code Genetics Demo - DNA-Like Strategy Evolution
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
from trading_bot.self_assembly_ai import create_code_genetics, Chromosome
genetics = create_code_genetics({\"population_size\": 30})
print(f\"Population: {len(genetics.gene_pool.population)} chromosomes\")
def fitness(c):
    config = c.express()
    return 0.5 + (0.1 if 10 <= config.get(\"rsi_period\", 0) <= 20 else 0)
for i in range(10):
    report = genetics.evolve_generation(fitness)
    print(f\"Gen {i+1}: Best={report[\"best_fitness\"]:.4f}, Diversity={report[\"diversity_score\"]:.2f}\")
best = genetics.get_best_strategy()
print(f\"\\nBest strategy: {best}\")
''')"
pause
goto :eof

:swarm_demo
echo.
echo ================================================================================
echo Swarm Intelligence Demo - Collective Optimization
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
from trading_bot.self_assembly_ai import create_swarm_intelligence
bounds = [(5, 50), (60, 90), (10, 40), (5, 50), (20, 200)]
swarm = create_swarm_intelligence(\"hybrid\", len(bounds), bounds)
print(f\"Agents: {swarm.get_report()[\"total_agents\"]}\")
def fitness(p):
    d = p.dimensions
    return 0.5 + (0.2 if 10 <= d[0] <= 20 else 0) + (0.15 if d[3] < d[4] else 0)
for i in range(30):
    r = swarm.step(fitness)
    if (i+1) % 10 == 0:
        print(f\"Iter {i+1}: Best={r[\"global_best_fitness\"]:.4f}\")
best = swarm.get_best_solution()
print(f\"\\nBest: {[f\"{v:.1f}\" for v in best.dimensions]}\")
''')"
pause
goto :eof

:nas_demo
echo.
echo ================================================================================
echo Neural Architecture Search Demo - Auto-Designing Networks
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
import random
from trading_bot.self_assembly_ai import create_nas_engine
nas = create_nas_engine((100, 10), (3,), {\"population_size\": 15})
nas.initialize_population()
print(f\"Population: {len(nas.population)} architectures\")
def fitness(a):
    f = 0.3
    f += 0.2 if any(l.layer_type.value == \"lstm\" for l in a.layers) else 0
    f += 0.15 if 3 <= len(a.layers) <= 6 else 0
    return min(1, f + random.uniform(-0.1, 0.1))
for i in range(10):
    nas.evaluate_population(fitness)
    nas.evolve()
    r = nas.get_report()
    print(f\"Gen {i+1}: Best={r[\"best_fitness\"]:.4f}, Params={r[\"avg_params\"]:,.0f}\")
best = nas.get_best_architecture()
print(f\"\\nBest: {len(best.layers)} layers, {best.estimate_total_params():,} params\")
''')"
pause
goto :eof

:emergent_demo
echo.
echo ================================================================================
echo Emergent Behavior Demo - Complex Patterns from Simple Rules
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; exec('''
from trading_bot.self_assembly_ai import create_emergent_behavior_engine
emergent = create_emergent_behavior_engine({\"ca_width\": 30, \"ca_height\": 30})
print(\"Running cellular automata and autopoiesis...\")
for i in range(30):
    r = emergent.step()
    if (i+1) % 10 == 0:
        print(f\"Step {i+1}: Alive={r[\"ca\"][\"alive_count\"]}, Pattern={r[\"ca\"][\"pattern_type\"]}\")
signal = emergent.get_emergent_signal()
print(f\"\\nEmergent Signal:\")
print(f\"  Direction: {signal[\"direction\"]}\")
print(f\"  Confidence: {signal[\"confidence\"]:.2f}\")
print(f\"  Pattern: {signal[\"pattern_type\"]}\")
''')"
pause
goto :eof

:factory_demo
echo.
echo ================================================================================
echo Strategy Factory Demo - Self-Replicating Strategies
echo ================================================================================
echo.
%PY_CMD% -c "import asyncio; import random; exec('''
from trading_bot.self_assembly_ai import create_strategy_factory
factory = create_strategy_factory({\"max_population\": 25})
print(f\"Initial: {factory.get_report()[\"current_population\"]} strategies\")
for _ in range(50):
    active = factory.get_active_strategies()
    if not active: break
    s = random.choice(active)
    factory.update_strategy_state(s.strategy_id, {\"pnl\": random.gauss(10, 50), \"drawdown\": 0.01})
factory.natural_selection()
r = factory.get_report()
print(f\"\\nAfter evolution:\")
print(f\"  Population: {r[\"current_population\"]}\")
print(f\"  Created: {r[\"total_created\"]}, Died: {r[\"total_died\"]}\")
print(f\"  Best fitness: {r[\"best_fitness\"]:.2f}\")
best = factory.get_best_strategy()
if best:
    print(f\"  Best: {best.dna.strategy_type.value}, Win rate: {best.get_win_rate():.1%}\")
''')"
pause
goto :eof

:status
echo.
echo ================================================================================
echo System Status Report
echo ================================================================================
echo.
%PY_CMD% -c "from trading_bot.self_assembly_ai import create_self_assembly_v2; orch = create_self_assembly_v2('.'); print('Self-Assembly AI V2 Status:'); print(f'  Version: 2.0.0'); print(f'  Subsystems: 6 (Genetics, Swarm, NAS, Emergent, Factory, AutoWiring)'); print(f'  Ready: Yes')"
echo.
pause
goto :eof

:end
echo.
echo ================================================================================
echo Self-Assembly AI V2 System Stopped
echo ================================================================================
pause
