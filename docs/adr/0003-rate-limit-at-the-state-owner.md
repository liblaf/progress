# ADR 0003: Rate-limit at the progress state owner

- Status: accepted
- Date: 2026-08-31

## Context

Fast loops can create millions of state changes. Relying on a particular logging handler to suppress them couples correctness and resource use to global logging configuration.

## Decision

`Progress` rate-limits ordinary snapshots with a monotonic clock and always permits a final snapshot. It does not run a background refresh thread.

## Consequences

Emission behavior is deterministic and testable. A task that stops changing emits no periodic heartbeat; callers needing one must update or explicitly refresh it.
