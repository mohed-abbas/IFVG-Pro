---
phase: 05-grading-system-remodel
fixed_at: 2026-04-12T00:00:00Z
review_path: .planning/phases/05-grading-system-remodel/05-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 05: Code Review Fix Report

**Fixed at:** 2026-04-12
**Source review:** .planning/phases/05-grading-system-remodel/05-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### WR-01: Tooltip momentum score diverges from stored momentum score

**Files modified:** `src/IFVG_Indicator.pine`
**Commit:** cbeddeb
**Applied fix:** Added `momentum_score` int field to the `IFVG` type (line 102). Stored the raw `assess_momentum()` int result directly on the IFVG in both the LTF constructor (line 1680) and HTF constructor (line 733). Updated the tooltip to read `ifvg.momentum_score` instead of re-deriving from the momentum string via ternary mapping (line 2010). This eliminates the fragile string-to-int round-trip that could silently drift.

### WR-02: `check_delivery_from_fvg` body-respect check uses current-bar series offsets, not candidate-relative offsets

**Files modified:** `src/IFVG_Indicator.pine`
**Commit:** 04bec1c
**Applied fix:** Changed `math.min(bar_dist, 50)` to `math.min(bar_dist - 1, 50)` in all three instances of the delivery body-respect check (HTF1, HTF2, LTF arrays at lines 1389, 1411, 1431). This excludes the bar at the FVG's end position from the check window, preventing false negatives where a pre-FVG bar's close was incorrectly counted as a zone violation.

### WR-03: `calculate_grade()` duplicates `score_singularity()` call already done in `check_inversions()`

**Files modified:** `src/IFVG_Indicator.pine`
**Commit:** 52923a3
**Applied fix:** Changed `calculate_grade()` signature to accept `int singularity_score` instead of `bool fvg_singular, float fvg_size` (line 1495). Removed internal `score_singularity()` call, replaced with `int singular_score = singularity_score` to use the passed pre-computed value. Updated the call site in `check_inversions()` (line 1658) to pass `singular_score` directly. This makes the pre-computed score the single source of truth and eliminates double computation.

### WR-04: Tooltip total score can differ from stored grade

**Files modified:** `src/IFVG_Indicator.pine`
**Commit:** 9044581
**Applied fix:** Updated tooltip header from `"Grade: " + ifvg.grade + " (" + str.tostring(tt_total) + "/10)"` to `"Grade: " + ifvg.grade + " (at inversion) | Now: " + str.tostring(tt_total) + "/10"` (line 2021). This clearly communicates that the grade was locked at inversion time while the breakdown reflects current conditions (DOL may have been refreshed by `update_dol_status()`).

### WR-05: `assess_momentum` uses global `atr_value` but is called with candle OHLC values suggesting isolation

**Files modified:** `src/IFVG_Indicator.pine`
**Commit:** 40f3a38
**Applied fix:** Added a `NOTE:` comment block (lines 1278-1281) documenting the constraint that parameters must be current-bar OHLC only, because the function uses series offsets `close[k]`, `open[k]`, `high[k]`, `low[k]` relative to the current bar for displacement analysis. This prevents future refactoring from passing saved OHLC values, which would silently produce wrong results.

---

_Fixed: 2026-04-12_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
