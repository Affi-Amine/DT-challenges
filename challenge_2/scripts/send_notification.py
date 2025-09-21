#!/usr/bin/env python3
"""
Notification Sender for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Standalone script for sending notifications from any component
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add the scripts directory to the path to import notification_system
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

try:
    from notification_system import NotificationManager, NotificationConfig
except ImportError as e:
    print(f"Failed to import notification system: {e}")
    sys.exit(1)

class NotificationSender:
    """Standalone notification sender"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.logs_dir = self.base_dir / "logs"
        
        # Ensure directories exist
        self.logs_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging for notification sender"""
        log_file = self.logs_dir / f"notifications_{datetime.now().strftime('%Y%m%d')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def send_notification(self, message: str, priority: str = "normal", 
                         notification_type: str = "info") -> bool:
        """Send a notification using the notification system"""
        try:
            self.logger.info(f"Sending {priority} notification: {message}")
            
            config_dir = self.base_dir / "config"
            if not config_dir.exists():
                self.logger.error(f"Configuration directory not found: {config_dir}")
                return False
                
            notification_manager = NotificationManager(str(self.base_dir))
            
            # Adapt standalone notification to existing execution notification system
            class MockExecutionResult:
                def __init__(self, message, priority, notification_type):
                    self.session_id = f"notification_{datetime.now().strftime('%H%M%S')}"
                    self.start_time = datetime.now()
                    self.end_time = datetime.now()
                    self.duration = 0.1
                    self.exit_code = 0
                    self.success = notification_type != "error"
                    self.stdout = message
                    self.stderr = ""
                    self.error_message = "" if self.success else message
                    self.peak_memory_mb = 10.0
                    self.cpu_percent = 5.0
                    self.output_lines = len(message.split('\n'))
                    self.warnings = 1 if notification_type == "warning" else 0
                    self.errors = 1 if notification_type == "error" else 0
            
            # Create mock execution result
            mock_result = MockExecutionResult(message, priority, notification_type)
            
            # Send notification
            results = notification_manager.send_execution_notification(mock_result)
            success = any(result.get("success", False) for result in results.values() if isinstance(result, dict))
            
            if success:
                self.logger.info("Notification sent successfully")
            else:
                self.logger.error("Failed to send notification")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Exception sending notification: {e}")
            return False
            
    def send_system_alert(self, alert_type: str, details: str) -> bool:
        """Send a system alert with predefined formatting"""
        try:
            alert_messages = {
                'scheduler_failure': f"🚨 SCHEDULER FAILURE: {details}",
                'execution_failure': f"❌ EXECUTION FAILURE: {details}",
                'health_warning': f"⚠️ HEALTH WARNING: {details}",
                'recovery_success': f"✅ RECOVERY SUCCESS: {details}",
                'system_startup': f"🚀 SYSTEM STARTUP: {details}",
                'system_shutdown': f"🛑 SYSTEM SHUTDOWN: {details}"
            }
            
            message = alert_messages.get(alert_type, f"SYSTEM ALERT: {details}")
            priority = "high" if alert_type in ['scheduler_failure', 'execution_failure'] else "normal"
            
            return self.send_notification(message, priority, "alert")
            
        except Exception as e:
            self.logger.error(f"Failed to send system alert: {e}")
            return False


def main():
    """Main entry point for notification sender"""
    parser = argparse.ArgumentParser(description="Send notifications via DiploTools notification system")
    parser.add_argument('--message', type=str, required=True,
                       help='Message to send')
    parser.add_argument('--priority', type=str, choices=['low', 'normal', 'high'], 
                       default='normal', help='Notification priority')
    parser.add_argument('--type', type=str, choices=['info', 'warning', 'error', 'alert'], 
                       default='info', help='Notification type')
    parser.add_argument('--alert-type', type=str, 
                       choices=['scheduler_failure', 'execution_failure', 'health_warning', 
                               'recovery_success', 'system_startup', 'system_shutdown'],
                       help='Send a predefined system alert')
    parser.add_argument('--base-dir', type=str,
                       help='Base directory (defaults to parent of script directory)')
    
    args = parser.parse_args()
    
    # Determine base directory
    if args.base_dir:
        base_dir = Path(args.base_dir)
    else:
        script_dir = Path(__file__).parent
        base_dir = script_dir.parent
        
    # Create notification sender
    sender = NotificationSender(base_dir)
    
    # Send notification
    if args.alert_type:
        success = sender.send_system_alert(args.alert_type, args.message)
    else:
        success = sender.send_notification(args.message, args.priority, args.type)
        
    if success:
        print("✅ Notification sent successfully")
    else:
        print("❌ Failed to send notification")
        sys.exit(1)


if __name__ == "__main__":
    main()