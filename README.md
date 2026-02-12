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
translate-profile translate "profile.json" --mode preserve                  # Explicit transition mode selection
```

The CLI echoes `Translation mode: <mode>` before translating (and `Mode: <mode>` in batch summaries) so you can confirm what ran. `--mode`/`--transition-mode` overrides everything, but when those flags are absent both commands look for `ESPRESSO_TRANSITION` (smart/preserve/linear/instant) before falling back to `smart`, letting automation preselect a mode without changing the command line.

### Batch Processing

```bash
translate-batch ./profiles/               # Process all .json files
translate-batch ./profiles/ -o ./output/  # Custom output directory
translate-batch ./profiles/ --mode linear  # Force uniform transition behavior for every profile
```

Batch processing also reports the active mode so you can confirm which mapping was applied across the run, but it still falls back to `smart` when no mode flag is supplied.

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

## Quick Reference

### Exit Trigger Type Mapping

| Meticulous Syntax | Gaggimate Syntax | Conversion |
|-------------------|------------------|------------|
| `{"exit": {"type": "weight", "value": 36.0}}` | `{"exit_target": {"type": "volumetric", "value": 36.0}}` | Weight → Volumetric (type renamed) |
| `{"exit": {"type": "time", "value": 30}}` | `{"exit_target": {"type": "time", "value": 30}}` | Time → Time (direct passthrough) |
| `{"exit": {"type": "pressure", "value": 9.0}}` | `{"exit_target": {"type": "pressure", "value": 9.0}}` | Pressure → Pressure (direct passthrough) |
| `{"exit": {"type": "flow", "value": 2.5}}` | `{"exit_target": {"type": "flow", "value": 2.5}}` | Flow → Flow (direct passthrough) |

### Operator Translation

| Meticulous | Gaggimate | Meaning |
|------------|-----------|---------|
| `>=` | `gte` | Greater than or equal |
| `<=` | `lte` | Less than or equal |
| `>` | `gt` | Greater than |
| `<` | `lt` | Less than |

**Default:** When no operator is specified, defaults to `gte` (greater than or equal).

---

## Exit Triggers

Meticulous exit triggers define when a phase ends. Each trigger specifies a condition (type, value, operator) that, when met, signals the transition to the next phase.

### Weight-Based Triggers

Weight-based triggers in Meticulous use grams for shot weight measurement. Gaggimate uses milliliters for volumetric targets.

**Translation:** Trigger type renames from "weight" to "volumetric", value remains unchanged.

Meticulous: {"exit": {"type": "weight", "value": 36.0}}
Gaggimate:  {"exit_target": {"type": "volumetric", "value": 36.0}}

### Direct Passthrough Triggers

Time, pressure, and flow triggers use direct value passthrough:

| Trigger Type | Meticulous Field | Gaggimate Field | Notes |
|--------------|------------------|-----------------|-------|
| Time | `value: seconds` | `value: seconds` | Direct passthrough |
| Pressure | `value: bar` | `value: bar` | Direct passthrough |
| Flow | `value: ml_per_sec` | `value: ml_per_sec` | Direct passthrough |

---

## Operator Translation

Meticulous comparison operators normalize to Gaggimate equivalents:

```
Meticulous: {"exit": {"type": "time", "value": 30, "operator": ">="}}
Gaggimate:  {"exit_target": {"type": "time", "operator": "gte", "value": 30}}
```

| Meticulous Operator | Gaggimate Operator | Semantic Meaning |
|-------------------|-------------------|------------------|
| `>=` | `gte` | Greater than or equal (default) |
| `<=` | `lte` | Less than or equal |
| `>` | `gt` | Greater than |
| `<` | `lt` | Less than |

---

## Relative Trigger Conversion

Meticulous supports relative exit triggers using `+value` syntax, meaning "X seconds after the previous phase ends."

### Accumulation Algorithm

Relative triggers accumulate across phases to calculate absolute timestamps:

```
Phase 1: 0-30s (absolute time, no "+" prefix)
Phase 2: +12.0 → 42s absolute (30 + 12)
Phase 3: +8.0  → 50s absolute (42 + 8)
```

### Example Conversion

```
Meticulous Input:
Phase 1: exit at 30s (absolute)
Phase 2: exit at +12.0 (relative)
Phase 3: exit at +8.0  (relative)

Gaggimate Output:
Phase 1: exit_target at 30s
Phase 2: exit_target at 42s
Phase 3: exit_target at 50s
```

### Error Condition

**Error:** Relative trigger on first phase (no prior phase to accumulate from)

```
Cannot use relative trigger on first phase
```

---

## Warning Categories

The translator emits warnings to help users understand translation quality:

### [Validation] Warnings

Conditions detected that may affect translation quality:

| Condition | Example | User Guidance |
|-----------|---------|---------------|
| Conflicting triggers | `weight >= 36 AND weight <= 30` | Review phase exit conditions |
| Duplicate triggers | Same trigger type twice | First trigger takes precedence |
| Density assumption | Weight trigger on unusual roast | May need manual adjustment |

**Example:**
```
[Validation] Conflicting weight triggers: weight >= 36 AND weight <= 30 - conditions can never both be true
```

### [Unsupported] Notices

Meticulous features without Gaggimate equivalent:

| Feature | Example | User Guidance |
|---------|---------|---------------|
| Unsupported trigger type | `piston_position`, `power`, `user_interaction` | Trigger will be ignored |
| Deprecated operator | Legacy operator syntax | Converted to modern equivalent |

**Example:**
```
[Unsupported] piston_position exit trigger is not supported by Gaggimate machines. This trigger will be ignored.
```

---

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
Gaggimate uses **0-10 bars** for pressure.

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
| flow | flow |

**See also:** [Exit Triggers](#exit-triggers) section for detailed syntax mapping examples.

| Meticulous Operator | Gaggimate Operator |
|-------------------|-------------------|
| >= | gte |
| <= | lte |
| > | gt |
| < | lt |

**See also:** [Operator Translation](#operator-translation) section for detailed syntax mapping and examples.

### Interpolation Mapping

The translator applies different interpolation mappings based on the selected transition mode.

#### Smart Mode (Default)

| Meticulous Interpolation | Gaggimate Transition |
|------------------------|-------------------|
| linear | linear |
| step | linear |
| instant | instant |
| bezier | ease-in-out |
| spline | ease-in-out |

#### Preserve Mode

| Meticulous Interpolation | Gaggimate Transition |
|------------------------|-------------------|
| linear | linear |
| step | linear |
| instant | linear |
| bezier | bezier |
| spline | spline |

#### Linear Mode (force linear)

| Meticulous Interpolation | Gaggimate Transition |
|------------------------|-------------------|
| linear | linear |
| step | linear |
| instant | linear |
| bezier | linear |
| spline | linear |

#### Instant Mode (force instant)

| Meticulous Interpolation | Gaggimate Transition |
|------------------------|-------------------|
| linear | instant |
| step | instant |
| instant | instant |
| bezier | instant |
| spline | instant |

Use the `--mode`/`--transition-mode` option when running either translate command to pick which of these tables apply. The CLI prints the selected mode before the translation runs so you can confirm it chose the mapping you expect, but the converter itself remains unchanged—only this flag toggles the heuristics listed above. The default `smart` mode balances accuracy and urgency, `preserve` keeps bezier/spline curves intact, `linear` forces all transitions to linear, and `instant` forces everything to fire immediately.

### Metadata Preservation

| Meticulous Field | Gaggimate Field | Notes |
|-----------------|-----------------|-------|
| name | label | Profile name preserved |
| id | description | "Meticulous ID: ..." |
| author | description | Included in description |
| original name | description | Included in description |

---

## Validation Rules

The translator enforces Gaggimate firmware constraints and emits warnings for translation quality issues:

| Constraint | Range | Notes |
|------------|-------|-------|
| Temperature | 0-150°C | Per-phase and profile-level |
| Pressure | 0-10 bars | PumpSettings.pressure (with bloom stages floored to 2.0 bar) |
| Flow | ≥ 0 | PumpSettings.flow |
| Duration | > 0 seconds | Phase duration |

**See also:** [Warning Categories](#warning-categories) section for detailed warning types and user guidance.

---
## Examples

This section provides concrete examples demonstrating how Meticulous profiles translate to Gaggimate format. Each example uses real profiles from the test suite that you can run yourself.

---

### Transition Mode Comparison Example


**Interpolation Type Effects:**

| Interpolation Type | Meticulous Syntax | Gaggimate Transition | Behavior |
|--------------------|-------------------|----------------------|----------|
| Linear | `interpolation: "linear"` | `type: "linear"` | Gradual transition between points |
| Instant | `interpolation: "instant"` | `type: "instant"` | Immediate jump to next point |
| Step | `interpolation: "step"` | `type: "linear"` | Simplified to linear |
| Bezier | `interpolation: "bezier"` | `type: "ease-in-out"` | Smooth acceleration/deceleration |
| Spline | `interpolation: "spline"` | `type: "ease-in-out"` | Smooth curve preservation |

**Multi-Point Dynamics Behavior:**

When a Meticulous stage has multiple dynamics points, the translator splits it into separate phases:

```
Input: 3 points → Output: 2 phases (point[0]→point[1], point[1]→point[2])
- Phase 1: Flow Stage (1/2) - duration: 5s, flow: 4.0 ml/s
- Phase 2: Flow Stage (2/2) - duration: 10s, flow: 2.0 ml/s, exit trigger: 25s
```

**When to Use Each Interpolation Type:**
- **Linear:** Standard pressure/flow ramps (most common)
- **Instant:** Quick pressure jumps or pre-infusion
- **Step:** Simplified instant transitions
- **Bezier:** Smooth pressure profiling for nuanced extraction
- **Spline:** Complex flow curves requiring natural curves

**Run this example:**
```bash
translate-profile translate tests/fixtures/batch_test_data/valid_profiles/profile2.json --output flow_profile_gaggimate.json
```

See also: [Dynamics Point Splitting](#dynamics-point-splitting) and [Interpolation Mapping](#interpolation-mapping).

---

### Warning Interpretation Example

This example demonstrates how to interpret translator warnings and resolve issues in your Meticulous profiles.

**Input (Meticulous JSON with issues):**
```json
{
    "name": "Profile with Issues",
    "id": "warning-test-1",
    "author": "test",
    "author_id": "test",
    "temperature": 93.0,
    "final_weight": 36.0,
    "stages": [
        {
            "name": "Test Stage",
            "key": "test",
            "type": "power",
            "dynamics": {
                "points": [[0, 50], [10, 90]],
                "over": "time",
                "interpolation": "linear"
            },
            "exit_triggers": [
                {"type": "weight", "value": 36.0, "comparison": ">="},
                {"type": "weight", "value": 30.0, "comparison": "<="},
                {"type": "piston_position", "value": 50, "comparison": ">="}
            ]
        }
    ]
}
```

**Warning Output:**
```
[Validation] Conflicting weight triggers: weight >= 36.0 AND weight <= 30.0 - conditions can never both be true. Only the first trigger will be used.
[Unsupported] piston_position exit trigger is not supported by Gaggimate machines. This trigger will be ignored.
[Validation] Duplicate weight trigger: weight <= 30.0 (already have weight >= 36.0). Only the first trigger will be used.
```

**Warning Interpretation:**

| Warning | Category | Meaning | Resolution |
|---------|----------|---------|------------|
| "Conflicting weight triggers" | [Validation] | Two triggers with impossible conditions | Remove one trigger or adjust values |
| "Duplicate weight trigger" | [Validation] | Same trigger type specified twice | Remove duplicate, keep desired trigger |
| "piston_position not supported" | [Unsupported] | Trigger type has no Gaggimate equivalent | Remove unsupported trigger or accept it will be ignored |

**Explanation:**

1. **Conflicting Weight Triggers:** The profile specifies both `weight >= 36.0` AND `weight <= 30.0`. Since a shot can't simultaneously weigh more than 36g AND less than 30g, the second trigger can never fire. The translator keeps the first trigger and warns about the conflict.

2. **Duplicate Trigger Warning:** This is a consequence of the conflicting triggers - after the first weight trigger is processed, the second one becomes a duplicate.

3. **Unsupported Trigger Type:** `piston_position` is not a valid exit trigger type for Gaggimate machines. The translator ignores this trigger entirely and continues processing.

**Corrected Profile (no warnings):**
```json
{
    "name": "Profile with Issues - Fixed",
    "id": "warning-test-1",
    "author": "test",
    "author_id": "test",
    "temperature": 93.0,
    "final_weight": 36.0,
    "stages": [
        {
            "name": "Test Stage",
            "key": "test",
            "type": "power",
            "dynamics": {
                "points": [[0, 50], [10, 90]],
                "over": "time",
                "interpolation": "linear"
            },
            "exit_triggers": [
                {"type": "weight", "value": 36.0, "comparison": ">="}
            ]
        }
    ]
}
```

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

**See also:** [Relative Trigger Conversion](#relative-trigger-conversion) section for detailed algorithm and examples.

### Conditional Logic (NOT SUPPORTED)

Meticulous supports conditional logic that cannot be represented in Gaggimate:

```json
// This pattern cannot be translated
// "if pressure exceeds X, do Y" - Gaggimate has no conditional execution
```

### Interpolation Types Other Than Linear (SIMPLIFIED)

The translator handles non-linear interpolations according to the active transition mode:

- **Smart (default):** linear → linear, step → linear, instant → instant, bezier/spline → ease-in-out
- **Preserve:** retains bezier/spline while immediately dropping instant to linear
- **Linear / Instant:** force every interpolation to the requested transition type

See [Interpolation Mapping](#interpolation-mapping) for the full tables that pair interpolation types with output transition types based on the configured mode.

---

## Phase Naming Convention

For multi-point dynamics, phases are named with index:

```
Original Stage: "Preinfusion" with 3 points
↓
Phase 1: "Preinfusion (1/2)"
Phase 2: "Preinfusion (2/2)"
```

Single-point stages emit exactly one phase and always use instant transitions to match the original rigidity.

### Flow Stage Transition Rule

Flow-type stages (any stage with `type: "flow"` or similarly labeled keys) always get `transition.type = "instant"`, even if the interpolation is linear, bezier, or spline. This guarantees the rapid adjustments that flow profiles expect and avoids the smoothing effects other transition types would introduce.

### Bloom Phase Semantics

Bloom stages (identified by keys like `"bloom"`/`"blooming"`) are treated like pressure stages with a hard floor of 2.0 bar and zero reported flow to emulate bloom hold behavior. They still emit instant transitions and use the pressure pump target even when their original stage type was `flow`.

### Duration Heuristics

When a stage lacks a time-based exit trigger, durations are inferred:

- Pressure stages calculate durations from the pressure delta (`points[-1][1] - 0.0`). Deltas greater than 3.0 bar become short bursts (`1.5s`); otherwise, they default to `4.0s`.
- Flow or other stages default to `4.0s` unless a trigger provides an explicit value.
- Any computed duration below or equal to 0 is clamped to `0.1s` to avoid invalid outputs.

Split stages compute each segments duration as the difference between successive dynamic points, ensuring the Gaggimate phases align with the original curve. Only the final segment carries exit targets; preceding segments are purely for pump target/profile shaping.

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
