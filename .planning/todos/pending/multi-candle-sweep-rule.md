---
title: Decide on multi-candle sweep rule for check_setup_sweep()
date: 2026-10-05
priority: medium
area: src/IFVG_Indicator.pine (check_setup_sweep)
revisit: after swing rework (Option D) and before grading remodel (#8)
status: deferred — test first, then decide
---

# Multi-candle sweep rule

## Problem

Rule 2 of `check_setup_sweep()` requires the candle that first swept the level to be the extreme of the move. In a multi-candle raid, candle A pokes beyond the level first (and is marked swept), then candle B goes further and makes the real turn. Rule 2 rejects the sweep, so a textbook setup shows "Delivery only".

```
               ▲ B (real top)
        ▲ A    │
  ─ ─ ─ ┼ ─ ─ ─┼ ─ ─ ─   level (swept by A)
       ┃ ┃    ┃╲
                ▼ inversion   → currently NOT credited
```

Observed: "A- SELL" setup, 2026-10-05 (user screenshot). Still to confirm: whether the level showed ✗, ⊘ or no line.

## Proposed rule (not applied)

A sweep counts for the setup if:
1. the level was swept inside the FVG → inversion window;
2. the move's extreme is at or after the sweep bar;
3. no candle closed beyond the level from the sweep bar to the inversion.

## Why deferred

- The current behaviour fails safe: it misses real sweeps but never adds false ones.
- The swing rework (Option D) changes which ITH/ITL exist, so evaluate afterwards.
- The user is skeptical; collect examples first.

## Evidence to collect while testing

- Missed real sweeps (multi-candle raids) — screenshot + label state.
- Cases where the proposed rule would add a sweep that did not cause the turn.

## Status (2026-10-06)

Fix applied in `check_setup_sweep()` (Rules 2 and 3 as proposed). Awaiting live verification; see docs/ISSUES.md Issue 11.
