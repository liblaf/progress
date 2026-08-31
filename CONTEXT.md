# Progress Reporting

This context describes observable advancement of finite or open-ended work
without tying that work to a terminal display.

## Language

**Progress owner**:
The lifecycle boundary for one or more related tasks.
_Avoid_: Progress bar, display

**Task**:
The changing accounting state for one unit of work.
_Avoid_: Job, bar

**Task snapshot**:
An immutable observation of one visible task at an emission boundary.
_Avoid_: Task copy, task state

**Progress event**:
A timestamped group of task snapshots; a final event marks a lifecycle boundary
without implying successful completion.
_Avoid_: Refresh, frame

**Emitter**:
An injected destination for progress events.
_Avoid_: Printer, logger

**Minimum interval**:
The shortest allowed duration between ordinary events from one progress owner.
_Avoid_: Refresh rate, timeout
