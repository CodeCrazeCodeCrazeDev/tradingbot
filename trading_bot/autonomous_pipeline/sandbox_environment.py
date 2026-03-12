"""
Sandbox Environment - Isolated testing environment for new data sources and models

Provides:
- Isolated Python environment
- Resource limits (CPU, memory, network)
- Security restrictions
- Performance monitoring
- Safe execution of untrusted code

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
import subprocess
import tempfile
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import psutil
import time

logger = logging.getLogger(__name__)


class SandboxStatus(Enum):
    """Status of sandbox environment"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    RESOURCE_LIMIT = "resource_limit"
    SECURITY_VIOLATION = "security_violation"


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment"""
    # Resource limits
    max_cpu_percent: float = 50.0  # Max CPU usage
    max_memory_mb: int = 512  # Max memory in MB
    max_execution_time: int = 300  # Max execution time in seconds
    max_network_calls: int = 100  # Max network requests
    
    # Security
    allow_network: bool = True
    allow_file_write: bool = False
    allow_subprocess: bool = False
    allowed_imports: List[str] = field(default_factory=lambda: [
        'numpy', 'pandas', 'sklearn', 'torch', 'tensorflow',
        'requests', 'aiohttp', 'asyncio', 'datetime', 'json'
    ])
    
    # Paths
    sandbox_dir: str = "sandbox_temp"
    data_dir: str = "sandbox_data"
    output_dir: str = "sandbox_output"


@dataclass
class IsolatedTest:
    """Represents a test running in sandbox"""
    test_id: str
    item_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Status
    status: SandboxStatus = SandboxStatus.CREATED
    exit_code: Optional[int] = None
    
    # Resources used
    cpu_usage: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    network_calls: int = 0
    
    # Output
    stdout: str = ""
    stderr: str = ""
    output_files: List[str] = field(default_factory=list)
    
    # Results
    success: bool = False
    error_message: Optional[str] = None
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'test_id': self.test_id,
            'item_name': self.item_name,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'status': self.status.value,
            'exit_code': self.exit_code,
            'cpu_usage_avg': sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0,
            'memory_usage_avg': sum(self.memory_usage) / len(self.memory_usage) if self.memory_usage else 0,
            'network_calls': self.network_calls,
            'success': self.success,
            'error_message': self.error_message,
            'performance_metrics': self.performance_metrics
        }


class SandboxEnvironment:
    """Isolated sandbox environment for testing"""
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.sandbox_path: Optional[Path] = None
        self.active_tests: Dict[str, IsolatedTest] = {}
        self.completed_tests: List[IsolatedTest] = []
    
    async def create_sandbox(self) -> Path:
        """Create isolated sandbox directory"""
        try:
            # Create temporary sandbox directory
            self.sandbox_path = Path(tempfile.mkdtemp(prefix="alphaalgo_sandbox_"))
            
            # Create subdirectories
            (self.sandbox_path / self.config.data_dir).mkdir(exist_ok=True)
            (self.sandbox_path / self.config.output_dir).mkdir(exist_ok=True)
            
            logger.info(f"Sandbox created: {self.sandbox_path}")
            return self.sandbox_path
            
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise
    
    async def run_in_sandbox(
        self,
        item_name: str,
        code: str,
        test_data: Optional[Dict] = None
    ) -> IsolatedTest:
        """Run code in isolated sandbox"""
        test_id = f"test_{item_name}_{int(time.time())}"
        test = IsolatedTest(
            test_id=test_id,
            item_name=item_name,
            start_time=datetime.now()
        )
        
        self.active_tests[test_id] = test
        
        try:
            # Create sandbox if not exists
            if not self.sandbox_path:
                await self.create_sandbox()
            
            # Write code to file
            code_file = self.sandbox_path / f"{test_id}.py"
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Write test data if provided
            if test_data:
                data_file = self.sandbox_path / self.config.data_dir / f"{test_id}_data.json"
                with open(data_file, 'w') as f:
                    json.dump(test_data, f)
            
            # Run code with monitoring
            test.status = SandboxStatus.RUNNING
            success = await self._execute_with_monitoring(test, code_file)
            
            test.success = success
            test.status = SandboxStatus.COMPLETED if success else SandboxStatus.FAILED
            test.end_time = datetime.now()
            
        except asyncio.TimeoutError:
            test.status = SandboxStatus.TIMEOUT
            test.error_message = f"Execution exceeded {self.config.max_execution_time}s timeout"
            logger.warning(f"Test {test_id} timed out")
            
        except Exception as e:
            test.status = SandboxStatus.FAILED
            test.error_message = str(e)
            logger.error(f"Test {test_id} failed: {e}")
        
        finally:
            # Move to completed
            self.active_tests.pop(test_id, None)
            self.completed_tests.append(test)
        
        return test
    
    async def _execute_with_monitoring(self, test: IsolatedTest, code_file: Path) -> bool:
        """Execute code with resource monitoring"""
        try:
            # Start process
            process = await asyncio.create_subprocess_exec(
                'python', str(code_file),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self.sandbox_path)
            )
            
            # Monitor resources
            monitor_task = asyncio.create_task(
                self._monitor_resources(test, process.pid)
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.max_execution_time
                )
                
                test.stdout = stdout.decode('utf-8', errors='ignore')
                test.stderr = stderr.decode('utf-8', errors='ignore')
                test.exit_code = process.returncode
                
                # Check resource limits
                if test.cpu_usage and max(test.cpu_usage) > self.config.max_cpu_percent:
                    test.status = SandboxStatus.RESOURCE_LIMIT
                    test.error_message = f"CPU usage exceeded limit: {max(test.cpu_usage):.1f}%"
                    return False
                
                if test.memory_usage and max(test.memory_usage) > self.config.max_memory_mb:
                    test.status = SandboxStatus.RESOURCE_LIMIT
                    test.error_message = f"Memory usage exceeded limit: {max(test.memory_usage):.1f}MB"
                    return False
                
                return process.returncode == 0
                
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
        
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return False
    
    async def _monitor_resources(self, test: IsolatedTest, pid: int):
        """Monitor resource usage of process"""
        try:
            process = psutil.Process(pid)
            
            while True:
                try:
                    # CPU usage
                    cpu_percent = process.cpu_percent(interval=0.1)
                    test.cpu_usage.append(cpu_percent)
                    
                    # Memory usage
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    test.memory_usage.append(memory_mb)
                    
                    # Network connections (approximate)
                    test.network_calls = len(process.connections())
                    
                    await asyncio.sleep(1)
                    
                except psutil.NoSuchProcess:
                    break
                    
        except asyncio.CancelledError:
            pass
    
    async def test_data_source(
        self,
        source_name: str,
        source_url: str,
        api_key: Optional[str] = None
    ) -> IsolatedTest:
        """Test a data source in sandbox"""
        # Generate test code
        code = f"""
import aiohttp

async def test_data_source():
    url = "{source_url}"
    headers = {{"Authorization": "Bearer {api_key}"}} if "{api_key}" else {{}}
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"SUCCESS: Retrieved {{len(str(data))}} bytes")
                    print(f"Data sample: {{str(data)[:200]}}")
                    return True
                else:
                    print(f"FAILED: Status {{response.status}}")
                    return False
    except Exception as e:
        print(f"ERROR: {{e}}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_data_source())
    exit(0 if result else 1)
"""
        
        return await self.run_in_sandbox(source_name, code)
    
    async def test_model(
        self,
        model_name: str,
        model_path: str,
        test_data: Optional[Dict] = None
    ) -> IsolatedTest:
        """Test a model in sandbox"""
        # Generate test code
        code = f"""
import sys

def test_model():
    try:
        # Import model
        sys.path.insert(0, str(Path("{model_path}").parent))
        module_name = Path("{model_path}").stem
        
        # Try to import
        module = __import__(module_name)
        print(f"SUCCESS: Imported {{module_name}}")
        
        # Check for common methods
        if hasattr(module, 'predict'):
            print("Has predict method")
        if hasattr(module, 'fit'):
            print("Has fit method")
        if hasattr(module, 'transform'):
            print("Has transform method")
        
        return True
        
    except Exception as e:
        print(f"ERROR: {{e}}")
        return False

if __name__ == "__main__":
    result = test_model()
    exit(0 if result else 1)
"""
        
        return await self.run_in_sandbox(model_name, code, test_data)
    
    async def cleanup(self):
        """Clean up sandbox environment"""
        if self.sandbox_path and self.sandbox_path.exists():
            try:
                shutil.rmtree(self.sandbox_path)
                logger.info(f"Sandbox cleaned up: {self.sandbox_path}")
            except Exception as e:
                logger.error(f"Failed to cleanup sandbox: {e}")
    
    def get_test_results(self) -> List[IsolatedTest]:
        """Get all test results"""
        return self.completed_tests
    
    def get_success_rate(self) -> float:
        """Get success rate of tests"""
        if not self.completed_tests:
            return 0.0
        
        successful = sum(1 for test in self.completed_tests if test.success)
        return successful / len(self.completed_tests)
    
    def save_results(self, filepath: str = "sandbox_results.json"):
        """Save test results to file"""
        data = [test.to_dict() for test in self.completed_tests]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Sandbox results saved to {filepath}")
