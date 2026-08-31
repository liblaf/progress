# Logging progress

`liblaf.progress` owns task state and emission timing. Logging owns
presentation, routing, and persistence. This separation lets applications use
the same progress code in a terminal, a test run, or a long-running service.

## Default logger

Constructing `Progress()` uses a standard-library logger named
`liblaf.progress`. Configure it like any other logger:

```python
import logging

from liblaf.progress import Progress

logging.basicConfig(level=logging.INFO)

with Progress(min_interval=5) as progress:
    task = progress.add_task("Archive", total=2)
    progress.advance(task, 2)
```

The `min_interval` belongs to the owner, so multiple handlers do not cause
extra work or duplicate rate limiting. Calling `stop_task()`, leaving a
context manager, or removing a task forces a final snapshot.

## Structured records

`log_to()` emits normal `LogRecord` instances. It adds two attributes:

- `progress_event` is the immutable `ProgressEvent` used for structured
  sinks.
- `progress_renderable` is a Rich renderable for handlers that can display
  one.

Handlers that only use the message get a stable, plain-text summary instead.
This means an application may add `liblaf.logging` for Rich output without
making it a dependency of the progress library.

## Custom destinations

Pass an emitter when events belong somewhere other than logging. Emitters are
called synchronously, so keep them fast or hand work to an application-owned
queue.

```python
from liblaf.progress import Progress

received = []
progress = Progress(emitter=received.append, min_interval=0)
task = progress.add_task("Parse", total=1)
progress.advance(task)
progress.stop()

assert received[-1].final
```
