---
phase: 02-pd-zone-detection-grading-integration
plan: 01
subsystem: pd-zone-engine
tags: [pd-zone, dealing-range, htf-swing, grading]
requires:
  - Existing Liquidity type + ITH/ITL pipeline (Phase 2 Section 6)
  - Existing calculate_grade / score_pd_zone wiring (Phase 5)
  - IFVG.pd_zone field already declared (line 101)
provides:
  - DealingRange custom type
  - g_pd_swing_highs / g_pd_swing_lows / g_pd_liquidity_array / g_current_range globals
  - PD pivot retrieval via request.security (4th security call)
  - create_pd_internal_levels / check_pd_sweeps / select_dealing_range_source
  - compute_pd_zone / compute_range_percent / is_pd_tf_higher helpers
  - Main-loop PD pipeline ordered before check_inversions()
affects:
  - LTF IFVG creation site (line 1684 region) now stores real pd_zone
  - calculate_grade() call site now receives a real zone (unlocks A+)
tech-stack:
  added:
    - ta.pivothigh / ta.pivotlow inside request.security tuple on PD TF
  patterns:
    - Mirrored ITH/ITL machinery scoped to PD arrays
    - `var` scalar mutation kept in main-loop scope (never inside `=>` fns)
key-files:
  created: []
  modified:
    - src/IFVG_Indicator.pine
decisions:
  - PD pipeline runs BEFORE check_inversions() so pd_zone is freshly computed at inversion
  - HTF IFVG site keeps pd_zone='neutral' per STATE.md (bias-only)
  - Chart-TF fallback via is_pd_tf_higher()/select_dealing_range_source() keeps feature active when chart TF >= PD TF
  - Range rotation keyed off selected ITH/ITL bar_idx mismatch (delete+recreate snapshot)
metrics:
  duration: "execution"
  completed: "2026-04-14"
---

# Phase 2 Plan 01: PD Zone Detection & Grading Integration — Summary

One-liner: HTF swing-based dealing range pipeline feeding computed pd_zone into LTF IFVG creation, unlocking A+ grades without any grading code changes.

## What Changed

### Section 1 — Type additions
Added `type DealingRange` with 16 fields: `high_price`, `low_price`, `high_bar_idx`, `low_bar_idx`, `is_valid`, three lines (`line_high`, `line_eq`, `line_low`), three labels, two zone linefills (`fill_premium`, `fill_discount`), two OTE lines, and OTE linefill. Rendering handles remain `na` until Plan 02 populates them.

### Section 2 — Inputs
Added `GROUP_PD_ZONES` input group between HTF and Liquidity groups with 8 inputs:
- `i_pd_timeframe` (default "D")
- `i_pd_swing_lookback` (default 5, range 2-20)
- `i_show_pd_lines` (true), `i_show_pd_fills` (false), `i_show_ote` (false)
- `i_pd_line_color` (white), `i_pd_eq_color` (yellow), `i_pd_line_width` (1)

### Section 3 — Globals
Added 5 PD globals: `g_pd_swing_highs`, `g_pd_swing_lows`, `g_pd_liquidity_array`, `g_current_range` (DealingRange snapshot), and `g_prev_pd_bar` (HTF-bar-change tracker).

### Section 4 — Utilities (end of Section 4)
Three helpers:
- `is_pd_tf_higher()` — TF comparison via `timeframe.in_seconds`.
- `compute_pd_zone(float price_mid)` — returns `premium`/`discount`/`equilibrium`/`neutral` against the current range (strict 50% EQ).
- `compute_range_percent(float price_mid)` — integer 0-100 or `na` when no valid range.

### Section 5B — HTF data retrieval
Added one new `request.security` tuple call on `i_pd_timeframe` pulling `ta.pivothigh` and `ta.pivotlow`. Security-call budget moved from 3/40 to 4/40. Budget comment updated accordingly.

### Section 6 — Liquidity
Added three functions AFTER `check_liquidity_sweeps()`:
- `create_pd_internal_levels()` — mirror of `create_internal_levels()` producing `PD_ITH`/`PD_ITL` into `g_pd_liquidity_array` (capped at 50, FIFO).
- `check_pd_sweeps()` — mirror of `check_liquidity_sweeps()` scoped to PD array; sweep detection on chart-TF close.
- `select_dealing_range_source()` — returns PD array when chart TF < PD TF, otherwise `g_liquidity_array` (D-05 fallback).

### Section 12 — Main loop
Inserted PD pipeline between `check_liquidity_sweeps()` and `check_inversions()` (the plan-required order). Steps:
1. On `barstate.isconfirmed` + PD bar change: push pivot high/low into `g_pd_swing_highs/lows`.
2. `create_pd_internal_levels()` — mirror ITH/ITL.
3. `check_pd_sweeps()` — invalidate or mark swept.
4. Inline range-selection: iterate source array newest-first, pick newest unswept ITH and ITL, rotate `g_current_range` when `bar_idx` mismatch, else mark existing snapshot `is_valid := false`. Scalar `var` mutation stays in main-loop scope per CLAUDE.md rule.

### LTF IFVG creation site
- Line 1820 (new): computes `ifvg_pd_zone = compute_pd_zone(fvg.mid)` before calling `calculate_grade`.
- Line 1821: `calculate_grade(...)` now receives `ifvg_pd_zone` instead of hardcoded `"neutral"`, so `score_pd_zone` criterion finally contributes a non-constant value.
- Line 1843: `pd_zone = ifvg_pd_zone` stored on the IFVG object, frozen at inversion time (D-09 semantics upheld).

### HTF IFVG creation site (line 732)
Intentionally unchanged — `pd_zone = "neutral"` remains per STATE.md convention ("HTF IFVGs get pd_zone='neutral' (bias-only, no PD grading)").

## Commits

- `3d8d594` — Phase 2: add DealingRange type, PD inputs, globals, and PD zone helpers
- `ba8f811` — Phase 2: wire PD HTF swing pipeline and inject computed pd_zone into IFVG creation

## Deviations from Plan

**[Rule 2 — Correctness] Updated calculate_grade call site to pass the computed pd_zone.**
- Found during: Task 2 implementation review of must_haves.truths ("Unlock A+ grades by feeding real pd_zone into score_pd_zone()").
- Issue: The plan's action section §4 only rewrites the IFVG.new() `pd_zone` field on line 1684, but the call to `calculate_grade(...)` one line above (1662) was still passing the string literal `"neutral"`. Without updating it, storing the correct zone on the IFVG would not affect grading — the must_have truth would fail.
- Fix: Extracted `string ifvg_pd_zone = compute_pd_zone(fvg.mid)` once, passed it both to `calculate_grade` and into `IFVG.new()`.
- Files modified: src/IFVG_Indicator.pine (one additional line change at the grade call site).
- Commit: ba8f811

No other deviations.

## Auth Gates

None.

## Known Stubs

- DealingRange rendering handles (`line_high`, `line_eq`, `line_low`, labels, linefills, OTE refs) remain `na`. Intentional — Plan 02 owns rendering. The `rotated` branch creates a fresh DealingRange with `na` handles; when Plan 02 adds `clear_range_drawings`, it will be called here before rotation.
- No dashboard rows yet (Plan 03).

## Self-Check: PASSED

Task 1 acceptance:
- `type DealingRange` present (1 occurrence).
- `GROUP_PD_ZONES` + 8 PD inputs present.
- `var DealingRange      g_current_range = na` present; PD arrays declared.
- `is_pd_tf_higher`, `compute_pd_zone`, `compute_range_percent` present.

Task 2 acceptance:
- New `request.security(syminfo.tickerid, i_pd_timeframe, ...)` present (1 occurrence, tuple of 2 elements).
- `create_pd_internal_levels`, `check_pd_sweeps`, `select_dealing_range_source` present.
- `pd_zone = compute_pd_zone` matches (via `string ifvg_pd_zone = compute_pd_zone(fvg.mid)` on line 1820 — regex matches).
- Grep count `pd_zone = "neutral"` equals 1 (only HTF site at line 732 remains).
- Main-loop order: liquidity sweeps → PD pivot push → create_pd_internal_levels → check_pd_sweeps → range-selection → check_inversions.
- Security-call budget comment updated to "4 calls / 16 tuple elements after Phase 2 PD pivots".

Commits verified in `git log --oneline`:
- 3d8d594 FOUND
- ba8f811 FOUND

Files verified:
- src/IFVG_Indicator.pine FOUND
- .planning/phases/02-pd-zone-detection-grading-integration/02-01-SUMMARY.md FOUND (this file)
