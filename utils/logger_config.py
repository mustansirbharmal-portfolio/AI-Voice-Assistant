import logging
import json
from datetime import datetime
from pathlib import Path
import os

# Create logs directory if it doesn't exist
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Create log files for different purposes
current_date = datetime.now().strftime("%Y-%m-%d")
api_log_file = logs_dir / f"api_{current_date}.log"
error_log_file = logs_dir / f"error_{current_date}.log"

# Configure logging format
log_format = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure API logger
api_logger = logging.getLogger('api')
api_logger.setLevel(logging.INFO)
api_handler = logging.FileHandler(api_log_file)
api_handler.setFormatter(log_format)
api_logger.addHandler(api_handler)

# Configure Error logger
error_logger = logging.getLogger('error')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler(error_log_file)
error_handler.setFormatter(log_format)
error_logger.addHandler(error_handler)

def log_api_request(endpoint: str, method: str, request_data: dict = None):
    """Log API request details"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'method': method,
        'request_data': request_data
    }
    api_logger.info(f"API Request: {json.dumps(log_data, indent=2)}")

def log_api_response(endpoint: str, status_code: int, response_data: dict = None, error: str = None):
    """Log API response details"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'endpoint': endpoint,
        'status_code': status_code,
        'response_data': response_data,
        'error': error
    }
    if error:
        error_logger.error(f"API Error: {json.dumps(log_data, indent=2)}")
    else:
        api_logger.info(f"API Response: {json.dumps(log_data, indent=2)}")

def log_external_api_call(api_name: str, request_data: dict = None, response_data: dict = None, error: str = None):
    """Log external API calls (Dialogflow, OpenRouter)"""
    log_data = {
        'timestamp': datetime.now().isoformat(),
        'api_name': api_name,
        'request_data': request_data,
        'response_data': response_data,
        'error': error
    }
    if error:
        error_logger.error(f"External API Error: {json.dumps(log_data, indent=2)}")
    else:
        api_logger.info(f"External API Call: {json.dumps(log_data, indent=2)}")
