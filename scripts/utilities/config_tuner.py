import yaml
import os

class ConfigTuner:
    def __init__(self, config_path='config/config.yaml'):
        self.config_path = config_path

    def tune(self, param, value):
        with open(self.config_path) as f:
            cfg = yaml.safe_load(f)
        cfg[param] = value
        with open(self.config_path, 'w') as f:
            yaml.safe_dump(cfg, f)
        print(f'Set {param} to {value}')

# Example usage:
if __name__ == '__main__':
    ct = ConfigTuner()
    ct.tune('max_positions', 2)
