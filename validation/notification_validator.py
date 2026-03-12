"""
Notification System Validator
Tests phone/email/Telegram alerts for trades and errors
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import List
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from validation.comprehensive_validator import ValidationResult, ValidationStatus

logger = logging.getLogger(__name__)


class NotificationValidator:
    """Validates notification systems"""
    
    def __init__(self):
        load_dotenv()
        self.results = []
    
    def validate_email_config(self) -> ValidationResult:
        """Validate email configuration"""
        start = time.time()
        
        try:
            email = os.getenv('EMAIL_ADDRESS')
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT')
            smtp_user = os.getenv('SMTP_USERNAME')
            smtp_pass = os.getenv('SMTP_PASSWORD')
            
            if not all([email, smtp_server, smtp_port, smtp_user]):
                return ValidationResult(
                    component="Notifications",
                    test_name="Email Configuration",
                    status=ValidationStatus.SKIPPED,
                    message="Email not configured (optional)",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Check if password is placeholder
            if smtp_pass and 'your_' in smtp_pass.lower():
                return ValidationResult(
                    component="Notifications",
                    test_name="Email Configuration",
                    status=ValidationStatus.WARNING,
                    message="Email password appears to be placeholder",
                    details={
                        'email': email,
                        'smtp_server': smtp_server,
                        'smtp_port': smtp_port
                    },
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Notifications",
                test_name="Email Configuration",
                status=ValidationStatus.PASSED,
                message="Email configured",
                details={
                    'email': email,
                    'smtp_server': smtp_server,
                    'smtp_port': smtp_port
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Notifications",
                test_name="Email Configuration",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_telegram_config(self) -> ValidationResult:
        """Validate Telegram configuration"""
        start = time.time()
        
        try:
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not bot_token or not chat_id:
                return ValidationResult(
                    component="Notifications",
                    test_name="Telegram Configuration",
                    status=ValidationStatus.SKIPPED,
                    message="Telegram not configured (optional)",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            # Basic token format validation
            if not bot_token.count(':') == 1:
                return ValidationResult(
                    component="Notifications",
                    test_name="Telegram Configuration",
                    status=ValidationStatus.WARNING,
                    message="Telegram bot token format appears invalid",
                    details={'token_format': 'Invalid'},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            return ValidationResult(
                component="Notifications",
                test_name="Telegram Configuration",
                status=ValidationStatus.PASSED,
                message="Telegram configured",
                details={
                    'bot_token_set': True,
                    'chat_id_set': True
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Notifications",
                test_name="Telegram Configuration",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_logging_system(self) -> ValidationResult:
        """Validate logging system"""
        start = time.time()
        
        try:
            import yaml
            from pathlib import Path
            
            # Check config
            config_path = Path('config/config.yaml')
            if not config_path.exists():
                return ValidationResult(
                    component="Notifications",
                    test_name="Logging System",
                    status=ValidationStatus.FAILED,
                    message="Config file not found",
                    details={},
                    timestamp=datetime.now().isoformat(),
                    duration_ms=(time.time() - start) * 1000
                )
            
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            logging_config = config.get('logging', {})
            log_file = logging_config.get('file', 'logs/trading_bot.log')
            log_level = logging_config.get('level', 'INFO')
            
            # Ensure logs directory exists
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            # Test write
            test_log = log_dir / 'validation_test.log'
            with open(test_log, 'w') as f:
                f.write(f"Test log entry: {datetime.now().isoformat()}\n")
            
            return ValidationResult(
                component="Notifications",
                test_name="Logging System",
                status=ValidationStatus.PASSED,
                message="Logging system operational",
                details={
                    'log_file': log_file,
                    'log_level': log_level,
                    'log_dir_writable': True
                },
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
        except Exception as e:
            return ValidationResult(
                component="Notifications",
                test_name="Logging System",
                status=ValidationStatus.FAILED,
                message=f"Error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now().isoformat(),
                duration_ms=(time.time() - start) * 1000
            )
    
    def validate_all(self) -> List[ValidationResult]:
        """Run all notification validations"""
        logger.info("=" * 80)
        logger.info("NOTIFICATION SYSTEM VALIDATION")
        logger.info("=" * 80)
        
        results = [
            self.validate_email_config(),
            self.validate_telegram_config(),
            self.validate_logging_system()
        ]
        
        for result in results:
            logger.info(f"{result.status.value} {result.test_name}: {result.message}")
        
        return results


if __name__ == "__main__":
    validator = NotificationValidator()
    results = validator.validate_all()
