import psutil
import time

RAM_THRESHOLD_MB = 1024
CPU_THRESHOLD = 90

class ResourceAlerts:
    def check(self):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        alerts = []
        if mem.available / (1024**2) < RAM_THRESHOLD_MB:
            alerts.append(f'Low RAM: {mem.available/1024**2:.1f} MB')
        if cpu > CPU_THRESHOLD:
            alerts.append(f'High CPU: {cpu}%')
        return alerts

# Example usage:
if __name__ == '__main__':
    ra = ResourceAlerts()
    print('Alerts:', ra.check())
