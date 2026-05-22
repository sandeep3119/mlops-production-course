import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
        }
        # merge any extra fields passed in
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        return json.dumps(log_data)
    
    