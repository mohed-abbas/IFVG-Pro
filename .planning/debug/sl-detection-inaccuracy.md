---
status: awaiting_human_verify
trigger: "SL detection places SL at raw swing point instead of most recent ITH/ITL"
created: 2026-04-12T00:00:00Z
updated: 2026-04-12T00:00:00Z
---

## Current Focus

hypothesis: SL calculation uses find_previous_swing_low/high (raw swing points from g_swing_lows/g_swing_highs) instead of searching g_liquidity_array for the most recent ITL/ITH before the FVG's start_bar
test: Read check_inversions() SL logic and find_previous_swing_* functions
expecting: Confirmed that SL references swing arrays not liquidity array
next_action: Write find_previous_itl() and find_previous_ith() functions, then update check_inversions() to use them

## Symptoms

expected: For bullish IFVG, SL below the most recent ITL before the IFVG formed. For bearish IFVG, SL above the most recent ITH before the IFVG formed.
actual: SL uses find_previous_swing_low/high which returns raw swing points, not ITH/ITL liquidity levels
errors: No runtime errors — logic bug
reproduction: Apply indicator, compare SL lines against ITH/ITL levels
started: Since initial implementation

## Eliminated

(none)

## Evidence

- timestamp: 2026-04-12
  checked: check_inversions() lines 1470-1494
  found: SL for bullish uses find_previous_swing_low(fvg.start_bar), SL for bearish uses find_previous_swing_high(fvg.start_bar). These search g_swing_lows/g_swing_highs arrays (raw swing points).
  implication: ROOT CAUSE CONFIRMED - SL should search g_liquidity_array for ITL/ITH entries instead

- timestamp: 2026-04-12
  checked: find_previous_swing_low/high (lines 1177-1209)
  found: Functions iterate g_swing_highs/g_swing_lows to find most recent swing before a bar index
  implication: These return any swing point, not specifically ITH/ITL liquidity levels

- timestamp: 2026-04-12
  checked: Liquidity type (lines 67-79)
  found: Has liq_type field ("ITH", "ITL", "EQH", "EQL"), bar_idx, level, is_valid, is_swept
  implication: Can search g_liquidity_array filtering by liq_type == "ITL" or "ITH"

## Resolution

root_cause: SL calculation in check_inversions() calls find_previous_swing_low/high which searches raw swing point arrays (g_swing_lows/g_swing_highs) instead of searching g_liquidity_array for the most recent ITL/ITH level before the FVG's start_bar
fix: Created find_previous_itl() and find_previous_ith() functions that search g_liquidity_array for ITL/ITH levels before a given bar. Updated check_inversions() to call these instead of find_previous_swing_low/high. Both functions fall back to raw swing points if no ITH/ITL exists. Updated tooltip and section comments.
verification: awaiting human verification on TradingView chart
files_changed: [src/IFVG_Indicator.pine]
