# Day 1 Self-Review (Iteration Notes)

## What we built
- Event schema v0
- World-state schema v0
- Minimal DES simulator loop
- MVP world builder
- Smoke tests for event ordering and run loop

## Self-check findings
1. **Scaling risk: O(N) queue scans not present yet, but future handlers may introduce them.**
   - Action: enforce heap-only scheduling and avoid linear scans in hot path.
2. **Abstraction risk: tools/resources schema overlap could diverge.**
   - Action: in v0.2, unify allocator contract to map tools -> required resources explicitly.
3. **Extensibility gap: no formal transition validator yet.**
   - Action: add runtime invariant checker module in Day 2.
4. **Reproducibility gap: seed exists but no replay snapshotting.**
   - Action: add event log + replay mode in Day 2.
5. **Dev-experience gap: `src/` layout requires `PYTHONPATH=src` for local smoke runs.**
   - Action: add `make test` / editable install instructions and CI sanity command.

## Next iteration focus
- Add transition validator
- Add resource allocator abstraction
- Add deterministic replay artifact


## Iteration 2 updates
- Added `TransitionValidator` to enforce event lifecycle constraints at runtime.
- Added `ResourceAllocator` to separate tool intents from shared-resource accounting.
- Added JSONL `EventRecorder` for replay artifacts.
- Upgraded smoke check to cover ordering, allocator contention, validator lifecycle, and replay persistence.

## Remaining design debts
- Rate-limit token-bucket semantics not implemented yet (currently capacity-only).
- No backpressure policy yet (drop vs wait vs preempt).
- Memory subsystem still schema-first, runtime hooks pending.
