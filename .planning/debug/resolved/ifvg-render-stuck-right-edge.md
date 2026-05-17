---
slug: ifvg-render-stuck-right-edge
status: resolved
trigger: |
  IFVG setup boxes/labels (A- SELL, A SELL, B+ SELL, etc.) are rendering at the
  FAR RIGHT EDGE of the chart at OLD price levels that haven't been touched in
  many bars. The setups were formed long ago (visible in the upper-left area
  where price was at those levels) but the boxes are anchored to recent bar
  indices. User confirms the same bug occurs for HTF FVGs as well.
created: 2026-05-17T17:25:44Z
updated: 2026-05-17T19:10:00Z
files_changed:
  - src/IFVG_Indicator.pine
reopened: 2026-05-17T18:15:00Z
reopened_reason: |
  Bug persists after commit 659ae57. User screenshot
  (/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/5.png) shows
  4+ IFVG boxes (A- BUY, B+ BUY, A- BUY, A BUY) clustered in mid-screen, NOT anchored
  at the original FVG formation bars (which are visibly far to the LEFT in the chart).
  The defensive `math.max(start_bar, bar_index - 400)` clamp left in place is the
  remaining culprit — for any IFVG whose source FVG formed more than 400 bars ago,
  the clamp slides the left edge forward to `bar_index - 400`, recreating the
  original "stranded near the right edge" symptom. User explicitly said "the box
  should start from the formation of the FVG which is inverted" and "for older fvgs
  it is still starting from the middle of the screen."
---

# Debug: IFVG/HTF FVG boxes rendering anchored to current bar (not inversion bar)

## Symptoms

**Expected behavior:** IFVG setup boxes (and HTF FVG boxes) should be drawn anchored to the bars where the inversion / formation actually occurred. The left edge of each box should sit at the bar where the FVG inverted (creating the IFVG), and the right edge should extend forward by `i_extend_bars` from that anchor.

**Actual behavior:** All graded IFVG boxes ("A- SELL", "A SELL", "B+ SELL", "B+ SELL") are clustered against the right edge of the chart at price levels that haven't been touched in many hundreds of bars. The price action that *formed* these setups is visible far to the left, but no boxes are drawn there. Same issue is reported by the user for HTF FVG boxes.

**Error messages:** None — no compile errors, no runtime errors. Pure visual misplacement.

**Timeline:** Unknown when introduced. User noticed during Phase 2 / Phase 5 UAT-style chart inspection. Likely a long-standing bug since boxes use bar-index anchors throughout Section 10 rendering.

**Reproduction:**
1. Load `src/IFVG_Indicator.pine` on any chart with significant historical IFVG formations (NQ1!/ES1! 15m suggested).
2. Scroll the chart so that older IFVG setups are visible mid-chart.
3. Observe that all graded setup boxes appear stranded near the right edge at stale prices instead of at their historical formation bars.

Reference screenshot: `/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/2.png`
Round 2 follow-up screenshot: `/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/5.png`

## Suspect Areas (orchestrator's initial hypotheses)

1. **Primary suspect — render functions overwrite box anchors with `bar_index` each bar.** CONFIRMED.
2. **Secondary suspect — IFVG.start_bar / end_bar populated with `bar_index` at inversion time.** ELIMINATED — `start_bar` is correctly inherited from source FVG, and `inversion_bar` correctly captured at inversion (lines 1869–1870 LTF, 817–818 HTF).
3. **Tertiary — drawings are deleted and recreated every bar.** PARTIAL — recreation logic is the actual bug; the per-bar delete+recreate is intentional, but the recreation uses live `bar_index` arithmetic that drags the box rightward each bar.
4. **Round-3 — defensive `math.max(start_bar, bar_index - 400)` clamp.** CONFIRMED. The clamp was added under the mistaken belief that `max_bars_back = 500` constrains drawing-object coordinates. It does not. `max_bars_back` only governs how far back **series** references (`close[N]`, `high[N]`) can reach. Drawing functions (`box.new`, `line.new`, `label.new`) accept arbitrary historical `bar_index` values for `left` / `x1` / `x` and TradingView renders them at the correct chart coordinate.

## Current Focus

- hypothesis: RESOLVED. The five `math.max(..., bar_index - 400)` clamps in the render layer are the bug. Removing them all and using the stored anchor (`start_bar` / `inversion_bar`) directly fixes the sliding for setups of any age.
- test: Visual verification on TradingView after deploying. Older IFVG boxes (whose source FVG formed >400 bars ago) should now have their left edge at the exact bar where the FVG formed, not at `bar_index - 400`.
- expecting: No "bar index too far" runtime error. Boxes for old setups render across the full historical extent of the chart (or are visually clipped at the left edge of the visible range, but anchored correctly).
- next_action: User to deploy `src/IFVG_Indicator.pine` to TradingView and confirm fix visually.

## Evidence (round 3 — final fix)

- timestamp: 2026-05-17T19:00Z
  observation: Confirmed five clamp sites in `src/IFVG_Indicator.pine`:
  - line 2149: `render_fvg_boxes` (active LTF FVG) — `math.max(fvg.start_bar, bar_index - 400)`
  - line 2234: `render_ifvg_boxes` (LTF IFVG box) — `math.max(ifvg.start_bar, bar_index - 400)`
  - line 2319: `render_ifvg_boxes` (LTF IFVG entry line) — `math.max(ifvg.inversion_bar, bar_index - 400)`
  - line 2393: `render_htf_fvg_boxes` (active HTF FVG) — `math.max(fvg.start_bar, bar_index - 400)`
  - line 2447: `render_htf_ifvg_boxes` (HTF IFVG) — `math.max(ifvg.start_bar, bar_index - 400)`
- timestamp: 2026-05-17T19:00Z
  observation: Pine Script v6 documentation: `max_bars_back` (set in `indicator()` declaration) is a directive that controls the buffer size for **historical series access**, e.g., `close[N]`, `high[N]`, `bar_index[N]`. It does NOT bound the integer values that can be passed to `box.new(left=...)`, `line.new(x1=...)`, or `label.new(x=...)`. The TradingView platform itself manages drawing clipping at the chart edge.
- timestamp: 2026-05-17T19:00Z
  observation: Active LTF FVG render (line 2149) had the same clamp and same incorrect comment. Removed for consistency — active FVGs younger than 400 bars never exercised the clamp, but the principle is the same.

## Evidence (round 2)

- timestamp: 2026-05-17T18:15Z
  observation: User screenshot 5.png (`/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/5.png`) shows 4+ IFVG boxes (A- BUY, B+ BUY, A- BUY, A BUY) stacked at center-screen extending to the right edge. The actual price action that *formed* the source FVGs is clearly visible in the LEFT half of the chart — far to the left of where the boxes start. This is the same sliding-clamp bug, just bounded to `bar_index - 400` instead of unbounded.
- timestamp: 2026-05-17T18:15Z
  observation: The clamp comment in the original code claimed it was "to prevent 'bar index too far' error (max_bars_back = 500)". This is a misunderstanding: `max_bars_back` controls how far back series references (e.g., `close[N]`) can reach, not the `left` argument to drawing functions. Drawing-object coordinates are independent of `max_bars_back`.

## Evidence

- timestamp: 2026-05-17T17:50Z
  observation: `render_ifvg_boxes()` line 2229 sets `right_edge = bar_index + i_extend_bars` every bar; line 2232 clamps `ifvg_left_edge = math.max(ifvg.start_bar, bar_index - 400)`. With `max_bars_back=500`, any IFVG with `start_bar < bar_index - 400` is clamped — its left edge slides forward each bar. The same right_edge is reused for SL line (2275), BE line (2299), entry line (2321) and entry label x (2354). Net effect: the historical IFVG's setup graphics slide rightward in lockstep with `bar_index`, appearing as a fixed-size window pinned to the chart's right edge.
- timestamp: 2026-05-17T17:50Z
  observation: `render_htf_fvg_boxes()` (lines 2369–2418) and `render_htf_ifvg_boxes()` (lines 2423–2471) use the identical anti-pattern: `right_edge = bar_index + i_extend_bars`, `left_edge = math.max(fvg.start_bar, bar_index - 400)` / `math.max(ifvg.start_bar, bar_index - 400)`. Confirms the user's report that HTF boxes show the same bug.
- timestamp: 2026-05-17T17:50Z
  observation: `check_inversions()` line 1870 stores `inversion_bar = bar_index` at the moment of inversion — this value is permanently captured and never mutated again. `check_htf_inversions()` line 818 does the same. So the source-of-truth anchor exists; only the render layer ignores it.
- timestamp: 2026-05-17T17:50Z
  observation: The active LTF FVG render (`render_fvg_boxes`, lines 2131–2173) also uses `bar_index + i_extend_bars` but in that context the FVG is still "live" and projecting forward, which is arguably correct UX. Not changed.

## Eliminated

- IFVG type fields are populated correctly at creation time. The bug is purely in the render layer.
- Drawing object lifecycle (delete-then-recreate) is correct; it must remain so to support live updates of BE/SL status.
- `max_bars_back = 500` as a hypothetical cause of "bar index too far" runtime error on drawing-object coordinates. Pine v6 drawing functions accept arbitrary `bar_index` values for their position arguments.

## Root Cause

Render functions used a defensive `math.max(start_bar, bar_index - 400)` clamp on every box/line left edge under the mistaken belief that drawing-object coordinates older than `max_bars_back` would error. They do not. The clamp transparently slid every historical setup's left edge forward each bar to `bar_index - 400`, producing the visible "stuck near the right edge / mid-screen" symptom.

## Resolution

**root_cause:** Five `math.max(start_bar, bar_index - 400)` (and one `math.max(inversion_bar, bar_index - 400)`) clamps in the render layer slide historical box/line left edges forward each bar, because the clamp was written under the false premise that `max_bars_back` constrains drawing-object coordinates.

**fix:** Removed the clamp at all five sites in `src/IFVG_Indicator.pine`. Each site now uses the stored anchor directly:
- line 2149 `render_fvg_boxes`: `int fvg_left_edge = fvg.start_bar`
- line 2234 `render_ifvg_boxes` (IFVG box): `int ifvg_left_edge = ifvg.start_bar`
- line 2319 `render_ifvg_boxes` (entry line): `int entry_left_edge = ifvg.inversion_bar`
- line 2393 `render_htf_fvg_boxes`: `int left_edge = fvg.start_bar`
- line 2447 `render_htf_ifvg_boxes`: `int left_edge = ifvg.start_bar`

The right edge of each render (`bar_index + i_extend_bars`) is intentionally left unchanged — these are live zones that project forward to the current bar until mitigated. Pine v6 syntax constraints respected: no blank lines added inside loops/ifs, no trailing `=`, no `math.abs/max/min` cast issues since `math.max` was removed entirely.

**files_changed:** `src/IFVG_Indicator.pine`
