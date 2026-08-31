"""Progress state machine backed by Rich task accounting."""

from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterable, Iterator, Mapping
from dataclasses import dataclass
from functools import cache
from types import MappingProxyType
from typing import Any, Final, override

from rich.console import Console
from rich.progress import (
    BarColumn,
    GetTimeCallable,
    MofNCompleteColumn,
    ProgressColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.progress import Progress as RichProgress

from ._logging import log_to
from ._render import SpeedColumn


@dataclass(frozen=True, slots=True)
class TaskSnapshot:
    """Immutable public state for one visible progress task.

    The enclosing event copies `fields` into a read-only mapping, so emitters
    may retain a snapshot without racing a later task update.
    """

    id: TaskID
    description: str
    completed: float
    total: float | None
    elapsed: float | None
    remaining: float | None
    speed: float | None
    finished: bool
    fields: Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class ProgressEvent:
    """One timestamped observation of every visible task.

    `final` marks an owner lifecycle boundary; it does not imply success.
    """

    tasks: tuple[TaskSnapshot, ...]
    timestamp: float
    final: bool = False


type Emitter = Callable[[ProgressEvent], None]


class _DefaultEmitter:
    pass


_DEFAULT_EMITTER: Final = _DefaultEmitter()


class Progress(RichProgress):
    """Own Rich-compatible task accounting and emit log-oriented snapshots.

    Unlike Rich's `Progress`, this class does not start a live terminal display. Mutable Rich tasks become immutable
    events sent to `emitter` at the owner's rate limit.

    Args:
        *columns: Optional Rich columns for rendering integrations.
        emitter: Destination for immutable events. Omit it to use standard
            logging; pass `None` to disable emission.
        min_interval: Minimum seconds between ordinary events. Final events are
            not delayed.
        speed_estimate_period: Rich speed-estimation window in seconds.
        get_time: Clock for task timing and rate limiting.
        disable: Disable all event emission.
        expand: Rich layout option retained for rendering adapters.
    """

    def __init__(
        self,
        *columns: str | ProgressColumn,
        emitter: Emitter | _DefaultEmitter | None = _DEFAULT_EMITTER,
        min_interval: float = 1.0,
        speed_estimate_period: float = 30.0,
        get_time: GetTimeCallable | None = None,
        disable: bool = False,
        expand: bool = False,
    ) -> None:
        if min_interval < 0:
            msg = "min_interval must be non-negative"
            raise ValueError(msg)
        resolved_clock = get_time or time.monotonic
        super().__init__(
            *columns,
            console=Console(quiet=True),
            auto_refresh=False,
            speed_estimate_period=speed_estimate_period,
            get_time=resolved_clock,
            disable=disable,
            expand=expand,
        )
        self.emitter: Emitter | None
        if isinstance(emitter, _DefaultEmitter):
            self.emitter = log_to()
        else:
            self.emitter = emitter
        self.min_interval = min_interval
        self._clock = resolved_clock
        self._last_emit = -math.inf
        self._stale = False
        self._last_was_final = False

    @override
    @classmethod
    def get_default_columns(cls) -> tuple[ProgressColumn, ...]:
        return (
            TextColumn("{task.description}", style="progress.description"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TextColumn("["),
            TimeElapsedColumn(),
            TextColumn("<"),
            TimeRemainingColumn(),
            TextColumn(","),
            SpeedColumn(),
            TextColumn("]"),
        )

    def _mark_stale(self) -> None:
        self._stale = True
        self._last_was_final = False

    def _snapshot(self, *, final: bool) -> ProgressEvent:
        tasks = tuple(
            TaskSnapshot(
                id=task.id,
                description=task.description,
                completed=task.completed,
                total=task.total,
                elapsed=task.elapsed,
                remaining=task.time_remaining,
                speed=task.finished_speed or task.speed,
                finished=task.finished,
                fields=MappingProxyType(dict(task.fields)),
            )
            for task in self.tasks
            if task.visible
        )
        return ProgressEvent(tasks, self._clock(), final)

    @override
    def add_task(
        self,
        description: str,
        start: bool = True,
        total: float | None = 100.0,
        completed: int = 0,
        visible: bool = True,
        **fields: Any,
    ) -> TaskID:
        task_id = super().add_task(
            description,
            start=start,
            total=total,
            completed=completed,
            visible=visible,
            **fields,
        )
        self._mark_stale()
        self.refresh()
        return task_id

    @override
    def remove_task(self, task_id: TaskID) -> None:
        """Emit a final snapshot before removing a task from this progress owner."""
        if not self._last_was_final:
            self._mark_stale()
            self.refresh(force=True)
        super().remove_task(task_id)

    @override
    def advance(self, task_id: TaskID, advance: float = 1) -> None:
        super().advance(task_id, advance)
        self._mark_stale()
        self.refresh()

    @override
    def update(
        self,
        task_id: TaskID,
        *,
        total: float | None = None,
        completed: float | None = None,
        advance: float | None = None,
        description: str | None = None,
        visible: bool | None = None,
        refresh: bool = False,
        **fields: Any,
    ) -> None:
        super().update(
            task_id,
            total=total,
            completed=completed,
            advance=advance,
            description=description,
            visible=visible,
            refresh=False,
            **fields,
        )
        self._mark_stale()
        self.refresh(force=refresh)

    @override
    def reset(
        self,
        task_id: TaskID,
        *,
        start: bool = True,
        total: float | None = None,
        completed: int = 0,
        visible: bool | None = None,
        description: str | None = None,
        **fields: Any,
    ) -> None:
        super().reset(
            task_id,
            start=start,
            total=total,
            completed=completed,
            visible=visible,
            description=description,
            **fields,
        )
        self._mark_stale()

    @override
    def stop_task(self, task_id: TaskID) -> None:
        super().stop_task(task_id)
        self._mark_stale()
        self.refresh(force=True)

    @override
    def start(self) -> None:
        """Start the context without creating a live terminal display."""

    @override
    def stop(self) -> None:
        """Force one final log snapshot if tasks remain."""
        self.refresh(force=True)

    def refresh(self, *, force: bool = False) -> None:
        """Emit a stale snapshot when the owner's rate limit permits.

        Args:
            force: Emit a final lifecycle snapshot even when `min_interval`
                has not elapsed.
        """
        if self.disable or self.emitter is None or not self.tasks:
            return
        if not self._stale and (not force or self._last_was_final):
            return
        now = self._clock()
        if not force and now - self._last_emit < self.min_interval:
            return
        event = self._snapshot(final=force)
        if not event.tasks:
            return
        self._stale = False
        self._last_was_final = force
        self._last_emit = now
        self.emitter(event)

    @override
    def track[T](
        self,
        sequence: Iterable[T],
        total: float | None = None,
        completed: int = 0,
        task_id: TaskID | None = None,
        description: str = "Working...",
        update_period: float = 0.1,
    ) -> Iterator[T]:
        del update_period
        created = task_id is None
        resolved = task_id
        if created:
            resolved = self.add_task(description, total=total, completed=completed)
        else:
            # Match Rich's ownership boundary: an explicit task remains owned
            # by its caller and may continue after this tracked sequence.
            assert resolved is not None
            self.update(resolved, total=total, completed=completed)
        assert resolved is not None
        try:
            for item in sequence:
                yield item
                self.advance(resolved)
        finally:
            if created:
                task = self._tasks[resolved]
                if total is None:
                    self.update(resolved, total=task.completed)
                self.stop_task(resolved)
                self.remove_task(resolved)


def track[T](
    sequence: Iterable[T],
    total: float | None = None,
    completed: int = 0,
    description: str = "Working...",
    *,
    progress: Progress | None = None,
    **progress_options: Any,
) -> Iterator[T]:
    """Yield a sequence while reporting rate-limited progress snapshots.

    Args:
        sequence: Values to yield.
        total: Expected number of values, or `None` for an open-ended sequence.
        completed: Initial completed count.
        description: Task description included in each event.
        progress: Existing owner to use. Omit it to create one for this call.
        **progress_options: Options passed to a newly-created `Progress`.

    Yields:
        Each value from `sequence`.

    Examples:
        >>> list(track(["a", "b"], emitter=None))
        ['a', 'b']
    """
    resolved = progress if progress is not None else Progress(**progress_options)
    with resolved:
        yield from resolved.track(
            sequence,
            total=total,
            completed=completed,
            description=description,
        )


def trange(*args: int, **kwargs: Any) -> Iterator[int]:
    """Yield a `range` while reporting progress.

    `args` have the same meaning as `range`; keyword arguments are forwarded to
    [`track`][liblaf.progress.track].

    Examples:
        >>> list(trange(3, emitter=None))
        [0, 1, 2]
    """
    return track(range(*args), total=len(range(*args)), **kwargs)


@cache
def get_progress() -> Progress:
    """Return the cached process-wide log-oriented progress owner.

    Use an explicit owner when independent operations must not share tasks.

    Examples:
        >>> get_progress() is get_progress()
        True
    """
    return Progress()
