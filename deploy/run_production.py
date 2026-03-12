#!/usr/bin/env python
"""Production launcher for AlphaAlgo Trading Bot"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    from trading_bot.main import main
    main()
