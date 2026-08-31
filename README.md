<div align="center" markdown>

![Progress](https://socialify.git.ci/liblaf/progress/image?description=1&forks=1&issues=1&language=1&name=1&owner=1&pattern=Transparent&pulls=1&stargazers=1&theme=Auto)

[![Python](https://img.shields.io/pypi/pyversions/liblaf-progress?logo=python)](https://pypi.org/project/liblaf-progress)
[![Test](https://github.com/liblaf/progress/actions/workflows/python-test.yaml/badge.svg)](https://github.com/liblaf/progress/actions/workflows/python-test.yaml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

</div>

`liblaf.progress` tracks Rich-compatible tasks and emits immutable, rate-limited
snapshots through Python logging. It does not own a live terminal display, so
the same progress state works in CI, services, notebooks, and terminal tools.

## Installation

```bash
uv add liblaf-progress
```

## Usage

```python
from liblaf.progress import Progress, track

for item in track(items, description="Indexing", min_interval=2):
    index(item)
```

For related tasks, make a single `Progress` owner. It rate-limits normal
updates and always emits lifecycle-final snapshots.

```python
from liblaf.progress import Progress

events = []
with Progress(emitter=events.append, min_interval=1) as progress:
    task = progress.add_task("Download", total=2)
    progress.advance(task)
    progress.advance(task)

assert events[-1].final
```

`log_to()` sends events to the standard-library logger named
`liblaf.progress` by default. A logging handler can use the structured
`progress_event` and `progress_renderable` record attributes, while ordinary
handlers receive stable plain text. `liblaf.logging` can render the latter but
is deliberately not a dependency.

`get_progress()` returns a cached process-wide owner when unrelated call sites
need to contribute to the same set of tasks. Prefer an explicit owner when
lifetimes must remain isolated.

## Design

- Rich supplies task accounting and optional rendering; this package never
  starts Rich's live display.
- Standard `logging` is the default integration; integrations are injected,
  and `liblaf.logging` remains optional.
- Ordinary snapshots are rate-limited at the owner; lifecycle-final snapshots
  are forced so logs have a closing state.

Read the [logging guide](https://liblaf.github.io/progress/guides/logging/),
[event model](https://liblaf.github.io/progress/concepts/events/),
[domain context](https://github.com/liblaf/progress/blob/main/CONTEXT.md), and
[architecture decisions](https://github.com/liblaf/progress/tree/main/docs/adr).

## License

[MIT](https://github.com/liblaf/progress/blob/main/LICENSE)
