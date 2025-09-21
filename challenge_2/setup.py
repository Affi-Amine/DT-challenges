#!/usr/bin/env python3
"""
Setup Script for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Comprehensive setup script for installing and configuring the cron job system
"""

import os
import sys
import subprocess
import shutil
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import getpass
import tempfile
from datetime import datetime


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class SetupManager:
    """Manages the setup and installation process"""
    
    def __init__(self, project_dir: Optional[str] = None):
        """Initialize setup manager"""
        self.project_dir = Path(project_dir) if project_dir else Path(__file__).parent
        self.scripts_dir = self.project_dir / "scripts"
        self.config_dir = self.project_dir / "config"
        self.logs_dir = self.project_dir / "logs"
        self.tests_dir = self.project_dir / "tests"
        
        # System information
        self.system_info = self._get_system_info()
        
        # Installation status
        self.installation_log = []
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information"""
        try:
            import platform
            return {
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "python_version": platform.python_version(),
                "python_executable": sys.executable
            }
        except Exception as e:
            return {"error": str(e)}
    
    def print_colored(self, message: str, color: str = Colors.ENDC):
        """Print colored message"""
        print(f"{color}{message}{Colors.ENDC}")
    
    def print_header(self, message: str):
        """Print header message"""
        self.print_colored(f"\n{'='*60}", Colors.HEADER)
        self.print_colored(f"{message}", Colors.HEADER + Colors.BOLD)
        self.print_colored(f"{'='*60}", Colors.HEADER)
    
    def print_success(self, message: str):
        """Print success message"""
        self.print_colored(f"✅ {message}", Colors.OKGREEN)
    
    def print_warning(self, message: str):
        """Print warning message"""
        self.print_colored(f"⚠️  {message}", Colors.WARNING)
    
    def print_error(self, message: str):
        """Print error message"""
        self.print_colored(f"❌ {message}", Colors.FAIL)
    
    def print_info(self, message: str):
        """Print info message"""
        self.print_colored(f"ℹ️  {message}", Colors.OKBLUE)
    
    def log_step(self, step: str, success: bool, details: str = ""):
        """Log installation step"""
        self.installation_log.append({
            "timestamp": datetime.now().isoformat(),
            "step": step,
            "success": success,
            "details": details
        })
    
    def run_command(self, command: List[str], capture_output: bool = True, 
                   check: bool = True) -> Tuple[bool, str, str]:
        """Run system command"""
        try:
            result = subprocess.run(
                command,
                capture_output=capture_output,
                text=True,
                check=check
            )
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout or "", e.stderr or str(e)
        except Exception as e:
            return False, "", str(e)
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Check system dependencies"""
        self.print_header("Checking System Dependencies")
        
        dependencies = {
            "python3": False,
            "pip": False,
            "at": False,
            "crontab": False
        }
        
        # Check Python 3
        success, stdout, stderr = self.run_command(["python3", "--version"])
        if success:
            dependencies["python3"] = True
            self.print_success(f"Python 3: {stdout.strip()}")
        else:
            self.print_error("Python 3: Not found")
        
        # Check pip
        success, stdout, stderr = self.run_command(["pip3", "--version"])
        if success:
            dependencies["pip"] = True
            self.print_success(f"pip: {stdout.strip()}")
        else:
            self.print_error("pip: Not found")
        
        # Check 'at' command
        success, stdout, stderr = self.run_command(["which", "at"])
        if success:
            dependencies["at"] = True
            self.print_success("'at' command: Available")
        else:
            self.print_error("'at' command: Not found")
            self.print_info("Install with: brew install at (macOS) or apt-get install at (Linux)")
        
        # Check crontab
        success, stdout, stderr = self.run_command(["which", "crontab"])
        if success:
            dependencies["crontab"] = True
            self.print_success("crontab: Available")
        else:
            self.print_error("crontab: Not found")
        
        return dependencies
    
    def install_python_dependencies(self) -> bool:
        """Install Python dependencies"""
        self.print_header("Installing Python Dependencies")
        
        # Required packages
        packages = [
            "pyyaml>=6.0",
            "requests>=2.25.0",
            "psutil>=5.8.0",
            "python-dotenv>=0.19.0"
        ]
        
        success_count = 0
        
        for package in packages:
            self.print_info(f"Installing {package}...")
            success, stdout, stderr = self.run_command(["pip3", "install", package])
            
            if success:
                self.print_success(f"Installed {package}")
                success_count += 1
                self.log_step(f"install_{package}", True)
            else:
                self.print_error(f"Failed to install {package}: {stderr}")
                self.log_step(f"install_{package}", False, stderr)
        
        return success_count == len(packages)
    
    def create_directory_structure(self) -> bool:
        """Create project directory structure"""
        self.print_header("Creating Directory Structure")
        
        directories = [
            self.scripts_dir,
            self.config_dir,
            self.logs_dir,
            self.tests_dir
        ]
        
        success_count = 0
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                self.print_success(f"Created directory: {directory}")
                success_count += 1
                self.log_step(f"create_dir_{directory.name}", True)
            except Exception as e:
                self.print_error(f"Failed to create directory {directory}: {e}")
                self.log_step(f"create_dir_{directory.name}", False, str(e))
        
        return success_count == len(directories)
    
    def setup_configuration(self) -> bool:
        """Setup configuration files"""
        self.print_header("Setting Up Configuration")
        
        # Check if .env file exists
        env_file = self.config_dir / ".env"
        env_template = self.config_dir / ".env.template"
        
        if not env_file.exists() and env_template.exists():
            self.print_info("Creating .env file from template...")
            try:
                shutil.copy(env_template, env_file)
                self.print_success("Created .env file")
                self.print_warning("Please edit .env file with your credentials")
                self.log_step("create_env_file", True)
            except Exception as e:
                self.print_error(f"Failed to create .env file: {e}")
                self.log_step("create_env_file", False, str(e))
                return False
        
        # Validate configuration
        config_file = self.config_dir / "config.yaml"
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    config = yaml.safe_load(f)
                self.print_success("Configuration file validated")
                self.log_step("validate_config", True)
                return True
            except Exception as e:
                self.print_error(f"Invalid configuration file: {e}")
                self.log_step("validate_config", False, str(e))
                return False
        else:
            self.print_error("Configuration file not found")
            return False
    
    def setup_permissions(self) -> bool:
        """Setup file permissions"""
        self.print_header("Setting Up File Permissions")
        
        # Make scripts executable
        script_files = [
            self.scripts_dir / "daily_scheduler.py",
            self.scripts_dir / "execution_wrapper.py",
            self.scripts_dir / "target_script.py"
        ]
        
        success_count = 0
        
        for script_file in script_files:
            if script_file.exists():
                try:
                    script_file.chmod(0o755)
                    self.print_success(f"Set executable permission: {script_file.name}")
                    success_count += 1
                    self.log_step(f"chmod_{script_file.name}", True)
                except Exception as e:
                    self.print_error(f"Failed to set permission for {script_file.name}: {e}")
                    self.log_step(f"chmod_{script_file.name}", False, str(e))
            else:
                self.print_warning(f"Script file not found: {script_file.name}")
        
        # Set secure permissions for config files
        config_files = [
            self.config_dir / ".env",
            self.config_dir / "config.yaml"
        ]
        
        for config_file in config_files:
            if config_file.exists():
                try:
                    config_file.chmod(0o600)
                    self.print_success(f"Set secure permission: {config_file.name}")
                    success_count += 1
                    self.log_step(f"secure_{config_file.name}", True)
                except Exception as e:
                    self.print_error(f"Failed to secure {config_file.name}: {e}")
                    self.log_step(f"secure_{config_file.name}", False, str(e))
        
        return success_count > 0
    
    def test_system(self) -> bool:
        """Test the system components"""
        self.print_header("Testing System Components")
        
        # Test configuration loading
        try:
            sys.path.insert(0, str(self.scripts_dir))
            from config_manager import ConfigurationManager
            
            config = ConfigurationManager()
            self.print_success("Configuration manager: OK")
            self.log_step("test_config_manager", True)
        except Exception as e:
            self.print_error(f"Configuration manager test failed: {e}")
            self.log_step("test_config_manager", False, str(e))
            return False
        
        # Test logging system
        try:
            from logging_system import setup_logging
            
            logger = setup_logging(config)
            logger.log_info("Test log message")
            self.print_success("Logging system: OK")
            self.log_step("test_logging_system", True)
        except Exception as e:
            self.print_error(f"Logging system test failed: {e}")
            self.log_step("test_logging_system", False, str(e))
            return False
        
        # Test notification system
        try:
            from notification_system import NotificationManager
            
            notifier = NotificationManager(self.project_dir)
            self.print_success("Notification system: OK")
            self.log_step("test_notification_system", True)
        except Exception as e:
            self.print_error(f"Notification system test failed: {e}")
            self.log_step("test_notification_system", False, str(e))
            return False
        
        return True
    
    def create_cron_job(self, schedule_time: str = "0 6 * * *") -> bool:
        """Create cron job entry"""
        self.print_header("Setting Up Cron Job")
        
        # Create cron job command
        scheduler_script = self.scripts_dir / "daily_scheduler.py"
        cron_command = f"{sys.executable} {scheduler_script}"
        cron_entry = f"{schedule_time} {cron_command}"
        
        self.print_info(f"Cron entry: {cron_entry}")
        
        # Ask user for confirmation
        response = input(f"\nAdd this cron job? (y/N): ").strip().lower()
        
        if response != 'y':
            self.print_info("Skipping cron job creation")
            return True
        
        try:
            # Get current crontab
            success, current_crontab, stderr = self.run_command(["crontab", "-l"], check=False)
            
            if not success and "no crontab" not in stderr.lower():
                self.print_error(f"Failed to read crontab: {stderr}")
                return False
            
            # Check if entry already exists
            if success and cron_command in current_crontab:
                self.print_warning("Cron job already exists")
                return True
            
            # Add new entry
            new_crontab = current_crontab + f"\n{cron_entry}\n" if success else f"{cron_entry}\n"
            
            # Write new crontab
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
                f.write(new_crontab)
                temp_file = f.name
            
            success, stdout, stderr = self.run_command(["crontab", temp_file])
            
            # Clean up temp file
            os.unlink(temp_file)
            
            if success:
                self.print_success("Cron job created successfully")
                self.log_step("create_cron_job", True)
                return True
            else:
                self.print_error(f"Failed to create cron job: {stderr}")
                self.log_step("create_cron_job", False, stderr)
                return False
                
        except Exception as e:
            self.print_error(f"Error creating cron job: {e}")
            self.log_step("create_cron_job", False, str(e))
            return False
    
    def create_requirements_file(self) -> bool:
        """Create requirements.txt file"""
        self.print_header("Creating Requirements File")
        
        requirements = [
            "pyyaml>=6.0",
            "requests>=2.25.0",
            "psutil>=5.8.0",
            "python-dotenv>=0.19.0"
        ]
        
        requirements_file = self.project_dir / "requirements.txt"
        
        try:
            with open(requirements_file, 'w') as f:
                f.write('\n'.join(requirements) + '\n')
            
            self.print_success("Created requirements.txt")
            self.log_step("create_requirements", True)
            return True
        except Exception as e:
            self.print_error(f"Failed to create requirements.txt: {e}")
            self.log_step("create_requirements", False, str(e))
            return False
    
    def create_readme(self) -> bool:
        """Create README file"""
        self.print_header("Creating README")
        
        readme_content = f"""# Challenge 2: Simple Cron Job System

## Overview
This is a comprehensive cron job system that executes a target script 10 times daily at random intervals with extensive logging and iPhone notifications.

## Installation
Run the setup script:
```bash
python3 setup.py --install
```

## Configuration
1. Copy `.env.template` to `.env` and fill in your credentials
2. Modify `config/config.yaml` as needed

## Usage
The system will automatically run via cron job. To manually test:
```bash
python3 scripts/daily_scheduler.py
```

## System Information
- Installation Date: {datetime.now().isoformat()}
- Python Version: {self.system_info.get('python_version', 'Unknown')}
- System: {self.system_info.get('system', 'Unknown')} {self.system_info.get('release', '')}

## Components
- `daily_scheduler.py`: Main scheduler that generates random execution times
- `execution_wrapper.py`: Handles script execution with logging and monitoring
- `target_script.py`: Sample script that demonstrates various scenarios
- `notification_system.py`: Handles Pushover and email notifications
- `config_manager.py`: Configuration management system
- `logging_system.py`: Comprehensive logging with rotation and cleanup

## Logs
Logs are stored in the `logs/` directory with automatic rotation and cleanup.

## Support
For issues or questions, refer to the SOLUTION_DESIGN_PROCESS.md document.
"""
        
        readme_file = self.project_dir / "README.md"
        
        try:
            with open(readme_file, 'w') as f:
                f.write(readme_content)
            
            self.print_success("Created README.md")
            self.log_step("create_readme", True)
            return True
        except Exception as e:
            self.print_error(f"Failed to create README.md: {e}")
            self.log_step("create_readme", False, str(e))
            return False
    
    def save_installation_log(self) -> bool:
        """Save installation log"""
        log_file = self.project_dir / "installation_log.json"
        
        try:
            with open(log_file, 'w') as f:
                json.dump({
                    "installation_date": datetime.now().isoformat(),
                    "system_info": self.system_info,
                    "steps": self.installation_log
                }, f, indent=2)
            
            self.print_success(f"Installation log saved: {log_file}")
            return True
        except Exception as e:
            self.print_error(f"Failed to save installation log: {e}")
            return False
    
    def run_full_installation(self, create_cron: bool = True) -> bool:
        """Run full installation process"""
        self.print_header("Challenge 2: Simple Cron Job - Installation")
        
        # Check dependencies
        deps = self.check_dependencies()
        if not all(deps.values()):
            self.print_error("Missing dependencies. Please install them and try again.")
            return False
        
        # Installation steps
        steps = [
            ("Installing Python dependencies", self.install_python_dependencies),
            ("Creating directory structure", self.create_directory_structure),
            ("Setting up configuration", self.setup_configuration),
            ("Setting up permissions", self.setup_permissions),
            ("Testing system components", self.test_system),
            ("Creating requirements file", self.create_requirements_file),
            ("Creating README", self.create_readme)
        ]
        
        # Add cron job step if requested
        if create_cron:
            steps.append(("Creating cron job", lambda: self.create_cron_job()))
        
        # Execute steps
        success_count = 0
        for step_name, step_func in steps:
            self.print_info(f"Executing: {step_name}")
            if step_func():
                success_count += 1
            else:
                self.print_error(f"Failed: {step_name}")
        
        # Save installation log
        self.save_installation_log()
        
        # Final status
        total_steps = len(steps)
        if success_count == total_steps:
            self.print_header("Installation Completed Successfully!")
            self.print_success(f"All {total_steps} steps completed successfully")
            
            # Next steps
            self.print_info("\nNext steps:")
            self.print_info("1. Edit config/.env with your notification credentials")
            self.print_info("2. Review config/config.yaml settings")
            self.print_info("3. Test the system: python3 scripts/daily_scheduler.py")
            
            return True
        else:
            self.print_header("Installation Completed with Issues")
            self.print_warning(f"{success_count}/{total_steps} steps completed successfully")
            self.print_info("Check installation_log.json for details")
            return False


def main():
    """Main setup function"""
    parser = argparse.ArgumentParser(description="Setup Challenge 2: Simple Cron Job")
    parser.add_argument("--install", action="store_true", help="Run full installation")
    parser.add_argument("--no-cron", action="store_true", help="Skip cron job creation")
    parser.add_argument("--test", action="store_true", help="Test system components only")
    parser.add_argument("--deps", action="store_true", help="Check dependencies only")
    parser.add_argument("--project-dir", help="Project directory path")
    
    args = parser.parse_args()
    
    # Initialize setup manager
    setup_manager = SetupManager(args.project_dir)
    
    if args.deps:
        # Check dependencies only
        deps = setup_manager.check_dependencies()
        sys.exit(0 if all(deps.values()) else 1)
    
    elif args.test:
        # Test system components only
        success = setup_manager.test_system()
        sys.exit(0 if success else 1)
    
    elif args.install:
        # Run full installation
        success = setup_manager.run_full_installation(create_cron=not args.no_cron)
        sys.exit(0 if success else 1)
    
    else:
        # Show help
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()