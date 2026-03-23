# Pitfalls Research

**Domain:** TradingView Pine Script v6 Indicator -- Adding PD Zones, Sessions, Dashboard, Alerts to IFVG Pro
**Researched:** 2026-03-23
**Confidence:** HIGH (verified against official TradingView Pine Script documentation)

## Critical Pitfalls

### Pitfall 1: request.security() Budget Exhaustion Prevents Compilation

**What goes wrong:**
The indicator currently uses 14 `request.security()` calls (7 per HTF timeframe). TradingView enforces a hard limit of 40 calls (64 on Ultimate plan). The PHASE4 plan adds 2 calls for PD zone HTF swings (total: 16). Session tracking for Asian, London, and NY highs/lows could naively consume 6+ additional calls if each session's high/low is fetched separately. Adding future features (SMT divergence requires correlated symbol data, additional timeframes) rapidly closes the remaining budget. Once the limit is hit, the indicator will not compile at all -- there is no graceful degradation.

**Why it happens:**
Each `request.security()` call with a different expression or timeframe argument counts as unique. Developers add calls incrementally without tracking the running total, and the error only surfaces at compile time when the threshold is crossed.

**How to avoid:**
1. **Consolidate existing HTF calls using tuples.** The current 7 calls per HTF timeframe can be collapsed into 2 calls using tuple syntax:
   ```pinescript
   [h, l, c, h2, l2, bi, atr_val] = request.security(syminfo.tickerid, i_htf_timeframe,
       [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
       lookahead=barmerge.lookahead_off)
   ```
   This reduces 14 calls to 4 (2 per HTF), freeing 10 slots immediately.
2. **Do NOT use request.security() for session tracking.** Session highs/lows can be computed entirely on the current timeframe using `time()` with session strings and tracking `high`/`low` within those windows. Zero additional security calls needed.
3. **PD zone pivot detection should also run on LTF first**, then pass the computed expression into a single `request.security()` call per PD timeframe.
4. **Maintain a budget ledger** as a comment block at the top of Section 5B listing every call, its purpose, and the running total.
5. **All combined request.\*() tuple elements must stay under 127 total.** With 7 elements per tuple and 4-6 calls, this is well within limits.

**Warning signs:**
- TradingView compiler error: "Script requests too many securities"
- Adding a new feature and having to remove an existing one to stay under budget
- The budget ledger showing >30 calls consumed

**Phase to address:**
Phase 4 (first task). Consolidate existing calls BEFORE adding new ones. This is a prerequisite that unlocks headroom for sessions, PD zones, and future features.

---

### Pitfall 2: ta.pivothigh/ta.pivotlow Delayed Confirmation Creates Stale PD Zone Boundaries

**What goes wrong:**
`ta.pivothigh(high, N, N)` confirms a swing high only after N bars have passed to the right. With the plan's default `i_pd_swing_lookback = 5`, the swing is confirmed 5 bars late. When wrapped in `request.security()` requesting a Daily timeframe while charting on 15m, the delay compounds: the HTF pivot is confirmed 5 Daily bars late (5 trading days), and then `ta.valuewhen()` retrieves that value. During those 5 days, the PD zone uses the *previous* confirmed swing -- potentially one from weeks ago. A new market structure shift (e.g., a lower high forms) won't update the zone for 5 more daily bars.

Additionally, `ta.pivothigh()` returns `na` for all bars except the exact confirmation bar. If `ta.valuewhen()` is used with `not na(pivot)` as the condition, it works correctly by persisting the last confirmed value. However, if a developer mistakenly checks `pivot` directly without `ta.valuewhen()`, the zone will flicker to `na` on every non-pivot bar.

**Why it happens:**
Pivot functions are retrospective by design -- they need right-side bars to confirm that the high/low was indeed a local extremum. This is correct behavior but creates a UX problem where the dealing range lags significantly behind price action.

**How to avoid:**
1. The PHASE4 plan correctly uses `ta.valuewhen(not na(pivot), pivot, 0)` to persist the last confirmed value -- keep this pattern.
2. Consider using a smaller `rightbars` value (3 instead of 5) for faster confirmation, accepting slightly less reliable pivots.
3. Add a dashboard indicator showing "Swing Age" (bars since last confirmation) so users understand when the zone is potentially stale.
4. Document in the tooltip that PD zones update with a delay equal to the swing lookback period.
5. Guard against `na` propagation: always check `not na(g_pd_swing_high) and not na(g_pd_swing_low)` before computing equilibrium (the plan already does this).

**Warning signs:**
- PD zone lines never update despite obvious new swing highs/lows on chart
- Zone percentage showing values far outside 0-100% (price has moved well beyond the stale dealing range)
- Users reporting "PD zone is wrong" when it is actually correctly delayed

**Phase to address:**
Phase 4, PD zones implementation. The `ta.valuewhen()` pattern in the existing plan is correct; ensure it is not modified during implementation.

---

### Pitfall 3: Grade Inflation Cascade from Adding PD Zone Modifier to Already-Inflated Scores

**What goes wrong:**
The grading system currently has a known bug: `fvg_singular = true` is hardcoded at line 1595, giving every IFVG an unearned +1 quality score. The current quality score range is -2 to +3. Adding a PD zone modifier (+1/-1) expands this to -3 to +4. With the existing `fvg_singular` bug, the effective range becomes -2 to +4 because the -1 from `fvg_singular = false` never fires.

For Tier A setups: A+ requires `quality_score >= 2`. With `fvg_singular` always +1, a long in discount (PD +1) with neutral momentum (0) already hits 2 and gets A+. Before the PD zone addition, this same setup would have been A (score = 1). The compounding effect means nearly every setup in the right zone with any sweep/delivery gets A+, making the grade meaningless as a discriminator.

**Why it happens:**
Quality modifiers are additive. Each new modifier widens the score range. When an existing modifier is broken (stuck at +1), adding a new one amplifies the distortion rather than just adding noise.

**How to avoid:**
1. **Fix the `fvg_singular = true` bug BEFORE adding the PD zone modifier.** This is the single most important prerequisite. At minimum, implement a basic "series of gaps" detection that checks if another FVG exists within 3 bars of the current one.
2. **Re-calibrate the quality score thresholds** after adding the PD zone modifier. With a range of -3 to +4, the thresholds for A+ (currently >= 2) may need to increase to >= 3.
3. **Add a grade distribution sanity check:** after implementation, visually scan 100+ IFVGs across multiple markets. If more than 30% are A+, thresholds are too loose.
4. **Consider capping the total quality score** at a maximum (e.g., +3) to prevent unlimited inflation from future modifiers.

**Warning signs:**
- Most setups grading A+ or A regardless of market conditions
- No C or B- grades appearing in practice
- Grade distribution skewed heavily toward the high end
- Users reporting that "everything looks like an A+ setup"

**Phase to address:**
Phase 4, but the `fvg_singular` fix MUST be completed in a preceding bugfix step before PD zone grading integration. If shipped together with the bug unfixed, the grading system loses credibility.

---

### Pitfall 4: Drawing Object Budget Pressure Causes Silent Object Loss

**What goes wrong:**
TradingView enforces hard limits: 500 boxes, 500 lines, 500 labels. When the limit is exceeded, the oldest drawing objects are silently deleted (FIFO). The current indicator already consumes up to 7 drawing objects per IFVG (box, label, BE line, SL line, entry line, entry label, delivery box), plus 2 per FVG, 2 per liquidity level, and 2 per HTF FVG/IFVG. With `i_max_ifvgs=30`, IFVGs alone can consume 210 objects.

Phase 4 adds: PD zone lines (3) + PD labels (3) + linefills (2) = 8 persistent objects. Session tracking adds up to 6 lines + 6 labels = 12 persistent objects per day. Dashboard expansion adds table cells but tables have their own ID space. The real danger is that PD zone and session objects are **persistent** (always visible) while IFVGs are **transient** (created and removed). If the persistent objects plus the maximum transient count exceeds 500 in any category, the oldest transient objects (potentially still-valid IFVGs or liquidity levels) get silently deleted.

Specific risk: The line budget is tightest. Each IFVG uses 3 lines (BE, SL, entry). 30 IFVGs = 90 lines. Each liquidity level = 1 line. 50 liquidity levels = 50 lines. HTF FVGs/IFVGs are rendered as boxes, not lines. PD zones = 3 lines. Sessions = 6 lines. Total: 90 + 50 + 3 + 6 = 149 lines. This is within 500 but will grow if display limits are increased.

**Why it happens:**
Each feature is developed in isolation and tested with moderate data. The budget is only exhausted when all features are enabled simultaneously on a volatile instrument with many active zones. The delete-and-recreate pattern (identified in CONCERNS.md) also wastes IDs -- deleted IDs are still counted against the 500 limit per execution cycle.

**How to avoid:**
1. **Track drawing object consumption in the dashboard.** Add a debug row showing `boxes: X/500, lines: X/500, labels: X/500` (can be toggled off for production).
2. **Reduce `i_max_ifvgs` default from 30 to 15.** 30 simultaneous IFVGs is excessive for most trading scenarios and the visual display limit (`i_max_recent_display=5`) already restricts what users see.
3. **Use `line.set_*()` and `box.set_*()` to update existing objects** instead of delete-and-recreate. This is especially important for PD zone and session lines that persist across bars.
4. **PD zone and session objects should use `var` declarations** so they are created once and updated in place, not recreated every bar.
5. **Add a linefill gotcha guard:** linefills are tied to their parent lines. Deleting a line automatically deletes its linefill. If PD zone lines are deleted and recreated, the linefill must also be recreated. Use `var` for both.

**Warning signs:**
- Liquidity lines or IFVG boxes disappearing from the chart unexpectedly
- Oldest zones vanishing when new ones form (even within display limits)
- Rendering flicker on each bar close (delete-and-recreate visible to user)

**Phase to address:**
Phase 4 (rendering step). Adopt the update-in-place pattern for ALL new drawing objects. Retrofitting existing rendering to update-in-place is ideal but can be deferred if scope is a concern.

---

### Pitfall 5: alertcondition() Global Scope Restriction Breaks Conditional Alert Logic

**What goes wrong:**
`alertcondition()` calls cannot be placed inside `if` blocks, loops, or any local scope -- they must be at column zero in the global scope. This means you cannot write:
```pinescript
if new_ifvg_formed and grade >= "B"
    alertcondition(true, "IFVG Entry", "...")  // COMPILE ERROR
```
Instead, the condition must be a series bool computed globally, and the `alertcondition()` must be at the top level. Each `alertcondition()` also counts toward the 64-plot limit (same pool as `plot()` calls), though the indicator currently uses few plots so this is unlikely to be a constraint.

The alternative `alert()` function CAN be placed in conditional blocks and accepts dynamic "series string" messages (e.g., including the grade, price, and direction). However, `alert()` does not appear in the "Create Alert" dialog dropdown -- users must select "Any alert() function call" as the condition, which is less discoverable.

**Why it happens:**
Pine Script's `alertcondition()` was designed before `alert()` existed and has stricter constraints. Developers coming from other languages expect conditional alert registration, but Pine Script requires pre-computed boolean conditions at global scope.

**How to avoid:**
1. **Use `alert()` for dynamic, grade-filtered alerts** (entry signals, invalidation, mitigation). These benefit from dynamic messages:
   ```pinescript
   if new_ifvg and grade_value >= min_grade_value
       alert("IFVG " + grade + " " + direction + " @ " + str.tostring(close), alert.freq_once_per_bar_close)
   ```
2. **Use `alertcondition()` for simple, always-on conditions** that users toggle in the dialog (e.g., "Any new IFVG detected", "Any BE taken"). Pre-compute the boolean at global scope:
   ```pinescript
   bool any_new_ifvg = false  // set to true inside check_inversions
   alertcondition(any_new_ifvg, "New IFVG", "New IFVG detected")
   ```
3. **Combine both approaches:** `alertcondition()` for discoverability in the UI, `alert()` for rich contextual messages.
4. **Be aware that alerts only fire on realtime bars.** The indicator's `barstate.isconfirmed` guard is correct for this -- alerts based on confirmed bar values will fire once per bar close on the realtime bar.

**Warning signs:**
- Compile error: "Cannot call 'alertcondition' in a local scope"
- Users reporting alerts never fire (forgot to create alert in UI, or condition is always false on realtime bars)
- Alert messages showing placeholder text instead of dynamic values (used `alertcondition()` where `alert()` was needed)

**Phase to address:**
Phase 4, alerts implementation. Design the alert architecture (which conditions use `alert()` vs `alertcondition()`) before writing code.

---

### Pitfall 6: Session Time Definitions Break Across Timezones and DST Transitions

**What goes wrong:**
Session tracking for Asian, London, and NY sessions requires precise time window definitions. If sessions are defined using fixed UTC offsets (e.g., "UTC-5" for NY), the session boundaries will be wrong for 6 months of the year when DST is in effect. For example, NY open is 09:30 ET, which is 14:30 UTC during EST but 13:30 UTC during EDT. A fixed UTC offset will be 1 hour off during the other half of the year.

Additional edge cases:
- **24-hour markets (crypto, futures):** Sessions wrap past midnight. The Asian session (20:00-00:00 ET) spans two calendar days.
- **Weekend gaps:** Forex opens Sunday evening ET, but `time()` with a session string that doesn't include Sunday (day 1) will miss the first hours.
- **Higher timeframe charts:** On 4H or Daily charts, a single bar can span an entire session or multiple sessions. Session high/low tracking becomes meaningless. The indicator should auto-disable session tracking above a threshold timeframe (e.g., > 1H).
- **Broker feed timezone mismatch:** The exchange timezone (`syminfo.timezone`) may differ from the session definition timezone. If sessions are defined in "America/New_York" but the chart is a crypto pair on Binance (UTC), the `time()` function needs an explicit timezone parameter.

**Why it happens:**
Session logic looks simple in prototyping (hardcode "0930-1600") but breaks in production across the full matrix of markets, timezones, and DST transitions. Most developers test on a single market/timezone combination.

**How to avoid:**
1. **Use IANA timezone names, never fixed UTC offsets.** Always pass `timezone="America/New_York"` to `time()`:
   ```pinescript
   bool in_ny_session = not na(time(timeframe.period, "0930-1600", "America/New_York"))
   ```
2. **Define sessions using the local time of the session's city:**
   - Asian: `"2000-0000"` in "America/New_York" (or `"0900-1500"` in "Asia/Tokyo")
   - London: `"0300-1200"` in "America/New_York" (or `"0800-1700"` in "Europe/London")
   - NY: `"0930-1600"` in "America/New_York"
3. **Auto-disable on higher timeframes.** Check `timeframe.in_seconds() > 3600` (> 1H) and skip session tracking entirely. Show "N/A" in the dashboard.
4. **Handle overnight sessions** correctly -- `time()` supports sessions that cross midnight.
5. **Test across DST boundaries.** March and November are critical dates. Load a chart that spans a DST transition and verify session lines shift correctly.
6. **Do NOT use request.security() for session data.** Track session highs/lows locally:
   ```pinescript
   var float session_high = na
   var float session_low = na
   if in_session
       session_high := na(session_high) ? high : math.max(session_high, high)
       session_low := na(session_low) ? low : math.min(session_low, low)
   ```
   This consumes zero security call budget.

**Warning signs:**
- Session lines appearing 1 hour offset from expected times
- Session ranges not resetting at the correct time
- Session tracking showing results on Daily chart (meaningless)
- Asian session range missing on crypto charts

**Phase to address:**
Phase 4, sessions implementation. Build with IANA timezones from the start -- retrofitting is painful.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcoding `fvg_singular = true` | Ship grading faster | All grades inflated by ~1 sub-grade; undermines core feature | Never -- must fix before adding more quality modifiers |
| Delete-and-recreate all drawings each bar | Simpler rendering logic | Wastes drawing IDs, causes flicker, O(n) per bar for all objects | MVP only; must migrate to update-in-place before adding PD zone + session drawings |
| Duplicated HTF bias calculation in two functions | Ship Phase 3 faster | Bug risk when updating one but not the other | Ship it, but fix in Phase 4's first bugfix pass |
| Individual `request.security()` calls instead of tuples | Easier to read/debug | Wastes 10+ security call budget slots | Never for production; consolidate in Phase 4 prerequisite |
| Magic number sentinels (999999) instead of `na` | Works for most instruments | Breaks on extreme-valued instruments; poor readability | Low priority but should clean up opportunistically |
| Not grading HTF IFVGs (grade = "HTF") | Avoids complexity of HTF grading pipeline | HTF IFVGs can't be quality-filtered; "HTF" string causes 0/gray in grade functions | Acceptable if HTF is bias-only; document explicitly |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Dashboard table rebuilt every bar | Slow indicator loading, especially on 1m charts with months of history | Use `var table` declaration, `table.cell()` updates only when values change (check with conditional) | >5,000 bars on chart; noticeable at >10,000 |
| `is_swing_intact()` doing O(n) lookback 4+ times per bar | Profiler showing >50% time in swing integrity checks | Cache `is_valid = false` on SwingPoint when broken; skip rechecking invalid swings | Lower timeframes (1m, 5m) with >500 active swings |
| All rendering functions iterate full arrays every bar | Linear scaling with array sizes; compounds with Phase 4 additions | Only re-render objects that changed; track dirty flags per object | When `i_max_ifvgs` + `i_max_fvgs` + liquidity count > 100 |
| PD zone linefill recreation every bar | Linefill + 2 parent lines deleted and recreated; visual flicker | Use `var` for PD zone lines and linefill; update with `line.set_*()` when values change | Immediately noticeable as flicker on every bar |
| `check_equal_highs/lows` nested O(n*m) loops | Computation timeout on volatile instruments with many swings | Cap inner loop iterations; break early on first match (already partially done) | >200 swing points and >50 liquidity levels active |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| PD zone modifier into grading | Adding modifier without recalibrating score thresholds | Re-evaluate A+/A/A- cutoffs for new score range (-3 to +4) |
| Session tracking into main loop | Inserting update call at wrong position; sessions computed after grading uses them | Insert `update_sessions()` early in main loop (after Step 1, before Step 4) |
| `alert()` inside `barstate.isconfirmed` block | Alert fires on confirmed bar close -- correct for this indicator | Ensure `alert.freq_once_per_bar_close` is used, not `alert.freq_all` which would still only fire once due to the `barstate.isconfirmed` gate |
| PD zone lines persisting across timeframe changes | Lines from 15m chart remain when switching to 4H | Use `var` declarations and clear/recreate on timeframe change detected via `timeframe.period` comparison |
| Adding `pd_zone` field to IFVG type | Forgetting to update HTF IFVG constructor (line 801-826) | Search for ALL `IFVG.new(` calls (currently 2 sites: LTF at 1602, HTF at 801) and update both |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| PD zone never updating (stale swing from weeks ago) | User thinks indicator is broken | Show "Swing Age: X bars" in dashboard; add tooltip explaining confirmation delay |
| Session lines cluttering chart on higher timeframes | Visual noise; lines meaningless on 4H/Daily | Auto-hide session elements when `timeframe.in_seconds() > 3600`; show "Sessions: N/A (TF too high)" in dashboard |
| Too many alert conditions in UI dropdown | User overwhelmed; creates wrong alert | Group alerts logically: "Entry Signals" (grade-filtered), "Status Changes" (BE taken, mitigation), "Zone Updates" (PD zone shift) |
| Grade changes after PD zone addition | Users accustomed to previous grades see different results | Add a "PD Zone Modifier" toggle (already in plan as `i_pd_grade_modifier`) defaulting to ON, with tooltip explaining the change |
| Alert() messages showing "[object Object]" or raw data | User gets unusable notification | Format all alert messages with human-readable text: "Bullish IFVG A+ @ 5,432.50 - Entry Valid - DOL: EQH @ 5,500" |
| Dashboard becoming too tall (12+ rows) | Covers price action on smaller screens | Add a "Compact Dashboard" toggle that shows only the most critical 5-6 rows |

## "Looks Done But Isn't" Checklist

- [ ] **PD Zones:** Swing high < swing low edge case -- verify `range > 0` guard prevents divide-by-zero and negative equilibrium
- [ ] **PD Zones:** Price outside dealing range (above swing high or below swing low) -- verify percentage can display >100% or <0% correctly, not clamped
- [ ] **PD Zones:** PD zone grading applied to HTF IFVGs -- verify HTF IFVGs (grade="HTF") skip PD modifier since they have no meaningful direction
- [ ] **Sessions:** DST transition test -- load chart spanning March/November DST change, verify session boundaries shift correctly
- [ ] **Sessions:** Weekend/overnight session for crypto -- verify Asian session (crosses midnight) renders correctly on 24/7 markets
- [ ] **Sessions:** Previous session highs/lows persist after session ends -- verify lines extend right and don't disappear
- [ ] **Alerts:** Alert fires on realtime bar only -- test by adding indicator to chart, creating alert, and waiting for next bar close
- [ ] **Alerts:** Alert persists after script update -- TradingView saves a snapshot; existing alerts won't pick up new alert conditions
- [ ] **Dashboard:** Table row count matches `table.new()` row parameter -- adding rows 10/11 requires expanding from 10 to 12 rows in constructor
- [ ] **Grading:** Run grade distribution check after PD modifier -- count A+/A/A-/B+/B/B-/C across 50+ setups on multiple markets
- [ ] **Drawing budget:** Enable ALL features simultaneously and check for missing drawings on a volatile 5m chart with 500+ bars

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Security call budget exhausted | MEDIUM | Consolidate existing calls into tuples; refactor to UDT-based requests if needed; can be done without changing functionality |
| Grade inflation from stacked modifiers | HIGH | Must recalibrate thresholds AND fix `fvg_singular` bug; existing grades on chart will change; users may need to re-evaluate setups |
| Drawing objects silently deleted | LOW | Reduce `i_max_ifvgs` default; add display budget tracking; switch to update-in-place rendering |
| Session times wrong due to DST | MEDIUM | Switch from UTC offsets to IANA timezone names; requires updating all `time()` calls and retesting |
| Alert conditions don't fire | LOW | Verify boolean computation at global scope; test with TradingView's alert creation dialog; add `plotchar()` debug overlay for alert conditions |
| PD zone showing stale data | LOW | Reduce pivot lookback from 5 to 3; add staleness indicator to dashboard; no architectural change needed |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Security call budget exhaustion | Phase 4 prerequisite (before any new features) | Count calls with `grep -c "request.security"` after consolidation; must be <20 |
| Stale PD zone boundaries | Phase 4, PD zones | Compare swing labels on HTF chart with PD zone lines on LTF; verify update timing |
| Grade inflation cascade | Phase 4, PD zones (bugfix `fvg_singular` first) | Grade distribution audit: no single grade should exceed 40% of all setups |
| Drawing object budget pressure | Phase 4, rendering | Enable all features on 5m chart with 500 bars; verify no unexpected drawing deletion |
| alertcondition() scope restriction | Phase 4, alerts | Compile test with all alert conditions; verify each appears in "Create Alert" dropdown |
| Session timezone/DST errors | Phase 4, sessions | Test on chart spanning DST transition date; verify with at least 2 different exchange timezones |
| IFVG type field addition breaks constructors | Phase 4, PD zones (when adding `pd_zone` field) | Search all `IFVG.new(` calls; both LTF and HTF constructors must include new field |
| Main loop ordering dependency | Phase 4, all features | `update_pd_zones()` must execute before `check_inversions()` calls `calculate_grade()` |
| Dashboard table row mismatch | Phase 4, dashboard expansion | `table.new()` row count parameter must equal or exceed highest row index + 1 |
| Delete-and-recreate rendering waste | Phase 4, PD zones + sessions (use `var` + setters for new objects) | Profile with Pine Profiler; rendering functions should not dominate execution time |

## Sources

- [TradingView Pine Script v6 Alerts Documentation](https://www.tradingview.com/pine-script-docs/concepts/alerts/)
- [TradingView Pine Script Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/)
- [TradingView Pine Script Repainting Concepts](https://www.tradingview.com/pine-script-docs/concepts/repainting/)
- [TradingView Pine Script Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/)
- [TradingView Pine Script Sessions](https://www.tradingview.com/pine-script-docs/concepts/sessions/)
- [TradingView Pine Script Time Concepts](https://www.tradingview.com/pine-script-docs/concepts/time/)
- [TradingView Pine Script Profiling and Optimization](https://www.tradingview.com/pine-script-docs/writing/profiling-and-optimization/)
- [TradingView Pine Script Tables](https://www.tradingview.com/pine-script-docs/visuals/tables/)
- [TradingView Pine Script Fills](https://www.tradingview.com/pine-script-docs/visuals/fills/)
- [PineCoders: How to Avoid Repainting with security()](https://www.tradingview.com/script/cyPWY96u-How-to-avoid-repainting-when-using-security-PineCoders-FAQ/)
- [How to Work With Pivots in Pine Script](https://marketscripters.com/how-to-work-with-pivots-in-pine-script/)
- [5 Causes of Slow Pine Scripts on TradingView](https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/)
- [Pine Script alertcondition() Complete Guide](https://pineify.app/resources/blog/pine-script-alertcondition-complete-guide-to-creating-custom-tradingview-alerts)
- Codebase analysis: `src/IFVG_Indicator.pine` (2,511 lines, 14 request.security() calls, 27-field IFVG type)
- `.planning/codebase/CONCERNS.md` (existing tech debt and performance bottleneck inventory)
- `PHASE4_PD_ZONES_PLAN.md` (implementation plan for PD zones feature)

---
*Pitfalls research for: TradingView Pine Script v6 IFVG Indicator -- Phase 4 PD Zones, Sessions, Dashboard, Alerts*
*Researched: 2026-03-23*
