@echo off
title Intelligence Core - Self-Auditing Quant Research Lab
color 0A

:menu
cls
echo ================================================================================
echo          INTELLIGENCE CORE - SELF-AUDITING QUANT RESEARCH LAB
echo ================================================================================
echo.
echo THE HIGHEST-LEVEL DESIGN:
echo A self-evaluating, risk-aware learning system that improves HYPOTHESIS quality
echo while detecting unseen failure modes.
echo.
echo CORE PRINCIPLES:
echo   1. AI improves HYPOTHESES, not models
echo   2. AI remembers mistakes STRUCTURALLY, not statistically
echo   3. AI learns how decision-making BREAKS under uncertainty
echo   4. AI becomes HARDER TO FOOL than the market itself
echo.
echo ================================================================================
echo.
echo [1] Run Full Demo (All 7 scenarios)
echo [2] Demo: Hypothesis Engine
echo [3] Demo: Structural Memory
echo [4] Demo: Failure Detection
echo [5] Demo: Self-Audit System
echo [6] Demo: Adversarial Hardening
echo [7] Demo: Governance Layer
echo [8] View Documentation
echo [9] Exit
echo.
echo ================================================================================
set /p choice="Enter your choice (1-9): "

if "%choice%"=="1" goto full_demo
if "%choice%"=="2" goto hypothesis
if "%choice%"=="3" goto memory
if "%choice%"=="4" goto failure
if "%choice%"=="5" goto audit
if "%choice%"=="6" goto hardening
if "%choice%"=="7" goto governance
if "%choice%"=="8" goto docs
if "%choice%"=="9" goto end

echo Invalid choice. Please try again.
timeout /t 2 >nul
goto menu

:full_demo
cls
echo ================================================================================
echo                         RUNNING FULL DEMO
echo ================================================================================
echo.
py examples/intelligence_core_demo.py
echo.
pause
goto menu

:hypothesis
cls
echo ================================================================================
echo                    HYPOTHESIS ENGINE DEMO
echo ================================================================================
echo.
echo AI improves HYPOTHESES, not models.
echo.
py -c "from examples.intelligence_core_demo import demo_hypothesis_engine; demo_hypothesis_engine()"
echo.
pause
goto menu

:memory
cls
echo ================================================================================
echo                    STRUCTURAL MEMORY DEMO
echo ================================================================================
echo.
echo AI remembers mistakes STRUCTURALLY, not statistically.
echo.
py -c "from examples.intelligence_core_demo import demo_structural_memory; demo_structural_memory()"
echo.
pause
goto menu

:failure
cls
echo ================================================================================
echo                    FAILURE DETECTION DEMO
echo ================================================================================
echo.
echo Detect failure modes FASTER than the market changes.
echo.
py -c "from examples.intelligence_core_demo import demo_failure_detection; demo_failure_detection()"
echo.
pause
goto menu

:audit
cls
echo ================================================================================
echo                    SELF-AUDIT SYSTEM DEMO
echo ================================================================================
echo.
echo Continuously audit ALL research activities.
echo.
py -c "from examples.intelligence_core_demo import demo_self_audit; demo_self_audit()"
echo.
pause
goto menu

:hardening
cls
echo ================================================================================
echo                    ADVERSARIAL HARDENING DEMO
echo ================================================================================
echo.
echo Become HARDER TO FOOL than the market itself.
echo.
py -c "from examples.intelligence_core_demo import demo_adversarial_hardening; demo_adversarial_hardening()"
echo.
pause
goto menu

:governance
cls
echo ================================================================================
echo                    GOVERNANCE LAYER DEMO
echo ================================================================================
echo.
echo IMMUTABLE rules that AI CANNOT change.
echo.
py -c "from examples.intelligence_core_demo import demo_governance; demo_governance()"
echo.
pause
goto menu

:docs
cls
echo ================================================================================
echo                         DOCUMENTATION
echo ================================================================================
echo.
echo Opening INTELLIGENCE_CORE_COMPLETE.md...
start "" "INTELLIGENCE_CORE_COMPLETE.md"
echo.
pause
goto menu

:end
cls
echo.
echo Thank you for using the Intelligence Core!
echo.
echo Remember:
echo   - AI CAN: try features, tune hyperparameters, test architectures
echo   - AI CANNOT: deploy models, change risk rules, access capital
echo.
timeout /t 3 >nul
exit
