"""Standard-library logging adapter for progress events."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ._render import ProgressEvent, format_event, render_event


@dataclass(frozen=True, slots=True)
class LoggingEmitter:
    """Send progress snapshots through one standard-library logger.

    The log message is plain text. Records also carry `progress_event` and
    `progress_renderable` for handlers that use structured or Rich output.

    Attributes:
        logger: Destination logger.
        level: Numeric logging level used for emitted events.
    """

    logger: logging.Logger
    level: int = logging.INFO

    def __call__(self, event: ProgressEvent) -> None:
        self.logger.log(
            self.level,
            "%s",
            format_event(event),
            extra={
                "progress_event": event,
                "progress_renderable": render_event(event),
            },
        )


def log_to(
    logger: logging.Logger | str | None = None,
    *,
    level: int = logging.INFO,
) -> LoggingEmitter:
    """Build a standard-library logging emitter.

    Args:
        logger: A logger instance or name. `None` selects `liblaf.progress`.
        level: Numeric logging level for emitted events.

    Returns:
        An emitter suitable for [`Progress`][liblaf.progress.Progress].
    """
    if logger is None:
        resolved = logging.getLogger("liblaf.progress")
    elif isinstance(logger, str):
        resolved = logging.getLogger(logger)
    else:
        resolved = logger
    return LoggingEmitter(resolved, level)
