# Phase 02: PD Zone Detection & Grading Integration - Research

**Researched:** 2026-03-26
**Domain:** Pine Script v6 -- HTF swing-based Premium/Discount zone detection, grading integration, visualization
**Confidence:** HIGH

## Summary

This phase adds HTF swing-based Premium/Discount zone detection to the IFVG indicator. The approach uses `ta.pivothigh()`/`ta.pivotlow()` + `ta.valuewhen()` wrapped in `request.security()` to get confirmed HTF swing levels, then calculates equilibrium (50%), premium (above EQ), and discount (below EQ) zones. Zone positioning feeds into the grading algorithm as a +1/-1 quality modifier, and new dashboard rows display current zone and range percentage.

The PHASE4_PD_ZONES_PLAN.md provides a solid implementation blueprint that aligns well with the codebase's existing patterns. Key modifications: consolidate the 2 planned `request.security()` calls into a single tuple call (matching the existing consolidation pattern), add `pd_zone` field to the IFVG type, add OTE zone visualization (62-79% lines with optional fill), and expand the dashboard table.

**Primary recommendation:** Follow PHASE4_PD_ZONES_PLAN.md as the implementation reference, consolidating PD swing data into a single `request.security()` tuple call (1 new call, bringing total from 2 to 3), and keeping grade threshold changes deferred per D-06.

<user_constraints>

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Dedicated PD timeframe input (`i_pd_timeframe`), separate from existing HTF1/HTF2 timeframes. Costs 2 extra `request.security()` calls (4 of 40 total). Traders get independent control -- e.g., 4H for FVG detection but Daily for dealing range.
- **D-02:** Default PD zone timeframe is Daily. Standard ICT dealing range timeframe, works across all chart timeframes.
- **D-03:** Display as two dashed lines at 62% and 79% retracement levels with optional fill between them (separate toggle from PD zone fill).
- **D-04:** OTE is visual only -- no extra grading modifier beyond the basic premium/discount +1/-1. Keeps grading simple, avoids double-counting zone position.
- **D-05:** OTE visual display is off by default (opt-in toggle). However, the PD zone grading modifier (+1/-1 for premium/discount) is always active when PD zones are enabled, regardless of OTE visual state. Visual and grading toggles are independent.
- **D-06:** Keep current grade thresholds unchanged initially (A tier: score>=2 -> A+, >=1 -> A, >=0 -> A-, etc.). Quality score range expands from [-2,+3] to [-3,+4]. Verify grade distribution on real charts after implementation. Recalibrate in a follow-up only if >40% of setups cluster in a single grade.
- **D-07:** Separate toggle for PD zone grading modifier (`i_pd_grade_modifier`, default: true). Traders can see zones without affecting grades.
- **D-08:** Show `pd_zone` in the IFVG label tooltip -- e.g., "A+ Bull IFVG [DISCOUNT]". No extra visual elements, leverages existing labels.
- **D-09:** `pd_zone` is frozen at inversion time and never changes. Reflects market context when the setup formed, consistent with how grade is already frozen at inversion.
- **D-10:** PD zone lines span full chart width (left edge to right edge). PD zones are structural reference -- always visible.
- **D-11:** Zone fills (premium/discount background) are off by default (opt-in). Lines + labels show zone structure without overwhelming busy charts.
- **D-12:** Right-edge price labels: "Swing H (100%)", "EQ (50%)", "Swing L (0%)". Clean, out of the way.

### Claude's Discretion
- OTE zone colors and opacity values
- Exact line widths for zone boundary lines (EQ likely width=2 solid, swing H/L likely width=1 dashed -- as sketched in PHASE4_PD_ZONES_PLAN.md)
- Pivot lookback default value (plan suggests 5 -- verify against typical swing spacing)
- Dashboard PD Zone and Range % row styling details
- OTE fill color and opacity
- How to handle edge case where swing high < swing low or no swings detected

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope

</user_constraints>

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PDZ-01 | Detect HTF swing-based dealing range using ta.pivothigh/ta.pivotlow via request.security() | Verified: ta.pivothigh/ta.pivotlow + ta.valuewhen works inside request.security() tuples in v6. Single consolidated call costs 1 request.security budget slot. |
| PDZ-02 | Calculate equilibrium (50%), premium zone (above EQ), and discount zone (below EQ) | Simple arithmetic: EQ = low + (range * 0.5). Zone is determined by comparing close to EQ. |
| PDZ-03 | Integrate PD zone positioning into grading algorithm (+1 optimal zone, -1 wrong zone) | Add `int pd_zone_modifier` parameter to `calculate_grade()` at line 1463. Apply after existing quality_score modifiers. Quality score range expands from [-2,+3] to [-3,+4]. |
| PDZ-04 | Visualize zone boundaries with dashed lines, labels showing Swing H/L and EQ levels | Use line.new() for 3 horizontal lines + label.new() for 3 right-edge labels. Delete-before-recreate pattern per codebase convention. |
| PDZ-05 | Optional zone fill (linefill) between swing high/EQ and EQ/swing low | Use linefill.new(lineA, lineB, color) -- requires lines to exist first. Auto-deleted when lines are deleted. Off by default per D-11. |
| PDZ-06 | Visualize OTE zone (62-79% retracement) with optional toggle | 2 additional dashed lines at 62% and 79% levels. Optional linefill between them. Off by default per D-05. |
| PDZ-07 | Recalibrate grade thresholds after adding PD modifier to prevent grade inflation | Per D-06: thresholds unchanged initially. Verify distribution on real charts post-implementation. Recalibrate only if >40% cluster. |
| PDZ-08 | Store pd_zone field ("premium"/"discount"/"equilibrium"/"neutral") on IFVG type | Add `string pd_zone` field to IFVG type definition (line 92-122). Set at inversion time, frozen per D-09. |
| DSH-01 | Add PD Zone row showing current zone (PREMIUM/DISCOUNT) with color coding | Expand dashboard table from 10 to 12 rows. Add row with zone name, color-coded (red=premium, green=discount, gray=neutral). |
| DSH-02 | Add Range % row showing current position within dealing range (0-100%) | Calculate: ((close - swing_low) / range) * 100. Display as "XX.X%" in white text. |

</phase_requirements>

## Standard Stack

This is a single-file Pine Script v6 project. There are no external libraries or packages.

### Core Pine Script v6 Functions Used

| Function | Purpose | Notes |
|----------|---------|-------|
| `ta.pivothigh(source, leftbars, rightbars)` | Detect swing highs on HTF | Returns float on pivot bar, `na` otherwise. Use `high` as source. |
| `ta.pivotlow(source, leftbars, rightbars)` | Detect swing lows on HTF | Returns float on pivot bar, `na` otherwise. Use `low` as source. |
| `ta.valuewhen(condition, source, occurrence)` | Get most recent confirmed swing value | occurrence=0 for most recent. Persists the value even when condition is false. |
| `request.security(symbol, timeframe, expression, lookahead)` | Fetch HTF swing data | Use tuple expression with `lookahead=barmerge.lookahead_off` to prevent repainting. |
| `linefill.new(line1, line2, color)` | Fill between zone lines | Auto-deleted when either line is deleted. No separate count limit. |
| `line.new(x1, y1, x2, y2, ...)` | Draw zone boundary lines | Already used extensively. Counts toward 500 line limit. |
| `label.new(x, y, text, ...)` | Draw zone labels | Already used extensively. Counts toward 500 label limit. |

### Resource Budget

| Resource | Limit | Current Usage | Phase 2 Adds | After Phase 2 |
|----------|-------|---------------|--------------|---------------|
| `request.security()` calls | 40 | 2 | 1 (tuple) | 3 |
| Tuple elements | 127 max | 14 (7 per HTF) | 2 | 16 |
| Lines | 500 | Variable | +3-5 (swing H/L, EQ, OTE 62%, OTE 79%) | Still well under |
| Labels | 500 | Variable | +3-5 (swing H/L, EQ, OTE labels) | Still well under |
| Linefills | No explicit limit | 0 | +0-3 (premium fill, discount fill, OTE fill) | Fine |
| Table rows | 10 | 10 | +2 | 12 |

## Architecture Patterns

### Integration Points (Exact Locations)

```
src/IFVG_Indicator.pine (2561 lines)
├── Section 1 (lines 36-122):  IFVG type definition -- ADD pd_zone field
├── Section 2 (lines 124-283): Inputs -- ADD GROUP_PD_ZONES after line 282
├── Section 3 (lines 284-307): Globals -- ADD PD zone var globals after line 304
├── Section 5B (lines 695-869): HTF detection -- ADD request.security tuple call
│                                                  for PD swing data after line 709
├── NEW Section 5C:             PD Zone functions (update_pd_zones,
│                               get_pd_zone_modifier, render_pd_zones)
├── Section 7 (line 1463):      calculate_grade -- ADD pd_zone_modifier parameter
├── Section 8 (line 1662):      calculate_grade call -- PASS pd_modifier argument
│                   (line 1667): IFVG.new() call -- ADD pd_zone field
├── Section 8 HTF (line 838):   HTF IFVG.new() call -- ADD pd_zone = "neutral"
├── Section 10 (line 2027):     Tooltip text -- ADD pd_zone to tooltip
├── Section 11 (line 2368):     Dashboard table -- EXPAND to 12 rows, ADD 2 rows
└── Section 12 (line 2439):     Main loop -- ADD update_pd_zones() call,
                                              ADD render_pd_zones() call
```

### Pattern 1: Consolidated request.security() Tuple

**What:** Bundle PD swing data into a single request.security() call using a tuple expression.
**When to use:** Always -- matches the existing consolidation pattern from Phase 1 (FIX-03).
**Example:**

```pinescript
// Compute pivot expressions at script level (evaluated in HTF context by request.security)
pd_pivot_high_expr = ta.pivothigh(high, i_pd_swing_lookback, i_pd_swing_lookback)
pd_pivot_low_expr = ta.pivotlow(low, i_pd_swing_lookback, i_pd_swing_lookback)
pd_swing_h_expr = ta.valuewhen(not na(pd_pivot_high_expr), pd_pivot_high_expr, 0)
pd_swing_l_expr = ta.valuewhen(not na(pd_pivot_low_expr), pd_pivot_low_expr, 0)

// Single request.security call with 2-element tuple
[pd_htf_swing_high, pd_htf_swing_low] = request.security(
    syminfo.tickerid, i_pd_timeframe,
    [pd_swing_h_expr, pd_swing_l_expr],
    lookahead = barmerge.lookahead_off
)
```

**Critical note:** The `ta.pivothigh()`, `ta.pivotlow()`, and `ta.valuewhen()` expressions are evaluated at the script level but `request.security()` re-evaluates them using HTF data. The `high` and `low` references inside `ta.pivothigh(high, ...)` will correctly use the HTF timeframe's high/low values.

### Pattern 2: Frozen State at Inversion Time (D-09)

**What:** Set pd_zone on the IFVG object at the moment of inversion, never update it afterwards.
**When to use:** In `check_inversions()` when creating the IFVG.new() object.
**Example:**

```pinescript
// Inside check_inversions(), right before IFVG.new():
string current_pd_zone = g_pd_current_zone  // Capture current zone

// In IFVG.new() constructor:
new_ifvg = IFVG.new(
    // ... existing fields ...
    pd_zone = current_pd_zone
)
```

### Pattern 3: Delete-Before-Recreate for Zone Lines

**What:** Delete all PD zone visual elements at the start of each render cycle, then recreate them.
**When to use:** In render_pd_zones(), matching the existing render_fvg_boxes() and render_liquidity_lines() patterns.
**Example:**

```pinescript
render_pd_zones() =>
    // Delete existing drawings
    if not na(g_pd_high_line)
        line.delete(g_pd_high_line)
    if not na(g_pd_low_line)
        line.delete(g_pd_low_line)
    // ... delete all PD lines, labels, linefills ...

    // Recreate if enabled and data available
    if i_enable_pd_zones and i_pd_show_lines and not na(g_pd_swing_high) and not na(g_pd_swing_low)
        right_edge = bar_index + i_extend_bars
        left_edge = bar_index - 400  // Full chart width per D-10
        // ... create lines, labels, optional fills ...
```

### Pattern 4: Independent Toggle Architecture (D-05, D-07)

**What:** Visual display toggles and grading modifier toggle are fully independent.
**When to use:** All PD zone input processing.

```
i_enable_pd_zones      -- Master enable (gates everything)
  i_pd_show_lines      -- Visual: zone boundary lines (default: true)
  i_pd_show_fill       -- Visual: zone background fill (default: false)
  i_pd_show_ote        -- Visual: OTE zone lines (default: false)
  i_pd_show_ote_fill   -- Visual: OTE fill between 62-79% (default: false)
  i_pd_grade_modifier  -- Logic: +1/-1 grading modifier (default: true)
```

Grading modifier applies even when all visual toggles are off, as long as `i_enable_pd_zones` and `i_pd_grade_modifier` are both true.

### Anti-Patterns to Avoid

- **Using separate request.security() calls for swing high and swing low:** Wastes a budget slot. Consolidate into a single tuple call.
- **Recomputing pd_zone on every bar for existing IFVGs:** Zone is frozen at inversion time (D-09). Only the current global zone (`g_pd_current_zone`) updates each bar.
- **Putting linefill.new() before line.new():** Linefills depend on line objects existing first. Create lines, then create fills.
- **Deleting linefills without deleting lines:** Linefills auto-delete when their lines are deleted. Delete lines and linefills will follow. But if you only want to remove the fill while keeping lines, delete the linefill explicitly.
- **Blank lines inside for loops or if blocks:** Pine Script parser uses indentation for blocks. Blank lines can prematurely terminate blocks (per CLAUDE.md rule #1).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Swing detection | Custom high/low comparison loops | `ta.pivothigh()` / `ta.pivotlow()` | Built-in, handles edge cases, optimized |
| Last confirmed value | Manual var tracking of last non-na pivot | `ta.valuewhen(condition, source, 0)` | Built-in, persists value correctly |
| Zone fill between lines | Custom box-based fill approximation | `linefill.new(line1, line2, color)` | Native fill, auto-extends, auto-deletes |
| HTF data retrieval | Manual time-based lookups | `request.security()` with tuple | Standard pattern, handles bar alignment |

**Key insight:** Pine Script v6 provides all the building blocks natively. The implementation is primarily integration work -- wiring existing primitives into the indicator's established patterns.

## Common Pitfalls

### Pitfall 1: Swing High == Swing Low or Invalid Range
**What goes wrong:** Division by zero when calculating percentage, or equilibrium calculation produces meaningless results.
**Why it happens:** On very short histories or flat markets, ta.valuewhen may return equal values for swing high and swing low. Also possible on first load before any pivots are detected.
**How to avoid:** Guard all range calculations with `range > 0` check. Set zone to "neutral" when range is zero or negative. Ensure `g_pd_current_percent` is `na` when range is invalid.
**Warning signs:** Dashboard shows "0.0%" or "NaN%", or all setups get "neutral" pd_zone.

### Pitfall 2: Stale Swing Values on Timeframe Change
**What goes wrong:** When user changes PD timeframe, old swing values persist in `var` globals until new pivots are detected on the new timeframe.
**Why it happens:** `var` declarations persist across bars. Changing a timeframe input restarts the script, but `ta.valuewhen` needs historical data to find the first pivot.
**How to avoid:** This is actually fine -- `ta.valuewhen` will find the most recent pivot on the new timeframe as the script replays history. The `var` globals will be correctly set during replay. No special handling needed.
**Warning signs:** None expected -- Pine Script's replay mechanism handles this.

### Pitfall 3: request.security() Repainting
**What goes wrong:** PD zone levels appear to change on historical bars when viewed in real-time.
**Why it happens:** Using `lookahead=barmerge.lookahead_on` or not gating on `barstate.isconfirmed`.
**How to avoid:** Always use `lookahead=barmerge.lookahead_off`. The update_pd_zones() function should run inside the main `barstate.isconfirmed` gate in the main loop. However, note that `request.security()` calls themselves are evaluated every bar regardless of the confirmed gate -- it's the *use* of the values that should be gated.
**Warning signs:** Zone lines moving on historical bars when scrolling.

### Pitfall 4: Line Continuation Syntax Errors
**What goes wrong:** "End of line without line continuation" compile errors.
**Why it happens:** Pine Script v6 is strict about line continuations. Blank lines in blocks, `=` as last token on a line, or expressions split without trailing operators cause errors.
**How to avoid:** Follow CLAUDE.md Pine Script v6 Syntax Rules (all 6 rules). Keep multi-line expressions connected with operators at end of lines. Never leave `=` dangling. No blank lines in blocks.
**Warning signs:** Compile error at specific line number mentioning "line continuation".

### Pitfall 5: IFVG Type Constructor Missing Fields
**What goes wrong:** Compile error or runtime error when adding `pd_zone` field to IFVG type but not all IFVG.new() call sites.
**Why it happens:** There are two IFVG.new() call sites: LTF (line 1667) and HTF (line 838). Both must be updated when adding a new field.
**How to avoid:** Search for ALL `IFVG.new(` occurrences and update each one. HTF IFVGs should get `pd_zone = "neutral"` since HTF IFVGs don't use grading.
**Warning signs:** Compile error mentioning field count mismatch.

### Pitfall 6: Dashboard Table Row Count Mismatch
**What goes wrong:** Dashboard shows empty rows or rows are missing.
**Why it happens:** `table.new()` specifies row count (currently 10). Must increase to 12 to accommodate 2 new PD zone rows. If row count doesn't match actual table.cell() calls, extra rows are blank or cells overflow.
**How to avoid:** Update `table.new(position.top_right, 2, 12, ...)` and add cells for rows 10 and 11 (0-indexed).
**Warning signs:** Dashboard layout breaks, empty space at bottom.

### Pitfall 7: Linefill Without Lines
**What goes wrong:** Runtime error when creating linefill.new() with `na` line references.
**Why it happens:** If `i_pd_show_fill` is true but `i_pd_show_lines` is false, lines won't exist to fill between.
**How to avoid:** Per D-11, zone fills require lines. Guard linefill creation: `if i_pd_show_fill and i_pd_show_lines`. The PHASE4_PD_ZONES_PLAN.md already handles this correctly. For OTE fills, similarly guard on OTE lines existing.
**Warning signs:** Compile or runtime error referencing linefill.

## Code Examples

### IFVG Type Extension (Section 1)

```pinescript
// Add after line 122 (delivery_box_id field):
    string pd_zone      // "premium", "discount", "equilibrium", or "neutral"
```

### Input Group (Section 2, after line 282)

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Premium/Discount Zone Settings
// ─────────────────────────────────────────────────────────────────────
string GROUP_PD_ZONES = "═══ Premium/Discount Zones ═══"
i_enable_pd_zones      = input.bool(true, "Enable PD Zones", group=GROUP_PD_ZONES,
                         tooltip="Calculate Premium/Discount zones based on HTF swing detection")
i_pd_timeframe         = input.timeframe("D", "PD Zone Timeframe", group=GROUP_PD_ZONES,
                         tooltip="Timeframe for swing-based dealing range detection")
i_pd_swing_lookback    = input.int(5, "Swing Lookback", minval=3, maxval=20, group=GROUP_PD_ZONES,
                         tooltip="Bars left/right for HTF pivot detection")
i_pd_show_lines        = input.bool(true, "Show Zone Lines", group=GROUP_PD_ZONES,
                         tooltip="Display equilibrium and swing boundary lines")
i_pd_show_fill         = input.bool(false, "Show Zone Fill", group=GROUP_PD_ZONES,
                         tooltip="Fill premium/discount zones with background color")
i_pd_show_ote          = input.bool(false, "Show OTE Zone (62-79%)", group=GROUP_PD_ZONES,
                         tooltip="Display Optimal Trade Entry zone lines at 62% and 79% retracement")
i_pd_show_ote_fill     = input.bool(false, "Show OTE Fill", group=GROUP_PD_ZONES,
                         tooltip="Fill the OTE zone between 62% and 79% lines")
i_pd_premium_color     = input.color(color.new(#FF5252, 85), "Premium Zone Color", group=GROUP_PD_ZONES)
i_pd_discount_color    = input.color(color.new(#4CAF50, 85), "Discount Zone Color", group=GROUP_PD_ZONES)
i_pd_equilibrium_color = input.color(color.new(#FFEB3B, 50), "Equilibrium Color", group=GROUP_PD_ZONES)
i_pd_grade_modifier    = input.bool(true, "Include in Grading", group=GROUP_PD_ZONES,
                         tooltip="Apply zone-based quality modifier to IFVG grades (+1 optimal, -1 wrong zone)")
```

### Consolidated request.security() for PD Swing Data

```pinescript
// Compute pivot expressions (evaluated in HTF context by request.security)
pd_pivot_high_expr = ta.pivothigh(high, i_pd_swing_lookback, i_pd_swing_lookback)
pd_pivot_low_expr = ta.pivotlow(low, i_pd_swing_lookback, i_pd_swing_lookback)
pd_swing_h_expr = ta.valuewhen(not na(pd_pivot_high_expr), pd_pivot_high_expr, 0)
pd_swing_l_expr = ta.valuewhen(not na(pd_pivot_low_expr), pd_pivot_low_expr, 0)

// PD Zone HTF Data - 1 call, 2 tuple elements
[pd_htf_swing_high, pd_htf_swing_low] = request.security(syminfo.tickerid, i_pd_timeframe, [pd_swing_h_expr, pd_swing_l_expr], lookahead = barmerge.lookahead_off)
```

### Zone Calculation with OTE

```pinescript
update_pd_zones() =>
    if i_enable_pd_zones and not na(pd_htf_swing_high) and not na(pd_htf_swing_low)
        g_pd_swing_high := pd_htf_swing_high
        g_pd_swing_low := pd_htf_swing_low
        float range_size = g_pd_swing_high - g_pd_swing_low
        if range_size > 0
            g_pd_equilibrium := g_pd_swing_low + (range_size * 0.5)
            g_pd_ote_low := g_pd_swing_low + (range_size * 0.62)
            g_pd_ote_high := g_pd_swing_low + (range_size * 0.79)
            g_pd_current_percent := ((close - g_pd_swing_low) / range_size) * 100
            if close > g_pd_equilibrium
                g_pd_current_zone := "premium"
            else if close < g_pd_equilibrium
                g_pd_current_zone := "discount"
            else
                g_pd_current_zone := "equilibrium"
        else
            g_pd_current_zone := "neutral"
    else
        g_pd_current_zone := "neutral"
```

### Grading Integration

```pinescript
// Updated signature:
calculate_grade(bool has_sweep, bool has_delivery, string momentum, bool has_dol, bool fvg_singular, int pd_zone_modifier) =>
    // ... existing Step 1 (tier determination) unchanged ...
    // ... existing Step 2 (quality_score) ...

    // Add PD zone modifier to quality score
    quality_score := quality_score + pd_zone_modifier

    // ... existing Step 3 (combine) unchanged ...

// Helper function:
get_pd_zone_modifier(bool is_bullish_ifvg) =>
    int modifier = 0
    if i_enable_pd_zones and i_pd_grade_modifier and g_pd_current_zone != "neutral" and g_pd_current_zone != "equilibrium"
        if is_bullish_ifvg
            if g_pd_current_zone == "discount"
                modifier := 1
            else if g_pd_current_zone == "premium"
                modifier := -1
        else
            if g_pd_current_zone == "premium"
                modifier := 1
            else if g_pd_current_zone == "discount"
                modifier := -1
    modifier
```

### Tooltip Update (D-08)

```pinescript
// In render_ifvg_boxes(), add pd_zone to tooltip text (after existing tooltip_text build):
pd_zone_text = not na(ifvg.pd_zone) and ifvg.pd_zone != "neutral" ? " [" + str.upper(ifvg.pd_zone) + "]" : ""

// Modify entry_label_text to include zone:
entry_label_text = ifvg.grade + " " + direction_text + pd_zone_text
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 14 separate request.security() calls | 2 consolidated tuple calls | Phase 1 (FIX-03) | Freed 12 budget slots; Phase 2 uses 1 more |
| Hardcoded fvg_singular=true | Dual-check singularity algorithm | Phase 1 (FIX-01) | Correct quality scores; PD modifier adds on top |
| No PD zone awareness in grading | +1/-1 PD zone modifier | Phase 2 (this phase) | Quality score range expands from [-2,+3] to [-3,+4] |

## Open Questions

1. **Pivot lookback default value**
   - What we know: PHASE4_PD_ZONES_PLAN.md suggests 5. The existing LTF swing lookback (`i_swing_lookback`) also defaults to 5. ICT typically uses 5-bar lookback for pivot detection.
   - What's unclear: Whether 5 is optimal for Daily timeframe PD zones specifically.
   - Recommendation: Default to 5 (matches existing convention and ICT standard). Input range 3-20 gives traders flexibility. This is a Claude's Discretion item and 5 is the recommended default.

2. **OTE zone colors**
   - What we know: Claude has discretion over OTE colors/opacity. The OTE zone represents the "optimal trade entry" retracement zone.
   - Recommendation: Use a distinct color from the zone fills -- suggest `color.new(#AB47BC, 70)` (purple, 70% opacity) for OTE lines. OTE fill at 85% opacity. Purple distinguishes OTE from red premium / green discount.

3. **Price outside dealing range**
   - What we know: Percentage can exceed 0-100% when price is outside the swing high/low range.
   - Recommendation: Display raw percentage (can show >100% or <0%). This is informative -- traders can see price has broken out of the range. Zone still correctly reports "premium" (above EQ) or "discount" (below EQ).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None -- Pine Script has no automated test framework |
| Config file | N/A |
| Quick run command | Copy to TradingView Pine Editor, Apply to chart |
| Full suite command | Visual verification on multiple symbols/timeframes |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PDZ-01 | HTF swing detection via request.security | manual-only | Apply indicator, compare zone lines to manual chart analysis | N/A |
| PDZ-02 | EQ at 50%, premium/discount classification | manual-only | Verify EQ line is exactly between swing H/L visually | N/A |
| PDZ-03 | Grade +1/-1 from PD zone position | manual-only | Compare grade of long in discount vs long in premium on same chart | N/A |
| PDZ-04 | Zone boundary lines and labels visible | manual-only | Enable PD zones, verify 3 lines + 3 labels appear | N/A |
| PDZ-05 | Zone fill between lines (optional) | manual-only | Toggle "Show Zone Fill", verify shaded regions appear | N/A |
| PDZ-06 | OTE zone lines at 62% and 79% | manual-only | Toggle "Show OTE Zone", verify 2 additional lines at correct levels | N/A |
| PDZ-07 | Grade distribution balanced | manual-only | Apply to ES/NQ Daily, inspect grade distribution | N/A |
| PDZ-08 | pd_zone stored on IFVG, shown in tooltip | manual-only | Hover over IFVG entry label, verify [PREMIUM]/[DISCOUNT] in tooltip | N/A |
| DSH-01 | Dashboard PD Zone row | manual-only | Check dashboard shows "PREMIUM" (red) or "DISCOUNT" (green) | N/A |
| DSH-02 | Dashboard Range % row | manual-only | Check dashboard shows percentage value matching visual zone position | N/A |

**Justification for manual-only:** Pine Script has no automated testing infrastructure. All validation requires visual verification on TradingView charts. This is a platform constraint, not a choice.

### Sampling Rate
- **Per task commit:** Compile check in TradingView Pine Editor (catches syntax errors)
- **Per wave merge:** Visual verification on 2-3 symbols (e.g., ES, NQ, BTC) across multiple timeframes
- **Phase gate:** Complete verification checklist (compile + visual + grade comparison)

### Wave 0 Gaps
None -- no test infrastructure to set up. Pine Script validation is inherently manual.

## Discretion Recommendations

These are Claude's Discretion items from CONTEXT.md with specific recommendations:

| Item | Recommendation | Rationale |
|------|---------------|-----------|
| OTE zone colors | `color.new(#AB47BC, 70)` (purple, 70% opacity) for lines | Distinguishes from red/green zone colors; purple = OTE is common in ICT tools |
| OTE fill color/opacity | `color.new(#AB47BC, 90)` (purple, 90% opacity) | Very subtle fill, only visible when explicitly enabled |
| Swing H/L line width | Width 1, dashed style | Subtler than EQ line; structural but not dominant |
| EQ line width | Width 2, solid style | Most important level -- slightly thicker, solid for emphasis |
| Pivot lookback default | 5 | Matches LTF swing lookback default and ICT standard |
| Dashboard PD Zone row styling | Zone name in ALL CAPS, colored text (red/green/gray) | Matches HTF Bias row styling pattern |
| Edge case: no swings | Set zone to "neutral", display "-" in dashboard | Graceful degradation; no visual clutter |
| Edge case: swing H < swing L | Treat as invalid (range <= 0), zone = "neutral" | Prevents nonsensical calculations |

## Project Constraints (from CLAUDE.md)

- **Platform:** Pine Script v6 on TradingView -- no build toolchain, single file
- **Testing:** Visual verification only -- no automated tests
- **Drawing limits:** Max 500 boxes, 500 lines, 500 labels -- FIFO cleanup required
- **Security calls:** Max 40 request.security() calls -- 2 currently used, Phase 2 adds 1
- **Single file:** All code in `src/IFVG_Indicator.pine` -- maintain section organization
- **No repainting:** All detection on `barstate.isconfirmed` only
- **No AI attribution:** No mentions of AI/Claude in commits, code comments, or PRs
- **Commit style:** Short descriptive messages with "Phase X:" prefix
- **Pine Script v6 syntax rules:** No blank lines in blocks, wrap multi-line operators in parens, cast math.abs/math.max to int when needed, `=` never as last token on a line

## Sources

### Primary (HIGH confidence)
- `PHASE4_PD_ZONES_PLAN.md` -- Pre-existing implementation blueprint with code examples, verified against current codebase structure
- `src/IFVG_Indicator.pine` -- Direct code inspection of all integration points (lines 92-122, 124-283, 284-307, 700-709, 1463-1529, 1662-1701, 838-868, 2027-2051, 2368-2434, 2439-2561)
- `strategy.md` Section 5.3 -- ICT Premium/Discount zone concept and optimal positioning rules
- `PRD.md` Section 3.6 -- PD zone feature specification
- CONTEXT.md (02-CONTEXT.md) -- 12 locked decisions and discretion areas

### Secondary (MEDIUM confidence)
- [Pine Wizards - ta.pivothigh documentation](https://pinewizards.com/technical-analysis-functions/ta-pivothigh-in-pine-script/) -- Function syntax and parameters verified
- [Pine Wizards - linefill.new documentation](https://pinewizards.com/drawing-on-charts/linefill-new-function/) -- linefill syntax and auto-deletion behavior verified
- [TradingView Official - Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) -- Tuple support in request.security(), 127-element limit
- [TradingView Official - Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) -- Drawing object limits, request.security() 40-call limit
- [TradingView Blog - Tuple Support](https://www.tradingview.com/blog/en/tuple-support-for-the-security-function-in-pine-script-18316/) -- Tuple consolidation pattern

### Tertiary (LOW confidence)
- None -- all findings verified through official or high-quality sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Pine Script v6 built-in functions are well-documented and stable. All functions used (ta.pivothigh, ta.valuewhen, linefill.new) are verified in official docs.
- Architecture: HIGH -- Integration points are precisely identified through direct code inspection. PHASE4_PD_ZONES_PLAN.md provides a verified blueprint.
- Pitfalls: HIGH -- Identified through code inspection and Pine Script v6 syntax rules in CLAUDE.md. All pitfalls have concrete prevention strategies.

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable -- Pine Script v6 API is mature, indicator codebase changes only through planned phases)
