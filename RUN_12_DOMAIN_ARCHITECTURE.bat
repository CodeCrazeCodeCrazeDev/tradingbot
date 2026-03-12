@echo off
title 12-Domain Hedge Fund Architecture
color 0A

echo.
echo ============================================================
echo    12-DOMAIN HEDGE FUND ARCHITECTURE
echo    Mirroring Renaissance Technologies, Two Sigma, Citadel
echo ============================================================
echo.

:MENU
echo.
echo  Select an option:
echo.
echo  [1] Run Full Demo
echo  [2] Quick Status Check
echo  [3] View Architecture Diagram
echo  [4] List All Domains
echo  [5] Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto DEMO
if "%choice%"=="2" goto QUICK
if "%choice%"=="3" goto DIAGRAM
if "%choice%"=="4" goto LIST
if "%choice%"=="5" goto END

echo Invalid choice. Please try again.
goto MENU

:DEMO
echo.
echo Running full 12-domain architecture demo...
echo.
cd /d "%~dp0"
python examples/domain_architecture_demo.py
pause
goto MENU

:QUICK
echo.
echo Running quick status check...
echo.
cd /d "%~dp0"
python examples/domain_architecture_demo.py --quick
pause
goto MENU

:DIAGRAM
echo.
echo ============================================================
echo                 12-DOMAIN ARCHITECTURE
echo ============================================================
echo.
echo   CRITICAL PRIORITY:
echo   ------------------
echo   [1] Alpha Generation    - Signal generation ^& alpha
echo   [3] Risk Management     - Risk control ^& monitoring
echo   [4] Execution           - Trading operations
echo   [5] Data Infrastructure - Data engineering
echo   [12] Governance         - Enterprise governance
echo.
echo   HIGH PRIORITY:
echo   --------------
echo   [2] Quant Research      - Mathematical models
echo   [7] Technology Infra    - Platform engineering
echo   [8] Compliance          - Regulatory compliance
echo.
echo   MEDIUM PRIORITY:
echo   ----------------
echo   [6] Machine Learning    - AI/ML platform
echo   [9] Operations          - Business operations
echo   [11] Portfolio Analytics - Performance ^& attribution
echo.
echo   LOW PRIORITY:
echo   -------------
echo   [10] Research ^& Dev     - Innovation ^& future tech
echo.
echo ============================================================
echo.
pause
goto MENU

:LIST
echo.
echo ============================================================
echo                    ALL 12 DOMAINS
echo ============================================================
echo.
echo  Domain 1:  Alpha Generation
echo            - alpha_research, alpha_engine, alphaalgo_core
echo            - aamis_v3, tamic, signals, strategies
echo.
echo  Domain 2:  Quant Research
echo            - analysis, advanced_analysis, deepchart
echo            - market_intelligence, adaptive_systems
echo.
echo  Domain 3:  Risk Management
echo            - risk, risk_management, hedge_fund_safety
echo            - position, portfolio, safety
echo.
echo  Domain 4:  Execution
echo            - execution, brokers, hft, market_making
echo            - connectivity, streaming, realtime
echo.
echo  Domain 5:  Data Infrastructure
echo            - data, database, ingestion, data_feeds
echo            - monitoring, observability, telemetry
echo.
echo  Domain 6:  Machine Learning
echo            - ml, ai_core, neural_integration
echo            - self_learning, brain, evolution
echo.
echo  Domain 7:  Technology Infrastructure
echo            - infrastructure, core, services
echo            - devops, deployment, production
echo.
echo  Domain 8:  Compliance
echo            - compliance, audit, governance
echo            - security, surveillance, reporting
echo.
echo  Domain 9:  Operations
echo            - ops, orchestrator, automation
echo            - integration, improvement_agent
echo.
echo  Domain 10: Research ^& Development
echo            - research, innovations, quantum
echo            - blockchain, autonomous
echo.
echo  Domain 11: Portfolio Analytics
echo            - analytics, performance, visualization
echo            - backtesting, profit_maximizer
echo.
echo  Domain 12: Governance ^& Control
echo            - alphaalgo_core, governance, safety
echo            - master_system, unified_system
echo.
echo ============================================================
echo.
pause
goto MENU

:END
echo.
echo Goodbye!
echo.
exit /b 0
