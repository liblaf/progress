# ADR 0004: Prefer explicit range tracking

- Status: accepted
- Date: 2026-09-03
- Supersedes: the helper-interface consequence in ADR 0001 only

## Context

`trange()` existed solely as a `tqdm`-shaped shorthand. It adds a public API commitment without expressing a capability unavailable through `track(range(...))`.

## Decision

Remove `trange()` and document `track(range(...))` as the iteration pattern. Replacement means serving the progress-tracking use case with clearer semantics, not preserving another project's helper names.

## Consequences

Range tracking remains concise and uses the same API as every other iterable. ADR 0001 remains accepted for the project name; this ADR supersedes only its helper-interface consequence.
