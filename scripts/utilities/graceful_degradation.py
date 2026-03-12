import psutil
import os

DASHBOARD_FLAG = 'DASHBOARD_DISABLED.flag'
ML_FLAG = 'ML_DISABLED.flag'
RAM_THRESHOLD_MB = 800
CPU_THRESHOLD = 90

class GracefulDegradation:
    def __init__(self):
        self.disabled = []

    def check_and_degrade(self):
        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        if mem.available / (1024**2) < RAM_THRESHOLD_MB:
            self.disable_dashboard()
            self.disable_ml()
        if cpu > CPU_THRESHOLD:
            self.disable_ml()
        return self.disabled

    def disable_dashboard(self):
        if not os.path.exists(DASHBOARD_FLAG):
            with open(DASHBOARD_FLAG, 'w') as f:
                f.write('Dashboard disabled due to low resources\n')
            self.disabled.append('dashboard')

    def disable_ml(self):
        if not os.path.exists(ML_FLAG):
            with open(ML_FLAG, 'w') as f:
                f.write('ML disabled due to low resources\n')
            self.disabled.append('ml')

    def is_dashboard_disabled(self):
        return os.path.exists(DASHBOARD_FLAG)

    def is_ml_disabled(self):
        return os.path.exists(ML_FLAG)

    def clear_flags(self):
        for flag in [DASHBOARD_FLAG, ML_FLAG]:
            if os.path.exists(flag):
                os.remove(flag)

# Example usage:
if __name__ == '__main__':
    gd = GracefulDegradation()
    print('Disabled:', gd.check_and_degrade())
