import psutil
import time
import json
from datetime import datetime

LOG = 'memory_leak_log.json'

class MemoryLeakDetector:
    def __init__(self):
        self.history = []

    def record(self):
        mem = psutil.virtual_memory()
        entry = {
            'timestamp': datetime.now().isoformat(),
            'used_mb': mem.used / (1024**2)
        }
        self.history.append(entry)
        with open(LOG, 'w') as f:
            json.dump(self.history, f, indent=2)

    def analyze(self):
        if len(self.history) < 2:
            return 'Not enough data.'
        diffs = [self.history[i]['used_mb'] - self.history[i-1]['used_mb'] for i in range(1, len(self.history))]
        if all(d > 0 for d in diffs):
            return 'Possible memory leak detected!'
        return 'No persistent leak detected.'

# Example usage:
if __name__ == '__main__':
    mld = MemoryLeakDetector()
    for _ in range(5):
        mld.record()
        time.sleep(1)
    print(mld.analyze())
