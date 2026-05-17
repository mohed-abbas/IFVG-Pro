---
phase: quick-260517-nlq
plan: 01
subsystem: src/IFVG_Indicator.pine — merge_with_existing_fvg()
tags: [fvg, merge, ict, pine-v6]
requires: []
provides:
  - "Opposite-color break filter on same-direction FVG merging"
affects:
  - "src/IFVG_Indicator.pine: merge_with_existing_fvg() (lines 538-580)"
tech_stack:
  added: []
  patterns:
    - "bar_index → historical-offset conversion (offset = bar_index - k) for OHLC lookback"
    - "Nested if blocks instead of continue/skip (Pine v6 parser hazard avoidance)"
key_files:
  created:
    - ".planning/quick/260517-nlq-implement-fvg-merge-fix-from-planning-to/260517-nlq-SUMMARY.md"
  modified:
    - "src/IFVG_Indicator.pine"
decisions:
  - "Apply opposite-color break per any single counter-direction body close in the strict-between range (decision: .planning/notes/fvg-merge-rule-decision.md, 2026-05-17)"
  - "Doji bars (close == open) treated as neutral — never break the merge"
metrics:
  duration_min: 4
  completed: 2026-05-17
---

# Quick 260517-nlq: Tighten FVG merge — opposite-color candle break

## One-liner

`merge_with_existing_fvg()` now scans the bars strictly between two same-direction FVGs and blocks the merge if any opposite-color candle exists in that range, restoring tighter ICT-correct IFVG setups without changing grading, IFVG creation, singularity, or HTF code paths.

## Scope of change

- **File**: `src/IFVG_Indicator.pine`
- **Function**: `merge_with_existing_fvg(FVG new_fvg)`
- **Pre-edit lines**: 538–564 (27 lines)
- **Post-edit lines**: 538–580 (43 lines)
- **Net delta**: +32 / −16

No other files, functions, or input groups were touched. No new `request.security()` calls. No new user inputs. No changes to grading, IFVG creation, singularity scoring, dashboard, rendering, or HTF code paths.

## Before / after

### Before (lines 547–563)

```pine
                if bar_distance <= 5
                    // Merge: extend existing FVG to encompass new one
                    float combined_top = math.max(existing.top, new_fvg.top)
                    float combined_bottom = math.min(existing.bottom, new_fvg.bottom)
                    existing.top := combined_top
                    existing.bottom := combined_bottom
                    existing.mid := (combined_top + combined_bottom) / 2
                    existing.end_bar := int(math.max(existing.end_bar, new_fvg.end_bar))
                    // Redraw the box to reflect combined zone
                    if not na(existing.box_id)
                        box.delete(existing.box_id)
                        existing.box_id := na
                    if not na(existing.label_id)
                        label.delete(existing.label_id)
                        existing.label_id := na
                    merged := true
                    break
```

### After (lines 547–579)

```pine
                if bar_distance <= 5
                    // Opposite-color scan: block merge when any opposite-color
                    // candle exists strictly between the two FVGs' 3-candle windows.
                    // Dojis (close == open) are neutral and never block.
                    bool opposite_found = false
                    int scan_from = existing.end_bar + 1
                    int scan_to = new_fvg.start_bar - 1
                    if scan_to >= scan_from
                        for k = scan_from to scan_to
                            int offset = bar_index - k
                            if new_fvg.is_bullish
                                if close[offset] < open[offset]
                                    opposite_found := true
                            if not new_fvg.is_bullish
                                if close[offset] > open[offset]
                                    opposite_found := true
                    if not opposite_found
                        // Merge: extend existing FVG to encompass new one
                        float combined_top = math.max(existing.top, new_fvg.top)
                        float combined_bottom = math.min(existing.bottom, new_fvg.bottom)
                        existing.top := combined_top
                        existing.bottom := combined_bottom
                        existing.mid := (combined_top + combined_bottom) / 2
                        existing.end_bar := int(math.max(existing.end_bar, new_fvg.end_bar))
                        // Redraw the box to reflect combined zone
                        if not na(existing.box_id)
                            box.delete(existing.box_id)
                            existing.box_id := na
                        if not na(existing.label_id)
                            label.delete(existing.label_id)
                            existing.label_id := na
                        merged := true
                        break
```

## Behavior matrix

| Scenario | Behavior |
|----------|----------|
| Two same-direction FVGs within 5 bars, no bar between (adjacent) | Merge proceeds (scan range empty: `scan_to < scan_from`) — no regression |
| Two same-direction FVGs within 5 bars, all intervening bars are dojis | Merge proceeds — dojis are neutral |
| Two bullish FVGs within 5 bars, ≥1 red bar (`close < open`) between them | Merge blocked, new FVG pushed as separate entry |
| Two bearish FVGs within 5 bars, ≥1 green bar (`close > open`) between them | Merge blocked, new FVG pushed as separate entry |
| `existing.is_bullish != new_fvg.is_bullish` | Untouched — pre-existing guard rejects the candidate before the new scan runs |
| `existing.status != "active"` | Untouched — pre-existing guard rejects the candidate before the new scan runs |
| `bar_distance > 5` | Untouched — pre-existing guard rejects the candidate before the new scan runs |

When `opposite_found` is true the inner `if bar_distance <= 5` block does NOT `break`, so the outer `for j` loop continues scanning older entries in `g_fvg_array`. In practice the 5-bar distance gate keeps this from changing observed behavior, but the loop structure is preserved as the plan specified.

## Pine Script v6 syntax compliance

All rules from `./CLAUDE.md` honored in the new block:

1. **No blank lines inside `for` or `if` bodies** — verified manually around lines 547–579.
2. **No multi-line `and`/`or`** — boolean checks are split into nested `if` statements (Rule 4 preference).
3. **`int()` casts on `math.abs()` / `math.max()`** — pre-existing casts on `bar_distance` and `existing.end_bar` retained unchanged.
4. **Nested `if` preferred over `continue`** — bullish/bearish branches are each `if … if …` (Rule 4).
5. **No line ends with bare operator/`=`** — verified by `awk '/merge_with_existing_fvg/,/^merged$/' | grep -nE '=[[:space:]]*$' | grep -v //` → 0 matches.
6. **Operator-at-end-of-line for continuations** — no line continuation introduced in the new block.

## Verification

### Automated (static grep checks)

| Check | Expected | Actual |
|-------|----------|--------|
| `opposite_found` references (non-comment) | ≥ 3 | 4 (1 declaration + 2 assignments + 1 guard) |
| `merge_with_existing_fvg` occurrences | ≥ 2 (def + call site) | 2 (line 538 definition, line 2777 call in `detect_fvg` series caller) |
| `scan_from` occurrences | ≥ 2 | 3 (assignment + 2 uses) |
| `scan_to` occurrences | ≥ 2 | 3 (assignment + 2 uses) |
| `bar_index - k` occurrences | ≥ 1 | 1 |
| `if not opposite_found` occurrences | exactly 1 | 1 |
| Trailing `=` lines in function | 0 | 0 |

All checks pass.

### Manual (TradingView visual regression) — PENDING

Task 2 of the plan is a `checkpoint:human-verify` that requires the user to paste `src/IFVG_Indicator.pine` into TradingView, compile, and visually verify against the acceptance criteria from `.planning/todos/pending/tighten-fvg-merge-opposite-color-break.md`:

1. Bullish FVG cluster with red candle between gap groups now splits into 2+ boxes (was 1 oversized box pre-fix).
2. Continuous bullish impulse with no red between same-direction gaps still merges into one box.
3. Doji-only between gaps still merges (3-bar test: bullish gap, doji, bullish gap).
4. Symmetric bearish behavior — green bar breaks bearish merge.
5. No "end of line without line continuation" compile errors around `merge_with_existing_fvg`.
6. No collapse to zero of A+/A IFVG counts across historical sessions (some reclassification expected per decision record).

**Status**: Not blocking this execution — visual verification will happen when the user pastes the file into TradingView. Per execution constraints, this checkpoint is skipped for the autonomous run.

## Deviations from Plan

None. The plan executed exactly as written. Pine v6 syntax rules from `./CLAUDE.md` were honored. No auto-fixes or architectural changes were needed.

## Commit

| Hash | Branch | Message |
|------|--------|---------|
| 23c84e7 | worktree-agent-a675f1cb0fca92f99 | Phase 4: block FVG merge across opposite-color candles |

## Self-Check: PASSED

Verified:
- `src/IFVG_Indicator.pine` modified in worktree (file exists, lines 538–580 contain new logic).
- Commit `23c84e7` exists on the worktree branch (`git log` confirms).
- No trailing `=` lines, no blank-line issues inside `for`/`if` bodies in the new block.
- All structural grep checks from plan `<verify>` block return expected counts.
