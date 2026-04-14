---
phase: 02-pd-zone-detection-grading-integration
plan: 02
subsystem: pd-zone-rendering
tags: [pd-zone, rendering, dealing-range, labels, linefill, ote]
requires:
  - Wave 1 DealingRange type with drawing-handle fields (line_high/line_eq/line_low, labels, fills, OTE refs)
  - g_current_range populated by Wave 1 main-loop range-selection block
  - Inputs i_show_pd_lines / i_show_pd_fills / i_show_ote / i_pd_line_color / i_pd_eq_color / i_pd_line_width
  - Existing i_extend_bars, i_bullish_color, i_bearish_color
provides:
  - clear_range_drawings(DealingRange r) Section 10 helper
  - render_dealing_range(DealingRange r) Section 10 renderer
  - Main-loop call render_dealing_range(g_current_range) alongside other render_* calls
  - Rotation-safe drawing lifecycle (delete via clear_range_drawings, then recreate with na handles)
  - Invalidation path that deletes drawings + nulls all handle fields when no valid ITH/ITL pair exists
affects:
  - Main-loop PD range-selection block (rotation branch + invalidation branch now call clear_range_drawings)
  - Render block in Section 12 (new render_dealing_range call placed between render_liquidity_lines and render_dashboard)
tech-stack:
  added:
    - line.style_dashed / line.style_dotted usage for PD and OTE lines
    - linefill.new / linefill.delete for zone and OTE shading
    - label.style_none (text-only labels at the right edge)
  patterns:
    - Delete-before-replace on rotation via clear_range_drawings
    - Extend-between-rotations via line.set_x2 and label.set_x (no per-bar recreation)
    - Right-edge clamp math.min(bar_index + i_extend_bars, bar_index + 400)
    - Gated creation + delete-on-toggle-off for optional fill and OTE features
key-files:
  created:
    - .planning/phases/02-pd-zone-detection-grading-integration/02-02-SUMMARY.md
  modified:
    - src/IFVG_Indicator.pine
decisions:
  - Labels use str.tostring(price, "#.##") to produce the exact "1 (price)", "0.5 (price)", "0 (price)" format required by D-08 (matches the user's reference indicator)
  - Lines use line.style_dashed per D-07 (swing H, EQ, swing L all dashed, width driven by i_pd_line_width)
  - OTE band rendered as two dotted purple (#AB47BC @ 70%) lines + linefill (#AB47BC @ 92%) for subtlety; visual only (D-10)
  - Zone fill opacity 92% (very subtle) using i_bearish_color for premium, i_bullish_color for discount (D-09)
  - Optional features (fills, OTE) actively delete their drawings when toggled off so the chart stays clean
  - Invalidation branch (no valid ITH/ITL pair) now clears drawings — without this, old lines persisted as ghosts
metrics:
  duration: execution
  completed: "2026-04-14"
  tasks: 1
  files: 1
requirements-completed: [PDZ-04, PDZ-05, PDZ-06, PDZ-07]
---

# Phase 2 Plan 02: PD Zone Rendering — Summary

One-liner: Added clear_range_drawings() + render_dealing_range() to paint the 3 dashed dealing-range lines with `percentage (price)` labels, optional zone fills, and optional 62%-79% OTE band — with rotation-safe drawing lifecycle.

## What Changed

### Section 10 (Rendering) — new helpers at the top

1. clear_range_drawings(DealingRange r) — deletes all 11 drawing handles on a DealingRange safely (na-guarded per handle). Called from the main loop on range rotation and invalidation.

2. render_dealing_range(DealingRange r) — single renderer that handles all range visuals:
   - Guarded by `not na(r) and r.is_valid and i_show_pd_lines`.
   - Clamps `right_edge = math.min(bar_index + i_extend_bars, bar_index + 400)` to avoid bar-index-too-far warnings.
   - `left_edge = math.max(r.high_bar_idx, r.low_bar_idx)` — line anchors at the later of the two swings.
   - For each of 3 lines (line_high, line_eq, line_low): line.new on first render, else line.set_x2 to extend — no per-bar delete/recreate (avoids flicker and drawing-count churn).
   - For each of 3 labels: label.new on first render, else label.set_x + label.set_text — text is recomputed every bar to keep the price portion of the `percentage (price)` string fresh.
   - Exact D-08 label format: `"1 (" + str.tostring(hi, "#.##") + ")"`, `"0.5 (" + str.tostring(eq, "#.##") + ")"`, `"0 (" + str.tostring(lo, "#.##") + ")"`.
   - Fills (i_show_pd_fills, default OFF): creates linefill.new(line_high, line_eq, bearish@92%) premium and linefill.new(line_eq, line_low, bullish@92%) discount on first render. When toggled off: deletes the linefills and nulls the refs so the next toggle-on recreates cleanly.
   - OTE band (i_show_ote, default OFF): two dotted #AB47BC@70% lines at 62% and 79% of the range, plus a #AB47BC@92% linefill between them. Uses line.set_y1/line.set_y2 in the extend path as a defensive measure. When toggled off: deletes all three refs.

### Section 12 (Main loop)

1. Rotation branch (`if rotated`): added `clear_range_drawings(g_current_range)` immediately before reassigning `g_current_range := DealingRange.new(...)`. The new range carries na drawing handles, which the next render call populates fresh.

2. Invalidation branch (else branch in the range-selection block): replaced the single-line `g_current_range.is_valid := false` with a guarded block that first calls `clear_range_drawings(g_current_range)`, then flips is_valid to false, then explicitly nulls all 11 drawing-handle fields on the snapshot. Without this, a previously valid range's dashed lines/labels would persist as ghosts once the ITH/ITL pair invalidated.

3. Render block: added `render_dealing_range(g_current_range)` between `render_liquidity_lines()` and `render_dashboard(current_latest_ifvg)` — keeps the PD zone under the dashboard but on top of liquidity lines.

## D-08 Label Format — why exactly this string

The user's reference indicator (02-CONTEXT comparison chart) renders right-edge labels as:
- `1 (24,764.25)` for the swing-high boundary
- `0.5 (24,270.00)` for EQ
- `0 (23,775.50)` for the swing-low boundary

We produce the numeric portion via `str.tostring(price, "#.##")`. Pine's `#.##` format trims to two decimals and handles grouping consistently across symbols — matching the reference 1:1 without bespoke formatting logic.

## Rotation Mechanics

| Step | Code | Effect |
|------|------|--------|
| 1. Detect rotation | `bool rotated = na(g_current_range) or not g_current_range.is_valid or g_current_range.high_bar_idx != sel_ith.bar_idx or g_current_range.low_bar_idx != sel_itl.bar_idx` | True when no range exists, current range is invalid, or either ITH/ITL bar idx differs from the newly selected boundary. |
| 2. Delete old drawings | `clear_range_drawings(g_current_range)` | Deletes all 11 handles on the old snapshot. Safe when the ref or handles are na. |
| 3. Reassign | `g_current_range := DealingRange.new(..., line_high=na, line_eq=na, ..., ote_fill=na)` | Fresh snapshot with all drawing handles na. |
| 4. Render creates | `render_dealing_range(g_current_range)` — next call enters the na-handle branch and creates fresh lines/labels. | New drawings appear, anchored to the new bar_idx. |

## Extension Mechanics Between Rotations

Rendered every bar within a stable range:

| Element | Create (once) | Extend (per bar) |
|---------|---------------|------------------|
| 3 PD lines | line.new(...) when handle is na | line.set_x2(r.line_*, right_edge) |
| 3 labels | label.new(...) when handle is na | label.set_x(r.label_*, right_edge) + label.set_text(r.label_*, txt_*) |
| 2 zone linefills | linefill.new(...) when handle is na | implicit — bound to lines, so extending the lines extends the fill |
| 2 OTE lines | line.new(...) when handle is na | line.set_x2 + set_y1/set_y2 |
| OTE linefill | linefill.new(...) when handle is na | implicit via bound lines |

This avoids per-bar delete-recreate, keeps drawing counts stable, and prevents visual flicker.

## Toggle Behavior — Optional Fills & OTE

Both i_show_pd_fills and i_show_ote default to OFF (D-09, D-10).

- Toggle ON: The renderer enters the `if i_show_*` branch; on the first render, the na-handle path creates linefill/line drawings. On subsequent bars they are either implicitly extended (fills) or explicitly extended (OTE lines).
- Toggle OFF: The renderer enters the else branch; each drawing handle is deleted and set back to na. Toggling the input back ON cleanly recreates the drawings — no stale refs.

## Deviations from Plan

None. Plan followed as written.

## Auth Gates

None.

## Known Stubs

- PDZ-07 (A+ frequency calibration per D-15) — post-deploy observation, no code action in this task. Will be recorded after visual validation on TradingView.
- Dashboard PD Zone / Range % rows belong to Plan 02-03 (Wave 3), not this plan.

## PDZ-07 Observation Placeholder

A+ frequency on NQ1! 15m with PD=D: TBD — requires user-side TradingView deployment and manual count over a representative window. Record here (or in STATE.md decisions) after first visual validation:

- Window: [date range]
- Total setups: [n]
- A+ setups: [n]
- A+ rate: [x%]
- Decision: [keep thresholds / tighten]

## Self-Check: PASSED

Automated anchors (verified via grep on commit f50a068):
- `clear_range_drawings(DealingRange r) =>` at line 1976 — FOUND
- `render_dealing_range(DealingRange r) =>` at line 2005 — FOUND
- Three label format strings (`"1 (" + str.tostring`, `"0.5 (" + str.tostring`, `"0 (" + str.tostring`) — FOUND on lines 2026-2028
- `line.set_x2(r.line_high, right_edge)` extension idiom — FOUND at line 2016
- Right-edge clamp `math.min(bar_index + i_extend_bars, bar_index + 400)` — FOUND at line 2007
- Main-loop render call `render_dealing_range(g_current_range)` — FOUND at line 2843
- Two `clear_range_drawings(g_current_range)` call sites in Section 12 (rotation at 2759, invalidation at 2763) — FOUND

Commit f50a068 verified in `git log --oneline`: FOUND.

File src/IFVG_Indicator.pine exists: FOUND.
File .planning/phases/02-pd-zone-detection-grading-integration/02-02-SUMMARY.md exists: FOUND (this file).

## Commits

- f50a068 — Phase 2: render PD dealing range lines, labels, fills, and OTE band
