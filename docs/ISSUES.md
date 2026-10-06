# IFVG Pro - Issue Tracker

Issues identified, root causes, and applied solutions for maintainability and future reference.

---

## Issue 1: ITH/ITL Mitigation Not Triggered on Body Close-Through

**Status:** Resolved (2026-10-05, verified on TradingView)
**Commits:** `257efaf` (rendering fix, reverted by `732356d`), "Phase 4: ITH/ITL close-through break and liquidity memory model"
**Affected Code:** `check_liquidity_sweeps()` (Section 6), `render_liquidity_lines()` (Section 10)

**Symptom:** ITH/ITL levels only became mitigated when a wick went through and the candle closed back. A candle body closing straight through left the level live, and a later wick back through it was wrongly counted as a sweep.

**Root Cause:** Close-through invalidation existed only for EQH/EQL. It had been removed for ITH/ITL during the PD zone work (`0cd3767`) to keep them as dealing-range anchors. Rendering also ignored the broken state for ITH/ITL.

**Decision (2026-10-05):** Swept and broken are different events and must stay different:
- **Swept (✗):** wick through, body closes back inside → stop hunt; can credit a setup's sweep.
- **Broken (⊘):** body closes through → level is gone; it can never be "swept" later.

The PD dealing range now uses its own `g_pd_liquidity_array` (`select_dealing_range_source()`), so breaking chart ITH/ITL no longer affects PD zones.

**Solution:**
- `check_liquidity_sweeps()`: close-through invalidation applies to ITH/ITL as well as EQH/EQL.
- Rendering: ITH/ITL have three states: live (yellow dashed), swept (faded dotted ✗), broken (grey dotted ⊘).

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

---

## Issue 10: Liquidity Memory Forgot Levels After 4 New Ones

**Status:** Resolved (2026-10-05, verified on TradingView)
**Commits:** "Phase 4: ITH/ITL close-through break and liquidity memory model"
**Affected Code:** `cleanup_liquidity_array()` (Section 4), `create_internal_levels()` (Section 6), `render_liquidity_lines()` and dashboard (Sections 10-11)

**Symptom:** A sweep inside a setup was not credited, and old major highs/lows were never recognised when price returned to them.

**Root Cause:** One setting, "Max Liquidity Levels" (default 4), controlled both what was drawn and what was remembered. Every new level pushed the oldest out (FIFO), so the oldest and most important levels were forgotten first.

**Decision (2026-10-05):** Separate memory from drawing, with no user setting:
- **Memory:** live levels are kept until swept or broken, however old (hard cap 100). Mitigated levels are kept 500 bars after mitigation (needed to credit sweeps within `max_bars_back`), then forgotten. Above the cap, the oldest mitigated level is dropped before any live one.
- **Drawing:** only the 3 nearest live levels above and below price; mitigated levels only with "Show Mitigated Liquidity".
- A swing already turned into an ITH/ITL is never turned into a level again (`g_last_internal_bar`), so a forgotten swept level can't come back as a fresh one.

**Solution:**
- Removed the "Max Liquidity Levels" input; added constants `LIQ_MEMORY_MAX`, `LIQ_MITIGATED_KEEP_BARS`, `LIQ_DRAW_PER_SIDE`.
- New `mitigated_bar` field on `Liquidity`.
- "Show Mitigated EQL/EQH" replaced by "Show Mitigated Liquidity" (covers all types, default off).
- Dashboard "Liquidity:" counts live levels only.

---

## Issue 11: Multi-Candle Raids Not Credited as Sweeps

**Status:** Open — deferred (test first, then decide); revisit after the swing rework and before the grading remodel (#8)
**Affected Code:** `check_setup_sweep()` (Section 7)
**Details:** `.planning/todos/pending/multi-candle-sweep-rule.md`

**Symptom:** A textbook sweep on an "A- SELL" setup (2026-10-05) showed "Delivery only".

**Suspected Cause:** Rule 2 requires the first candle that swept the level to be the extreme of the move. In a multi-candle raid, an earlier candle sweeps the level and a later one makes the top, so the sweep is rejected.

**Proposed Fix (not applied):** count the sweep if the level was swept inside the window, the move's extreme is at or after the sweep, and no candle closed beyond the level between the sweep and the inversion.

**Why deferred:** the current rule fails safe (under-credits, never invents sweeps); the swing rework changes the ITH/ITL set; more examples are needed before changing a grading input.

---

## Issue 12: Swing Detection Used a Fixed 5-Bar Lookback Setting

**Status:** Resolved (2026-10-05, verified on TradingView)
**Commits:** "Phase 4: automatic swing detection (no lookback setting)"
**Affected Code:** `detect_swing_points()`, `create_internal_levels()` (Section 6), `cleanup_liquidity_array()` (Section 4)
**Spec:** `.planning/notes/auto-swing-detection.md`

**Symptom:** Swings confirmed slowly (5 bars = 20 h on H4), chop produced swings, and exact double tops produced no swing at all (each high was "not higher" than the other), so obvious highs had no ITH.

**Root Cause:** One number (`i_swing_lookback`) controlled both significance and confirmation delay, and ignored volatility.

**Decision (2026-10-05):** No lookback settings for end users. A timeframe table was rejected: bar counts are already timeframe-invariant; what differs between charts is noise and volatility. Chose Option D (ICT 3-candle candidate + ATR displacement confirmation). On equal highs/lows the first candle is the swing; the second is paired by the EQH/EQL logic.

**Solution:**
- Candidate: `high[1] > high[2]` and `high[1] >= high[0]` (lows mirrored).
- Confirmed when a candle closes ≥ 1 ATR (`SWING_CONFIRM_ATR`) away; cancelled if price trades beyond it first.
- `create_internal_levels()` creates an ITH/ITL for every newly confirmed swing (several can confirm on one candle).
- "Swing Lookback" input removed. The PD swing lookback is a separate later step.
- Liquidity memory limit raised to 200 (`LIQ_MEMORY_MAX`). When full and no mitigated level is left to drop, the live level farthest from price is dropped (not the oldest), so major levels within reach are kept. Verified: memory fills with mitigated levels, live levels untouched.

**Note — settings shift after removing an input:** TradingView stores input values by position. Removing an input shifts saved values onto the wrong settings (observed: "Show ITH/ITL" turned off, hiding all ITH/ITL). After any update that removes a setting: open settings → Defaults → Reset settings (then re-save your own defaults).

---

## Issue 13: Important Swing Levels Hidden Behind Minor Pullback Levels

**Status:** Resolved (2026-10-06, verified on TradingView, 1m and 15m)
**Commits:** "Phase 4: Strong High/Low (structure-based) liquidity drawing"
**Affected Code:** `create_internal_levels()`, `find_swing_before()`, `check_liquidity_sweeps()` (Section 6), `render_liquidity_lines()` (Section 10)
**Spec:** `.planning/notes/major-minor-liquidity.md`

**Symptom:** With only the 3 nearest live levels per side drawn, the high that started a whole leg was hidden behind small pullback highs closer to price, although it was still live in memory.

**Rejected approach:** "Major" = price moved ≥ 3 ATR away at any time since the swing. On TradingView 85 of 87 live levels became major (distance grows with time). A first-leg ATR variant was also rejected (a 1-ATR bounce forms a swing and cuts a big leg in two).

**Decision (2026-10-06):** ICT/SMC strong vs weak, named "Strong High" / "Strong Low":
- **Strong High:** after the ITH, a candle closes below the swing low the rally came from before a newer swing high confirms (it broke structure).
- **Strong Low:** mirrored.
- **Weak (shown as ITH/ITL):** a newer swing forms first, or the level is mitigated first.
- Decided once during that leg; no ATR, no setting.

**Solution:**
- New `Liquidity` fields `is_strong`, `is_decided`, `structure_ref`.
- Drawing per side: 3 nearest live strong + 3 nearest live weak (weak includes EQH/EQL); strong = width 2, label "Strong High"/"Strong Low".
- Drawing only; sweeps, DOL, SL and grading unchanged.
- Verified: about 60% of *live* levels are strong (weak pullback levels are usually mitigated quickly, so the live set leans strong); 1 undecided level per chart.

**Known cosmetic issue:** labels overlap when a level sits at nearly the same price as a setup line (e.g. "Strong Low" over "B BUY").

---

## Issue 14: No Swings Detected (Liquidity 0) Without Debug Code

**Status:** Resolved (2026-10-06, verified on TradingView, several symbols)
**Affected Code:** swing detection (now inline in Section 12, Step 1), `create_internal_levels()` (Section 6), swing globals (Section 3)

**Symptom:** After the Strong High/Low change, the dashboard showed Liquidity 0 and no ITH/ITL/EQH/EQL on any symbol or timeframe. Builds with debug counters *inside* `detect_swing_points()` worked (1,339 confirmed highs); every build without them, including one that only read the swing arrays from outside, gave 0 swings.

**Cause:** TradingView skipped the body of `detect_swing_points()` (a function whose body was a single `if` and whose result was unused). The swing rules themselves were correct. A first attempt (moving the `high[1]`/`high[2]` checks to global scope and passing them in) did not help.

**Solution:**
- Swing detection runs inline in the main loop (Step 1); there is no `detect_swing_points()` function any more.
- Candidate checks (`swing_ready`, `swing_cand_high`, `swing_cand_low`) are computed at global scope on every bar.
- Strong High/Low at creation no longer scans `close[k]` up to 499 bars back. Each pending swing tracks `far_close` (lowest close since a swing high, highest since a swing low) and the check uses that. Same result, no long history lookback.

**Rule for future changes:** don't wrap code that only mutates `var` arrays in a function whose result is unused. If detection silently produces nothing, check the dashboard Liquidity count first.
