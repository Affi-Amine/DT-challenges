#!/usr/bin/env python3
"""
Notification System for Challenge 2: Simple Cron Job
Author: Amine Affi
Description: Multi-channel notification system with Pushover primary and email fallback
"""

import os
import sys
import json
import smtplib
import requests
import logging
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time

# Load environment variables from .env file
def load_env_file(env_path):
    """Load environment variables from .env file"""
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: Could not load .env file: {e}")


class NotificationConfig:
    """Configuration management for notifications"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.config_file = self.base_dir / "config" / "notification_config.json"
        
        # Load environment variables from .env file BEFORE loading config
        env_file = self.base_dir / "config" / ".env"
        if env_file.exists():
            load_env_file(env_file)
        
        self.load_config()
        
    def load_config(self):
        """Load notification configuration"""
        default_config = {
            "pushover": {
                "enabled": True,
                "app_token": os.getenv("PUSHOVER_API_TOKEN", ""),
                "user_key": os.getenv("PUSHOVER_USER_KEY", ""),
                "api_url": "https://api.pushover.net/1/messages.json",
                "timeout": 10,
                "retry_attempts": 3
            },
            "email": {
                "enabled": True,
                "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
                "smtp_port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("EMAIL_USERNAME", ""),
                "password": os.getenv("EMAIL_PASSWORD", ""),
                "from_email": os.getenv("FROM_EMAIL", ""),
                "to_email": os.getenv("TO_EMAIL", ""),
                "use_tls": True,
                "timeout": 30
            },
            "notification_settings": {
                "success_notifications": True,
                "failure_notifications": True,
                "include_logs": True,
                "max_log_lines": 50,
                "rate_limit_minutes": 5
            }
        }
        
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                # Merge with defaults, but preserve environment variables
                self.config = {**default_config, **loaded_config}
                # Override with environment variables if they exist
                if os.getenv("PUSHOVER_API_TOKEN"):
                    self.config["pushover"]["app_token"] = os.getenv("PUSHOVER_API_TOKEN")
                if os.getenv("PUSHOVER_USER_KEY"):
                    self.config["pushover"]["user_key"] = os.getenv("PUSHOVER_USER_KEY")
                if os.getenv("EMAIL_USERNAME"):
                    self.config["email"]["username"] = os.getenv("EMAIL_USERNAME")
                if os.getenv("EMAIL_PASSWORD"):
                    self.config["email"]["password"] = os.getenv("EMAIL_PASSWORD")
                if os.getenv("EMAIL_FROM"):
                    self.config["email"]["from_email"] = os.getenv("EMAIL_FROM")
                if os.getenv("EMAIL_TO"):
                    self.config["email"]["to_email"] = os.getenv("EMAIL_TO")
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            print(f"Warning: Failed to load notification config: {e}")
            self.config = default_config
            
    def save_config(self):
        """Save configuration to file"""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save notification config: {e}")
            
    def is_pushover_configured(self):
        """Check if Pushover is properly configured"""
        pushover = self.config["pushover"]
        return (pushover["enabled"] and 
                pushover["app_token"] and 
                pushover["user_key"])
                
    def is_email_configured(self):
        """Check if email is properly configured"""
        email = self.config["email"]
        return (email["enabled"] and 
                email["username"] and 
                email["password"] and 
                email["from_email"] and 
                email["to_email"])


class PushoverNotifier:
    """Handles Pushover notifications"""
    
    def __init__(self, config):
        self.config = config["pushover"]
        self.logger = logging.getLogger(__name__)
        
    def format_message(self, execution_result):
        """Format execution result for Pushover notification"""
        status = "✅ SUCCESS" if execution_result.success else "❌ FAILURE"
        
        message = f"{status}\n"
        message += f"Duration: {execution_result.duration:.2f}s\n"
        message += f"Memory: {execution_result.peak_memory_mb:.1f}MB\n"
        
        if execution_result.success:
            message += f"Output: {execution_result.output_lines} lines\n"
        else:
            message += f"Exit Code: {execution_result.exit_code}\n"
            if execution_result.error_message:
                # Truncate error message for Pushover
                error_msg = execution_result.error_message[:100]
                if len(execution_result.error_message) > 100:
                    error_msg += "..."
                message += f"Error: {error_msg}\n"
                
        message += f"Session: {execution_result.session_id}"
        
        return message
        
    def send_notification(self, execution_result):
        """
        Send notification via Pushover
        
        Args:
            execution_result: ExecutionResult object
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Prepare payload
            payload = {
                "token": self.config["app_token"],
                "user": self.config["user_key"],
                "title": f"Cron Job {execution_result.session_id}",
                "message": self.format_message(execution_result),
                "priority": 2 if not execution_result.success else 0,  # High priority for failures
                "sound": "siren" if not execution_result.success else "success",
                "timestamp": int(execution_result.start_time.timestamp())
            }
            
            # Add URL action for detailed logs
            if hasattr(execution_result, 'log_file_path'):
                payload["url"] = f"file://{execution_result.log_file_path}"
                payload["url_title"] = "View Logs"
                
            # Send request with retries
            for attempt in range(self.config["retry_attempts"]):
                try:
                    response = requests.post(
                        self.config["api_url"],
                        data=payload,
                        timeout=self.config["timeout"]
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == 1:
                            return True, "Pushover notification sent successfully"
                        else:
                            return False, f"Pushover API error: {result.get('errors', 'Unknown error')}"
                    else:
                        return False, f"HTTP {response.status_code}: {response.text}"
                        
                except requests.exceptions.RequestException as e:
                    if attempt < self.config["retry_attempts"] - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
                    return False, f"Network error: {str(e)}"
                    
        except Exception as e:
            return False, f"Pushover notification failed: {str(e)}"


class EmailNotifier:
    """Handles email notifications with detailed reports"""
    
    def __init__(self, config):
        self.config = config["email"]
        self.logger = logging.getLogger(__name__)
        
    def format_html_message(self, execution_result):
        """Format execution result as HTML email"""
        status_color = "#28a745" if execution_result.success else "#dc3545"
        status_text = "SUCCESS ✅" if execution_result.success else "FAILURE ❌"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: {status_color}; color: white; padding: 15px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .metrics {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
                .error {{ background-color: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; }}
                .logs {{ background-color: #f1f3f4; padding: 10px; border-radius: 5px; font-family: monospace; font-size: 12px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>Cron Job Execution Report</h2>
                <p>Status: {status_text}</p>
                <p>Session ID: {execution_result.session_id}</p>
            </div>
            
            <div class="content">
                <div class="metrics">
                    <h3>Execution Metrics</h3>
                    <table>
                        <tr><th>Metric</th><th>Value</th></tr>
                        <tr><td>Start Time</td><td>{execution_result.start_time.strftime('%Y-%m-%d %H:%M:%S UTC')}</td></tr>
                        <tr><td>Duration</td><td>{execution_result.duration:.3f} seconds</td></tr>
                        <tr><td>Exit Code</td><td>{execution_result.exit_code}</td></tr>
                        <tr><td>Peak Memory</td><td>{execution_result.peak_memory_mb:.1f} MB</td></tr>
                        <tr><td>CPU Usage</td><td>{execution_result.cpu_percent:.1f}%</td></tr>
                        <tr><td>Output Lines</td><td>{execution_result.output_lines}</td></tr>
                        <tr><td>Warnings</td><td>{execution_result.warnings}</td></tr>
                        <tr><td>Errors</td><td>{execution_result.errors}</td></tr>
                    </table>
                </div>
        """
        
        # Add error details if present
        if execution_result.error_message:
            html += f"""
                <div class="error">
                    <h3>Error Details</h3>
                    <p>{execution_result.error_message}</p>
                </div>
            """
            
        # Add output samples
        if execution_result.stdout:
            stdout_lines = execution_result.stdout.split('\n')[:20]  # First 20 lines
            html += f"""
                <div class="logs">
                    <h3>Script Output (first 20 lines)</h3>
                    <pre>{'<br>'.join(stdout_lines)}</pre>
                </div>
            """
            
        if execution_result.stderr:
            stderr_lines = execution_result.stderr.split('\n')[:10]  # First 10 error lines
            html += f"""
                <div class="logs">
                    <h3>Error Output</h3>
                    <pre>{'<br>'.join(stderr_lines)}</pre>
                </div>
            """
            
        html += """
            </div>
            <p><small>This is an automated message from the Cron Job Monitoring System.</small></p>
        </body>
        </html>
        """
        
        return html
        
    def send_notification(self, execution_result, attach_logs=True):
        """
        Send detailed email notification
        
        Args:
            execution_result: ExecutionResult object
            attach_logs: Whether to attach log files
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"Cron Job {'Success' if execution_result.success else 'Failure'} - {execution_result.session_id}"
            msg['From'] = self.config['from_email']
            msg['To'] = self.config['to_email']
            msg['Date'] = execution_result.start_time.strftime('%a, %d %b %Y %H:%M:%S +0000')
            
            # Create HTML content
            html_content = self.format_html_message(execution_result)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Attach log file if requested and available
            if attach_logs and hasattr(execution_result, 'log_file_path'):
                try:
                    log_path = Path(execution_result.log_file_path)
                    if log_path.exists():
                        with open(log_path, 'rb') as f:
                            attachment = MIMEBase('application', 'octet-stream')
                            attachment.set_payload(f.read())
                            encoders.encode_base64(attachment)
                            attachment.add_header(
                                'Content-Disposition',
                                f'attachment; filename= {log_path.name}'
                            )
                            msg.attach(attachment)
                except Exception as e:
                    self.logger.warning(f"Failed to attach log file: {e}")
                    
            # Send email
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                if self.config['use_tls']:
                    server.starttls()
                server.login(self.config['username'], self.config['password'])
                server.send_message(msg)
                
            return True, "Email notification sent successfully"
            
        except Exception as e:
            return False, f"Email notification failed: {str(e)}"


class NotificationManager:
    """Main notification manager that coordinates all channels"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.config_manager = NotificationConfig(base_dir)
        
        # Initialize notifiers
        self.pushover = PushoverNotifier(self.config_manager.config)
        self.email = EmailNotifier(self.config_manager.config)
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Rate limiting
        self.last_notification_time = {}
        
    def should_send_notification(self, execution_result):
        """Check if notification should be sent based on settings and rate limiting"""
        settings = self.config_manager.config["notification_settings"]
        
        # Check if notifications are enabled for this result type
        if execution_result.success and not settings["success_notifications"]:
            return False
        if not execution_result.success and not settings["failure_notifications"]:
            return False
            
        # Rate limiting check
        rate_limit_key = "success" if execution_result.success else "failure"
        rate_limit_minutes = settings["rate_limit_minutes"]
        
        if rate_limit_key in self.last_notification_time:
            time_since_last = datetime.now() - self.last_notification_time[rate_limit_key]
            if time_since_last < timedelta(minutes=rate_limit_minutes):
                self.logger.info(f"Rate limiting: skipping {rate_limit_key} notification")
                return False
                
        return True
        
    def send_execution_notification(self, execution_result):
        """
        Send notification about script execution
        
        Args:
            execution_result: ExecutionResult object
            
        Returns:
            dict: Results from all notification channels
        """
        if not self.should_send_notification(execution_result):
            return {"skipped": True, "reason": "Rate limited or disabled"}
            
        results = {}
        
        # Try Pushover first (primary channel)
        if self.config_manager.is_pushover_configured():
            self.logger.info("Sending Pushover notification...")
            success, message = self.pushover.send_notification(execution_result)
            results["pushover"] = {"success": success, "message": message}
            
            if success:
                self.logger.info("✅ Pushover notification sent successfully")
                # Update rate limiting
                rate_limit_key = "success" if execution_result.success else "failure"
                self.last_notification_time[rate_limit_key] = datetime.now()
                return results
            else:
                self.logger.warning(f"❌ Pushover notification failed: {message}")
        else:
            results["pushover"] = {"success": False, "message": "Not configured"}
            self.logger.info("Pushover not configured, skipping...")
            
        # Fallback to email
        if self.config_manager.is_email_configured():
            self.logger.info("Sending email notification (fallback)...")
            success, message = self.email.send_notification(execution_result)
            results["email"] = {"success": success, "message": message}
            
            if success:
                self.logger.info("✅ Email notification sent successfully")
                # Update rate limiting
                rate_limit_key = "success" if execution_result.success else "failure"
                self.last_notification_time[rate_limit_key] = datetime.now()
            else:
                self.logger.warning(f"❌ Email notification failed: {message}")
        else:
            results["email"] = {"success": False, "message": "Not configured"}
            self.logger.warning("Email not configured, no notifications sent!")
            
        return results
        
    def test_notifications(self):
        """Test all configured notification channels"""
        print("🧪 Testing notification channels...")
        
        # Create a test execution result
        from execution_wrapper import ExecutionResult
        test_result = ExecutionResult()
        test_result.session_id = "TEST"
        test_result.start_time = datetime.now()
        test_result.end_time = datetime.now()
        test_result.duration = 1.234
        test_result.exit_code = 0
        test_result.success = True
        test_result.peak_memory_mb = 25.6
        test_result.cpu_percent = 15.2
        test_result.output_lines = 42
        test_result.warnings = 0
        test_result.errors = 0
        
        # Test notifications
        results = self.send_execution_notification(test_result)
        
        print("\n📊 Test Results:")
        for channel, result in results.items():
            status = "✅" if result["success"] else "❌"
            print(f"  {channel}: {status} {result['message']}")
            
        return results


def main():
    """Main entry point for testing notifications"""
    if len(sys.argv) < 2:
        print("Usage: python notification_system.py <base_dir> [test]")
        sys.exit(1)
        
    base_dir = Path(sys.argv[1])
    
    # Create notification manager
    manager = NotificationManager(base_dir)
    
    if len(sys.argv) > 2 and sys.argv[2] == "test":
        # Run tests
        manager.test_notifications()
    else:
        print("Notification system initialized. Use 'test' argument to run tests.")
        

if __name__ == "__main__":
    main()