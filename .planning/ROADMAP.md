# Roadmap: IFVG Pro

## Overview

This roadmap covers Phase 4 of IFVG Pro: extending the indicator with premium/discount zone detection, session tracking, dashboard expansion, and an alert system. Phases 1-3 (FVG detection, liquidity/grading, HTF analysis) are already complete. The work begins with critical bug fixes that block accurate grading, then builds PD zones (the core value addition), sessions (independent context layer), and finally alerts (which consume all upstream data). Four phases, each delivering a complete, verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Bug Fixes & Security Consolidation** - Fix grade-inflating bugs and consolidate request.security() calls to free budget
- [ ] **Phase 2: PD Zone Detection & Grading Integration** - HTF swing-based premium/discount zones with grading modifier and visualization
- [ ] **Phase 3: Session Tracking & Visualization** - Asia/London/NY session H/L tracking with dashboard expansion
- [ ] **Phase 4: Alert System** - Grade-filtered entry, invalidation, and mitigation alerts with dynamic messages

## Phase Details

### Phase 1: Bug Fixes & Security Consolidation
**Goal**: The grading system produces accurate, trustworthy grades and the indicator has headroom for future request.security() calls
**Depends on**: Nothing (first phase of this milestone)
**Requirements**: FIX-01, FIX-02, FIX-03
**Success Criteria** (what must be TRUE):
  1. IFVG grades reflect actual setup quality -- removing the fvg_singular hardcode causes grade distribution to spread across tiers (no single grade exceeds 40% of setups on a test chart)
  2. HTF bias calculation exists in exactly one function, called from both render paths -- no duplicated logic
  3. The indicator uses 3 or fewer request.security() calls total (down from 16), freeing 37+ slots for future use
  4. All existing visual behavior is unchanged -- no regressions in FVG/IFVG rendering or HTF overlays
**Plans**: 2 plans

Plans:
- [x] 01-01-PLAN.md -- Consolidate request.security() calls into 2 tuples and extract shared get_htf_bias() function
- [x] 01-02-PLAN.md -- Implement FVG singularity detection algorithm and verify all fixes on TradingView

### Phase 2: PD Zone Detection & Grading Integration
**Goal**: Traders can see where price sits within the HTF dealing range, and zone positioning feeds into setup grading
**Depends on**: Phase 1 (accurate grading baseline required before adding PD modifier)
**Requirements**: PDZ-01, PDZ-02, PDZ-03, PDZ-04, PDZ-05, PDZ-06, PDZ-07, PDZ-08, DSH-01, DSH-02
**Success Criteria** (what must be TRUE):
  1. The chart displays HTF swing high/low boundaries with an equilibrium line at 50%, and optional OTE zone (62-79%) -- zone lines update when new HTF pivots confirm
  2. Each IFVG stores its pd_zone ("premium"/"discount"/"equilibrium"/"neutral") at inversion time, visible in the dashboard or label tooltip
  3. Setups in the optimal zone (longs in discount, shorts in premium) receive a +1 quality boost; wrong-zone setups receive -1 -- observable as grade differences between same-quality setups in different zones
  4. The dashboard shows the current PD zone name (PREMIUM/DISCOUNT) with color coding and the current range percentage (0-100%)
  5. Grade distribution remains balanced after adding the PD modifier -- no single grade exceeds 40% of setups after threshold recalibration
**Plans**: 3 plans
**UI hint**: yes

Plans:
- [ ] 02-01-PLAN.md -- PD zone engine: type extension, inputs, globals, HTF swing detection, zone calculation, grading integration
- [ ] 02-02-PLAN.md -- PD zone visualization (lines, labels, fills, OTE), tooltip update, dashboard expansion
- [ ] 02-03-PLAN.md -- Human verification of complete Phase 2 implementation on TradingView

### Phase 3: Session Tracking & Visualization
**Goal**: Traders can see Asian, London, and NY session boundaries with tracked highs/lows as liquidity reference levels
**Depends on**: Phase 2 (dashboard layout builds on PD zone rows)
**Requirements**: SES-01, SES-02, SES-03, SES-04, SES-05, SES-06, DSH-03, DSH-04
**Success Criteria** (what must be TRUE):
  1. Asian, London, and NY sessions are detected using DST-safe IANA timezones -- session boundaries shift correctly across March/November DST transitions
  2. Previous session highs and lows appear as labeled horizontal lines on the chart, updating each time a new session of that type opens
  3. Session H/L levels are integrated into the DOL (draw on liquidity) finder as Data High/Data Low liquidity targets
  4. Session tracking auto-disables on timeframes above 1H -- no session lines or dashboard rows appear on Daily/Weekly charts
  5. The dashboard shows the active session name and expands cleanly to ~14 rows while remaining readable
**Plans**: TBD
**UI hint**: yes

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD
- [ ] 03-03: TBD

### Phase 4: Alert System
**Goal**: Traders receive actionable, context-rich alerts for valid entries, invalidations, and mitigations without repainting
**Depends on**: Phase 3 (alerts consume grade, PD zone, session, and IFVG state data)
**Requirements**: ALT-01, ALT-02, ALT-03, ALT-04, ALT-05, ALT-06
**Success Criteria** (what must be TRUE):
  1. A valid entry alert fires with a dynamic message containing symbol, timeframe, grade, direction, entry price, BE level, DOL target, and PD zone -- all fields populated from upstream detection
  2. An invalidation alert fires when a BE point is taken on a previously valid IFVG -- the alert identifies which setup was invalidated
  3. An IFVG mitigation alert fires when price fully passes through an active zone
  4. Users can filter entry alerts by minimum grade (A+, A, A-, B+, B, or All) via an input setting
  5. All alerts use freq_once_per_bar_close and only fire on confirmed bars -- no repainting alerts under any condition
**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Bug Fixes & Security Consolidation | 2/2 | Complete | 2026-03-24 |
| 2. PD Zone Detection & Grading Integration | 0/3 | Planned | - |
| 3. Session Tracking & Visualization | 0/0 | Not started | - |
| 4. Alert System | 0/0 | Not started | - |
