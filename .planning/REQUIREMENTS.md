# Requirements: Espresso Profile Translator

**Defined:** 2026-02-12
**Core Value:** Users can seamlessly adapt their existing Meticulous extraction profiles for use with Gaggimate machines

## Validated
- ✅ **v2.3 Field Mappings Review** — All stage, power, dynamics, exit trigger, and interpolation mappings verified and documented (2026-02-12)

## v2.4 Requirements

### CLI Mode Flag
- [ ] **CLI-01**: `translate-profile translate` accepts `--mode`/`--transition-mode` (choices: smart, preserve, linear, instant) and forwards the selection into `translate_profile`.
- [ ] **CLI-02**: `translate-profile translate-batch` exposes the same flag/choices so batch workflows share consistent behavior and still default to `smart` when the flag is omitted.
- [ ] **CLI-03**: CLI output echoes the mode in use so users can confirm which translation path ran (default message should say “smart mode”).

### Documentation
- [ ] **DOC-01**: README quick-start includes a concrete example showing `translate-profile translate input.json --mode preserve` (or equivalent) and explains which file is produced.
- [ ] **DOC-02**: README describes all available modes (smart, preserve, linear, instant), summarizes their visual impact (how interpolation mapping changes), and highlights that only the CLI argument changes the mode (translation logic unchanged).

## Out of Scope
| Feature | Reason |
|---------|--------|
| Bidirectional conversion | Out of scope for this milestone and already documented as future work |
| Custom interpolation types (bezier, spline) | Already simplified in existing heuristic; no change needed |
| Conditional execution logic | Requires architectural work outside this CLI/documentation effort |
| Translation core changes | The mode flag must drive existing mappings without touching interpolation logic |
| Cross-phase cumulative weight tracking | Complex feature deferred for future milestones |

## Traceability
| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 20 | Pending |
| CLI-02 | Phase 20 | Pending |
| CLI-03 | Phase 20 | Pending |
| DOC-01 | Phase 21 | Pending |
| DOC-02 | Phase 21 | Pending |

**Coverage:**
- v2.4 requirements: 5 total
- Mapped to phases: 5
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after v2.4 milestone started*
