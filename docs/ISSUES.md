# IFVG Pro - Issue Tracker

Issues identified, root causes, and applied solutions for maintainability and future reference.

---

## Issue 1: ITH/ITL Mitigation Not Triggered on Body Close-Through

**Status:** Resolved
**Commits:** `257efaf`
**Affected Code:** `render_liquidity_lines()` (Section 10)

**Symptom:** ITH/ITL levels only marked as mitigated when a wick passed through. When a candle body closed directly through the level, it remained visually active.

**Root Cause:** The detection logic in `check_liquidity_sweeps()` was already correct -- it set `is_valid=false` for body close-through. The bug was entirely in rendering:
1. ITH/ITL color logic only checked `is_swept`, ignoring `is_valid=false`. Broken levels rendered with active color.
2. The skip/hide block for mitigated levels only covered EQH/EQL types, not ITH/ITL.

**Solution:**
- Expanded ITH/ITL rendering to check three states: swept (yellow faded, dotted), broken/invalid (gray, dotted), and active (yellow, dashed) -- matching EQH/EQL behavior.
- Added skip/hide logic for mitigated ITH/ITL with a separate `i_show_swept_ithl` input toggle (default: true), independent from the EQH/EQL setting. This avoids confusion since ITH/ITL and EQH/EQL are related but not identical concepts.

---

## Issue 2: SL Placed at Wrong Swing Point Instead of Nearest ITH/ITL

**Status:** Resolved
**Commits:** `257efaf`
**Affected Code:** `check_inversions()` (Section 8), new `find_previous_itl()` / `find_previous_ith()`

**Symptom:** Stop Loss was placed far below/above the setup, skipping nearby ITH/ITL levels.

**Root Cause:** Three compounding problems:
1. SL used `find_previous_swing_low/high()` (raw swing points) instead of searching for ITH/ITL levels in the liquidity structure.
2. The search used `fvg.start_bar` (when the FVG originally formed) instead of `bar_index` (the inversion bar). ITH/ITL levels created between FVG formation and inversion were excluded.
3. The fallback `find_previous_swing_low()` found the most recent swing by time without filtering by price, returning swings far from the setup.
4. `g_liquidity_array` only holds `i_max_liquidity` entries (default 4), so nearby ITLs were often cleaned out by FIFO.

**Solution:**
- Added `find_previous_itl(before_bar, below_price)` and `find_previous_ith(before_bar, above_price)` that search `g_liquidity_array` for ITH/ITL levels, filtering by both time (before inversion) and price direction (below for bullish SL, above for bearish SL).
- Fallback now searches `g_swing_lows`/`g_swing_highs` (50 entries) with the same price filter, instead of blindly returning the most recent swing.
- Changed call site from `fvg.start_bar` to `bar_index` so ITLs formed after the FVG but before the inversion are included.

---

## Issue 3: SL Check Asymmetry Between Creation and Tracking

**Status:** Resolved
**Commits:** `404f307`
**Affected Code:** `check_inversions()` (Section 8), BE/SL tracking loop (Section 9)

**Symptom:** A candle opening exactly at the SL level passed the creation check but got caught during the next bar's tracking update.

**Root Cause:** Inconsistent comparison operators:
- At creation: `low > sl_level` (exclusive -- touching SL was valid)
- During tracking: `low < sl_level` (strict -- touching SL was NOT caught)

A candle at exactly the SL level would pass creation but could trigger invalidation on the next bar depending on price action.

**Solution:**
- Unified tracking to use `low <= sl_level` / `high >= sl_level` (inclusive), so touching the SL level consistently means the stop was hit. Creation keeps `low > sl_level` (exclusive), meaning a setup isn't created if SL is already touched on the inversion candle.

---

## Issue 4: Sweep Lookback Hardcoded at 20 Bars

**Status:** Resolved
**Commits:** `404f307`
**Affected Code:** `check_inversions()` call to `check_recent_sweep()`

**Symptom:** The sweep detection lookback was hardcoded to 20 bars, which doesn't scale with timeframe. On M1 that's 20 minutes; on H4 it's 80 hours.

**Root Cause:** The `check_recent_sweep()` function already accepted a `lookback_bars` parameter, but the call site passed a hardcoded `20`.

**Solution:**
- Added `i_sweep_lookback` input (default 20, range 5-100) in the Grading Settings group.
- Call site now uses `i_sweep_lookback` instead of `20`, allowing users to adjust per timeframe.

---

## Issue 5: Momentum Assessment Only Analyzed Single Inversion Candle

**Status:** Resolved
**Commits:** `404f307`
**Affected Code:** `assess_momentum()` (Section 7)

**Symptom:** ICT "displacement" refers to the 3-5 candle directional move leading to inversion, but the function only looked at the inversion candle itself. A strong inversion candle after choppy action was treated the same as one after a clean displacement leg.

**Root Cause:** `assess_momentum()` only computed `body_ratio` and `candle_range` for the single inversion candle's OHLC values.

**Solution:**
- Enhanced `assess_momentum()` to also evaluate the 5 preceding candles for displacement:
  - Counts candles moving in the same direction with body ratio > 50% ("displacement candles")
  - Measures the total leg range from the 5th candle back to the inversion candle
- Combined assessment: "strong_no_chop" if either the inversion candle is strong OR the displacement leg has 2+ directional candles with leg range > 1.5x ATR.
- "weak_or_choppy" only when the inversion candle itself is weak (body < 30% of range or range < 0.5 ATR).

---

## Issue 6: `calculate_stop_loss()` Was Dead Code

**Status:** Resolved
**Commits:** `404f307`
**Affected Code:** Removed function (was ~lines 1289-1300)

**Symptom:** The standalone `calculate_stop_loss()` function was never called anywhere in the codebase.

**Root Cause:** The SL calculation in `check_inversions()` reimplemented the logic inline. The standalone function was leftover from an earlier refactor.

**Solution:**
- Removed the dead function entirely.

---

## Issue 7: FVG Merge Creating Oversized Zones on Lower Timeframes

**Status:** Resolved
**Commits:** `4e0bd50`
**Affected Code:** `merge_with_existing_fvg()` (Section 4)

**Symptom:** On lower timeframes, consecutive FVGs of very different sizes merged into a single enormous zone spanning an unrealistic price range.

**Root Cause:** The merge logic only checked temporal proximity (within 5 bars) and direction. It did not verify:
1. Whether the FVGs overlapped or were close in **price**
2. Whether the size difference between them was reasonable

Two FVGs at completely different price levels got merged just because they were close in time, creating a combined zone that included the gap between them.

**Solution:**
- Added **price proximity guard**: FVGs must overlap in price OR be within 0.5 ATR of each other to merge.
- Added **size ratio cap (3:1)**: If one FVG is more than 3x the size of the other, they stay as separate zones. This prevents a tiny FVG + huge FVG from creating a disproportionate combined zone.

---

## Issue 8: Grading System Remodel

**Status:** Pending
**Affected Code:** `calculate_grade()`, grading inputs (Section 7-8)

**Description:** The current grading system has several misunderstandings and needs a complete remodel. To be tackled after all other issues are resolved, with discussion to align on the desired grading logic.
