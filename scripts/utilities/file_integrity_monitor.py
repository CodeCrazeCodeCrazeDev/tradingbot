import hashlib
import os
import json
from datetime import datetime

INTEGRITY_DB = 'file_integrity.json'
MONITORED_FILES = [
    'main.py',
    'system_supervisor.py',
    'config/config.yaml',
    'requirements.txt'
]

class FileIntegrityMonitor:
    def __init__(self, files=MONITORED_FILES, db=INTEGRITY_DB):
        self.files = files
        self.db = db
        self.hashes = self.load_hashes()

    def hash_file(self, path):
        if not os.path.exists(path):
            return None
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def load_hashes(self):
        if os.path.exists(self.db):
            with open(self.db) as f:
                return json.load(f)
        return {}

    def save_hashes(self):
        with open(self.db, 'w') as f:
            json.dump(self.hashes, f, indent=2)

    def verify(self):
        tampered = []
        for file in self.files:
            hash_now = self.hash_file(file)
            if file in self.hashes and self.hashes[file] != hash_now:
                tampered.append(file)
        return tampered

    def update(self):
        for file in self.files:
            hash_now = self.hash_file(file)
            if hash_now:
                self.hashes[file] = hash_now
        self.save_hashes()

# Example usage:
if __name__ == '__main__':
    fim = FileIntegrityMonitor()
    tampered = fim.verify()
    if tampered:
        print('Tampered files:', tampered)
    else:
        print('All files OK')
    fim.update()
