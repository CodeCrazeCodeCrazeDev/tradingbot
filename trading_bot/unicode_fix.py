"""
Unicode Encoding Fix for Windows
=================================

Comprehensive fix for UnicodeEncodeError on Windows systems.
This module ensures all output (stdout, stderr, logging) uses UTF-8 encoding.
"""

import sys
import os
import logging
from pathlib import Path


def apply_unicode_fix():
    """Apply comprehensive Unicode encoding fix for Windows"""
    
    if sys.platform == 'win32':
        # Set environment variables
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        os.environ['PYTHONUTF8'] = '1'
        
        # Reconfigure stdout and stderr
        if hasattr(sys.stdout, 'reconfigure'):
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
        
        if hasattr(sys.stderr, 'reconfigure'):
            try:
                sys.stderr.reconfigure(encoding='utf-8', errors='replace')
            except Exception:
                pass
        
        # Fix existing logging handlers
        for handler in logging.root.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                if hasattr(handler.stream, 'reconfigure'):
                    try:
                        handler.stream.reconfigure(encoding='utf-8', errors='replace')
                    except Exception:
                        pass
        
        # Set default encoding for file operations
        import locale
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
        except:
            try:
                locale.setlocale(locale.LC_ALL, 'C.UTF-8')
            except:
                pass


def setup_utf8_logging(log_dir: str = 'logs'):
    """Setup UTF-8 safe logging configuration"""
    
    # Create log directory
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Remove existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create UTF-8 safe handlers
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    file_handler = logging.FileHandler(
        log_path / 'trading_bot.log',
        encoding='utf-8',
        mode='a',
        errors='replace'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Configure root logger
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(console_handler)
    logging.root.addHandler(file_handler)


def safe_print(*args, **kwargs):
    """UTF-8 safe print function"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode to ASCII with replacement
        safe_args = []
        for arg in args:
            if isinstance(arg, str):
                safe_args.append(arg.encode('ascii', errors='replace').decode('ascii'))
            else:
                safe_args.append(str(arg))
        print(*safe_args, **kwargs)


def safe_log(logger_instance, level, message, *args, **kwargs):
    """UTF-8 safe logging function"""
    try:
        getattr(logger_instance, level)(message, *args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: encode message to ASCII
        safe_message = message.encode('ascii', errors='replace').decode('ascii')
        getattr(logger_instance, level)(safe_message, *args, **kwargs)


# Apply fix on import
apply_unicode_fix()


if __name__ == "__main__":
    # Test the fix
    apply_unicode_fix()
    setup_utf8_logging()
    
    print("Unicode fix applied successfully!")
    print("Testing special characters: ✓ ✗ → ← ↑ ↓ ★ ☆ ♠ ♣ ♥ ♦")
    
    logging.info("Unicode fix test: ✓ Success")
    logging.warning("Testing emoji: 🚀 📊 💰 ⚠️")
    
    print("\nAll Unicode tests passed!")
