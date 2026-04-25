#!/usr/bin/env python3
"""
Claude Code - Python implementation using Anthropic API
Uses API key: sk-fLNAsr6dAydWpQ-FioLJnQ
"""

import os
import sys
from anthropic import Anthropic

def main():
    # Set the API key
    api_key = "sk-fLNAsr6dAydWpQ-FioLJnQ"
    os.environ["ANTHROPIC_API_KEY"] = api_key
    
    client = Anthropic(api_key=api_key)
    
    # Get prompt from command line or interactive
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
    else:
        print("Claude Code - Usage: python claude_code.py <your prompt>")
        print("Example: python claude_code.py 'What is the meaning of life?'")
        sys.exit(1)
    
    print(f"Claude Code - Sending request...")
    print(f"Prompt: {prompt}")
    print("-" * 50)
    
    try:
        response = client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=4096,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        print(response.content[0].text)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
