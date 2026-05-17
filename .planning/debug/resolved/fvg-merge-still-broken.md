---
slug: fvg-merge-still-broken
status: resolved
trigger: |
  After commits 23c84e7 (initial merge fix) and 817ed9f (adjacent-FVG edge case fix),
  user reports merge still produces oversized IFVG boxes containing mixed-color
  candles at the formation area. Screenshot 8 shows an LTF IFVG (no dashed border;
  blue entry line at top, red SL line at bottom) with visibly mixed-color candles
  near the left edge of the box.
created: 2026-05-17T19:15:00Z
updated: 2026-05-17T19:45:00Z
files_changed:
  - src/IFVG_Indicator.pine
prior_sessions:
  - .planning/debug/resolved/fvg-merge-fix-not-applied.md (concluded HTF box, not LTF)
  - .planning/debug/resolved/fvg-merge-edge-case.md (added middle-candle check, commit 817ed9f)
user_config:
  i_fvg_min_size_mult: 0.1
  i_fvg_atr_period: 14
  i_max_fvgs: 3 (default — only 3 active FVGs tracked simultaneously)
---

# Debug: FVG merge still produces oversized boxes despite two prior fixes

## Symptoms

Screenshot 8 (`/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/8.png`) shows a single bullish LTF IFVG box whose left edge anchors at a region of mixed-color candles. The user has applied commits 23c84e7 and 817ed9f and still observes the same symptom on multiple cases.

Visual identification:
- Box has NO dashed border → LTF (not HTF this time)
- Top of box: thin BLUE horizontal line → entry line (`i_entry_color_bull = #2962FF`) at inversion_close
- Bottom of box: thin RED horizontal line → SL line below the FVG
- No `[TF] IFVG` label visible → LTF
- Leftmost ~3-4 bars at the box's left edge appear mixed (blue, red, blue alternating)

## Hypotheses

### H1 — Real merge bug still present despite both fixes
The 817ed9f scan checks `existing.end_bar - 1` and `new_fvg.end_bar - 1` (middle candles only). The OUTER candles `[end_bar-2]` and `[end_bar]` of each FVG were never checked. Choppy 3-candle FVG patterns can form on `[red, blue, blue]` or `[blue, blue, red]`, leaving red outer candles inside the eventual merged span.

### H2 — Cumulative chain merge
After FVG1+FVG2 merge, `existing.end_bar` advances to FVG2's value. When FVG3 arrives, `bar_distance` is measured against FVG2 and the scan only covers candles between FVG2 and FVG3. Anything between FVG1 and FVG2 has already been "approved" by the time of the second merge — but the merge logic never validates the COMBINED span. Bug magnitude grows with chain depth.

### H3 — Visual misinterpretation
Post-c976911 box anchoring stretches the box from `ifvg.start_bar` to `bar_index + i_extend_bars`. The user cannot tell from the box alone which bars are formation vs post-formation projection.

### H4 — UX problem
Even with correct merge logic, users see the wide box and assume it's a detection bug. A visual marker at `inversion_bar` would eliminate the ambiguity.

## Current Focus

- hypothesis: H1 + H2 are BOTH real (scan gaps allow opposite candles inside the merged span). H4 is a UX win regardless.
- next_action: replace the three-piece scan (between-range + new-mid + existing-mid) with a single combined-span scan that covers every candle in `[min(start_bars), max(end_bars)]`, plus add a formation divider line at `inversion_bar`.

## Evidence

- timestamp: 2026-05-17T19:30:00Z
  source: screenshot 8 (image read)
  finding: LTF bullish IFVG box, left edge anchored at ~5-6 bars of mixed blue/red candles. Top of box has thin blue line (entry); bottom has thin red line (SL). No dashed border, no `[TF]` label. Confirms LTF.
- timestamp: 2026-05-17T19:32:00Z
  source: src/IFVG_Indicator.pine lines 543-605 (pre-fix merge_with_existing_fvg)
  finding: scan covered ONLY `(existing.end_bar, new_fvg.start_bar)` range + new_fvg's middle candle + existing's middle candle. Outer candles of both 3-bar FVG windows never inspected. Combined chain span never inspected against the original FVG1's start_bar.
- timestamp: 2026-05-17T19:33:00Z
  source: src/IFVG_Indicator.pine line 595 (pre-fix merge)
  finding: merge updates `existing.end_bar` but never updates `existing.start_bar`. So `start_bar` correctly remains the original FVG1's start across any chain depth. Combined-span scan from `start_bar` is therefore safe and meaningful.

## Eliminated

- timestamp: 2026-05-17T19:34:00Z
  hypothesis: HTF box mis-identification (from prior session)
  reason: screenshot 8 lacks dashed border AND `[TF]` label. Confirmed LTF.

## Resolution

**Root cause:** Two compounding scan gaps in `merge_with_existing_fvg`:
1. The 817ed9f middle-candle check ignored OUTER candles of both 3-bar FVG windows. A choppy bullish FVG can form on `[red, blue, blue]` — the red outer candle slips through.
2. On chain merges (FVG1 → FVG2 → FVG3 → ...), each merge only validated candles since the LAST merge. The earlier original-FVG span was never re-validated against the latest extension. After multiple merges, the combined span could contain opposite-color candles that were never inspected by any single merge step.

**Fix (logic):** Replace the three-piece scan (between-range + new-mid + existing-mid) with a single combined-span loop from `min(existing.start_bar, new_fvg.start_bar)` to `max(existing.end_bar, new_fvg.end_bar)`. Any opposite-color candle (close < open for bullish, close > open for bearish; dojis ignored) anywhere in the merged region blocks the merge. Because the merge never updates `existing.start_bar`, the combined span on every chain step always covers from the original FVG1's first bar to the latest candidate's last bar — closing the chain-merge gap and the outer-candle gap simultaneously.

**Fix (UX):** Added `i_show_formation_divider` input (default on) that draws a thin gray dotted vertical line at `ifvg.inversion_bar` on every rendered IFVG. The line visually splits the formation window (left of line — the original FVG candles) from the post-inversion live zone projection (right of line — pure price action, not part of the gap). Field `formation_divider_id` added to IFVG type with full lifecycle (constructor init, pre-render cleanup, mitigation cleanup, FIFO cleanup).

**Files changed:**
- `src/IFVG_Indicator.pine`:
  - Type `IFVG`: added `line formation_divider_id`
  - Input section: added `i_show_formation_divider` toggle
  - `cleanup_ifvg_array`: added `formation_divider_id` deletion
  - `merge_with_existing_fvg`: replaced three-piece scan with combined-span scan
  - Both `IFVG.new(...)` constructors: added `formation_divider_id = na`
  - LTF mitigation cleanup: added `formation_divider_id` deletion + reset
  - Pre-render cleanup: added `formation_divider_id` deletion + reset
  - `render_ifvg_boxes`: draw vertical dotted line at `inversion_bar` when toggle on
