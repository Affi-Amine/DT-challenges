#!/usr/bin/env python3
"""
Log Cleanup Script for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Manages log files to prevent disk space issues and maintain system health
"""

import os
import sys
import shutil
import gzip
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

class LogCleanupManager:
    """Manages log file cleanup and archival"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
        # Configuration
        self.max_log_age_days = 30  # Keep logs for 30 days
        self.max_result_files = 100  # Keep max 100 result files
        self.compress_age_days = 7   # Compress logs older than 7 days
        
    def setup_logging(self):
        """Setup logging for cleanup manager"""
        log_file = self.logs_dir / f"cleanup_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def get_file_age_days(self, file_path: Path) -> float:
        """Get the age of a file in days"""
        try:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            age = datetime.now() - file_time
            return age.total_seconds() / 86400  # Convert to days
        except Exception:
            return 0
            
    def compress_old_logs(self) -> int:
        """Compress log files older than compress_age_days"""
        compressed_count = 0
        
        try:
            for log_file in self.logs_dir.glob("*.log"):
                if self.get_file_age_days(log_file) > self.compress_age_days:
                    # Skip if already compressed version exists
                    compressed_file = log_file.with_suffix('.log.gz')
                    if compressed_file.exists():
                        continue
                        
                    # Compress the file
                    try:
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_file, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                                
                        # Remove original file
                        log_file.unlink()
                        compressed_count += 1
                        self.logger.info(f"Compressed: {log_file.name}")
                        
                    except Exception as e:
                        self.logger.error(f"Failed to compress {log_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during log compression: {e}")
            
        return compressed_count
        
    def cleanup_old_logs(self) -> int:
        """Remove log files older than max_log_age_days"""
        removed_count = 0
        
        try:
            # Clean up regular log files
            for log_file in self.logs_dir.glob("*.log"):
                if self.get_file_age_days(log_file) > self.max_log_age_days:
                    try:
                        log_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed old log: {log_file.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {log_file}: {e}")
                        
            # Clean up compressed log files
            for log_file in self.logs_dir.glob("*.log.gz"):
                if self.get_file_age_days(log_file) > self.max_log_age_days:
                    try:
                        log_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed old compressed log: {log_file.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {log_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during log cleanup: {e}")
            
        return removed_count
        
    def cleanup_result_files(self) -> int:
        """Clean up excess result files, keeping only the most recent ones"""
        removed_count = 0
        
        try:
            results_dir = self.logs_dir / "results"
            if not results_dir.exists():
                return 0
                
            # Get all result files sorted by modification time (newest first)
            result_files = list(results_dir.glob("result_*.json"))
            result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remove excess files
            if len(result_files) > self.max_result_files:
                files_to_remove = result_files[self.max_result_files:]
                
                for file_path in files_to_remove:
                    try:
                        file_path.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed excess result file: {file_path.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {file_path}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during result file cleanup: {e}")
            
        return removed_count
        
    def cleanup_temp_files(self) -> int:
        """Clean up temporary files and lock files"""
        removed_count = 0
        
        try:
            # Clean up lock files older than 1 day
            for lock_file in self.logs_dir.glob("*.lock"):
                if self.get_file_age_days(lock_file) > 1:
                    try:
                        lock_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed stale lock file: {lock_file.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {lock_file}: {e}")
                        
            # Clean up backup files older than 7 days
            for backup_file in self.logs_dir.glob("*_backup_*"):
                if self.get_file_age_days(backup_file) > 7:
                    try:
                        backup_file.unlink()
                        removed_count += 1
                        self.logger.info(f"Removed old backup: {backup_file.name}")
                    except Exception as e:
                        self.logger.error(f"Failed to remove {backup_file}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error during temp file cleanup: {e}")
            
        return removed_count
        
    def get_disk_usage(self) -> dict:
        """Get disk usage information for the logs directory"""
        try:
            total_size = 0
            file_count = 0
            
            for file_path in self.logs_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
                    file_count += 1
                    
            return {
                'total_size_mb': total_size / (1024 * 1024),
                'file_count': file_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate disk usage: {e}")
            return {'total_size_mb': 0, 'file_count': 0}
            
    def run_cleanup(self) -> dict:
        """Run complete cleanup process"""
        self.logger.info("Starting log cleanup process...")
        
        # Get initial disk usage
        initial_usage = self.get_disk_usage()
        
        # Perform cleanup operations
        compressed_count = self.compress_old_logs()
        removed_logs = self.cleanup_old_logs()
        removed_results = self.cleanup_result_files()
        removed_temp = self.cleanup_temp_files()
        
        # Get final disk usage
        final_usage = self.get_disk_usage()
        
        # Calculate savings
        space_saved_mb = initial_usage['total_size_mb'] - final_usage['total_size_mb']
        
        results = {
            'compressed_files': compressed_count,
            'removed_logs': removed_logs,
            'removed_results': removed_results,
            'removed_temp': removed_temp,
            'space_saved_mb': space_saved_mb,
            'final_usage': final_usage
        }
        
        self.logger.info(f"Cleanup completed: {results}")
        return results


def main():
    """Main entry point for log cleanup"""
    # Determine base directory
    script_dir = Path(__file__).parent
    base_dir = script_dir.parent
    
    # Create cleanup manager
    cleanup_manager = LogCleanupManager(base_dir)
    
    # Run cleanup
    results = cleanup_manager.run_cleanup()
    
    # Print summary
    print(f"✅ Log cleanup completed:")
    print(f"   Compressed: {results['compressed_files']} files")
    print(f"   Removed logs: {results['removed_logs']} files")
    print(f"   Removed results: {results['removed_results']} files")
    print(f"   Removed temp: {results['removed_temp']} files")
    print(f"   Space saved: {results['space_saved_mb']:.2f} MB")
    print(f"   Current usage: {results['final_usage']['file_count']} files, {results['final_usage']['total_size_mb']:.2f} MB")


if __name__ == "__main__":
    main()