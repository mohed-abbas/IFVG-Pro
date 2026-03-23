# Architecture Research

**Domain:** TradingView Pine Script v6 overlay indicator -- Phase 4 feature integration (PD zones, sessions, dashboard, alerts) into existing 2,511-line single-file architecture
**Researched:** 2026-03-23
**Confidence:** HIGH

## Current System Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        INDICATOR DECLARATION                         │
│  indicator("IFVG Indicator", overlay=true, max_boxes_count=500...)   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ S1: Types│  │ S2: Inputs   │  │ S3: Data     │  │ S4: Utils   │  │
│  │ 5 types  │  │ 9 groups     │  │ 10 var arrays│  │ helpers     │  │
│  └──────────┘  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                                      │
│  INPUT + FOUNDATION LAYER (lines 36-597)                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │ S5: LTF FVG  │  │ S5B: HTF FVG │  │ S6: Swing/Liquidity     │   │
│  │ detect_fvg() │  │ req.security │  │ swings, EQH/EQL, sweeps │   │
│  │              │  │ (16 calls)   │  │                          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                                                                      │
│  DETECTION ENGINE (lines 598-1223)                                   │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐  ┌────────────────────────────────────┐   │
│  │ S7: Grading/BE/SL    │  │ S8: Inversion Detection            │   │
│  │ grade calc, DOL,     │  │ FVG -> IFVG conversion, creates    │   │
│  │ momentum, sweep check│  │ full IFVG with all grading data    │   │
│  └──────────────────────┘  └────────────────────────────────────┘   │
│                                                                      │
│  GRADING + INVERSION ENGINE (lines 1224-1637)                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │
│  │ S9: State    │  │ S10: Render  │  │ S11: Dash    │               │
│  │ BE/SL/DOL   │  │ boxes, lines │  │ 10-row table │               │
│  │ mitigations  │  │ labels       │  │ top_right    │               │
│  └──────────────┘  └──────────────┘  └──────────────┘               │
│                                                                      │
│  STATE UPDATE + RENDERING LAYER (lines 1638-2387)                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │ S12: MAIN EXECUTION LOOP                                     │    │
│  │ Sequential pipeline: detect -> update -> grade -> render      │    │
│  │ Gated on barstate.isconfirmed + i_show_indicator              │    │
│  └──────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ORCHESTRATION LAYER (lines 2388-2512)                               │
└──────────────────────────────────────────────────────────────────────┘
```

### How Phase 4 Features Map Into This Architecture

```
                          EXISTING                    PHASE 4 ADDITIONS
                          ────────                    ─────────────────
S1: Types              5 custom types              + SessionData type (optional)
                                                   + pd_zone field on IFVG

S2: Inputs             9 input groups              + GROUP_PD_ZONES (9 inputs)
                                                   + GROUP_SESSIONS (8-10 inputs)
                                                   + GROUP_ALERTS (5-7 inputs)

S3: Data Store         10 var arrays               + PD zone scalar vars (5-6)
                                                   + Session tracking vars (9-12)
                                                   + Alert state booleans (3-4)

S5B: HTF Detection     16 request.security()       + 2 req.security() for PD swings
                                                   = 18 of 40 budget used

S5C: PD Zone Detection (NEW SECTION)               + update_pd_zones()
                                                   + get_pd_zone_modifier()

S6B: Session Detection (NEW SECTION)               + session time checks (NO req.security)
                                                   + session H/L tracking

S7: Grading            calculate_grade(5 params)   + calculate_grade(6 params)
                                                     6th param: pd_zone_modifier

S8: Inversion          check_inversions()          + pass pd_modifier to grade calc
                                                   + store pd_zone on IFVG

S10: Rendering         5 render functions          + render_pd_zones()
                                                   + render_session_levels()

S11: Dashboard         10-row, 2-column table      + 4-6 new rows (14-16 total)

S12: Main Loop         15 steps                    + update_pd_zones() after step 1
                                                   + update_sessions() after step 1
                                                   + render_pd_zones() in step 9
                                                   + render_session_levels() in step 9

S12B: Alerts           (NEW SECTION)               + alert() calls at global scope
                                                   + alertcondition() at global scope
```

## Component Boundaries and Responsibilities

### Existing Components (Unchanged)

| Component | Responsibility | Phase 4 Impact |
|-----------|----------------|----------------|
| FVG Detection (S5) | 3-candle LTF FVG pattern detection | None -- untouched |
| HTF Detection (S5B) | HTF OHLC via request.security, HTF FVG/IFVG detection | Shares request.security budget |
| Swing/Liquidity (S6) | Swing points, EQH/EQL, ITH/ITL, sweep detection | None -- untouched |
| State Update (S9) | BE/SL status, DOL refresh, mitigation removal | None -- untouched |

### New Components (Phase 4)

| Component | Responsibility | Communicates With |
|-----------|----------------|-------------------|
| PD Zone Detection (S5C) | HTF swing detection via request.security, zone calculation | S3 (writes PD globals), S7 (grading reads zone), S10 (rendering reads zone), S11 (dashboard reads zone) |
| Session Tracking (S6B) | Detect Asia/London/NY session boundaries, track session H/L | S3 (writes session vars), S11 (dashboard reads session data), S12B (alerts reference session levels) |
| PD Zone Rendering | Draw equilibrium/premium/discount lines and fills | S3 (reads PD globals), S2 (reads visual settings) |
| Session Rendering | Draw session H/L horizontal rays | S3 (reads session vars), S2 (reads visual settings) |
| Alert System (S12B) | Fire alerts on IFVG detection, invalidation, mitigation | S3 (reads IFVG array state), S8 (inversion creates alert trigger), S9 (mitigation creates alert trigger) |

### Modified Components (Phase 4)

| Component | What Changes | Why |
|-----------|-------------|-----|
| Grading (S7) | `calculate_grade()` gains `pd_zone_modifier` param | PD zone position affects quality score (+1/-1) |
| Inversion (S8) | `check_inversions()` calls `get_pd_zone_modifier()` before grading, stores `pd_zone` on IFVG | Zone must be captured at inversion time, not later |
| Dashboard (S11) | Table grows from 10 to 14-16 rows | Displays PD zone, range %, session data, alert status |
| IFVG Type (S1) | Gains `pd_zone` string field | Records zone at time of inversion for historical accuracy |

## Data Flow

### Per-Bar Processing Pipeline (Phase 4 Augmented)

```
if barstate.isconfirmed:
                                              EXISTING              NEW (Phase 4)
                                              ────────              ─────────────
  1. detect_swing_points()                        X
  1B. update_pd_zones()                                                  X
  1C. update_session_tracking()                                          X
  2. check_equal_highs/lows()                     X
  3. check_liquidity_sweeps()                     X
  4. detect_fvg() + delivery tracking             X
  4B. detect_htf_fvg() (x2)                       X
  5. check_inversions()                           X          (modified: passes pd_modifier)
  5B. check_htf_inversions() (x2)                 X
  6. update_be_status()                           X
  6.5. update_dol_status()                        X
  7. check_mitigations()                          X
  8. find_most_recent_ifvg()                      X
  9. render_fvg_boxes()                           X
  9. render_ifvg_boxes()                          X
  9B. render_htf_boxes() (x4)                     X
  9C. render_pd_zones()                                                  X
  9D. render_session_levels()                                            X
  9E. render_liquidity_lines()                    X
  9F. render_dashboard()                          X          (modified: +4-6 rows)

AFTER main loop (global scope, NOT inside if):
  alertcondition() calls                                                 X
  alert() calls (inside conditional)                                     X
```

### Critical Ordering Constraint

PD zone calculation (`update_pd_zones()`) MUST execute before `check_inversions()` because the grading algorithm needs `g_pd_current_zone` to compute `get_pd_zone_modifier()` at inversion time. Placing it after step 1 (swing detection) is correct because PD zones depend on HTF swings, not LTF swings.

Session tracking (`update_session_tracking()`) has no dependency on other detection steps and can run early. It only writes session-local state variables. Nothing downstream in the detection pipeline reads session data -- only rendering and alerts consume it.

### Data Dependencies Graph

```
request.security() [PD HTF swings]
        |
        v
  update_pd_zones() --> g_pd_swing_high, g_pd_swing_low, g_pd_current_zone
        |
        v
  get_pd_zone_modifier() <-- called inside check_inversions()
        |
        v
  calculate_grade(... pd_zone_modifier) --> IFVG.grade, IFVG.pd_zone
        |
        v
  render_dashboard() <-- reads g_pd_current_zone, IFVG.pd_zone
  render_pd_zones() <-- reads g_pd_swing_high/low, g_pd_equilibrium

time() [session time checks, NO request.security]
        |
        v
  update_session_tracking() --> g_session_asia_high/low, g_session_london_high/low, etc.
        |
        v
  render_session_levels() <-- reads session vars
  render_dashboard() <-- reads session summary
  alert() <-- references session levels as liquidity targets (future)
```

## request.security() Budget Allocation

This is the most critical resource constraint. TradingView allows 40 unique `request.security()` calls (64 for Ultimate plan users). The indicator currently uses 16.

### Current Usage (16 of 40)

| Purpose | Calls | Timeframe |
|---------|-------|-----------|
| HTF 1 OHLC data | 6 | `i_htf_timeframe` |
| HTF 2 OHLC data | 6 | `i_htf_timeframe_2` |
| HTF 1 ATR | 1 | `i_htf_timeframe` |
| HTF 2 ATR | 1 | `i_htf_timeframe_2` |
| HTF 1 bar_index | 1 | `i_htf_timeframe` |
| HTF 2 bar_index | 1 | `i_htf_timeframe_2` |
| **Total** | **16** | |

### Phase 4 Additions (2 new calls)

| Purpose | Calls | Timeframe |
|---------|-------|-----------|
| PD zone swing high | 1 | `i_pd_timeframe` |
| PD zone swing low | 1 | `i_pd_timeframe` |
| **Phase 4 Total** | **2** | |

### Budget After Phase 4: 18 of 40

| Category | Calls | Notes |
|----------|-------|-------|
| HTF FVG Detection (existing) | 16 | Two HTF timeframes, 8 data points each |
| PD Zone HTF Swings (Phase 4) | 2 | Single PD timeframe |
| **Used** | **18** | |
| **Remaining** | **22** | For future phases |

### Why Sessions Need Zero request.security() Calls

Session tracking uses `time()` with session strings (e.g., `"0000-0800"`) to detect which session a bar belongs to. This operates on the chart's native timeframe data -- no cross-timeframe request needed. Session highs/lows are tracked by comparing current bar's high/low against running session max/min. This is a major architectural advantage: sessions are "free" from the security budget.

### Optimization Opportunity (Existing Code)

The current 16 calls could potentially be reduced to 12 by bundling HTF OHLC into tuple requests:

```pinescript
// BEFORE: 6 separate calls for HTF 1
htf_high = request.security(..., high, ...)
htf_low = request.security(..., low, ...)
htf_close = request.security(..., close, ...)
htf_high_2 = request.security(..., high[2], ...)
htf_low_2 = request.security(..., low[2], ...)
htf_bar_idx = request.security(..., bar_index, ...)

// AFTER: 2 bundled calls for HTF 1
[htf_high, htf_low, htf_close] = request.security(..., [high, low, close], ...)
[htf_high_2, htf_low_2, htf_bar_idx] = request.security(..., [high[2], low[2], bar_index], ...)
```

This would reclaim 8 calls (4 per HTF), bringing the budget from 18 to 10 of 40. However, this is an optimization, not a Phase 4 requirement. Note: tuple bundling in `request.security()` is supported in Pine Script v6 and is the recommended pattern per TradingView documentation.

### Future Budget Forecast

| Phase | Feature | Estimated Calls | Cumulative |
|-------|---------|-----------------|------------|
| Current (1-3) | HTF FVG detection | 16 | 16 |
| Phase 4 | PD zones | +2 | 18 |
| Phase 4 | Sessions | +0 | 18 |
| Phase 4 | Dashboard/Alerts | +0 | 18 |
| Future | SMT divergence | +4-8 | 22-26 |
| Future | Additional HTF layers | +2-6 | 24-32 |
| **Safety margin** | | | **8-16 remaining** |

## Architectural Patterns

### Pattern 1: Section-Based Monolith Organization

**What:** All code in a single file, organized into numbered sections (1-12) with `// ═══════` banner separators. Each section has a clear responsibility boundary.

**When to use:** Always in Pine Script -- there is no module system. This is the only organizational pattern available.

**Why it works here:** The section numbering creates a mental model of the pipeline. New features slot in at predictable locations (detection after S6, rendering before S11, orchestration in S12).

**Phase 4 implication:** Add new sections S5C (PD zones) and S6B (sessions) between existing detection sections. Place alert logic after S12 as S12B. Do NOT insert new sections that break the existing numbering -- use sub-numbering (5C, 6B, 12B).

### Pattern 2: Pipeline-with-State Architecture

**What:** Each bar executes a fixed pipeline of steps. Steps read/write shared state (global `var` arrays). The pipeline ordering guarantees that downstream steps see upstream results from the current bar.

**When to use:** This is the standard Pine Script execution model. Every indicator uses this pattern implicitly.

**Trade-offs:**
- Pro: Simple mental model, easy to reason about data flow
- Pro: No callback/event system needed -- just sequential function calls
- Con: Adding new pipeline steps requires careful ordering analysis
- Con: Shared mutable state means any function can corrupt data for downstream steps

**Phase 4 implication:** PD zone calculation MUST be inserted early in the pipeline (after swing detection, before inversions). Session tracking is order-independent and can go anywhere before rendering.

### Pattern 3: Global-Scope Alert Pattern

**What:** `alertcondition()` calls must be at the global scope (column zero, outside all `if` blocks). `alert()` can be inside conditionals but is best placed after the main pipeline completes.

**When to use:** For any Pine Script indicator that needs alerts.

**Trade-offs:**
- `alertcondition()`: Static messages (const string), but users can select which condition to alert on in the UI. Each call costs 1 plot count (64 max). Must be global scope.
- `alert()`: Dynamic messages (series string), can be inside `if` blocks, programmer controls frequency. Better for contextual alerts ("A+ Bullish IFVG at 5598.50").

**Phase 4 approach:** Use `alert()` for IFVG entry alerts (need dynamic grade/price in message). Use `alertcondition()` for simple boolean triggers (new IFVG detected, BE taken, mitigation). Pre-calculate all boolean conditions at global scope, then pass to `alertcondition()`.

```pinescript
// Global scope -- track state changes for alerts
var bool prev_had_new_ifvg = false
bool new_ifvg_detected = array.size(g_ifvg_array) > prev_ifvg_count
bool be_taken_this_bar = ... // computed in update_be_status()
bool ifvg_mitigated_this_bar = ... // computed in check_mitigations()

// alertcondition at global scope
alertcondition(new_ifvg_detected, "New IFVG", "New IFVG detected")
alertcondition(be_taken_this_bar, "BE Taken", "Break-even level reached")
alertcondition(ifvg_mitigated_this_bar, "IFVG Mitigated", "IFVG zone mitigated")

// alert() with dynamic message inside main loop
if new_ifvg_detected and barstate.isconfirmed
    IFVG latest = array.last(g_ifvg_array)
    alert(latest.grade + " " + (latest.is_bullish ? "Bullish" : "Bearish") +
          " IFVG @ " + str.tostring(latest.mid, format.mintick),
          alert.freq_once_per_bar)
```

### Pattern 4: Session Tracking via time() Without request.security()

**What:** Define sessions as time strings (e.g., `"1800-0300"` for Asia in NY time). Use `time(timeframe.period, session_string)` to check if the current bar falls within a session. Track running high/low with `math.max()`/`math.min()` during the session. Reset on session boundary.

**When to use:** For any session-based feature. This pattern costs zero `request.security()` calls.

**Trade-offs:**
- Pro: Zero security budget cost
- Pro: Works on any timeframe (auto-adjusts)
- Con: Session detection fails on daily+ timeframes (bars span multiple sessions)
- Con: Must handle timezone complexity (user should configure timezone)

**Implementation pattern:**

```pinescript
// Session time strings (configurable via input)
i_asia_session = input.session("1800-0300", "Asian Session", group=GROUP_SESSIONS)
i_london_session = input.session("0300-0930", "London Session", group=GROUP_SESSIONS)
i_ny_session = input.session("0930-1600", "NY Session", group=GROUP_SESSIONS)
i_session_tz = input.string("America/New_York", "Session Timezone", group=GROUP_SESSIONS)

// Detection -- no request.security needed
bool in_asia = not na(time(timeframe.period, i_asia_session, i_session_tz))
bool in_london = not na(time(timeframe.period, i_london_session, i_session_tz))
bool in_ny = not na(time(timeframe.period, i_ny_session, i_session_tz))

// Track session highs/lows
var float asia_high = na
var float asia_low = na
bool asia_started = in_asia and not in_asia[1]
if asia_started
    asia_high := high
    asia_low := low
else if in_asia
    asia_high := math.max(asia_high, high)
    asia_low := math.min(asia_low, low)
```

### Pattern 5: Dashboard Expansion via Row Count Increment

**What:** The dashboard is a `table.new()` with fixed row/column count. Expanding it means increasing the row count parameter and adding `table.cell()` calls for new rows.

**When to use:** Any time new data needs to appear in the dashboard.

**Trade-offs:**
- Pro: Simple, additive pattern
- Con: Each added row costs table cell budget (shared across all tables in the script)
- Con: Large tables can become visually cluttered

**Phase 4 approach:** Expand from 10 to 14-16 rows:

| Row | Content | Source |
|-----|---------|--------|
| 0 | Title (IFVG PRO v4.0) | Static |
| 1 | Active FVGs count | `g_fvg_array` |
| 2 | Active IFVGs count | `g_ifvg_array` |
| 3 | Liquidity levels count | `g_liquidity_array` |
| 4 | Divider | Static |
| 5 | Latest Setup grade | `find_most_recent_ifvg()` |
| 6 | Entry status | Latest IFVG |
| 7 | DOL target | Latest IFVG |
| 8 | HTF Bias | HTF IFVG arrays |
| 9 | HTF timeframes | Input settings |
| 10 | **Divider** | **NEW** |
| 11 | **PD Zone** | **NEW -- g_pd_current_zone** |
| 12 | **Range %** | **NEW -- g_pd_current_percent** |
| 13 | **Session** | **NEW -- current active session** |
| 14 | **Session H/L** | **NEW -- active session high/low** |
| 15 | **Alert Status** | **NEW -- last alert fired (optional)** |

**Performance note:** Tables should only update on `barstate.islast`. The current code already does this correctly. The additional rows (5-6) add negligible overhead since table operations only run once on the final bar.

## Anti-Patterns to Avoid

### Anti-Pattern 1: Placing alertcondition() Inside the Main If Block

**What people do:** Put `alertcondition()` inside the `if i_show_indicator` block or inside `if barstate.isconfirmed`.

**Why it's wrong:** Pine Script requires `alertcondition()` at global scope (column zero). It will produce a compilation error if placed in any local scope.

**Do this instead:** Calculate all alert boolean conditions inside the main loop, store results in global `var` variables, then call `alertcondition()` at the file's global scope after Section 12. Use `alert()` for dynamic messages inside conditionals.

### Anti-Pattern 2: Using request.security() for Session Detection

**What people do:** Create a separate security call to get session data from a different timeframe.

**Why it's wrong:** Wastes security budget (2-4 calls) for data that's already available on the current timeframe. Session boundaries are time-based, not price-based.

**Do this instead:** Use `time(timeframe.period, session_string, timezone)` which checks if the current bar's time falls within the session. This is free -- zero security calls.

### Anti-Pattern 3: Recalculating PD Zone on Every Bar Without Change Detection

**What people do:** Run the full PD zone calculation (HTF swing detection, equilibrium, percentage) on every bar even when the HTF data hasn't changed.

**Why it's wrong:** Wastes computation. HTF swings change infrequently (daily swings only shift once per day on a 5m chart).

**Do this instead:** Track previous HTF swing values and only recalculate when they change:

```pinescript
var float prev_pd_high = na
var float prev_pd_low = na
if pd_htf_swing_high != prev_pd_high or pd_htf_swing_low != prev_pd_low
    // Recalculate zones
    prev_pd_high := pd_htf_swing_high
    prev_pd_low := pd_htf_swing_low
```

### Anti-Pattern 4: Storing Session Data in Arrays When Scalars Suffice

**What people do:** Create `array<SessionData>` to track sessions, mimicking the FVG/IFVG array pattern.

**Why it's wrong:** Sessions are fixed (3 known sessions) with simple scalar data (high, low, is_active). Arrays add unnecessary complexity and memory overhead.

**Do this instead:** Use `var float` scalars for each session's high/low. There are only 3 sessions x 2 values = 6 variables. This is cleaner and faster than array operations.

### Anti-Pattern 5: Making Dashboard Table Wider Instead of Taller

**What people do:** Add columns to show more data side-by-side.

**Why it's wrong:** Pine Script tables with 2 columns and many rows render well. Adding columns makes the table visually wider, harder to read, and wastes horizontal space on the chart. The current 2-column (label + value) layout is optimal.

**Do this instead:** Keep the 2-column format. Add divider rows to create visual sections. Group related data (PD zone section, session section).

## Integration Points

### Internal Boundaries

| Boundary | Communication | Direction | Notes |
|----------|---------------|-----------|-------|
| PD Detection -> Grading | `get_pd_zone_modifier()` function call | PD -> S7 | Returns int (+1, -1, 0). Called inside `check_inversions()` |
| PD Detection -> IFVG Type | `pd_zone` field assignment | PD -> S1 | Stored at inversion time for historical record |
| PD Detection -> Dashboard | Global scalar reads | PD -> S11 | `g_pd_current_zone`, `g_pd_current_percent` |
| PD Detection -> Rendering | Global scalar reads | PD -> S10 | `g_pd_swing_high/low`, `g_pd_equilibrium` |
| Session Tracking -> Dashboard | Global scalar reads | Sessions -> S11 | `g_session_*_high/low`, `g_session_current` |
| Session Tracking -> Rendering | Global scalar reads | Sessions -> S10 | Session H/L for line drawing |
| Main Loop -> Alerts | Global boolean variables | S12 -> S12B | `new_ifvg_detected`, `be_taken`, `ifvg_mitigated` |
| Inversion -> Alerts | IFVG creation event | S8 -> S12B | Alert fires when new IFVG pushed to array |

### Alert System Integration Detail

The alert system is architecturally unique because `alertcondition()` must execute at global scope. This means the detection pipeline (inside `if i_show_indicator`) must communicate results to the global scope via state variables.

**Communication pattern:**

```
INSIDE main loop (local scope):
  var int prev_ifvg_count = 0
  int current_ifvg_count = array.size(g_ifvg_array)
  bool _new_ifvg = current_ifvg_count > prev_ifvg_count
  prev_ifvg_count := current_ifvg_count

  --> Store in global var: g_alert_new_ifvg := _new_ifvg

OUTSIDE main loop (global scope):
  alertcondition(g_alert_new_ifvg, ...)
```

**Alternative (simpler):** Use only `alert()` inside the main loop's conditional blocks. This avoids the global-scope dance entirely. The trade-off is that users cannot select individual alert conditions in TradingView's UI -- they get one "Any alert() call" trigger.

**Recommendation:** Use both. `alertcondition()` for the 3-4 key triggers (users can subscribe to specific ones). `alert()` with dynamic messages for the richest alert content.

## Suggested Build Order

Build order matters because of data dependencies between Phase 4 features.

### Build Order Recommendation

```
                DEPENDENCY GRAPH
                ─────────────────

  [1] Bug Fixes (fvg_singular, HTF bias duplication)
       │
       │  (no dependency, but clean foundation needed)
       │
       v
  [2] PD Zone Detection + Grading Integration
       │
       │  (PD zones modify grades, must exist before alerts reference grades)
       │
       v
  [3] PD Zone Visualization + Dashboard Rows
       │
       │  (rendering is independent of sessions, can ship separately)
       │
       v
  [4] Session Tracking + Visualization
       │
       │  (fully independent of PD zones, but dashboard expansion
       │   is easier to do after PD rows are in place)
       │
       v
  [5] Alert System
       │
       │  (depends on EVERYTHING -- needs PD zone data, session data,
       │   IFVG state, all detection pipeline complete)
       │
       v
  [6] Performance Optimization + Edge Case Hardening
```

**Why this order:**

1. **Bug fixes first** because the hardcoded `fvg_singular = true` inflates ALL grades. Every IFVG created after this fix will have more accurate grades. Building PD zones on top of broken grades means re-testing everything.

2. **PD zones before sessions** because PD zones directly modify the grading algorithm (the core value proposition). Sessions are visualization/awareness features that don't affect trading decisions as directly.

3. **Visualization after detection** for each feature because you can validate detection logic independently (via dashboard display or logs) before committing to the visual rendering code.

4. **Alerts last** because alerts consume ALL data from the pipeline. Every alert message references grade, direction, price, PD zone, and potentially session context. Building alerts before the data sources exist means re-writing alert messages.

5. **Optimization last** because premature optimization would constrain the feature implementation. The `request.security()` tuple bundling optimization is valuable but not blocking.

## Drawing Object Budget

The indicator has hard limits on drawing objects (set in `indicator()` declaration):

| Object Type | Max Count | Current Estimated Usage | Phase 4 Additions |
|-------------|-----------|-------------------------|-------------------|
| Boxes | 500 | ~200 (FVGs + IFVGs + HTF + delivery) | +0 (PD zones use lines, not boxes) |
| Lines | 500 | ~150 (BE, SL, entry, liquidity) | +3 PD zone lines + 6 session H/L lines = +9 |
| Labels | 500 | ~100 (grade labels, liquidity labels) | +3 PD zone labels + 6 session labels = +9 |
| Linefills | N/A | 0 | +2 (premium/discount zone fills, optional) |

Drawing budget is not a concern for Phase 4. The PD zone and session additions are constant (not proportional to data) -- always exactly 3 PD lines and up to 6 session lines regardless of how many bars are on the chart.

## Plot Count Budget

Pine Script allows a maximum of 64 plot counts per script. Each `alertcondition()` call costs 1 plot count. Each `plot()`, `plotshape()`, `plotchar()`, `plotarrow()`, `plotcandle()`, `plotbar()` also costs plot counts.

| Usage | Count | Notes |
|-------|-------|-------|
| Current plots | ~0-2 | Indicator uses overlay boxes/lines, minimal plots |
| Phase 4 alertcondition() calls | 3-5 | New IFVG, BE taken, mitigation, grade filter, session break |
| **Estimated total** | **3-7** | Well within 64 limit |

This is not a binding constraint for Phase 4.

## Sources

- [TradingView Pine Script Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) -- Official limits documentation (request.security, drawing objects, plot counts)
- [TradingView Concepts: Alerts](https://www.tradingview.com/pine-script-docs/concepts/alerts/) -- alert() vs alertcondition() behavior, global scope requirement
- [TradingView Concepts: Sessions](https://www.tradingview.com/pine-script-docs/concepts/sessions/) -- Session detection via time(), session string format
- [TradingView Concepts: Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) -- request.security() call counting, tuple bundling
- [Pine Script v6 Dynamic Requests](https://blog.traderspost.io/article/pine-script-v6-dynamic-requests) -- Dynamic request optimization techniques
- [TradingView Visuals: Tables](https://www.tradingview.com/pine-script-docs/visuals/tables/) -- Table limits, cell update efficiency, barstate.islast pattern
- [TradingView Profiling and Optimization](https://www.tradingview.com/pine-script-docs/writing/profiling-and-optimization/) -- Performance best practices
- [Pineify: alertcondition() Guide](https://pineify.app/resources/blog/pine-script-alertcondition-complete-guide-to-creating-custom-tradingview-alerts) -- alertcondition() patterns and limitations
- Existing codebase analysis: `src/IFVG_Indicator.pine` (2,511 lines), `PHASE4_PD_ZONES_PLAN.md`

---
*Architecture research for: IFVG Pro Phase 4 integration*
*Researched: 2026-03-23*
