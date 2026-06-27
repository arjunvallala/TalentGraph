"""
TalentGraph AI — Structured Logging Setup

Configures Loguru for structured, contextual logging across the platform.
Provides per-module loggers with consistent formatting.

Usage:
    from shared.logging_setup import get_logger
    logger = get_logger(__name__)
    logger.info("Processing candidate", candidate_id="c123", score=0.87)
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from loguru import logger as _logger

from shared.config import settings


def configure_logging() -> None:
    """
    Configure Loguru with console and file handlers.

    - Console: colored, human-readable output
    - File: structured log rotation at 500 MB, 10-day retention

    Should be called once at application startup (e.g., in main.py lifespan).
    """
    # Remove default handler
    _logger.remove()

    # ── Console Handler ───────────────────────────────────────────────────────
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    _logger.add(
        sys.stderr,
        format=log_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=settings.debug,
    )

    # ── File Handler ──────────────────────────────────────────────────────────
    log_file = Path(settings.log_file_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message} | "
        "{extra}"
    )

    _logger.add(
        str(log_file),
        format=file_format,
        level=settings.log_level,
        rotation=settings.log_rotation,
        retention=settings.log_retention,
        compression="gz",
        backtrace=True,
        diagnose=False,  # Never put sensitive data in file logs
        serialize=False,
        enqueue=True,    # Thread-safe async logging
    )

    _logger.info(
        "TalentGraph AI logging configured",
        log_level=settings.log_level,
        log_file=str(log_file),
        environment=settings.app_env,
    )


def get_logger(name: str, **context) -> "BoundLogger":
    """
    Get a contextual logger bound to a module name.

    Args:
        name: Module name, typically __name__.
        **context: Additional context fields to bind to every log message.

    Returns:
        A Loguru logger bound with the provided context.

    Example:
        logger = get_logger(__name__, service="preprocessing")
        logger.info("Starting batch", batch_size=1000)
    """
    return _logger.bind(module=name, **context)


# ── Convenience Type Hint ─────────────────────────────────────────────────────
# Using the base loguru logger type for type hints
BoundLogger = type(_logger)


# ── Timing Decorator ──────────────────────────────────────────────────────────
import functools
import time
from typing import Callable, TypeVar

F = TypeVar("F", bound=Callable)


def log_execution_time(operation: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator that logs the execution time of a function.

    Args:
        operation: Optional human-readable operation name.
                   Defaults to the function name.

    Example:
        @log_execution_time("embedding generation")
        def generate_embeddings(batch): ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            module_logger = get_logger(func.__module__)
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                module_logger.info(
                    f"✓ {op_name} completed",
                    elapsed_seconds=round(elapsed, 3),
                )
                return result
            except Exception as exc:
                elapsed = time.perf_counter() - start
                module_logger.error(
                    f"✗ {op_name} failed after {elapsed:.3f}s",
                    error=str(exc),
                    error_type=type(exc).__name__,
                )
                raise

        return wrapper  # type: ignore

    return decorator
