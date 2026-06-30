import os

filepath = 'trading_bot/elite_system/elite_system.py'
with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if 'PositionSizeMethod = None' in line:
        new_lines.append('    from .risk_command_center import PositionSizeMethod\n')
    elif 'PredictionHorizon = None' in line:
        new_lines.append('    from .ai_ml_cortex import PredictionHorizon\n')
    else:
        new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)
