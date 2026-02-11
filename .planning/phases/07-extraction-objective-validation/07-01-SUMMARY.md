---
phase: 7
plan: 1
type: feature
autonomous: true
wave: 1
subsystem: validate_profile
tags:
  - validation
  - profile-comparison
  - extraction-objectives
  - tolerance-checking
  - cli

dependency_graph:
  requires:
    - 06-01
    - 06-02
  provides:
    - validate_profile module
    - profile validation CLI
    - tolerance-based comparison
    - phase matching with split support
  affects:
    - 07-02
    - 08-01

tech_stack:
  added:
    - orjson (for Gaggimate JSON parsing)
  patterns:
    - dataclass-based data models
    - typer CLI with commands
    - tolerance-based validation

key_files:
  created:
    - src/validate_profile/__init__.py
    - src/validate_profile/models.py
    - src/validate_profile/exceptions.py
    - src/validate_profile/core.py
    - src/validate_profile/reporter.py
    - src/validate_profile/cli.py
  modified: []

decisions: []

metrics:
  completed: 2026-02-10
  duration: ~5 minutes
---

# Phase 7 Plan 1: Profile Validation Module Summary

Created a complete profile validation module that compares Meticulous extraction profiles against their Gaggimate translations, verifying that extraction objectives (pressure, flow, duration) are preserved within acceptable tolerances.

## Implementation Details

### Core Validation (`src/validate_profile/core.py`)

**Tolerance Configuration:**
- Pressure: ±0.1 bar or ±2% (whichever is larger)
- Flow: ±0.2 ml/s or ±5% (whichever is larger)
- Duration: ±0.5s or ±2% (whichever is larger)

**Key Functions:**
- `extract_meticulous_stage_data()` - Extracts validation-relevant data from Meticulous stages (type, points, duration, controlled variable)
- `extract_gaggimate_phase_data()` - Extracts validation-relevant data from Gaggimate phases (duration, pressure, flow)
- `match_phases()` - Matches stages to phases, handling split phases with (X/Y) suffixes
- `compare_with_tolerance()` - Applies configurable tolerances with automatic selection between absolute and percentage-based
- `validate_profile_pair()` - Main entry point for single profile validation
- `validate_batch()` - Batch validation across directory pairs

### Phase Matching with Split Support

The `match_phases()` function handles split phases correctly:
- Detects phases with (1/2), (2/2) suffixes using regex
- Matches split phases to corresponding Meticulous stages
- Tracks split index and total for reporting

### Data Models (`src/validate_profile/models.py`)

```python
- MeticulousStageData  # Extracted stage data
- GaggimatePhaseData  # Extracted phase data
- PhaseMatch          # Paired stage/phase with split info
- PhaseDeviation      # Individual deviation details
- ValidationResult    # Single phase validation result
- ProfileValidationResult  # Complete profile validation
- BatchValidationResult     # Batch validation summary
```

### CLI Interface (`src/validate_profile/cli.py`)

Commands:
- `validate <meticulous_file> <gaggimate_file>` - Validate single profile pair
- `validate-batch <profiles_dir> <gaggimate_dir>` - Batch validate all profiles

Exit codes:
- 0: All validations passed
- 1: Any validation failed

## Validation Results

All 5 translated profiles were validated:

| Profile | Phases | Passed | Deviations | Status |
|---------|--------|--------|------------|--------|
| Slay-ish | 2/2 | 2 | 3 | ✓ PASSED |
| Turbo Ultimate | 2/2 | 1 | 4 | ✗ FAILED |
| Soup v1.2 | 3/3 | 2 | 4 | ✗ FAILED |
| Bailey - PSPH/Soup | 4/4 | 2 | 7 | ✗ FAILED |
| Gentle & Sweet v1.4 | 3/3 | 1 | 5 | ✗ FAILED |

**Key Findings:**
1. **PreFill/Power stages** have significant flow deviations (100 vs 10) - likely translation mapping issue for power-controlled stages
2. **Rise & Hold phases** show pressure and duration mismatches requiring investigation
3. **Split phase handling** works correctly for multi-phase translations

## Commands Verified

```bash
# Import validation functions
uv run python -c "from validate_profile import validate_profile_pair, TOLERANCES; print(TOLERANCES)"

# Single profile validation
uv run python -c "... validate_profile_pair(...)"

# Batch validation
uv run python -c "... validate_batch(Path('.'), Path('./TranslatedToGaggimate/'))"
```

## Deviations from Plan

None - plan executed exactly as written. All 6 files created, CLI commands implemented, tolerances applied correctly, and split phases handled.

## Authentication Gates

None required for this phase.
