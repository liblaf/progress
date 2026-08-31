# ADR 0001: Name the project `liblaf.progress`

- Status: accepted
- Date: 2026-08-31

## Context

The package replaces parts of `tqdm` and `rich.progress`, but its output model is intentionally different: state changes become log events instead of terminal repaint operations.

## Decision

Use `liblaf.progress` and the `liblaf-progress` distribution name. Treat `tqdm` as an inspiration, not as a promised drop-in API.

## Consequences

The name describes the domain without inheriting another project's compatibility expectations. Convenience APIs remain familiar through `track()` and `trange()`.
