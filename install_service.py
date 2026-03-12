"""
Install AlphaAlgo as Windows Service
Runs automatically on system startup
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import asyncio
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from fully_automated_system import AutomatedAlphaAlgo


class AlphaAlgoService(win32serviceutil.ServiceFramework):
    _svc_name_ = "AlphaAlgoBot"
    _svc_display_name_ = "AlphaAlgo Automated Trading Bot"
    _svc_description_ = "Fully automated trading bot that manages deployment, testing, and live trading"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        socket.setdefaulttimeout(60)
    
    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
    
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
    
    def main(self):
        """Main service loop"""
        try:
            system = AutomatedAlphaAlgo()
            asyncio.run(system.run_forever())
        except Exception as e:
            servicemanager.LogErrorMsg(f"Service error: {str(e)}")


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(AlphaAlgoService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(AlphaAlgoService)
