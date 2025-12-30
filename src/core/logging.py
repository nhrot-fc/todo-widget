import logging
import sys
from datetime import datetime


class SimpleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        if record.exc_info:
            exc = "\n" + self.formatException(record.exc_info)
        else:
            exc = ""
        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname
        func = record.funcName
        line = record.lineno
        message = record.getMessage()
        return f"[{level}] [{ts}] [{func}: at line: {line}] {message}{exc}"


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    root = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric_level)
    root.handlers.clear()

    formatter = SimpleFormatter()

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    if log_file:
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setFormatter(formatter)
        root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


__all__ = ["setup_logging", "get_logger"]
