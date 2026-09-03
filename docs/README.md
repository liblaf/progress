# Progress

`liblaf.progress` builds on Rich task accounting, turning it into immutable,
rate-limited events for logging and other application-owned destinations. It
deliberately does not create a live terminal display.

Start with the [logging guide](guides/logging.md) for standard logging and
custom emitters, then read the [event model](concepts/events.md) for ownership,
final snapshots, and rate limiting. The [API reference](reference/liblaf/progress/README.md)
documents the public module.
