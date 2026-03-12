@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

:: Neural Brain Integration Launcher
:: Launches the brain-like neural architecture connecting all 100+ modules

title 🧠 Neural Brain Integration - AlphaAlgo Trading Bot

cls
echo ================================================================
echo 🧠 NEURAL BRAIN INTEGRATION ARCHITECTURE
echo ================================================================
echo.
echo Connecting all 100+ trading bot modules like neurons in a brain
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found! Please install Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python found

:: Set UTF-8 encoding
set PYTHONIOENCODING=utf-8

echo.
echo ================================================================
echo SELECT DEMO TYPE
echo ================================================================
echo.
echo [1] Full Neural Brain Demo (Complete walkthrough)
echo [2] Quick Brain Stats (Just show statistics)
echo [3] Stimulate Specific Module (Interactive)
echo [4] Query Module Status (Interactive)
echo [5] Export Connectome (Save neural map to JSON)
echo [6] Run Continuous Neural Processing
echo [7] Run Integration Test
echo [0] Exit
echo.

set /p choice="Enter your choice (0-7): "

if "%choice%"=="1" goto full_demo
if "%choice%"=="2" goto quick_stats
if "%choice%"=="3" goto stimulate_module
if "%choice%"=="4" goto query_module
if "%choice%"=="5" goto export_connectome
if "%choice%"=="6" goto continuous_processing
if "%choice%"=="7" goto integration_test
if "%choice%"=="0" goto exit_script

echo ❌ Invalid choice
pause
exit /b 1

:full_demo
echo.
echo ================================================================
echo 🚀 RUNNING FULL NEURAL BRAIN DEMO
echo ================================================================
echo.
echo This will demonstrate:
echo   • Neural brain architecture with 7 regions
echo   • 100+ modules connected as neurons
echo   • Neurotransmitter messaging system
echo   • Collective consciousness layer
echo   • Brain stem vital functions
echo.
echo Press any key to start...
pause >nul
echo.

python examples\neural_brain_demo.py

if errorlevel 1 (
    echo.
    echo ❌ Demo failed. Check errors above.
) else (
    echo.
    echo ✅ Demo completed successfully!
)

pause
exit /b 0

:quick_stats
echo.
echo ================================================================
echo 📊 QUICK BRAIN STATISTICS
echo ================================================================
echo.

python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from trading_bot.neural_integration import quick_start_neural_brain, brain_stats

async def show_stats():
    brain = await quick_start_neural_brain()
    stats = await brain_stats()
    
    print('=' * 70)
    print('🧠 NEURAL BRAIN STATISTICS')
    print('=' * 70)
    print()
    print(f'Total Modules: {stats[\"total_modules\"]}')
    print(f'Total Synapses: {stats[\"total_synapses\"]}')
    print(f'Active Connections: {stats[\"active_connections\"]}')
    print(f'Consciousness Level: {stats[\"consciousness_level\"]:.2f}')
    print()
    print('Brain Regions:')
    for region, count in sorted(stats['regions'].items(), key=lambda x: x[1], reverse=True):
        print(f'  • {region}: {count} modules')
    print()
    print('=' * 70)
    
    await brain.stop()

asyncio.run(show_stats())
"

pause
exit /b 0

:stimulate_module
echo.
echo ================================================================
echo ⚡ STIMULATE SPECIFIC MODULE
echo ================================================================
echo.

:: Show available modules
python -c "
from trading_bot.neural_integration import SYNAPTIC_MATRIX
print('Available Brain Regions and Modules:')
print()
for region in ['brain_stem', 'thalamus', 'neocortex', 'limbic_system', 'cerebellum', 'hippocampus', 'hypothalamus']:
    modules = SYNAPTIC_MATRIX.get_all_modules_in_region(region)
    print(f'{region.upper()}: {len(modules)} modules')
    for m in modules[:5]:
        print(f'  • {m}')
    if len(modules) > 5:
        print(f'  ... and {len(modules) - 5} more')
    print()
"

echo.
set /p module_name="Enter module name to stimulate: "
set /p data_type="Enter data type (market/analysis/decision): "

python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from trading_bot.neural_integration import quick_start_neural_brain, stimulate

async def stim():
    brain = await quick_start_neural_brain()
    
    result = await stimulate('%module_name%', {
        'action': 'process',
        'type': '%data_type%',
        'test': True
    })
    
    print()
    print('Stimulation Result:')
    print(result)
    
    await brain.stop()

asyncio.run(stim())
"

pause
exit /b 0

:query_module
echo.
echo ================================================================
echo 🔍 QUERY MODULE STATUS
echo ================================================================
echo.

set /p module_name="Enter module name to query: "

python -c "
import asyncio
import sys
import json
sys.path.insert(0, '.')
from trading_bot.neural_integration import quick_start_neural_brain, query

async def q():
    brain = await quick_start_neural_brain()
    
    status = await query('%module_name%', 'status')
    
    print()
    print('Module Status:')
    print(json.dumps(status, indent=2, default=str))
    
    await brain.stop()

asyncio.run(q())
"

pause
exit /b 0

:export_connectome
echo.
echo ================================================================
echo 💾 EXPORT CONNECTOME TO JSON
echo ================================================================
echo.

set /p filename="Enter filename (default: neural_connectome.json): "
if "%filename%"=="" set filename=neural_connectome.json

python -c "
from trading_bot.neural_integration import SYNAPTIC_MATRIX
SYNAPTIC_MATRIX.export_connectome('%filename%')
print(f'Connectome exported to: %filename%')
"

if exist "%filename%" (
    echo ✅ Connectome saved successfully!
    echo.
    echo First few lines:
    head -20 "%filename%"
) else (
    echo ❌ Failed to export connectome
)

pause
exit /b 0

:continuous_processing
echo.
echo ================================================================
echo 🔄 CONTINUOUS NEURAL PROCESSING
echo ================================================================
echo.
echo Starting continuous neural processing mode...
echo Press Ctrl+C to stop
echo.

python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from trading_bot.neural_integration import quick_start_neural_brain, brain_stats

async def continuous():
    brain = await quick_start_neural_brain()
    
    print('Neural brain running in continuous mode...')
    print('Stats will update every 10 seconds')
    print()
    
    try:
        while True:
            stats = brain.get_brain_statistics()
            print(f'\\rConsciousness: {stats[\"consciousness_level\"]:.2f} | '
                  f'Modules: {stats[\"total_modules\"]} | '
                  f'Connections: {stats[\"active_connections\"]} | '
                  f'Status: {stats[\"brain_stem_health\"][\"status\"]}', 
                  end='', flush=True)
            await asyncio.sleep(10)
    except KeyboardInterrupt:
        print()
        print('\\nStopping neural processing...')
        await brain.stop()

asyncio.run(continuous())
"

echo.
echo Neural processing stopped
pause
exit /b 0

:integration_test
echo.
echo ================================================================
echo 🧪 RUNNING INTEGRATION TEST
echo ================================================================
echo.

python -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def test():
    print('Testing Neural Integration Components...')
    print()
    
    # Test 1: Neural Hub
    try:
        from trading_bot.neural_integration import NeuralIntegrationHub
        hub = NeuralIntegrationHub()
        print('✅ Neural Hub: OK')
    except Exception as e:
        print(f'❌ Neural Hub: {e}')
    
    # Test 2: Synaptic Matrix
    try:
        from trading_bot.neural_integration import SYNAPTIC_MATRIX
        stats = SYNAPTIC_MATRIX.get_connectome_stats()
        print(f'✅ Synaptic Matrix: {stats[\"total_modules\"]} modules mapped')
    except Exception as e:
        print(f'❌ Synaptic Matrix: {e}')
    
    # Test 3: Neurotransmitters
    try:
        from trading_bot.neural_integration import SYNAPTIC_CLEFT, CONSCIOUSNESS, BRAIN_STEM
        print('✅ Neurotransmitter System: OK')
    except Exception as e:
        print(f'❌ Neurotransmitter System: {e}')
    
    # Test 4: Brain Orchestrator
    try:
        from trading_bot.neural_integration import quick_start_neural_brain
        brain = await quick_start_neural_brain()
        stats = brain.get_brain_statistics()
        print(f'✅ Brain Orchestrator: {stats[\"total_modules\"]} modules active')
        await brain.stop()
    except Exception as e:
        print(f'❌ Brain Orchestrator: {e}')
    
    print()
    print('=' * 70)
    print('Integration test complete!')

asyncio.run(test())
"

pause
exit /b 0

:exit_script
echo.
echo 👋 Goodbye!
echo.
exit /b 0
