# Project Research Summary

**Project:** IFVG Pro — Phase 4 (PD Zones, Sessions, Dashboard, Alerts)
**Domain:** TradingView Pine Script v6 overlay indicator — ICT/SMC trading methodology
**Researched:** 2026-03-23
**Confidence:** HIGH

## Executive Summary

IFVG Pro is a mature Pine Script v6 indicator at the end of Phase 3 with a well-established 2,511-line codebase organized around a sequential per-bar detection pipeline. Phase 4 extends this codebase with four features: premium/discount (PD) zone detection, trading session tracking, dashboard expansion, and an alert system. Unlike a greenfield project, Phase 4 is entirely additive — the architecture, types, rendering patterns, and data store patterns are all established. The primary decisions are about where in the pipeline each feature slots in, how to stay within Pine Script's resource limits, and what order to build in.

The recommended approach is to treat Phase 4 as two sequential sub-phases: first fix two known bugs and add PD zones (which directly modifies the grading algorithm — the indicator's core differentiator), then add sessions and alerts (which enhance context but do not change the grading model). This ordering matters because the `fvg_singular = true` hardcoded bug inflates all grades by +1; adding the PD zone quality modifier on top of that inflation makes grades meaningless. The bug fix must precede the feature addition. Sessions are architecturally independent and cost zero `request.security()` calls — a significant advantage that makes them cheap to add after PD zones are validated.

The main risks are resource budget exhaustion and grade inflation. The `request.security()` call count is currently 16 of 40; the single highest-impact action to address this is consolidating the existing 16 individual calls into 2 tuple calls (freeing 14 slots), which should be the first task of Phase 4. Grade integrity depends on fixing `fvg_singular` before adding the PD zone modifier and recalibrating thresholds afterward. Both risks have clear, well-understood mitigations.

## Key Findings

### Recommended Stack

Pine Script v6 is the only technology — this is not a stack selection problem. Phase 4 requires specific API choices: `time()` with IANA timezone strings for session detection (zero security budget cost), `ta.pivothigh/ta.pivotlow` plus `ta.valuewhen()` for PD zone swing detection, `linefill.new()` for zone visualization (not `fill()`, which only works with `plot()`/`hline()` outputs), and both `alertcondition()` at global scope and `alert()` inside conditionals for the alert system.

The most critical API constraint is the `request.security()` budget of 40 calls. The existing 16 individual calls should be collapsed into 2 tuple calls immediately, reducing budget usage from 40% to 5% and freeing 14 slots for Phase 4 and future phases. After consolidation, Phase 4 requires only 1 additional call (PD zone swings), bringing the total to 3 of 40.

**Core APIs for Phase 4:**
- `ta.pivothigh/ta.pivotlow` + `ta.valuewhen`: HTF swing detection for PD zone boundaries — the only built-in pivot mechanism, requires lookback confirmation delay
- `time(timeframe.period, session_string, "America/New_York")`: session detection — zero security budget, handles DST automatically via IANA timezone names
- `linefill.new(line1, line2, color)`: PD zone fill — required because `fill()` cannot fill between dynamically-positioned price levels
- `alertcondition()` at global scope + `alert()` in conditionals: combined approach gives both UI-selectable conditions and dynamic message content
- Tuple `request.security()`: `[a,b,c] = request.security(...)` — mandatory consolidation to free budget

**What NOT to use:**
- `request.security()` for session data — use `time()` with session strings instead
- `fill()` for PD zone backgrounds — use `linefill.new()`
- `alertcondition()` inside `if` blocks — Pine Script requires global scope; compile error otherwise
- `alert.freq_all` for trading signals — use `alert.freq_once_per_bar_close` to prevent repainting alerts

### Expected Features

No competitor indicator combines IFVG detection, setup grading, PD zone integration into grading, session tracking, and actionable alerts. The grading system is the core differentiator; every Phase 4 feature should feed into or enhance it.

**Must have (table stakes — users will consider indicator incomplete without these):**
- Premium/discount zones with equilibrium line — every ICT indicator provides this; using HTF swing-based dealing range (not simple daily high/low)
- PD zone grading integration — zone position must affect quality score (+1/-1 modifier)
- Session high/low tracking (Asia, London, NY) — ICT methodology treats these as liquidity targets
- Session visualization (horizontal lines with labels) — cleaner than boxes for this already-dense indicator
- Grade-filtered entry alert — core alert; traders need notification when a high-grade IFVG forms
- Alert for entry invalidation (BE taken) — traders need to know when a watched setup becomes invalid
- Dashboard showing PD zone and session context — existing 10-row table expands to 14-16 rows
- Bug fix: `fvg_singular = true` hardcode — prerequisite; without this all grades are unreliable
- Bug fix: duplicated HTF bias logic — quick cleanup to eliminate maintenance risk

**Should have (competitive differentiators):**
- Context-rich alert messages with grade, direction, entry price, SL, zone percentage, DOL target — no competitor provides this level of alert detail
- Multi-layer dashboard with PD zone %, active session, session H/L — one-glance decision tool
- OTE zone (62%-79%) within dealing range — optional fill for premium entry zone; off by default

**Defer to Phase 5+:**
- Session H/L as liquidity targets in grading — complex DOL integration, high value but deferred within milestone
- NY midnight open price line — low complexity but not essential for IFVG trading specifically
- PDH/PDL as liquidity — costs 2 additional security calls; defer until grading system is stable
- Webhook-compatible JSON alert format — Phase 5+ automation feature

**Anti-features (deliberately NOT building):**
- Killzone background boxes — creates visual noise on an already-dense overlay indicator
- Comprehensive Fibonacci levels within dealing range — clutter; show only equilibrium (50%) plus optional OTE (62%-79%)
- Auto-trading strategy mode — fundamentally changes indicator execution model; IFVG trading requires discretion
- Real-time (intra-bar) alerts — causes repainting; all alerts on `barstate.isconfirmed` only

### Architecture Approach

Phase 4 fits cleanly into the existing section-based monolith architecture. New sections S5C (PD zone detection) and S6B (session tracking) are inserted between existing detection sections. Alert logic becomes S12B at global scope after the main loop. The existing pipeline-with-state pattern extends naturally: PD zone calculation runs after step 1 (swing detection) and before step 5 (inversions), because the grading algorithm reads `g_pd_current_zone` at inversion time. Sessions are order-independent and can run early.

**Major components (existing, unchanged):**
1. FVG/IFVG Detection (S5/S8) — 3-candle LTF pattern detection and inversion logic
2. HTF Detection (S5B) — cross-timeframe FVG/IFVG overlay via `request.security()`
3. Swing/Liquidity (S6) — swing points, EQH/EQL, sweep detection

**New components (Phase 4):**
1. PD Zone Detection (S5C) — HTF swing detection, equilibrium, zone classification; writes to global scalars read by grading, rendering, and dashboard
2. Session Tracking (S6B) — Asia/London/NY session boundary detection, H/L tracking; uses `time()` with no security cost
3. PD Zone Rendering — 3 lines + 2 linefills; use `var` declarations and `line.set_*()` for update-in-place
4. Session Rendering — 6 horizontal rays with labels; also update-in-place
5. Alert System (S12B) — `alertcondition()` at global scope using pre-computed boolean state; `alert()` with dynamic messages inside conditionals

**Modified components (Phase 4):**
- `calculate_grade()` (S7) — gains 6th parameter `pd_zone_modifier`
- `check_inversions()` (S8) — calls `get_pd_zone_modifier()` before grading, stores `pd_zone` on IFVG
- Dashboard (S11) — expands from 10 to 14-16 rows; both PD and session sections added
- IFVG type (S1) — gains `pd_zone` string field; requires updating ALL `IFVG.new()` call sites (2 sites: line 1602 for LTF, line 801 for HTF)

**Critical ordering constraint:** `update_pd_zones()` must execute before `check_inversions()`. PD zone data is captured at inversion time and stored on the IFVG — it cannot be back-filled.

### Critical Pitfalls

1. **`request.security()` budget exhaustion** — Hard limit of 40 calls. Current code uses 16 individual calls that can be consolidated into 2 tuple calls, freeing 14 slots. Do this consolidation as the first task of Phase 4 before adding any new calls. Maintain a call budget ledger comment block in Section 5B.

2. **Grade inflation cascade from stacking modifiers on broken grading** — The hardcoded `fvg_singular = true` at line ~1595 gives every IFVG an unearned +1 quality score. Adding PD zone modifier (+1/-1) on top of this inflated baseline means nearly every setup in the right zone gets A+, destroying the grade discriminator. Fix `fvg_singular` first, re-validate grade distribution (no single grade should exceed 40% of setups), then add the PD zone modifier and recalibrate thresholds for the new -3 to +4 range.

3. **`alertcondition()` global scope restriction** — `alertcondition()` cannot be inside any `if` block; it must be at column zero. Compute alert boolean conditions inside the main loop, store in `var` globals, then call `alertcondition()` at file level after Section 12. Use `alert()` (which can be in conditionals) for rich dynamic messages with grade, price, direction, and zone context.

4. **PD zone pivot confirmation delay** — `ta.pivothigh/ta.pivotlow` requires `rightbars` to confirm; with default lookback 5, the zone lags by 5 HTF bars (5 trading days on a Daily PD timeframe). Use `ta.valuewhen(not na(pivot), pivot, 0)` to persist the last confirmed value (already in the plan). Add "Swing Age: X bars" to the dashboard so users understand when the zone may be stale. Consider reducing lookback to 3 for faster confirmation.

5. **Session timezone/DST errors** — Never use fixed UTC offsets for session boundaries; they break for 6 months per year when DST is in effect. Always pass `timezone="America/New_York"` to `time()` (IANA notation handles DST automatically). Auto-disable session tracking when `timeframe.in_seconds() > 3600` — on Daily+ charts, sessions are meaningless.

## Implications for Roadmap

Based on combined research, Phase 4 should be structured as two sub-phases with a prerequisite bugfix step:

### Phase 4.0: Bug Fixes and `request.security()` Consolidation
**Rationale:** These are blocking prerequisites. Grade inflation from `fvg_singular` makes it impossible to validate PD zone grading. Security call debt means Phase 4 additions could push the indicator to 18+ of 40 calls without headroom for the future. Fix both before writing new feature code.
**Delivers:** Accurate grading system, 37 of 40 security call slots available
**Addresses:** `fvg_singular = true` hardcode (line ~1595), duplicated HTF bias logic (extract to shared `get_htf_bias()` function), 16 individual security calls consolidated to 2 tuple calls
**Avoids:** Grade inflation cascade (Pitfall 3), security budget exhaustion (Pitfall 1)
**Research flag:** Standard patterns — no additional research needed

### Phase 4.1: PD Zone Detection and Grading Integration
**Rationale:** PD zones directly modify the grading algorithm — this is the core Phase 4 value proposition. Must precede sessions and alerts, which reference zone data in their output. Must follow the bugfix phase so grades are accurate before adding another modifier.
**Delivers:** HTF swing-based premium/discount/equilibrium zones, `pd_zone` field on IFVG type, +1/-1 quality modifier in `calculate_grade()`, dashboard PD zone rows (zone name + percentage)
**Addresses:** PD zone calculation, PD zone grading integration, dashboard PD rows
**Uses:** `ta.pivothigh/ta.pivotlow`, `ta.valuewhen()`, tuple `request.security()` (1 new call), `linefill.new()` for zone visualization
**Implements:** S5C (PD zone detection), updates to S7 (grading) and S8 (inversion), S1 (IFVG type field), S11 (dashboard rows 10-12)
**Avoids:** Stale pivot data (Pitfall 2, use `ta.valuewhen()` pattern), IFVG constructor mismatch (both `IFVG.new()` call sites must be updated)
**Research flag:** Standard patterns — `ta.pivothigh`, `ta.valuewhen`, `linefill.new` are well-documented

### Phase 4.2: Session Tracking and Visualization
**Rationale:** Sessions are architecturally independent of PD zones and cost zero security calls. They can be built and validated separately. Inserting them after PD zones means the dashboard expansion for sessions happens after PD zone rows are already in place, making the layout cleaner.
**Delivers:** Asia/London/NY session H/L tracking, session level visualization (horizontal rays), dashboard session rows (active session name, H/L prices), auto-disable on timeframes > 1H
**Addresses:** Session tracking, session visualization, dashboard session rows
**Uses:** `time(timeframe.period, session_string, "America/New_York")`, `var float` session state scalars (not arrays), `line.set_*()` for update-in-place rendering
**Implements:** S6B (session tracking), new render function, S11 dashboard rows 13-15
**Avoids:** DST timezone errors (Pitfall 6, IANA timezone names only), session noise on higher timeframes (auto-disable guard), session arrays where scalars suffice (Anti-Pattern 4)
**Research flag:** Standard patterns — `time()` with session strings is well-documented

### Phase 4.3: Alert System
**Rationale:** Alerts consume data from the entire pipeline — grades, PD zone context, session levels, IFVG state. Building them last ensures all data sources exist and alert messages can include full context. This is the only phase that touches the global scope outside the main loop.
**Delivers:** Grade-filtered entry alerts, entry invalidation alerts (BE taken), IFVG mitigation alerts (optional, off by default), dynamic messages with grade/direction/price/zone/DOL
**Addresses:** Grade-filtered entry alert, entry invalidation alert, IFVG mitigation alert
**Uses:** `alertcondition()` at global scope, `alert()` with `alert.freq_once_per_bar_close`, pre-computed boolean state variables
**Implements:** S12B (alert section after main loop), 3-5 `alertcondition()` calls, `alert()` calls with dynamic message content
**Avoids:** `alertcondition()` scope error (Pitfall 5, must be at column zero), duplicate alert firing (`alert.freq_once_per_bar_close` only)
**Research flag:** Architecture gotcha (`alertcondition()` scope) is non-obvious but well-documented — no additional research needed

### Phase Ordering Rationale

- **Bugs before features:** The `fvg_singular` hardcode makes the grading system unreliable. Every test of Phase 4.1 grade behavior would be unreliable without fixing this first. Security consolidation is a force-multiplier that unlocks all future development.
- **Core value proposition before supporting features:** PD zone grading integration is the primary differentiator. Sessions and alerts are enhancements that reference PD zone data. This ordering ensures alerts can include zone context in messages.
- **Rendering after detection for each feature:** Validate detection logic via dashboard display before committing to visualization code. For PD zones: add dashboard row first, confirm values are correct, then add linefill visualization.
- **Alerts last because they depend on everything:** Alert messages benefit from grade (Phase 4.0 fix), PD zone data (Phase 4.1), and session context (Phase 4.2). Building alerts before these data sources exist means rewriting messages.

### Research Flags

Phases NOT needing deeper research (standard patterns, well-documented):
- **Phase 4.0:** Bug fixes and tuple consolidation are straightforward refactors with no novel APIs
- **Phase 4.1:** `ta.pivothigh`, `ta.valuewhen`, `linefill.new` are all documented with clear patterns in STACK.md
- **Phase 4.2:** `time()` with session strings is well-documented; the IANA timezone pattern is established
- **Phase 4.3:** `alertcondition()` and `alert()` patterns are fully covered in STACK.md and ARCHITECTURE.md

Potential validation checkpoint (not research, but implementation verification):
- **After Phase 4.1:** Run grade distribution audit across 50+ setups on multiple markets. No single grade should exceed 40% of setups. If A+ exceeds 40%, thresholds need recalibration before shipping Phase 4.2.
- **After Phase 4.2:** Test on a chart spanning a DST transition date (March or November). Verify session boundaries shift correctly.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All APIs verified against official TradingView Pine Script documentation. Budget analysis is based on documented hard limits. |
| Features | HIGH | Competitor analysis covers the major ICT/SMC indicator landscape. Feature prioritization aligns with PRD.md existing requirements. |
| Architecture | HIGH | Based on direct analysis of the existing 2,511-line codebase. Pipeline ordering constraints are derived from actual data dependencies. |
| Pitfalls | HIGH | Each pitfall is verified against official documentation or codebase analysis. The `fvg_singular` bug is a confirmed line-level issue. |

**Overall confidence:** HIGH

### Gaps to Address

- **Grade recalibration thresholds:** Research identifies that score range becomes -3 to +4 after adding PD zone modifier, but exact threshold values for A+/A/A- with the new range need empirical calibration. Cannot be determined from research alone — requires visual validation across markets after implementation.
- **`fvg_singular` replacement logic:** Research confirms the bug must be fixed but does not specify the exact algorithm for detecting "overlapping FVGs at inversion time." The implementation needs to define what constitutes a singular vs. non-singular FVG (e.g., no other FVG within 3 bars, or no overlapping FVG price range). This is a design decision for the implementation phase.
- **PD timeframe default value:** Research recommends the PD timeframe be independently configurable (separate from HTF1/HTF2). The best default value depends on the target user's primary trading timeframe. Leave this as a user configuration decision; suggest "D" (Daily) as the default.
- **Session H/L persistence after session close:** Sessions should persist previous session levels until the next session of the same type opens. The exact persistence logic (how many previous sessions to show) is a UX decision not resolved by research. Recommend showing only the most recent completed session for each type (1 prior Asia, 1 prior London, 1 prior NY).

## Sources

### Primary (HIGH confidence)
- [TradingView Pine Script Docs: Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) — `request.security()` tuples, limits, budget rules
- [TradingView Pine Script Docs: Alerts](https://www.tradingview.com/pine-script-docs/concepts/alerts/) — `alertcondition()` scope requirement, `alert()` vs `alertcondition()` signatures
- [TradingView Pine Script Docs: Time](https://www.tradingview.com/pine-script-docs/concepts/time/) — `time()` function, session strings, IANA timezone handling
- [TradingView Pine Script Docs: Sessions](https://www.tradingview.com/pine-script-docs/concepts/sessions/) — session string format, `input.session()` usage
- [TradingView Pine Script Docs: Fills](https://www.tradingview.com/pine-script-docs/visuals/fills/) — `linefill.new()` behavior, constraints, auto-delete on line deletion
- [TradingView Pine Script Docs: Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) — all hard limits (40 security calls, 500 drawing objects, 64 plots)
- [TradingView Pine Script Docs: Tables](https://www.tradingview.com/pine-script-docs/visuals/tables/) — `barstate.islast` optimization pattern, table cell efficiency
- [TradingView Blog: Tuple Support for Security](https://www.tradingview.com/blog/en/tuple-support-for-the-security-function-in-pine-script-18316/) — tuple consolidation patterns
- Codebase analysis: `src/IFVG_Indicator.pine` (2,511 lines) — confirmed 16 security calls, `fvg_singular = true` at line ~1595, IFVG type structure

### Secondary (MEDIUM confidence)
- [LuxAlgo SMC Indicator](https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/) — competitor feature baseline for table stakes determination
- [LuxAlgo IFVG Indicator](https://www.luxalgo.com/library/indicator/inversion-fair-value-gaps-ifvg/) — competitor IFVG detection (confirmed: no grading)
- [TehThomas ICT Premium & Discount](https://www.tradingview.com/script/omnLTn3f-TehThomas-ICT-Premium-Discount/) — PD zone visual reference
- [LuxAlgo: 5 Causes of Slow Pine Scripts](https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/) — security consolidation performance data
- [Pine Script alertcondition() Complete Guide](https://pineify.app/resources/blog/pine-script-alertcondition-complete-guide-to-creating-custom-tradingview-alerts) — alertcondition patterns and limitations
- [TradersPost: Pine Script v6 Dynamic Requests](https://blog.traderspost.io/article/pine-script-v6-dynamic-requests) — v6-specific dynamic request features

### Internal references
- `PHASE4_PD_ZONES_PLAN.md` — existing implementation plan for PD zones (confirms tuple approach, `ta.valuewhen` pattern)
- `.planning/codebase/CONCERNS.md` — existing tech debt and performance bottleneck inventory
- `PRD.md` — product requirements confirming PD zone modifier (+1/-1) design
- `ARCHITECTURE.md` — technical specification confirming section organization and pipeline order

---
*Research completed: 2026-03-23*
*Ready for roadmap: yes*
