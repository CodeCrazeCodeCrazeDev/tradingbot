@echo off
title Intelligent & Social Delegation System
echo ======================================================
echo   INTELLIGENT ^& SOCIAL DELEGATION SYSTEM
echo   Based on Google DeepMind (2026, arXiv:2602.11865)
echo ======================================================
echo.
echo   9 Framework Components ^| 34 Risk Mitigations ^| 17 Threat Categories
echo.
echo   [1] Run Full Demo (all 7 demos)
echo   [2] Quick Start (Python interactive)
echo   [3] View Risk Dashboard
echo   [4] Exit
echo.
set /p choice="Select option: "

if "%choice%"=="1" (
    echo.
    echo Running full demo...
    py examples\intelligent_delegation_demo.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo Starting interactive Python...
    py -i -c "from trading_bot.intelligent_delegation import *; orchestrator = quick_start(); print('Orchestrator ready. Use: await orchestrator.delegate(task)')"
    pause
) else if "%choice%"=="3" (
    echo.
    py -c "from trading_bot.intelligent_delegation import ALL_RISK_MITIGATIONS; [print(f'{i+1:2d}. [{m.severity_before.name}->{m.severity_after.name}] {m.risk.value}: {m.mitigation_strategy[:80]}') for i,m in enumerate(ALL_RISK_MITIGATIONS)]"
    pause
) else if "%choice%"=="4" (
    exit
) else (
    echo Invalid option.
    pause
)
