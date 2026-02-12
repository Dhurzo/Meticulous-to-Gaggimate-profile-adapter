# Espresso Profile Translator

## What This Is

A tool that converts espresso extraction profiles from **Meticulous** JSON format to **Gaggimate** JSON format. Users can import Meticulous profiles to their Gaggiuino espresso machine without manual re-creation.

## Core Value

Users can seamlessly adapt their existing Meticulous extraction profiles for use with Gaggimate machines, preserving the intended extraction profile behavior.

## Current Milestone: v2.4 Mode Selection Visibility

**Goal:** Give users control over the transition mode via the CLI and document how each mode behaves so they can choose intentionally.

**Target features:**
- Add a `--mode`/`--transition-mode` argument to the `translate` and `translate-batch` commands that passes the selected mode to `translate_profile`.
- Ensure selecting a mode still defaults to the established `smart` behavior whenever no option is supplied and surface that default in CLI output.
- Update the README with a usage example, mention of the available modes (smart/preserve/linear/instant), and clear guidance on when to pick each.
- Highlight in documentation that the conversion logic remains untouched and that the new flag only drives the existing mode mappings.

## Previous Milestone: v2.2 README Update

**Shipped:** 2026-02-12
- Technical Translation Guide complete (816-line README)
- Examples Section with real test profiles
- Warning generation integrated

## Requirements

### Validated

- ✅ **v2.2 README Update** — Technical Translation Guide and Examples Section (2026-02-12)
  - Exit trigger mappings documented (weight→volumetric, time→time, pressure→pressure, flow→flow)
  - Operator translations documented (>=→gte, <=→lte, >→gt, <→lt)
  - Relative-to-absolute trigger conversion documented
  - Transition mode options documented (SMART, PRESERVE, LINEAR, INSTANT)
  - Warning categories documented ([Validation], [Unsupported])
  - Before/after profile example with real test data
  - Mode selection comparison example
  - Warning interpretation example

- ✅ **v2.0 Exit Mode Support** — Translate Meticulous stop conditions to Gaggimate exit modes (2026-02-11)
  - All trigger types convert: weight→volumetric, time→time, pressure→pressure, flow→flow
  - Comparison operators map correctly (>=→gte, <=→lte, >→gt, <→lt)
  - Relative time triggers convert to absolute values
  - Conflict detection for contradictory triggers
  - Duplicate trigger type reporting
  - Categorized warnings ([Validation], [Unsupported])
  - 40 tests passing (19 translation + 21 validation)
  - exit_mode.py module extracted and exportable

- ✅ **v2.1 README Documentation** — Feature documentation for exit mode translation (2026-02-11)

- ✅ **v1.5 Testing** — Profile validation across all .json files (2026-02-11)
- ✅ **v1.4 ExDos Profile Fix** — Fix phase translation issues (2026-02-10)
- ✅ **v1.3 Analysis & Optimization** — Documentation & analysis of smart_interpolation_map (2026-02-10)
- ✅ **v1.2 Tests & Documentation** — Test coverage & README updates (2026-02-10)
- ✅ **v1.1 Smooth Transitions** — Smart interpolation heuristics (2026-02-10)
- ✅ **v1.0 MVP** — Basic profile translation (2026-02-10)

### Active

- [ ] **v2.4 Mode Selection Visibility** — Expose transition-mode selection to users and document how to use it (2026-02-12)
  - CLI accepts a `--mode` argument that limits choices to smart, preserve, linear, or instant.
  - The default remains `smart`; any other selection maps directly to the pre-existing interpolation mappings.
  - README includes a concrete example showing how to call the command with a non-default mode and explains the visual impact of each mode.

### Out of Scope

- Bidirectional conversion (Gaggimate → Meticulous)
- Custom interpolation types (bezier, spline)
- Conditional execution logic
- User-facing visualization
- Translation core changes — This milestone only adds a CLI flag and docs (conversion logic stays the same)
- Cross-phase cumulative weight tracking — Complex, low priority

## Context

- **Current version:** v2.0
- **Tech Stack:** Python 3.12+, Pydantic V2, Typer CLI
- **Translation modes:** smart (default), preserve, linear, instant
- **Gaggimate transitions:** linear, instant, ease-in-out
- **Meticulous interpolations:** linear, step, instant, bezier, spline
- **Python LOC:** ~5,928

### Technical Notes

- Duration thresholds: 1.0 bar and 3.0 bar pressure delta boundaries
- Duration values: 1.5s (large), 4.0s (normal), 7.0s (small)
- Exit mode translation: TRIGGER_TO_TARGET_TYPE and OPERATOR_MAP mappings
- Validation: detect_conflicting_triggers() for range-based conflict detection
- Module pattern: exit_mode.py with convert_exit_triggers() exported

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| v2.0: Separate exit_mode.py module | Enables reuse in batch processing | ✅ Implemented with package-level exports |
| v2.0: Warning tuple pattern | Separates validation from emission | ✅ convert_exit_triggers returns (targets, warnings) |
| v2.0: Categorized warnings | User-friendly filtering | ✅ [Validation] and [Unsupported] tags |
| v1.4: Phantom phase guard | Single-point stages should not create extra phases | ✅ Fixed with `if num_points >= 2` guard |
| v1.4: Duration preservation | Exit triggers define duration, not pressure delta | ✅ Fixed with time_trigger_found check |
| v1.4: Bloom semantics | Bloom uses pressure target, flow uses flow target | ✅ Fixed with MIN_BLOOM_PRESSURE=2.0 |
| v1.4: Stage-type transitions | Flow stages always use instant transitions | ✅ Applied to SMART and PRESERVE modes |
| v1.4: Duration fallback | Prevent zero-duration validation errors | ✅ Added `max(duration, 1.0)` |
| v1.3: Documentation focus | Establish baseline understanding before optimization | ✅ 40 KB documentation created |
| v1.2: Test-driven documentation | Verify implementation before documenting | ✅ 18 tests pass |
| v1.1: Smart mode default | Balance safety and fidelity for most users | ✅ Implemented |
| v1.1: instant→instant in smart mode | Preserve urgency scenarios | ✅ Documented |
| v1.1: instant→linear in preserve mode | Force gradual transitions for safety | ✅ Documented |
| Pydantic V2 for validation | Type safety and schema validation | ✅ Good |
| Typer for CLI | Modern CLI with type hints | ✅ Good |

## Constraints

- **Tech Stack:** Python 3.12+, Pydantic V2, Typer CLI
- **Output Format:** Must conform to Gaggimate JSON schema
- **Backward Compatibility:** Existing profiles must continue to work
- **Scope:** v1.x focused on translation quality; v2.0+ for major features

---

*Last updated: 2026-02-12 after v2.4 milestone started*
