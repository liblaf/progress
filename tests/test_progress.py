import logging

import pytest
from rich.console import Console

from liblaf.progress import (
    Progress,
    format_event,
    get_progress,
    render_event,
    track,
    trange,
)


class ManualClock:
    value = 0.0

    def __call__(self) -> float:
        return self.value


def test_rate_limit_and_forced_final_event() -> None:
    clock = ManualClock()
    events = []
    progress = Progress(emitter=events.append, min_interval=1.0, get_time=clock)
    task = progress.add_task("download", total=2)

    clock.value = 0.1
    progress.advance(task)
    clock.value = 1.0
    progress.advance(task)
    progress.stop_task(task)

    assert [event.final for event in events] == [False, False, True]
    assert events[-1].tasks[0].completed == 2
    assert events[-1].tasks[0].finished


def test_track_unknown_total_finishes_at_observed_count() -> None:
    events = []

    assert list(track(iter([1, 2, 3]), emitter=events.append, min_interval=100)) == [
        1,
        2,
        3,
    ]

    assert events[-1].final
    assert events[-1].tasks[0].completed == 3
    assert events[-1].tasks[0].total == 3


def test_track_preserves_caller_owned_task() -> None:
    events = []
    progress = Progress(emitter=events.append, min_interval=0)
    task = progress.add_task("owned", total=2)

    assert list(progress.track([1], task_id=task)) == [1]

    assert progress.tasks[task].description == "owned"
    assert progress.tasks[task].completed == 1
    assert not progress.tasks[task].finished


def test_remove_task_emits_one_final_snapshot() -> None:
    events = []
    progress = Progress(emitter=events.append, min_interval=100)
    task = progress.add_task("removed", total=1)

    progress.remove_task(task)
    progress.stop()

    assert [event.final for event in events] == [False, True]
    assert events[-1].tasks[0].description == "removed"


def test_default_emitter_uses_standard_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, logger="liblaf.progress")
    progress = Progress(min_interval=0)

    progress.add_task("compile", total=1)

    assert "compile" in caplog.text
    assert hasattr(caplog.records[0], "progress_event")
    assert hasattr(caplog.records[0], "progress_renderable")


def test_plain_and_rich_rendering() -> None:
    events = []
    progress = Progress(emitter=events.append, min_interval=0)
    progress.add_task("render", total=4, completed=2, unit="page")
    event = events[-1]

    assert "2/4" in format_event(event)
    console = Console(record=True, width=100)
    console.print(render_event(event))
    assert "render" in console.export_text()


def test_disabled_progress_emits_nothing() -> None:
    events = []
    progress = Progress(emitter=events.append, disable=True)
    progress.add_task("quiet")
    progress.stop()

    assert events == []


def test_trange() -> None:
    events = []

    assert list(trange(3, emitter=events.append, min_interval=100)) == [0, 1, 2]
    assert events[-1].tasks[0].finished


def test_get_progress_is_cached() -> None:
    get_progress.cache_clear()

    assert get_progress() is get_progress()
