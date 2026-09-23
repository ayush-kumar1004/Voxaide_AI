import logging
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any

class StructuredLogger:
    """Structured JSON logger that avoids leaking secrets, tokens, or PII."""
    def __init__(self, name: str = "voxaide"):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Strip or mask known sensitive keys."""
        sensitive_keys = {"authorization", "token", "password", "api_key", "secret", "private_key"}
        sanitized = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                sanitized[k] = "[REDACTED]"
            elif isinstance(v, dict):
                sanitized[k] = self._sanitize(v)
            else:
                sanitized[k] = v
        return sanitized

    def log(self, level: str, message: str, **context):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            "message": message,
            **self._sanitize(context)
        }

        log_str = json.dumps(payload)
        if level.lower() == "error":
            self.logger.error(log_str)
        elif level.lower() == "warning":
            self.logger.warning(log_str)
        else:
            self.logger.info(log_str)

    def info(self, message: str, **context):
        self.log("info", message, **context)

    def warning(self, message: str, **context):
        self.log("warning", message, **context)

    def error(self, message: str, **context):
        self.log("error", message, **context)

logger = StructuredLogger()
