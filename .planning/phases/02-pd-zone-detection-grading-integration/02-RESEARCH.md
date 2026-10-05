# Phase 2: PD Zone Detection & Grading Integration - Research

**Researched:** 2026-04-14
**Domain:** Pine Script v6 — HTF data aggregation, ICT dealing-range detection via reused ITH/ITL logic, drawing lifecycle, grading hook
**Confidence:** HIGH for Pine v6 syntax/patterns (verified from codebase); MEDIUM for chosen HTF-ITH/ITL approach (novel; failed approaches excluded per CONTEXT)

## Summary

Phase 2 requires detecting the ICT dealing range on a user-selected higher timeframe, then supplying `pd_zone` at IFVG creation so the already-wired `score_pd_zone()` grading criterion can produce real scores (not the hardcoded `"neutral"` at lines 732 and 1684). Three prior approaches (`ta.pivothigh`+`valuewhen`, zigzag state machine, `ta.highest`/`lowest`) failed — they are locked out by CONTEXT D-01.

The chosen approach (D-01/D-02) is to compute **HTF swing highs/lows via `request.security` of the existing `ta.pivothigh`/`ta.pivotlow` primitives on the HTF timeframe**, then **mirror the existing `create_internal_levels()` ITH/ITL bookkeeping** on chart to get an array of HTF ITH/ITL entries with `is_valid`/`is_swept` tracking. The current unswept-newest ITH/ITL pair defines the dealing range. Rotation happens automatically via the existing sweep-detection machinery applied to the HTF-level array.

**Primary recommendation:** Extend the existing Phase 1 tuple `request.security` calls (or add one new small tuple) to also return `ta.pivothigh(n, n)` and `ta.pivotlow(n, n)` evaluated on the PD timeframe. Mirror `create_internal_levels()` into a parallel `create_pd_internal_levels()` that writes to a new `g_pd_liquidity_array`. Select newest unswept ITH and newest unswept ITL from that array; compute range, EQ, and `pd_zone` at IFVG creation time. Render 3 dashed lines with `percentage (price)` labels per D-07/D-08. Introduce a lightweight `DealingRange` type (not reuse `Liquidity`) to hold the current snapshot plus its 3 line + 3 label handles.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Dealing range top/bottom = HTF's ITH and ITL. Reuse existing `create_internal_levels()` logic against HTF-resampled data. Not raw swings, not `pivothigh`+`valuewhen`, not zigzag, not `ta.highest`/`ta.lowest`.
- **D-02:** Pick rule = most recent unswept by `bar_idx`. `swing_high_dr` = newest ITH where `is_valid=true AND is_swept=false`. `swing_low_dr` = newest ITL same criteria. Rotation via existing sweep/invalidation machinery.
- **D-03:** `pd_zone` computed at IFVG creation. Valid ITH+ITL pair + IFVG mid strictly above 50% → `"premium"`; strictly below → `"discount"`; exactly 50% → `"equilibrium"`; no pair → `"neutral"`.
- **D-04:** Default PD timeframe = `D`. Input via `input.timeframe()`; typical 1H/4H/D/W.
- **D-05:** When chart TF >= PD TF, skip `request.security`, use chart-TF ITH/ITL directly.
- **D-06:** No valid pair → `pd_zone = "neutral"`, scoring returns 1, A+ unreachable for those setups, no lines, dashboard shows `—`.
- **D-07:** 3 dashed lines: swing H, EQ (50%), swing L. Extended from swing `bar_idx` to right edge + small buffer. Width configurable. Delete and recreate on rotation.
- **D-08:** Label format: `percentage (price)` at right edge, e.g., `1 (24,764.25)`, `0.5 (24,270.00)`, `0 (23,775.50)`.
- **D-09:** Zone fills (linefill) — optional, default OFF.
- **D-10:** OTE zone (62%–79%) — optional input `i_show_ote`, default OFF. Visual only; no grading effect.
- **D-11:** Dashboard PD row: `PREMIUM` (red), `DISCOUNT` (green), `EQ` (yellow), `—` (gray).
- **D-12:** Dashboard Range % row: integer 0–100, e.g., `62%`, `35%`; `—` when no range. No decimals, no arrows.
- **D-13:** EQ threshold is strict 50.00%. No equilibrium band.
- **D-14:** Grading already wired. This phase only removes the hardcoded `pd_zone = "neutral"` at lines 732 and 1684 and injects the real value.
- **D-15:** Ship current thresholds as-is. Observe A+ frequency; tune only if >~10% of setups.

### Claude's Discretion

- Exact `request.security` mechanism for HTF ITH/ITL (tuple extension vs. new tuple). Budget: 3/40 used after Phase 1, 37 free. Research recommends **extending** with a single new 1-call/2-element tuple (see Architecture Patterns).
- Exact input group placement — research recommends new `GROUP_PD_ZONES` group after HTF group, mirror `PHASE4_PD_ZONES_PLAN.md` variable names but not its failed detection.
- Label `bar_idx` placement offset — research recommends `bar_index + i_extend_bars + 2` (2-bar pad past box-extension).
- Reuse `Liquidity` vs. new `DealingRange` type — research recommends **new lightweight `DealingRange` type** (rationale below).

### Deferred Ideas (OUT OF SCOPE)

- Failed approaches 1–3 (pivot+valuewhen, zigzag, highest/lowest). Do not retry.
- Directional hint on Range % (e.g., `62% ↑`).
- Equilibrium band (45%–55%).
- OTE as grading input.
- Zone fills on by default.
- REQUIREMENTS.md §PDZ-01 wording amendment (post-phase doc update).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PDZ-01 | Detect HTF swing-based dealing range | Architecture §1 — HTF swing detection via `ta.pivothigh`/`pivotlow` inside `request.security`, feeding mirrored `create_internal_levels()` on chart |
| PDZ-02 | Calculate EQ (50%), premium (>50%), discount (<50%) | Code Example §1 — `compute_pd_zone()` helper |
| PDZ-03 | Integrate into grading (+1 optimal, -1 wrong) | Already wired in `score_pd_zone()` (lines 1486–1492) and `calculate_grade()` (1499–1520). This phase only supplies `pd_zone` value. |
| PDZ-04 | Visualize zone boundaries with dashed lines + labels | Architecture §3 (drawing lifecycle), Code Example §2 (render), D-07/D-08 |
| PDZ-05 | Optional zone fill via `linefill` | Code Example §3, D-09 |
| PDZ-06 | OTE zone (62%–79%) optional | Code Example §4, D-10 |
| PDZ-07 | Recalibrate thresholds after PD modifier | D-15: ship current thresholds, observe, recalibrate only if A+ >10%. No research action required pre-release; measurement task post-deploy. |
| PDZ-08 | Store `pd_zone` on IFVG type | Field already exists on type (line 101). Remove hardcoded `"neutral"` at lines 732 (HTF) and 1684 (LTF). Inject computed value at 1684; keep `"neutral"` at 732 per STATE.md convention (HTF IFVGs are bias-only, no PD grading). |
| DSH-01 | PD Zone row | Code Example §5 (dashboard cell), D-11 color map |
| DSH-02 | Range % row | Code Example §5, D-12 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

Actionable directives the planner MUST enforce in every task:

1. **No blank lines inside `for` loop or `if` block bodies.** Parser uses indentation; blank line terminates block. Keep block bodies contiguous.
2. **Wrap multi-line `and`/`or` expressions in parentheses.** Operator must be last token on line, or whole expression in outer parens.
3. **Cast `math.abs()` / `math.max()` / `math.min()` to `int()` when assigning to int fields.** These return float in v6.
4. **Prefer nested `if` over `continue`** for skip logic in loops.
5. **Never leave `=` as last token on a line.** RHS must start on same line. Tuple assignments from `request.security(...)` stay on a single line.
6. **No AI attribution** in commits/PRs/comments. Commit style: `Phase 2: ...` prefix.
7. **`barstate.isconfirmed` guards all detection.** No repainting.
8. **Drawing objects:** always `not na(obj)` before `box.delete`/`line.delete`/`label.delete`.
9. **Memory limits:** max 500 boxes/lines/labels; FIFO cleanup.
10. **GSD workflow enforcement:** Edits only via GSD commands.

## Standard Stack

### Core (Pine Script v6 built-ins only — no external libraries)

| Built-in | Version | Purpose | Why Standard |
|----------|---------|---------|--------------|
| `request.security(sym, tf, expr, lookahead)` | v6 | Fetch HTF values on-chart | Only supported HTF mechanism in Pine v6. Already used in codebase with tuple pattern. [CITED: TradingView Pine v6 Reference] |
| `ta.pivothigh(src, leftbars, rightbars)` | v6 | HTF swing-high primitive | Standard ICT-style pivot; returns `na` until right-bar confirmation. [CITED: TradingView Pine v6 Reference] |
| `ta.pivotlow(src, leftbars, rightbars)` | v6 | HTF swing-low primitive | Counterpart of pivothigh. [CITED: TradingView Pine v6 Reference] |
| `timeframe.in_seconds(tf)` | v6 | Compare chart TF vs. PD TF | Canonical idiom for D-05 fallback. Returns `int` seconds for any tf string. [CITED: TradingView Pine v6 Reference] |
| `linefill.new(line1, line2, color)` | v6 | Zone shading between 2 lines | Native way to fill between two lines — preferred over `bgcolor` (which spans entire chart width). [CITED: TradingView Pine v6 Reference] |

### Supporting

| Function | Purpose | When to Use |
|----------|---------|-------------|
| `str.tostring(x, "#.##")` | Format price with 2 decimals | For price portion of `percentage (price)` label |
| `format.mintick` | Alternative — formats at instrument precision | Use when tick precision matters more than fixed-2-decimal |
| `barmerge.lookahead_off` | Prevent HTF lookahead leak | ALWAYS pass this in `request.security` (already codebase convention) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff / Why Not |
|------------|-----------|---------------------|
| HTF pivot inside `request.security` (recommended) | Fetch HTF OHLC and rebuild pivot detection on chart | Doubles code complexity; `ta.pivothigh` on-chart with HTF bar tracking is error-prone because chart bars don't align with HTF bars. Rejected. |
| One new `request.security` tuple call (recommended) | Append to existing Phase 1 tuples (line 579 or 583) | Possible but conflates concerns — PD TF is user-selectable independent of HTF1/HTF2. Adding to HTF1 tuple breaks if user sets PD TF ≠ HTF1. Rejected. |
| New `DealingRange` type (recommended) | Reuse `Liquidity` type | `Liquidity` holds one level; range needs two levels + 3 lines + 3 labels + optional linefill + OTE handles. Overloading `Liquidity` muddies its semantics. |

**Installation:** None — Pine Script has no package management.

**Version verification:** N/A — platform pins v6 runtime. `//@version=6` already declared line 29.

## Architecture Patterns

### Recommended Project Structure (file sections to touch)

```
src/IFVG_Indicator.pine
├── Section 1 (types)         ADD: type DealingRange
├── Section 2 (inputs)        ADD: GROUP_PD_ZONES (9 inputs — see below)
├── Section 3 (globals)       ADD: g_pd_swing_highs, g_pd_swing_lows, g_pd_liquidity_array, var DealingRange g_current_range
├── Section 4 (utilities)     ADD: compute_pd_zone(), get_pd_zone_color(), is_pd_tf_higher()
├── Section 5B (HTF block)    ADD: new tuple request.security for PD pivots (1 call, 2 elements)
├── Section 6 (liquidity)     ADD: detect_pd_swings(), create_pd_internal_levels(), check_pd_sweeps() — mirrors of existing functions scoped to pd arrays
├── Section 8 (inversion)     EDIT line 1684: pd_zone = compute_pd_zone(new_ifvg.mid) instead of "neutral"
├── Section 10 (rendering)    ADD: render_dealing_range() — rotates 3 lines + 3 labels + optional linefill + optional OTE
├── Section 11 (dashboard)    ADD: 2 new rows (PD Zone, Range %) shifting existing rows or appending
└── Section 12 (main loop)    ADD: PD pipeline step between "Step 2" (swings/liquidity) and "Step 5" (inversions)
```

### Pattern 1: HTF Data via Extended `request.security` Tuple

**What:** Fetch HTF `ta.pivothigh` and `ta.pivotlow` in a single new tuple call. Total budget after Phase 2 = **4 calls** (Phase 1 baseline 3 + 1 new), tuple elements = 18 (was 16).

**When to use:** Whenever PD timeframe differs from chart (see D-05 fallback).

**Pine v6 idiom — pivot inside request.security:**

```pinescript
// Source: Phase 1 codebase pattern (line 579) + TradingView Pine v6 request.security reference
// PD timeframe swing data — 1 call, 2 tuple elements. Budget 4/40 after this phase.
// Evaluated on PD TF; returns the pivot PRICE when a pivot confirms on PD bar, else na.
[pd_pivot_high_raw, pd_pivot_low_raw] = request.security(
     syminfo.tickerid,
     i_pd_timeframe,
     [ta.pivothigh(i_pd_swing_lookback, i_pd_swing_lookback),
      ta.pivotlow(i_pd_swing_lookback, i_pd_swing_lookback)],
     lookahead = barmerge.lookahead_off)
```

**Important gotcha:** `ta.pivothigh/pivotlow` returns the **price** of the pivot that confirmed on the CURRENT (PD TF) bar. Each HTF bar may or may not produce a pivot — most return `na`. Only push into the swing array when the value transitions from `na` to non-na AND it's a new HTF bar (avoid duplicate pushes on every chart bar inside the same HTF bar). Use the existing `htf_bar_changed` pattern (previous-bar tracker).

### Pattern 2: Mirror `create_internal_levels()` for PD Array

Copy the structure of `create_internal_levels()` (lines 1035–1102) into `create_pd_internal_levels()` that reads `g_pd_swing_highs`/`g_pd_swing_lows` and writes to `g_pd_liquidity_array`. Same logic, different arrays. Reason: the existing sweep/invalidation machinery (`check_liquidity_sweeps`) then applies the same way — but scoped to `g_pd_liquidity_array` via `check_pd_sweeps()`.

**Sweep detection on PD array runs on chart TF close** (not HTF close) — the dealing range boundaries get swept on chart candles, which is what ICT traders mean by "sweep of the HTF ITH/ITL."

### Pattern 3: Drawing Rotation — Delete-Before-Create

**Trigger for rotation:** On each bar, after `check_pd_sweeps()`, re-select `swing_high_dr` and `swing_low_dr` = newest unswept ITH / ITL from `g_pd_liquidity_array`. If the selected pair differs from `g_current_range`'s cached bar_idx pair, delete all 3 lines + 3 labels + optional linefill + optional OTE handles on the old snapshot and create new ones.

**Cache invariant:** `g_current_range` is a `var DealingRange` (persists across bars). Fields: `high_price`, `low_price`, `high_bar_idx`, `low_bar_idx`, 3 line refs, 3 label refs, 2 optional linefill refs, 2 optional OTE line + 1 linefill ref. On rotation: call a `clear_range_drawings(DealingRange r)` helper that `not na()` guards every delete.

**Extension of lines each bar:** As chart bar advances, right-extend lines/labels. Pattern used by existing `render_ifvg_boxes` — update `line.set_x2(line, right_edge)` and `label.set_x(label, right_edge)` each bar without recreating.

### Pattern 4: Timeframe Comparison for D-05 Fallback

```pinescript
// Source: TradingView Pine v6 timeframe.in_seconds reference
// true when chart TF is >= PD TF (e.g., chart=W, PD=D => fall back to chart ITH/ITL)
is_pd_tf_higher() =>
    timeframe.in_seconds(i_pd_timeframe) > timeframe.in_seconds(timeframe.period)
```

**Fallback behavior (D-05):** When `is_pd_tf_higher()` is false, skip the `request.security` block entirely — use `g_liquidity_array` (chart ITH/ITL) to select the newest unswept ITH/ITL instead of the PD-specific array. Planner should define a `select_dealing_range_source() => array<Liquidity>` helper that returns the correct array, so downstream code is indifferent.

**Note:** `request.security` is evaluated globally each bar regardless of whether its result is used. True cost avoidance requires NOT calling it at all when `is_pd_tf_higher()` is false. Pine v6 allows conditional `request.security` only via the dynamic-requests pattern — but simpler: just always make the call; a `na` result is effectively equivalent to fallback. **Recommendation:** always call `request.security` for the PD pivots (1 call permanently); use `is_pd_tf_higher()` only to select which array feeds the range selector.

### Anti-Patterns to Avoid

- **Declaring `var` globals inside `=>` functions.** Pine v6 does not allow modifying `var` globals from inside user-defined functions. Keep all mutation in the main loop scope or pass arrays explicitly by reference (arrays in Pine are reference types, so passing an array works). For single scalars like `g_current_range`, mutate only from the main loop.
- **Blank lines inside for-loops.** The parser terminates the block. Every detect/render helper in this phase must have contiguous block bodies (CLAUDE.md rule 1).
- **`math.abs(...)` assigned to int field without cast.** Produces type mismatch compile error. Cast with `int(math.abs(...))`.
- **Recreating lines every bar instead of extending.** Causes flicker and wastes draw objects. Use `line.set_x2` / `label.set_x` for bar-by-bar extension.
- **Using `bgcolor()` for zone fill.** Spans entire chart width. Use `linefill.new()` between the two lines instead (D-09).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTF bar-change detection | Custom counter with `ta.change(time("D"))` | Existing `htf_bar_changed` pattern from Phase 1 (copy idiom) | Already-proven, same edge cases handled |
| ITH/ITL sweep detection | Reinvent logic | `check_liquidity_sweeps()` already covers EQH/EQL/ITH/ITL semantics (lines 1108–1128). Create `check_pd_sweeps()` as near-copy parameterized on array. | Canonical sweep rules; divergence risks behavior drift |
| Price formatting | `str.format` templates | `str.tostring(price, "#.##")` | Matches existing codebase label style |
| Zone fill between 2 lines | `bgcolor()` or drawn boxes | `linefill.new()` | Native, respects line extent |
| TF comparison for D-05 | String matching `timeframe.period == "D"` | `timeframe.in_seconds()` | Works for any user-selected TF string including weird ones like `240` (4H) and `3D` |

**Key insight:** Every piece of state and detection this phase needs has a precedent in the codebase. The work is replication + scoping, not invention. Research found no novel algorithms required — the "failed approaches" failed because they attempted novel detection; this approach succeeds because it reuses a working detector at a different scale.

## Runtime State Inventory

> Phase does not rename/refactor — no existing runtime state needs migration. **Nothing found in any category** — verified by grep. New state introduced (g_pd_swing_highs, g_pd_swing_lows, g_pd_liquidity_array, g_current_range) starts empty on script reload, as with all Pine `var` arrays.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Pine Script has no persistent storage | None |
| Live service config | None | None |
| OS-registered state | None | None |
| Secrets/env vars | None — TradingView input-only | None |
| Build artifacts | None — no build step | None |

## Common Pitfalls

### Pitfall 1: `ta.pivothigh`/`pivotlow` Only Confirms on Pivot+rightbars Bar

**What goes wrong:** Every HTF bar calls the function, but only bars where a confirmed pivot sits at `leftbars` back return a price. Most return `na`. If the push-to-swing-array code doesn't guard on `not na(pd_pivot_high_raw)`, the array fills with `na` entries.
**Why it happens:** Pivot functions are stateless per-bar; they don't "remember" pivots.
**How to avoid:** Only `array.push(g_pd_swing_highs, ...)` when `not na(pd_pivot_high_raw) and htf_bar_changed`.
**Warning signs:** Swing arrays growing to cap (50) within first few bars; range boundaries picking up `na`-price levels.

### Pitfall 2: Mutating `var` Globals Inside `=>` Functions

**What goes wrong:** Pine v6 emits compile error when you try to reassign a `var` scalar from inside a user function (e.g., `g_current_range := DealingRange.new(...)` inside `render_dealing_range()`).
**Why it happens:** User-defined functions execute in a restricted scope; arrays pass by reference (mutations allowed), but scalar var reassignments are not allowed.
**How to avoid:** Either (a) make `g_current_range` mutation happen only from main-loop scope (call `render_dealing_range()` and pass it the current range by value), or (b) keep the snapshot inside a one-element `array<DealingRange>` (array mutation is allowed in functions).
**Warning signs:** `Cannot modify global variable ... in function` error at compile.

### Pitfall 3: Label Right-Edge Drift Past Chart End

**What goes wrong:** Labels anchored at `bar_index + i_extend_bars + 2` go off the right side of the chart if `max_bars_back` limit reached, or produce a "bar index too far" warning.
**Why it happens:** Pine limits future bar references to (roughly) 500 bars past `bar_index`.
**How to avoid:** Clamp: `right_edge = math.min(bar_index + i_extend_bars + 2, bar_index + 400)`.
**Warning signs:** Warnings in Pine log about bar index; labels disappearing or stacking.

### Pitfall 4: Blank Line in Block Body Breaks Parser

**What goes wrong:** "end of line without line continuation" error at compile.
**Why it happens:** Pine v6 uses indentation + contiguity for block boundaries. Blank line ends the block.
**How to avoid:** No blank lines inside `for` or `if` bodies. Use comment-only lines (`//`) if visual spacing is desired inside a block.
**Warning signs:** Cryptic parser error on a line that looks valid.

### Pitfall 5: Rotating Lines Without Deleting Old Handles

**What goes wrong:** Old lines stay on chart as ghosts; exceeds `max_lines_count=500`; newer detections stop rendering.
**Why it happens:** Overwriting a line variable doesn't delete the underlying line object.
**How to avoid:** `clear_range_drawings(g_current_range)` with `not na(...) then line.delete(...)` before replacing.
**Warning signs:** Stale horizontal lines accumulating; line count climbing toward 500.

### Pitfall 6: IFVG `pd_zone` Computed With Stale Range

**What goes wrong:** If `check_pd_sweeps()` and range-selection happen AFTER `check_inversions()` in the main loop, a newly-invalidated range boundary could mean the IFVG just created was graded against a swept boundary.
**Why it happens:** Order dependency in main loop.
**How to avoid:** Place the PD pipeline (detect pd swings → create_pd_internal_levels → check_pd_sweeps → select current range) BEFORE `check_inversions()` in the main loop. `check_inversions()` then calls `compute_pd_zone(new_ifvg.mid)` which reads the fresh `g_current_range`.

## Code Examples

### Example 1: `compute_pd_zone()` Helper

```pinescript
// Source: CONTEXT D-03, D-06, D-13 — strict 50% equilibrium, no band
compute_pd_zone(float price_mid) =>
    string result = "neutral"
    if not na(g_current_range) and g_current_range.is_valid
        float hi = g_current_range.high_price
        float lo = g_current_range.low_price
        if hi > lo
            float eq = (hi + lo) / 2.0
            if price_mid > eq
                result := "premium"
            else if price_mid < eq
                result := "discount"
            else
                result := "equilibrium"
    result
```

### Example 2: Dealing-Range Render with 3 Lines + 3 Labels

```pinescript
// Source: CONTEXT D-07, D-08 — 3 dashed lines, labels "percentage (price)"
// Called from main loop after range selection. Passes range by reference.
render_dealing_range(DealingRange r) =>
    if r.is_valid
        int right_edge = math.min(bar_index + i_extend_bars + 2, bar_index + 400)
        float hi = r.high_price
        float lo = r.low_price
        float eq = (hi + lo) / 2.0
        int left_edge = math.max(r.high_bar_idx, r.low_bar_idx)

        // Delete previous
        if not na(r.line_high)
            line.delete(r.line_high)
        if not na(r.line_eq)
            line.delete(r.line_eq)
        if not na(r.line_low)
            line.delete(r.line_low)
        if not na(r.label_high)
            label.delete(r.label_high)
        if not na(r.label_eq)
            label.delete(r.label_eq)
        if not na(r.label_low)
            label.delete(r.label_low)

        // Create
        r.line_high := line.new(left_edge, hi, right_edge, hi, color=i_pd_line_color, style=line.style_dashed, width=i_pd_line_width)
        r.line_eq   := line.new(left_edge, eq, right_edge, eq, color=i_pd_eq_color, style=line.style_dashed, width=i_pd_line_width)
        r.line_low  := line.new(left_edge, lo, right_edge, lo, color=i_pd_line_color, style=line.style_dashed, width=i_pd_line_width)

        r.label_high := label.new(right_edge, hi, "1 (" + str.tostring(hi, "#.##") + ")", style=label.style_none, textcolor=i_pd_line_color, size=size.small)
        r.label_eq   := label.new(right_edge, eq, "0.5 (" + str.tostring(eq, "#.##") + ")", style=label.style_none, textcolor=i_pd_eq_color, size=size.small)
        r.label_low  := label.new(right_edge, lo, "0 (" + str.tostring(lo, "#.##") + ")", style=label.style_none, textcolor=i_pd_line_color, size=size.small)
```

### Example 3: Optional Zone Fill via `linefill`

```pinescript
// Source: CONTEXT D-09 — optional, default OFF
if i_show_pd_fills and r.is_valid
    if not na(r.fill_premium)
        linefill.delete(r.fill_premium)
    if not na(r.fill_discount)
        linefill.delete(r.fill_discount)
    r.fill_premium := linefill.new(r.line_high, r.line_eq, color.new(i_bearish_color, 92))
    r.fill_discount := linefill.new(r.line_eq, r.line_low, color.new(i_bullish_color, 92))
```

### Example 4: Optional OTE Fill (62%–79%)

```pinescript
// Source: CONTEXT D-10 — visual only, no grading effect
if i_show_ote and r.is_valid
    float range = r.high_price - r.low_price
    // OTE defined from the sweep low (for bullish) — approach: symmetric band from EQ using range
    // Simplest interpretation: 62%-79% of range above low
    float ote_low = r.low_price + range * 0.62
    float ote_high = r.low_price + range * 0.79
    // (delete previous + create fresh — omitted for brevity; same pattern)
    r.ote_line_top := line.new(left_edge, ote_high, right_edge, ote_high, color=color.new(#AB47BC, 70), style=line.style_dotted)
    r.ote_line_bot := line.new(left_edge, ote_low, right_edge, ote_low, color=color.new(#AB47BC, 70), style=line.style_dotted)
    r.ote_fill := linefill.new(r.ote_line_top, r.ote_line_bot, color.new(#AB47BC, 92))
```

### Example 5: Dashboard Rows (DSH-01, DSH-02)

```pinescript
// Source: CONTEXT D-11, D-12 — row numbers TBD by planner based on existing layout
string pd_text = "—"
color pd_color = color.gray
string range_pct_text = "—"

if not na(g_current_range) and g_current_range.is_valid and not na(current_latest_ifvg)
    switch current_latest_ifvg.pd_zone
        "premium"     => pd_text := "PREMIUM", pd_color := color.red
        "discount"    => pd_text := "DISCOUNT", pd_color := color.green
        "equilibrium" => pd_text := "EQ", pd_color := color.yellow
    float range_span = g_current_range.high_price - g_current_range.low_price
    if range_span > 0
        int pct = int(math.round((current_latest_ifvg.mid - g_current_range.low_price) / range_span * 100))
        range_pct_text := str.tostring(pct) + "%"

table.cell(dashboard, 0, row_pd, "PD Zone:", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
table.cell(dashboard, 1, row_pd, pd_text, text_color=pd_color, text_size=size.small, text_halign=text.align_right)
table.cell(dashboard, 0, row_range, "Range %:", text_color=color.gray, text_size=size.small, text_halign=text.align_left)
table.cell(dashboard, 1, row_range, range_pct_text, text_color=color.white, text_size=size.small, text_halign=text.align_right)
```

## Security-Call Budget Accounting

| Phase | Calls | Tuple Elements | Running Total |
|-------|-------|----------------|---------------|
| Phase 1 baseline | 2 (HTF1, HTF2 — 7 elements each) + 1 ATR | 14 | 3 calls / 40 max |
| **Phase 2 add** | **+1 (PD pivots — 2 elements)** | **+2** | **4 calls / 40 max** |
| Post-Phase 2 budget remaining | — | — | **36 calls free** |

Recommendation: a single dedicated `request.security` call for PD pivots keeps PD TF independent of HTF1/HTF2 selection (user can pick PD=D while HTF1=4H and HTF2=1H). Conflating would break that independence.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `ta.pivothigh` + `ta.valuewhen` via `request.security` for range boundaries | HTF pivot → mirrored ITH/ITL array → newest unswept pick | Phase 2 rewrite (this research) | Swings now alternate correctly; range rotates on sweeps; matches user reference indicator |
| Hardcoded `pd_zone = "neutral"` at IFVG creation | Computed `compute_pd_zone(ifvg.mid)` | Phase 2 | A+ grades reachable for setups in optimal zone |
| PDZ-01 REQUIREMENTS wording (`ta.pivothigh via request.security`) | Superseded by D-01 (HTF ITH/ITL) | Phase 2 | Doc update deferred per CONTEXT |

**Deprecated/outdated:**
- `PHASE4_PD_ZONES_PLAN.md` detection section — input-group and naming references remain useful, but detection logic is obsolete.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `ta.pivothigh(n, n)` evaluated inside `request.security` on HTF returns the pivot price when confirmed on the HTF bar, `na` otherwise | Architecture §1, Pitfall 1 | If behavior differs (e.g., repaints), swing array gets duplicate or leaked-future values; range boundaries wrong. Mitigation: verify on TradingView during first task with `lookahead=barmerge.lookahead_off` and `barstate.isconfirmed` guards. [ASSUMED — documented TradingView v6 behavior but not verified this session] |
| A2 | Pine v6 disallows reassigning `var` scalar globals inside `=>` functions but allows array mutation | Pitfall 2 | If wrong direction, `g_current_range` design may need re-architecting. Mitigation: planner should test-compile a minimal reassignment early; fall back to one-element array wrapper. [ASSUMED — consistent with Pine docs and memory note but not verified this session] |
| A3 | `linefill.new()` between two `line` objects persists across bar updates when lines are extended via `line.set_x2` | Code Example §3 | If linefill disconnects, shading flickers. Mitigation: recreate linefill along with line extension; acceptable cost (2 extra objects per bar). [ASSUMED] |
| A4 | Total post-Phase-2 security-call count of 4 fits within the 40-call budget — each new tuple counts as 1 call regardless of element count | Budget table | If TradingView counts elements-not-calls, budget tightens. Mitigation: Phase 1 SESSION log confirms 14 elements across 2 calls used 2 budget units, so calls-not-elements is the correct accounting. [VERIFIED: STATE.md Phase 01 decisions line 66] |
| A5 | Chart-TF ITH/ITL fallback (D-05) using `g_liquidity_array` produces range boundaries that match user expectation when `timeframe.period >= i_pd_timeframe` | Pattern 4 | User may expect "no range shown" instead of "fallback to chart"; CONTEXT D-05 explicitly states fallback, so this is verified. [VERIFIED: CONTEXT D-05] |

**Action for planner:** A1 and A2 should be validated with a minimal compile test in the first implementation task before committing to the full architecture. A3 is low-risk; recreate-on-rotation covers it.

## Open Questions

1. **Dashboard row insertion index**
   - What we know: Existing dashboard uses rows 0–9 (lines ~2308–2399). Adding 2 rows pushes total to 11.
   - What's unclear: User preference for placement — before HTF rows, after HTF rows, or between grade/direction rows.
   - Recommendation: Append as rows 10, 11 initially; Phase 3 will expand dashboard (DSH-04) and can re-layout then.

2. **OTE anchor direction (bullish vs. bearish)**
   - What we know: OTE in ICT is retracement from sweep point. CONTEXT D-10 says 62%–79% between high and low without specifying which end is the "start."
   - What's unclear: Is OTE always measured from the low upward (bullish-biased), or should it flip with HTF bias?
   - Recommendation: Ship symmetric — fixed 62%–79% of range above low. Revisit if user feedback requests bias-aware OTE.

3. **Does `request.security` with pivot functions repaint without `lookahead_off`?**
   - What we know: Existing codebase always passes `barmerge.lookahead_off`. Phase 1 commits confirm no repainting.
   - What's unclear: Nothing — this is a solved pattern. Continue using `lookahead_off`.
   - Recommendation: No action.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| TradingView Pine Script v6 runtime | Entire indicator | ✓ | v6 (server-side) | — |
| Pine built-ins: `request.security`, `ta.pivothigh`, `ta.pivotlow`, `linefill.new`, `timeframe.in_seconds`, `str.tostring` | All detection + render | ✓ | v6 | — |

**Missing dependencies with no fallback:** None.
**Missing dependencies with fallback:** None.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None — Pine Script has no test runner |
| Config file | None |
| Quick run command | Manual: paste `src/IFVG_Indicator.pine` into TradingView Pine Editor, click "Add to chart" |
| Full suite command | Manual: load multiple charts (1H, 4H, D, W × at least 3 instruments) and visually verify |
| Phase gate | `/gsd-verify-work` uses user visual confirmation on TradingView |

### Phase Requirements → Test Map

Pine Script has **no automated test framework**. All verification is visual on TradingView. Research checked `CONCERNS.md`, `CLAUDE.md`, and CONTEXT — all confirm: "Testing: Visual verification only — no automated test framework exists for Pine Script."

| Req ID | Behavior | Test Type | Verification Procedure | Automatable? |
|--------|----------|-----------|------------------------|--------------|
| PDZ-01 | HTF dealing range detected | Visual | Load chart (e.g., NQ1! 15m, PD=D). Verify 3 dashed lines appear at distinct HTF swing levels (not spanning entire chart). | No — visual |
| PDZ-02 | EQ at 50% | Visual | Verify EQ label reads `0.5 (midprice)` and sits halfway between high/low lines. | No — visual |
| PDZ-03 | Grading +1/-1 effect | Visual + log | On a bullish IFVG in discount: verify grade one tier higher than on an otherwise-identical bullish IFVG in premium. Inspect IFVG tooltip for `pd_score = 2` vs `pd_score = 0`. | Partial — tooltip introspection |
| PDZ-04 | 3 dashed lines + labels | Visual | Verify dashed style, label format `percentage (price)` matches D-08 exactly. | No — visual |
| PDZ-05 | Zone fill toggle | Visual | Toggle `i_show_pd_fills` — verify fills appear/disappear between correct line pairs. | No — visual |
| PDZ-06 | OTE toggle | Visual | Toggle `i_show_ote` — verify 62%–79% band renders within range. | No — visual |
| PDZ-07 | Grade distribution balanced | Visual + manual count | On a representative chart (~50 IFVGs), count grade distribution. No single grade >40%. | Partial — manual tally |
| PDZ-08 | `pd_zone` stored on IFVG | Visual via tooltip | Hover IFVG label; tooltip should reflect zone and pd_score. | Partial — tooltip |
| DSH-01 | PD Zone row | Visual | Verify row shows PREMIUM/DISCOUNT/EQ/— with correct colors. | No — visual |
| DSH-02 | Range % row | Visual | Verify integer 0–100% displayed; matches manual calc `(mid - low) / (high - low) * 100`. | No — visual |

### Sampling Rate
- **Per task commit:** Paste-and-compile check in Pine Editor (syntax-only); compile error = fail.
- **Per plan merge:** Load on 1H/4H/D on one test instrument; visual verify all affected features.
- **Phase gate:** Full multi-TF × multi-instrument visual sweep before `/gsd-verify-work`.

### Wave 0 Gaps

Not applicable — no test infrastructure exists or can be created for Pine Script. CONCERNS.md confirms this constraint.

*Recommendation to planner:* Add a single "Compile Check" task at the start of each plan (paste into Pine Editor, confirm 0 errors) and a "Visual Verification" task at the end.

## Sources

### Primary (HIGH confidence)
- `src/IFVG_Indicator.pine` lines 1–2511 — current working codebase, verified during research
- `.planning/phases/02-pd-zone-detection-grading-integration/02-CONTEXT.md` — locked decisions D-01..D-15
- `CLAUDE.md` — Pine v6 syntax rules (verified working on Phase 1)
- `.planning/STATE.md` — Phase 1/5 decisions confirming security-call budget accounting
- `.planning/REQUIREMENTS.md` — PDZ-01..PDZ-08, DSH-01..DSH-02

### Secondary (MEDIUM confidence)
- `PHASE4_PD_ZONES_PLAN.md` — reference for input-group/variable naming (detection logic excluded per CONTEXT)
- `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/CONCERNS.md` — codebase intel

### Tertiary (LOW confidence — external docs referenced from training)
- TradingView Pine v6 reference for `request.security`, `ta.pivothigh`, `ta.pivotlow`, `linefill.new`, `timeframe.in_seconds` — documented behavior consistent with codebase usage; not re-verified this session

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all built-ins used elsewhere in same codebase
- Architecture: HIGH — patterns mirror existing Phase 1/Phase 2/Phase 3 code
- Drawing rotation: HIGH — same pattern as existing ifvg/fvg rendering
- HTF pivot behavior: MEDIUM — documented but not re-verified in this session; planner should add a minimal compile-test task first
- Validation: HIGH — visual-only constraint is well-established

**Research date:** 2026-04-14
**Valid until:** 2026-05-14 (30 days — Pine v6 is stable; HTF/pivot behavior unlikely to change)
