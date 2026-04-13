---
phase: 05-grading-system-remodel
reviewed: 2026-04-12T00:00:00Z
depth: standard
files_reviewed: 1
files_reviewed_list:
  - src/IFVG_Indicator.pine
findings:
  critical: 0
  warning: 5
  info: 4
  total: 9
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-04-12
**Depth:** standard
**Files Reviewed:** 1
**Status:** issues_found

## Summary

Phase 5 added five significant changes to `src/IFVG_Indicator.pine`: three new `IFVG` type fields (`has_delivery`, `pd_zone`, `singularity_score`), the `check_delivery_from_fvg()` function, a rewritten `assess_momentum()` returning `int 0-2`, three helper scoring functions (`score_target_clarity`, `score_singularity`, `score_pd_zone`), a rewritten `calculate_grade()` using checklist scoring, and updated tooltip rendering. The overall structure is solid and follows project conventions. No security or repainting issues were found. The concerns below are correctness and logic bugs that affect grading accuracy.

---

## Warnings

### WR-01: Tooltip momentum score diverges from stored momentum score

**File:** `src/IFVG_Indicator.pine:2005`
**Issue:** The tooltip re-derives the momentum score from `ifvg.momentum` (the `string` field) instead of using `ifvg.singularity_score` / `ifvg.momentum` as a cached int. This is the right approach for `tt_sg` (uses `ifvg.singularity_score`) but is inconsistent for momentum. More importantly, the `momentum` string is derived by mapping `momentum_score` (int) back to a string at line 1650, then the tooltip maps the string back to an int at line 2005. If the int-to-string mapping at line 1650 and the string-to-int mapping at line 2005 ever drift, the displayed tooltip score will silently differ from the score used in `calculate_grade()`.

The string bridge exists only for "backward compatibility" (line 1649 comment). The IFVG type already stores `singularity_score` as an `int` — the same pattern should be applied to momentum.

**Fix:** Add a `momentum_score` int field to the `IFVG` type and store the raw int directly, then use it in the tooltip instead of re-deriving from the string. As an immediate lower-risk fix, at least add an assertion comment that the two mappings must stay in sync, and move the string-to-int conversion to a shared helper function.

```pine
// In IFVG type (line ~102):
int momentum_score  // 0=weak, 1=moderate, 2=strong (raw assess_momentum result)

// In check_inversions() (line ~1679):
momentum_score = momentum_score,   // store the int directly

// In tooltip (line 2005):
int tt_mom = ifvg.momentum_score   // read cached int, not re-derived
```

---

### WR-02: `check_delivery_from_fvg` body-respect check uses current-bar series offsets, not candidate-relative offsets

**File:** `src/IFVG_Indicator.pine:1388-1437`
**Issue:** The inner loop `for k = 1 to check_bars` uses `close[k]` — a series offset relative to the **current bar** — to check whether price respected the FVG zone during delivery. `check_bars` is capped at `bar_dist` (distance from the FVG end to the current bar), so `close[1]` through `close[check_bars]` does cover the correct historical window. However, this means the check window starts at `close[1]` (one bar before the current bar) and goes back `check_bars` bars. If the inversion candle itself (the current bar, `close[0]`) violated the zone it would be missed, but more importantly the window is measured back from **now** rather than from the FVG's end bar.

For a recent FVG (`bar_dist = 3`) `close[1..3]` covers the right bars. But the check includes any bar in the lookback window regardless of whether that bar was before or after the FVG formed — if there was a zone violation at `close[3]` but the FVG only formed 2 bars ago, `close[3]` is actually older than the FVG's source and should not count.

**Fix:** The `k` loop should start at `bar_dist` (oldest bar of the delivery window) and count down to `1`, and ideally verify `k` maps to a bar that is after `candidate.end_bar`. The safest fix is to compute check_bars as `math.min(bar_dist - 1, 50)` and loop `for k = 1 to check_bars` unchanged — this avoids checking the bar before the FVG formed — but a more precise approach anchors the offset to `candidate.end_bar`.

```pine
// Replace:
int check_bars = math.min(bar_dist, 50)
for k = 1 to check_bars
// With (excludes bars older than the FVG's end bar):
int check_bars = math.min(bar_dist - 1, 50)
for k = 1 to check_bars
```

---

### WR-03: `calculate_grade()` duplicates `score_singularity()` call already done in `check_inversions()`

**File:** `src/IFVG_Indicator.pine:1505, 1655`
**Issue:** In `check_inversions()` at line 1655, `score_singularity()` is called to get `singular_score`, and the result is stored on `ifvg.singularity_score`. Then `calculate_grade()` at line 1505 also calls `score_singularity()` internally. This means `score_singularity` runs twice per inversion with the same inputs. More critically, the two calls happen in close sequence so the results should agree — but it creates fragile double-computation. If `is_fvg_singular` or `atr_value` somehow differed between the two calls (they don't today, but it's error-prone), the stored `singularity_score` and the score used for `grade` would silently diverge.

The same risk exists for the DOL target score: `score_target_clarity` is called at line 1503 (inside `calculate_grade`) and again at line 2006 (in the tooltip). The tooltip call is correct since it reads live state, but the graded score was computed from the DOL at inversion time, which may differ from the current DOL after `update_dol_status()` refreshes it.

**Fix:** Pass the already-computed `singular_score` into `calculate_grade()` rather than recomputing it inside. This removes the double call and makes `singularity_score` the single source of truth.

```pine
// Change signature to accept pre-computed score:
calculate_grade(bool has_sweep, bool has_delivery, int momentum_score,
                Liquidity dol_target, int singularity_score,
                string pd_zone, bool ifvg_is_bullish) =>
    // ...
    // Remove internal score_singularity() call
    int singular_score = singularity_score  // use passed value

// In check_inversions() call site (line 1656):
string grade = calculate_grade(has_sweep, has_delivery, momentum_score,
                               dol, singular_score, "neutral", ifvg_is_bullish)
```

---

### WR-04: Tooltip total score can differ from stored grade

**File:** `src/IFVG_Indicator.pine:2004-2009`
**Issue:** The tooltip recomputes `tt_total` from current state at render time (line 2009). The grade shown is `ifvg.grade` (set at inversion time), but `tt_total` uses the current DOL (`ifvg.dol` may have been refreshed by `update_dol_status()`), current `ifvg.pd_zone`, and current `ifvg.singularity_score`. These can differ from values used to compute the grade at inversion time, creating a mismatch where the tooltip shows "Grade: B+ (6/10)" but the numbers don't add up to 6. This is misleading to the trader who reads the tooltip as the explanation for the grade.

**Fix:** Either (a) cache the five criterion scores at inversion time as IFVG fields and display those frozen values in the tooltip, or (b) add a clear note in the tooltip that the breakdown reflects current conditions, not the time of grading. Option (a) is preferred for precision. Option (b) is a quick win with minimal code change:

```pine
// Change tooltip header line:
"Grade: " + ifvg.grade + " (at inversion) | Now: " + str.tostring(tt_total) + "/10\n"
```

---

### WR-05: `assess_momentum` uses global `atr_value` but is called with candle OHLC values suggesting isolation

**File:** `src/IFVG_Indicator.pine:1277-1316`
**Issue:** `assess_momentum` accepts `inv_open, inv_high, inv_low, inv_close` as parameters (implying it could work with arbitrary candle data), but internally it reads `close[k]`, `open[k]`, `high[k]`, `low[k]`, and `atr_value` directly as global series. This means the function always evaluates momentum for the **current bar's context**, not for arbitrary candles. When called from `check_inversions()` at line 1648 with `open, high, low, close` — the current bar — this is correct. However, the function signature implies it could be called for a different bar's OHLC values, which would silently produce wrong results because the inner series accesses would still reference the current bar.

This is a latent bug: if `check_inversions()` were ever refactored to call `assess_momentum` with saved OHLC values (e.g., for re-grading), the function would return incorrect scores without any error.

**Fix:** Document the constraint explicitly in the function signature, or make the series dependency explicit by removing the parameters and relying purely on the global series (since `open, high, low, close` are always the current bar anyway):

```pine
// Option A: Document the constraint
// NOTE: Parameters must be current-bar open/high/low/close only.
// The function uses series offsets [k] relative to the current bar.
assess_momentum(float inv_open, float inv_high, float inv_low, float inv_close) =>

// Option B: Remove misleading parameters (simplest)
assess_momentum() =>
    // Use open, high, low, close directly
```

---

## Info

### IN-01: `calculate_stop_loss()` function is now dead code

**File:** `src/IFVG_Indicator.pine:1321-1332`
**Issue:** The `calculate_stop_loss()` function (declared at line 1321) is never called. SL calculation is inlined directly in `check_inversions()` at lines 1604-1621. The function takes an `inv_close` parameter it never uses.

**Fix:** Remove the dead function, or replace the inlined SL logic in `check_inversions()` with a call to it.

---

### IN-02: `score_pd_zone` comment says A+ is unreachable — this should be a user-visible warning

**File:** `src/IFVG_Indicator.pine:1477-1478`
**Issue:** The comment correctly notes that `pd_zone` is always `"neutral"` (returns score 1), so `pd_score` can never reach 2, making the A+ hard gate (`pd_score == 2`) permanently impossible. A trader relying on the grade display will never see A+ regardless of setup quality, with no indication why.

**Fix:** Add a dashboard indicator or tooltip note when A+ is structurally blocked (pd_zone always neutral). Alternatively, remove the A+ hard gate on `pd_score == 2` until PD zone detection is re-implemented, so A+ remains achievable.

---

### IN-03: Tooltip `sd_detail` string build uses deeply nested ternaries that are hard to maintain

**File:** `src/IFVG_Indicator.pine:2010`
**Issue:** The line at 2010 chains three nested ternary operators. Pine Script evaluates these correctly but they are fragile to edit and the condition `ifvg.has_sweep and ifvg.has_delivery` at the outer level is already evaluated as `tt_sd` at line 2004. Using the already-computed `tt_sd` value would be cleaner and reduce drift risk.

**Fix:**
```pine
string sd_detail = tt_sd == 2 ? "Sweep+Delivery" : (tt_sd == 1 ? (ifvg.has_sweep ? "Sweep only" : "Delivery only") : "Neither")
```

---

### IN-04: Header comment still says "Phase 3" — should reflect Phase 5 additions

**File:** `src/IFVG_Indicator.pine:3`
**Issue:** The banner on line 3 reads `Phase 3: Multi-Timeframe`. Phase 5 added significant new features (delivery detection, checklist grading, singularity scoring) that are not reflected in the file header.

**Fix:** Update the banner and add a Phase 5 section listing the new features, following the same pattern as the Phase 1-3 sections.

---

_Reviewed: 2026-04-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
