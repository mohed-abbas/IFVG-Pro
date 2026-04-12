---
phase: 05-grading-system-remodel
plan: 01
subsystem: grading-engine
tags: [ifvg-type, delivery-detection, momentum-scoring, pine-script]
dependency_graph:
  requires: []
  provides: [has_delivery-field, pd_zone-field, check_delivery_from_fvg, int-momentum-scoring]
  affects: [check_inversions, IFVG-type, assess_momentum]
tech_stack:
  added: []
  patterns: [priority-cascade-search, body-respect-validation, displacement-counting]
key_files:
  created: []
  modified:
    - src/IFVG_Indicator.pine
decisions:
  - Used hardcoded lookback of 20 bars for delivery detection (matches existing sweep lookback) since i_sweep_lookback input does not exist
  - Inlined array iteration 3 times (HTF1, HTF2, LTF) to avoid Pine Script function call limitations
  - Kept momentum string field on IFVG type for backward compatibility until Plan 03 rewrites rendering
metrics:
  duration: 219s
  completed: "2026-04-12T20:43:02Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 1
---

# Phase 5 Plan 1: Grading Foundation - Type Extension & Data Inputs Summary

IFVG type extended with has_delivery/pd_zone fields, delivery-from-FVG detection via HTF priority cascade with body respect check, and assess_momentum() rewritten to return int 0-2 with displacement counting and AND/OR bug fix.

## Completed Tasks

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Extend IFVG type and update .new() sites | 732356d | Added has_delivery bool + pd_zone string to IFVG type, updated both LTF and HTF IFVG.new() call sites |
| 2 | Create check_delivery_from_fvg() | b20b2f3 | New function with HTF1->HTF2->LTF priority cascade, body respect validation per D-04, wired to LTF check_inversions() |
| 3 | Rewrite assess_momentum() to int 0-2 | cde420d | Returns int score (0/1/2), adds displacement candle counting, fixes AND/OR bug, maps to string for backward compat |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] i_sweep_lookback input does not exist**
- **Found during:** Task 2
- **Issue:** Plan references `i_sweep_lookback` but no such input exists. Sweep lookback is hardcoded as 20 in check_recent_sweep() call.
- **Fix:** Used hardcoded value of 20 for delivery detection lookback, matching the existing sweep detection behavior.
- **Files modified:** src/IFVG_Indicator.pine

## Key Implementation Details

### check_delivery_from_fvg() Algorithm
- Searches for active opposite-direction FVGs within 20-bar lookback
- Priority cascade: g_htf_fvg_array -> g_htf2_fvg_array -> g_fvg_array (per D-11)
- Body respect check: iterates candles between source FVG and current bar, verifying no body close through zone (per D-04)
- Iteration capped at 50 bars to prevent deep lookback issues
- Returns true on first match from any array (per D-12, all sources scored equally)

### assess_momentum() Rewrite
- Score 2: BOTH strong inversion (body>70%, range>ATR) AND strong displacement (>=2 same-direction candles with body>50% in 5-bar leg, leg range>1.5x ATR)
- Score 1: EITHER strong inversion OR displacement, OR moderate candle (body>50%, range>0.7x ATR)
- Score 0: weak/choppy (body<30% OR range<0.5x ATR) or default
- String mapping preserved: 2->"strong_no_chop", 1->"neutral", 0->"weak_or_choppy"

## Verification Results

- has_delivery references: 4 (type def + HTF .new() + call site + LTF .new())
- pd_zone references: 3 (type def + 2 .new() sites)
- check_delivery_from_fvg references: 2 (function def + call site)
- int momentum_score call: confirmed present
- Old "string momentum = assess_momentum" pattern: confirmed removed
- File line count: 2475 lines (was ~2411, net +64 lines)

## Self-Check: PASSED
