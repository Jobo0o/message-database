"""
Logging utility for the Hostaway Message Database application.
Configures and provides logging functionality.
"""
import os
import logging
import datetime
from pathlib import Path
import sys
import smtplib
from email.message import EmailMessage

from ..config import LOG_DIR, NUMERIC_LOG_LEVEL, NOTIFICATION_EMAIL

def setup_logging(name="hostaway_message_db"):
    """
    Set up logging with file and console handlers.
    
    Args:
        name (str): The logger name
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path(LOG_DIR)
    log_dir.mkdir(exist_ok=True, parents=True)
    
    # Generate log filename with current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{current_date}.log"
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(NUMERIC_LOG_LEVEL)
    
    # Clear existing handlers if any
    if logger.handlers:
        logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(NUMERIC_LOG_LEVEL)
    
    # Create file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(NUMERIC_LOG_LEVEL)
    
    # Create formatter and add to handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def send_error_notification(subject, message):
    """
    Send an error notification email if configured.
    
    Args:
        subject (str): Email subject
        message (str): Email body message
    """
    if not NOTIFICATION_EMAIL:
        return
    
    try:
        msg = EmailMessage()
        msg.set_content(message)
        msg['Subject'] = subject
        msg['From'] = NOTIFICATION_EMAIL
        msg['To'] = NOTIFICATION_EMAIL
        
        # This would need to be expanded with proper SMTP configuration
        # For now, we'll just log that we would send an email
        logger = logging.getLogger("hostaway_message_db")
        logger.info(f"Would send notification email: {subject}")
        logger.debug(f"Email content: {message}")
        
        # Uncomment and configure when SMTP is available
        # with smtplib.SMTP('smtp.example.com', 587) as server:
        #     server.starttls()
        #     server.login(username, password)
        #     server.send_message(msg)
    except Exception as e:
        logger = logging.getLogger("hostaway_message_db")
        logger.error(f"Failed to send notification email: {str(e)}")

# Create a default logger instance
logger = setup_logging() 