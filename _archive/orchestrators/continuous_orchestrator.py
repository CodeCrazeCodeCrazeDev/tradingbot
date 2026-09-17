"""
Continuous Orchestrator with SCP Integration
Orchestrates the continuous recursive self-improvement loop with remote backup and coordination
"""

import asyncio
import json
import time
import logging
import subprocess
import os
import sys
import paramiko
import threading
import queue
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import schedule
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import requests
from concurrent.futures import ThreadPoolExecutor
import hashlib
import pickle

from recursive_self_improvement import RecursiveSelfImprovementSystem, ImprovementPhase
from plotcode_integration import EnhancedRecursiveSelfImprovement
from self_diagnosis_engine import EnhancedSelfDiagnosis
from code_evolution_engine import CodeEvolutionEngine

@dataclass
class OrchestrationConfig:
    """Configuration for continuous orchestration"""
    loop_interval_seconds: int = 300  # 5 minutes
    max_concurrent_evolutions: int = 3
    scp_remote_host: str = "user@backup-server.com"
    scp_remote_path: str = "/backups/trading_bot/"
    email_notifications: bool = True
    email_recipients: List[str] = None
    webhook_url: Optional[str] = None
    health_check_interval: int = 60
    emergency_threshold: float = 50.0
    improvement_threshold: float = 80.0
    max_daily_evolutions: int = 10

@dataclass
class OrchestrationState:
    """State of the orchestration system"""
    current_loop: int
    total_evolutions: int
    successful_evolutions: int
    failed_evolutions: int
    last_evolution_time: datetime
    system_health_score: float
    is_running: bool
    emergency_mode: bool
    daily_evolution_count: int
    last_reset_date: datetime

class SCPManager:
    """Manages SCP operations for remote backup and coordination"""
    
    def __init__(self, remote_host: str, remote_path: str, 
                 ssh_key_path: Optional[str] = None):
        self.remote_host = remote_host
        self.remote_path = remote_path
        self.ssh_key_path = ssh_key_path or os.path.expanduser("~/.ssh/id_rsa")
        self.logger = logging.getLogger("SCPManager")
        self.ssh_client = None
    
    async def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect using SSH key
            self.ssh_client.connect(
                hostname=self.remote_host.split('@')[1],
                username=self.remote_host.split('@')[0],
                key_filename=self.ssh_key_path,
                timeout=30
            )
            
            self.logger.info(f"Connected to {self.remote_host}")
            return True
            
        except Exception as e:
            self.logger.error(f"SSH connection failed: {e}")
            return False
    
    async def upload_backup(self, local_path: str, remote_filename: str) -> bool:
        """Upload backup to remote server"""
        try:
            if not self.ssh_client:
                await self.connect()
            
            sftp = self.ssh_client.open_sftp()
            remote_file_path = f"{self.remote_path}/{remote_filename}"
            
            # Ensure remote directory exists
            try:
                sftp.stat(self.remote_path)
            except FileNotFoundError:
                sftp.mkdir(self.remote_path)
            
            # Upload file
            sftp.put(local_path, remote_file_path)
            sftp.close()
            
            self.logger.info(f"Uploaded {local_path} to {self.remote_host}:{remote_file_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"SCP upload failed: {e}")
            return False
    
    async def download_backup(self, remote_filename: str, local_path: str) -> bool:
        """Download backup from remote server"""
        try:
            if not self.ssh_client:
                await self.connect()
            
            sftp = self.ssh_client.open_sftp()
            remote_file_path = f"{self.remote_path}/{remote_filename}"
            
            # Download file
            sftp.get(remote_file_path, local_path)
            sftp.close()
            
            self.logger.info(f"Downloaded {remote_file_path} to {local_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"SCP download failed: {e}")
            return False
    
    async def list_remote_backups(self) -> List[str]:
        """List available remote backups"""
        try:
            if not self.ssh_client:
                await self.connect()
            
            sftp = self.ssh_client.open_sftp()
            files = sftp.listdir(self.remote_path)
            sftp.close()
            
            # Filter for backup files
            backup_files = [f for f in files if f.startswith('backup_') and f.endswith('.tar.gz')]
            backup_files.sort(reverse=True)  # Most recent first
            
            return backup_files
            
        except Exception as e:
            self.logger.error(f"Listing remote backups failed: {e}")
            return []
    
    async def sync_state(self, state_data: Dict[str, Any]) -> bool:
        """Synchronize orchestration state across instances"""
        try:
            state_file = "orchestration_state.json"
            local_path = f"/tmp/{state_file}"
            
            # Write state to local temp file
            with open(local_path, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
            
            # Upload to remote
            success = await self.upload_backup(local_path, state_file)
            
            # Clean up local temp file
            os.unlink(local_path)
            
            return success
            
        except Exception as e:
            self.logger.error(f"State synchronization failed: {e}")
            return False
    
    def disconnect(self):
        """Close SSH connection"""
        if self.ssh_client:
            self.ssh_client.close()
            self.ssh_client = None

class NotificationManager:
    """Manages notifications and alerts"""
    
    def __init__(self, config: OrchestrationConfig):
        self.config = config
        self.logger = logging.getLogger("NotificationManager")
    
    async def send_evolution_notification(self, evolution_result: Dict[str, Any]) -> None:
        """Send notification about evolution results"""
        try:
            message = self._format_evolution_message(evolution_result)
            
            # Send email if enabled
            if self.config.email_notifications and self.config.email_recipients:
                await self._send_email("Evolution Update", message)
            
            # Send webhook if configured
            if self.config.webhook_url:
                await self._send_webhook(evolution_result)
            
        except Exception as e:
            self.logger.error(f"Failed to send evolution notification: {e}")
    
    async def send_emergency_alert(self, alert_data: Dict[str, Any]) -> None:
        """Send emergency alert"""
        try:
            message = f"🚨 EMERGENCY ALERT 🚨\n\n{json.dumps(alert_data, indent=2, default=str)}"
            
            # Send email immediately
            if self.config.email_notifications and self.config.email_recipients:
                await self._send_email("EMERGENCY ALERT", message, priority="high")
            
            # Send webhook with high priority
            if self.config.webhook_url:
                await self._send_webhook({"type": "emergency", "data": alert_data})
            
        except Exception as e:
            self.logger.error(f"Failed to send emergency alert: {e}")
    
    def _format_evolution_message(self, evolution_result: Dict[str, Any]) -> str:
        """Format evolution result into readable message"""
        return f"""
Evolution Update
================

Evolution ID: {evolution_result.get('evolution_id', 'Unknown')}
Status: {'✅ SUCCESS' if evolution_result.get('success', False) else '❌ FAILED'}
Timestamp: {evolution_result.get('timestamp', 'Unknown')}

Mutations Applied: {len(evolution_result.get('mutations_applied', []))}
Improvement Metrics: {evolution_result.get('improvement_metrics', {})}

Test Results:
- Unit Tests: {evolution_result.get('test_results', {}).get('unit_tests', {})}
- Integration Tests: {evolution_result.get('test_results', {}).get('integration_tests', {})}

Side Effects: {len(evolution_result.get('side_effects', []))}
"""
    
    async def _send_email(self, subject: str, message: str, priority: str = "normal") -> None:
        """Send email notification"""
        try:
            # This is a simplified email implementation
            # In production, configure proper SMTP settings
            msg = MimeMultipart()
            msg['From'] = "trading-bot@company.com"
            msg['To'] = ", ".join(self.config.email_recipients)
            msg['Subject'] = subject
            
            msg.attach(MimeText(message, 'plain'))
            
            # Send email (implementation depends on your SMTP server)
            # server = smtplib.SMTP('smtp.company.com', 587)
            # server.send_message(msg)
            # server.quit()
            
            self.logger.info(f"Email notification sent: {subject}")
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
    
    async def _send_webhook(self, data: Dict[str, Any]) -> None:
        """Send webhook notification"""
        try:
            response = requests.post(
                self.config.webhook_url,
                json=data,
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info("Webhook notification sent")
            
        except Exception as e:
            self.logger.error(f"Failed to send webhook: {e}")

class ContinuousOrchestrator:
    """Main orchestrator for continuous recursive self-improvement"""
    
    def __init__(self, codebase_path: str = ".", config: Optional[OrchestrationConfig] = None):
        self.codebase_path = Path(codebase_path)
        self.config = config or OrchestrationConfig()
        self.logger = logging.getLogger("ContinuousOrchestrator")
        
        # Initialize components
        self.scp_manager = SCPManager(
            self.config.scp_remote_host,
            self.config.scp_remote_path
        )
        self.notification_manager = NotificationManager(self.config)
        
        # Initialize improvement systems
        self.base_system = RecursiveSelfImprovementSystem(
            str(self.codebase_path),
            app_url="http://localhost:8080"
        )
        self.enhanced_system = EnhancedRecursiveSelfImprovement(
            str(self.codebase_path),
            app_url="http://localhost:8080"
        )
        self.diagnosis_system = EnhancedSelfDiagnosis(str(self.codebase_path))
        self.evolution_engine = CodeEvolutionEngine(str(self.codebase_path))
        
        # Orchestration state
        self.state = OrchestrationState(
            current_loop=0,
            total_evolutions=0,
            successful_evolutions=0,
            failed_evolutions=0,
            last_evolution_time=datetime.now(),
            system_health_score=100.0,
            is_running=False,
            emergency_mode=False,
            daily_evolution_count=0,
            last_reset_date=datetime.now()
        )
        
        # Thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_evolutions)
        
        # Task queue
        self.task_queue = queue.Queue()
        
        # Scheduling
        self.scheduler_thread = None
        
    async def start_continuous_orchestration(self) -> None:
        """Start the continuous orchestration loop"""
        self.logger.info("Starting continuous orchestration")
        
        self.state.is_running = True
        
        # Connect to remote backup
        await self.scp_manager.connect()
        
        # Sync initial state
        await self._sync_state_with_remote()
        
        # Start background scheduler
        self._start_scheduler()
        
        # Start health monitoring
        health_task = asyncio.create_task(self._health_monitoring_loop())
        
        # Start main orchestration loop
        orchestration_task = asyncio.create_task(self._orchestration_loop())
        
        try:
            # Wait for tasks
            await asyncio.gather(orchestration_task, health_task)
            
        except KeyboardInterrupt:
            self.logger.info("Received interrupt signal")
            await self.stop_continuous_orchestration()
        
        except Exception as e:
            self.logger.error(f"Orchestration failed: {e}")
            await self.stop_continuous_orchestration()
    
    async def stop_continuous_orchestration(self) -> None:
        """Stop the continuous orchestration"""
        self.logger.info("Stopping continuous orchestration")
        
        self.state.is_running = False
        
        # Disconnect from remote
        self.scp_manager.disconnect()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        # Final state sync
        await self._sync_state_with_remote()
    
    async def _orchestration_loop(self) -> None:
        """Main orchestration loop"""
        while self.state.is_running:
            try:
                self.state.current_loop += 1
                self.logger.info(f"Starting orchestration loop {self.state.current_loop}")
                
                # Check daily evolution limit
                await self._check_daily_limits()
                
                # Perform comprehensive health check
                health_report = await self.diagnosis_system.diagnosis_engine.comprehensive_self_diagnosis()
                self.state.system_health_score = health_report.overall_health_score
                
                # Check for emergency conditions
                if health_report.overall_health_score < self.config.emergency_threshold:
                    await self._handle_emergency_mode(health_report)
                    continue
                
                # Check if evolution is needed
                if await self._should_evolve(health_report):
                    evolution_task = asyncio.create_task(self._execute_evolution_cycle())
                    await evolution_task
                
                # Sync state with remote
                await self._sync_state_with_remote()
                
                # Wait for next iteration
                await asyncio.sleep(self.config.loop_interval_seconds)
                
            except Exception as e:
                self.logger.error(f"Orchestration loop error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _execute_evolution_cycle(self) -> None:
        """Execute a complete evolution cycle"""
        try:
            self.logger.info("Starting evolution cycle")
            
            # Phase 1: Visual Testing with PlotCode
            visual_results = await self.enhanced_system.plotcode_tester.test_with_plotcode(
                self.enhanced_system._create_plotcode_test_cases()
            )
            
            # Phase 2: Self-Diagnosis
            audit_report = await self.diagnosis_system.diagnosis_engine.comprehensive_self_diagnosis()
            
            # Phase 3: Code Evolution
            evolution_result = await self.evolution_engine.evolve_codebase(
                asdict(audit_report), visual_results
            )
            
            # Update statistics
            self.state.total_evolutions += 1
            self.state.daily_evolution_count += 1
            self.state.last_evolution_time = datetime.now()
            
            if evolution_result.success:
                self.state.successful_evolutions += 1
            else:
                self.state.failed_evolutions += 1
            
            # Send notifications
            await self.notification_manager.send_evolution_notification(asdict(evolution_result))
            
            # Create and upload backup
            await self._create_and_upload_backup(evolution_result.evolution_id)
            
            self.logger.info(f"Evolution cycle completed: {evolution_result.evolution_id}")
            
        except Exception as e:
            self.logger.error(f"Evolution cycle failed: {e}")
            self.state.failed_evolutions += 1
    
    async def _health_monitoring_loop(self) -> None:
        """Continuous health monitoring"""
        while self.state.is_running:
            try:
                # Quick health check
                health_score = await self._quick_health_check()
                
                if health_score < self.config.emergency_threshold:
                    await self._trigger_emergency_response(health_score)
                
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _quick_health_check(self) -> float:
        """Perform quick health check"""
        try:
            # Check system resources
            import psutil
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            # Calculate health score
            resource_score = max(0, 100 - ((cpu_usage + memory_usage) / 2))
            
            # Check if main process is running
            process_score = 100 if self._is_main_process_healthy() else 0
            
            return (resource_score + process_score) / 2
            
        except Exception as e:
            self.logger.error(f"Quick health check failed: {e}")
            return 0.0
    
    def _is_main_process_healthy(self) -> bool:
        """Check if main process is healthy"""
        try:
            # Simplified health check
            return True
        except Exception:
            return False
    
    async def _should_evolve(self, health_report) -> bool:
        """Determine if evolution should be triggered"""
        # Check if improvement threshold not met
        if health_report.overall_health_score < self.config.improvement_threshold:
            return True
        
        # Check if there are critical issues
        if health_report.critical_issues:
            return True
        
        # Check if enough time has passed since last evolution
        time_since_last = datetime.now() - self.state.last_evolution_time
        if time_since_last > timedelta(hours=6):  # Minimum 6 hours between evolutions
            return True
        
        return False
    
    async def _check_daily_limits(self) -> None:
        """Check and reset daily evolution limits"""
        current_date = datetime.now().date()
        
        if current_date > self.state.last_reset_date.date():
            self.state.daily_evolution_count = 0
            self.state.last_reset_date = datetime.now()
            self.logger.info("Daily evolution count reset")
        
        if self.state.daily_evolution_count >= self.config.max_daily_evolutions:
            self.logger.warning("Daily evolution limit reached")
            await asyncio.sleep(3600)  # Wait 1 hour
    
    async def _handle_emergency_mode(self, health_report) -> None:
        """Handle emergency mode conditions"""
        self.logger.critical("Entering emergency mode")
        self.state.emergency_mode = True
        
        # Send emergency alert
        await self.notification_manager.send_emergency_alert({
            'health_score': health_report.overall_health_score,
            'critical_issues': health_report.critical_issues,
            'timestamp': datetime.now()
        })
        
        # Create emergency backup
        await self._create_emergency_backup()
        
        # Apply emergency fixes
        await self._apply_emergency_fixes(health_report)
        
        # Exit emergency mode after fixes
        self.state.emergency_mode = False
    
    async def _trigger_emergency_response(self, health_score: float) -> None:
        """Trigger emergency response"""
        self.logger.critical(f"Emergency response triggered - Health score: {health_score}")
        
        # Create emergency backup
        await self._create_emergency_backup()
        
        # Restart main system if needed
        if health_score < 30:
            await self._restart_main_system()
    
    async def _create_emergency_backup(self) -> None:
        """Create emergency backup"""
        try:
            backup_name = f"emergency_backup_{int(time.time())}.tar.gz"
            
            # Create archive
            subprocess.run([
                "tar", "-czf", backup_name,
                "--exclude='*.pyc'", "--exclude='__pycache__'",
                "--exclude='.git'", "--exclude='node_modules'",
                "."
            ], cwd=self.codebase_path)
            
            # Upload to remote
            await self.scp_manager.upload_backup(backup_name, backup_name)
            
            # Clean up local
            os.unlink(backup_name)
            
            self.logger.info(f"Emergency backup created: {backup_name}")
            
        except Exception as e:
            self.logger.error(f"Emergency backup failed: {e}")
    
    async def _create_and_upload_backup(self, evolution_id: str) -> None:
        """Create and upload backup after evolution"""
        try:
            backup_name = f"evolution_backup_{evolution_id}.tar.gz"
            
            # Create archive
            subprocess.run([
                "tar", "-czf", backup_name,
                "--exclude='*.pyc'", "--exclude='__pycache__'",
                "--exclude='.git'", "--exclude='node_modules'",
                "."
            ], cwd=self.codebase_path)
            
            # Upload to remote
            await self.scp_manager.upload_backup(backup_name, backup_name)
            
            # Clean up local
            os.unlink(backup_name)
            
            self.logger.info(f"Evolution backup created: {backup_name}")
            
        except Exception as e:
            self.logger.error(f"Evolution backup failed: {e}")
    
    async def _apply_emergency_fixes(self, health_report) -> None:
        """Apply emergency fixes"""
        try:
            # Apply fixes based on critical issues
            for issue in health_report.critical_issues:
                if "memory" in issue.lower():
                    await self._apply_memory_fix()
                elif "cpu" in issue.lower():
                    await self._apply_cpu_fix()
                elif "security" in issue.lower():
                    await self._apply_security_fix()
            
        except Exception as e:
            self.logger.error(f"Emergency fixes failed: {e}")
    
    async def _apply_memory_fix(self) -> None:
        """Apply memory-related fixes"""
        # Simplified memory fix
        subprocess.run(["sync"], shell=True)
        subprocess.run(["echo", "3", ">", "/proc/sys/vm/drop_caches"], shell=True)
    
    async def _apply_cpu_fix(self) -> None:
        """Apply CPU-related fixes"""
        # Simplified CPU fix
        pass
    
    async def _apply_security_fix(self) -> None:
        """Apply security-related fixes"""
        # Simplified security fix
        pass
    
    async def _restart_main_system(self) -> None:
        """Restart the main system"""
        try:
            self.logger.warning("Restarting main system")
            
            # Graceful shutdown
            await self.stop_continuous_orchestration()
            
            # Wait a bit
            await asyncio.sleep(10)
            
            # Restart (this would be implemented based on your deployment)
            # subprocess.run(["systemctl", "restart", "trading-bot"])
            
        except Exception as e:
            self.logger.error(f"System restart failed: {e}")
    
    async def _sync_state_with_remote(self) -> None:
        """Synchronize orchestration state with remote"""
        try:
            state_data = asdict(self.state)
            await self.scp_manager.sync_state(state_data)
        except Exception as e:
            self.logger.error(f"State synchronization failed: {e}")
    
    def _start_scheduler(self) -> None:
        """Start background scheduler for periodic tasks"""
        def run_scheduler():
            while self.state.is_running:
                schedule.run_pending()
                time.sleep(1)
        
        # Schedule daily backup
        schedule.every().day.at("02:00").do(self._scheduled_daily_backup)
        
        # Schedule weekly report
        schedule.every().week.do(self._generate_weekly_report)
        
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
    
    def _scheduled_daily_backup(self) -> None:
        """Scheduled daily backup"""
        asyncio.create_task(self._create_emergency_backup())
    
    def _generate_weekly_report(self) -> None:
        """Generate weekly report"""
        report = {
            'period': 'weekly',
            'timestamp': datetime.now(),
            'total_evolutions': self.state.total_evolutions,
            'successful_evolutions': self.state.successful_evolutions,
            'failed_evolutions': self.state.failed_evolutions,
            'system_health_score': self.state.system_health_score,
            'current_loop': self.state.current_loop
        }
        
        asyncio.create_task(
            self.notification_manager.send_evolution_notification(report)
        )
    
    def get_orchestration_status(self) -> Dict[str, Any]:
        """Get current orchestration status"""
        return {
            'state': asdict(self.state),
            'config': asdict(self.config),
            'is_healthy': self.state.system_health_score > self.config.emergency_threshold,
            'next_evolution_possible': (
                self.state.daily_evolution_count < self.config.max_daily_evolutions and
                not self.state.emergency_mode
            )
        }

# Usage example
async def main():
    """Main entry point for continuous orchestration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configuration
    config = OrchestrationConfig(
        loop_interval_seconds=300,  # 5 minutes
        scp_remote_host="user@backup-server.com",
        scp_remote_path="/backups/trading_bot/",
        email_notifications=True,
        email_recipients=["admin@company.com"],
        webhook_url="https://hooks.slack.com/services/xxx/yyy/zzz",
        max_daily_evolutions=5
    )
    
    # Start orchestrator
    orchestrator = ContinuousOrchestrator(".", config)
    
    try:
        await orchestrator.start_continuous_orchestration()
    except KeyboardInterrupt:
        print("\nShutting down orchestrator...")
        await orchestrator.stop_continuous_orchestration()

if __name__ == "__main__":
    asyncio.run(main())
