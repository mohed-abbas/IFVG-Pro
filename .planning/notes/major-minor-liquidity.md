---
title: Strong / weak liquidity (structure-based) and drawing
date: 2026-10-06
status: implemented and verified 2026-10-06 (Option B)
---

# Strong / weak liquidity drawing

## Why

After the swing rework (Option D, `fe617ca`) only the 3 nearest live levels per side were
drawn. In trends the nearest levels are small pullback highs/lows, so the high that started
the whole leg (the most important level) was hidden while still live in memory.

## Attempt 1 — rejected (ATR distance, "major")

Major = price moved ≥ 3 ATR away at any time since the swing. Verified on TradingView:
85 of 87 live levels became major — distance grows with time, so the label meant nothing.
A first-leg ATR variant was also rejected: with Option D a 1-ATR bounce forms a swing and
cuts a big leg in two.

## Rule (Option B — ICT/SMC strong vs weak)

- **Strong High:** an ITH after which price CLOSES below the low the rally came from
  (most recent confirmed swing low before the ITH) before a newer swing high is confirmed
  → it caused a break of structure (protected high).
- **Weak high (shown as "ITH"):** a newer swing high confirms first, or the level is
  swept/broken first.
- **Strong Low / weak low ("ITL"):** mirrored (close above the high the drop came from).
- Decided once, during that leg; never changes. No ATR, no setting.
- Breaks between the swing candle and its confirmation count (checked at creation).
- **Drawing per side:** 3 nearest live strong + 3 nearest live weak (weak includes EQH/EQL).
- **Style:** strong = line width 2, label "Strong High" / "Strong Low".
- Drawing only — no effect on sweeps, DOL, SL or grading.
