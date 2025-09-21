#!/usr/bin/env python3
"""
Health Check Runner for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Lightweight runner that ensures the system health monitor is active
"""

import os
import sys
import subprocess
import signal
import time
import logging
from datetime import datetime
from pathlib import Path

class HealthCheckRunner:
    """Lightweight runner to ensure system health monitor is active"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.scripts_dir = self.base_dir / "scripts"
        self.logs_dir = self.base_dir / "logs"
        self.pid_file = self.logs_dir / "health_monitor.pid"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
    def is_health_monitor_running(self) -> bool:
        """Check if the health monitor is currently running"""
        try:
            if not self.pid_file.exists():
                return False
                
            with open(self.pid_file, 'r') as f:
                pid = int(f.read().strip())
                
            # Check if process is still running
            try:
                os.kill(pid, 0)  # Signal 0 just checks if process exists
                return True
            except OSError:
                # Process doesn't exist, remove stale PID file
                self.pid_file.unlink(missing_ok=True)
                return False
                
        except (ValueError, FileNotFoundError):
            return False
            
    def start_health_monitor(self) -> bool:
        """Start the system health monitor"""
        try:
            python_path = sys.executable
            monitor_script = self.scripts_dir / "system_health_monitor.py"
            
            if not monitor_script.exists():
                print(f"Health monitor script not found: {monitor_script}")
                return False
                
            # Start the health monitor as a background process
            process = subprocess.Popen(
                [python_path, str(monitor_script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True  # Detach from parent process
            )
            
            # Save PID
            with open(self.pid_file, 'w') as f:
                f.write(str(process.pid))
                
            # Give it a moment to start
            time.sleep(2)
            
            # Verify it's still running
            if process.poll() is None:
                print(f"Health monitor started successfully (PID: {process.pid})")
                return True
            else:
                print("Health monitor failed to start")
                self.pid_file.unlink(missing_ok=True)
                return False
                
        except Exception as e:
            print(f"Failed to start health monitor: {e}")
            return False
            
    def run_health_check(self) -> bool:
        """Run a quick health check and ensure monitor is active"""
        try:
            # Check if health monitor is running
            if self.is_health_monitor_running():
                print("✅ Health monitor is running")
                return True
            else:
                print("⚠️ Health monitor is not running, starting it...")
                return self.start_health_monitor()
                
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


def main():
    """Main entry point for health check runner"""
    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Create health check runner
    runner = HealthCheckRunner(base_dir)
    
    # Run health check
    success = runner.run_health_check()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()