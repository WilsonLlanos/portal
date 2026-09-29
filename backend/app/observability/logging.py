"""T021: logging estruturado em JSON (constituição, Princípio VIII).

Não usa nenhuma dependência externa — só o `logging` padrão com um
formatter em JSON, para que os logs da Vercel fiquem parseáveis.
"""

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Campos extras passados via `extra={...}` no log.
        for key, value in record.__dict__.items():
            if key in ("args", "msg", "message") or key in payload:
                continue
            if key.startswith("_"):
                continue
            if key in logging.LogRecord.__dict__:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
