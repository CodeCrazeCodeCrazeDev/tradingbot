#!/usr/bin/env python3
"""Fix indentation in reporter.py"""

file_path = r'c:\Users\peterson\trading bot\trading_bot\reporting\reporter.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Fix the indentation issue in daily_report
# Lines 80-94 have extra indentation
for i in range(79, min(95, len(lines))):
    if lines[i].startswith('                '):
        # Remove 4 spaces
        lines[i] = lines[i][4:]

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[DONE] Fixed reporter.py indentation")
