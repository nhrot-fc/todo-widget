import logging
import sys
from datetime import datetime


class SimpleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        exc = ""
        if record.exc_info:
            exc = "\n" + self.formatException(record.exc_info)

        ts = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        return (
            f"[{record.levelname}] [{ts}] "
            f"[{record.funcName}:{record.lineno}] {record.getMessage()}{exc}"
        )


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    root = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(numeric_level)
    root.handlers.clear()

    formatter = SimpleFormatter()

    # Console Handler
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(formatter)
    root.addHandler(sh)

    # File Handler
    if log_file:
        try:
            fh = logging.FileHandler(log_file, encoding="utf-8")
            fh.setFormatter(formatter)
            root.addHandler(fh)
        except Exception as e:
            sys.stderr.write(f"Failed to setup log file handler: {e}\n")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


__all__ = ["setup_logging", "get_logger"]
