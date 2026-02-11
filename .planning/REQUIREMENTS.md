# Requirements: Espresso Profile Translator

**Defined:** 2026-02-12
**Core Value:** Users can seamlessly adapt their existing Meticulous extraction profiles for use with Gaggimate machines

## v2.3 Requirements

Field mappings review and error fixes. All mappings verified against actual implementation.

### Stage Type Mapping

- [ ] **STAGE-01**: Verify Fill (power) → preinfusion with pressure pump
- [ ] **STAGE-02**: Verify Bloom (power) → preinfusion with pressure pump
- [ ] **STAGE-03**: Verify Extraction (power) → brew with pressure pump
- [ ] **STAGE-04**: Verify Flow stages → Same phase key with flow pump

### Power-to-Pressure Conversion

- [ ] **POWER-01**: Verify formula: `gaggimate_pressure = meticulous_power / 10.0`
- [ ] **POWER-02**: Verify 50% → 5.0 bar conversion
- [ ] **POWER-03**: Verify 90% → 9.0 bar conversion
- [ ] **POWER-04**: Verify bounds (0-100 → 0-15 bar)

### Dynamics Point Splitting

- [ ] **DYN-01**: Verify single point → one phase with instant transition
- [ ] **DYN-02**: Verify N points → N-1 phases with linear transitions
- [ ] **DYN-03**: Verify phase naming: "Original (1/N)", "Original (2/N)"
- [ ] **DYN-04**: Verify duration calculation for split phases

### Exit Trigger → Exit Target Mapping

- [ ] **EXIT-01**: Verify weight → volumetric type conversion
- [ ] **EXIT-02**: Verify time → time passthrough
- [ ] **EXIT-03**: Verify pressure → pressure passthrough
- [ ] **EXIT-04**: Verify flow → flow passthrough

### Interpolation Mapping

- [ ] **INTERP-01**: Verify linear → linear transition
- [ ] **INTERP-02**: Verify step/instant → instant transition
- [ ] **INTERP-03**: Verify bezier/spline → ease-in-out transition
- [ ] **INTERP-04**: Verify other → instant transition (fallback)

### Documentation Fixes

- [ ] **DOC-01**: Fix any incorrect mappings found in README.md
- [ ] **DOC-02**: Fix any incorrect formulas or examples
- [ ] **DOC-03**: Update tables to match actual implementation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Bidirectional conversion | One-way translation only |
| Custom interpolation types | Already documented as simplified |
| Exit mode strategies | Requires separate semantic definition |
| Cross-phase cumulative weight | Complex, low priority |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAGE-01 through STAGE-04 | Phase 19 | Pending |
| POWER-01 through POWER-04 | Phase 19 | Pending |
| DYN-01 through DYN-04 | Phase 19 | Pending |
| EXIT-01 through EXIT-04 | Phase 19 | Pending |
| INTERP-01 through INTERP-04 | Phase 19 | Pending |
| DOC-01 through DOC-03 | Phase 19 | Pending |

**Coverage:**
- v2.3 requirements: 23 total
- Mapped to phases: 23
- Unmapped: 0 ✓

---
*Requirements defined: 2026-02-12*
*Last updated: 2026-02-12 after v2.3 milestone started*
