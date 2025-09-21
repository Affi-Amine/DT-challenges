#!/usr/bin/env python3
"""
Daily Scheduler for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Generates 10 random execution times daily and schedules them using 'at' command
"""

import os
import sys
import random
import secrets
import time
import subprocess
import logging
import fcntl
from datetime import datetime, timedelta
from pathlib import Path
import json

class AtomicScheduler:
    """Handles atomic scheduling operations with file locking"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.lock_file = self.base_dir / "config" / "scheduler.lock"
        self.config_file = self.base_dir / "config" / "scheduler_config.json"
        self.log_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.lock_file.parent.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configure logging for the scheduler"""
        log_file = self.log_dir / f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_secure_random_time(self):
        """
        Generate cryptographically secure random time
        Combines multiple entropy sources for better randomness
        """
        entropy = int.from_bytes(os.urandom(4), 'big')
        time_factor = int(time.time() * 1000000) % 86400
        pid_factor = os.getpid() % 1000
        
        combined_seed = entropy ^ time_factor ^ pid_factor
        random.seed(combined_seed)
        
        return random.randint(0, 86399)  # Seconds in a day
        
    def generate_random_times(self, count=10, min_spacing_minutes=30):
        """
        Generate well-distributed random times for today
        Includes one fixed execution at 5 PM Tunisian time (16:00 UTC)
        
        Args:
            count: Number of execution times to generate
            min_spacing_minutes: Minimum spacing between executions
            
        Returns:
            List of datetime objects representing execution times
        """
        current_time = datetime.now()
        day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        # If it's past noon, schedule for tomorrow
        if current_time.hour >= 12:
            day_start += timedelta(days=1)
            day_end += timedelta(days=1)
            
        self.logger.info(f"Generating {count} random times between {day_start} and {day_end}")
        
        times = []
        min_spacing_seconds = min_spacing_minutes * 60
        
        # Business requirement: CEO expects executions during peak business hours in Tunisia
        fixed_times = [
            (16, 10, "5:10 PM"),  # 5:10 PM Tunisian time (16:10 UTC)
            (17, 5, "6:05 PM")    # 6:05 PM Tunisian time (17:05 UTC)
        ]
        
        for hour, minute, display_time in fixed_times:
            fixed_time = day_start.replace(hour=hour, minute=minute, second=0)
            if fixed_time > current_time + timedelta(minutes=5):
                times.append(fixed_time)
                self.logger.info(f"Added fixed execution at {display_time} Tunisian time: {fixed_time.strftime('%H:%M:%S')} UTC")
                count -= 1
        
        # Distribute remaining executions randomly to avoid predictable patterns
        for i in range(count):
            attempts = 0
            max_attempts = 100
            
            while attempts < max_attempts:
                random_seconds = self.generate_secure_random_time()
                execution_time = day_start + timedelta(seconds=random_seconds)
                
                # Skip times too close to current time to allow proper scheduling
                if execution_time <= current_time + timedelta(minutes=5):
                    attempts += 1
                    continue
                    
                # Maintain minimum spacing to prevent resource conflicts
                too_close = False
                for existing_time in times:
                    if abs((execution_time - existing_time).total_seconds()) < min_spacing_seconds:
                        too_close = True
                        break
                        
                if not too_close:
                    times.append(execution_time)
                    break
                    
                attempts += 1
                
            if attempts >= max_attempts:
                # Fallback: use systematic spacing
                fallback_time = day_start + timedelta(hours=8 + i * 1.2)
                times.append(fallback_time)
                self.logger.warning(f"Used fallback time for execution {i+1}: {fallback_time}")
                
        # Sort times chronologically
        times.sort()
        
        self.logger.info(f"Generated execution times: {[t.strftime('%H:%M:%S') for t in times]}")
        return times
        
    def clear_existing_jobs(self):
        """Clear existing 'at' jobs created by this scheduler"""
        try:
            # Get list of current jobs
            result = subprocess.run(['atq'], capture_output=True, text=True, check=True)
            
            if result.stdout.strip():
                self.logger.info("Clearing existing 'at' jobs")
                
                # Parse job IDs and clear them
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        job_id = line.split()[0]
                        try:
                            subprocess.run(['atrm', job_id], check=True)
                            self.logger.debug(f"Removed job {job_id}")
                        except subprocess.CalledProcessError as e:
                            self.logger.warning(f"Failed to remove job {job_id}: {e}")
            else:
                self.logger.info("No existing 'at' jobs to clear")
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to query existing jobs: {e}")
            
    def schedule_execution(self, execution_time):
        """
        Schedule a single execution using 'at' command
        
        Args:
            execution_time: datetime object for when to execute
            
        Returns:
            bool: True if scheduling succeeded, False otherwise
        """
        try:
            # Format time for 'at' command - use format that 'at' accepts
            at_time = execution_time.strftime('%H:%M %m/%d/%Y')
            
            # Path to execution wrapper
            wrapper_script = self.base_dir / "scripts" / "execution_wrapper.py"
            
            # Command to execute
            command = f"cd {self.base_dir} && python3 {wrapper_script}"
            
            # Schedule with 'at'
            process = subprocess.Popen(
                ['at', at_time],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=command)
            
            if process.returncode == 0:
                # Extract job ID from output
                job_info = stdout.strip()
                self.logger.info(f"Scheduled execution at {at_time}: {job_info}")
                return True
            else:
                self.logger.error(f"Failed to schedule execution at {at_time}: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception scheduling execution at {execution_time}: {e}")
            return False
            
    def save_schedule_info(self, execution_times):
        """Save scheduling information for monitoring and debugging"""
        schedule_info = {
            'scheduled_at': datetime.now().isoformat(),
            'execution_times': [t.isoformat() for t in execution_times],
            'total_executions': len(execution_times),
            'next_scheduling': (datetime.now() + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(schedule_info, f, indent=2)
            self.logger.info(f"Saved schedule information to {self.config_file}")
        except Exception as e:
            self.logger.error(f"Failed to save schedule info: {e}")
            
    def schedule_with_lock(self):
        """
        Main scheduling function with atomic locking
        
        Returns:
            bool: True if scheduling completed successfully
        """
        try:
            with open(self.lock_file, 'w') as lock:
                # Acquire exclusive lock
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                
                self.logger.info("=== Starting Daily Scheduling Process ===")
                
                # Generate random execution times
                execution_times = self.generate_random_times()
                
                # Clear existing jobs
                self.clear_existing_jobs()
                
                # Schedule new executions
                successful_schedules = 0
                for execution_time in execution_times:
                    if self.schedule_execution(execution_time):
                        successful_schedules += 1
                        
                # Save schedule information
                self.save_schedule_info(execution_times)
                
                self.logger.info(f"Scheduling complete: {successful_schedules}/{len(execution_times)} executions scheduled")
                
                # Verify scheduled jobs
                self.verify_scheduled_jobs()
                
                return successful_schedules == len(execution_times)
                
        except IOError:
            self.logger.warning("Another scheduler instance is running, skipping this execution")
            return False
        except Exception as e:
            self.logger.error(f"Scheduling failed with exception: {e}")
            return False
        finally:
            # Lock is automatically released when file is closed
            pass
            
    def verify_scheduled_jobs(self):
        """Verify that jobs were scheduled correctly"""
        try:
            result = subprocess.run(['atq'], capture_output=True, text=True, check=True)
            job_count = len([line for line in result.stdout.strip().split('\n') if line.strip()])
            self.logger.info(f"Verification: {job_count} jobs currently in 'at' queue")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to verify scheduled jobs: {e}")


def main():
    """Main entry point for the daily scheduler"""
    # Get base directory (parent of scripts directory)
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Create scheduler instance
    scheduler = AtomicScheduler(base_dir)
    
    # Run scheduling
    success = scheduler.schedule_with_lock()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()