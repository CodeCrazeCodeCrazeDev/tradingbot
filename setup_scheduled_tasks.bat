@echo off
title Setup Windows Scheduled Tasks
color 0B

echo ======================================================
echo   SETUP WINDOWS SCHEDULED TASKS FOR TRADING BOT
echo ======================================================
echo.
echo This will create Windows Task Scheduler tasks for:
echo   1. Data Cleanup (Daily 1 AM)
echo   2. Offline RL Training (Daily 2 AM)
echo   3. Neural Evolution (Daily 3 AM)
echo   4. Performance Analysis (Daily 5 PM)
echo   5. Model Retraining (Saturday 2 AM)
echo   6. Adversarial Testing (Sunday 3 AM)
echo   7. Pattern Discovery (Sunday 4 AM)
echo   8. Strategy Optimization (Sunday 5 AM)
echo.
echo NOTE: Requires Administrator privileges!
echo.
pause

set PYTHON_PATH=py
set SCRIPT_PATH=%CD%\scheduled_jobs_runner.py

echo.
echo Creating scheduled tasks...
echo.

REM Daily Tasks
echo [1/8] Data Cleanup (Daily 1 AM)...
schtasks /create /tn "AlphaAlgo_DataCleanup" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now data_cleanup" /sc daily /st 01:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [2/8] Offline RL Training (Daily 2 AM)...
schtasks /create /tn "AlphaAlgo_OfflineRL" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now offline_rl" /sc daily /st 02:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [3/8] Neural Evolution (Daily 3 AM)...
schtasks /create /tn "AlphaAlgo_NeuralEvolution" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now neural_evolution" /sc daily /st 03:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [4/8] Performance Analysis (Daily 5 PM)...
schtasks /create /tn "AlphaAlgo_Performance" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now performance" /sc daily /st 17:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

REM Weekly Tasks
echo [5/8] Model Retraining (Saturday 2 AM)...
schtasks /create /tn "AlphaAlgo_ModelRetraining" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now model_retraining" /sc weekly /d SAT /st 02:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [6/8] Adversarial Testing (Sunday 3 AM)...
schtasks /create /tn "AlphaAlgo_AdversarialTest" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now adversarial" /sc weekly /d SUN /st 03:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [7/8] Pattern Discovery (Sunday 4 AM)...
schtasks /create /tn "AlphaAlgo_PatternDiscovery" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now pattern_discovery" /sc weekly /d SUN /st 04:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo [8/8] Strategy Optimization (Sunday 5 AM)...
schtasks /create /tn "AlphaAlgo_StrategyOptimization" /tr "%PYTHON_PATH% %SCRIPT_PATH% --run-now strategy_optimization" /sc weekly /d SUN /st 05:00 /f
if %errorlevel% neq 0 echo   FAILED - Run as Administrator

echo.
echo ======================================================
echo   SCHEDULED TASKS SETUP COMPLETE
echo ======================================================
echo.
echo To view scheduled tasks:
echo   schtasks /query /tn "AlphaAlgo_*"
echo.
echo To delete all tasks:
echo   schtasks /delete /tn "AlphaAlgo_DataCleanup" /f
echo   schtasks /delete /tn "AlphaAlgo_OfflineRL" /f
echo   schtasks /delete /tn "AlphaAlgo_NeuralEvolution" /f
echo   schtasks /delete /tn "AlphaAlgo_Performance" /f
echo   schtasks /delete /tn "AlphaAlgo_ModelRetraining" /f
echo   schtasks /delete /tn "AlphaAlgo_AdversarialTest" /f
echo   schtasks /delete /tn "AlphaAlgo_PatternDiscovery" /f
echo   schtasks /delete /tn "AlphaAlgo_StrategyOptimization" /f
echo.
pause
