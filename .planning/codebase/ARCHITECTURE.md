# Architecture

**Analysis Date:** 2026-03-23

## Pattern Overview

**Overall:** Single-file pipeline architecture (INPUTS -> ENGINE -> RENDERING) in Pine Script v6.

The indicator is a monolithic 2511-line Pine Script file (`src/IFVG_Indicator.pine`) organized into 12 numbered sections. There is no module system -- Pine Script v6 does not support imports or separate files. All logic runs bar-by-bar on confirmed candles only (`barstate.isconfirmed`), with global arrays serving as the persistent data store between bars.

**Key Characteristics:**
- Bar-by-bar execution model -- the main loop (Section 12) runs once per confirmed bar
- No repainting -- all detection logic gates on `barstate.isconfirmed`
- State persisted via `var` arrays that survive across bars
- Pipeline pattern: detect -> update state -> check inversions -> grade -> render
- Multi-timeframe data pulled via `request.security()` calls (Phase 3)

## Layers

**Input Layer (Section 2, lines 124-283):**
- Purpose: User-configurable parameters organized into input groups
- Location: `src/IFVG_Indicator.pine` lines 124-283
- Contains: 9 input groups with `input.bool`, `input.int`, `input.float`, `input.string`, `input.color`, `input.timeframe` declarations
- Depends on: Nothing
- Used by: Every other section reads `i_*` prefixed variables

**Type Layer (Section 1, lines 36-123):**
- Purpose: Custom type definitions for all domain objects
- Location: `src/IFVG_Indicator.pine` lines 36-123
- Contains: 5 custom types: `FVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`, `IFVG`
- Depends on: Nothing
- Used by: All data store arrays, all detection/rendering functions

**Data Store Layer (Section 3, lines 284-307):**
- Purpose: Global `var` arrays that persist state across bars
- Location: `src/IFVG_Indicator.pine` lines 284-307
- Contains: 7 typed arrays initialized once with `var`
- Depends on: Type definitions (Section 1)
- Used by: Engine and Rendering layers read/write these arrays

**Utility Layer (Section 4, lines 310-597):**
- Purpose: Helper functions for color, grading, cleanup, delivery detection, swing validation
- Location: `src/IFVG_Indicator.pine` lines 310-597
- Contains: Grade conversion, color helpers, array cleanup (FIFO), delivery tracking functions, swing integrity checks, EQH/EQL quality classification
- Depends on: Input layer, Data store layer
- Used by: Engine and Rendering layers

**Detection Engine (Sections 5-6, lines 598-1223):**
- Purpose: Core FVG detection (LTF + HTF) and liquidity/swing detection
- Location: `src/IFVG_Indicator.pine` lines 598-1223
- Contains: `detect_fvg()`, `detect_htf_fvg()`, HTF data via `request.security()`, `detect_swing_points()`, `check_equal_highs()`, `check_equal_lows()`, `create_internal_levels()`, `check_liquidity_sweeps()`
- Depends on: Input layer, Data store, Utility layer, ATR calculation
- Used by: Main loop (Section 12)

**Grading & Inversion Engine (Sections 7-8, lines 1224-1637):**
- Purpose: BE/SL calculation, DOL finding, sweep detection, momentum assessment, grading algorithm, and FVG->IFVG inversion logic
- Location: `src/IFVG_Indicator.pine` lines 1224-1637
- Contains: `find_previous_swing_high/low()`, `find_dol()`, `check_recent_sweep()`, `assess_momentum()`, `calculate_stop_loss()`, `calculate_grade()`, `check_inversions()`
- Depends on: Data store, swing point arrays, liquidity arrays
- Used by: Main loop (Section 12)

**State Update Layer (Section 9, lines 1638-1749):**
- Purpose: Update BE/SL status, refresh DOL targets, detect IFVG mitigations
- Location: `src/IFVG_Indicator.pine` lines 1638-1749
- Contains: `update_be_status()`, `update_dol_status()`, `check_mitigations()`
- Depends on: Data store (g_ifvg_array, g_liquidity_array)
- Used by: Main loop (Section 12)

**Rendering Layer (Sections 10-11, lines 1751-2387):**
- Purpose: Draw all visual elements (boxes, lines, labels, dashboard table)
- Location: `src/IFVG_Indicator.pine` lines 1751-2387
- Contains: `render_fvg_boxes()`, `render_ifvg_boxes()`, `render_htf_fvg_boxes()`, `render_htf_ifvg_boxes()`, `render_liquidity_lines()`, `render_dashboard()`
- Depends on: Data store arrays, Input layer (visibility/style settings)
- Used by: Main loop (Section 12)

**Main Execution Loop (Section 12, lines 2388-2511):**
- Purpose: Orchestrates the entire pipeline in correct order
- Location: `src/IFVG_Indicator.pine` lines 2388-2511
- Contains: Sequential calls to all detection, update, and rendering functions
- Depends on: All other sections
- Used by: TradingView runtime (called each bar)

## Data Flow

**Per-Bar Processing Pipeline (Section 12):**

1. `detect_swing_points()` -- find swing highs/lows at `[lookback]` offset
2. `check_equal_highs()` + `check_equal_lows()` + `create_internal_levels()` -- form EQH/EQL/ITH/ITL liquidity levels
3. `cleanup_liquidity_array()` -- FIFO trim to `i_max_liquidity`
4. `check_liquidity_sweeps()` -- mark swept/broken liquidity levels
5. `detect_fvg()` -- detect new LTF 3-candle FVG patterns
6. `record_fvg_for_delivery()` + `update_delivery_traversal()` -- track FVG delivery history
7. `detect_htf_fvg()` (x2, one per HTF timeframe) -- detect HTF FVGs via `request.security()`
8. `check_inversions()` -- check if any active FVG has been inverted (body close through zone)
9. `check_htf_inversions()` (x2) -- same for HTF FVGs
10. `check_htf_mitigations()` (x2) -- remove mitigated HTF IFVGs
11. `update_be_status()` -- check if BE targets reached, if SL levels hit
12. `update_dol_status()` -- refresh stale DOL targets
13. `check_mitigations()` -- remove mitigated LTF IFVGs
14. `find_most_recent_ifvg()` -- get latest IFVG for dashboard display
15. Render all: `render_fvg_boxes()`, `render_ifvg_boxes()`, HTF boxes, `render_liquidity_lines()`, `render_dashboard()`

**State Management:**
- All state lives in 7 global `var` arrays declared at lines 289-304
- `var` keyword in Pine Script means the array is initialized once and persists across bars
- Arrays are modified in-place; objects are mutated directly via field assignment (e.g., `fvg.status := "inverted"`)
- Each array has a max size enforced by FIFO cleanup functions that `array.shift()` the oldest entry when exceeded

## Key Abstractions

**FVG (Fair Value Gap):**
- Purpose: Represents a 3-candle price gap (imbalance zone)
- Defined at: `src/IFVG_Indicator.pine` lines 46-56
- Lifecycle: `"active"` -> `"inverted"` (becomes IFVG) or `"mitigated"` (removed)
- Key fields: `top`, `bottom`, `is_bullish`, `status`, `timeframe`, `box_id`
- Created by: `detect_fvg()` (line 605) or `detect_htf_fvg()` (line 685)

**IFVG (Inverted Fair Value Gap):**
- Purpose: An FVG that has been inverted by a body close through its zone; the primary trading setup
- Defined at: `src/IFVG_Indicator.pine` lines 92-122
- Lifecycle: Created when FVG inverts -> `"inverted"` (active setup) -> `"mitigated"` (removed)
- Key fields: `grade`, `entry_valid`, `be_level`, `be_status`, `sl_level`, `has_sweep`, `has_delivery`, `momentum`, `dol`
- Created by: `check_inversions()` (line 1470) or `check_htf_inversions()` (line 765)

**SwingPoint:**
- Purpose: Represents a swing high or swing low used for structure analysis
- Defined at: `src/IFVG_Indicator.pine` lines 58-64
- Pattern: Detected at `[lookback]` offset using left/right bar comparison
- Created by: `detect_swing_points()` (line 872)
- Used for: EQH/EQL formation, BE level calculation, SL placement

**Liquidity:**
- Purpose: Represents a liquidity level (EQH, EQL, ITH, ITL) that can be swept
- Defined at: `src/IFVG_Indicator.pine` lines 67-79
- Lifecycle: created -> `is_valid=true` -> swept (`is_swept=true`) or broken (`is_valid=false`)
- Quality classification: `"perfect"` (within 0.02 ATR) or `"relative"` (within 0.10 ATR)
- Used for: Grading (sweep detection), DOL targeting, dashboard display

**DeliveryFVG:**
- Purpose: Lightweight FVG record tracking whether price was "delivered" from a prior same-direction FVG
- Defined at: `src/IFVG_Indicator.pine` lines 82-89
- Pattern: Recorded when any FVG forms, checked when inversion occurs
- Created by: `record_fvg_for_delivery()` (line 426)
- Checked by: `check_delivery()` (line 480)

## Entry Points

**TradingView Runtime Entry:**
- Location: `src/IFVG_Indicator.pine` line 30 (`indicator(...)`)
- Triggers: TradingView calls the script once per bar
- Responsibilities: Configures overlay mode, sets max_bars_back/boxes/lines/labels limits

**Main Execution Gate:**
- Location: `src/IFVG_Indicator.pine` line 2392 (`if i_show_indicator`)
- Triggers: Every bar, but only if the indicator is enabled
- Responsibilities: Runs the entire detection -> update -> render pipeline

**HTF Data Entry:**
- Location: `src/IFVG_Indicator.pine` lines 653-680 (`request.security(...)` calls)
- Triggers: Evaluated by TradingView on each bar automatically
- Responsibilities: Pulls OHLC and ATR data from two configurable higher timeframes

## Key Algorithms

**FVG Detection (`detect_fvg()`, line 605):**
- 3-candle pattern: bullish if `low[0] > high[2]`, bearish if `high[0] < low[2]`
- Minimum gap size filter: gap must exceed `ATR * i_fvg_min_size_mult` (default 0.25)
- Only one FVG detected per bar (bullish checked first)

**Inversion Detection (`check_inversions()`, line 1470):**
- Iterates active FVGs in reverse (newest first)
- Bullish FVG inversion: price enters zone AND body closes below `fvg.bottom`
- Bearish FVG inversion: price enters zone AND body closes above `fvg.top`
- On inversion: creates IFVG with full grading data, removes FVG from active array

**Grading Algorithm (`calculate_grade()`, line 1398):**
- Step 1 (Tier): Must have DOL target or grade is "C". Has sweep+delivery = "A" tier. Has sweep OR delivery = "A" tier. Neither = "B" tier.
- Step 2 (Modifier): Quality score from momentum (+1/-1), FVG clarity (+1/-1), bonus for both sweep AND delivery (+1)
- Step 3 (Combine): A tier + score>=2 = "A+", score>=1 = "A", score>=0 = "A-", else "B+". B tier + score>=1 = "B+", score>=0 = "B", else "B-".

**Liquidity Sweep Detection (`check_liquidity_sweeps()`, line 1193):**
- BSL sweep (EQH/ITH): `high > level AND close < level` (wick above, body stays below)
- SSL sweep (EQL/ITL): `low < level AND close > level` (wick below, body stays above)
- Complete break: close through level invalidates without sweep marker

**EQH/EQL Detection (`check_equal_highs()` line 933, `check_equal_lows()` line 1028):**
- Compares most recent swing against up to 10 previous swings
- Both swings must be intact (not broken through by close)
- Validates formation direction (EQH: new <= old, EQL: new >= old)
- Price difference must be within ATR-based tolerance
- Liquidity must NOT have been swept between the two swings
- Quality: "perfect" if within `ATR * 0.02`, "relative" if within `ATR * 0.10`

**Delivery Detection (`check_delivery()`, line 480):**
- Searches `g_delivery_history` for a prior FVG matching IFVG direction
- Delivery FVG must have formed before source FVG
- Must be within `i_delivery_lookback` bars
- Price must have traversed the delivery FVG zone

## Error Handling

**Strategy:** Defensive programming with `na` checks and bounds validation.

**Patterns:**
- Every array access is guarded by `i < array.size(arr)` bounds checks
- `na()` checks on all float/object values before use (e.g., `not na(atr_value)`, `not na(fvg.box_id)`)
- Fallback values when swing points not found: uses FVG boundary as BE/SL default
- Drawing objects (box, line, label) always deleted before recreating to prevent orphans
- `bar_index` clamping with `math.max(start_bar, bar_index - 400)` to prevent "bar index too far" errors

## Memory Management

**TradingView Limits (set at line 30-34):**
- `max_bars_back = 500` -- maximum historical bars accessible
- `max_boxes_count = 500` -- maximum simultaneous box drawings
- `max_lines_count = 500` -- maximum simultaneous line drawings
- `max_labels_count = 500` -- maximum simultaneous label drawings

**Array Size Limits:**
- `g_fvg_array`: capped at `i_max_fvgs` (default 20, max 50)
- `g_ifvg_array`: capped at `i_max_ifvgs` (default 30, max 100)
- `g_liquidity_array`: capped at `i_max_liquidity` (default 30, max 100)
- `g_swing_highs` / `g_swing_lows`: hardcoded cap at 50 entries each (line 899, 923)
- `g_delivery_history`: cleaned by lookback period, no hard cap
- HTF arrays: use same `i_max_fvgs` / `i_max_ifvgs` limits

**Cleanup Strategy:**
- FIFO (`array.shift()`) -- oldest entries removed first
- Drawing cleanup on removal: every cleanup function deletes associated `box`, `line`, `label` objects
- Delivery history cleaned by age (`bar_index - record.end_bar > i_delivery_lookback`)
- Mitigated IFVGs removed from array entirely (not just marked)
- Rendering: all drawings deleted and recreated each bar to prevent stale visuals

## Cross-Cutting Concerns

**No-Repaint Guarantee:** Every detection function gates on `barstate.isconfirmed`. No calculations run on the forming candle.

**ATR-Based Sizing:** All distance thresholds use ATR multiples (FVG minimum size, EQH/EQL tolerances) making the indicator market-agnostic.

**HTF Bias Filtering:** When enabled, `render_ifvg_boxes()` (line 1835-1851) calculates HTF bias inline by checking the most recent HTF IFVG direction, and filters LTF setups that don't align.

**Visual Display Limiting:** `i_max_recent_display` (default 5) limits how many IFVGs are rendered, independent of how many are tracked. This prevents chart clutter while maintaining full data for grading.

---

*Architecture analysis: 2026-03-23*
