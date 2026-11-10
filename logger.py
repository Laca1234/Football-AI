# logger.py — simple file logger
import logging
import os

LOG_FILE = "app_activity.log"

# Configure standard Python logging to write to a .txt file
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def log_event(message):
    logging.info(message)
    print(f"[LOG] {message}")