import csv
import time
import os
from datetime import datetime, timedelta

UPTIME_LOG = 'uptime_history.csv'

class UptimeTracker:
    def __init__(self):
        self.session_start = datetime.now()
        self.last_crash = None
        self.status = 'STARTED'
        if not os.path.exists(UPTIME_LOG):
            with open(UPTIME_LOG, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp','event','uptime_minutes','crash_count'])

    def log_event(self, event, crash_count=0):
        uptime_minutes = (datetime.now() - self.session_start).total_seconds() / 60
        with open(UPTIME_LOG, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), event, f'{uptime_minutes:.2f}', crash_count])

    def mark_crash(self, crash_count):
        self.last_crash = datetime.now()
        self.status = 'CRASHED'
        self.log_event('CRASH', crash_count)

    def mark_restart(self, crash_count):
        self.session_start = datetime.now()
        self.status = 'RESTARTED'
        self.log_event('RESTART', crash_count)

    def mark_shutdown(self):
        self.status = 'STOPPED'
        self.log_event('STOP')

    def mark_healthy(self, crash_count):
        self.status = 'RUNNING'
        self.log_event('HEALTHY', crash_count)

# Example usage:
if __name__ == '__main__':
    tracker = UptimeTracker()
    tracker.mark_healthy(0)
    time.sleep(1)
    tracker.mark_crash(1)
    time.sleep(1)
    tracker.mark_restart(1)
    tracker.mark_shutdown()
