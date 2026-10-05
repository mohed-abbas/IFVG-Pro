---
title: Automatic swing detection (Option D)
date: 2026-10-05
status: implemented and verified 2026-10-05
replaces: i_swing_lookback input (fixed 5-bar pivot)
---

# Automatic swing detection — Option D (3-candle candidate + ATR displacement)

## Why

`i_swing_lookback` (5 bars each side) did two jobs with one number — significance and
confirmation delay — and caused:
1. Slow confirmation (5 bars: 5 min on M1, 20 h on H4) — fresh highs can't be swept yet.
2. No volatility awareness — chop creates swings; clean highs with one slightly higher neighbour don't.
3. Exact double tops vanish (each is "not higher" than the other).

The user wants no lookback settings (non-technical traders). A timeframe table was rejected
because bar counts are already timeframe-invariant; what differs is noise/volatility.

## Rule

- **Candidate (ICT 3-candle swing):** swing high at [1] when `high[1] > high[2]` and
  `high[1] >= high[0]` (on equal highs the FIRST one is the candidate). Lows mirrored.
- **Confirm:** a candidate high becomes a swing when a candle closes at or below
  `high - SWING_CONFIRM_ATR × ATR` (internal constant 1.0) before any candle trades above it.
- **Cancel:** a candidate high is discarded when a later candle's high exceeds it.
- Equal highs do not cancel each other, so a double top yields two swings → EQH logic pairs them.
- Pending candidates per side capped at SWING_PENDING_MAX (20), FIFO.
- `create_internal_levels()` turns every newly confirmed swing into an ITH/ITL (several can
  confirm on the same candle).

## Scope

Chart timeframe only. PD swing lookback (`i_pd_swing_lookback`) is a separate later step that
reuses this rule once it is proven on charts.

## Expected chart changes

Downstream everything moves: ITH/ITL positions and count, EQH/EQL, BE levels, sweep credit,
grades. Expect fewer levels in lower-timeframe chop and faster confirmation in strong moves.
