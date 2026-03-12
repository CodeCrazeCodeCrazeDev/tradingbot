import time
import os
from datetime import datetime, timedelta

SAFE_MODE_FLAG = 'SAFE_MODE_ON.flag'
CRASH_WINDOW_MINUTES = 60
CRASH_THRESHOLD = 3

class AdaptiveRestartPolicy:
    def __init__(self, crash_log='bot_crash_log.txt'):
        self.crash_log = crash_log

    def recent_crash_count(self):
        now = datetime.now()
        count = 0
        if not os.path.exists(self.crash_log):
            return 0
        with open(self.crash_log) as f:
            for line in f:
                if 'Crash' in line or 'CRASH' in line:
                    try:
                        ts = datetime.fromisoformat(line.split('|')[0].strip())
                        if now - ts < timedelta(minutes=CRASH_WINDOW_MINUTES):
                            count += 1
                    except Exception:
                        continue
        return count

    def check_and_activate_safe_mode(self):
        count = self.recent_crash_count()
        if count >= CRASH_THRESHOLD:
            with open(SAFE_MODE_FLAG, 'w') as f:
                f.write(f'Safe mode activated at {datetime.now().isoformat()} due to {count} crashes in {CRASH_WINDOW_MINUTES}min\n')
            print('SAFE MODE ACTIVATED')
            return True
        return False

    def is_safe_mode(self):
        return os.path.exists(SAFE_MODE_FLAG)

    def clear_safe_mode(self):
        if os.path.exists(SAFE_MODE_FLAG):
            os.remove(SAFE_MODE_FLAG)

# Example usage:
if __name__ == '__main__':
    policy = AdaptiveRestartPolicy()
    if policy.check_and_activate_safe_mode():
        print('Bot should run in safe mode!')
    else:
        print('Normal mode.')
