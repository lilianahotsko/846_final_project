import logging
import sys

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "action": getattr(record, "action", None),
            "user_id": getattr(record, "user_id", None),
            "resource_id": getattr(record, "resource_id", None),
            "message": record.getMessage(),
        }
        return str({k: v for k, v in log_record.items() if v is not None})

logger = logging.getLogger("app_logger")
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(StructuredFormatter())
logger.setLevel(logging.INFO)
logger.addHandler(handler)
