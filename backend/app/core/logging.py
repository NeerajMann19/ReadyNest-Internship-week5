"""
Logging utilities configuration.
"""
import logging
import os
import sys

def setup_logging() -> None:
    """
    Configures application-wide logging with Console and File handlers.
    """
    log_format = "%(asctime)s %(levelname)s %(name)s %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Ensure logs directory exists relative to the backend workspace
    # Since backend runs from backend/ directory, check/create logs/
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    log_file = os.path.join(log_dir, "app.log")
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8")
        ]
    )
    
    # Reduce noise from default uvicorn access logs if desired
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
