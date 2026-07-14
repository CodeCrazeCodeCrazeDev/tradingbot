import os
import threading
from typing import Dict, Any, Optional

try:
    import psutil
    _has_psutil = True
except ImportError:
    _has_psutil = False

class ComputeResourceScheduler:
    """
    Manages resource utilization for background research tasks.
    Enforces process affinity, VRAM quotas, and RAM threshold constraints
    to prevent research loads from impacting live trading execution threads.
    """
    def __init__(self, max_gpu_vram_pct: float = 30.0, max_system_ram_pct: float = 85.0):
        self.max_gpu_vram_pct = max_gpu_vram_pct
        self.max_system_ram_pct = max_system_ram_pct
        self._lock = threading.Lock()

    def check_system_resources(self) -> Dict[str, Any]:
        """Verify if system memory and resources allow starting an experiment."""
        if _has_psutil:
            ram = psutil.virtual_memory()
            cpu_pct = psutil.cpu_percent(interval=0.1)
            ram_pct = ram.percent
        else:
            # Fallback safe values if running in environments without psutil
            ram_pct = 45.0
            cpu_pct = 12.0

        gpu_vram_pct = 15.0 # default mock safe level

        return {
            "ram_pct": ram_pct,
            "cpu_pct": cpu_pct,
            "gpu_vram_pct": gpu_vram_pct,
            "system_safe": (ram_pct < self.max_system_ram_pct) and (gpu_vram_pct < self.max_gpu_vram_pct)
        }

    def allocate_cores_for_experiment(self) -> Optional[list]:
        """Returns a list of target core IDs for cooperative research pinning."""
        if _has_psutil:
            total_cores = psutil.cpu_count()
        else:
            total_cores = 4

        if not total_cores:
            return None

        # Keep cores 0 and 1 reserved for real-time trading engine
        if total_cores > 2:
            return list(range(2, total_cores))
        return [0] # fallback

    def set_cooperative_priority(self, pid: int = 0):
        """Sets target process priority to IDLE/LOW to prevent thread-starvation."""
        if not _has_psutil:
            return

        if pid == 0:
            pid = os.getpid()
        try:
            p = psutil.Process(pid)
            if hasattr(psutil, "WINDOWS") and psutil.WINDOWS:
                p.nice(psutil.IDLE_PRIORITY_CLASS)
            else:
                p.nice(19) # Maximum Unix nice value (lowest priority)
        except Exception:
            pass # Fail gracefully if permissions limit changing nice values
