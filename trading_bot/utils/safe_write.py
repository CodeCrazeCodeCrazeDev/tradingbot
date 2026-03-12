"""
Safe file writing utility to prevent Unicode encoding errors.
"""

import sys
from pathlib import Path

import logging
from typing import Dict, List, Optional, Any, Tuple
logger = logging.getLogger(__name__)


def safe_write(filepath, content, mode='w'):
    """
    Safely write content to file with proper Unicode handling.
    
    Args:
        filepath: Path to file
        content: Content to write
        mode: File mode ('w' for write, 'a' for append)
    """
    try:
        with open(filepath, mode, encoding='utf-8', errors='replace') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.info(f"Error writing to {filepath}: {e}")
        try:
            safe_content = content.encode('ascii', 'replace').decode('ascii')
            with open(filepath, mode, encoding='ascii') as f:
                f.write(safe_content)
            return True
        except Exception as e2:
            logger.info(f"Fallback write also failed: {e2}")
            return False

def sanitize_text(text):
    """Remove or replace problematic Unicode characters."""
    replacements = {
        '\u2713': '[OK]',    # checkmark
        '\u274c': '[FAIL]',  # cross mark
        '\u26a0': '[WARN]',  # warning
        '\u2705': '[OK]',    # white checkmark
        '\u274e': '[X]',     # negative squared cross mark
    }
    
    for emoji, replacement in replacements.items():
        text = text.replace(emoji, replacement)
    
    return text
