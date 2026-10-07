---
title: FVG merge rule — opposite-color candle decision record
date: 2026-05-17
context: exploration session on FVG merge behavior
related_todo: .planning/todos/pending/tighten-fvg-merge-opposite-color-break.md
related_code: src/IFVG_Indicator.pine:538 (merge_with_existing_fvg)
---

# FVG merge rule — opposite-color candle decision record

## Why this exists

The existing merge rule in `merge_with_existing_fvg()` is purely temporal: any same-direction active FVG within 5 bars is absorbed into the new one (top/bottom expanded to encompass both, `end_bar` extended). It does not test whether the intervening price action actually continued the impulse — only that detection happened recently.

In practice this produces oversized FVG zones across visible counter-direction candles. Once such a zone inverts into an IFVG, the stop-loss derived from the merged top/bottom is far wider than the lower-gap-only stop would have been, gutting the risk-to-reward ratio of otherwise valid setups. The chart inspected on 2026-05-17 showed a bullish cluster with two red doji-ish candles between the gap groups merged into one large zone — exactly the failure mode being addressed.

## The decision

A merge is **blocked** if any opposite-color candle exists strictly between the two FVGs' 3-candle windows.

- Bullish FVG merge: a red bar (`close < open`) anywhere in `[existing.end_bar+1, new.start_bar-1]` blocks the merge.
- Bearish FVG merge: a green bar (`close > open`) does the same.
- Dojis (`close == open`) are neutral — they do not block the merge.
- All other current guards (same direction, status == "active", bar_distance ≤ 5) remain.

## Rejected alternatives

These were considered during exploration and rejected:

| Option | Why rejected |
|--------|--------------|
| **2+ consecutive opposite candles** | Too lenient. A single counter-direction body close *is* a break in ICT methodology — it shows price didn't continue the imbalance leg, so merging across it falsifies the zone. |
| **Body retraces meaningfully into prior FVG** | Conceptually sound but adds two layers of judgment (color + retracement depth) and a new ATR-based threshold. The user explicitly chose simpler/stricter; opposite color alone is already a strong enough filter. |
| **Any non-same-direction candle (incl. doji)** | Doji bars are common at micro-pauses inside strong impulses (especially on low-volume bars). Treating them as breaks would over-fragment FVGs and re-introduce noise that the merge logic was originally trying to suppress. |
| **Body close back inside the prior FVG zone** | Stricter and more "ICT correct" — but harder to reason about, and requires checking each intervening candle's close against `existing.bottom/existing.top`. May be a future refinement, but for now the opposite-color rule captures most of the same setups. |

## Rule choice: "any single opposite candle"

User selected the strictest available option on first prompt. Rationale captured:
- Deterministic, easy to read in code, easy to debug on chart.
- Matches the visual intuition ("I see a red candle in a bullish impulse → that's a break") without requiring threshold tuning.
- Risk of over-splitting is acceptable given the downstream singularity scoring at src/IFVG_Indicator.pine:1528, which independently penalizes overlapping FVGs — meaning false splits get caught at grading time anyway.

## Implications

- Expect more FVG entries in `g_fvg_array` per bar of chart history. `i_max_fvgs` default of 3 may become tight — consider bumping the default to 5+ once the new merge rule is verified.
- Singularity check (src/IFVG_Indicator.pine:1528, `is_fvg_singular`) may now flag more clusters as non-singular because the merge no longer collapses them. The 2 scoring functions are coupled — flagged as a research question (see `.planning/research/questions.md`).
- HTF FVG handling is unaffected — HTF uses `htf_fvg_exists()` (existence dedup), not merge. No code change needed there.
- No `request.security()` budget impact.

## Evidence

Source: chart visual reviewed during 2026-05-17 exploration session. Pattern: bullish FVG cluster on intraday chart, two red doji-ish candles between gap-groups, merge produced a single oversized box extending up to the upper red horizontal line in the screenshot. The IFVG that should have formed from the lower gap with a tight stop did not appear.

## When to revisit

- If post-fix charts show legitimate continuous impulses getting split because their middle bar happened to be a small red candle on volume noise → consider promoting to "body retraces into prior FVG" rule.
- If singularity scoring starts dropping too many newly-split clusters to score 0 → revisit the ATR×0.1 overlap tolerance in `is_fvg_singular` together with this rule.

## Status (2026-10-07)

Superseded by the Series of Gaps rule (docs/ISSUES.md Issue 7): same-direction gaps chain while candles between their windows are the move's color; the setup fires once on a close through all of them. The merge function still runs at detection; its removal waits on the series grading decision (Issue 8).
