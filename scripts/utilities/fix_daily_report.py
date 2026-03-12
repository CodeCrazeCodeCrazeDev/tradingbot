import logging
#!/usr/bin/env python3
"""Fix the daily_report TODO in reporter.py"""

import re

logger = logging.getLogger(__name__)


file_path = r'c:\Users\peterson\trading bot\trading_bot\reporting\reporter.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the daily_report method
pattern = r'(    def daily_report\(self\) -> None:  # noqa: D401\n        now = _dt\.datetime\.utcnow\(\)\n        file = self\.log_dir / f"daily_{now:%Y%m%d}\.txt"\n)        with file\.open\("w", encoding="utf-8"\) as fh:\n            fh\.write\(f"Daily Report – {now:%Y-%m-%d UTC}\\n"\)\n            fh\.write\("TODO: aggregate today\'s trades and performance metrics\.\\n"\)\n        logger\.success\("Daily report saved: {}", file\)'

replacement = r'''\1        try:
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Daily Report – {now:%Y-%m-%d UTC}\n")
                fh.write("="*50 + "\n\n")
                trades = self._get_daily_trades(now.date())
                fh.write(f"Total Trades: {len(trades)}\n")
                if trades:
                    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
                    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]
                    fh.write(f"Winning Trades: {len(winning_trades)}\n")
                    fh.write(f"Losing Trades: {len(losing_trades)}\n")
                    fh.write(f"Win Rate: {len(winning_trades)/len(trades)*100:.1f}%\n\n")
                    total_pnl = sum(t.get('pnl', 0) for t in trades)
                    fh.write(f"Total P&L: {total_pnl:.2f}\n")
                    fh.write(f"Average Trade: {total_pnl/len(trades):.2f}\n")
                    fh.write(f"Best Trade: {max(t.get('pnl', 0) for t in trades):.2f}\n")
                    fh.write(f"Worst Trade: {min(t.get('pnl', 0) for t in trades):.2f}\n")
                else:
                    fh.write("No trades today.\n")
        except Exception as e:
            logger.error(f"Daily report generation failed: {e}")
            with file.open("w", encoding="utf-8") as fh:
                fh.write(f"Daily Report – {now:%Y-%m-%d UTC}\n")
                fh.write(f"Error: {e}\n")
        logger.success("Daily report saved: {}", file)'''

content = re.sub(pattern, replacement, content)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[DONE] Fixed daily_report TODO")
