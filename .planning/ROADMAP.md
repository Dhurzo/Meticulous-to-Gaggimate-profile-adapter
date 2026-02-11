# Roadmap: Espresso Profile Translator

## Milestones

- ✅ **v2.3 Field Mappings Review** — Phase 19 (in progress)
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

_Phase 20+: Run `/gsd-new-milestone` to define next goals_

---

*Last updated: 2026-02-12 after v2.3 milestone started*
