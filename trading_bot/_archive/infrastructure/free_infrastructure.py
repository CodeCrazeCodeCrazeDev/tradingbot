"""
Free Infrastructure System ($0 Budget)
Uses free hosting, open-source tools, and local deployment
"""

import time
import json
import psutil  # Free system monitoring
import socket
from typing import Dict, List, Set
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class FreeDeploymentTarget(Enum):
    """Free deployment options"""
    LOCAL = "local"  # Run on your PC
    HEROKU_FREE = "heroku_free"  # Free tier (deprecated but alternatives exist)
    RAILWAY_FREE = "railway_free"  # $5 free credit monthly
    RENDER_FREE = "render_free"  # Free tier
    VERCEL_FREE = "vercel_free"  # Free for hobby projects


@dataclass
class SystemHealth:
    """System health metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    network_latency: float
    status: str


class FreeSystemMonitor:
    """Free system monitoring using psutil"""
    
    def __init__(self):
        self.history: List[SystemHealth] = []
        
    def check_health(self) -> SystemHealth:
        """Check system health (free)"""
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        
        # Network latency (ping localhost)
        start = time.time()
        try:
            socket.create_connection(('localhost', 80), timeout=1)
            latency = (time.time() - start) * 1000  # ms
        except Exception:
            latency = 999  # Failed
        
        # Determine status
        if cpu_percent > 90 or memory_percent > 90 or disk_percent > 90:
            status = 'critical'
        elif cpu_percent > 70 or memory_percent > 70 or disk_percent > 70:
            status = 'warning'
        else:
            status = 'healthy'
        
        health = SystemHealth(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            disk_percent=disk_percent,
            network_latency=latency,
            status=status
        )
        
        self.history.append(health)
        return health
    
    def get_health_report(self) -> Dict:
        """Get health report"""
        
        if not self.history:
            return {}
        
        recent = self.history[-10:]  # Last 10 checks
        
        return {
            'current': self.history[-1],
            'avg_cpu': sum(h.cpu_percent for h in recent) / len(recent),
            'avg_memory': sum(h.memory_percent for h in recent) / len(recent),
            'avg_latency': sum(h.network_latency for h in recent) / len(recent),
            'num_checks': len(self.history)
        }


class FreeAutoScaler:
    """Free auto-scaling using process management"""
    
    def __init__(self):
        self.max_workers = psutil.cpu_count()  # Use all CPU cores
        self.current_workers = 1
        
    def scale_decision(self, cpu_percent: float, memory_percent: float) -> Dict:
        """Decide if scaling is needed"""
        
        if cpu_percent > 80 and self.current_workers < self.max_workers:
            # Scale up
            new_workers = min(self.current_workers + 1, self.max_workers)
            action = 'scale_up'
        elif cpu_percent < 30 and self.current_workers > 1:
            # Scale down
            new_workers = max(self.current_workers - 1, 1)
            action = 'scale_down'
        else:
            new_workers = self.current_workers
            action = 'no_change'
        
        self.current_workers = new_workers
        
        return {
            'action': action,
            'current_workers': self.current_workers,
            'max_workers': self.max_workers,
            'cpu_percent': cpu_percent,
            'cost': 0  # Free
        }


class FreeCacheManager:
    """Free caching using Python dict (in-memory)"""
    
    def __init__(self, max_size: int = 1000):
        self.cache: Dict = {}
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        
    def get(self, key: str):
        """Get from cache"""
        if key in self.cache:
            self.hits += 1
            return self.cache[key]
        self.misses += 1
        return None
    
    def set(self, key: str, value):
        """Set in cache"""
        if len(self.cache) >= self.max_size:
            # Remove oldest (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = {
            'value': value,
            'timestamp': datetime.now()
        }
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': hit_rate,
            'cost': 0  # Free
        }


class FreeLoadBalancer:
    """Free load balancing using round-robin"""
    
    def __init__(self):
        self.workers = []
        self.current_index = 0
        
    def add_worker(self, worker_id: str):
        """Add worker"""
        self.workers.append({
            'id': worker_id,
            'requests': 0,
            'status': 'active'
        })
    
    def get_next_worker(self) -> str:
        """Get next worker (round-robin)"""
        if not self.workers:
            return 'default'
        
        # Round-robin
        worker = self.workers[self.current_index]
        worker['requests'] += 1
        
        self.current_index = (self.current_index + 1) % len(self.workers)
        
        return worker['id']
    
    def get_stats(self) -> Dict:
        """Get load balancer stats"""
        return {
            'total_workers': len(self.workers),
            'workers': self.workers,
            'algorithm': 'round_robin',
            'cost': 0  # Free
        }


class FreeBackupManager:
    """Free backup using local filesystem"""
    
    def __init__(self, backup_dir: str = './backups'):
        self.backup_dir = backup_dir
        self.backups: List[Dict] = []
        
    def create_backup(self, data: Dict, name: str) -> str:
        """Create backup (free)"""
        
        import os
        
        # Create backup directory if not exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Create backup file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{name}_{timestamp}.json"
        filepath = os.path.join(self.backup_dir, filename)
        
        # Save data
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        backup_info = {
            'name': name,
            'filename': filename,
            'filepath': filepath,
            'timestamp': datetime.now(),
            'size_bytes': os.path.getsize(filepath)
        }
        
        self.backups.append(backup_info)
        
        return filepath
    
    def list_backups(self) -> List[Dict]:
        """List all backups"""
        return self.backups
    
    def restore_backup(self, filepath: str) -> Dict:
        """Restore from backup"""
        
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        return data


class FreeInfrastructure:
    """Free unified infrastructure system"""
    
    def __init__(self):
        self.monitor = FreeSystemMonitor()
        self.scaler = FreeAutoScaler()
        self.cache = FreeCacheManager()
        self.load_balancer = FreeLoadBalancer()
        self.backup_manager = FreeBackupManager()
        
        # Initialize workers
        for i in range(psutil.cpu_count()):
            self.load_balancer.add_worker(f"worker_{i}")
        
    def health_check(self) -> Dict:
        """Comprehensive health check"""
        
        # System health
        health = self.monitor.check_health()
        
        # Scaling decision
        scaling = self.scaler.scale_decision(
            health.cpu_percent,
            health.memory_percent
        )
        
        # Cache stats
        cache_stats = self.cache.get_stats()
        
        # Load balancer stats
        lb_stats = self.load_balancer.get_stats()
        
        return {
            'system_health': {
                'cpu': health.cpu_percent,
                'memory': health.memory_percent,
                'disk': health.disk_percent,
                'latency': health.network_latency,
                'status': health.status
            },
            'scaling': scaling,
            'cache': cache_stats,
            'load_balancer': lb_stats,
            'cost': 0,  # $0 budget
            'timestamp': datetime.now()
        }
    
    def deploy_strategy(self, strategy_code: str, target: str = 'local') -> Dict:
        """Deploy strategy (free)"""
        
        deployment_info = {
            'target': target,
            'status': 'deployed',
            'timestamp': datetime.now(),
            'cost': 0
        }
        
        if target == 'local':
            deployment_info['url'] = 'http://localhost:8000'
            deployment_info['instructions'] = [
                'Run: python main.py',
                'Access: http://localhost:8000',
                'Cost: $0 (runs on your PC)'
            ]
        
        elif target == 'railway_free':
            deployment_info['url'] = 'https://your-app.railway.app'
            deployment_info['instructions'] = [
                '1. Sign up at railway.app (free)',
                '2. Connect GitHub repo',
                '3. Deploy with one click',
                '4. Get $5 free credit monthly'
            ]
        
        elif target == 'render_free':
            deployment_info['url'] = 'https://your-app.onrender.com'
            deployment_info['instructions'] = [
                '1. Sign up at render.com (free)',
                '2. Connect GitHub repo',
                '3. Free tier: 750 hours/month',
                '4. Auto-sleep after 15min inactivity'
            ]
        
        elif target == 'vercel_free':
            deployment_info['url'] = 'https://your-app.vercel.app'
            deployment_info['instructions'] = [
                '1. Sign up at vercel.com (free)',
                '2. Import GitHub repo',
                '3. Free for hobby projects',
                '4. Unlimited bandwidth'
            ]
        
        return deployment_info
    
    def create_system_backup(self, data: Dict) -> str:
        """Create system backup"""
        return self.backup_manager.create_backup(data, 'system_state')


# Example usage
if __name__ == '__main__':
    # Initialize free infrastructure
    infra = FreeInfrastructure()
    
    # Health check
    health = infra.health_check()
    
    print("Free Infrastructure Status:")
    print(f"\nSystem Health:")
    print(f"  CPU: {health['system_health']['cpu']:.1f}%")
    print(f"  Memory: {health['system_health']['memory']:.1f}%")
    print(f"  Disk: {health['system_health']['disk']:.1f}%")
    print(f"  Status: {health['system_health']['status']}")
    
    print(f"\nScaling:")
    print(f"  Workers: {health['scaling']['current_workers']}/{health['scaling']['max_workers']}")
    print(f"  Action: {health['scaling']['action']}")
    
    print(f"\nCache:")
    print(f"  Hit Rate: {health['cache']['hit_rate']:.1%}")
    print(f"  Size: {health['cache']['size']}/{health['cache']['max_size']}")
    
    print(f"\nLoad Balancer:")
    print(f"  Workers: {health['load_balancer']['total_workers']}")
    print(f"  Algorithm: {health['load_balancer']['algorithm']}")
    
    print(f"\nTotal Cost: ${health['cost']}")
    
    # Deploy strategy
    print("\n" + "="*60)
    print("Deployment Options:")
    
    for target in ['local', 'railway_free', 'render_free', 'vercel_free']:
        deployment = infra.deploy_strategy('strategy_code', target)
        print(f"\n{target.upper()}:")
        print(f"  URL: {deployment['url']}")
        print(f"  Cost: ${deployment['cost']}")
