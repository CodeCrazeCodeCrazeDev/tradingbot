@echo off
REM Complete System Integration Test
REM ===================================

echo.
echo ================================================================================
echo COMPLETE TRADING BOT INTEGRATION TEST
echo ================================================================================
echo.
echo Testing integration of all modules with Unicode/logging fixes...
echo.

py -c "from trading_bot.complete_integrator import quick_integrate; integrator, modules = quick_integrate(); status = integrator.get_status(); print('\n\n=== FINAL INTEGRATION STATUS ==='); print('Total Modules:', status['total_modules']); print('Successfully Integrated:', status['successful']); print('Failed:', status['failed']); print('Success Rate: {:.1f}%'.format(status['successful']/status['total_modules']*100))"

echo.
echo ================================================================================
echo Integration test complete!
echo ================================================================================
echo.
pause
