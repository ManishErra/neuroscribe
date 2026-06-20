import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import json
from datetime import datetime
from fastapi import Request
from typing import Optional

# Define path for the audit log file
AUDIT_LOG_PATH = Path(__file__).resolve().parent / "audit.log"

# Create a dedicated logger for audits
audit_logger = logging.getLogger("neuroscribe_audit")
audit_logger.setLevel(logging.INFO)

# Make sure we don't duplicate handlers if the module is imported multiple times
if not audit_logger.handlers:
    file_handler = RotatingFileHandler(AUDIT_LOG_PATH, maxBytes=10*1024*1024, backupCount=10, encoding="utf-8")
    # Custom format: Timestamp - Level - Message
    formatter = logging.Formatter('%(asctime)s - AUDIT - %(message)s')
    file_handler.setFormatter(formatter)
    audit_logger.addHandler(file_handler)

def log_audit(event_type: str, user_id: str, entity_id: str, request: Optional[Request], details: dict):
    """
    Log a structured audit event.
    """
    request_ip = "unknown"
    if request:
        request_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "unknown")

    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "user_id": str(user_id) if user_id else "system",
        "entity_id": str(entity_id) if entity_id else "system",
        "request_ip": request_ip,
        "details": details
    }
    # Log it as JSON string for easy log parsing/analysis
    audit_logger.info(json.dumps(event))
