# NEXT TODO

## Immediate (next session)
1. Implement rate-limit semantics (token bucket / refill clock) on top of allocator.
2. Add backpressure policy choices (`wait`, `drop`, `retry`) and expose in config.
3. Add memory runtime hooks (read/write/invalidate events) beyond schema-only.

## Quality tasks
- Add `make smoke` or equivalent command (no external deps).
- Add CI-friendly test path (install + run) to avoid `PYTHONPATH` friction.
- Add minimal benchmark runner for 3 baselines with CSV output.
