"""
Logging setup for ARIA using loguru with file and console outputs.
"""

import sys
from pathlib import Path

try:
    from loguru import logger
except ImportError:
    import logging
    # Fallback to standard logging if loguru is not installed yet
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    logger = logging.getLogger("aria")
    if not hasattr(logger, "success"):
        logger.success = logger.info


def setup_logger():
    """Configure loguru logging with rotation and retention."""
    if hasattr(logger, "remove"):
        try:
            from aria.config import config
            log_dir = config.memory_dir / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            logger.remove()
            # Console format
            logger.add(
                sys.stderr,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
                level=config.log_level,
                colorize=True,
            )
            # File format with rotation
            logger.add(
                log_dir / "aria_{time:YYYY-MM-DD}.log",
                rotation="10 MB",
                retention="7 days",
                level="DEBUG",
                compression="zip",
            )
        except Exception as e:
            print(f"Warning: could not fully initialize loguru: {e}", file=sys.stderr)
