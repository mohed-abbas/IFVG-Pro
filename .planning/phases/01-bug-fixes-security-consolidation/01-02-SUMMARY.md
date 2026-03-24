---
phase: 01-bug-fixes-security-consolidation
plan: 02
subsystem: engine
tags: [fvg-singularity, grading, dual-check, pine-script-v6]

# Dependency graph
requires:
  - "01-01 (Security Consolidation & Bias Deduplication)"
provides:
  - "is_fvg_singular() dual-check algorithm replacing hardcoded fvg_singular = true"
  - "Accurate grade distribution reflecting actual setup quality (non-singular FVGs graded lower)"
affects: [02-pd-zones]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dual-check singularity algorithm: proximity (5 bars) AND overlap (ATR * 0.1 tolerance)"
    - "ATR-based overlap tolerance consistent with EQH/EQL relative tolerance pattern"

key-files:
  created: []
  modified:
    - "src/IFVG_Indicator.pine"

key-decisions:
  - "Proximity threshold N=5 bars: allows buffer beyond minimum 3-bar FVG spacing, consistent with strategy.md section 7.1"
  - "Overlap tolerance ATR * 0.1: matches existing i_relative_tolerance default for EQH/EQL detection"
  - "Both checks must fail (proximity AND overlap) for non-singular, per D-01 dual-check requirement"
  - "Grade thresholds unchanged per D-02; natural recalibration from singularity fix alone"
  - "Singularity computed at inversion time (not FVG creation) using current g_fvg_array state"

patterns-established:
  - "is_fvg_singular() function pattern: iterate g_fvg_array with self-skip, direction filter, dual-check"

requirements-completed: [FIX-01]

# Metrics
duration: 1min
completed: 2026-03-24
status: checkpoint-paused
---

# Phase 01 Plan 02: FVG Singularity Fix Summary

**Replaced hardcoded fvg_singular=true with dual-check algorithm (proximity + overlap) so clustered FVGs receive lower grades than isolated singular ones**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-24T13:41:19Z
- **Completed:** 2026-03-24T13:42:22Z (Task 1 only; paused at human-verify checkpoint)
- **Tasks:** 1 of 2 (checkpoint pending)
- **Files modified:** 1

## Accomplishments
- Implemented is_fvg_singular() function with dual-check algorithm: proximity (within 5 bars) AND overlap (zones overlap within ATR * 0.1 tolerance)
- Replaced hardcoded `fvg_singular = true` at line ~1604 with `is_fvg_singular(fvg)` call
- Self-skip guard prevents source FVG from matching itself during iteration
- Only active, same-direction FVGs are considered for singularity check
- Grade thresholds unchanged (A+: score>=2, A: score>=1, etc.) -- grades naturally recalibrate

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement is_fvg_singular() and replace hardcoded true** - `fa2198e` (fix)
2. **Task 2: Verify all Phase 1 fixes on TradingView** - PENDING (checkpoint:human-verify)

## Files Created/Modified
- `src/IFVG_Indicator.pine` - Added is_fvg_singular() function in Section 7 (before calculate_grade()), replaced hardcoded true in check_inversions()

## Decisions Made
- Proximity threshold set to 5 bars (FVGs are 3-candle patterns; 5 bars allows small buffer for "consecutive" definition)
- Overlap tolerance uses ATR * 0.1 (consistent with existing EQH/EQL relative tolerance default)
- Self-skip compares both start_bar AND end_bar (source FVG is still in g_fvg_array at inversion time)
- Status filter checks for "active" only (defensive; inverted/mitigated are already removed from g_fvg_array)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Known Stubs
None - all functionality fully wired.

## Checkpoint Status

**Task 2 (human-verify) is PENDING.** The user must:
1. Copy `src/IFVG_Indicator.pine` into TradingView Pine Script Editor
2. Verify compilation succeeds
3. Verify FIX-03 (security consolidation), FIX-02 (bias dedup), and FIX-01 (singularity) all work correctly
4. Confirm grade distribution shows spread across tiers (not all A/A+)
5. Check no visual regressions on 2+ instruments/timeframes

## Self-Check: PASSED

- src/IFVG_Indicator.pine: FOUND
- is_fvg_singular count: 2 (1 definition + 1 call site)
- fvg_singular = true: NOT FOUND (hardcoded bug removed)
- request.security() count: 2 (from Plan 01)
- get_htf_bias() count: 3 (from Plan 01)
- quality_score >= 2: FOUND (grade thresholds unchanged)
- Commit fa2198e (Task 1): FOUND

---
*Phase: 01-bug-fixes-security-consolidation*
*Paused at checkpoint: 2026-03-24*
