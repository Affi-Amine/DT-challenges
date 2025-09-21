#!/usr/bin/env python3
"""
Comprehensive test suite for Challenge 2 - 24/7 Cron Job System
Tests all components of the automated scheduling system
"""

import os
import sys
import json
import time
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

class Challenge2Tester:
    def __init__(self):
        self.results = []
        self.base_dir = Path(__file__).parent
        self.scripts_dir = self.base_dir / "scripts"
        
    def log_result(self, test_name, status, message="", duration=0, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "duration": f"{duration:.3f}s",
            "details": details or {}
        }
        self.results.append(result)
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {message} ({duration:.3f}s)")
        
    def test_system_installation(self):
        """Test if the system is properly installed"""
        start_time = time.time()
        try:
            # Check if installation log exists
            install_log = self.base_dir / "installation_log.json"
            if install_log.exists():
                with open(install_log) as f:
                    log_data = json.load(f)
                    
                duration = time.time() - start_time
                self.log_result(
                    "System Installation", 
                    "PASS", 
                    f"Installed on {log_data.get('installation_date', 'unknown')}", 
                    duration,
                    {"python_version": log_data.get("python_version"), "system": log_data.get("system")}
                )
            else:
                duration = time.time() - start_time
                self.log_result("System Installation", "FAIL", "Installation log not found", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("System Installation", "FAIL", f"Error: {str(e)}", duration)
            
    def test_cron_jobs_active(self):
        """Test if cron jobs are active"""
        start_time = time.time()
        try:
            # Check crontab
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                cron_lines = [line for line in result.stdout.split('\n') if line.strip() and not line.startswith('#')]
                challenge2_jobs = [line for line in cron_lines if 'challenge_2' in line or 'daily_scheduler' in line]
                
                if challenge2_jobs:
                    self.log_result(
                        "Cron Jobs Active", 
                        "PASS", 
                        f"Found {len(challenge2_jobs)} active cron jobs", 
                        duration,
                        {"jobs": challenge2_jobs}
                    )
                else:
                    self.log_result("Cron Jobs Active", "FAIL", "No Challenge 2 cron jobs found", duration)
            else:
                self.log_result("Cron Jobs Active", "FAIL", "Could not access crontab", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Cron Jobs Active", "FAIL", f"Error: {str(e)}", duration)
            
    def test_scheduled_jobs_queue(self):
        """Test scheduled jobs in at queue"""
        start_time = time.time()
        try:
            result = subprocess.run(['atq'], capture_output=True, text=True)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                jobs = result.stdout.strip().split('\n') if result.stdout.strip() else []
                job_count = len([job for job in jobs if job.strip()])
                
                if job_count > 0:
                    self.log_result(
                        "Scheduled Jobs Queue", 
                        "PASS", 
                        f"Found {job_count} scheduled jobs", 
                        duration,
                        {"job_count": job_count}
                    )
                else:
                    self.log_result("Scheduled Jobs Queue", "SKIP", "No jobs in queue (normal if recently cleared)", duration)
            else:
                self.log_result("Scheduled Jobs Queue", "FAIL", "Could not access at queue", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Scheduled Jobs Queue", "FAIL", f"Error: {str(e)}", duration)
            
    def test_health_monitor_running(self):
        """Test if system health monitor is running"""
        start_time = time.time()
        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            duration = time.time() - start_time
            
            if result.returncode == 0:
                health_monitor_processes = [
                    line for line in result.stdout.split('\n') 
                    if 'system_health_monitor' in line and 'grep' not in line
                ]
                
                if health_monitor_processes:
                    self.log_result(
                        "Health Monitor Running", 
                        "PASS", 
                        f"Health monitor active (PID found)", 
                        duration,
                        {"process_count": len(health_monitor_processes)}
                    )
                else:
                    self.log_result("Health Monitor Running", "SKIP", "Health monitor not currently running", duration)
            else:
                self.log_result("Health Monitor Running", "FAIL", "Could not check processes", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Health Monitor Running", "FAIL", f"Error: {str(e)}", duration)
            
    def test_script_files_exist(self):
        """Test if all required script files exist"""
        start_time = time.time()
        
        required_scripts = [
            "daily_scheduler.py",
            "execution_wrapper.py", 
            "system_health_monitor.py",
            "target_script.py",
            "notification_system.py",
            "config_manager.py",
            "logging_system.py"
        ]
        
        missing_scripts = []
        existing_scripts = []
        
        for script in required_scripts:
            script_path = self.scripts_dir / script
            if script_path.exists():
                existing_scripts.append(script)
            else:
                missing_scripts.append(script)
                
        duration = time.time() - start_time
        
        if not missing_scripts:
            self.log_result(
                "Script Files Exist", 
                "PASS", 
                f"All {len(required_scripts)} scripts found", 
                duration,
                {"scripts": existing_scripts}
            )
        else:
            self.log_result(
                "Script Files Exist", 
                "FAIL", 
                f"Missing {len(missing_scripts)} scripts", 
                duration,
                {"missing": missing_scripts, "existing": existing_scripts}
            )
            
    def test_configuration_files(self):
        """Test if configuration files exist and are valid"""
        start_time = time.time()
        try:
            config_dir = self.base_dir / "config"
            env_file = self.base_dir / ".env"
            
            config_files = []
            if config_dir.exists():
                config_files.extend(list(config_dir.glob("*.yaml")))
                config_files.extend(list(config_dir.glob("*.yml")))
                config_files.extend(list(config_dir.glob("*.json")))
                
            env_exists = env_file.exists()
            
            duration = time.time() - start_time
            
            if config_files or env_exists:
                self.log_result(
                    "Configuration Files", 
                    "PASS", 
                    f"Found {len(config_files)} config files + env file", 
                    duration,
                    {"config_files": [f.name for f in config_files], "env_exists": env_exists}
                )
            else:
                self.log_result("Configuration Files", "SKIP", "No configuration files found", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Configuration Files", "FAIL", f"Error: {str(e)}", duration)
            
    def test_log_directory(self):
        """Test if log directory exists and has recent logs"""
        start_time = time.time()
        try:
            logs_dir = self.base_dir / "logs"
            
            if logs_dir.exists():
                log_files = list(logs_dir.glob("*.log"))
                recent_logs = []
                
                # Check for logs modified in the last 24 hours
                cutoff_time = datetime.now() - timedelta(hours=24)
                for log_file in log_files:
                    if datetime.fromtimestamp(log_file.stat().st_mtime) > cutoff_time:
                        recent_logs.append(log_file.name)
                        
                duration = time.time() - start_time
                
                if recent_logs:
                    self.log_result(
                        "Log Directory", 
                        "PASS", 
                        f"Found {len(recent_logs)} recent log files", 
                        duration,
                        {"recent_logs": recent_logs, "total_logs": len(log_files)}
                    )
                else:
                    self.log_result(
                        "Log Directory", 
                        "SKIP", 
                        f"Found {len(log_files)} log files but none recent", 
                        duration
                    )
            else:
                duration = time.time() - start_time
                self.log_result("Log Directory", "SKIP", "Logs directory not found", duration)
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Log Directory", "FAIL", f"Error: {str(e)}", duration)
            
    def test_daily_scheduler_execution(self):
        """Test daily scheduler can be executed"""
        start_time = time.time()
        try:
            scheduler_script = self.scripts_dir / "daily_scheduler.py"
            
            if scheduler_script.exists():
                # Test dry run
                result = subprocess.run(
                    [sys.executable, str(scheduler_script), '--dry-run'], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                duration = time.time() - start_time
                
                if result.returncode == 0:
                    self.log_result(
                        "Daily Scheduler Execution", 
                        "PASS", 
                        "Scheduler executed successfully (dry run)", 
                        duration,
                        {"output_lines": len(result.stdout.split('\n'))}
                    )
                else:
                    self.log_result(
                        "Daily Scheduler Execution", 
                        "FAIL", 
                        f"Scheduler failed with exit code {result.returncode}", 
                        duration,
                        {"stderr": result.stderr[:200]}
                    )
            else:
                duration = time.time() - start_time
                self.log_result("Daily Scheduler Execution", "FAIL", "Scheduler script not found", duration)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_result("Daily Scheduler Execution", "FAIL", "Scheduler execution timed out", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Daily Scheduler Execution", "FAIL", f"Error: {str(e)}", duration)
            
    def test_target_script_execution(self):
        """Test target script can be executed"""
        start_time = time.time()
        try:
            target_script = self.scripts_dir / "target_script.py"
            
            if target_script.exists():
                result = subprocess.run(
                    [sys.executable, str(target_script)], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                duration = time.time() - start_time
                
                if result.returncode == 0:
                    self.log_result(
                        "Target Script Execution", 
                        "PASS", 
                        "Target script executed successfully", 
                        duration,
                        {"output_lines": len(result.stdout.split('\n'))}
                    )
                else:
                    self.log_result(
                        "Target Script Execution", 
                        "FAIL", 
                        f"Target script failed with exit code {result.returncode}", 
                        duration
                    )
            else:
                duration = time.time() - start_time
                self.log_result("Target Script Execution", "FAIL", "Target script not found", duration)
                
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            self.log_result("Target Script Execution", "FAIL", "Target script execution timed out", duration)
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Target Script Execution", "FAIL", f"Error: {str(e)}", duration)
            
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Challenge 2 Tests - 24/7 Cron Job System")
        print("=" * 60)
        
        self.test_system_installation()
        self.test_script_files_exist()
        self.test_configuration_files()
        self.test_log_directory()
        self.test_cron_jobs_active()
        self.test_scheduled_jobs_queue()
        self.test_health_monitor_running()
        self.test_daily_scheduler_execution()
        self.test_target_script_execution()
        
        print("\n" + "=" * 60)
        print("📊 Test Summary:")
        
        passed = len([r for r in self.results if r["status"] == "PASS"])
        failed = len([r for r in self.results if r["status"] == "FAIL"])
        skipped = len([r for r in self.results if r["status"] == "SKIP"])
        total = len(self.results)
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️  Skipped: {skipped}")
        print(f"📈 Total: {total}")
        
        if failed == 0:
            print("\n🎉 All tests passed or skipped!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")
            
        # Calculate system health score
        health_score = (passed / total) * 100 if total > 0 else 0
        print(f"🏥 System Health Score: {health_score:.1f}%")
        
        return self.results

if __name__ == "__main__":
    tester = Challenge2Tester()
    results = tester.run_all_tests()
    
    # Save results to JSON
    with open("challenge_2_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to challenge_2_test_results.json")