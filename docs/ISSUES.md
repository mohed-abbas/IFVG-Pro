# IFVG Pro - Issue Tracker

Issues identified, root causes, and applied solutions for maintainability and future reference.

---

## Issue 1: ITH/ITL Mitigation Not Triggered on Body Close-Through

**Status:** Regressed — fix reverted by `732356d`; ITH/ITL close-through invalidation later removed in `0cd3767` for PD zones
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

**Status:** Regressed — fix reverted by `732356d`
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

**Status:** Resolved (re-applied 2026-10-05, verified on TradingView)
**Commits:** `404f307` (reverted by `732356d`), re-applied in "Fix SL check asymmetry and remove dead calculate_stop_loss()"
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

**Status:** Resolved (2026-10-05, verified on TradingView) — replaced by a structural rule, no setting
**Commits:** `404f307` (input-based fix, reverted by `732356d` and superseded), "Phase 4: structural sweep window"
**Affected Code:** `check_setup_sweep()` (Section 7), called from `check_inversions()`

**Symptom:** The sweep window was a fixed 20 bars from the inversion candle. 20 bars = 20 minutes on M1 but 80 hours on H4, and any sweep of any level inside the window counted, even when unrelated to the setup.

**Root Cause:** A bar count has no meaning of its own; it neither scales with timeframe nor tests whether the sweep caused the reversal.

**Decision (2026-10-05):** No lookback settings for end users — bar-count windows are confusing for non-technical traders and inconsistent across timeframes. Options considered: fixed clock time (A), timeframe table (B), structural window (C), C + safety cap (D). **Chose C, strict.**

**Solution:** A sweep counts toward a setup only if:
1. it happened between the source FVG's first candle (`fvg.start_bar`) and the inversion candle, inclusive (strict: sweeps before the gap formed do not count); and
2. the sweep candle's wick is the extreme of that move (lowest low for bullish IFVGs, highest high for bearish).

The window is therefore set by the setup itself (3 candles on a fast M1 setup, 40 on a slow H4 one). Technical cap: 499 bars (`max_bars_back = 500`). If good setups lose sweep credit in practice, the window can be loosened to start at the swing that began the move.

---

## Issue 5: Momentum Assessment Only Analyzed Single Inversion Candle

**Status:** Partially fixed — reverted by `732356d`, re-implemented in Phase 5 (`cde420d`); no chop penalty yet
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

**Status:** Resolved (re-applied 2026-10-05, verified on TradingView)
**Commits:** `404f307` (reverted by `732356d`), re-applied in "Fix SL check asymmetry and remove dead calculate_stop_loss()"
**Affected Code:** Removed function (was ~lines 1289-1300)

**Symptom:** The standalone `calculate_stop_loss()` function was never called anywhere in the codebase.

**Root Cause:** The SL calculation in `check_inversions()` reimplemented the logic inline. The standalone function was leftover from an earlier refactor.

**Solution:**
- Removed the dead function entirely.

---

## Issue 7: FVG Merge Creating Oversized Zones on Lower Timeframes

**Status:** Regressed — size-ratio/proximity guards reverted by `732356d`; opposite-color rule added later (`23c84e7`, `817ed9f`, `140634e`)
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

**Status:** Done early in Phase 5 (5-criterion scoring); full remodel still pending
**Affected Code:** `calculate_grade()`, grading inputs (Section 7-8)

**Description:** The current grading system has several misunderstandings and needs a complete remodel. To be tackled after all other issues are resolved, with discussion to align on the desired grading logic.

---

## Issue 9: "Bar index too far" Runtime Error on Old Drawings

**Status:** Resolved (2026-10-05, verified on TradingView)
**Affected Code:** New `clamp_left_bar()` (Section 4); all left-edge anchors in Section 10 rendering

**Symptom:** `Error on bar 6670: Bar index value of the left argument (1669) in box.new() is too far from the current bar index` at `render_htf_ifvg_boxes()`.

**Root Cause:** `c976911` removed the 400-bar clamp so boxes anchor at their formation bar. TradingView rejects bar_index x-coordinates more than 5000 bars from the current bar, so any zone still live 5000+ bars after forming (most often HTF IFVGs) crashed the script.

**Solution:**
- Added `clamp_left_bar(x)` which keeps the true anchor unless it is more than 4999 bars back.
- Applied to FVG/IFVG boxes (LTF and HTF), SL/BE/entry lines, liquidity lines, and PD/OTE lines.
- The vertical formation divider is skipped (not clamped) when older than 5000 bars, so it never tilts.
