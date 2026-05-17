---
slug: fvg-merge-fix-not-applied
status: root_caused
trigger: |
  User screenshot shows a single large IFVG zone visibly spanning multiple bars
  of mixed colors. User believes the opposite-color FVG merge fix (commit 23c84e7,
  src/IFVG_Indicator.pine:548-563) is not working — that "FVG has multiple
  different color candles but still considered as a single FVG."
created: 2026-05-17T18:30:00Z
updated: 2026-05-17T18:45:00Z
files_changed: []
---

# Debug: FVG merge fix appears not applied (or user misinterpretation of box rendering)

## Symptoms

**Expected behavior:** When two same-direction FVGs form with an opposite-color candle between them, the merge_with_existing_fvg() opposite-color scan at lines 548-563 of src/IFVG_Indicator.pine should block the merge, producing two distinct FVG entries instead of one large merged box.

**Actual behavior (per user):** Chart shows a single large IFVG box that "visibly contains multiple different color candles" in its span. User interprets this as the merge fix being inactive.

**Error messages:** None — visual interpretation issue.

**Timeline:** Reported 2026-05-17 after pasting the post-fix indicator into TradingView.

**Reproduction:** Load src/IFVG_Indicator.pine on a 1H or 15m chart with significant FVG formations. Observe an IFVG that has been "live" for many bars — the user expects the box to be only as wide as the 3-candle FVG formation; the box is in fact much wider.

Reference screenshot: `/Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/6.png`

## Suspect Hypotheses (in priority order)

### Hypothesis A: User misinterpretation of LTF box rendering after the live-zone anchoring fix
**Status:** Partially confirmed — the same "live zone" visualization principle applies, but the box in the screenshot is HTF, not LTF.

### Hypothesis B (CONFIRMED): The box in the screenshot is an HTF IFVG; HTF detection has no merge logic
**Status:** CONFIRMED via screenshot border-style inspection and code review.

### Hypothesis C: Fix is present in source file but somehow not active in TradingView
**Status:** Eliminated. Merge fix code verified present at lines 548-563. Not relevant to user's screenshot since the box is HTF.

## Current Focus

- hypothesis: B confirmed.
- test: Done — inspected screenshot, confirmed HTF border style (thin red dashed) and verified no merge logic exists in HTF detection path.
- next_action: Explain finding to user. No code fix needed — behavior is correct by design. Decision pending on whether to add opposite-color scan to HTF detection (deferred; see Resolution).

## Evidence

- timestamp: 2026-05-17T18:40:00Z
  source: src/IFVG_Indicator.pine:2240-2243
  finding: LTF IFVG box uses `border_color = color.new(color.gray, 100)` (fully transparent) and `border_width = 0`. NO visible border in any LTF rendering.

- timestamp: 2026-05-17T18:41:00Z
  source: src/IFVG_Indicator.pine:2443, 2455-2457
  finding: HTF IFVG box uses `border_color = ifvg.is_bullish ? i_bullish_color : i_bearish_color` (red `#F23645` for bearish), `border_width = i_htf_border_width`, `border_style = line.style_dashed`. This produces a visible thin red dashed border for bearish HTF IFVGs.

- timestamp: 2026-05-17T18:42:00Z
  source: screenshot inspection at /Users/murx/.claude/image-cache/e11f6b32-0bce-463c-b94f-8196a8969a1c/6.png
  finding: Gray IFVG box has thin red border lines at top and bottom edges. Matches HTF bearish IFVG render. The "A SELL" label below at line.style_solid red is the SL line tied to this IFVG's grade. Below the IFVG is a pale pink-shaded discount zone (PD-zone fill).

- timestamp: 2026-05-17T18:43:00Z
  source: src/IFVG_Indicator.pine:2778-2784 (LTF) vs 2789-2799 (HTF)
  finding: LTF FVG detection path calls `merge_with_existing_fvg(new_fvg)` which contains the opposite-color scan fix. HTF FVG detection path uses `htf_fvg_exists()` only for dedup — there is NO merging logic for HTF, so the opposite-color scan does not run for HTF FVGs.

- timestamp: 2026-05-17T18:44:00Z
  source: screenshot leftmost edge of gray box
  finding: The left edge of the gray IFVG box visibly anchors at strong bearish displacement candles (red bodies, one with long upper wick around the swing high). This is the 3-HTF-bar formation that produced the HTF FVG. Mixed-color candles in the rest of the box are post-formation LTF candles playing through the live HTF zone — NOT part of the FVG.

## Eliminated

- Hypothesis C (fix not actually in file): merge code verified present at lines 548-563.
- Hypothesis A pure form (LTF + misinterpretation): partially eliminated by the visible HTF border style — but the same "live zone covers post-formation candles" misinterpretation principle still applies, just to HTF rather than LTF.

## Resolution

### Root Cause

The IFVG box in the screenshot is a **bearish HTF IFVG**, not an LTF IFVG. The opposite-color merge fix at src/IFVG_Indicator.pine:548-563 lives inside `merge_with_existing_fvg()`, which is called **only from the LTF detection path** (line 2781). HTF FVG detection (lines 2789-2799) uses `htf_fvg_exists()` for simple existence-dedup and has **no merging logic at all** — so there is nothing for the merge fix to "fail at" in this case.

What the user sees is one legitimate HTF FVG:
1. Detected across 3 HTF bars (visible at the left edge of the box: strong bearish displacement candles).
2. Right-edge projected forward to the current bar as a live-zone visualization (this is the intended behavior added in commits 659ae57 and c976911).
3. The mixed-color candles **inside the box span** are subsequent LTF price action playing through the live HTF zone — they are NOT part of the FVG formation. An HTF bar represents N LTF bars; viewing an HTF FVG from a lower-TF chart will naturally show that aggregation.

### Visual identification of LTF vs HTF IFVG

| Element | LTF IFVG | HTF IFVG |
|---|---|---|
| Border | None (`border_width=0`, transparent color) | Thin colored dashed (`line.style_dashed`, bullish_color or bearish_color) |
| Label | "IFVG" in subtle gray | `[1H] IFVG SHORT` (or LONG), colored to match border |
| Fill | gray @ `i_ifvg_box_opacity` | gray @ `i_htf_box_opacity` |

The screenshot box has visible thin red border lines → HTF bearish IFVG.

### Fix

**No code fix applied.** The behavior shown is correct by design.

### Optional follow-up (deferred — not blocking)

If desired, the same opposite-color scan logic could be added to HTF FVG detection — but it would require:
1. Adding `open` to the HTF `request.security` tuple for each timeframe (currently 14 tuple elements across 2 calls; adding `open` adds 2 more elements, well within the 40-call security budget).
2. Storing the per-HTF-bar `htf_open` and `htf_open_1`, `htf_open_2` values to compare across the 3 HTF bars between two detected FVGs.
3. Writing a parallel `merge_with_existing_htf_fvg()` that operates on HTF data.

In practice this is **unnecessary** for HTF because:
- HTF FVG detection already uses `htf_fvg_exists()` dedup, which prevents multiple identical-zone HTF FVGs from accumulating.
- Two distinct HTF FVGs (separated by mixed-direction HTF bars) would each pass the dedup check and be added as separate entries, since `htf_fvg_exists()` only filters by top/bottom price overlap — not bar proximity.
- The "merging across opposite color" failure mode that the LTF fix addresses simply cannot occur in HTF because there is no merging code path at all.

Decision: **Document this asymmetry and close the session.** Revisit only if the user identifies a real HTF case where two distinct same-direction HTF FVGs visibly merged into one box (which would require a different bug — not the merge fix's domain).

### Status

CLOSED — expected behavior, no fix needed.
