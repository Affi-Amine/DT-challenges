#!/usr/bin/env python3
"""
System Health Monitor for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Continuous monitoring system that ensures 24/7 operation and service reliability
"""

import os
import sys
import subprocess
import logging
import json
import time
import signal
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import fcntl

class SystemHealthMonitor:
    """Monitors system health and ensures continuous operation"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.config_dir = self.base_dir / "config"
        self.logs_dir = self.base_dir / "logs"
        self.scripts_dir = self.base_dir / "scripts"
        
        # Health check configuration
        self.check_interval = 300  # 5 minutes
        self.min_jobs_required = 5  # Minimum jobs that should be scheduled
        self.max_hours_without_execution = 2  # Alert if no execution in 2 hours
        
        # State tracking
        self.running = False
        self.last_health_check = None
        self.last_execution_time = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
        
        # Setup logging
        self.setup_logging()
        
        # Load notification system
        self.setup_notifications()
        
    def setup_logging(self):
        """Setup dedicated logging for health monitor"""
        log_file = self.logs_dir / f"health_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_notifications(self):
        """Setup notification system"""
        try:
            sys.path.append(str(self.scripts_dir))
            from notification_system import NotificationManager
            self.notifier = NotificationManager(self.base_dir)
            self.logger.info("Notification system initialized")
        except ImportError as e:
            self.logger.warning(f"Notification system not available: {e}")
            self.notifier = None
        except Exception as e:
            self.logger.error(f"Failed to initialize notifications: {e}")
            self.notifier = None
            
    def get_scheduled_jobs_count(self) -> int:
        """Get count of currently scheduled 'at' jobs"""
        try:
            result = subprocess.run(['atq'], capture_output=True, text=True, check=True)
            if result.stdout.strip():
                return len([line for line in result.stdout.strip().split('\n') if line.strip()])
            return 0
        except subprocess.CalledProcessError:
            return 0
            
    def get_last_execution_time(self) -> Optional[datetime]:
        """Get timestamp of last successful execution"""
        try:
            results_dir = self.logs_dir / "results"
            if not results_dir.exists():
                return None
                
            # Find most recent result file
            result_files = list(results_dir.glob("result_*.json"))
            if not result_files:
                return None
                
            # Sort by modification time
            result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Read most recent result
            with open(result_files[0], 'r') as f:
                result_data = json.load(f)
                
            return datetime.fromisoformat(result_data['end_time'])
            
        except Exception as e:
            self.logger.warning(f"Could not determine last execution time: {e}")
            return None
            
    def check_system_health(self) -> Dict[str, any]:
        """Perform comprehensive system health check"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'issues': [],
            'metrics': {}
        }
        
        # Check scheduled jobs
        jobs_count = self.get_scheduled_jobs_count()
        health_status['metrics']['scheduled_jobs'] = jobs_count
        
        if jobs_count < self.min_jobs_required:
            health_status['issues'].append(f"Insufficient scheduled jobs: {jobs_count} < {self.min_jobs_required}")
            health_status['overall_status'] = 'unhealthy'
            
        # Check last execution time
        last_execution = self.get_last_execution_time()
        if last_execution:
            hours_since_execution = (datetime.now() - last_execution).total_seconds() / 3600
            health_status['metrics']['hours_since_last_execution'] = hours_since_execution
            
            if hours_since_execution > self.max_hours_without_execution:
                health_status['issues'].append(f"No execution in {hours_since_execution:.1f} hours")
                health_status['overall_status'] = 'unhealthy'
        else:
            health_status['issues'].append("No execution history found")
            health_status['overall_status'] = 'unhealthy'
            
        # Check disk space
        try:
            disk_usage = os.statvfs(str(self.base_dir))
            free_space_gb = (disk_usage.f_frsize * disk_usage.f_bavail) / (1024**3)
            health_status['metrics']['free_disk_space_gb'] = free_space_gb
            
            if free_space_gb < 1.0:  # Less than 1GB free
                health_status['issues'].append(f"Low disk space: {free_space_gb:.1f}GB")
                health_status['overall_status'] = 'unhealthy'
        except Exception as e:
            health_status['issues'].append(f"Could not check disk space: {e}")
            
        # Check log directory size
        try:
            log_size_mb = sum(f.stat().st_size for f in self.logs_dir.rglob('*') if f.is_file()) / (1024**2)
            health_status['metrics']['log_size_mb'] = log_size_mb
            
            if log_size_mb > 500:  # More than 500MB of logs
                health_status['issues'].append(f"Large log directory: {log_size_mb:.1f}MB")
        except Exception as e:
            health_status['issues'].append(f"Could not check log size: {e}")
            
        return health_status
        
    def trigger_emergency_scheduling(self) -> bool:
        """Trigger emergency rescheduling when system is unhealthy"""
        try:
            self.logger.warning("Triggering emergency scheduling...")
            
            # Execute daily scheduler to restore normal operations
            scheduler_script = self.scripts_dir / "daily_scheduler.py"
            result = subprocess.run(
                [sys.executable, str(scheduler_script)],
                capture_output=True,
                text=True,
                cwd=self.base_dir
            )
            
            if result.returncode == 0:
                self.logger.info("Emergency scheduling completed successfully")
                return True
            else:
                self.logger.error(f"Emergency scheduling failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Emergency scheduling exception: {e}")
            return False
            
    def send_health_alert(self, health_status: Dict[str, any]):
        """Send health alert notification"""
        try:
            # Use the standalone notification sender
            python_path = sys.executable
            notification_script = self.scripts_dir / "send_notification.py"
            
            if notification_script.exists():
                # Determine alert type based on health status
                if health_status['overall_status'] == 'unhealthy':
                    alert_type = "health_warning"
                    message = f"System health check failed. Issues: {', '.join(health_status['issues'])}"
                else:
                    alert_type = "recovery_success"
                    message = "System health check passed - all systems operational"
                
                # Send notification
                subprocess.run([
                    python_path, str(notification_script),
                    "--alert-type", alert_type,
                    "--message", message
                ], capture_output=True)
                
                self.logger.info(f"Health alert notification sent: {message}")
            else:
                # Fallback: just log the alert
                message = f"Health Status: {health_status['overall_status']}"
                if health_status['issues']:
                    message += f" - Issues: {', '.join(health_status['issues'])}"
                self.logger.warning(f"Notification script not found, logging health alert: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to send health alert: {e}")
            
    def send_notification(self, message: str, priority: str = "normal"):
        """Send notification using the notification system"""
        try:
            # Use the standalone notification sender
            python_path = sys.executable
            notification_script = self.scripts_dir / "send_notification.py"
            
            if notification_script.exists():
                # Determine notification type based on message content
                if any(word in message.lower() for word in ['failure', 'failed', 'error', 'critical']):
                    alert_type = "scheduler_failure"
                elif any(word in message.lower() for word in ['warning', 'issue', 'problem']):
                    alert_type = "health_warning"
                elif any(word in message.lower() for word in ['recovery', 'restored', 'fixed']):
                    alert_type = "recovery_success"
                else:
                    alert_type = None
                
                # Send notification
                if alert_type:
                    subprocess.run([
                        python_path, str(notification_script),
                        "--alert-type", alert_type,
                        "--message", message
                    ], capture_output=True)
                else:
                    subprocess.run([
                        python_path, str(notification_script),
                        "--message", message,
                        "--priority", priority,
                        "--type", "info"
                    ], capture_output=True)
                    
                self.logger.info(f"NOTIFICATION [{priority.upper()}]: {message}")
            else:
                # Fallback: just log the notification
                self.logger.warning(f"Notification script not found, logging instead: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to send notification: {e}")
            
    def perform_health_check_cycle(self):
        """Perform one complete health check cycle"""
        try:
            self.logger.info("Starting health check cycle...")
            
            # Perform health check
            health_status = self.check_system_health()
            self.last_health_check = datetime.now()
            
            # Log health status
            if health_status['overall_status'] == 'healthy':
                self.logger.info("System health: HEALTHY")
                self.consecutive_failures = 0
            else:
                self.logger.warning(f"System health: UNHEALTHY - Issues: {', '.join(health_status['issues'])}")
                self.consecutive_failures += 1
                
                # Attempt recovery
                if self.consecutive_failures <= self.max_consecutive_failures:
                    self.logger.info(f"Attempting recovery (attempt {self.consecutive_failures}/{self.max_consecutive_failures})")
                    
                    if self.trigger_emergency_scheduling():
                        self.logger.info("Recovery successful")
                        self.consecutive_failures = 0
                    else:
                        self.logger.error("Recovery failed")
                        
                # Send alert for persistent issues
                if self.consecutive_failures >= self.max_consecutive_failures:
                    self.logger.critical("Maximum consecutive failures reached, sending alert")
                    self.send_health_alert(health_status)
                    
            # Save health status
            health_file = self.logs_dir / f"health_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(health_file, 'w') as f:
                json.dump(health_status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Health check cycle failed: {e}")
            
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    def run_monitor(self):
        """Main monitoring loop"""
        self.logger.info("Starting System Health Monitor...")
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            while self.running:
                self.perform_health_check_cycle()
                
                # Wait for next check interval
                for _ in range(self.check_interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except KeyboardInterrupt:
            self.logger.info("Monitor stopped by user")
        except Exception as e:
            self.logger.error(f"Monitor crashed: {e}")
        finally:
            self.logger.info("System Health Monitor stopped")


def main():
    """Main entry point for the health monitor"""
    # Get base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Create and run monitor
    monitor = SystemHealthMonitor(base_dir)
    monitor.run_monitor()


if __name__ == "__main__":
    main()