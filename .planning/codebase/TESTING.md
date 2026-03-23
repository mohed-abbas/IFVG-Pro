# Testing Patterns

**Analysis Date:** 2026-03-23

## Test Framework

**Runner:** None - Pine Script has no automated testing framework.

**Assertion Library:** Not applicable.

**Run Commands:**
```
N/A - No automated test toolchain exists for Pine Script.
```

Pine Script v6 is a domain-specific language that runs exclusively inside the TradingView platform. There is no local execution environment, no REPL, no unit test runner, and no way to simulate bar-by-bar execution outside TradingView. All validation is manual and visual.

## Deployment & Validation Workflow

### How to Deploy Changes

1. Open TradingView in a browser
2. Navigate to the Pine Script Editor (bottom panel)
3. Copy the entire contents of `src/IFVG_Indicator.pine`
4. Paste into the Pine Script Editor, replacing all existing code
5. Click "Save" (or Ctrl+S)
6. Click "Add to chart" (first time) or the script auto-reloads on save
7. Observe the chart for compilation errors (shown in the editor console)

### Compilation Check

TradingView's Pine Script compiler provides:
- **Syntax errors** with line numbers (shown in the editor console)
- **Runtime errors** displayed as a red banner on the chart (e.g., array index out of bounds, division by zero)
- **Memory/performance warnings** if the script exceeds TradingView limits

If the script compiles but produces a runtime error, it will show on the chart as a red error banner. Check the browser console or the Pine Script editor output for details.

## Validation Checklist by Change Type

### Visual Element Changes (boxes, lines, labels)

**What to verify:**
- [ ] Elements appear on the chart at correct price levels
- [ ] Colors match expected values (bullish = teal `#089981`, bearish = red `#F23645`)
- [ ] Opacity/transparency looks correct (not fully opaque, not invisible)
- [ ] Labels display correct text with proper formatting
- [ ] Border styles match configuration (solid, dashed, dotted)
- [ ] Elements extend to the correct right edge (`bar_index + i_extend_bars`)
- [ ] Old drawings are cleaned up (no ghost boxes/lines from previous bars)
- [ ] Toggle inputs (`i_show_*`) properly hide/show elements
- [ ] Elements do not exceed TradingView's `max_boxes_count` / `max_lines_count` / `max_labels_count` (500 each)

**How to verify:**
1. Load the indicator on a chart with known FVG formations
2. Toggle each visibility setting on/off in the indicator settings
3. Scroll through historical data to verify cleanup works
4. Check that the chart does not show a "too many drawings" error

### FVG/IFVG Detection Logic Changes

**What to verify:**
- [ ] FVGs appear at correct 3-candle gap locations
- [ ] Minimum size filter works (tiny gaps should be filtered)
- [ ] Bullish FVGs: `low[0] > high[2]` gap exists
- [ ] Bearish FVGs: `low[2] > high[0]` gap exists
- [ ] Inversions trigger on body close through (not wicks)
- [ ] IFVG direction is inverted from source FVG direction
- [ ] Detection only fires on confirmed bars (no repainting)
- [ ] Mitigated IFVGs are removed from the chart

**How to verify:**
1. Find a known FVG on the chart and confirm the indicator detects it
2. Manually verify the 3-candle pattern matches the box boundaries
3. Wait for a bar to close through an FVG and verify inversion triggers
4. Switch to a replay bar-by-bar and confirm no future data leaks
5. Compare ATR-based filtering by adjusting `i_fvg_min_size_mult`

### Liquidity Detection Changes (EQH/EQL/ITH/ITL)

**What to verify:**
- [ ] Swing highs/lows detected at correct pivot points
- [ ] EQH/EQL tolerance works correctly (perfect vs relative)
- [ ] Labels show correct quality indicators (star for perfect, R. prefix for relative)
- [ ] Touch counts increment correctly for multiple touches
- [ ] Sweeps detected correctly (wick through, close respects level)
- [ ] Swept liquidity shows correct visual state (gray, dotted)
- [ ] Broken-through liquidity invalidates correctly
- [ ] `i_require_intact` setting properly filters

**How to verify:**
1. Identify equal highs/lows visually, then check indicator matches
2. Adjust tolerance settings and verify detection sensitivity changes
3. Look for wick-through-close-below patterns on EQH levels
4. Verify the label text format: `EQH★ (2)` for perfect, `R.EQL (3)` for relative

### Grading System Changes

**What to verify:**
- [ ] Grade appears in the entry line label (e.g., "A+ BUY", "B- SELL")
- [ ] Tooltip shows full grade breakdown (sweep, delivery, momentum, DOL)
- [ ] Grade color matches the grade-to-color mapping
- [ ] Minimum grade filter (`i_min_grade_display`) correctly hides low grades
- [ ] Sweep detection feeds into grading correctly
- [ ] Delivery detection feeds into grading correctly
- [ ] Momentum assessment classifies correctly (body ratio vs range)

**How to verify:**
1. Hover over entry line labels to read the tooltip breakdown
2. Cross-reference each checkbox (sweep, delivery, momentum, DOL) against chart context
3. Change `i_min_grade_display` and verify lower-grade setups disappear
4. Look for A+ setups and verify all criteria are met

### HTF (Higher Timeframe) Changes

**What to verify:**
- [ ] HTF FVG boxes appear with thicker borders than LTF
- [ ] HTF labels include timeframe prefix: `[1H] FVG ▲`
- [ ] HTF bar change detection works (`htf_bar_changed`)
- [ ] No duplicate HTF FVGs (deduplication via `htf_fvg_exists()`)
- [ ] HTF bias correctly filters LTF setups when `i_htf_filter_ltf` is enabled
- [ ] Dashboard shows correct HTF bias (BULLISH/BEARISH/NEUTRAL)
- [ ] Changing HTF timeframe setting updates detection correctly
- [ ] `request.security()` calls use `lookahead=barmerge.lookahead_off` (no future data)

**How to verify:**
1. Set chart to a low timeframe (e.g., 5m) with HTF set to 1H
2. Verify HTF boxes span wider price ranges than LTF boxes
3. Toggle `i_htf_filter_ltf` and verify LTF setups appear/disappear based on bias
4. Check dashboard HTF Bias row matches the most recent HTF IFVG direction

### BE/SL/Entry Line Changes

**What to verify:**
- [ ] BE line appears at the correct swing point (first swing to the LEFT)
- [ ] SL line appears at FVG boundary (default) or swing stop (configurable)
- [ ] Entry line appears at inversion candle close price
- [ ] BE status updates from "intact" to "taken" when price reaches target
- [ ] Entry validity changes from VALID to INVALID when SL is hit
- [ ] Visual state changes: intact lines are solid/dashed, taken lines are faded/dotted
- [ ] Fallback logic works when no swing point is found (defaults to FVG boundary)

**How to verify:**
1. Find an active IFVG setup and check BE/SL levels against nearby swings
2. Watch in real-time or replay as price approaches BE/SL levels
3. Verify the dashboard "Entry: VALID/INVALID" updates correctly
4. Toggle `i_sl_type` between "FVG Boundary" and "Swing Stop"

### Dashboard Changes

**What to verify:**
- [ ] Dashboard renders in top-right position
- [ ] All rows populate with correct data
- [ ] Grade color in "Latest Setup" row matches grade_to_color mapping
- [ ] Entry status shows VALID (green) or INVALID (red) correctly
- [ ] DOL shows liquidity type and price level
- [ ] HTF Bias and HTF timeframe display correctly
- [ ] Dashboard updates on the last bar (`barstate.islast`)

**How to verify:**
1. Observe dashboard while scrolling through chart history
2. Verify numbers match actual array counts (FVGs, IFVGs, liquidity)
3. Compare dashboard DOL against visible liquidity lines on chart

## No-Repaint Verification

**Critical rule:** The indicator must never repaint. All detection uses `barstate.isconfirmed`.

**How to verify no repainting:**
1. Use TradingView's "Replay" mode (bar replay)
2. Step forward one bar at a time
3. Verify that no boxes, lines, or labels appear/disappear on bars that were already confirmed
4. Specifically check: FVG detection, inversion triggers, sweep detection, grading

**What causes repainting (avoid these):**
- Reading `close`, `high`, `low`, `open` without gating on `barstate.isconfirmed`
- Using `request.security()` with `lookahead=barmerge.lookahead_on`
- Modifying `var` state on unconfirmed bars
- Using `barstate.isrealtime` for detection logic

## Memory & Performance Testing

### TradingView Limits

| Resource | Limit | Current Setting |
|----------|-------|-----------------|
| `max_bars_back` | 5000 | 500 |
| `max_boxes_count` | 500 | 500 |
| `max_lines_count` | 500 | 500 |
| `max_labels_count` | 500 | 500 |

**What to verify for memory:**
- [ ] FIFO cleanup functions (`cleanup_*_array()`) prevent array overflow
- [ ] Drawing object limits are not exceeded (TradingView shows error)
- [ ] Bar index clamping works for old HTF boxes: `math.max(fvg.start_bar, bar_index - 400)`
- [ ] Script does not crash on high-volume charts (e.g., 1-second timeframe with many bars)

**How to test:**
1. Load indicator on a 1-minute chart with 5000+ bars of data
2. Set `i_max_fvgs` and `i_max_ifvgs` to maximum values (50 and 100)
3. Set `i_max_liquidity` to maximum (100)
4. Verify no runtime errors appear

### Performance Indicators

TradingView shows script execution time in the Pine Script editor status bar. Watch for:
- Execution time over 200ms (potential timeout on free plans)
- "Calculation takes too long" errors
- Memory usage warnings

## Known Validation Challenges

### Cannot Automate Tests

Pine Script has no test harness. Every change requires:
1. Manual copy-paste to TradingView
2. Visual inspection on multiple chart types
3. Multiple timeframe verification

**Impact:** Regression testing is entirely manual. Changes to detection logic can silently break grading or rendering without obvious visual indicators.

### State Dependencies

The main execution loop processes in strict order (Section 12, lines 2392-2511). Functions depend on prior steps having completed:
- Grading depends on liquidity detection and sweep detection
- BE/SL calculation depends on swing point detection
- Rendering depends on all detection/grading being complete

**Impact:** Changing processing order can cause subtle bugs that are hard to catch visually.

### Multi-Timeframe Testing Requires Multiple Charts

HTF features need verification across timeframe combinations:
- LTF chart (e.g., 5m) with HTF set to 1H
- LTF chart (e.g., 15m) with HTF set to 4H
- Same-timeframe edge case (HTF == LTF)

**Impact:** Each timeframe combination may behave differently. Testing one combination does not guarantee others work.

### Edge Cases to Watch

1. **First bars on chart**: Not enough history for swing detection (`bar_index > lookback * 2`)
2. **Very volatile markets**: ATR-based filtering may reject all FVGs or accept too many
3. **Gaps in data**: Missing bars can cause array index issues
4. **Extremely thin FVGs**: Near the ATR minimum threshold, detection is sensitive to the multiplier
5. **Simultaneous events**: FVG inversion happening on the same bar as a liquidity sweep
6. **HTF bar alignment**: HTF bars may not align cleanly with LTF bars, causing approximate `start_bar` positions

## Recommended Validation Instruments

Test across different market types to ensure market-agnostic ATR-based logic works:

| Market | Symbol | Why |
|--------|--------|-----|
| Index | NQ1! or ES1! | High liquidity, clean structure |
| Forex | EURUSD | 24-hour market, many swing points |
| Crypto | BTCUSD | High volatility, large FVGs |
| Low volatility | Bond futures or stable forex pairs | Tests ATR minimum size filtering |

## Testing New Features Checklist

Before considering a new feature complete:

1. [ ] Script compiles without errors in TradingView Pine Editor
2. [ ] No runtime errors on chart load
3. [ ] Feature works on at least 2 different instruments
4. [ ] Feature works on at least 2 different timeframes
5. [ ] Toggle inputs properly show/hide the feature
6. [ ] Existing features still work correctly (regression check)
7. [ ] Dashboard updates reflect the new feature if applicable
8. [ ] Memory limits not exceeded (check drawing counts)
9. [ ] No repainting observed in replay mode
10. [ ] Tooltips and labels display correctly

---

*Testing analysis: 2026-03-23*
