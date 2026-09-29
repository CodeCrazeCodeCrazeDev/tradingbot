"""
Install AlphaAlgo as Windows Service
Runs automatically on system startup
"""

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    _WIN32_AVAILABLE = True
except ImportError:  # pywin32 absent — service skeleton inert; guard still shows
    _WIN32_AVAILABLE = False
import socket
import sys
import asyncio
from pathlib import Path


if _WIN32_AVAILABLE:

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
            """Main service loop — DISABLED (quarantined parallel capital path)."""
            servicemanager.LogErrorMsg(
                "AlphaAlgoBot service is quarantined: fully_automated_system is a "
                "parallel trading loop outside the canonical runtime. Use "
                "main.py --mode paper."
            )

else:
    AlphaAlgoService = None


if __name__ == '__main__':
    raise SystemExit(
        "install_service.py is QUARANTINED: installing an auto-start Windows "
        "service that runs a parallel trading system is not a supported entry "
        "point. Use 'python main.py --mode paper'."
    )
