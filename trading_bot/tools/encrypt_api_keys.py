#!/usr/bin/env python
"""
API Key Encryption Tool

This tool helps securely encrypt API keys for the Elite Trading Bot.
It prompts for API keys and saves them in an encrypted format.
"""

import json
import os
import sys
from pathlib import Path
import getpass
from cryptography.fernet import Fernet

# Add parent directory to path to allow importing from trading_bot
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))


def generate_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()


def load_or_create_key(key_file):
    """Load existing key or create a new one"""
    key_file = Path(key_file)
    
    if key_file.exists():
        print(f"Using existing encryption key from {key_file}")
        with open(key_file, 'rb') as f:
            key = f.read()
    else:
        print(f"Generating new encryption key at {key_file}")
        key = generate_key()
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Set secure permissions on Unix-like systems
        if os.name != 'nt':
            try:
                os.chmod(key_file, 0o600)  # Read/write for owner only
                print("Set secure permissions on key file")
            except Exception as e:
                print(f"Warning: Could not set secure permissions on key file: {e}")
    
    return key


def encrypt_value(cipher, value):
    """Encrypt a value using the cipher"""
    if not value:
        return ""
    return cipher.encrypt(value.encode()).decode()


def main():
    """Main function"""
    print("Elite Trading Bot - API Key Encryption Tool")
    print("===========================================")
    
    # Get configuration paths
    config_dir = Path("config")
    key_file = config_dir / "encryption.key"
    api_keys_file = config_dir / "api_keys.json"
    
    # Ensure config directory exists
    config_dir.mkdir(exist_ok=True)
    
    # Load or create encryption key
    key = load_or_create_key(key_file)
    cipher = Fernet(key)
    
    # Initialize API keys dictionary
    api_keys = {}
    
    # Load existing API keys if available
    if api_keys_file.exists():
        try:
            with open(api_keys_file, 'r') as f:
                api_keys = json.load(f)
            print(f"Loaded existing API keys from {api_keys_file}")
        except Exception as e:
            print(f"Error loading existing API keys: {e}")
            print("Starting with empty API keys")
    
    # Prompt for exchanges
    while True:
        print("\nAvailable exchanges:", ", ".join(api_keys.keys()) if api_keys else "None")
        exchange = input("\nEnter exchange name (or leave empty to finish): ").strip().lower()
        
        if not exchange:
            break
        
        if exchange not in api_keys:
            api_keys[exchange] = {"api_key": "", "api_secret": ""}
        
        # Prompt for API key and secret
        print(f"\nEntering credentials for {exchange.upper()}")
        api_key = getpass.getpass(f"API Key for {exchange} (leave empty to keep existing): ")
        api_secret = getpass.getpass(f"API Secret for {exchange} (leave empty to keep existing): ")
        
        # Update and encrypt values if provided
        if api_key:
            api_keys[exchange]["api_key"] = encrypt_value(cipher, api_key)
        
        if api_secret:
            api_keys[exchange]["api_secret"] = encrypt_value(cipher, api_secret)
    
    # Save API keys
    with open(api_keys_file, 'w') as f:
        json.dump(api_keys, f, indent=2)
    
    # Set secure permissions on Unix-like systems
    if os.name != 'nt':
        try:
            os.chmod(api_keys_file, 0o600)  # Read/write for owner only
            print(f"Set secure permissions on {api_keys_file}")
        except Exception as e:
            print(f"Warning: Could not set secure permissions on API keys file: {e}")
    
    print(f"\nAPI keys encrypted and saved to {api_keys_file}")
    print("Remember to keep your encryption key secure!")


if __name__ == "__main__":
    main()
