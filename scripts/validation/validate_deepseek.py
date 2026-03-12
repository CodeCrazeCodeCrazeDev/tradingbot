"""
DeepSeek Integration Validation Script
Validates that the DeepSeek AI Engineer is properly configured and running.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header():
    """Print validation header"""
    print(f"""
{Colors.CYAN}================================================================================
                                                                              
              DeepSeek Integration Validation                           
                                                                              
                    AlphaAlgo AI Trading Bot System                           
                                                                              
================================================================================{Colors.RESET}
""")


def check_result(name: str, passed: bool, message: str = ""):
    """Print check result"""
    status = f"{Colors.GREEN}[PASS]{Colors.RESET}" if passed else f"{Colors.RED}[FAIL]{Colors.RESET}"
    print(f"  {status} {name}")
    if message and not passed:
        print(f"       {Colors.YELLOW}-> {message}{Colors.RESET}")
    return passed


def check_imports():
    """Check if all required imports work"""
    print(f"\n{Colors.BOLD}[*] Checking Module Imports...{Colors.RESET}")
    
    all_passed = True
    
    # Check core imports
    try:
        from trading_bot.ai_engineer import (
            DeepSeekConfig,
            DeepSeekInferenceClient,
            DeepSeekEngineer,
            InferenceBackend,
            TaskType,
            EngineeringTask,
            CodeChange
        )
        all_passed &= check_result("Core DeepSeek Integration", True)
    except ImportError as e:
        all_passed &= check_result("Core DeepSeek Integration", False, str(e))
    
    # Check orchestrator imports
    try:
        from trading_bot.ai_engineer import (
            AutonomousOrchestrator,
            CyclePhase,
            Priority,
            WindsurfContext,
            AuditResult
        )
        all_passed &= check_result("Autonomous Orchestrator", True)
    except ImportError as e:
        all_passed &= check_result("Autonomous Orchestrator", False, str(e))
    
    # Check safeguards imports
    try:
        from trading_bot.ai_engineer import (
            SafeguardSystem,
            SandboxMode,
            ChangeMonitor,
            ComplianceAuditor,
            IntegratedSafeguardSystem,
            SafeDeepSeekEngineer,
            ChangeRiskLevel,
            ApprovalStatus,
            RoleBasedAccessControl,
            VersionCheckpoint,
            ContainerizedEnvironment,
            BranchIsolation
        )
        all_passed &= check_result("Safeguards System", True)
    except ImportError as e:
        all_passed &= check_result("Safeguards System", False, str(e))
    
    # Check aiohttp
    try:
        import aiohttp
        all_passed &= check_result("aiohttp (async HTTP)", True)
    except ImportError as e:
        all_passed &= check_result("aiohttp (async HTTP)", False, "pip install aiohttp")
    
    # Check requests
    try:
        import requests
        all_passed &= check_result("requests (HTTP client)", True)
    except ImportError as e:
        all_passed &= check_result("requests (HTTP client)", False, "pip install requests")
    
    return all_passed


def check_inference_servers():
    """Check if any DeepSeek inference server is running"""
    print(f"\n{Colors.BOLD}[*] Checking Inference Servers...{Colors.RESET}")
    
    import requests
    
    servers = [
        ("Ollama", "http://localhost:11434/api/tags", "ollama serve"),
        ("LM Studio", "http://localhost:1234/v1/models", "Start LM Studio app"),
        ("TextGen WebUI", "http://localhost:5000/api/v1/model", "python server.py"),
        ("vLLM", "http://localhost:8000/v1/models", "vllm serve deepseek-coder-6.7b"),
    ]
    
    found_server = None
    
    for name, endpoint, start_cmd in servers:
        try:
            response = requests.get(endpoint, timeout=2)
            if response.status_code == 200:
                check_result(f"{name} Server", True)
                found_server = (name, endpoint)
                
                # Check for DeepSeek model
                try:
                    data = response.json()
                    models = []
                    if 'models' in data:
                        models = [m.get('name', m.get('id', '')) for m in data['models']]
                    elif isinstance(data, list):
                        models = [m.get('name', m.get('id', '')) for m in data]
                    
                    deepseek_found = any('deepseek' in str(m).lower() for m in models)
                    if deepseek_found:
                        check_result(f"  DeepSeek Model Loaded", True)
                    else:
                        check_result(f"  DeepSeek Model Loaded", False, 
                                   f"Available models: {models[:5]}...")
                except:
                    pass
            else:
                check_result(f"{name} Server", False, f"Status: {response.status_code}")
        except requests.exceptions.ConnectionError:
            check_result(f"{name} Server", False, f"Not running. Start with: {start_cmd}")
        except requests.exceptions.Timeout:
            check_result(f"{name} Server", False, "Connection timeout")
        except Exception as e:
            check_result(f"{name} Server", False, str(e))
    
    return found_server


def check_directories():
    """Check required directories exist"""
    print(f"\n{Colors.BOLD}[*] Checking Directories...{Colors.RESET}")
    
    all_passed = True
    
    dirs = [
        ("logs/deepseek", "DeepSeek logs"),
        ("logs/safeguards", "Safeguards logs"),
        ("alphaalgo_context", "Windsurf context"),
    ]
    
    for dir_path, desc in dirs:
        full_path = project_root / dir_path
        exists = full_path.exists()
        if not exists:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                all_passed &= check_result(f"{desc} ({dir_path})", True, "Created")
            except Exception as e:
                all_passed &= check_result(f"{desc} ({dir_path})", False, str(e))
        else:
            all_passed &= check_result(f"{desc} ({dir_path})", True)
    
    return all_passed


def check_configuration():
    """Check DeepSeek configuration"""
    print(f"\n{Colors.BOLD}[*] Checking Configuration...{Colors.RESET}")
    
    all_passed = True
    
    try:
        from trading_bot.ai_engineer import DeepSeekConfig, InferenceBackend
        
        # Test default config creation
        config = DeepSeekConfig()
        all_passed &= check_result("Default Config Creation", True)
        
        # Check config values
        all_passed &= check_result(f"Backend: {config.backend.value}", True)
        all_passed &= check_result(f"Endpoint: {config.endpoint}", True)
        all_passed &= check_result(f"Model: {config.model_name}", True)
        all_passed &= check_result(f"Temperature: {config.temperature}", True)
        all_passed &= check_result(f"Max Tokens: {config.max_tokens}", True)
        all_passed &= check_result(f"Sandbox Mode: {config.sandbox_mode}", True)
        
    except Exception as e:
        all_passed &= check_result("Configuration Check", False, str(e))
    
    return all_passed


async def test_inference_connection(endpoint: str):
    """Test actual inference connection"""
    print(f"\n{Colors.BOLD}[*] Testing Inference Connection...{Colors.RESET}")
    
    try:
        from trading_bot.ai_engineer import DeepSeekConfig, DeepSeekInferenceClient, InferenceBackend
        
        # Determine backend from endpoint
        if "11434" in endpoint:
            backend = InferenceBackend.OLLAMA
            api_endpoint = "http://localhost:11434/api/generate"
        elif "1234" in endpoint:
            backend = InferenceBackend.LM_STUDIO
            api_endpoint = "http://localhost:1234/v1/chat/completions"
        else:
            backend = InferenceBackend.OLLAMA
            api_endpoint = endpoint
        
        config = DeepSeekConfig(
            backend=backend,
            endpoint=api_endpoint,
            model_name="deepseek-coder:6.7b",
            temperature=0.2,
            max_tokens=100,
            timeout=30
        )
        
        async with DeepSeekInferenceClient(config) as client:
            # Simple test prompt
            response = await client.generate(
                prompt="Write a Python function that returns 'Hello, World!'",
                system_prompt="You are a helpful coding assistant. Respond with only code.",
                max_tokens=100
            )
            
            if response and response.get('text'):
                check_result("Inference Test", True)
                print(f"       {Colors.CYAN}Response preview: {response['text'][:100]}...{Colors.RESET}")
                return True
            else:
                check_result("Inference Test", False, "Empty response")
                return False
                
    except Exception as e:
        check_result("Inference Test", False, str(e))
        return False


def check_activation_script():
    """Check activation script exists and is valid"""
    print(f"\n{Colors.BOLD}[*] Checking Activation Script...{Colors.RESET}")
    
    script_path = project_root / "ACTIVATE_DEEPSEEK_ENGINEER.py"
    
    if script_path.exists():
        check_result("Activation Script Exists", True)
        
        # Check script is valid Python
        try:
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            compile(content, script_path, 'exec')
            check_result("Script Syntax Valid", True)
        except SyntaxError as e:
            check_result("Script Syntax Valid", False, str(e))
            return False
        
        return True
    else:
        check_result("Activation Script Exists", False, "ACTIVATE_DEEPSEEK_ENGINEER.py not found")
        return False


def print_summary(results: dict):
    """Print validation summary"""
    print(f"\n{Colors.BOLD}{'='*80}{Colors.RESET}")
    print(f"{Colors.BOLD}[*] VALIDATION SUMMARY{Colors.RESET}")
    print(f"{'='*80}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for name, result in results.items():
        status = f"{Colors.GREEN}[OK]{Colors.RESET}" if result else f"{Colors.RED}[X]{Colors.RESET}"
        print(f"  {status} {name}")
    
    print(f"\n{Colors.BOLD}Results: {passed}/{total} checks passed{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}[SUCCESS] All checks passed! DeepSeek is ready to use.{Colors.RESET}")
        print(f"\n{Colors.CYAN}To start DeepSeek Engineer:{Colors.RESET}")
        print(f"  python ACTIVATE_DEEPSEEK_ENGINEER.py")
    else:
        print(f"\n{Colors.YELLOW}[WARNING] {failed} check(s) failed. Please fix the issues above.{Colors.RESET}")
        
        if not results.get("Inference Server"):
            print(f"\n{Colors.CYAN}To start an inference server:{Colors.RESET}")
            print(f"  Option 1 (Ollama): ollama serve && ollama pull deepseek-coder:6.7b")
            print(f"  Option 2 (LM Studio): Download and start LM Studio, load deepseek-coder model")


async def main():
    """Main validation function"""
    print_header()
    
    results = {}
    
    # Run all checks
    results["Module Imports"] = check_imports()
    results["Directories"] = check_directories()
    results["Configuration"] = check_configuration()
    results["Activation Script"] = check_activation_script()
    
    # Check inference servers
    server_info = check_inference_servers()
    results["Inference Server"] = server_info is not None
    
    # Test inference if server found
    if server_info:
        name, endpoint = server_info
        results["Inference Test"] = await test_inference_connection(endpoint)
    
    # Print summary
    print_summary(results)
    
    return all(results.values())


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Validation cancelled.{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.RESET}")
        sys.exit(1)
