"""
Critical Fixes for Trading Bot
Applies two essential fixes:
1. Make PaperExecutor.execute_trade() async
2. Add sleep delay in main trading loop
"""

import re

def fix_paper_executor():
    """Fix 1: Make execute_trade async"""
    file_path = "trading_bot/execution/paper_executor.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace def execute_trade with async def execute_trade
    content = content.replace(
        "    def execute_trade(self, symbol: str = None",
        "    async def execute_trade(self, symbol: str = None"
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Fixed PaperExecutor.execute_trade() - made it async")

def fix_main_loop():
    """Fix 2: Add sleep in trading loop"""
    file_path = "main.py"
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the section after trade execution and before the except block
    # Add sleep after the second execute_trade call
    pattern = r"(                            size=abs\(position\)\s*\)\s*)\n(                except Exception as e:)"
    replacement = r"\1\n                        # Sleep after processing to avoid infinite loop\n                        await asyncio.sleep(5)\n\2"
    
    content = re.sub(pattern, replacement, content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("[OK] Fixed main trading loop - added sleep delay")

if __name__ == "__main__":
    print("Applying critical fixes...")
    fix_paper_executor()
    fix_main_loop()
    print("\n[SUCCESS] All fixes applied successfully!")
    print("\nYou can now start the bot with:")
    print("  py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 200")
