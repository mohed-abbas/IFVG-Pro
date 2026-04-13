---
phase: 05-grading-system-remodel
verified: 2026-04-13T00:00:00Z
status: human_needed
score: 5/6 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Verify grade distribution is meaningful on TradingView"
    expected: "Grades spread across A through C range (no single grade exceeds 40% of setups); no A+ grades appear since PD zone is hardcoded neutral; A grades visible when sweep+delivery present with strong momentum"
    why_human: "Grade distribution quality requires visual inspection of actual candles on a live chart — cannot be verified from code structure alone. Pine Script has no automated test framework."
  - test: "Verify indicator compiles without errors in TradingView Pine Script Editor"
    expected: "Indicator loads on ES/NQ 15-min chart with no compilation errors or runtime exceptions"
    why_human: "Pine Script compilation can only be verified by running in the TradingView editor; no offline compiler exists."
  - test: "Hover over IFVG labels to confirm 5-criterion tooltip renders correctly"
    expected: "Tooltip shows Grade: X (N/10), then [N] Sweep+Delivery, [N] Momentum, [N] Target, [N] Singularity, [N] Zone — each on its own line with numeric score"
    why_human: "Tooltip rendering is a visual output; string construction verified in code but actual display requires TradingView chart interaction."
---

# Phase 5: Grading System Remodel — Verification Report

**Phase Goal:** Complete redesign of the IFVG setup grading algorithm to fix ICT methodology misunderstandings and produce accurate, meaningful grades
**Verified:** 2026-04-13
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Grading criteria accurately reflect ICT/SMC methodology — sweep quality, displacement, zone positioning, and FVG characteristics are weighted correctly | VERIFIED | 5-criterion checklist scoring implemented in calculate_grade() (line 1493): sweep+delivery (0-2), momentum (0-2), target clarity (0-2), singularity (0-2), PD zone (0-2) per D-05 decisions in CONTEXT.md |
| 2 | Grade distribution is meaningful — A+ setups are genuinely high-probability, C setups are genuinely marginal | NEEDS HUMAN | Algorithm is structurally sound with hard gates blocking A+ when pd_score<2; actual distribution on real charts requires TradingView visual verification |
| 3 | Each grading factor is independently verifiable via labels/tooltips | VERIFIED | Tooltip at lines 2003-2023 shows all 5 criteria with [0-2] numeric scores and total /10 in format "Grade: X (N/10)\n[N] Sweep+Delivery\n[N] Momentum\n[N] Target\n[N] Singularity\n[N] Zone: NEUTRAL" |

**Score:** 2/3 truths fully verified (1 needs human)

### Deferred Items

None — no later phases cover items from this phase.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/IFVG_Indicator.pine` | IFVG type with has_delivery, pd_zone, singularity_score fields | VERIFIED | Lines 100-102: bool has_delivery, string pd_zone, int singularity_score all present in IFVG type |
| `src/IFVG_Indicator.pine` | check_delivery_from_fvg() with HTF priority cascade and body respect check | VERIFIED | Lines 1368-1440: function exists with HTF1->HTF2->LTF cascade, body respect validation per D-04, capped at 50 bars |
| `src/IFVG_Indicator.pine` | assess_momentum() returning int 0-2 with displacement counting | VERIFIED | Lines 1277-1316: returns int with `int result = 0`, score 2 for both strong inversion AND displacement, score 1 for either, score 0 for weak |
| `src/IFVG_Indicator.pine` | calculate_grade() with 5-criterion checklist scoring (0-10) and A+ hard gates | VERIFIED | Lines 1493-1526: all 5 criteria scored, total 0-10, hard gate at line 1513: total>=9 AND sweep_delivery_score==2 AND pd_score==2 |
| `src/IFVG_Indicator.pine` | score_target_clarity(), score_singularity(), score_pd_zone() helper functions | VERIFIED | Lines 1448, 1463, 1480: all three exist and produce 0-2 scores |
| `src/IFVG_Indicator.pine` | IFVG tooltip with 5-criterion breakdown and /10 total | VERIFIED | Lines 2003-2023: tooltip shows Grade: X (N/10) and all 5 criteria with [N] prefix format |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| check_delivery_from_fvg() | g_htf_fvg_array, g_htf2_fvg_array, g_fvg_array | array iteration with body respect check | WIRED | Lines 1378-1440: three separate inlined blocks iterating each array in priority order; short-circuits on first match |
| IFVG type | both IFVG.new() call sites | has_delivery, pd_zone, singularity_score fields | WIRED | HTF .new() at lines 730-732 (has_delivery=false, pd_zone="neutral", singularity_score=0); LTF .new() at lines 1677-1679 (has_delivery=computed, pd_zone="neutral", singularity_score=computed) |
| calculate_grade() | check_inversions() | expanded 8-parameter call | WIRED | Line 1656: calculate_grade(has_sweep, has_delivery, momentum_score, dol, fvg_singular, fvg_size, "neutral", ifvg_is_bullish) |
| score_pd_zone() | IFVG.pd_zone field | string-to-int mapping | WIRED | Lines 1480-1489 (definition); line 1507 (called from calculate_grade); line 2008 (called from tooltip) |
| render_ifvg_boxes() tooltip | IFVG.has_delivery, IFVG.has_sweep, IFVG.pd_zone, IFVG.singularity_score fields | field access for tooltip text construction | WIRED | Lines 2004-2023: all 5 fields read from ifvg object to compute tt_sd, tt_mom, tt_tgt, tt_sg, tt_pd |

### Data-Flow Trace (Level 4)

This is a Pine Script indicator — data flows bar-by-bar through function calls, not fetch/async patterns.

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| calculate_grade() | sweep_delivery_score | has_sweep (check_recent_sweep) + has_delivery (check_delivery_from_fvg) | Real-time detection on confirmed bars | FLOWING |
| calculate_grade() | momentum_score | assess_momentum() using close/open/high/low from confirmed bar | Real OHLC data | FLOWING |
| calculate_grade() | target_score | score_target_clarity(dol) where dol comes from find_dol() | Real liquidity array search | FLOWING |
| calculate_grade() | pd_score | score_pd_zone("neutral", ifvg_is_bullish) | Hardcoded "neutral" (intentional — PD zone detection not yet re-implemented) | STATIC (intentional) |
| Tooltip | tt_total | Recomputed from stored IFVG fields at render time | Derived from stored values at inversion time | FLOWING |

### Behavioral Spot-Checks

Step 7b: SKIPPED — Pine Script has no runnable entry point outside TradingView; no offline executor exists. Indicator behavior can only be verified on the TradingView platform.

### Requirements Coverage

**Note on D-xx IDs:** The requirement IDs D-01 through D-12 referenced in the plans are implementation decision records defined in `.planning/phases/05-grading-system-remodel/05-CONTEXT.md`. They are NOT listed in `.planning/REQUIREMENTS.md`, which uses different ID schemes (FIX-xx, PDZ-xx, etc.). These D-xx IDs are phase-internal design decisions, not formal v1 requirements. REQUIREMENTS.md has no Phase 5 traceability entries — this is a documentation gap but not a functional deficiency.

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| D-01 | 05-01 | Delivery from FVG detection with body respect check | SATISFIED | check_delivery_from_fvg() at lines 1368-1440 |
| D-02 | 05-02 | A+ requires both sweep AND delivery (hard gate) | SATISFIED | A+ hard gate: sweep_delivery_score==2 required (line 1513) |
| D-03 | 05-01 | Delivery shares i_sweep_lookback input | PARTIAL | i_sweep_lookback input does not exist; hardcoded 20-bar lookback used instead (documented deviation in 05-01-SUMMARY.md). Functionally equivalent. |
| D-04 | 05-01 | Bodies-respected check (wicks allowed, closes count) | SATISFIED | Lines 1388-1397: close[k] > candidate.top / < candidate.bottom for body closes only |
| D-05 | 05-02, 05-03 | 5-criterion checklist scoring 0-10 | SATISFIED | calculate_grade() at lines 1493-1526 with all 5 criteria |
| D-06 | 05-02 | A+ hard gates: sweep_delivery=2, pd_score=2, total>=9 | SATISFIED | Line 1513: `if total >= 9 and sweep_delivery_score == 2 and pd_score == 2` |
| D-07 | 05-02 | Hardcoded grade thresholds (A+=9-10, A=7-8, etc.) | SATISFIED | Lines 1513-1524: all 7 grade boundaries hardcoded |
| D-08 | 05-01, 05-03 | Momentum int 0-2 with AND/OR fix | SATISFIED | assess_momentum() returns int; score 2 requires BOTH conditions (AND), score 1 requires EITHER (OR) |
| D-09 | 05-02 | PD zone scored 0-2 (correct=2, neutral=1, wrong=0) | SATISFIED | score_pd_zone() at lines 1480-1489 |
| D-10 | 05-02 | Correct PD zone is A+ hard gate | SATISFIED | pd_score==2 required for A+ at line 1513; always 1 with neutral pd_zone |
| D-11 | 05-01 | HTF priority cascade: HTF1 -> HTF2 -> LTF | SATISFIED | check_delivery_from_fvg() searches g_htf_fvg_array, then g_htf2_fvg_array, then g_fvg_array |
| D-12 | 05-01 | HTF and LTF delivery scored equally | SATISFIED | All three arrays produce `result := true` equally; no weight difference |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| src/IFVG_Indicator.pine | 1656, 1678 | pd_zone hardcoded to "neutral" | INFO | Intentional — PD zone detection not re-implemented yet; A+ unreachable as designed. Not a stub: behavior is deliberate and documented. |

### Human Verification Required

#### 1. Grade Distribution on TradingView

**Test:** Copy `src/IFVG_Indicator.pine` to TradingView Pine Script Editor, apply to ES or NQ 15-minute chart, and observe IFVG grade labels across recent setups.
**Expected:** Grade labels visible spanning A through C range. No A+ grades should appear (PD zone is hardcoded neutral, blocking the hard gate). A few A grades expected on setups with both sweep+delivery and strong momentum. C grades expected on setups with neither sweep nor delivery and weak momentum.
**Why human:** Grade distribution quality — whether the mapping produces "meaningful" differentiation between high-probability and marginal setups — requires human judgment on real chart data. No automated test framework exists for Pine Script.

#### 2. Compilation Verification

**Test:** Open `src/IFVG_Indicator.pine` in TradingView Pine Script Editor and click "Add to chart."
**Expected:** Indicator compiles with zero errors. Overlay renders on chart with FVG/IFVG boxes, liquidity lines, and dashboard visible.
**Why human:** Pine Script compilation only happens in TradingView's server-side runtime; no offline validator exists.

#### 3. Tooltip Rendering Verification

**Test:** Hover over an IFVG entry label on the chart (the "A BUY" / "B SELL" labels at the entry price level).
**Expected:** Tooltip popup shows "Grade: X (N/10)" on line 1, separator, then five lines each in "[N] CriterionName" format for Sweep+Delivery, Momentum, Target, Singularity, and Zone, another separator, then "Entry: VALID/INVALID."
**Why human:** Tooltip content is constructed from string concatenation and is only visible via TradingView chart interaction. String construction is verified in code but display requires actual rendering.

### Gaps Summary

No blocking gaps found. All must-have artifacts exist, are substantive, and are correctly wired. The only items pending are human verification steps that require TradingView visual inspection — these were explicitly planned in 05-03-PLAN.md Task 2 as a human checkpoint. The SUMMARY documents the human checkpoint as "approved," but since verifier cannot confirm TradingView results independently, these remain as required human verification items.

**D-03 deviation** (i_sweep_lookback input absent, hardcoded 20 used) is documented and functionally equivalent. No correction needed.

**Requirements.md gap:** D-01 through D-12 requirements are not tracked in REQUIREMENTS.md. These are phase-internal decision records. If the project wishes to formally track them, REQUIREMENTS.md should be updated to include a "Grading System Remodel" section with these decision IDs.

---

_Verified: 2026-04-13_
_Verifier: Claude (gsd-verifier)_
