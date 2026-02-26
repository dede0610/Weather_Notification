"""Logging configuration."""

import logging
import sys
from datetime import datetime


def setup_logger(name: str = "pipeline") -> logging.Logger:
    """Configure and return a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def log_execution_summary(
    logger: logging.Logger,
    status: str,
    records_processed: int,
    alerts_triggered: int,
    duration_seconds: float,
) -> None:
    """Log a formatted execution summary."""
    logger.info("=" * 50)
    logger.info("EXECUTION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Status: {status}")
    logger.info(f"Records processed: {records_processed}")
    logger.info(f"Alerts triggered: {alerts_triggered}")
    logger.info(f"Duration: {duration_seconds:.2f}s")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 50)
