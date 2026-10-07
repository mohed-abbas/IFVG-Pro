---
title: Tighten FVG merge — opposite-color candle breaks the merge
date: 2026-05-17
priority: high
area: src/IFVG_Indicator.pine
relates_to: src/IFVG_Indicator.pine:538 (merge_with_existing_fvg)
companion_note: .planning/notes/fvg-merge-rule-decision.md
---

# Tighten FVG merge — opposite-color candle breaks the merge

## Problem

`merge_with_existing_fvg()` at src/IFVG_Indicator.pine:538 merges any same-direction active FVG within 5 bars, with no test for whether the intervening price action actually continued the impulse leg. In practice this absorbs gaps separated by clear counter-direction candles into a single oversized zone, destroying the smaller IFVG setups that would otherwise form with tight stops.

Visual evidence (chart inspection, 2026-05-17): a bullish FVG cluster with two red doji-ish candles between the gap groups was merged into one large zone whose IFVG carries a stop-loss several times wider than the lower-gap-only IFVG would have used. Risk-to-reward on the resulting setup is degraded.

## Rule change

In `merge_with_existing_fvg()`, after the `bar_distance <= 5` and same-direction guards already in place, add an opposite-color scan over the bars **strictly between** the two FVGs' 3-candle windows. If any opposite-color candle exists in that range, the new FVG must be pushed as a separate entry (do not merge).

### Precise definition

Let:
- `existing` = the same-direction active FVG already in `g_fvg_array`
- `new_fvg` = the freshly detected FVG passed to `merge_with_existing_fvg`
- check range = `[existing.end_bar + 1, new_fvg.start_bar - 1]` inclusive
- "opposite color" for a bullish merge candidate: a bar where `close[k] < open[k]` (red)
- "opposite color" for a bearish merge candidate: a bar where `close[k] > open[k]` (green/blue)

Dojis (`close == open`) are **neutral** — they do not break the merge.

If the check range is empty (FVGs are adjacent), the scan trivially passes → merge proceeds as today.

### Pseudocode

```
if existing.is_bullish == new_fvg.is_bullish and existing.status == "active":
    bar_distance = abs(new_fvg.end_bar - existing.end_bar)
    if bar_distance <= 5:
        opposite_found = false
        scan_from = existing.end_bar + 1
        scan_to   = new_fvg.start_bar - 1
        if scan_to >= scan_from:
            for k from scan_from to scan_to:
                offset = bar_index - k
                if new_fvg.is_bullish and close[offset] < open[offset]:
                    opposite_found := true
                if (not new_fvg.is_bullish) and close[offset] > open[offset]:
                    opposite_found := true
        if not opposite_found:
            # existing merge logic — extend top/bottom/end_bar, redraw box
            ...
            merged := true
return merged
```

Note: Pine Script accesses historical bars via offset from `bar_index`, so convert absolute `bar_index`-based positions to offsets when reading `open[k]` / `close[k]`.

## Acceptance criteria

1. On the chart inspected on 2026-05-17, the merged oversized FVG is replaced by 2+ separate FVGs; the lower gap-cluster yields its own IFVG with a tighter stop-loss when it inverts.
2. Two adjacent bullish gaps with no bar between them (or no opposite-color bar between them) still merge — no regression on tight continuous impulses.
3. Two same-direction gaps separated by ≥1 opposite-color candle within 5 bars no longer merge — visible as two distinct boxes on chart.
4. Bearish-side behavior is symmetric — green candle breaks bearish merge.
5. Doji bars (close == open) do not break merge — verified by constructing a 3-bar sequence: bullish gap, doji, bullish gap.
6. All existing Pine v6 rules respected (no blank lines in `for` body, no trailing `=`, `int()` casts on `math.abs` results).
7. No new `request.security()` calls introduced — same budget.

## Out of scope

- Changing the 5-bar window or the singularity check at src/IFVG_Indicator.pine:1528 (tracked separately in `.planning/research/questions.md`).
- Applying this to HTF FVG merging (HTF doesn't currently merge — different code path).
- Adding a user-configurable toggle. The opposite-color break is the correct default per ICT methodology; no input needed.

## Verification

Visual regression on TradingView using NQ1!/ES1!/BTCUSD 15m and 1H charts:
- Identify pre-fix clusters where merge happened across red candles.
- Apply fix; confirm those clusters now split.
- Confirm continuous impulses (no opposite candles) still merge.
- Check that A+/A grade distribution doesn't collapse — splitting may expose more singular FVGs, which is expected and desirable.

## Status (2026-10-07)

Done: implemented in `23c84e7`, `817ed9f`, `140634e` (combined-span opposite-color scan). Superseded for setup logic by the Series of Gaps rule (docs/ISSUES.md Issue 7). Removing `merge_with_existing_fvg()` entirely is on hold until the series grading decision (Issue 8).
