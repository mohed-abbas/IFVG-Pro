---
status: testing
phase: 02-pd-zone-detection-grading-integration
source:
  - 02-01-SUMMARY.md
  - 02-02-SUMMARY.md
  - 02-03-SUMMARY.md
started: 2026-04-14T00:00:00Z
updated: 2026-04-14T00:00:00Z
---

## Current Test

number: 1
name: Pine Editor Compile Gate
expected: |
  Paste src/IFVG_Indicator.pine into the TradingView Pine Editor (must fully remove and re-add the indicator on the chart to pick up new input defaults). It compiles with zero errors and loads onto the chart.
awaiting: user response

## Tests

### 1. Pine Editor Compile Gate
expected: Paste src/IFVG_Indicator.pine into the TradingView Pine Editor. It compiles with zero errors and loads onto the chart. (Remove/re-add the indicator to pick up new input defaults.)
result: issue
reported: "Error on bar 0: bad session entry - 60 at #main():2764"
severity: blocker
root_cause: "time() args reversed: `time(\"\", i_pd_timeframe)` treats empty string as timeframe and i_pd_timeframe (e.g. '60') as session string. Correct signature is time(timeframe, [session]) so it should be `time(i_pd_timeframe)` (single arg)."
fix: "Replace `time(\"\", i_pd_timeframe)` with `time(i_pd_timeframe)` at src/IFVG_Indicator.pine:2762 and :2764."

### 2. PD Dealing Range Lines + Labels
expected: On a chart where chart TF < PD TF (e.g., NQ1! 15m with PD=D), three dashed lines appear spanning the current dealing range — swing-high at the top, EQ in the middle, swing-low at the bottom. Right-edge labels read "1 (price)", "0.5 (price)", "0 (price)" with the live price values.
result: [pending]

### 3. Range Rotation on New Swing
expected: When a new HTF swing confirms (new ITH or ITL), the old PD lines/labels disappear cleanly and a new range is drawn. No ghost lines from the previous range remain.

result: [pending]

### 4. Dashboard PD Zone + Range %
expected: Dashboard shows two new rows near the bottom. "PD Zone:" displays PREMIUM (red), DISCOUNT (green), or EQ (yellow) based on current price. "Range %:" shows an integer 0–100 (white). When no valid range exists, both rows show "—" in gray.
result: [pending]

### 5. IFVG Tooltip pd_zone Populated
expected: Hover any LTF IFVG label. Tooltip's pd_zone field shows "premium", "discount", or "equilibrium" (not universally "neutral"). HTF IFVGs may still show "neutral" — that's intentional.
result: [pending]

### 6. Grade Distribution Shift (A+ unlocked)
expected: Compared to pre-Phase-2 charts, you now see A+ grades appearing on IFVGs that are in the correct zone (bullish IFVG in discount, bearish IFVG in premium) with sweep + strong momentum. Grade distribution is no longer capped at A.
result: [pending]

### 7. Optional Zone Fills Toggle
expected: Toggling "Show Zone Fills" on renders very subtle colored fills between EQ and swing high (premium, bearish color) and between EQ and swing low (discount, bullish color). Toggling off cleanly removes both fills.
result: [pending]

### 8. Optional OTE Band Toggle
expected: Toggling "Show OTE Band" on renders two dotted purple lines at 62% and 79% of the range with a subtle purple fill between them. Toggling off cleanly removes the band.
result: [pending]

### 9. TF Fallback (chart TF >= PD TF)
expected: On a chart where chart TF >= PD TF (e.g., put chart on Daily with PD=D, or PD=60 and chart=60), the PD feature stays active — it falls back to the chart-TF liquidity array. PD lines still appear (derived from chart-TF ITH/ITL), no crash, no blank dashboard.
result: [pending]

## Summary

total: 9
passed: 0
issues: 0
pending: 9
skipped: 0

## Gaps

[none yet]
