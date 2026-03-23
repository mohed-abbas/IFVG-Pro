# External Integrations

**Analysis Date:** 2026-03-23

## APIs & External Services

**TradingView Platform (sole integration):**
- The indicator runs entirely within TradingView's Pine Script runtime
- No external API calls, HTTP requests, or third-party service integrations
- All data comes from TradingView's built-in market data feeds

## TradingView Platform Integration Points

### 1. Market Data Feed

**Current Timeframe OHLCV:**
- `open`, `high`, `low`, `close` - Accessed directly as built-in variables
- Used throughout all detection functions in `src/IFVG_Indicator.pine`
- Processed only on confirmed bars via `barstate.isconfirmed` guard

**Historical Bar Access:**
- `bar_index` - Current bar's sequential index
- Square bracket notation `high[2]`, `low[2]`, etc. for lookback
- Maximum lookback: 500 bars (`max_bars_back=500`, line 31)

**Symbol Metadata:**
- `syminfo.tickerid` - Current symbol identifier (used in all `request.security` calls)
- `timeframe.period` - Current chart timeframe string (used for delivery FVG timeframe tagging, line 2417)
- `format.mintick` - Minimum tick precision for price formatting in labels and dashboard

### 2. Multi-Timeframe Data Requests (`request.security`)

**HTF Timeframe 1 (lines 653-659):**
All requests use `syminfo.tickerid` as symbol and `i_htf_timeframe` (default `"60"` = 1H) as timeframe.

```pinescript
htf_high = request.security(syminfo.tickerid, i_htf_timeframe, high, lookahead=barmerge.lookahead_off)
htf_low = request.security(syminfo.tickerid, i_htf_timeframe, low, lookahead=barmerge.lookahead_off)
htf_close = request.security(syminfo.tickerid, i_htf_timeframe, close, lookahead=barmerge.lookahead_off)
htf_high_2 = request.security(syminfo.tickerid, i_htf_timeframe, high[2], lookahead=barmerge.lookahead_off)
htf_low_2 = request.security(syminfo.tickerid, i_htf_timeframe, low[2], lookahead=barmerge.lookahead_off)
htf_bar_idx_raw = request.security(syminfo.tickerid, i_htf_timeframe, bar_index, lookahead=barmerge.lookahead_off)
```

**HTF Timeframe 2 (lines 662-668):**
Same pattern with `i_htf_timeframe_2` (default `"240"` = 4H).

**HTF ATR (lines 679-680):**
```pinescript
htf_atr = request.security(syminfo.tickerid, i_htf_timeframe, ta.atr(i_fvg_atr_period), lookahead=barmerge.lookahead_off)
htf2_atr = request.security(syminfo.tickerid, i_htf_timeframe_2, ta.atr(i_fvg_atr_period), lookahead=barmerge.lookahead_off)
```

**Total `request.security` calls: 14**
- 7 per HTF timeframe (high, low, close, high[2], low[2], bar_index, ATR)
- All use `lookahead=barmerge.lookahead_off` to prevent future data leakage (no repainting)

**HTF Bar Change Detection (lines 671-676):**
```pinescript
var int prev_htf_bar = na
bool htf_bar_changed = na(prev_htf_bar) or htf_bar_idx != prev_htf_bar
prev_htf_bar := htf_bar_idx
```
- Tracks when a new HTF bar forms to trigger HTF FVG detection only once per HTF bar
- Prevents duplicate detections within the same HTF candle

### 3. Chart Rendering System

**Boxes (`box.*`):**
- `box.new()` - Create price zone rectangles (FVG zones, IFVG zones, delivery highlights, HTF overlays)
- `box.delete()` - Remove stale/mitigated drawings
- Used for: Active FVGs, IFVGs, HTF FVGs, HTF IFVGs, delivery FVG highlights
- Parameters used: `left`, `top`, `right`, `bottom`, `bgcolor`, `border_color`, `border_width`, `border_style`, `text`, `text_size`, `text_color`, `text_halign`, `text_valign`
- Maximum count: 500 (set at indicator declaration)

**Lines (`line.*`):**
- `line.new()` - Create horizontal price lines (BE levels, SL levels, entry lines, liquidity lines)
- `line.delete()` - Remove stale drawings
- Styles used: `line.style_solid`, `line.style_dashed`, `line.style_dotted`
- Used for: Break-even levels, stop loss levels, entry price lines, EQH/EQL lines, ITH/ITL lines
- Maximum count: 500

**Labels (`label.*`):**
- `label.new()` - Create text annotations (FVG labels, grade labels, liquidity type labels, entry labels with tooltips)
- `label.delete()` - Remove stale labels
- Styles used: `label.style_none` (text-only, no background bubble)
- Sizes used: `size.tiny`, `size.small`, `size.normal`
- Alignment: `text.align_left`, `text.align_right`
- Y-location: `yloc.price` (positioned at specific price level)
- **Tooltip feature**: Entry labels include multi-line tooltip with grade breakdown (lines 1971-1978)
- Maximum count: 500

**Tables (`table.*`):**
- `table.new()` - Create dashboard panel (line 2312)
- `table.cell()` - Populate dashboard cells (lines 2317-2386)
- Position: `position.top_right`
- Size: 2 columns x 10 rows
- Rendered only on last bar (`barstate.islast`)
- Dashboard content: FVG/IFVG counts, latest setup grade, entry status, DOL target, HTF bias, HTF timeframes

### 4. Input System (`input.*`)

**Input types used in `src/IFVG_Indicator.pine` Section 2 (lines 124-282):**

| Input Function | Count | Purpose |
|---------------|-------|---------|
| `input.bool()` | 15 | Toggle features on/off |
| `input.int()` | 11 | Numeric settings (lookbacks, limits, widths, opacity) |
| `input.float()` | 3 | Decimal settings (ATR multipliers, tolerances) |
| `input.string()` | 4 | Dropdown selections (grade filter, SL type, border styles, label size) |
| `input.color()` | 9 | Color pickers (bullish, bearish, liquidity, BE, SL, entry, delivery) |
| `input.timeframe()` | 2 | Timeframe selectors (HTF1, HTF2) |

**Input features used:**
- `group` - Organize inputs into collapsible sections (11 groups)
- `tooltip` - Hover text explaining each setting
- `minval` / `maxval` - Constrain numeric ranges
- `step` - Control increment for float inputs
- `options` - Dropdown lists for string inputs

### 5. Alert System

**Current status: Not yet implemented (Phase 4)**

The architecture document (`ARCHITECTURE.md`, Section 9) specifies a planned alert system:
- `alertcondition()` - Pine Script built-in for defining alert triggers
- Planned alert types: New IFVG detection, grade-filtered alerts, entry valid/invalid notifications
- No `alertcondition()` calls exist in the current codebase

### 6. Technical Analysis Library (`ta.*`)

**Functions used:**
- `ta.atr(period)` - Average True Range (line 307, lines 679-680)
  - LTF ATR: `ta.atr(i_fvg_atr_period)` with configurable period (default 14)
  - HTF ATR: Fetched via `request.security` for each HTF timeframe
  - Used for: FVG minimum size filter, EQH/EQL tolerance, momentum assessment

## Data Storage

**Databases:**
- None. All state is transient, held in Pine Script `var` arrays during chart execution.
- State resets when indicator is removed/reloaded.

**File Storage:**
- None. No file I/O capability in Pine Script.

**Caching:**
- Pine Script runtime handles bar-level caching internally.
- `var` keyword persists values across bars (7 arrays + 2 tracking variables + 1 table).

## Authentication & Identity

**Auth Provider:**
- TradingView account authentication (handled by the platform, not the indicator)
- No custom auth logic in the codebase

## Monitoring & Observability

**Error Tracking:**
- None. Pine Script has no error reporting mechanism beyond compile-time errors.
- Runtime errors cause the indicator to stop with a TradingView error overlay.

**Logs:**
- None. No logging capability in Pine Script (no `console.log` equivalent).
- Debugging is done via visual inspection on charts or temporary `label.new()` calls.

## CI/CD & Deployment

**Hosting:**
- TradingView platform (cloud-hosted, no self-hosting option)

**CI Pipeline:**
- None. No automated testing, linting, or deployment pipeline.

**Deployment Process:**
1. Edit `src/IFVG_Indicator.pine` locally
2. Copy entire file contents
3. Paste into TradingView Pine Script Editor
4. Click "Add to chart" or "Save" to deploy
5. Visually verify on chart

## Environment Configuration

**Required env vars:**
- None. Pine Script has no environment variable concept.

**Secrets location:**
- Not applicable. No secrets, API keys, or credentials required.

## Webhooks & Callbacks

**Incoming:**
- None. Pine Script cannot receive external data.

**Outgoing:**
- None currently. Phase 4 plans to add `alertcondition()` which can trigger TradingView webhooks to external services.
- TradingView alerts can be configured to send webhooks to URLs, but this is a platform feature, not indicator code.

## External Data Dependencies

**Market Data:**
- Depends entirely on TradingView's data feeds for OHLCV prices
- Supports any TradingView-available instrument (indices, forex, crypto, commodities)
- Data quality and availability determined by the user's TradingView subscription tier

**No Other External Dependencies:**
- No external APIs
- No external libraries or imports
- No CDN resources
- No database connections
- No file system access

---

*Integration audit: 2026-03-23*
