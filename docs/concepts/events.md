# Events and ownership

A `Progress` instance is the owner of every task created through it. The owner
turns Rich's mutable task accounting into immutable `TaskSnapshot` values and
emits a `ProgressEvent` containing all currently visible tasks.

## Snapshot boundary

Events are observations, not commands. Their fields cannot change after an
emitter receives them, including the mapping of task fields. This lets a
handler retain, serialize, or render an event without racing later progress
updates.

## Rate limiting

State changes mark the owner stale. The next normal refresh emits only after
`min_interval`; several advances can therefore collapse into one event. A
forced lifecycle event is different: it is emitted at task stop, removal, or
owner stop so a log records the final accounting state.

An explicit task passed to `Progress.track()` remains owned by its caller.
Only a task created by `track()` is stopped and removed automatically.

## No terminal lifecycle

The class is compatible with Rich's task API, but `start()` does not create a
live display and `stop()` does not tear one down. Rendering is an adapter
decision: use `format_event()` for text or `render_event()` for a Rich
renderable.
