# Roadmap: Espresso Profile Translator

## Milestones

- ⚙️ **v2.4 Mode Selection Visibility** — Phases 20‑21 (in progress)
  - Goal: Let users pick the transition mode from the CLI and document how each option alters the output.
  - Requirements mapped: CLI-01 through DOC-02 (5 requirements)
- ✅ **v2.3 Field Mappings Review** — Phase 19 (shipped 2026-02-12)
- ✅ **v2.2 README Update** — Phases 17-18 (shipped 2026-02-12) — [details](milestones/v2.2-ROADMAP.md)
- ✅ **v2.1 README Documentation** — Phase 16 (shipped 2026-02-11) — [details](milestones/v2.1-ROADMAP.md)
- ✅ **v2.0 Exit Mode Support** — Phases 10-12 (shipped 2026-02-11) — [details](milestones/v2.0-ROADMAP.md)
- ✅ **v1.5 Testing** — Phase 9 (shipped 2026-02-11)
- ✅ **v1.4 ExDos Profile Fix** — Phase 4 (shipped 2026-02-10)
- ✅ **v1.3 Analysis & Optimization** — Phase 3 (shipped 2026-02-10)
- ✅ **v1.2 Tests & Documentation** — Phase 2 (shipped 2026-02-10)
- ✅ **v1.1 Smooth Transitions** — Phase 1 (shipped 2026-02-10)
- ✅ **v1.0 MVP** — Phase 0 (shipped 2026-02-10)

---

## Phases

### 🚧 Phase 19: Field Mappings Review

**Goal:** Review all translation field mappings against implementation, fix any errors found

**Target features:**
- Stage Type Mapping verification (Fill/Bloom/Extraction → Gaggimate phases)
- Power-to-Pressure Conversion verification (0-100 → 0-15 bar)
- Dynamics Point Splitting verification
- Exit Trigger → Exit Target Mapping verification
- Interpolation Mapping verification
- Fix any errors found

**Requirements mapped:** STAGE-01 through DOC-03 (23 requirements)

**Success Criteria:**
1. All 5 mapping categories verified against actual implementation
2. Any discrepancies between documentation and code identified
3. Errors fixed in code and/or documentation
4. Tests pass after fixes

**Plans:** 3 plans

Plans:
- [ ] 19-01-PLAN.md — Stage Type & Power-to-Pressure Mapping verification
- [ ] 19-02-PLAN.md — Exit Trigger → Exit Target Mapping verification
- [ ] 19-03-PLAN.md — Interpolation & Dynamics Point Splitting verification

---

### 🚀 Phase 20: CLI Mode Flag

**Goal:** Make the `translate` and `translate-batch` commands accept an explicit transition mode option without changing the existing interpolation logic.

**Target features:**
- `--mode`/`--transition-mode` flag for the single-profile `translate` command (choices: smart, preserve, linear, instant)
- Same flag for `translate-batch` with identical behavior and sensible defaults
- CLI output announcing the mode used so the user knows which mapping path executed

**Requirements mapped:** CLI-01, CLI-02, CLI-03

**Success Criteria:**
1. Both translate commands validate mode choices and default to `smart` when the flag is absent
2. The batch command honors the same semantics as the single-profile command
3. Command output names the mode used and clarifies the default selection

**Plans:** 2 plans

Plans:
- [x] 20-01-PLAN.md — Add mode flag plumbing to `translate` and CLI output verb
- [x] 20-02-PLAN.md — Mirror the flag on `translate-batch` and document default messaging

---

### 📘 Phase 21: README Mode Documentation

**Goal:** Teach users how to invoke the new mode flag and call out what each mode does.

**Target features:**
- Quick-start example showing `translate-profile translate input.json --mode preserve` (or `--transition-mode preserve`)
- Section summarizing each mode’s visual behavior plus a note that the CLI controls the selection
- Reminder that the underlying conversion logic is unchanged and that `smart` is the default mode

**Requirements mapped:** DOC-01, DOC-02

**Success Criteria:**
1. README includes a CLI usage snippet demonstrating the mode flag
2. Mode summary now explains smart, preserve, linear, and instant behaviors
3. Documentation points out that only the CLI arg changes the active mode (conversion heuristics remain untouched)

**Plans:** 1 plan

Plans:
- [ ] 21-01-PLAN.md — Update README CLI usage and mode explanation

---

### 🧪 Phase 22: Mode Verification Tests

**Goal:** Confirm the CLI emits `Translation mode:`/`Mode:` for every allowed mode via automated tests.

**Target features:**
- Automated pytest coverage for `translate` and `translate-batch` (smart default plus preserve/linear/instant overrides)
- Assertions verifying the console output includes the expected mode lines before and after translation

**Requirements mapped:** TEST-01

**Success Criteria:**
1. Pytests run without failure and inspect the mode logging text
2. Tests cover both single-profile and batch CLI commands, including the default smart behavior
3. Evidence recorded in `.planning/phases/22-mode-verification/22-01-SUMMARY.md`

**Plans:** 1 plan

Plans:
- [x] 22-01-PLAN.md — Cover translate/translate-batch mode logging via pytest

---

_Phase 22+: Run `/gsd-new-milestone` to define next goals_

---

*Last updated: 2026-02-12 after v2.4 milestone started*
