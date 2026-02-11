# Espresso Profile Translator

**Status: Experimental**

**IA is involved in the development and documentation.**

This code was created for personal use (PoC/Research/Testing), but it is published in case someone wants to use or refine it.

Convert espresso extraction profiles from **Meticulous** JSON format to **Gaggimate** JSON format.

## Purpose

Users can import any Meticulous profile to their Gaggiuino espresso machine without manual re-creation.

## Disclaimer

This is **not a literal translation**. Meticulous and Gaggimate are different systems with different capabilities and architectures. The resulting profiles are an **adaptation** that attempts to preserve the original profile's intent while conforming to Gaggimate's format and constraints. Some features may be simplified, approximated, or unavailable in the target format.

## Meticulous Access Disclaimer

I don't have access to Meticulous, so I don't have access to all types of profiles. This means the translator is quite experimental and may not cover all edge cases or profile variations. If you encounter any issues or have profiles that don't translate correctly, please open an issue.

## Unsupported Features Disclaimer

There is no adaptation for some values and options from Meticulous profiles. Features that are not translated include but are not limited to:

- Certain types of exit triggers (e.g., pressure-based triggers)
- Complex interpolation types (bezier, spline, or custom — simplified to instant)
- Conditional execution logic (Meticulous patterns like "if pressure exceeds X, do Y" cannot be represented)
- Relative exit triggers (converted to absolute values, which may change behavior)
- Variables (must be resolved to concrete values before translation)

See the [Lost Values & Unsupported Features](#lost-values--unsupported-features) section for full details.

## Installation

```bash
uv pip install .
```

## Usage

### Single Profile Translation

```bash
translate-profile translate "profile.json"  # Output to TranslatedToGaggimate/
translate-profile translate input.json -o output.json                         # Custom output path
```

### Batch Processing

```bash
translate-batch ./profiles/               # Process all .json files
translate-batch ./profiles/ -o ./output/  # Custom output directory
```

## Requirements

- Python 3.12+
- Meticulous JSON files with concrete values (no `$variable` references)
- Output: Valid Gaggimate JSON file

## Commands

| Command | Description |
|---------|-------------|
| `translate-profile translate <FILE>` | Translate single profile to Gaggimate |
| `translate-profile translate <FILE> -o <OUTPUT>` | Translate with custom output path |
| `translate-batch <DIRECTORY>` | Batch translate all JSON files in directory |
| `translate-batch <DIRECTORY> -o <OUTPUT>` | Batch translate to custom output directory |

## Example Usage

```bash
# Translate the example profile
translate-profile translate "profile1.json"

# Batch process all profiles in current directory
translate-batch .
```

# Technical Translation Guide

This section documents how Meticulous profiles are converted to Gaggimate format.

## Schema Overview

### Meticulous Format (Stages-Based)

Meticulous uses a **stages-based** structure:

```json
{
  "name": "Profile Name",
  "temperature": 93.5,
  "stages": [
    {
      "name": "Preinfusion",
      "key": "Fill",
      "type": "power",
      "dynamics": {
        "points": [[0, 2], [10, 5]],
        "over": "pressure",
        "interpolation": "linear"
      },
      "exit_triggers": [
        {"type": "time", "value": 10, "relative": false, "comparison": ">="}
      ]
    }
  ]
}
```

### Gaggimate Format (Phases-Based)

Gaggimate uses a **phases-based** structure:

```json
{
  "label": "Profile Name",
  "type": "pro",
  "temperature": 93.5,
  "phases": [
    {
      "name": "Preinfusion",
      "phase": "preinfusion",
      "valve": 1,
      "duration": 10.0,
      "transition": {"type": "linear", "duration": 10.0, "adaptive": false},
      "pump": {"target": "pressure", "pressure": 0.5, "flow": 10.0},
      "targets": [{"type": "time", "operator": "gte", "value": 10.0}]
    }
  ]
}
```

---

## Field Mappings

### Stage Type Mapping

| Meticulous Stage Key | Meticulous Stage Type | Gaggimate Phase Type | Gaggimate Pump Target |
|---------------------|----------------------|---------------------|----------------------|
| Fill | power | preinfusion | pressure |
| Bloom | power | preinfusion | pressure |
| Extraction | power | brew | pressure |
| Any | flow | Same as key | flow |

### Power-to-Pressure Conversion

Meticulous uses **0-100** scale for power.
Gaggimate uses **0-15 bars** for pressure.

```python
# Conversion formula
gaggimate_pressure = meticulous_power / 10.0

# Example: 50% power → 5.0 bar
# Example: 90% power → 9.0 bar
```

### Dynamics Point Splitting

**Single Point:** Single dynamics point becomes one phase with instant transition.

**Multiple Points:** N dynamics points split into N-1 phases:

| Point Index | Phase | Transition | Duration |
|------------|-------|------------|----------|
| 0→1 | Phase 1 | linear | time[1] - time[0] |
| 1→2 | Phase 2 | linear | time[2] - time[1] |
| ... | ... | ... | ... |

Example: 3-point dynamics creates 2 phases.

### Exit Trigger → Exit Target Mapping

| Meticulous Trigger Type | Gaggimate Target Type |
|------------------------|----------------------|
| weight | volumetric |
| time | time |
| pressure | pressure |

| Meticulous Operator | Gaggimate Operator |
|-------------------|-------------------|
| >= | gte |
| <= | lte |
| > | gt |
| < | lt |

### Interpolation Mapping

| Meticulous Interpolation | Gaggimate Transition |
|------------------------|-------------------|
| linear | linear |
| step/instant | instant |
| other | instant |

### Metadata Preservation

| Meticulous Field | Gaggimate Field | Notes |
|-----------------|-----------------|-------|
| name | label | Profile name preserved |
| id | description | "Meticulous ID: ..." |
| author | description | Included in description |
| original name | description | Included in description |

---

## Validation Rules

The translator enforces Gaggimate firmware constraints:

| Constraint | Range | Notes |
|------------|-------|-------|
| Temperature | 0-150°C | Per-phase and profile-level |
| Pressure | 0-15 bars | PumpSettings.pressure |
| Flow | ≥ 0 | PumpSettings.flow |
| Duration | > 0 seconds | Phase duration |

---

## Lost Values & Unsupported Features

Some Meticulous features are handled specially during translation:

### Variables (AUTOMATICALLY RESOLVED)

Variables defined in the `variables` array are automatically resolved:

```json
{
  "variables": [
    {"name": "Fill Power", "key": "fill_power", "type": "power", "value": 100}
  ],
  "stages": [
    {"dynamics": {"points": [[0, "$fill_power"], [10, 9]]}}  // ✓ Resolved to 100
  ]
}
```

Variable references use `$` prefix (e.g., `$fill_power`). The translator resolves them to concrete values before translation.

### Limits (IGNORED)

Stage `limits` arrays are not translated:

```json
// These fields are read but have no effect
"limits": [{"type": "pressure", "max": 12}]
```

### Previous Authors (IGNORED)

The `previous_authors` array is read but not included in output.

### Final Weight (IGNORED)

`final_weight` field is read but not included in Gaggimate output.

### Relative Exit Triggers (CONVERTED TO ABSOLUTE)

Meticulous supports `relative: true` for exit triggers.
This is converted to absolute values during translation.

### Conditional Logic (NOT SUPPORTED)

Meticulous supports conditional logic that cannot be represented in Gaggimate:

```json
// This pattern cannot be translated
// "if pressure exceeds X, do Y" - Gaggimate has no conditional execution
```

### Interpolation Types Other Than Linear (SIMPLIFIED)

| Meticulous Type | Result |
|----------------|--------|
| linear | Linear transition ✓ |
| step | Instant transition |
| bezier/spline | Instant transition |
| other | Instant transition |

---

## Phase Naming Convention

For multi-point dynamics, phases are named with index:

```
Original Stage: "Preinfusion" with 3 points
↓
Phase 1: "Preinfusion (1/2)"
Phase 2: "Preinfusion (2/2)"
```

---

## Error Handling

| Error | Exit Code | Cause |
|-------|----------|-------|
| FileNotFoundError | 1 | Input file not found |
| InvalidJSONSyntaxError | 1 | Malformed JSON |
| ValidationError | 1 | Concrete values required (no variables) |
| ValueOutOfRangeError | 1 | Pressure > 15, temperature > 150, etc. |

---

## Technical Architecture

```
translate-profile/
├── cli.py              # Typer CLI interface
├── translator.py       # Core translation logic
├── core.py            # File I/O utilities
├── exceptions.py      # Custom error types
└── models/
    ├── meticulous.py  # Pydantic models for input
    └── gaggimate.py   # Pydantic models for output
```

### Key Decisions

- **Typer** — Modern CLI framework with type hints
- **Pydantic V2** — Schema validation and type safety
- **orjson** — Fast JSON processing
- **rich.progress** — Batch processing progress bars

---

## Limitations

1. No bidirectional conversion (Gaggimate → Meticulous)
2. No variable substitution support
3. No profile validation against actual Gaggimate firmware
4. Complex interpolation types simplified to instant
5. Conditional execution patterns lost

---
