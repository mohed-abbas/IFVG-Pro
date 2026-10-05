# Phase 4: HTF Swing-Based Premium/Discount Zones

## Overview

Implement true ICT-style Premium/Discount zones using HTF swing detection. The dealing range is defined by the **most recent confirmed swing high and swing low** on a user-selected timeframe (1H, 4H, or Daily), NOT mechanical highest/lowest over N bars.

**File**: `/Users/murx/Developer/personal/IFVG-Pro/src/IFVG_Indicator.pine`

---

## Core Concept

```
Swing High (5,598) ─────────────────────── 100% ─┐
                   │                              │ PREMIUM ZONE
                   │                              │
Equilibrium (5,140) ─────────────────────── 50% ─┤
                   │                              │
                   │                              │ DISCOUNT ZONE
Swing Low (4,683) ──────────────────────── 0%  ─┘
```

**Grading Integration:**
- Long in Discount → quality_score +1 (optimal)
- Long in Premium → quality_score -1 (suboptimal)
- Short in Premium → quality_score +1 (optimal)
- Short in Discount → quality_score -1 (suboptimal)

---

## Technical Approach

Use `ta.pivothigh/ta.pivotlow` + `ta.valuewhen()` to get the MOST RECENT confirmed swing:

```pinescript
// Detect pivot on HTF
htf_pivot_high = ta.pivothigh(high, 5, 5)  // Returns price on confirmation bar

// Get LAST confirmed value (even if many bars ago)
htf_swing_high = ta.valuewhen(not na(htf_pivot_high), htf_pivot_high, 0)
```

---

## Implementation Steps

### Step 1: Add Input Configuration (after line 268)

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Premium/Discount Zone Settings (Phase 4)
// ─────────────────────────────────────────────────────────────────────
string GROUP_PD_ZONES = "═══ Premium/Discount Zones ═══"
i_enable_pd_zones      = input.bool(true, "Enable PD Zones", group=GROUP_PD_ZONES,
                         tooltip="Calculate Premium/Discount zones based on HTF swings")
i_pd_timeframe         = input.timeframe("D", "PD Zone Timeframe", group=GROUP_PD_ZONES,
                         tooltip="Timeframe for swing detection (1H, 4H, Daily, Weekly)")
i_pd_swing_lookback    = input.int(5, "PD Swing Lookback", minval=3, maxval=20, group=GROUP_PD_ZONES,
                         tooltip="Bars left/right for pivot detection on HTF")
i_pd_show_lines        = input.bool(true, "Show PD Zone Lines", group=GROUP_PD_ZONES,
                         tooltip="Display equilibrium and zone boundary lines")
i_pd_show_fill         = input.bool(false, "Show Zone Fill", group=GROUP_PD_ZONES,
                         tooltip="Fill premium/discount zones with background color")
i_pd_premium_color     = input.color(color.new(#FF5252, 85), "Premium Zone Color", group=GROUP_PD_ZONES)
i_pd_discount_color    = input.color(color.new(#4CAF50, 85), "Discount Zone Color", group=GROUP_PD_ZONES)
i_pd_equilibrium_color = input.color(color.new(#FFEB3B, 50), "Equilibrium Color", group=GROUP_PD_ZONES)
i_pd_grade_modifier    = input.bool(true, "Include in Grading", group=GROUP_PD_ZONES,
                         tooltip="Apply zone-based quality modifier to IFVG grades")
```

### Step 2: Add Global Variables (after line 294)

```pinescript
// ══════════════════════════════════════════════════════════════════════
// Premium/Discount Zone Variables
// ══════════════════════════════════════════════════════════════════════
var float g_pd_swing_high = na      // Most recent HTF swing high
var float g_pd_swing_low = na       // Most recent HTF swing low
var float g_pd_equilibrium = na     // 50% level
var float g_pd_current_percent = na // Current price position (0-100%)
var string g_pd_current_zone = "neutral"  // "premium", "discount", "neutral"

// PD Zone visual elements
var line g_pd_high_line = na
var line g_pd_low_line = na
var line g_pd_eq_line = na
var linefill g_pd_premium_fill = na
var linefill g_pd_discount_fill = na
var label g_pd_high_label = na
var label g_pd_low_label = na
var label g_pd_eq_label = na
```

### Step 3: Add HTF Swing Detection (new Section 5C, after line 666)

```pinescript
// ══════════════════════════════════════════════════════════════════════
// SECTION 5C: HTF PREMIUM/DISCOUNT ZONE DETECTION (Phase 4)
// ══════════════════════════════════════════════════════════════════════

// Calculate pivots and get most recent confirmed values via request.security
pd_pivot_high_raw = ta.pivothigh(high, i_pd_swing_lookback, i_pd_swing_lookback)
pd_pivot_low_raw = ta.pivotlow(low, i_pd_swing_lookback, i_pd_swing_lookback)

pd_swing_high_ltf = ta.valuewhen(not na(pd_pivot_high_raw), pd_pivot_high_raw, 0)
pd_swing_low_ltf = ta.valuewhen(not na(pd_pivot_low_raw), pd_pivot_low_raw, 0)

// Request from PD timeframe
pd_htf_swing_high = request.security(syminfo.tickerid, i_pd_timeframe, pd_swing_high_ltf, lookahead=barmerge.lookahead_off)
pd_htf_swing_low = request.security(syminfo.tickerid, i_pd_timeframe, pd_swing_low_ltf, lookahead=barmerge.lookahead_off)
```

### Step 4: Add Zone Calculation Function (after HTF detection)

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Update PD Zone Calculations
// ─────────────────────────────────────────────────────────────────────
update_pd_zones() =>
    if i_enable_pd_zones and not na(pd_htf_swing_high) and not na(pd_htf_swing_low)
        g_pd_swing_high := pd_htf_swing_high
        g_pd_swing_low := pd_htf_swing_low

        float range = g_pd_swing_high - g_pd_swing_low

        if range > 0
            g_pd_equilibrium := g_pd_swing_low + (range * 0.5)
            g_pd_current_percent := ((close - g_pd_swing_low) / range) * 100

            if close > g_pd_equilibrium
                g_pd_current_zone := "premium"
            else if close < g_pd_equilibrium
                g_pd_current_zone := "discount"
            else
                g_pd_current_zone := "equilibrium"
    else
        g_pd_current_zone := "neutral"

// ─────────────────────────────────────────────────────────────────────
// Get PD Zone Grading Modifier
// Returns: +1 (optimal), -1 (suboptimal), 0 (neutral/disabled)
// ─────────────────────────────────────────────────────────────────────
get_pd_zone_modifier(bool is_bullish_ifvg) =>
    int modifier = 0

    if i_enable_pd_zones and i_pd_grade_modifier and g_pd_current_zone != "neutral"
        if is_bullish_ifvg
            // Long: Optimal in discount, suboptimal in premium
            if g_pd_current_zone == "discount"
                modifier := 1
            else if g_pd_current_zone == "premium"
                modifier := -1
        else
            // Short: Optimal in premium, suboptimal in discount
            if g_pd_current_zone == "premium"
                modifier := 1
            else if g_pd_current_zone == "discount"
                modifier := -1

    modifier
```

### Step 5: Modify Grading Function (line 1384)

**Change signature from:**
```pinescript
calculate_grade(bool has_sweep, bool has_delivery, string momentum, bool has_dol, bool fvg_singular) =>
```

**To:**
```pinescript
calculate_grade(bool has_sweep, bool has_delivery, string momentum, bool has_dol, bool fvg_singular, int pd_zone_modifier) =>
```

**Add after line 1425 (after sweep+delivery bonus):**
```pinescript
        // NEW: Premium/Discount Zone modifier
        quality_score := quality_score + pd_zone_modifier
```

### Step 6: Update calculate_grade() Call Site (line 1577)

**Replace:**
```pinescript
string grade = calculate_grade(
    has_sweep, has_delivery, momentum, has_dol, fvg_singular
)
```

**With:**
```pinescript
int pd_modifier = get_pd_zone_modifier(ifvg_is_bullish)

string grade = calculate_grade(
    has_sweep, has_delivery, momentum, has_dol, fvg_singular, pd_modifier
)
```

### Step 7: Add IFVG Type Field (line 91-115) - Optional

```pinescript
type IFVG
    // ... existing fields ...
    string pd_zone      // "premium", "discount", "equilibrium", or "neutral"
```

### Step 8: Add Zone Visualization (after line 2227)

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Render Premium/Discount Zone Lines
// ─────────────────────────────────────────────────────────────────────
render_pd_zones() =>
    if i_enable_pd_zones and not na(g_pd_swing_high) and not na(g_pd_swing_low)
        right_edge = bar_index + i_extend_bars
        left_edge = bar_index - 100

        // Delete old drawings
        if not na(g_pd_high_line)
            line.delete(g_pd_high_line)
        // ... (delete all other PD lines/labels/fills)

        if i_pd_show_lines
            // Swing High line
            g_pd_high_line := line.new(left_edge, g_pd_swing_high, right_edge, g_pd_swing_high,
                              color=i_pd_premium_color, style=line.style_dashed, width=1)

            // Swing Low line
            g_pd_low_line := line.new(left_edge, g_pd_swing_low, right_edge, g_pd_swing_low,
                             color=i_pd_discount_color, style=line.style_dashed, width=1)

            // Equilibrium line (50%)
            g_pd_eq_line := line.new(left_edge, g_pd_equilibrium, right_edge, g_pd_equilibrium,
                            color=i_pd_equilibrium_color, style=line.style_solid, width=2)

            // Labels
            g_pd_high_label := label.new(right_edge, g_pd_swing_high, "Swing H (100%)",
                               style=label.style_none, textcolor=i_pd_premium_color, size=size.tiny)
            g_pd_low_label := label.new(right_edge, g_pd_swing_low, "Swing L (0%)",
                              style=label.style_none, textcolor=i_pd_discount_color, size=size.tiny)
            g_pd_eq_label := label.new(right_edge, g_pd_equilibrium, "EQ (50%)",
                             style=label.style_none, textcolor=i_pd_equilibrium_color, size=size.tiny)

        // Optional zone fill
        if i_pd_show_fill and i_pd_show_lines
            g_pd_premium_fill := linefill.new(g_pd_high_line, g_pd_eq_line, i_pd_premium_color)
            g_pd_discount_fill := linefill.new(g_pd_eq_line, g_pd_low_line, i_pd_discount_color)
```

### Step 9: Update Dashboard (line 2251-2325)

**Expand table from 10 to 12 rows:**
```pinescript
var table dashboard = table.new(position.top_right, 2, 12, ...)
```

**Add new rows after existing rows:**
```pinescript
// Row 10: PD Zone
string pd_zone_text = i_enable_pd_zones and g_pd_current_zone != "neutral" ? str.upper(g_pd_current_zone) : "-"
color pd_zone_color = g_pd_current_zone == "premium" ? color.red : g_pd_current_zone == "discount" ? color.green : color.gray
table.cell(dashboard, 0, 10, "PD Zone:", text_color=color.gray, text_size=size.small)
table.cell(dashboard, 1, 10, pd_zone_text, text_color=pd_zone_color, text_size=size.small)

// Row 11: Zone Percentage
string zone_pct_text = i_enable_pd_zones and not na(g_pd_current_percent) ? str.tostring(g_pd_current_percent, "#.0") + "%" : "-"
table.cell(dashboard, 0, 11, "Range %:", text_color=color.gray, text_size=size.small)
table.cell(dashboard, 1, 11, zone_pct_text, text_color=color.white, text_size=size.small)
```

### Step 10: Update Main Loop (Section 12)

**Add after swing detection (~line 2343):**
```pinescript
// Step 1B: Update Premium/Discount zones
update_pd_zones()
```

**Add after other rendering (~line 2449):**
```pinescript
// Step 9C: Render Premium/Discount zones
render_pd_zones()
```

---

## Code Changes Summary

| Location | Line(s) | Change |
|----------|---------|--------|
| Inputs | After 268 | Add GROUP_PD_ZONES (9 inputs) |
| Globals | After 294 | Add PD zone variables |
| HTF Detection | After 666 | Add Section 5C with request.security |
| Zone Functions | After 666 | Add update_pd_zones() and get_pd_zone_modifier() |
| Grading Signature | 1384 | Add pd_zone_modifier parameter |
| Quality Score | After 1425 | Add pd_zone_modifier to score |
| Grade Call | 1577 | Pass pd_modifier to calculate_grade() |
| IFVG Type | 91-115 | Add pd_zone field (optional) |
| Visualization | After 2227 | Add render_pd_zones() function |
| Dashboard | 2251 | Expand to 12 rows |
| Dashboard | After 2325 | Add PD Zone and Range % rows |
| Main Loop | After 2343 | Call update_pd_zones() |
| Main Loop | After 2449 | Call render_pd_zones() |

---

## Quality Score Impact

**Before (current):**
- Momentum: +1/-1
- FVG Clarity: +1/-1
- Sweep+Delivery: +1
- **Range: -2 to +3**

**After (with PD zones):**
- Momentum: +1/-1
- FVG Clarity: +1/-1
- Sweep+Delivery: +1
- **PD Zone: +1/-1** (NEW)
- **Range: -3 to +4**

---

## Verification Checklist

1. **Compile**: No errors in TradingView
2. **Swing Detection**: Compare swing levels with manual chart analysis
3. **Zone Math**: Verify EQ is exactly 50% between swing high/low
4. **Percentage**: 0% at swing low, 50% at EQ, 100% at swing high
5. **Grading**:
   - Long in discount = grade improves
   - Long in premium = grade degrades
   - Short in premium = grade improves
   - Short in discount = grade degrades
6. **Dashboard**: Zone and % update correctly
7. **Visualization**: Lines at correct levels
8. **Edge Cases**:
   - No swings detected → graceful handling
   - Swing high < swing low → prevent divide by zero
   - Price outside range → percentage can exceed 0-100%

---

## Files to Modify

- `/Users/murx/Developer/personal/IFVG-Pro/src/IFVG_Indicator.pine` - Main indicator file

## Reference Files

- `/Users/murx/Developer/personal/IFVG-Pro/ARCHITECTURE.md` - Module structure
- `/Users/murx/Developer/personal/IFVG-Pro/PRD.md` - Feature spec (Section 3.6)
- `/Users/murx/Developer/personal/IFVG-Pro/CLAUDE.md` - Commit guidelines
