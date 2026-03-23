# Stack Research

**Domain:** TradingView Pine Script v6 indicator — Phase 4 APIs (PD zones, sessions, dashboard, alerts)
**Researched:** 2026-03-23
**Confidence:** HIGH

## Recommended Stack

This is not a technology selection problem — the project is locked to Pine Script v6 on TradingView. This document specifies the **exact Pine Script v6 APIs, patterns, and budget constraints** needed for Phase 4 features.

### Core APIs Required for Phase 4

| API | Purpose | Why This API | Confidence |
|-----|---------|-------------|------------|
| `ta.pivothigh(source, leftbars, rightbars)` | HTF swing detection for PD zones | Only built-in pivot function; returns `na` for non-pivot bars, price on confirmation. Requires `rightbars` delay for confirmation — not optional. | HIGH |
| `ta.valuewhen(condition, source, occurrence)` | Persist last confirmed swing value | Retrieves the value of `source` when `condition` was last true. Essential because `ta.pivothigh` returns `na` on most bars — `ta.valuewhen` carries the last confirmed value forward. | HIGH |
| `request.security(symbol, timeframe, expression)` | HTF data retrieval for PD zones | Required for any cross-timeframe data. Already used (16 calls). Tuple consolidation is the primary optimization lever. | HIGH |
| `time(timeframe, session, timezone)` | Session detection (Asia/London/NY) | Returns bar UNIX timestamp if bar falls within session, `na` otherwise. Zero `request.security()` cost — purely LTF calculation. | HIGH |
| `input.session(defval, title)` | User-configurable session times | Returns valid session string for `time()`. Users can adjust session boundaries for their timezone/market. | HIGH |
| `linefill.new(line1, line2, color)` | PD zone background fill | Only way to fill between two dynamically-positioned lines. `fill()` only works between plots/hlines — not suitable for zone visualization at arbitrary prices. | HIGH |
| `alertcondition(condition, title, message)` | Named alert conditions in indicator UI | Required for indicators (not strategies). Creates selectable conditions in TradingView's "Create Alert" dialog. Must be at global scope (column zero). | HIGH |
| `alert(message, freq)` | Programmatic alert triggering | Accepts `series string` messages (dynamic content). Can be placed inside `if` blocks. Complementary to `alertcondition()` — use for webhook/dynamic payloads. | HIGH |
| `table.cell(table_id, column, row, text)` | Dashboard expansion | Already used. Expanding from 10 to 14+ rows for PD zone and session data. | HIGH |

### API Usage Patterns

#### Pattern 1: Tuple-Consolidated request.security()

**Current problem:** 16 individual `request.security()` calls for 2 HTF timeframes (7 values each + 2 ATR).

**Solution:** Consolidate into 2 calls using tuple returns.

```pinescript
// BEFORE: 7 calls for HTF1 data
htf_high = request.security(syminfo.tickerid, i_htf_timeframe, high, ...)
htf_low = request.security(syminfo.tickerid, i_htf_timeframe, low, ...)
htf_close = request.security(syminfo.tickerid, i_htf_timeframe, close, ...)
htf_high_2 = request.security(syminfo.tickerid, i_htf_timeframe, high[2], ...)
htf_low_2 = request.security(syminfo.tickerid, i_htf_timeframe, low[2], ...)
htf_bar_idx = request.security(syminfo.tickerid, i_htf_timeframe, bar_index, ...)
htf_atr = request.security(syminfo.tickerid, i_htf_timeframe, ta.atr(period), ...)

// AFTER: 1 call with tuple (7 elements)
[htf_high, htf_low, htf_close, htf_high_2, htf_low_2, htf_bar_idx_raw, htf_atr] =
    request.security(syminfo.tickerid, i_htf_timeframe,
        [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
        lookahead=barmerge.lookahead_off)
```

**Savings:** 16 calls reduced to 2 calls. Frees 14 slots.

#### Pattern 2: PD Zone Swing Detection via request.security() with Pivots

```pinescript
// Calculate pivots on LTF context (they get evaluated in HTF context by request.security)
pd_pivot_h = ta.pivothigh(high, i_pd_swing_lookback, i_pd_swing_lookback)
pd_pivot_l = ta.pivotlow(low, i_pd_swing_lookback, i_pd_swing_lookback)
pd_last_swing_h = ta.valuewhen(not na(pd_pivot_h), pd_pivot_h, 0)
pd_last_swing_l = ta.valuewhen(not na(pd_pivot_l), pd_pivot_l, 0)

// Single request.security call for both PD zone values
[pd_htf_swing_high, pd_htf_swing_low] = request.security(
    syminfo.tickerid, i_pd_timeframe,
    [pd_last_swing_h, pd_last_swing_l],
    lookahead=barmerge.lookahead_off)
```

**Cost:** 1 `request.security()` call (not 2 as PHASE4_PD_ZONES_PLAN.md proposes).

#### Pattern 3: Session Detection Without request.security()

```pinescript
// Session strings — no request.security() needed
i_asian_session  = input.session("1800-0000", "Asian Session",
                   tooltip="Default: 6PM-12AM ET")
i_london_session = input.session("0200-1000", "London Session",
                   tooltip="Default: 2AM-10AM ET")
i_ny_session     = input.session("0700-1600", "New York Session",
                   tooltip="Default: 7AM-4PM ET")

// Detect session membership using time() — returns na if outside session
bool in_asian  = not na(time(timeframe.period, i_asian_session, "America/New_York"))
bool in_london = not na(time(timeframe.period, i_london_session, "America/New_York"))
bool in_ny     = not na(time(timeframe.period, i_ny_session, "America/New_York"))

// Track session highs/lows using var (persist across bars)
var float asian_high = na
var float asian_low  = na
var bool  asian_was_active = false

// Reset on session start, track during session
if in_asian
    if not asian_was_active  // Session just started
        asian_high := high
        asian_low  := low
    else
        asian_high := math.max(asian_high, high)
        asian_low  := math.min(asian_low, low)
asian_was_active := in_asian
```

**Cost:** Zero `request.security()` calls. The `time()` function with session parameter works entirely on LTF data.

#### Pattern 4: linefill for Zone Visualization

```pinescript
// Create lines first (required by linefill)
var line pd_high_line = na
var line pd_eq_line   = na
var line pd_low_line  = na
var linefill premium_fill  = na
var linefill discount_fill = na

// Delete old, create new (matching existing indicator pattern)
if not na(pd_high_line)
    line.delete(pd_high_line)
    line.delete(pd_eq_line)
    line.delete(pd_low_line)
    // linefills auto-delete when their lines are deleted

pd_high_line := line.new(left, swing_high, right, swing_high, ...)
pd_eq_line   := line.new(left, equilibrium, right, equilibrium, ...)
pd_low_line  := line.new(left, swing_low, right, swing_low, ...)

// linefill between lines — only one fill allowed per line pair
premium_fill  := linefill.new(pd_high_line, pd_eq_line, premium_color)
discount_fill := linefill.new(pd_eq_line, pd_low_line, discount_color)
```

**Key behavior:** linefills auto-delete when either referenced line is deleted. No explicit `linefill.delete()` needed if using the delete-and-recreate pattern.

#### Pattern 5: alertcondition() at Global Scope + alert() in Logic

```pinescript
// alertcondition() MUST be at global scope (column zero)
// Creates named conditions in "Create Alert" dialog
alertcondition(
    new_ifvg_detected and latest_grade_value >= min_grade_value,
    title="New Valid IFVG Entry",
    message='New {{plot("grade_plot")}} IFVG on {{ticker}} {{interval}}'
)

alertcondition(
    be_taken_this_bar,
    title="IFVG Entry Invalidated (BE Taken)",
    message='IFVG entry invalidated on {{ticker}} {{interval}} — BE level breached'
)

alertcondition(
    ifvg_mitigated_this_bar,
    title="IFVG Mitigated",
    message='IFVG mitigated on {{ticker}} {{interval}}'
)

// alert() for dynamic messages (inside conditional blocks)
if new_ifvg_detected and latest_grade_value >= min_grade_value
    alert("New " + latest_grade + " IFVG on " + syminfo.ticker +
          " | Entry: " + str.tostring(entry_price, format.mintick) +
          " | SL: " + str.tostring(sl_price, format.mintick),
          alert.freq_once_per_bar_close)
```

**Why both:** `alertcondition()` gives users a menu of named alert options in the UI. `alert()` enables dynamic messages with exact prices for webhook integrations. They serve different use cases and should both be implemented.

### Supporting Patterns

| Pattern | Purpose | When to Use |
|---------|---------|-------------|
| `var` keyword for persistent state | Session H/L tracking, zone values | Any value that must survive across bars |
| `barstate.isconfirmed` guard | Prevent repainting in all detection | Every detection/calculation block (already used throughout) |
| `barstate.islast` guard | Dashboard rendering optimization | Table rendering only — draw once on last bar |
| `na()` checks before field access | Prevent runtime errors on optional fields | Every access to potentially unset IFVG/FVG fields |
| `line.set_*()` / `box.set_*()` | Update drawing objects in place | Consider for Phase 4 to replace delete-and-recreate pattern (performance gain, reduces drawing object churn) |

## request.security() Budget Analysis

This is the most critical constraint for Phase 4. Hard limit: 40 calls (64 for Ultimate plan users).

### Current State (Phase 3)

| Calls | Timeframe | Data Retrieved | Source Lines |
|-------|-----------|----------------|-------------|
| 7 | `i_htf_timeframe` (HTF1) | high, low, close, high[2], low[2], bar_index, ATR | 653-659, 679 |
| 7 | `i_htf_timeframe_2` (HTF2) | high, low, close, high[2], low[2], bar_index, ATR | 662-668, 680 |
| 2 | (counted in above) | ATR for HTF1 and HTF2 | 679-680 |
| **16** | **Total** | | |

### After Tuple Consolidation (Refactor)

| Calls | Timeframe | Data Retrieved |
|-------|-----------|----------------|
| 1 | HTF1 | [high, low, close, high[2], low[2], bar_index, ATR] (7 tuple elements) |
| 1 | HTF2 | [high, low, close, high[2], low[2], bar_index, ATR] (7 tuple elements) |
| **2** | **Total** | **14 tuple elements** |

**Savings: 14 calls freed** (16 down to 2).

### Phase 4 Budget (After Consolidation)

| Feature | Calls Needed | Tuple Elements | Rationale |
|---------|-------------|----------------|-----------|
| Existing HTF (consolidated) | 2 | 14 | 7 values per HTF timeframe |
| PD zone swings | 1 | 2 | Swing high + swing low from PD timeframe |
| Session tracking | 0 | 0 | Uses `time()` with session strings — no `request.security()` |
| Dashboard expansion | 0 | 0 | Pure rendering, no external data |
| Alerts | 0 | 0 | alertcondition/alert operate on existing data |
| **Phase 4 Total** | **3** | **16** | |

### Budget Summary

| State | Calls Used | Remaining | % of 40 |
|-------|-----------|-----------|---------|
| Current (Phase 3, no consolidation) | 16 | 24 | 40% |
| After consolidation (refactor) | 2 | 38 | 5% |
| After Phase 4 additions | 3 | 37 | 7.5% |
| **Available for future phases** | — | **37** | **92.5%** |

**Tuple element budget:** 16 of 127 max = 12.6% used. Massive headroom.

### Budget Recommendation

Consolidate the existing 16 calls into 2 tuple calls as the **first step** of Phase 4. This is not optional — it is prerequisite work that transforms the constraint from "tight budget requiring careful planning" to "abundant headroom for any reasonable feature set."

If PD zones use the same timeframe as HTF1 or HTF2 (e.g., user selects "D" for both), the PD zone data can be folded into the existing HTF tuple, reducing Phase 4 to **2 total calls**. However, since the PD timeframe is independently selectable via `i_pd_timeframe`, keep it as a separate call for flexibility.

## Drawing Object Budget Analysis

Hard limits: 500 boxes, 500 lines, 500 labels (per indicator). No documented limit on linefill count, but linefills depend on lines.

### Phase 4 Drawing Additions

| Feature | Lines | Labels | Linefills | Boxes |
|---------|-------|--------|-----------|-------|
| PD zones (swing H, swing L, EQ) | 3 | 3 | 2 | 0 |
| Session H/L (3 sessions x 2 levels) | 6 | 6 | 0 | 0 |
| **Phase 4 total new** | **9** | **9** | **2** | **0** |

These are fixed-count elements (not per-IFVG), so they add a constant overhead regardless of market activity. The budget impact is minimal.

### Current Drawing Consumption (Worst Case)

| Element | Per-IFVG | Max IFVGs (default 30) | Total |
|---------|----------|----------------------|-------|
| IFVG box + delivery box | 2 boxes | 30 | 60 boxes |
| IFVG label | 1 label | 30 | 30 labels |
| BE + SL + entry lines | 3 lines | 30 | 90 lines |
| Entry label | 1 label | 30 | 30 labels |
| FVG boxes + labels | 2 per FVG | 20 max | 40 boxes, 20 labels |
| Liquidity lines + labels | 2 per level | 30 max | 30 lines, 30 labels |
| HTF FVG/IFVG boxes + labels | 2 per | ~20 each | 40 boxes, 40 labels |
| **Subtotal** | | | ~140 boxes, ~120 lines, ~150 labels |

Adding 9 lines + 9 labels + 2 linefills = well within limits. No concern.

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Individual `request.security()` calls for same timeframe | Wastes call budget (16 vs 2 calls for same data) | Tuple returns: `[a, b, c] = request.security(...)` |
| `request.security_lower_tf()` for session tracking | Returns arrays, adds complexity, uses intrabar budget (100K limit), overkill for session H/L | `time(timeframe.period, session_string, timezone)` with `var` state tracking |
| `fill()` for PD zone visualization | Only works between `plot()` or `hline()` outputs — cannot fill between dynamically-positioned price levels | `linefill.new(line1, line2, color)` |
| Hardcoded session times without timezone | Breaks across exchanges, ignores DST | `input.session()` with explicit IANA timezone (e.g., `"America/New_York"`) |
| `alertcondition()` inside `if` blocks | Will not compile — must be at global scope (column zero) | Place at file level; use `alert()` for conditional dynamic messages |
| `alert.freq_all` for trading signals | Fires multiple times per bar during realtime — causes duplicate alerts | `alert.freq_once_per_bar_close` for confirmed signals |
| `line.set_*()` / `box.set_*()` mixed with delete-and-recreate | Inconsistent patterns create bugs. Pick one. | Use delete-and-recreate for Phase 4 (matches existing codebase pattern). Consider full migration to set_*() as a future optimization. |
| More than 9 tables per indicator | Hard limit — TradingView allows max 9 tables (one per position) | Expand existing dashboard table rows, do not create new tables |

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `time()` for sessions | `request.security()` on session TF | Only if you need session data from a different symbol (e.g., forex session on crypto chart) |
| `ta.pivothigh/low` + `ta.valuewhen` | Manual swing detection with for loops | Never — `ta.pivothigh/low` is optimized, well-tested, and standard practice |
| `alertcondition()` + `alert()` combined | `alert()` only | If you only need dynamic messages and do not care about named conditions in UI. But providing both gives users flexibility. |
| `linefill.new()` for zone fill | `bgcolor()` with conditions | If you want full-width background coloring (column fill) rather than zone-bounded fill. Less precise but simpler. |
| Expand existing 2-column table | Multi-column table redesign | Only if dashboard information density becomes unmanageable at 14+ rows. Not needed for Phase 4 scope. |

## Platform Constraints Summary

| Constraint | Limit | Current Usage | After Phase 4 | Headroom |
|-----------|-------|---------------|---------------|----------|
| `request.*()` calls | 40 | 16 (2 after consolidation) | 3 | 37 (92%) |
| Tuple elements | 127 | 0 (no tuples yet) | 16 | 111 (87%) |
| Boxes | 500 | ~140 worst case | ~140 | ~360 (72%) |
| Lines | 500 | ~120 worst case | ~129 | ~371 (74%) |
| Labels | 500 | ~150 worst case | ~159 | ~341 (68%) |
| Linefills | undocumented | 0 | 2 | ample |
| Tables | 9 (one per position) | 1 | 1 | 8 |
| Compiled tokens | 100,000 | unknown (~2,500 lines) | ~3,000 lines | likely fine |

## Session Time Defaults

For ICT/SMC trading methodology, standard session times (ET/New York timezone):

| Session | Default Times (ET) | Session String | IANA Timezone |
|---------|-------------------|----------------|---------------|
| Asian (Tokyo) | 7:00 PM - 12:00 AM | `"1900-0000"` | `"America/New_York"` |
| London | 2:00 AM - 10:00 AM | `"0200-1000"` | `"America/New_York"` |
| New York AM | 7:00 AM - 12:00 PM | `"0700-1200"` | `"America/New_York"` |
| New York PM | 12:00 PM - 4:00 PM | `"1200-1600"` | `"America/New_York"` |

Use `"America/New_York"` as the timezone because ICT methodology uses ET as the reference timezone. IANA notation handles DST automatically — fixed UTC offsets do not.

## Alert Design Recommendations

| Alert | Type | Frequency | Message Content |
|-------|------|-----------|-----------------|
| New valid IFVG entry | `alertcondition()` + `alert()` | `freq_once_per_bar_close` | Grade, direction, entry price, SL price |
| Entry invalidated (BE taken) | `alertcondition()` + `alert()` | `freq_once_per_bar_close` | Which IFVG, invalidation reason |
| IFVG mitigated | `alertcondition()` | `freq_once_per_bar_close` | Direction, mitigation level |
| Grade upgrade/downgrade | `alert()` only | `freq_once_per_bar_close` | Old grade, new grade, reason |

Use `alert.freq_once_per_bar_close` for all trading signals to prevent repainting alerts. The `freq_once_per_bar` and `freq_all` options fire during realtime bar construction, which means the condition could change before bar close.

## Sources

- [TradingView Pine Script Docs: Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) — request.security() tuples, limits, dynamic requests (HIGH confidence)
- [TradingView Pine Script Docs: Alerts](https://www.tradingview.com/pine-script-docs/concepts/alerts/) — alertcondition() vs alert() signatures and scope rules (HIGH confidence)
- [TradingView Pine Script Docs: Time](https://www.tradingview.com/pine-script-docs/concepts/time/) — time() function, session strings, timezone handling (HIGH confidence)
- [TradingView Pine Script Docs: Fills](https://www.tradingview.com/pine-script-docs/visuals/fills/) — linefill.new() behavior and constraints (HIGH confidence)
- [TradingView Pine Script Docs: Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) — all hard limits (HIGH confidence)
- [TradingView Pine Script Docs: Profiling](https://www.tradingview.com/pine-script-docs/writing/profiling-and-optimization/) — table and performance optimization (HIGH confidence)
- [TradingView Blog: Tuple Support for Security](https://www.tradingview.com/blog/en/tuple-support-for-the-security-function-in-pine-script-18316/) — tuple consolidation patterns (HIGH confidence)
- [LuxAlgo: 5 Causes of Slow Pine Scripts](https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/) — request.security consolidation performance data (MEDIUM confidence)
- [TradersPost: Pine Script v6 Dynamic Requests](https://blog.traderspost.io/article/pine-script-v6-dynamic-requests) — v6-specific dynamic request features (MEDIUM confidence)

---
*Stack research for: IFVG Pro Phase 4 — PD Zones, Sessions, Dashboard, Alerts*
*Researched: 2026-03-23*
