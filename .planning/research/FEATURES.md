# Feature Research

**Domain:** ICT/SMC TradingView Indicator (IFVG Pro Phase 4 milestone -- PD Zones, Sessions, Dashboard, Alerts)
**Researched:** 2026-03-23
**Confidence:** MEDIUM-HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

Features ICT/SMC traders assume exist in any serious indicator offering PD zones, sessions, and alerts. Missing these = the indicator feels incomplete compared to LuxAlgo SMC, ICT Flow Matrix, and similar free competitors.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Premium/Discount zones with equilibrium line** | Every ICT indicator shows PD zones. Traders need to know if they're buying in discount or selling in premium. LuxAlgo SMC, TehThomas PD, and Exponential-X all provide this. | MEDIUM | Use HTF swing-based dealing range (not simple daily high/low). Plan in PHASE4_PD_ZONES_PLAN.md is solid. Needs 2 `request.security()` calls. |
| **PD zone grading integration** | Traders expect zone context to affect setup quality. Long in discount = better grade, long in premium = worse. PRD Section 3.4.1 explicitly lists this as a grading criterion. | LOW | Already designed: +1/-1 quality modifier. Must fix the hardcoded `fvg_singular=true` bug at the same time to avoid compounding grade inflation. |
| **Session high/low tracking (Asia, London, NY)** | ICT methodology treats session highs/lows as liquidity targets ("data highs/lows"). Every ICT killzone indicator tracks these. Traders look for sweeps of prior session highs/lows. | MEDIUM | Track high/low per session, persist previous session levels. Use named timezone strings (e.g., "America/New_York") not fixed UTC offsets, to handle DST automatically. |
| **Session visualization (boxes or lines)** | Traders expect to see session ranges on chart. Most ICT session indicators use colored background boxes or horizontal lines marking session highs/lows. | LOW | Horizontal lines with labels ("Asia H", "LDN L", "NY H") are cleaner than background boxes for an overlay indicator that already has FVG boxes. Boxes would create visual noise. |
| **Grade-filtered alert for valid entries** | Core alert. Traders want notifications when a high-grade IFVG forms with a valid entry so they don't have to watch the chart constantly. PRD Section 6.1 specifies this. | LOW | Use `alert()` (not `alertcondition()`) for dynamic messages with grade, price, direction. Minimum grade threshold as user input. |
| **Alert for entry invalidation (BE taken)** | Traders need to know when a setup they were watching becomes invalid. BE point being taken means the trade idea is dead. | LOW | Fire when `be_status` transitions from "pending" to "hit". Simple state change detection. |
| **Dashboard showing current state** | Dashboard already exists (v3.0, 10 rows). Traders expect it to show PD zone and session context when those features are enabled. | LOW | Extend existing `table.new` from 10 to 14-16 rows. Add PD zone, zone %, active session, session H/L. |
| **Bug fix: hardcoded fvg_singular=true** | This inflates all grades by giving +1 quality score unconditionally. Every grade is artificially high. Undermines trust in the grading system. | LOW | Line ~1595. Change to actual FVG singularity check (no overlapping FVGs at inversion time). Must be fixed before PD zone modifier is added, otherwise grade range becomes -3 to +5 with inflated baseline. |
| **Bug fix: duplicated HTF bias logic** | HTF bias is calculated inline in two render functions instead of once. Creates maintenance burden and potential inconsistency. | LOW | Extract to a shared function `get_htf_bias()`, call once per bar, store in global variable. |

### Differentiators (Competitive Advantage)

Features that set IFVG Pro apart from the crowded ICT indicator space. These are where the indicator competes.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Integrated IFVG grading with PD zone context** | No competing IFVG indicator grades setups using zone positioning as a factor. LuxAlgo IFVG has no grading at all. Most PD zone indicators are standalone. Combining PD zones into the grading algorithm (not just visual overlay) is unique. | LOW | Already designed. The +1/-1 modifier feeds into the existing hybrid grading system. This is the core differentiator of the entire indicator. |
| **Session highs/lows as liquidity targets in grading** | Session H/L can serve as DOL (Draw on Liquidity) targets. If a session high is the nearest liquidity target for a bearish IFVG, that strengthens the grade. No competitor does this automatically. | HIGH | Requires integrating session levels into the `g_liquidity_array` so they participate in DOL finding and sweep detection. Most complex new feature. |
| **Alert with full context (grade + zone + direction + price + DOL)** | Most indicator alerts are generic. A message like "NQ 5m: A IFVG -- Valid Long Entry @ 18,320. BE: 18,380, DOL: EQH @ 18,450. Zone: DISCOUNT (38%)" gives traders everything they need to act. | LOW | Use `alert()` with `str.format()` to build dynamic messages. Pine Script v6 supports series string in `alert()`. |
| **Multi-layer dashboard with actionable state** | Existing dashboard already shows HTF bias and DOL. Adding PD zone %, active session, session H/L, and a "signal quality" summary makes it a one-glance decision tool. Most competitor dashboards show only counts or generic bias. | LOW | Incremental extension of existing table. Keep it compact -- information density over decoration. |
| **OTE (Optimal Trade Entry) zone within dealing range** | ICT's 62%-79% retracement zone within the dealing range is the premium entry area. Displaying this within the PD zone visualization would highlight the "sweet spot" for entries. | MEDIUM | Requires adding two additional lines at 62% and 79% of the dealing range. Visual clutter risk -- make it optional and off by default. |
| **New York midnight open price** | ICT methodology heavily uses the NY midnight open as a reference level. Many traders track this manually. Auto-plotting it as a reference line is low effort, high value. | LOW | Single horizontal line at the open price of the bar at 00:00 ET. Use `time()` function with "America/New_York" timezone. |
| **Previous day high/low (PDH/PDL) as liquidity** | PDH and PDL are considered major liquidity pools in ICT methodology. Traders expect price to sweep these levels. Adding them as liquidity targets feeds the grading system. | MEDIUM | Daily H/L via `request.security(syminfo.tickerid, "D", high/low[1])`. Costs 2 `request.security()` calls. Add to `g_liquidity_array` as "PDH"/"PDL" type. |
| **Alert for IFVG mitigation** | Less critical than entry alerts, but useful for trade management. Tells traders when a setup they may have entered has been fully closed out. | LOW | Fire when IFVG is removed from array due to mitigation. Optional (off by default per PRD). |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem valuable but create problems in this context. Deliberately NOT building these.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Killzone background boxes (session time shading)** | Many ICT session indicators shade entire session periods. Looks impressive in screenshots. | Creates massive visual noise on an overlay indicator that already draws FVG boxes, IFVG boxes, HTF overlays, liquidity lines, BE/SL lines, and PD zone lines. Chart becomes unreadable. | Session H/L lines only. Clean, lightweight, provides the same actionable information (where session liquidity rests). |
| **Comprehensive Fibonacci levels within dealing range** | ICT methodology uses multiple fib levels (0.236, 0.382, 0.5, 0.618, 0.705, 0.786). Some indicators draw all of them. | Clutters the chart with 7+ horizontal lines in PD zone alone. Most levels are not actionable for IFVG trading specifically. | Show only equilibrium (50%) as a solid line. Optionally show OTE zone (62%-79%) as a subtle fill. Everything else is noise for this indicator's purpose. |
| **Auto-trading / strategy mode** | Users want to automate entries based on IFVG grades. | Pine Script strategy mode fundamentally changes indicator behavior (adds broker emulator, changes drawing limits, different execution model). The IFVG strategy requires discretion (momentum reading, context). Mechanical execution of IFVG grades would produce poor results. | Keep as overlay indicator. Provide webhook-compatible alert messages for users who want to route to execution tools themselves. |
| **SMT (Smart Money Tool) divergence detection** | PRD mentions SMT as a +1 bonus in grading. Some ICT indicators include it. | Requires loading a correlated symbol's data via `request.security()` (e.g., ES for NQ). Costs additional security calls (already 16 of 40 used). Complex to implement correctly (needs bar alignment, correlation logic). | Defer to future milestone. Already listed as "Out of Scope" in PROJECT.md. |
| **LRLR (Linear Regression / Trendline) liquidity** | PRD lists LRLR as a liquidity type. Some advanced ICT indicators detect trendline liquidity. | Diagonal rendering on TradingView is complex. Trendline detection requires multiple confirmed touches (3+), expensive computation. Pine Script line objects count against the 500 limit. | Defer to future milestone. Already listed as "Out of Scope" in PROJECT.md. |
| **Real-time (intra-bar) alerts** | Some traders want alerts before bar close for speed. | Causes repainting. An alert fires, then the bar reverses and the condition is no longer true. Leads to false signals and erodes trust in the indicator. Core design principle is no-repaint. | All alerts on `barstate.isconfirmed` only. Document this clearly in tooltips. |
| **Dashboard with dozens of metrics** | "More data = better" thinking. Some dashboards show 20+ rows of indicators, moving averages, RSI, MACD, etc. | Irrelevant to IFVG methodology. Clutters the chart. Performance cost of large tables. Distracts from the indicator's core purpose. | Compact dashboard (14-16 rows max) showing only IFVG-relevant state: grade, entry status, DOL, PD zone, session, HTF bias. |

## Feature Dependencies

```
[PD Zone Calculation]
    |
    +---requires---> [HTF Swing Detection via request.security()]
    |                    (costs 2 request.security() calls)
    |
    +---enhances---> [Grading Algorithm]
    |                    (PD zone modifier: +1/-1 quality score)
    |
    +---requires---> [Bug Fix: fvg_singular hardcode]
                         (must fix before adding another modifier)

[Session Tracking]
    |
    +---requires---> [Session Time Detection (time() with named timezone)]
    |
    +---enhances---> [Dashboard] (active session, session H/L display)
    |
    +---optionally-enhances---> [Liquidity Array]
                                    (session H/L as DOL targets -- differentiator)

[Alert System]
    |
    +---requires---> [IFVG Grading] (already exists)
    |
    +---enhanced-by---> [PD Zone] (zone context in alert message)
    |
    +---enhanced-by---> [Session Tracking] (session context in alert message)

[Dashboard Enhancement]
    |
    +---requires---> [Existing Dashboard] (already exists, 10 rows)
    |
    +---enhanced-by---> [PD Zones] (zone %, zone name)
    |
    +---enhanced-by---> [Sessions] (active session, session H/L)

[Bug Fix: fvg_singular]
    |
    +---blocks---> [PD Zone Grading Integration]
                       (grade range expands; must fix inflation first)

[Bug Fix: HTF Bias Duplication]
    |
    +---independent (can be done anytime, no dependencies)
```

### Dependency Notes

- **PD Zone Grading requires fvg_singular bug fix:** The grading system currently inflates all grades by +1 due to hardcoded `fvg_singular=true`. Adding a PD zone modifier on top of an already-inflated system would make grades meaningless. Fix the bug first, validate grades are correct, then add the PD zone modifier.
- **Session H/L as liquidity targets enhances grading (optional):** This is the most complex integration. Session levels would need to be added to `g_liquidity_array` with type "PDH"/"PDL"/"Asia H"/"LDN L"/"NY H" etc. This lets the DOL finder and sweep detector see session levels as potential targets. High value but high complexity -- could be deferred within the milestone.
- **Alerts are enhanced by PD zones and sessions:** Alert messages become more valuable when they include zone context ("DISCOUNT 38%") and session context ("NY session"). Build PD zones and sessions first, then build alerts that incorporate them.
- **Dashboard is incrementally enhanced:** Each new feature (PD zones, sessions) adds 2-4 rows to the dashboard. No conflicts -- purely additive.

## MVP Definition

### Launch With (Phase 4a -- Bug Fixes + PD Zones)

Minimum viable additions that fix known issues and add the most impactful new feature.

- [ ] **Fix fvg_singular hardcode** -- Prerequisite. Without this, all grading is unreliable.
- [ ] **Fix HTF bias duplication** -- Quick cleanup. Extract to shared function.
- [ ] **PD zone calculation from HTF swings** -- Core feature. Uses `ta.pivothigh/ta.pivotlow` + `request.security()`.
- [ ] **PD zone visualization (lines + optional fill)** -- Equilibrium line, swing H/L boundary lines, optional zone fill.
- [ ] **PD zone grading integration** -- +1/-1 quality modifier for optimal/suboptimal zone positioning.
- [ ] **Dashboard PD zone rows** -- Zone name + percentage in existing dashboard.

### Add After Validation (Phase 4b -- Sessions + Alerts)

Features to add once PD zones are working and grades are validated.

- [ ] **Session tracking (Asia, London, NY)** -- Track H/L per session with DST-aware timezone strings.
- [ ] **Session H/L visualization** -- Horizontal lines with labels for previous session highs/lows.
- [ ] **Grade-filtered entry alert** -- `alert()` with dynamic message, minimum grade threshold.
- [ ] **Entry invalidation alert** -- Fire when BE point is taken.
- [ ] **IFVG mitigation alert** -- Fire when IFVG is mitigated (optional, off by default).
- [ ] **Dashboard session rows** -- Active session name, session H/L prices.

### Future Consideration (Phase 5+)

Features to defer until core Phase 4 is validated.

- [ ] **Session H/L as liquidity targets in grading** -- Complex integration with `g_liquidity_array`. Defer because it requires careful DOL finder changes and testing.
- [ ] **OTE zone visualization (62%-79%)** -- Subtle fill within dealing range. Low priority, high visual clutter risk.
- [ ] **NY midnight open price line** -- Easy to implement but not critical for IFVG methodology specifically.
- [ ] **Previous day high/low (PDH/PDL) as liquidity** -- Costs 2 `request.security()` calls (18 of 40 would be used). Valuable for DOL targeting.
- [ ] **Webhook-compatible alert format** -- JSON-structured messages for automation tools like TradersPost or CrossTrade.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Fix fvg_singular hardcode | HIGH | LOW | P0 |
| Fix HTF bias duplication | MEDIUM | LOW | P0 |
| PD zone calculation | HIGH | MEDIUM | P1 |
| PD zone visualization | HIGH | LOW | P1 |
| PD zone grading integration | HIGH | LOW | P1 |
| Dashboard PD zone rows | MEDIUM | LOW | P1 |
| Session tracking (H/L) | HIGH | MEDIUM | P1 |
| Session visualization | MEDIUM | LOW | P1 |
| Entry alert (grade-filtered) | HIGH | LOW | P1 |
| Entry invalidation alert | MEDIUM | LOW | P1 |
| IFVG mitigation alert | LOW | LOW | P2 |
| Dashboard session rows | MEDIUM | LOW | P1 |
| Session H/L as DOL targets | HIGH | HIGH | P2 |
| OTE zone (62%-79%) | LOW | MEDIUM | P3 |
| NY midnight open | LOW | LOW | P3 |
| PDH/PDL as liquidity | MEDIUM | MEDIUM | P2 |
| Webhook-compatible alerts | LOW | LOW | P3 |

**Priority key:**
- P0: Must fix before adding new features (blockers)
- P1: Core milestone deliverables
- P2: Should have, add if time/resources permit within milestone
- P3: Nice to have, defer to future milestone

## Competitor Feature Analysis

| Feature | LuxAlgo SMC (Free) | LuxAlgo IFVG | ICT Flow Matrix | TehThomas PD | IFVG Pro (Ours) |
|---------|-------------------|--------------|-----------------|--------------|-----------------|
| **PD Zones** | Yes (built-in) | No | Yes | Yes (standalone) | Planned: HTF swing-based |
| **IFVG Detection** | No | Yes (basic) | No | No | Yes (with grading) |
| **Setup Grading** | No | No | No | No | Yes (A+ to C, unique) |
| **Session Tracking** | No | No | Yes | No | Planned |
| **Entry Alerts** | Yes (generic) | Yes (zone retest) | Yes | No | Planned (grade-filtered, context-rich) |
| **Dashboard** | No | No | Limited | No | Yes (comprehensive) |
| **HTF Analysis** | Yes (BOS/CHoCH) | No | Yes | No | Yes (FVG/IFVG overlay) |
| **Liquidity Detection** | Yes (EQH/EQL) | No | Yes | No | Yes (EQH/EQL/ITH/ITL + sweeps) |
| **BE/SL Levels** | No | No | No | No | Yes (unique) |
| **PD Zone in Grading** | N/A | N/A | N/A | N/A | Planned (unique) |

**Key Competitive Insight:** No single competitor combines IFVG detection, setup grading, PD zone integration into grading, session tracking, and actionable alerts. Most are either generic SMC indicators (LuxAlgo) or single-concept indicators (TehThomas PD, standalone IFVG detectors). IFVG Pro's grading system is the primary differentiator -- every new feature should feed into it.

## Resource Budget (request.security() Calls)

Critical constraint: TradingView limits indicators to 40 `request.security()` calls total.

| Feature | Calls Used | Running Total |
|---------|-----------|---------------|
| Existing (Phase 1-3) | 16 | 16 |
| PD Zone HTF swings | 2 | 18 |
| PDH/PDL (if added) | 2 | 20 |
| Session H/L (if via security) | 0 | 20 |
| **Remaining budget** | | **20 calls** |

Session tracking does NOT require `request.security()` -- use `time()` function with session strings to detect session boundaries, track highs/lows using real-time bar data within sessions.

## Sources

- [LuxAlgo SMC Indicator](https://www.tradingview.com/script/CnB3fSph-Smart-Money-Concepts-SMC-LuxAlgo/) -- Most popular free SMC indicator, feature baseline
- [LuxAlgo IFVG Indicator](https://www.luxalgo.com/library/indicator/inversion-fair-value-gaps-ifvg/) -- Competitor IFVG detection (no grading)
- [LuxAlgo PD Zones Documentation](https://docs.luxalgo.com/docs/luxalgo-toolkits/price-action-concepts/pdzones) -- Premium/Discount implementation reference
- [TehThomas ICT Premium & Discount](https://www.tradingview.com/script/omnLTn3f-TehThomas-ICT-Premium-Discount/) -- Standalone PD zone indicator
- [ICT Dealing Range by originalsaucemaker](https://www.tradingview.com/script/OWed4e6I-ICT-Dealing-Range/) -- Dealing range with liquidity sweep-based construction
- [ICT Killzones Toolkit (LuxAlgo)](https://www.luxalgo.com/library/indicator/ict-killzones-toolkit/) -- Session tracking reference
- [ICT Asian Range and Killzones](https://www.tradingview.com/script/k1qv9OWl-ICT-Asian-Range-and-Killzones/) -- Session H/L implementation reference
- [Pine Script Alerts Documentation](https://www.tradingview.com/pine-script-docs/concepts/alerts/) -- `alert()` vs `alertcondition()` for dynamic messages
- [Pine Script Sessions Documentation](https://www.tradingview.com/pine-script-docs/concepts/sessions/) -- `time()` function and session handling
- [ICT Killzone Times Guide 2025](https://innercircletrader.net/tutorials/master-ict-kill-zones/) -- Standard session times reference
- [ICT Dealing Range and OTE](https://tradingfinder.com/education/forex/ict-dealing-range/) -- OTE zone (62%-79%) within dealing range
- [ICT Premium/Discount Zones Guide](https://www.equiti.com/sc-en/news/trading-ideas/discount-premium-zones-in-ict-trading/) -- Zone calculation methodology

---
*Feature research for: IFVG Pro Phase 4 (PD Zones, Sessions, Dashboard, Alerts)*
*Researched: 2026-03-23*
