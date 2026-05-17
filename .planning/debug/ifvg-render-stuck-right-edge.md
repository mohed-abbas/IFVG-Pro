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
updated: 2026-05-17T17:55:00Z
files_changed:
  - src/IFVG_Indicator.pine
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

## Suspect Areas (orchestrator's initial hypotheses)

1. **Primary suspect — render functions overwrite box anchors with `bar_index` each bar.** CONFIRMED.
2. **Secondary suspect — IFVG.start_bar / end_bar populated with `bar_index` at inversion time.** ELIMINATED — `start_bar` is correctly inherited from source FVG, and `inversion_bar` correctly captured at inversion (lines 1869–1870 LTF, 817–818 HTF).
3. **Tertiary — drawings are deleted and recreated every bar.** PARTIAL — recreation logic is the actual bug; the per-bar delete+recreate is intentional, but the recreation uses live `bar_index` arithmetic that drags the box rightward each bar.

## Current Focus

- hypothesis: Render functions in Section 10 use `bar_index + i_extend_bars` for the right edge and clamp the left edge to `math.max(start_bar, bar_index - 400)`. Combined with the indicator-level `max_bars_back=500`, any IFVG older than 400 bars becomes a sliding 420-bar-wide window pinned to the chart's right edge.
- test: Read render_ifvg_boxes, render_htf_fvg_boxes, render_htf_ifvg_boxes — identify every `bar_index +` / `bar_index -` reference used as a coordinate for HISTORICAL setup drawings (boxes, BE/SL/entry lines, entry label).
- expecting: Find right_edge = bar_index + i_extend_bars and left_edge clamped to bar_index - 400. CONFIRMED at lines 2229, 2232, 2273–2275, 2297–2299, 2317–2321, 2354, 2388, 2390, 2441, 2443.
- next_action: apply fix — anchor boxes/lines/labels to `ifvg.inversion_bar` (LTF/HTF IFVG) and `fvg.start_bar` (active HTF FVG), with right edge = anchor + i_extend_bars (not bar_index + i_extend_bars).

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

## Root Cause

Render functions for historical setup graphics (LTF IFVG box + BE/SL/entry lines + entry label; HTF FVG box; HTF IFVG box) compute every coordinate from the live `bar_index`, dragging historical drawings rightward each confirmed bar. The IFVG already stores `inversion_bar` (and active HTF FVGs store `start_bar`) — these stable historical anchors must be used in place of `bar_index` for both left and right edges.

## Resolution

**root_cause:** `render_ifvg_boxes`, `render_htf_fvg_boxes`, and `render_htf_ifvg_boxes` use `bar_index + i_extend_bars` for the right edge and `bar_index - 400` to clamp the left edge — so every historical setup's box/lines/labels slide rightward each confirmed bar instead of staying anchored to the formation bar.

**fix (revised 2026-05-17 after user feedback):** The first revision anchored both edges to `ifvg.inversion_bar`, but the IFVG box should span FROM the **original FVG's first bar** TO the current bar + extend (the zone remains live until mitigated). Correct anchoring:
- LTF IFVG (in `render_ifvg_boxes`): left = `math.max(ifvg.start_bar, bar_index - 400)` (anchors at the source FVG's first candle, not the inversion bar), right = `bar_index + i_extend_bars` (projects forward — live zone). SL/BE lines follow the same `ifvg_left_edge` / `right_edge` so they span the full zone.
- LTF IFVG entry line/label (intentionally different): left = `math.max(ifvg.inversion_bar, bar_index - 400)`, right = `right_edge`. The entry line is drawn at the inversion candle's close — it didn't exist before inversion, so it logically begins at `inversion_bar`.
- HTF active FVG (in `render_htf_fvg_boxes`): left = `math.max(fvg.start_bar, bar_index - 400)` (unchanged), right = `bar_index + i_extend_bars` (projects forward — live zone).
- HTF IFVG (in `render_htf_ifvg_boxes`): left = `math.max(ifvg.start_bar, bar_index - 400)` (source HTF FVG's first bar, not inversion), right = `bar_index + i_extend_bars`.
- Active LTF FVG (`render_fvg_boxes`) UNCHANGED — those are live candidate zones, behaved correctly already.

The `bar_index - 400` floor remains as a defensive clamp for IFVGs older than 400 bars (residual sliding for very-old setups is bounded). The sliding the user originally observed is eliminated for any setup younger than 400 bars — which is the typical case after FIFO cleanup.

Pine v6 syntax constraints respected: no blank lines inside loops/ifs, no trailing `=` at end of line, no split expressions without operator at line end.

**files_changed:** `src/IFVG_Indicator.pine`
