#!/usr/bin/env python3
"""Simple fix for daily_report TODO"""

file_path = r'c:\Users\peterson\trading bot\trading_bot\reporting\reporter.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find and fix the TODO line
for i, line in enumerate(lines):
    if 'TODO: aggregate today' in line:
        # Replace this line and add implementation
        indent = '                '
        new_lines = [
            indent + 'trades = self._get_daily_trades(now.date())\n',
            indent + 'fh.write(f"Total Trades: {len(trades)}\\n")\n',
            indent + 'if trades:\n',
            indent + '    winning_trades = [t for t in trades if t.get("pnl", 0) > 0]\n',
            indent + '    losing_trades = [t for t in trades if t.get("pnl", 0) < 0]\n',
            indent + '    fh.write(f"Winning Trades: {len(winning_trades)}\\n")\n',
            indent + '    fh.write(f"Losing Trades: {len(losing_trades)}\\n")\n',
            indent + '    fh.write(f"Win Rate: {len(winning_trades)/len(trades)*100:.1f}%\\n\\n")\n',
            indent + '    total_pnl = sum(t.get("pnl", 0) for t in trades)\n',
            indent + '    fh.write(f"Total P&L: {total_pnl:.2f}\\n")\n',
            indent + '    fh.write(f"Average Trade: {total_pnl/len(trades):.2f}\\n")\n',
            indent + '    fh.write(f"Best Trade: {max(t.get("pnl", 0) for t in trades):.2f}\\n")\n',
            indent + '    fh.write(f"Worst Trade: {min(t.get("pnl", 0) for t in trades):.2f}\\n")\n',
            indent + 'else:\n',
            indent + '    fh.write("No trades today.\\n")\n',
        ]
        lines[i:i+1] = new_lines
        break

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("[DONE] Fixed daily_report")
