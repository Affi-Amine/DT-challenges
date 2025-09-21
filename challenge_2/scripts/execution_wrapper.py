#!/usr/bin/env python3
"""
Execution Wrapper for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Wraps target script execution with comprehensive logging and notifications
"""

import os
import sys
import subprocess
import logging
import json
import uuid
import time
import psutil
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import signal
from contextlib import contextmanager

class ExecutionResult:
    """Container for execution results and metrics"""
    
    def __init__(self):
        self.session_id = str(uuid.uuid4())[:8]
        self.start_time = datetime.now()
        self.end_time = None
        self.duration = None
        self.exit_code = None
        self.success = False
        self.stdout = ""
        self.stderr = ""
        self.error_message = ""
        self.peak_memory_mb = 0
        self.cpu_percent = 0
        self.output_lines = 0
        self.warnings = 0
        self.errors = 0
        
    def finalize(self):
        """Finalize the execution result"""
        self.end_time = datetime.now()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.success = self.exit_code == 0 and not self.error_message
        
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'exit_code': self.exit_code,
            'success': self.success,
            'stdout_lines': len(self.stdout.split('\n')) if self.stdout else 0,
            'stderr_lines': len(self.stderr.split('\n')) if self.stderr else 0,
            'error_message': self.error_message,
            'peak_memory_mb': self.peak_memory_mb,
            'cpu_percent': self.cpu_percent,
            'output_lines': self.output_lines,
            'warnings': self.warnings,
            'errors': self.errors
        }


class ExecutionLogger:
    """Handles comprehensive logging for script execution"""
    
    def __init__(self, base_dir, session_id):
        self.base_dir = Path(base_dir)
        self.session_id = session_id
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create unique log file for this execution
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_file = self.log_dir / f"execution_{self.timestamp}_{self.session_id}.log"
        
        # Setup logger
        self.logger = logging.getLogger(f"execution_{session_id}")
        self.logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler with detailed formatting
        file_handler = logging.FileHandler(self.log_file)
        file_formatter = logging.Formatter(
            '[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter('%(levelname)s: %(message)s')
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
    def log_execution_story(self, result, target_script, environment_info):
        """Log the complete execution story"""
        
        # Story header
        self.logger.info("=" * 60)
        self.logger.info("EXECUTION STORY")
        self.logger.info("=" * 60)
        
        # Prologue: Context and environment
        self.logger.info(f"Session ID: {result.session_id}")
        self.logger.info(f"Start Time: {result.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        self.logger.info(f"Target Script: {target_script}")
        self.logger.info(f"Trigger: scheduled_execution")
        self.logger.info("")
        
        # Environment information
        self.logger.info("ENVIRONMENT")
        self.logger.info("-" * 30)
        for key, value in environment_info.items():
            self.logger.info(f"{key}: {value}")
        self.logger.info("")
        
        # Execution log (this will be filled during execution)
        self.logger.info("EXECUTION LOG")
        self.logger.info("-" * 30)
        
    def log_summary(self, result):
        """Log execution summary"""
        self.logger.info("")
        self.logger.info("SUMMARY")
        self.logger.info("-" * 30)
        self.logger.info(f"Duration: {result.duration:.3f} seconds")
        self.logger.info(f"Exit Code: {result.exit_code}")
        self.logger.info(f"Peak Memory: {result.peak_memory_mb:.1f}MB")
        self.logger.info(f"CPU Usage: {result.cpu_percent:.1f}%")
        self.logger.info(f"Output Lines: {result.output_lines}")
        self.logger.info(f"Errors: {result.errors}")
        self.logger.info(f"Warnings: {result.warnings}")
        self.logger.info(f"Success: {'✅' if result.success else '❌'}")
        
        if result.error_message:
            self.logger.error(f"Error Details: {result.error_message}")
            
        self.logger.info("=" * 60)


class ResourceMonitor:
    """Monitors resource usage during execution"""
    
    def __init__(self):
        self.process = None
        self.peak_memory = 0
        self.cpu_samples = []
        self.monitoring = False
        
    def start_monitoring(self, process):
        """Start monitoring a process"""
        self.process = psutil.Process(process.pid)
        self.monitoring = True
        self.peak_memory = 0
        self.cpu_samples = []
        
    def update_metrics(self):
        """Update resource metrics"""
        if not self.monitoring or not self.process:
            return
            
        try:
            # Memory usage
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            self.peak_memory = max(self.peak_memory, memory_mb)
            
            # CPU usage
            cpu_percent = self.process.cpu_percent()
            self.cpu_samples.append(cpu_percent)
            
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            self.monitoring = False
            
    def get_metrics(self):
        """Get final metrics"""
        avg_cpu = sum(self.cpu_samples) / len(self.cpu_samples) if self.cpu_samples else 0
        return {
            'peak_memory_mb': self.peak_memory,
            'avg_cpu_percent': avg_cpu
        }
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False


class SelfHealingExecutor:
    """Handles script execution with error recovery and self-healing"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.max_retries = 3
        self.backoff_factor = 2
        self.timeout_seconds = 300  # 5 minutes default timeout
        
    def get_environment_info(self):
        """Collect environment information"""
        return {
            'Hostname': os.uname().nodename,
            'User': os.getenv('USER', 'unknown'),
            'Working Directory': str(self.base_dir),
            'Python Version': sys.version.split()[0],
            'Available Memory': f"{psutil.virtual_memory().available / 1024**3:.1f}GB",
            'Disk Space': f"{psutil.disk_usage(str(self.base_dir)).free / 1024**3:.1f}GB free",
            'Load Average': str(os.getloadavg()) if hasattr(os, 'getloadavg') else 'N/A'
        }
        
    @contextmanager
    def timeout_handler(self, seconds):
        """Context manager for execution timeout"""
        def timeout_signal_handler(signum, frame):
            raise TimeoutError(f"Execution timed out after {seconds} seconds")
            
        # Set up signal handler
        old_handler = signal.signal(signal.SIGALRM, timeout_signal_handler)
        signal.alarm(seconds)
        
        try:
            yield
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            
    def execute_script(self, target_script_path):
        """
        Execute target script with comprehensive monitoring
        
        Args:
            target_script_path: Path to the script to execute
            
        Returns:
            ExecutionResult: Complete execution results
        """
        result = ExecutionResult()
        logger = ExecutionLogger(self.base_dir, result.session_id)
        monitor = ResourceMonitor()
        
        # Get environment info
        env_info = self.get_environment_info()
        
        # Log execution story header
        logger.log_execution_story(result, target_script_path, env_info)
        
        try:
            # Validate target script
            if not Path(target_script_path).exists():
                raise FileNotFoundError(f"Target script not found: {target_script_path}")
                
            logger.logger.info(f"Starting script execution: {target_script_path}")
            
            # Execute with timeout
            with self.timeout_handler(self.timeout_seconds):
                # Start process
                process = subprocess.Popen(
                    [sys.executable, str(target_script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=self.base_dir
                )
                
                # Start monitoring
                monitor.start_monitoring(process)
                
                # Monitor execution
                stdout_lines = []
                stderr_lines = []
                
                # Read output in real-time
                while process.poll() is None:
                    # Update resource metrics
                    monitor.update_metrics()
                    
                    # Small sleep to prevent excessive CPU usage
                    time.sleep(0.1)
                    
                # Get final output
                stdout, stderr = process.communicate()
                
                # Stop monitoring
                monitor.stop_monitoring()
                
                # Update result
                result.exit_code = process.returncode
                result.stdout = stdout
                result.stderr = stderr
                
                # Count lines and analyze output
                if stdout:
                    result.output_lines = len(stdout.split('\n'))
                    logger.logger.info(f"Script output ({result.output_lines} lines):")
                    for line in stdout.split('\n')[:10]:  # Log first 10 lines
                        if line.strip():
                            logger.logger.info(f"  {line}")
                    if result.output_lines > 10:
                        logger.logger.info(f"  ... ({result.output_lines - 10} more lines)")
                        
                if stderr:
                    stderr_lines = stderr.split('\n')
                    result.errors = len([line for line in stderr_lines if 'error' in line.lower()])
                    result.warnings = len([line for line in stderr_lines if 'warning' in line.lower()])
                    
                    logger.logger.warning(f"Script stderr ({len(stderr_lines)} lines):")
                    for line in stderr_lines[:5]:  # Log first 5 error lines
                        if line.strip():
                            logger.logger.warning(f"  {line}")
                            
                # Get resource metrics
                metrics = monitor.get_metrics()
                result.peak_memory_mb = metrics['peak_memory_mb']
                result.cpu_percent = metrics['avg_cpu_percent']
                
                logger.logger.info(f"Script completed with exit code: {result.exit_code}")
                
        except TimeoutError as e:
            result.error_message = str(e)
            result.exit_code = -1
            logger.logger.error(f"Execution timed out: {e}")
            
        except Exception as e:
            result.error_message = str(e)
            result.exit_code = -1
            logger.logger.error(f"Execution failed: {e}")
            logger.logger.error(f"Traceback: {traceback.format_exc()}")
            
        finally:
            # Finalize result
            result.finalize()
            
            # Log summary
            logger.log_summary(result)
            
        return result
        
    def execute_with_recovery(self, target_script_path):
        """
        Execute script with retry logic and error recovery
        
        Args:
            target_script_path: Path to the script to execute
            
        Returns:
            ExecutionResult: Final execution result
        """
        last_result = None
        
        for attempt in range(self.max_retries):
            print(f"Execution attempt {attempt + 1}/{self.max_retries}")
            
            result = self.execute_script(target_script_path)
            last_result = result
            
            if result.success:
                print(f"✅ Execution successful on attempt {attempt + 1}")
                return result
                
            # If not the last attempt, wait before retrying
            if attempt < self.max_retries - 1:
                wait_time = self.backoff_factor ** attempt
                print(f"❌ Attempt {attempt + 1} failed, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"❌ All {self.max_retries} attempts failed")
                
        return last_result


def main():
    """Main entry point for the execution wrapper"""
    # Get base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Default target script
    target_script = base_dir / "scripts" / "target_script.py"
    
    # Allow override via command line argument
    if len(sys.argv) > 1:
        target_script = Path(sys.argv[1])
        if not target_script.is_absolute():
            target_script = base_dir / target_script
            
    print(f"🚀 Starting execution wrapper for: {target_script}")
    
    # Create executor
    executor = SelfHealingExecutor(base_dir)
    
    # Execute with recovery
    result = executor.execute_with_recovery(target_script)
    
    # Save execution result
    results_dir = base_dir / "logs" / "results"
    results_dir.mkdir(exist_ok=True)
    
    result_file = results_dir / f"result_{result.session_id}.json"
    try:
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        print(f"📊 Execution result saved to: {result_file}")
    except Exception as e:
        print(f"⚠️ Failed to save execution result: {e}")
        
    # Import and send notifications
    try:
        from notification_system import NotificationManager
        notifier = NotificationManager(base_dir)
        notifier.send_execution_notification(result)
    except ImportError:
        print("📱 Notification system not available (will be implemented next)")
    except Exception as e:
        print(f"📱 Failed to send notification: {e}")
        
    # Exit with appropriate code
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()