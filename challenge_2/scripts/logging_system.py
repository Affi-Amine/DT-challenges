#!/usr/bin/env python3
"""
Logging System for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Comprehensive logging system with rotation, cleanup, and structured logging
"""

import os
import sys
import logging
import logging.handlers
import json
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
import threading
import time
import traceback


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger_name: str
    message: str
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    execution_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    exception: Optional[str] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Create structured log entry
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            logger_name=record.name,
            message=record.getMessage(),
            module=record.module,
            function=record.funcName,
            line_number=record.lineno,
            thread_id=record.thread,
            process_id=record.process,
            execution_id=getattr(record, 'execution_id', None),
            context=getattr(record, 'context', None) if self.include_context else None,
            exception=self.formatException(record.exc_info) if record.exc_info else None
        )
        
        # Convert to JSON
        return json.dumps(asdict(log_entry), ensure_ascii=False)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for better readability"""
    
    # Color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        # Add color to level name
        level_color = self.COLORS.get(record.levelname, '')
        reset_color = self.COLORS['RESET']
        
        # Create colored level name
        colored_level = f"{level_color}{record.levelname}{reset_color}"
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Format message
        message = record.getMessage()
        
        # Add execution ID if present
        execution_id = getattr(record, 'execution_id', None)
        execution_part = f" [{execution_id}]" if execution_id else ""
        
        # Format final message
        formatted = f"{timestamp} {colored_level:20} {record.name:15} {message}{execution_part}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class LogRotationHandler(logging.handlers.TimedRotatingFileHandler):
    """Custom log rotation handler with compression and cleanup"""
    
    def __init__(self, filename: str, when: str = 'midnight', interval: int = 1, 
                 backup_count: int = 30, compress: bool = True, **kwargs):
        super().__init__(filename, when, interval, backupCount=backup_count, **kwargs)
        self.compress = compress
    
    def doRollover(self):
        """Perform log rotation with compression"""
        super().doRollover()
        
        if self.compress:
            self._compress_old_logs()
    
    def _compress_old_logs(self):
        """Compress old log files"""
        log_dir = Path(self.baseFilename).parent
        log_name = Path(self.baseFilename).stem
        
        # Find uncompressed log files
        for log_file in log_dir.glob(f"{log_name}.*"):
            if log_file.suffix not in ['.gz', '.log']:
                try:
                    # Compress the file
                    compressed_file = log_file.with_suffix(log_file.suffix + '.gz')
                    with open(log_file, 'rb') as f_in:
                        with gzip.open(compressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    # Remove original file
                    log_file.unlink()
                    
                except Exception as e:
                    print(f"Error compressing log file {log_file}: {e}")


class LogCleanupManager:
    """Manages log file cleanup and maintenance"""
    
    def __init__(self, log_directory: str, retention_days: int = 30):
        self.log_directory = Path(log_directory)
        self.retention_days = retention_days
        self.cleanup_thread = None
        self.stop_cleanup = threading.Event()
    
    def start_cleanup_scheduler(self, interval_hours: int = 24):
        """Start automatic log cleanup scheduler"""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        self.stop_cleanup.clear()
        self.cleanup_thread = threading.Thread(
            target=self._cleanup_scheduler,
            args=(interval_hours,),
            daemon=True
        )
        self.cleanup_thread.start()
    
    def stop_cleanup_scheduler(self):
        """Stop automatic log cleanup scheduler"""
        if self.cleanup_thread:
            self.stop_cleanup.set()
            self.cleanup_thread.join(timeout=5)
    
    def _cleanup_scheduler(self, interval_hours: int):
        """Background cleanup scheduler"""
        while not self.stop_cleanup.wait(interval_hours * 3600):
            try:
                self.cleanup_old_logs()
            except Exception as e:
                print(f"Error during log cleanup: {e}")
    
    def cleanup_old_logs(self) -> Dict[str, int]:
        """Clean up old log files"""
        if not self.log_directory.exists():
            return {"deleted": 0, "errors": 0}
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        deleted_count = 0
        error_count = 0
        
        # Find old log files
        for log_file in self.log_directory.rglob("*.log*"):
            try:
                # Check file modification time
                file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    
            except Exception as e:
                error_count += 1
                print(f"Error deleting log file {log_file}: {e}")
        
        return {"deleted": deleted_count, "errors": error_count}
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get log directory statistics"""
        if not self.log_directory.exists():
            return {"total_files": 0, "total_size": 0, "oldest_file": None, "newest_file": None}
        
        log_files = list(self.log_directory.rglob("*.log*"))
        
        if not log_files:
            return {"total_files": 0, "total_size": 0, "oldest_file": None, "newest_file": None}
        
        total_size = sum(f.stat().st_size for f in log_files)
        file_times = [(f, f.stat().st_mtime) for f in log_files]
        
        oldest_file = min(file_times, key=lambda x: x[1])
        newest_file = max(file_times, key=lambda x: x[1])
        
        return {
            "total_files": len(log_files),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": {
                "name": oldest_file[0].name,
                "date": datetime.fromtimestamp(oldest_file[1]).isoformat()
            },
            "newest_file": {
                "name": newest_file[0].name,
                "date": datetime.fromtimestamp(newest_file[1]).isoformat()
            }
        }


class CronJobLogger:
    """Main logging system for the cron job"""
    
    def __init__(self, config_manager=None):
        """Initialize the logging system"""
        self.config = config_manager
        self.cleanup_manager = None
        self.loggers = {}
        self.execution_id = None
        
        # Setup logging
        self._setup_logging()
        
        # Start cleanup manager
        if self.config:
            self.cleanup_manager = LogCleanupManager(
                self.config.logging_config.directory,
                self.config.logging_config.backup_count
            )
            self.cleanup_manager.start_cleanup_scheduler()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        # Get configuration
        if self.config:
            log_level = getattr(logging, self.config.logging_config.level.upper())
            log_dir = Path(self.config.logging_config.directory)
            log_format = self.config.logging_config.format
            date_format = self.config.logging_config.date_format
            console_logging = self.config.logging_config.console_logging
            file_logging = self.config.logging_config.file_logging
            max_file_size = self.config.logging_config.max_file_size * 1024 * 1024  # Convert MB to bytes
            backup_count = self.config.logging_config.backup_count
        else:
            # Default configuration
            log_level = logging.INFO
            log_dir = Path("logs")
            log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            date_format = "%Y-%m-%d %H:%M:%S"
            console_logging = True
            file_logging = True
            max_file_size = 10 * 1024 * 1024  # 10MB
            backup_count = 30
        
        # Create log directory
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            
            if self.config and self.config.is_development():
                console_formatter = ColoredConsoleFormatter()
            else:
                console_formatter = logging.Formatter(log_format, date_format)
            
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if file_logging:
            log_file = log_dir / "cron_job.log"
            
            # Use rotating file handler
            file_handler = LogRotationHandler(
                str(log_file),
                when='midnight',
                interval=1,
                backup_count=backup_count,
                compress=True
            )
            file_handler.setLevel(log_level)
            
            # Use structured formatter for file logging
            if self.config and self.config.is_development():
                file_formatter = logging.Formatter(log_format, date_format)
            else:
                file_formatter = StructuredFormatter()
            
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        
        # Create main logger
        self.logger = logging.getLogger("cron_job")
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(f"cron_job.{name}")
        return self.loggers[name]
    
    def set_execution_id(self, execution_id: str):
        """Set execution ID for context"""
        self.execution_id = execution_id
    
    def log_with_context(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, 
                        logger_name: Optional[str] = None):
        """Log message with context"""
        logger = self.get_logger(logger_name) if logger_name else self.logger
        
        # Create log record
        record = logger.makeRecord(
            logger.name, level, __file__, 0, message, (), None
        )
        
        # Add context
        if context:
            record.context = context
        
        if self.execution_id:
            record.execution_id = self.execution_id
        
        # Log the record
        logger.handle(record)
    
    def log_execution_start(self, script_path: str, execution_id: str):
        """Log execution start"""
        self.set_execution_id(execution_id)
        self.log_with_context(
            logging.INFO,
            f"Starting script execution: {script_path}",
            {"event": "execution_start", "script_path": script_path, "execution_id": execution_id}
        )
    
    def log_execution_end(self, execution_id: str, success: bool, duration: float, 
                         exit_code: Optional[int] = None):
        """Log execution end"""
        self.log_with_context(
            logging.INFO if success else logging.ERROR,
            f"Script execution {'completed' if success else 'failed'} in {duration:.2f}s",
            {
                "event": "execution_end",
                "execution_id": execution_id,
                "success": success,
                "duration": duration,
                "exit_code": exit_code
            }
        )
    
    def log_error(self, message: str, exception: Optional[Exception] = None, 
                  context: Optional[Dict[str, Any]] = None):
        """Log error with optional exception"""
        if exception:
            context = context or {}
            context.update({
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "traceback": traceback.format_exc()
            })
        
        self.log_with_context(logging.ERROR, message, context)
    
    def log_warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log warning"""
        self.log_with_context(logging.WARNING, message, context)
    
    def log_info(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log info"""
        self.log_with_context(logging.INFO, message, context)
    
    def log_debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Log debug"""
        self.log_with_context(logging.DEBUG, message, context)
    
    def get_log_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        stats = {"cleanup_manager": None}
        
        if self.cleanup_manager:
            stats["cleanup_manager"] = self.cleanup_manager.get_log_statistics()
        
        return stats
    
    def cleanup_logs(self) -> Dict[str, int]:
        """Manually trigger log cleanup"""
        if self.cleanup_manager:
            return self.cleanup_manager.cleanup_old_logs()
        return {"deleted": 0, "errors": 0}
    
    def shutdown(self):
        """Shutdown logging system"""
        if self.cleanup_manager:
            self.cleanup_manager.stop_cleanup_scheduler()
        
        # Shutdown all handlers
        logging.shutdown()


# Global logger instance
_logger_instance = None


def get_logger(config_manager=None) -> CronJobLogger:
    """Get the global logger instance"""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = CronJobLogger(config_manager)
    return _logger_instance


def setup_logging(config_manager=None) -> CronJobLogger:
    """Setup and return the global logger instance"""
    global _logger_instance
    _logger_instance = CronJobLogger(config_manager)
    return _logger_instance


if __name__ == "__main__":
    # Test logging system
    from config_manager import ConfigurationManager
    
    # Setup configuration
    config = ConfigurationManager()
    
    # Setup logging
    logger_system = setup_logging(config)
    
    # Test logging
    logger = logger_system.get_logger("test")
    
    logger_system.log_execution_start("/test/script.py", "test-123")
    logger_system.log_info("This is a test info message", {"test": True})
    logger_system.log_warning("This is a test warning")
    logger_system.log_error("This is a test error", context={"error_code": 500})
    
    try:
        raise ValueError("Test exception")
    except Exception as e:
        logger_system.log_error("Exception occurred", e)
    
    logger_system.log_execution_end("test-123", True, 1.5, 0)
    
    # Get statistics
    stats = logger_system.get_log_statistics()
    print(f"Log statistics: {json.dumps(stats, indent=2)}")
    
    # Cleanup
    logger_system.shutdown()