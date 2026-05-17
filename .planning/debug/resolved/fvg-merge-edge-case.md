---
slug: fvg-merge-edge-case
status: resolved
trigger: |
  User reports the opposite-color FVG merge fix (commit 23c84e7) appears to fail
  again on retest. Screenshot 7 shows a single large IFVG zone with mixed-color
  candles visible inside the box. User says "there are several similar cases."
  User's ATR settings: i_fvg_min_size_mult=0.1, i_fvg_atr_period=14.
created: 2026-05-17T19:00:00Z
updated: 2026-05-17T19:35:00Z
files_changed:
  - src/IFVG_Indicator.pine
prior_session: .planning/debug/resolved/fvg-merge-fix-not-applied.md
related_commits:
  - 23c84e7 (the original merge fix — now extended by this session)
---

# Debug: FVG merge fix edge case — empty scan range + uncovered displacement candles

## Symptoms

**Expected behavior:** With the opposite-color merge scan in place at src/IFVG_Indicator.pine:548-563, two same-direction FVGs separated by ANY opposite-color candle should NOT merge.

**Actual behavior (per user):** Multiple test cases show a single large IFVG box that visually spans candles of mixed colors. User has retested after the fix and the bug recurs in similar cases.

**User config:**
- `i_fvg_min_size_mult = 0.1` (very permissive — accepts FVGs as small as 0.1 × ATR)
- `i_fvg_atr_period = 14`

**Reference screenshot:** `/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/7.png`

**Prior session:** `.planning/debug/resolved/fvg-merge-fix-not-applied.md`

## Hypotheses (priority order)

### H1 (HIGH) — Real bug: empty scan range merges adjacent FVGs unconditionally
**CONFIRMED.** See Evidence section.

### H2 (MEDIUM) — Same as prior session: HTF IFVG misinterpretation
**ELIMINATED.** Screenshot inspection: gray-filled box, NO dashed colored border at top/bottom, label reads "IFVG" (not "[TF] IFVG SHORT/LONG"). This is an LTF IFVG.

### H3 (LOW) — Scan checks wrong candles via offset arithmetic
**ELIMINATED.** `merge_with_existing_fvg` is called immediately after `detect_fvg()` (line 2781), at which point `bar_index == new_fvg.end_bar`. So `offset = bar_index - k = new_fvg.end_bar - k`. Pine's `close[0]` = current bar = end_bar, `close[1]` = end_bar - 1, etc. Offset math is correct.

## Evidence

- timestamp: 2026-05-17T19:25:00Z
  source: Screenshot /Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/7.png
  observation: Gray-filled box without dashed colored top/bottom border, label "IFVG", label "A SELL" on its SL line — confirms LTF bearish IFVG. Mixed-color candles (clearly blue bullish bars) visible inside what should be a continuous bearish displacement. Rules out H2.

- timestamp: 2026-05-17T19:26:00Z
  source: src/IFVG_Indicator.pine:538-580 (merge_with_existing_fvg) and :625-661 (detect_fvg)
  observation: `scan_from = existing.end_bar + 1`, `scan_to = new_fvg.start_bar - 1 = new_fvg.end_bar - 3`. For bar_distance N = (new.end_bar - existing.end_bar):
    - N=1: scan_to = existing.end_bar - 2, scan_from = existing.end_bar + 1 → EMPTY range → merge proceeds unconditionally
    - N=2: scan_to = existing.end_bar - 1 → EMPTY
    - N=3: 1-bar scan
    - N=4: 2-bar scan
    - N=5: 3-bar scan
  With min_size_mult=0.1, FVGs form frequently at adjacent bars (N=1, N=2). The opposite-color guard never runs for those.

- timestamp: 2026-05-17T19:27:00Z
  source: src/IFVG_Indicator.pine:625-661 (detect_fvg)
  observation: A 3-candle FVG's middle candle at `bar_index - 1` (= `end_bar - 1` = `start_bar + 1`) is the displacement bar. The current merge scan strictly excludes both FVGs' middle candles. So even when scan range is non-empty, an opposite-color middle candle of EITHER FVG is never checked. A "bullish" FVG whose middle candle is actually red (formed via wick alignment: low[0] > high[2] can still hold with a red middle candle) merges with a prior bullish FVG.

- timestamp: 2026-05-17T19:30:00Z
  source: src/IFVG_Indicator.pine:563-587 (after fix applied)
  observation: Option A applied. Two new guarded checks added after the original scan loop, examining the displacement (middle) candle of BOTH the new FVG (`new_fvg.end_bar - 1`) and the existing FVG (`existing.end_bar - 1`). Both guarded by `offset >= 0` to stay safe near chart start. Pine v6 syntax verified: no blank lines in blocks, no trailing operators, no multi-line and/or expressions.

## Eliminated

- H2 (HTF misinterpretation): box style and label confirm LTF.
- H3 (off-by-one offset math): verified correct.

## Resolution

**Root cause:** The original opposite-color merge scan introduced in commit 23c84e7 only inspects candles in the half-open range strictly between the two FVGs' 3-candle windows (`[existing.end_bar + 1, new_fvg.end_bar - 3]`). For adjacent FVGs (`bar_distance` 1 or 2) the range is empty, so the merge always proceeds without any color check. Additionally, neither FVG's own middle/displacement candle is ever inspected, so an FVG that formed via wick alignment with an opposite-color middle candle could still merge with a same-direction neighbour. With the user's permissive `i_fvg_min_size_mult = 0.1`, both conditions occur frequently in volatile sessions and produce oversized merged IFVGs that distort SL distance and grading.

**Fix:** Extended `merge_with_existing_fvg` (src/IFVG_Indicator.pine:563-587) to additionally examine the displacement (middle) candle of the new FVG (`new_fvg.end_bar - 1`) and the existing FVG (`existing.end_bar - 1`). Both checks are guarded by `offset >= 0` for chart-start safety. With these two extra checks, any opposite-color displacement candle on either side now correctly blocks the merge — closing the empty-scan-range gap for adjacent FVGs and the uncovered-displacement gap for all distances.

**Verification:** Pine v6 syntax sanity-checked (no blank lines inside if/for bodies, no trailing operators, no multi-line and/or expressions, all int() casts intact). User must visually re-verify on the original problem chart by reapplying the indicator after pulling the new commit.
