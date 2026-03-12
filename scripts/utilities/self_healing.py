import shutil
import os
from datetime import datetime

BACKUP_DIR = 'code_backups/'

class SelfHealing:
    def backup(self, file_path):
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        backup_path = os.path.join(BACKUP_DIR, os.path.basename(file_path) + f'.bak_{datetime.now().strftime("%Y%m%d%H%M%S")}')
        shutil.copy2(file_path, backup_path)
        return backup_path

    def restore(self, file_path):
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith(os.path.basename(file_path))]
        if not backups:
            return None
        latest = sorted(backups)[-1]
        shutil.copy2(os.path.join(BACKUP_DIR, latest), file_path)
        return file_path

# Example usage:
if __name__ == '__main__':
    sh = SelfHealing()
    print('Backup:', sh.backup('main.py'))
    print('Restore:', sh.restore('main.py'))
