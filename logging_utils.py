import logging
import os
from logging.handlers import TimedRotatingFileHandler


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_DIR = "/config/logs" if os.path.isdir("/config") else None

log_formatter = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S %Z"
)
logger = logging.getLogger("coordinator")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

if LOG_DIR is not None:
    log_dir = LOG_DIR
    try:
        os.makedirs(log_dir, exist_ok=True)

        class WeeklyLogHandler(TimedRotatingFileHandler):
            """Rotate logs weekly, keeping .log extension on rotated files."""

            def rotation_filename(self, default_name):
                base = os.path.join(log_dir, "coordinator")
                suffix = default_name.split(".")[-1]
                return f"{base}.{suffix}.log"

        file_handler = WeeklyLogHandler(
            os.path.join(log_dir, "coordinator.log"),
            when="W0",
            interval=1,
            backupCount=4,
            utc=False,
        )
        file_handler.setFormatter(log_formatter)
        logger.addHandler(file_handler)
    except OSError:
        # Fall back to console logging if the mounted config volume is read-only
        # or owned by a different runtime user.
        LOG_DIR = None

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter)
logger.addHandler(stream_handler)

logging.getLogger("werkzeug").setLevel(logging.ERROR)
