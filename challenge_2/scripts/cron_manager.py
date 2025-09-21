#!/usr/bin/env python3
"""
Cron Job Manager for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Manages cron jobs for 24/7 operation with redundancy and health monitoring
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple

class CronJobManager:
    """Manages cron job installation and configuration for 24/7 operation"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.scripts_dir = self.base_dir / "scripts"
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for cron manager"""
        log_file = self.logs_dir / f"cron_manager_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_current_crontab(self) -> str:
        """Get current crontab content"""
        try:
            result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
            else:
                return ""
        except subprocess.CalledProcessError:
            return ""
            
    def backup_crontab(self) -> bool:
        """Backup current crontab"""
        try:
            current_crontab = self.get_current_crontab()
            if current_crontab:
                backup_file = self.logs_dir / f"crontab_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(backup_file, 'w') as f:
                    f.write(current_crontab)
                self.logger.info(f"Crontab backed up to {backup_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup crontab: {e}")
            return False
            
    def create_improved_cron_jobs(self) -> List[str]:
        """Create improved cron job entries for 24/7 operation"""
        python_path = sys.executable
        
        # Define cron jobs for comprehensive coverage
        cron_jobs = [
            # Daily scheduler - runs multiple times for redundancy
            f"0 6 * * * {python_path} {self.scripts_dir}/daily_scheduler.py >> {self.logs_dir}/cron_scheduler.log 2>&1",
            f"0 12 * * * {python_path} {self.scripts_dir}/daily_scheduler.py >> {self.logs_dir}/cron_scheduler.log 2>&1",
            f"0 18 * * * {python_path} {self.scripts_dir}/daily_scheduler.py >> {self.logs_dir}/cron_scheduler.log 2>&1",
            
            # Health monitor - runs continuously
            f"*/5 * * * * {python_path} {self.scripts_dir}/health_check_runner.py >> {self.logs_dir}/cron_health.log 2>&1",
            
            # Emergency scheduler - runs every 2 hours as backup
            f"0 */2 * * * {python_path} {self.scripts_dir}/emergency_scheduler.py >> {self.logs_dir}/cron_emergency.log 2>&1",
            
            # Log cleanup - runs daily at midnight
            f"0 0 * * * {python_path} {self.scripts_dir}/log_cleanup.py >> {self.logs_dir}/cron_cleanup.log 2>&1",
        ]
        
        return cron_jobs
        
    def install_cron_jobs(self) -> bool:
        """Install improved cron jobs"""
        try:
            self.logger.info("Installing improved cron jobs for 24/7 operation...")
            
            # Backup existing crontab
            if not self.backup_crontab():
                self.logger.warning("Could not backup crontab, continuing anyway...")
                
            # Get current crontab
            current_crontab = self.get_current_crontab()
            
            # Remove existing DiploTools entries
            lines = current_crontab.split('\n') if current_crontab else []
            filtered_lines = [line for line in lines if 'DiploTools' not in line and 'challenge_2' not in line]
            
            # Add new cron jobs
            new_cron_jobs = self.create_improved_cron_jobs()
            
            # Add header comment
            filtered_lines.append("")
            filtered_lines.append("# DiploTools Challenge 2 - 24/7 Cron Job System")
            filtered_lines.append(f"# Installed: {datetime.now().isoformat()}")
            filtered_lines.extend(new_cron_jobs)
            
            # Write new crontab
            new_crontab = '\n'.join(filtered_lines)
            
            # Install new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                self.logger.info("Cron jobs installed successfully")
                self.logger.info(f"Installed {len(new_cron_jobs)} cron jobs:")
                for job in new_cron_jobs:
                    self.logger.info(f"  {job}")
                return True
            else:
                self.logger.error("Failed to install cron jobs")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception installing cron jobs: {e}")
            return False
            
    def verify_cron_jobs(self) -> bool:
        """Verify that cron jobs are installed correctly"""
        try:
            current_crontab = self.get_current_crontab()
            expected_jobs = self.create_improved_cron_jobs()
            
            installed_count = 0
            for job in expected_jobs:
                # Extract the command part (after the schedule)
                job_command = ' '.join(job.split()[5:])
                if job_command in current_crontab:
                    installed_count += 1
                    
            self.logger.info(f"Verification: {installed_count}/{len(expected_jobs)} cron jobs found")
            return installed_count == len(expected_jobs)
            
        except Exception as e:
            self.logger.error(f"Failed to verify cron jobs: {e}")
            return False
            
    def remove_cron_jobs(self) -> bool:
        """Remove DiploTools cron jobs"""
        try:
            self.logger.info("Removing DiploTools cron jobs...")
            
            # Backup existing crontab
            if not self.backup_crontab():
                self.logger.warning("Could not backup crontab, continuing anyway...")
                
            # Get current crontab
            current_crontab = self.get_current_crontab()
            
            # Remove DiploTools entries
            lines = current_crontab.split('\n') if current_crontab else []
            filtered_lines = []
            skip_next = False
            
            for line in lines:
                if '# DiploTools Challenge 2' in line:
                    skip_next = True
                    continue
                elif skip_next and (line.strip() == '' or line.startswith('#')):
                    continue
                elif 'DiploTools' in line or 'challenge_2' in line:
                    continue
                else:
                    skip_next = False
                    filtered_lines.append(line)
                    
            # Write new crontab
            new_crontab = '\n'.join(filtered_lines)
            
            # Install new crontab
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            
            if process.returncode == 0:
                self.logger.info("DiploTools cron jobs removed successfully")
                return True
            else:
                self.logger.error("Failed to remove cron jobs")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception removing cron jobs: {e}")
            return False


def main():
    """Main entry point for cron manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage DiploTools cron jobs")
    parser.add_argument('action', choices=['install', 'remove', 'verify'], 
                       help='Action to perform')
    parser.add_argument('--base-dir', type=str, 
                       help='Base directory (defaults to parent of script directory)')
    
    args = parser.parse_args()
    
    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent
        
    # Create cron manager
    cron_manager = CronJobManager(base_dir)
    
    # Perform requested action
    if args.action == 'install':
        success = cron_manager.install_cron_jobs()
        if success:
            print("✅ Cron jobs installed successfully")
            cron_manager.verify_cron_jobs()
        else:
            print("❌ Failed to install cron jobs")
            sys.exit(1)
            
    elif args.action == 'remove':
        success = cron_manager.remove_cron_jobs()
        if success:
            print("✅ Cron jobs removed successfully")
        else:
            print("❌ Failed to remove cron jobs")
            sys.exit(1)
            
    elif args.action == 'verify':
        success = cron_manager.verify_cron_jobs()
        if success:
            print("✅ All cron jobs are properly installed")
        else:
            print("⚠️ Some cron jobs are missing or incorrect")
            sys.exit(1)


if __name__ == "__main__":
    main()