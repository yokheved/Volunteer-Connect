import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

ACCESS_LOGGER_NAME = "volunteerconnect.access"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(app) -> logging.Logger:
    access_logger = logging.getLogger(ACCESS_LOGGER_NAME)
    try:
        log_dir = Path(app.config["LOG_DIR"])
        log_dir.mkdir(parents=True, exist_ok=True)
        max_bytes = int(app.config.get("LOG_MAX_BYTES", 1048576))
        backup_count = int(app.config.get("LOG_BACKUP_COUNT", 5))

        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

        def rotating(filename: str, level: int) -> RotatingFileHandler:
            handler = RotatingFileHandler(
                log_dir / filename,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setLevel(level)
            handler.setFormatter(formatter)
            return handler

        app.logger.setLevel(logging.INFO)
        app.logger.propagate = False
        _replace_handlers(
            app.logger,
            rotating("app.log", logging.INFO),
            rotating("error.log", logging.ERROR),
        )

        access_logger.setLevel(logging.INFO)
        access_logger.propagate = False
        _replace_handlers(access_logger, rotating("access.log", logging.INFO))

        werkzeug_logger = logging.getLogger("werkzeug")
        werkzeug_logger.setLevel(logging.ERROR)
        werkzeug_logger.propagate = False
    except Exception:
        pass
    return access_logger


def close_logging(app=None) -> None:
    loggers = [logging.getLogger(ACCESS_LOGGER_NAME)]
    if app is not None:
        loggers.append(app.logger)
    for logger in loggers:
        _close_handlers(logger)


def _replace_handlers(logger: logging.Logger, *handlers: logging.Handler) -> None:
    _close_handlers(logger)
    for handler in handlers:
        logger.addHandler(handler)


def _close_handlers(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
