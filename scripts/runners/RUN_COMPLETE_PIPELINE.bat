@echo off
REM ============================================================================
REM ALPHAALGO COMPLETE 9-STAGE TRADING PIPELINE
REM ============================================================================
REM Integrates ALL trading bot modules through the complete pipeline:
REM   1. MARKET DATA - MT5, cTrader, all data sources
REM   2. VALIDATION - Data quality, anomaly detection
REM   3. FEATURES - Feature engineering, technical analysis
REM   4. AI ANALYSIS - DeepSeek, cognitive architecture, ML
REM   5. SIGNALS - Signal generation and validation
REM   6. RISK CHECK - MSOS, safety systems (VETO POWER)
REM   7. GOVERNANCE - Human approval, G0/G1/G2 hierarchy
REM   8. EXECUTION - MT5/cTrader execution
REM   9. MONITORING - Performance tracking, feedback loop
REM
REM Plus: Evolution Engine, Unified Human Approval System
REM ============================================================================

title AlphaAlgo Complete 9-Stage Pipeline
color 0B

setlocal enabledelayedexpansion
cd /d "%~dp0"

:MAIN_MENU
cls
echo.
echo ================================================================================
echo          ALPHAALGO COMPLETE 9-STAGE TRADING PIPELINE
echo ================================================================================
echo.
echo  ┌─────────────────────────────────────────────────────────────────────────┐
echo  │  MARKET DATA → VALIDATION → FEATURES → AI ANALYSIS → SIGNALS           │
echo  │       ↓                                                                 │
echo  │  RISK CHECK ⚠️ (VETO) → GOVERNANCE → EXECUTION → MONITORING            │
echo  └─────────────────────────────────────────────────────────────────────────┘
echo.
echo  Brokers: MT5 + cTrader    DeepSeek: Enabled    Evolution: Enabled
echo.
echo ================================================================================
echo.
echo                        QUICK START
echo ================================================================================
echo.
echo   [1] Run Complete Pipeline - PAPER MODE (Safe)
echo       - All 9 stages active
echo       - MT5 + cTrader data
echo       - Human approval required
echo       - No real money
echo.
echo   [2] Run Complete Pipeline - LIVE MODE (Real Money)
echo       - All 9 stages active
echo       - Real execution on MT5/cTrader
echo       - Multiple safety confirmations
echo.
echo   [3] Run Complete Pipeline - AUTONOMOUS MODE
echo       - Auto-approve low-risk trades
echo       - DeepSeek verification required
echo       - Continuous operation
echo.
echo ================================================================================
echo.
echo                        BROKER SELECTION
echo ================================================================================
echo.
echo   [10] Run with MT5 Only
echo   [11] Run with cTrader Only
echo   [12] Run with Both MT5 + cTrader
echo.
echo ================================================================================
echo.
echo                        APPROVAL SYSTEM
echo ================================================================================
echo.
echo   [20] Launch Approval Dashboard (Web)
echo   [21] Launch Approval CLI
echo   [22] View Pending Approvals
echo.
echo ================================================================================
echo.
echo                        SYSTEM TOOLS
echo ================================================================================
echo.
echo   [30] Validate Pipeline
echo   [31] View Pipeline Architecture
echo   [32] Run Single Cycle (Test)
echo   [33] Check Dependencies
echo.
echo   [0] Exit
echo.
echo ================================================================================
echo.

set /p choice="Select option (0-33): "

if "%choice%"=="1" goto :PAPER_MODE
if "%choice%"=="2" goto :LIVE_MODE
if "%choice%"=="3" goto :AUTONOMOUS_MODE

if "%choice%"=="10" goto :MT5_ONLY
if "%choice%"=="11" goto :CTRADER_ONLY
if "%choice%"=="12" goto :BOTH_BROKERS

if "%choice%"=="20" goto :APPROVAL_WEB
if "%choice%"=="21" goto :APPROVAL_CLI
if "%choice%"=="22" goto :VIEW_APPROVALS

if "%choice%"=="30" goto :VALIDATE
if "%choice%"=="31" goto :ARCHITECTURE
if "%choice%"=="32" goto :SINGLE_CYCLE
if "%choice%"=="33" goto :DEPENDENCIES

if "%choice%"=="0" goto :EXIT
goto :MAIN_MENU

REM ============================================================================
REM PAPER MODE
REM ============================================================================

:PAPER_MODE
cls
echo.
echo ================================================================================
echo              COMPLETE PIPELINE - PAPER TRADING MODE
echo ================================================================================
echo.
echo CONFIGURATION:
echo   Mode: PAPER (No real money)
echo   Brokers: MT5 + cTrader
echo   Human Approval: REQUIRED
echo   DeepSeek: ENABLED
echo   Evolution: ENABLED
echo.
echo PIPELINE STAGES:
echo   [1] MARKET DATA - MT5, cTrader, Yahoo, Binance, News, Sentiment
echo   [2] VALIDATION - Quality checks, anomaly detection, quarantine
echo   [3] FEATURES - Technical indicators, patterns, ML features
echo   [4] AI ANALYSIS - DeepSeek, 10-layer cognitive, Offline RL
echo   [5] SIGNALS - Signal generation with verification
echo   [6] RISK CHECK - MSOS, 2%% max risk, 5%% daily loss, 20%% drawdown
echo   [7] GOVERNANCE - Human approval via dashboard/CLI
echo   [8] EXECUTION - Paper execution (simulated)
echo   [9] MONITORING - Performance tracking, feedback loop
echo.
echo SAFETY LIMITS (IMMUTABLE):
echo   Max Risk Per Trade: 2%%
echo   Max Daily Loss: 5%%
echo   Max Drawdown: 20%%
echo   Max Leverage: 5x
echo.
echo ================================================================================
echo.
echo Starting pipeline in PAPER mode...
echo Press Ctrl+C to stop
echo.
pause

py trading_bot\complete_pipeline_orchestrator.py --mode paper --broker both --symbols EURUSD GBPUSD USDJPY

echo.
pause
goto :MAIN_MENU

REM ============================================================================
REM LIVE MODE
REM ============================================================================

:LIVE_MODE
cls
echo.
echo ================================================================================
echo              *** LIVE TRADING MODE - REAL MONEY ***
echo ================================================================================
echo.
echo WARNING: This will execute REAL trades with REAL money!
echo.
echo SAFETY CHECKS:
echo   [x] All 9 pipeline stages active
echo   [x] Risk check with VETO power
echo   [x] Human approval REQUIRED for all trades
echo   [x] DeepSeek verification REQUIRED
echo   [x] Circuit breakers active
echo   [x] Emergency shutdown available
echo.
echo IMMUTABLE LIMITS:
echo   Max Risk Per Trade: 2%%
echo   Max Daily Loss: 5%%
echo   Max Drawdown: 20%%
echo.
echo ================================================================================
echo.

set /p confirm1="Type 'I UNDERSTAND THE RISKS' to continue: "
if not "%confirm1%"=="I UNDERSTAND THE RISKS" (
    echo Cancelled. Returning to menu...
    timeout /t 2 > nul
    goto :MAIN_MENU
)

echo.
set /p confirm2="Have you tested in PAPER mode successfully? (YES/NO): "
if not "%confirm2%"=="YES" (
    echo.
    echo ERROR: Test in PAPER mode first!
    timeout /t 3 > nul
    goto :MAIN_MENU
)

echo.
set /p confirm3="Are MT5/cTrader credentials configured? (YES/NO): "
if not "%confirm3%"=="YES" (
    echo.
    echo ERROR: Configure broker credentials first!
    timeout /t 3 > nul
    goto :MAIN_MENU
)

echo.
set /p confirm4="Type 'START LIVE TRADING' to final confirm: "
if not "%confirm4%"=="START LIVE TRADING" (
    echo Cancelled. Returning to menu...
    timeout /t 2 > nul
    goto :MAIN_MENU
)

echo.
echo ================================================================================
echo Starting LIVE trading pipeline...
echo ================================================================================
echo.

py trading_bot\complete_pipeline_orchestrator.py --mode live --broker both --symbols EURUSD GBPUSD

echo.
pause
goto :MAIN_MENU

REM ============================================================================
REM AUTONOMOUS MODE
REM ============================================================================

:AUTONOMOUS_MODE
cls
echo.
echo ================================================================================
echo              AUTONOMOUS TRADING MODE
echo ================================================================================
echo.
echo This mode will:
echo   - Auto-approve LOW-RISK trades (risk_score ^< 0.3, DeepSeek ^>= 0.9)
echo   - Still require approval for HIGH-RISK trades
echo   - Run continuously until stopped
echo   - Use all safety systems
echo.
echo REQUIREMENTS FOR AUTO-APPROVAL:
echo   - Risk score ^< 0.3 (low risk)
echo   - DeepSeek verification score ^>= 0.9 (high confidence)
echo   - Within all risk limits
echo   - No circuit breaker active
echo.
echo HIGH-RISK trades will STILL require manual approval!
echo.
echo ================================================================================
echo.

set /p mode="Select mode - PAPER or LIVE: "
if /i "%mode%"=="LIVE" (
    set /p confirm="Type 'CONFIRM AUTONOMOUS LIVE' to proceed: "
    if not "!confirm!"=="CONFIRM AUTONOMOUS LIVE" (
        echo Cancelled.
        timeout /t 2 > nul
        goto :MAIN_MENU
    )
    set trading_mode=live
) else (
    set trading_mode=paper
)

echo.
echo Starting AUTONOMOUS mode (%trading_mode%)...
echo Low-risk trades will be auto-approved
echo Press Ctrl+C to stop
echo.

py -c "
import asyncio
import sys
sys.path.insert(0, '.')

from trading_bot.complete_pipeline_orchestrator import (
    CompletePipelineOrchestrator, 
    PipelineConfig, 
    TradingMode, 
    BrokerType
)

async def run_autonomous():
    config = PipelineConfig(
        mode=TradingMode('%trading_mode%'),
        primary_broker=BrokerType.MT5,
        secondary_broker=BrokerType.CTRADER,
        symbols=['EURUSD', 'GBPUSD', 'USDJPY'],
        require_human_approval=True,
        auto_approve_low_risk=True,  # Auto-approve low-risk trades
        use_deepseek=True,
        enable_evolution=True,
    )
    
    orchestrator = CompletePipelineOrchestrator(config)
    await orchestrator.run(cycles=-1)  # Run forever

asyncio.run(run_autonomous())
"

echo.
pause
goto :MAIN_MENU

REM ============================================================================
REM BROKER SELECTION
REM ============================================================================

:MT5_ONLY
cls
echo.
echo ================================================================================
echo              MT5 ONLY MODE
echo ================================================================================
echo.
echo Using MetaTrader 5 for:
echo   - Market data
echo   - Trade execution
echo.

set /p mode="Select mode - PAPER or LIVE: "
if /i "%mode%"=="LIVE" (
    set trading_mode=live
) else (
    set trading_mode=paper
)

py trading_bot\complete_pipeline_orchestrator.py --mode %trading_mode% --broker mt5 --symbols EURUSD GBPUSD

pause
goto :MAIN_MENU

:CTRADER_ONLY
cls
echo.
echo ================================================================================
echo              cTRADER ONLY MODE
echo ================================================================================
echo.
echo Using cTrader for:
echo   - Market data (via Open API)
echo   - Trade execution
echo.
echo NOTE: Ensure cTrader Open API credentials are configured.
echo.

set /p mode="Select mode - PAPER or LIVE: "
if /i "%mode%"=="LIVE" (
    set trading_mode=live
) else (
    set trading_mode=paper
)

py trading_bot\complete_pipeline_orchestrator.py --mode %trading_mode% --broker ctrader --symbols EURUSD GBPUSD

pause
goto :MAIN_MENU

:BOTH_BROKERS
cls
echo.
echo ================================================================================
echo              MT5 + cTRADER MODE
echo ================================================================================
echo.
echo Using both brokers:
echo   - MT5: Primary broker
echo   - cTrader: Secondary/backup
echo   - Best price execution
echo   - Failover support
echo.

set /p mode="Select mode - PAPER or LIVE: "
if /i "%mode%"=="LIVE" (
    set trading_mode=live
) else (
    set trading_mode=paper
)

py trading_bot\complete_pipeline_orchestrator.py --mode %trading_mode% --broker both --symbols EURUSD GBPUSD USDJPY

pause
goto :MAIN_MENU

REM ============================================================================
REM APPROVAL SYSTEM
REM ============================================================================

:APPROVAL_WEB
cls
echo.
echo ================================================================================
echo              APPROVAL DASHBOARD - WEB INTERFACE
echo ================================================================================
echo.
echo Starting web dashboard on http://localhost:8080
echo.

if exist "run_approval_dashboard.py" (
    py run_approval_dashboard.py
) else (
    echo Dashboard not found. Using CLI instead...
    py approve.py
)

pause
goto :MAIN_MENU

:APPROVAL_CLI
cls
echo.
echo ================================================================================
echo              APPROVAL CLI
echo ================================================================================
echo.

if exist "approve.py" (
    py approve.py
) else (
    echo CLI not found.
)

pause
goto :MAIN_MENU

:VIEW_APPROVALS
cls
echo.
echo ================================================================================
echo              PENDING APPROVALS
echo ================================================================================
echo.

py -c "
import sys
sys.path.insert(0, '.')

try:
    from trading_bot.unified_approval import get_approval_hub
    hub = get_approval_hub()
    pending = hub.get_pending_requests()
    
    if not pending:
        print('No pending approvals.')
    else:
        print(f'Found {len(pending)} pending approvals:')
        print()
        for req in pending:
            print(f'  ID: {req.request_id}')
            print(f'  Title: {req.title}')
            print(f'  Priority: {req.priority.value}')
            print(f'  Created: {req.created_at}')
            print()
except Exception as e:
    print(f'Error: {e}')
"

pause
goto :MAIN_MENU

REM ============================================================================
REM SYSTEM TOOLS
REM ============================================================================

:VALIDATE
cls
echo.
echo ================================================================================
echo              PIPELINE VALIDATION
echo ================================================================================
echo.

py -c "
import sys
import asyncio
sys.path.insert(0, '.')

print('Validating Complete Pipeline Orchestrator...')
print()

# Test imports
stages = [
    ('Stage 1: Market Data', 'trading_bot.complete_pipeline_orchestrator', 'MarketDataStage'),
    ('Stage 2: Validation', 'trading_bot.complete_pipeline_orchestrator', 'ValidationStage'),
    ('Stage 3: Features', 'trading_bot.complete_pipeline_orchestrator', 'FeatureStage'),
    ('Stage 4: AI Analysis', 'trading_bot.complete_pipeline_orchestrator', 'AIAnalysisStage'),
    ('Stage 5: Signals', 'trading_bot.complete_pipeline_orchestrator', 'SignalStage'),
    ('Stage 6: Risk Check', 'trading_bot.complete_pipeline_orchestrator', 'RiskCheckStage'),
    ('Stage 7: Governance', 'trading_bot.complete_pipeline_orchestrator', 'GovernanceStage'),
    ('Stage 8: Execution', 'trading_bot.complete_pipeline_orchestrator', 'ExecutionStage'),
    ('Stage 9: Monitoring', 'trading_bot.complete_pipeline_orchestrator', 'MonitoringStage'),
    ('Evolution Engine', 'trading_bot.complete_pipeline_orchestrator', 'EvolutionEngine'),
]

all_ok = True
for name, module, cls in stages:
    try:
        mod = __import__(module, fromlist=[cls])
        getattr(mod, cls)
        print(f'✓ {name}')
    except Exception as e:
        print(f'✗ {name}: {e}')
        all_ok = False

print()

# Test orchestrator
try:
    from trading_bot.complete_pipeline_orchestrator import CompletePipelineOrchestrator, PipelineConfig
    config = PipelineConfig()
    orchestrator = CompletePipelineOrchestrator(config)
    print('✓ CompletePipelineOrchestrator')
except Exception as e:
    print(f'✗ CompletePipelineOrchestrator: {e}')
    all_ok = False

print()
if all_ok:
    print('='*50)
    print('ALL VALIDATIONS PASSED')
    print('='*50)
else:
    print('='*50)
    print('SOME VALIDATIONS FAILED')
    print('='*50)
"

pause
goto :MAIN_MENU

:ARCHITECTURE
cls
echo.
echo ================================================================================
echo              9-STAGE PIPELINE ARCHITECTURE
echo ================================================================================
echo.
echo ┌─────────────────────────────────────────────────────────────────────────────┐
echo │                         ALPHAALGO TRADING PIPELINE                          │
echo └─────────────────────────────────────────────────────────────────────────────┘
echo.
echo STAGE 1: MARKET DATA (~350 files)
echo     ↓ Raw data from MT5, cTrader, Yahoo, Binance, News, Sentiment
echo STAGE 2: VALIDATION (~280 files)
echo     ↓ Clean, validated data (quarantine bad data)
echo STAGE 3: FEATURES (~420 files)
echo     ↓ Engineered features (technical, ML, alternative)
echo STAGE 4: AI ANALYSIS (~450 files)
echo     ↓ AI predictions (DeepSeek, Cognitive, Offline RL)
echo STAGE 5: SIGNALS (~320 files)
echo     ↓ Trading signals with verification
echo.
echo ┌─────────────────────────────────────────────────────────────────────────────┐
echo │  STAGE 6: RISK CHECK ⚠️ (~280 files) - CRITICAL GATE WITH VETO POWER       │
echo │  MSOS: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."        │
echo │  Limits: 2%% risk, 5%% daily loss, 20%% drawdown                            │
echo └─────────────────────────────────────────────────────────────────────────────┘
echo     ↓ APPROVED (or REJECTED)
echo STAGE 7: GOVERNANCE (~80 files)
echo     ↓ Human approval (G0 ^> G1 ^> G2 hierarchy)
echo STAGE 8: EXECUTION (~150 files)
echo     ↓ Orders sent to MT5/cTrader
echo STAGE 9: MONITORING (~500 files)
echo     ↓ Feedback loop, performance tracking
echo.
echo TOTAL: ~2,830 files organized in 9 stages
echo.
echo PRINCIPLE: Survival ^> Profit
echo "The bot doesn't try to win. The bot tries not to die."
echo.
echo ================================================================================
echo.
pause
goto :MAIN_MENU

:SINGLE_CYCLE
cls
echo.
echo ================================================================================
echo              SINGLE PIPELINE CYCLE (TEST)
echo ================================================================================
echo.
echo Running one complete pipeline cycle...
echo.

py -c "
import asyncio
import sys
sys.path.insert(0, '.')

from trading_bot.complete_pipeline_orchestrator import (
    CompletePipelineOrchestrator, 
    PipelineConfig, 
    TradingMode
)

async def run_single():
    config = PipelineConfig(
        mode=TradingMode.PAPER,
        require_human_approval=False,  # Auto-approve for test
        use_deepseek=True,
        enable_evolution=False,
    )
    
    orchestrator = CompletePipelineOrchestrator(config)
    
    if await orchestrator.initialize():
        result = await orchestrator.run_pipeline_cycle()
        
        if result:
            print()
            print('='*50)
            print('CYCLE RESULT')
            print('='*50)
            print(f'Order ID: {result.order_id}')
            print(f'Symbol: {result.symbol}')
            print(f'Status: {result.status}')
            print(f'Fill Price: {result.fill_price}')
            print(f'Slippage: {result.slippage}')
        else:
            print()
            print('No trade executed (normal - may not have signal)')
        
        await orchestrator.shutdown()

asyncio.run(run_single())
"

echo.
pause
goto :MAIN_MENU

:DEPENDENCIES
cls
echo.
echo ================================================================================
echo              DEPENDENCY CHECK
echo ================================================================================
echo.

py -c "
import importlib

required = [
    ('numpy', 'Core numerical computing'),
    ('pandas', 'Data manipulation'),
    ('asyncio', 'Async operations'),
    ('MetaTrader5', 'MT5 trading (optional)'),
    ('torch', 'Deep learning'),
    ('sklearn', 'Machine learning'),
    ('ta', 'Technical analysis'),
    ('requests', 'HTTP requests'),
    ('websockets', 'WebSocket connections'),
    ('flask', 'Web dashboard'),
]

print('Checking dependencies...')
print()

for pkg, desc in required:
    try:
        importlib.import_module(pkg)
        print(f'✓ {pkg} - {desc}')
    except ImportError:
        print(f'✗ {pkg} - {desc} (NOT INSTALLED)')

print()
print('Note: MetaTrader5 is optional - simulation mode works without it')
"

pause
goto :MAIN_MENU

:EXIT
cls
echo.
echo ================================================================================
echo              ALPHAALGO COMPLETE PIPELINE
echo ================================================================================
echo.
echo Thank you for using AlphaAlgo Complete 9-Stage Pipeline!
echo.
echo REMEMBER:
echo   - All 9 stages work together
echo   - Stage 6 (Risk Check) has VETO power
echo   - Human approval is ALWAYS available
echo   - Safety limits are IMMUTABLE (2%%, 5%%, 20%%)
echo.
echo FILES:
echo   - trading_bot/complete_pipeline_orchestrator.py
echo   - RUN_COMPLETE_PIPELINE.bat (this file)
echo.
echo PRINCIPLE: "AlphaAlgo does not try to win. AlphaAlgo tries to not die."
echo.
echo ================================================================================
echo.
timeout /t 5
exit /b 0
