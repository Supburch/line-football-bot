import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
        }
        
        # Determine if there's an 'event' in the message or extra
        if record.msg:
            if isinstance(record.msg, dict):
                log_record.update(record.msg)
            else:
                log_record["message"] = record.getMessage()

        # Add any extra arguments passed via extra=...
        if hasattr(record, "match_id"): log_record["match_id"] = record.match_id
        if hasattr(record, "score"): log_record["score"] = record.score
        if hasattr(record, "scorer"): log_record["scorer"] = record.scorer
        if hasattr(record, "event_key"): log_record["event_key"] = record.event_key
        if hasattr(record, "event"): log_record["event"] = record.event
        
        return json.dumps(log_record)

def setup_logger(name: str = "footballbot") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding multiple handlers if already set up
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
