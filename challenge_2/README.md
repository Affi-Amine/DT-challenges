# Challenge 2: Simple Cron Job System

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
- Installation Date: 2025-09-18T09:55:54.960850
- Python Version: 3.13.2
- System: Darwin 23.5.0

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
