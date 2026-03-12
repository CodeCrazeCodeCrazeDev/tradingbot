import subprocess
import time
import psutil

SUPERVISOR_CMD = ['py', 'system_supervisor.py']

class WatchdogProcess:
    def __init__(self):
        self.proc = None

    def start_supervisor(self):
        self.proc = subprocess.Popen(SUPERVISOR_CMD, encoding='utf-8')
        print(f'Started supervisor with PID {self.proc.pid}')

    def monitor(self):
        while True:
            if self.proc.poll() is not None:
                print('Supervisor crashed! Restarting...')
                self.start_supervisor()
            time.sleep(10)

# Example usage:
if __name__ == '__main__':
    wd = WatchdogProcess()
    wd.start_supervisor()
    wd.monitor()
