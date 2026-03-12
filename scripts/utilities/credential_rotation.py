import os
import secrets
from datetime import datetime

ENV_PATH = '.env'
ROTATION_LOG = 'credential_rotation.log'

class CredentialRotator:
    def __init__(self, env_path=ENV_PATH):
        self.env_path = env_path

    def rotate_api_key(self, key_name):
        new_key = secrets.token_hex(16)
        lines = []
        rotated = False
        with open(self.env_path) as f:
            for line in f:
                if line.startswith(f'{key_name}='):
                    lines.append(f'{key_name}={new_key}\n')
                    rotated = True
                else:
                    lines.append(line)
        if rotated:
            with open(self.env_path, 'w') as f:
                f.writelines(lines)
            with open(ROTATION_LOG, 'a') as log:
                log.write(f'{datetime.now().isoformat()} | Rotated {key_name}\n')
        return new_key if rotated else None

# Example usage:
if __name__ == '__main__':
    cr = CredentialRotator()
    print('New API Key:', cr.rotate_api_key('ALPHA_VANTAGE_KEY'))
