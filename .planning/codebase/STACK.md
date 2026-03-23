# Technology Stack

**Analysis Date:** 2026-03-23

## Languages

**Primary:**
- Pine Script v6 - Sole language for the entire indicator (`src/IFVG_Indicator.pine`, 2511 lines)

**Secondary:**
- None. This is a single-file Pine Script project with no build tools, transpilers, or secondary languages.

## Runtime

**Environment:**
- TradingView Pine Script Runtime (server-side execution on TradingView infrastructure)
- Pine Script version: v6 (declared via `//@version=6` at line 29)
- Execution model: Bar-by-bar processing on confirmed bars only (`barstate.isconfirmed`)

**Package Manager:**
- None. Pine Script is self-contained with no external dependencies or package management.
- No lockfile, no `package.json`, no `requirements.txt`.

## Frameworks

**Core:**
- TradingView Pine Script v6 built-in library - Full standard library for financial indicators

**Testing:**
- None. No automated testing framework exists for Pine Script.
- Validation is manual: copy code into TradingView Pine Script Editor, apply to charts, visually verify.

**Build/Dev:**
- None. No build step, no transpilation, no bundling.
- Deployment: Manual copy-paste of `src/IFVG_Indicator.pine` into TradingView.

## Key Built-in Functions & Libraries

**Indicator Declaration (line 30-34):**
```pinescript
indicator("IFVG Indicator", shorttitle="IFVG", overlay=true,
          max_bars_back=500,
          max_boxes_count=500,
          max_lines_count=500,
          max_labels_count=500)
```

**Technical Analysis (`ta.*`):**
- `ta.atr(period)` - Average True Range for dynamic sizing (line 307)
- Used for FVG minimum size filtering, EQH/EQL tolerance calculations, momentum assessment

**Math (`math.*`):**
- `math.abs()` - Absolute value for price difference calculations
- `math.max()` / `math.min()` - Clamping values, bar index bounds
- Used extensively in swing detection, EQH/EQL quality, and stop loss calculations

**String (`str.*`):**
- `str.tostring()` - Number-to-string conversion for labels and dashboard
- `str.upper()` - Uppercase formatting for dashboard bias display

**Color (`color.*`):**
- `color.new(base_color, transparency)` - Color with transparency for all visual elements
- Predefined colors: `color.gray`, `color.orange`, `color.yellow`, `color.red`, `color.green`, `color.white`, `color.black`

**Multi-Timeframe (`request.*`):**
- `request.security(symbol, timeframe, expression, lookahead)` - HTF data retrieval (lines 653-680)
- Used for 14 separate HTF data requests (high, low, close, high[2], low[2], bar_index, ATR for two timeframes)
- Always uses `lookahead=barmerge.lookahead_off` to prevent repainting

**Bar State (`barstate.*`):**
- `barstate.isconfirmed` - Guard for all detection logic (prevents repainting)
- `barstate.islast` - Guard for dashboard rendering (only on last bar)

**Symbol Info (`syminfo.*`):**
- `syminfo.tickerid` - Current symbol identifier for `request.security` calls

**Timeframe (`timeframe.*`):**
- `timeframe.period` - Current chart timeframe string

**Format Constants:**
- `format.mintick` - Price formatting at minimum tick precision

## Custom Type System

Pine Script v6 supports user-defined types (UDTs). This project defines 5 custom types in Section 1 (lines 46-123):

| Type | Purpose | Key Fields |
|------|---------|------------|
| `FVG` | Fair Value Gap | `top`, `bottom`, `mid`, `start_bar`, `end_bar`, `is_bullish`, `status`, `timeframe`, `box_id`, `label_id` |
| `SwingPoint` | Swing high/low | `price`, `bar_idx`, `is_high`, `is_internal`, `is_valid` |
| `Liquidity` | EQH/EQL/ITH/ITL levels | `level`, `liq_type`, `quality`, `touch_count`, `is_swept`, `is_valid`, `line_id`, `label_id` |
| `DeliveryFVG` | Lightweight FVG for delivery tracking | `top`, `bottom`, `is_bullish`, `was_traversed`, `timeframe` |
| `IFVG` | Inverted FVG with full grading | `grade`, `entry_valid`, `be_level`, `sl_level`, `has_sweep`, `has_delivery`, `momentum`, plus 7 visual element references |

## Data Storage

**State Management:**
- All state stored in `var` arrays (persist across bars)
- 7 primary arrays declared in Section 3 (lines 289-304):
  - `g_fvg_array` - LTF active FVGs
  - `g_ifvg_array` - LTF inverted FVGs
  - `g_htf_fvg_array` / `g_htf2_fvg_array` - HTF active FVGs (2 timeframes)
  - `g_htf_ifvg_array` / `g_htf2_ifvg_array` - HTF inverted FVGs (2 timeframes)
  - `g_swing_highs` / `g_swing_lows` - Detected swing points
  - `g_liquidity_array` - All liquidity levels
  - `g_delivery_history` - FVG delivery tracking records

**Drawing Object References:**
- `box` references stored on FVG/IFVG types
- `line` references stored on Liquidity and IFVG types
- `label` references stored on all visual types
- `table` for dashboard (1 persistent `var table` at line 2312)

## Platform Resource Limits

**Configured limits (line 30-34):**
- `max_bars_back=500` - Maximum historical bars accessible
- `max_boxes_count=500` - Maximum simultaneous box drawings
- `max_lines_count=500` - Maximum simultaneous line drawings
- `max_labels_count=500` - Maximum simultaneous label drawings

**Enforced via FIFO cleanup functions:**
- `cleanup_fvg_array()` - Caps at `i_max_fvgs` (default 20, max 50)
- `cleanup_ifvg_array()` - Caps at `i_max_ifvgs` (default 30, max 100)
- `cleanup_liquidity_array()` - Caps at `i_max_liquidity` (default 30, max 100)
- Swing arrays capped at 50 entries each
- HTF arrays capped at same limits as LTF

## Configuration

**Environment:**
- No environment variables. All configuration via TradingView `input.*` functions.
- 11 input groups with ~40 configurable parameters (Section 2, lines 124-283).

**Input System Groups:**
| Group | Parameters | Lines |
|-------|-----------|-------|
| General Settings | 4 inputs (enable, max FVGs, max IFVGs, extend bars) | 131-140 |
| FVG Detection | 4 inputs (ATR period, min size, show active, show IFVG) | 145-154 |
| Higher Timeframe | 7 inputs (enable, TF1, TF2, show, filter, opacity, border) | 159-175 |
| Liquidity Detection | 3 inputs (swing lookback, show ITH/ITL, max levels) | 180-186 |
| EQH/EQL Detection | 5 inputs (show, tolerances, require intact, perfect only, show swept) | 191-205 |
| Grading Settings | 5 inputs (min grade, show BE/SL, SL type, show grade) | 210-222 |
| Delivery Detection | 6 inputs (enable, lookback, body only, show box, color, opacity) | 227-239 |
| Visual Settings | 9 inputs (colors, opacity, labels, sizes) | 244-258 |
| IFVG Style | 5 inputs (box color, opacity, entry line, entry colors) | 263-273 |
| Border Settings | 4 inputs (widths, styles) | 278-282 |

## Platform Requirements

**Development:**
- Any text editor for editing `src/IFVG_Indicator.pine`
- TradingView account (free or paid) for testing and deployment
- Web browser to access TradingView platform

**Production:**
- TradingView platform (web-based, no self-hosting)
- Pine Script v6 runtime (automatically provided by TradingView)
- No server, no database, no external infrastructure

**Supported Markets:**
- Any instrument available on TradingView (indices, forex, crypto, commodities)
- Market-agnostic via ATR-based dynamic sizing

---

*Stack analysis: 2026-03-23*
