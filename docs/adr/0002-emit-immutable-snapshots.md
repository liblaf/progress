# ADR 0002: Emit immutable snapshots through logging

- Status: accepted
- Date: 2026-08-31

## Context

Progress tracking must work in terminals, notebooks, services, and captured CI logs without depending on `liblaf.logging`.

## Decision

Keep Rich for task accounting and optional presentation, but emit immutable `ProgressEvent` values through one injected callback. The default callback writes a plain-text message through standard logging and attaches both the event and a Rich renderable to the `LogRecord`.

## Consequences

Every normal logging setup remains readable. Rich-aware handlers can use the attached renderable without an import cycle. Alternative event destinations require one small adapter.
