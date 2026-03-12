import subprocess
import sys
from datetime import datetime

PATCH_LOG = 'patch_manager.log'

class AutoPatchManager:
    def update_packages(self):
        result = subprocess.run([sys.executable, '-m', 'pip', 'list', '--outdated'], capture_output=True, text=True)
        outdated = [line.split()[0] for line in result.stdout.splitlines()[2:] if line]
        for pkg in outdated:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', pkg])
            with open(PATCH_LOG, 'a') as log:
                log.write(f'{datetime.now().isoformat()} | Upgraded {pkg}\n')

# Example usage:
if __name__ == '__main__':
    apm = AutoPatchManager()
    apm.update_packages()
