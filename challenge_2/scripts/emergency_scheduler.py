#!/usr/bin/env python3
"""
Emergency Scheduler for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Backup scheduler that ensures executions are scheduled even if main scheduler fails
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

class EmergencyScheduler:
    """Emergency backup scheduler for ensuring continuous operation"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.scripts_dir = self.base_dir / "scripts"
        self.logs_dir = self.base_dir / "logs"
        self.config_file = self.logs_dir / "scheduler_config.json"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for emergency scheduler"""
        log_file = self.logs_dir / f"emergency_scheduler_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_scheduled_jobs(self) -> List[Dict]:
        """Get currently scheduled 'at' jobs"""
        try:
            result = subprocess.run(['atq'], capture_output=True, text=True)
            jobs = []
            
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 6:
                            job_id = parts[0]
                            # Parse the date/time
                            date_str = ' '.join(parts[1:6])
                            jobs.append({
                                'id': job_id,
                                'datetime_str': date_str,
                                'line': line
                            })
                            
            return jobs
            
        except Exception as e:
            self.logger.error(f"Failed to get scheduled jobs: {e}")
            return []
            
    def count_future_executions(self) -> int:
        """Count how many executions are scheduled for the future"""
        jobs = self.get_scheduled_jobs()
        future_count = 0
        now = datetime.now()
        
        for job in jobs:
            try:
                # This is a simplified check - in practice, parsing 'at' output is complex
                # We'll count all jobs as potentially future executions
                future_count += 1
            except:
                continue
                
        return future_count
        
    def load_scheduler_config(self) -> Dict:
        """Load scheduler configuration"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            self.logger.error(f"Failed to load scheduler config: {e}")
            return {}
            
    def check_last_scheduling(self) -> bool:
        """Check if main scheduler has run recently"""
        try:
            config = self.load_scheduler_config()
            
            if 'last_scheduled' not in config:
                self.logger.warning("No last_scheduled timestamp found")
                return False
                
            last_scheduled = datetime.fromisoformat(config['last_scheduled'])
            hours_since = (datetime.now() - last_scheduled).total_seconds() / 3600
            
            # If more than 6 hours since last scheduling, consider it stale
            if hours_since > 6:
                self.logger.warning(f"Main scheduler hasn't run in {hours_since:.1f} hours")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to check last scheduling: {e}")
            return False
            
    def emergency_schedule(self) -> bool:
        """Perform emergency scheduling if needed"""
        try:
            self.logger.info("Running emergency scheduler check...")
            
            # Check if we have enough future executions
            future_count = self.count_future_executions()
            self.logger.info(f"Found {future_count} scheduled jobs")
            
            # Check if main scheduler has run recently
            main_scheduler_ok = self.check_last_scheduling()
            
            # If we have fewer than 5 jobs scheduled OR main scheduler hasn't run recently
            if future_count < 5 or not main_scheduler_ok:
                self.logger.warning(f"Emergency scheduling needed: jobs={future_count}, main_scheduler_ok={main_scheduler_ok}")
                
                # Run the main scheduler
                python_path = sys.executable
                scheduler_script = self.scripts_dir / "daily_scheduler.py"
                
                if scheduler_script.exists():
                    self.logger.info("Running main scheduler from emergency scheduler...")
                    result = subprocess.run([python_path, str(scheduler_script)], 
                                          capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        self.logger.info("Emergency scheduling completed successfully")
                        return True
                    else:
                        self.logger.error(f"Emergency scheduling failed: {result.stderr}")
                        return False
                else:
                    self.logger.error(f"Main scheduler script not found: {scheduler_script}")
                    return False
            else:
                self.logger.info("No emergency scheduling needed")
                return True
                
        except Exception as e:
            self.logger.error(f"Emergency scheduling failed: {e}")
            return False
            
    def send_emergency_notification(self, message: str):
        """Send emergency notification"""
        try:
            # Try to use the notification system
            python_path = sys.executable
            notification_script = self.scripts_dir / "send_notification.py"
            
            if notification_script.exists():
                subprocess.run([
                    python_path, str(notification_script),
                    "--message", f"EMERGENCY: {message}",
                    "--priority", "high"
                ], capture_output=True)
            else:
                # Fallback: log the emergency
                self.logger.critical(f"EMERGENCY NOTIFICATION: {message}")
                
        except Exception as e:
            self.logger.error(f"Failed to send emergency notification: {e}")


def main():
    """Main entry point for emergency scheduler"""
    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Create emergency scheduler
    emergency_scheduler = EmergencyScheduler(base_dir)
    
    # Run emergency check
    success = emergency_scheduler.emergency_schedule()
    
    if not success:
        emergency_scheduler.send_emergency_notification("Emergency scheduler failed to ensure job scheduling")
        sys.exit(1)


if __name__ == "__main__":
    main()