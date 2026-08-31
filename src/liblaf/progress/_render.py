"""Plain and Rich rendering for immutable progress snapshots."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from rich.console import Group, RenderableType
from rich.progress import ProgressColumn, Task, TaskProgressColumn
from rich.text import Text


class TaskSnapshot(Protocol):
    """The immutable task shape consumed by formatting adapters."""

    @property
    def description(self) -> str: ...

    @property
    def completed(self) -> float: ...

    @property
    def total(self) -> float | None: ...

    @property
    def elapsed(self) -> float | None: ...

    @property
    def remaining(self) -> float | None: ...

    @property
    def speed(self) -> float | None: ...

    @property
    def fields(self) -> Mapping[str, Any]: ...


class ProgressEvent(Protocol):
    """The event shape consumed by formatting adapters."""

    @property
    def tasks(self) -> Sequence[TaskSnapshot]: ...


def _number(value: float) -> str:
    return str(int(value)) if value.is_integer() else f"{value:.4g}"


def _duration(seconds: float | None) -> str:
    if seconds is None or not math.isfinite(seconds):
        return "?"
    seconds = max(0.0, seconds)
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds_ = divmod(remainder, 60)
    if hours:
        return f"{hours:d}:{minutes:02d}:{seconds_:02d}"
    return f"{minutes:02d}:{seconds_:02d}"


def format_task(task: TaskSnapshot, *, bar_width: int = 20) -> str:
    """Format one task as a stable plain-text log line.

    Args:
        task: Snapshot-like value to render.
        bar_width: Width of the Unicode progress bar before timing fields.

    Returns:
        A single text line suitable for a conventional logging handler.
    """
    unit = str(task.fields.get("unit", "it"))
    speed = task.speed
    speed_text = "?" if speed is None else f"{speed:.4g}"
    if task.total is None:
        bar = "━" * min(bar_width, int(task.completed) % (bar_width + 1))
        count = _number(task.completed)
        percent = "?%"
    else:
        ratio = 1.0 if task.total == 0 else task.completed / task.total
        ratio = min(1.0, max(0.0, ratio))
        filled = round(bar_width * ratio)
        bar = "━" * filled + "╺" + "━" * max(0, bar_width - filled - 1)
        count = f"{_number(task.completed)}/{_number(task.total)}"
        percent = f"{ratio:>4.0%}"
    timing = f"{_duration(task.elapsed)}<{_duration(task.remaining)}"
    return (
        f"{task.description} {bar:<{bar_width}} {percent} {count} "
        f"[{timing}, {speed_text} {unit}/s]"
    )


def format_event(event: ProgressEvent) -> str:
    """Format every task in an event as newline-delimited plain text.

    Returns:
        An empty string for an event with no visible tasks.
    """
    return "\n".join(format_task(task) for task in event.tasks)


def render_event(event: ProgressEvent) -> RenderableType:
    """Build a Rich renderable for an event without starting a live display.

    Returns:
        A Rich group that a handler or console may render at its chosen time.
    """
    lines: list[Text] = []
    for task in event.tasks:
        line = Text(format_task(task))
        line.stylize("progress.description", 0, len(task.description))
        lines.append(line)
    return Group(*lines)


class SpeedColumn(ProgressColumn):
    """Render a task speed with its configured `unit` field."""

    def render(self, task: Task) -> Text:
        return TaskProgressColumn.render_speed(task.finished_speed or task.speed)
