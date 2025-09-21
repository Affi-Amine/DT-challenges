#!/usr/bin/env python3
"""
Configuration Manager for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Handles configuration loading, validation, and environment variable integration
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
import secrets


@dataclass
class NotificationConfig:
    """Configuration for notification system"""
    enabled: bool = True
    channels: List[str] = field(default_factory=lambda: ["pushover", "email"])
    
    # Pushover settings
    pushover_enabled: bool = True
    pushover_api_token: str = ""
    pushover_user_key: str = ""
    pushover_priority: int = 0
    pushover_sound: str = "pushover"
    
    # Email settings
    email_enabled: bool = True
    email_smtp_server: str = "smtp.gmail.com"
    email_smtp_port: int = 587
    email_use_tls: bool = True
    email_username: str = ""
    email_password: str = ""
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # Triggers
    on_success: bool = False
    on_warning: bool = True
    on_error: bool = True
    on_critical: bool = True
    on_start: bool = False
    on_completion: bool = True
    
    # Rate limiting
    rate_limit_enabled: bool = True
    max_notifications_per_hour: int = 10
    cooldown_period: int = 300


@dataclass
class LoggingConfig:
    """Configuration for logging system"""
    level: str = "INFO"
    directory: str = ""
    filename_pattern: str = "cron_job_{date}.log"
    max_file_size: int = 10
    backup_count: int = 30
    rotation: str = "daily"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    console_logging: bool = True
    file_logging: bool = True


@dataclass
class SchedulingConfig:
    """Configuration for scheduling system"""
    executions_per_day: int = 10
    start_time: str = "06:00"
    end_time: str = "22:00"
    min_interval: int = 30
    max_retry_attempts: int = 3
    lock_timeout: int = 300


@dataclass
class TargetScriptConfig:
    """Configuration for target script execution"""
    path: str = ""
    python_interpreter: str = "python3"
    timeout: int = 300
    working_directory: str = ""
    environment_variables: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemConfig:
    """Main system configuration"""
    name: str = "Simple Cron Job System"
    version: str = "1.0.0"
    environment: str = "production"
    timezone: str = "UTC"
    debug: bool = False


class ConfigurationManager:
    """Manages configuration loading and validation"""
    
    def __init__(self, config_path: Optional[str] = None, env_file: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_path: Path to YAML configuration file
            env_file: Path to .env file
        """
        self.logger = logging.getLogger(__name__)
        
        # Set default paths
        self.base_dir = Path(__file__).parent.parent
        self.config_path = Path(config_path) if config_path else self.base_dir / "config" / "config.yaml"
        self.env_file = Path(env_file) if env_file else self.base_dir / "config" / ".env"
        
        # Configuration objects
        self.system = SystemConfig()
        self.scheduling = SchedulingConfig()
        self.target_script = TargetScriptConfig()
        self.logging_config = LoggingConfig()
        self.notifications = NotificationConfig()
        
        # Load configuration
        self._load_environment_variables()
        self._load_yaml_config()
        self._validate_configuration()
        self._setup_defaults()
    
    def _load_environment_variables(self):
        """Load environment variables from .env file and system"""
        # Load from .env file if it exists
        if self.env_file.exists():
            self._load_env_file()
        
        # Override with system environment variables
        self._load_system_env()
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        try:
            with open(self.env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        except Exception as e:
            self.logger.warning(f"Could not load .env file: {e}")
    
    def _load_system_env(self):
        """Load configuration from system environment variables"""
        # System configuration
        self.system.environment = os.getenv('ENVIRONMENT', self.system.environment)
        self.system.debug = os.getenv('DEBUG', '').lower() == 'true'
        
        # Logging configuration
        self.logging_config.level = os.getenv('LOG_LEVEL', self.logging_config.level)
        
        # Notification credentials
        self.notifications.pushover_api_token = os.getenv('PUSHOVER_API_TOKEN', '')
        self.notifications.pushover_user_key = os.getenv('PUSHOVER_USER_KEY', '')
        self.notifications.email_username = os.getenv('EMAIL_USERNAME', '')
        self.notifications.email_password = os.getenv('EMAIL_PASSWORD', '')
        self.notifications.email_from = os.getenv('EMAIL_FROM', '')
        
        # Email recipients
        email_to = os.getenv('EMAIL_TO', '')
        if email_to:
            self.notifications.email_to = [addr.strip() for addr in email_to.split(',')]
        
        # Scheduling overrides
        if os.getenv('EXECUTIONS_PER_DAY'):
            self.scheduling.executions_per_day = int(os.getenv('EXECUTIONS_PER_DAY'))
        
        if os.getenv('SCHEDULE_START_TIME'):
            self.scheduling.start_time = os.getenv('SCHEDULE_START_TIME')
        
        if os.getenv('SCHEDULE_END_TIME'):
            self.scheduling.end_time = os.getenv('SCHEDULE_END_TIME')
    
    def _load_yaml_config(self):
        """Load configuration from YAML file"""
        if not self.config_path.exists():
            self.logger.warning(f"Configuration file not found: {self.config_path}")
            return
        
        try:
            with open(self.config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Load system configuration
            if 'system' in config_data:
                sys_config = config_data['system']
                self.system.name = sys_config.get('name', self.system.name)
                self.system.version = sys_config.get('version', self.system.version)
                if not os.getenv('ENVIRONMENT'):  # Don't override env var
                    self.system.environment = sys_config.get('environment', self.system.environment)
                self.system.timezone = sys_config.get('timezone', self.system.timezone)
            
            # Load scheduling configuration
            if 'scheduling' in config_data:
                sched_config = config_data['scheduling']
                if not os.getenv('EXECUTIONS_PER_DAY'):
                    self.scheduling.executions_per_day = sched_config.get('executions_per_day', self.scheduling.executions_per_day)
                
                time_window = sched_config.get('time_window', {})
                if not os.getenv('SCHEDULE_START_TIME'):
                    self.scheduling.start_time = time_window.get('start', self.scheduling.start_time)
                if not os.getenv('SCHEDULE_END_TIME'):
                    self.scheduling.end_time = time_window.get('end', self.scheduling.end_time)
                
                self.scheduling.min_interval = sched_config.get('min_interval', self.scheduling.min_interval)
                self.scheduling.max_retry_attempts = sched_config.get('max_retry_attempts', self.scheduling.max_retry_attempts)
                self.scheduling.lock_timeout = sched_config.get('lock_timeout', self.scheduling.lock_timeout)
            
            # Load target script configuration
            if 'target_script' in config_data:
                script_config = config_data['target_script']
                self.target_script.path = script_config.get('path', self.target_script.path)
                self.target_script.python_interpreter = script_config.get('python_interpreter', self.target_script.python_interpreter)
                self.target_script.timeout = script_config.get('timeout', self.target_script.timeout)
                self.target_script.working_directory = script_config.get('working_directory', self.target_script.working_directory)
                self.target_script.environment_variables = script_config.get('environment_variables', {})
            
            # Load logging configuration
            if 'logging' in config_data:
                log_config = config_data['logging']
                if not os.getenv('LOG_LEVEL'):
                    self.logging_config.level = log_config.get('level', self.logging_config.level)
                
                self.logging_config.directory = log_config.get('directory', self.logging_config.directory)
                self.logging_config.filename_pattern = log_config.get('filename_pattern', self.logging_config.filename_pattern)
                self.logging_config.max_file_size = log_config.get('max_file_size', self.logging_config.max_file_size)
                self.logging_config.backup_count = log_config.get('backup_count', self.logging_config.backup_count)
                self.logging_config.rotation = log_config.get('rotation', self.logging_config.rotation)
                self.logging_config.format = log_config.get('format', self.logging_config.format)
                self.logging_config.date_format = log_config.get('date_format', self.logging_config.date_format)
                self.logging_config.console_logging = log_config.get('console_logging', self.logging_config.console_logging)
                self.logging_config.file_logging = log_config.get('file_logging', self.logging_config.file_logging)
            
            # Load notification configuration
            if 'notifications' in config_data:
                notif_config = config_data['notifications']
                self.notifications.enabled = notif_config.get('enabled', self.notifications.enabled)
                self.notifications.channels = notif_config.get('channels', self.notifications.channels)
                
                # Pushover settings
                pushover_config = notif_config.get('pushover', {})
                self.notifications.pushover_enabled = pushover_config.get('enabled', self.notifications.pushover_enabled)
                self.notifications.pushover_priority = pushover_config.get('priority', self.notifications.pushover_priority)
                self.notifications.pushover_sound = pushover_config.get('sound', self.notifications.pushover_sound)
                
                # Email settings
                email_config = notif_config.get('email', {})
                self.notifications.email_enabled = email_config.get('enabled', self.notifications.email_enabled)
                self.notifications.email_smtp_server = email_config.get('smtp_server', self.notifications.email_smtp_server)
                self.notifications.email_smtp_port = email_config.get('smtp_port', self.notifications.email_smtp_port)
                self.notifications.email_use_tls = email_config.get('use_tls', self.notifications.email_use_tls)
                
                # Triggers
                triggers = notif_config.get('triggers', {})
                self.notifications.on_success = triggers.get('on_success', self.notifications.on_success)
                self.notifications.on_warning = triggers.get('on_warning', self.notifications.on_warning)
                self.notifications.on_error = triggers.get('on_error', self.notifications.on_error)
                self.notifications.on_critical = triggers.get('on_critical', self.notifications.on_critical)
                self.notifications.on_start = triggers.get('on_start', self.notifications.on_start)
                self.notifications.on_completion = triggers.get('on_completion', self.notifications.on_completion)
                
                # Rate limiting
                rate_limit = notif_config.get('rate_limit', {})
                self.notifications.rate_limit_enabled = rate_limit.get('enabled', self.notifications.rate_limit_enabled)
                self.notifications.max_notifications_per_hour = rate_limit.get('max_notifications_per_hour', self.notifications.max_notifications_per_hour)
                self.notifications.cooldown_period = rate_limit.get('cooldown_period', self.notifications.cooldown_period)
            
        except Exception as e:
            self.logger.error(f"Error loading YAML configuration: {e}")
            raise
    
    def _validate_configuration(self):
        """Validate configuration values"""
        errors = []
        
        # Validate scheduling
        if self.scheduling.executions_per_day <= 0:
            errors.append("executions_per_day must be greater than 0")
        
        if self.scheduling.min_interval <= 0:
            errors.append("min_interval must be greater than 0")
        
        # Validate time format
        try:
            datetime.strptime(self.scheduling.start_time, "%H:%M")
            datetime.strptime(self.scheduling.end_time, "%H:%M")
        except ValueError:
            errors.append("start_time and end_time must be in HH:MM format")
        
        # Validate target script
        if self.target_script.path and not Path(self.target_script.path).exists():
            errors.append(f"Target script not found: {self.target_script.path}")
        
        # Validate notification credentials
        if self.notifications.enabled:
            if 'pushover' in self.notifications.channels:
                if not self.notifications.pushover_api_token or not self.notifications.pushover_user_key:
                    self.logger.warning("Pushover credentials not configured")
            
            if 'email' in self.notifications.channels:
                if not self.notifications.email_username or not self.notifications.email_password:
                    self.logger.warning("Email credentials not configured")
                
                if not self.notifications.email_to:
                    self.logger.warning("No email recipients configured")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def _setup_defaults(self):
        """Setup default values based on environment"""
        # Set default paths if not specified
        if not self.logging_config.directory:
            self.logging_config.directory = str(self.base_dir / "logs")
        
        if not self.target_script.working_directory:
            self.target_script.working_directory = str(self.base_dir)
        
        # Create directories if they don't exist
        Path(self.logging_config.directory).mkdir(parents=True, exist_ok=True)
        
        # Development mode adjustments
        if self.system.environment == 'development':
            self.system.debug = True
            self.logging_config.level = 'DEBUG'
            self.logging_config.console_logging = True
    
    def get_log_file_path(self) -> str:
        """Get the current log file path"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        filename = self.logging_config.filename_pattern.format(date=date_str)
        return str(Path(self.logging_config.directory) / filename)
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.system.environment == 'development'
    
    def is_debug(self) -> bool:
        """Check if debug mode is enabled"""
        return self.system.debug
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'system': {
                'name': self.system.name,
                'version': self.system.version,
                'environment': self.system.environment,
                'timezone': self.system.timezone,
                'debug': self.system.debug
            },
            'scheduling': {
                'executions_per_day': self.scheduling.executions_per_day,
                'start_time': self.scheduling.start_time,
                'end_time': self.scheduling.end_time,
                'min_interval': self.scheduling.min_interval,
                'max_retry_attempts': self.scheduling.max_retry_attempts,
                'lock_timeout': self.scheduling.lock_timeout
            },
            'target_script': {
                'path': self.target_script.path,
                'python_interpreter': self.target_script.python_interpreter,
                'timeout': self.target_script.timeout,
                'working_directory': self.target_script.working_directory,
                'environment_variables': self.target_script.environment_variables
            },
            'logging': {
                'level': self.logging_config.level,
                'directory': self.logging_config.directory,
                'filename_pattern': self.logging_config.filename_pattern,
                'max_file_size': self.logging_config.max_file_size,
                'backup_count': self.logging_config.backup_count,
                'rotation': self.logging_config.rotation,
                'format': self.logging_config.format,
                'date_format': self.logging_config.date_format,
                'console_logging': self.logging_config.console_logging,
                'file_logging': self.logging_config.file_logging
            },
            'notifications': {
                'enabled': self.notifications.enabled,
                'channels': self.notifications.channels,
                'pushover_enabled': self.notifications.pushover_enabled,
                'email_enabled': self.notifications.email_enabled,
                'triggers': {
                    'on_success': self.notifications.on_success,
                    'on_warning': self.notifications.on_warning,
                    'on_error': self.notifications.on_error,
                    'on_critical': self.notifications.on_critical,
                    'on_start': self.notifications.on_start,
                    'on_completion': self.notifications.on_completion
                },
                'rate_limit_enabled': self.notifications.rate_limit_enabled,
                'max_notifications_per_hour': self.notifications.max_notifications_per_hour,
                'cooldown_period': self.notifications.cooldown_period
            }
        }


# Global configuration instance
config = None


def get_config() -> ConfigurationManager:
    """Get the global configuration instance"""
    global config
    if config is None:
        config = ConfigurationManager()
    return config


def reload_config():
    """Reload the global configuration"""
    global config
    config = ConfigurationManager()
    return config


if __name__ == "__main__":
    # Test configuration loading
    config_manager = ConfigurationManager()
    print("Configuration loaded successfully!")
    print(f"Environment: {config_manager.system.environment}")
    print(f"Debug mode: {config_manager.system.debug}")
    print(f"Executions per day: {config_manager.scheduling.executions_per_day}")
    print(f"Log level: {config_manager.logging_config.level}")
    print(f"Notifications enabled: {config_manager.notifications.enabled}")