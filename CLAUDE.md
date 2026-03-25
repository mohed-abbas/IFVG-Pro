# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IFVG Pro is a TradingView indicator implementing the Inversion Fair Value Gap trading strategy in Pine Script v6. It detects FVGs, tracks their inversions, identifies liquidity levels, and grades trading setups from A+ to C.

**Current Status**: Phase 3 complete (Phase 4 pending: sessions, PD zones, dashboard, alerts)

## Development Workflow

This is a Pine Script project with no build/test toolchain:
- **Deployment**: Copy `src/IFVG_Indicator.pine` to TradingView Pine Script Editor
- **Validation**: Visual verification on TradingView charts (no automated testing)
- **No package manager**: Pine Script is self-contained with no dependencies

## Architecture

The indicator follows a modular architecture organized into 12 logical sections:

```
INPUTS → ENGINE → RENDERING
           ↓
        DATA STORE (Arrays)
           ↓
        ALERTS
```

### Core Data Types (Section 1)
- `FVG` - Fair Value Gap with position, state, and visual elements
- `IFVG` - Inverted FVG with grading, BE tracking, and entry validity
- `SwingPoint` - Swing highs/lows for structure analysis
- `Liquidity` - EQH/EQL/ITH/ITL levels with sweep detection

### Key Sections
| Section | Purpose |
|---------|---------|
| 5 | FVG detection (3-candle pattern, ATR-based sizing) |
| 6 | Liquidity detection (swing points, EQH/EQL, sweeps) |
| 7 | Inversion logic & BE point tracking |
| 8 | Grading algorithm (A+ to C based on sweep, momentum, zone) |
| 9-11 | Rendering (boxes, lines, labels, dashboard) |
| 12 | Main execution loop with sequential processing |

### Processing Order (Main Loop)
1. Detect swing points
2. Check EQH/EQL formations
3. Check liquidity sweeps
4. Detect new FVGs
5. Check inversions (FVG → IFVG)
6. Update BE status
7. Check mitigations
8. Grade IFVGs
9. Render visualization
10. Update dashboard

### Memory Management
- Max limits: 500 bars back, 500 boxes/lines/labels each
- FIFO cleanup when array limits exceeded
- Process only on `barstate.isconfirmed` (no repainting)

## Grading System

Setups are graded A+ to C based on:
- **Sweep presence**: Liquidity sweep before FVG formation
- **Delivery**: Price delivered from FVG (not just random formation)
- **Momentum**: "strong_no_chop", "neutral", or "weak_or_choppy"
- **Zone positioning**: Longs in discount, shorts in premium
- **Entry validity**: BE point not yet taken at inversion time

## Key Documentation Files

- `ARCHITECTURE.md` - Complete technical specification with algorithms
- `PRD.md` - Product requirements and feature matrix
- `strategy.md` - Trading strategy rules and entry criteria
- `briefing/IFVG_Rating_System.pdf` - Reference grading system

## Pine Script Conventions

- All detection runs on confirmed bars only (`barstate.isconfirmed`)
- ATR-based dynamic sizing for market-agnostic behavior
- Clear section comments with `// ═══════` separators
- Custom types use PascalCase, functions use snake_case

### Pine Script v6 Syntax Rules (MUST FOLLOW)

These cause "end of line without line continuation" errors if violated:

1. **No blank lines inside `for` loop or `if` block bodies.** The Pine Script parser uses indentation to determine block boundaries. A blank line can terminate the block prematurely. Keep all lines within a block contiguous.
2. **Wrap multi-line `and`/`or` expressions in parentheses.** Bad: `a > b and\n    c < d`. Good: `(a > b) and (c < d)` on one line, or `(a > b and\n    c < d)` with outer parens.
3. **Cast `math.abs()` and `math.max()`/`math.min()` to `int()` when assigning to int fields.** These return `float` in v6. Use `int(math.abs(...))` not `int x = math.abs(...)`.
4. **Prefer nested `if` blocks over `continue` for skip logic in loops.** While `continue` works, nested conditions avoid parser edge cases and are more readable.
5. **Never split a single expression across lines without an operator at the end of the first line.** The operator (`and`, `or`, `+`, etc.) must be the LAST token before the newline.

## Git Commit Rules

- **No AI attribution**: Do NOT include any mention of AI, Claude, or AI assistance in:
  - Commit messages
  - Pull request descriptions
  - Code comments
- **No Co-Authored-By tags**: Do NOT add `Co-Authored-By: Claude` or similar tags
- **Commit style**: Use short descriptive messages with "Phase X:" prefix for major features
- **Examples of recent commits**:
  - `Phase 3: Multi-Timeframe HTF Analysis`
  - `Phase 2.1: Bug fixes and UX improvements`
  - `Add PDA delivery detection for IFVG grading system`

<!-- GSD:project-start source:PROJECT.md -->
## Project

**IFVG Pro**

A TradingView Pine Script v6 overlay indicator that automates the detection, grading, and visualization of Inversion Fair Value Gap (IFVG) setups based on ICT/SMC methodology. It identifies FVGs, tracks their inversions, detects liquidity levels, grades setups from A+ to C, and provides multi-timeframe HTF analysis — enabling traders to spot high-probability entries without manual chart analysis.

**Core Value:** Accurately detect and grade IFVG setups so traders can identify high-probability trade entries with clear risk management levels, across any market and timeframe.

### Constraints

- **Platform**: Pine Script v6 on TradingView — no external dependencies, no build toolchain
- **Testing**: Visual verification only — no automated test framework exists for Pine Script
- **Drawing limits**: Max 500 boxes, 500 lines, 500 labels — FIFO cleanup required
- **Security calls**: Max 40 request.security() calls — 16 already used, Phase 4+ needs careful budgeting
- **Single file**: All code lives in src/IFVG_Indicator.pine — must maintain section organization
- **No repainting**: All detection on barstate.isconfirmed only
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->
## Technology Stack

## Languages
- Pine Script v6 - Sole language for the entire indicator (`src/IFVG_Indicator.pine`, 2511 lines)
- None. This is a single-file Pine Script project with no build tools, transpilers, or secondary languages.
## Runtime
- TradingView Pine Script Runtime (server-side execution on TradingView infrastructure)
- Pine Script version: v6 (declared via `//@version=6` at line 29)
- Execution model: Bar-by-bar processing on confirmed bars only (`barstate.isconfirmed`)
- None. Pine Script is self-contained with no external dependencies or package management.
- No lockfile, no `package.json`, no `requirements.txt`.
## Frameworks
- TradingView Pine Script v6 built-in library - Full standard library for financial indicators
- None. No automated testing framework exists for Pine Script.
- Validation is manual: copy code into TradingView Pine Script Editor, apply to charts, visually verify.
- None. No build step, no transpilation, no bundling.
- Deployment: Manual copy-paste of `src/IFVG_Indicator.pine` into TradingView.
## Key Built-in Functions & Libraries
- `ta.atr(period)` - Average True Range for dynamic sizing (line 307)
- Used for FVG minimum size filtering, EQH/EQL tolerance calculations, momentum assessment
- `math.abs()` - Absolute value for price difference calculations
- `math.max()` / `math.min()` - Clamping values, bar index bounds
- Used extensively in swing detection, EQH/EQL quality, and stop loss calculations
- `str.tostring()` - Number-to-string conversion for labels and dashboard
- `str.upper()` - Uppercase formatting for dashboard bias display
- `color.new(base_color, transparency)` - Color with transparency for all visual elements
- Predefined colors: `color.gray`, `color.orange`, `color.yellow`, `color.red`, `color.green`, `color.white`, `color.black`
- `request.security(symbol, timeframe, expression, lookahead)` - HTF data retrieval (lines 653-680)
- Used for 14 separate HTF data requests (high, low, close, high[2], low[2], bar_index, ATR for two timeframes)
- Always uses `lookahead=barmerge.lookahead_off` to prevent repainting
- `barstate.isconfirmed` - Guard for all detection logic (prevents repainting)
- `barstate.islast` - Guard for dashboard rendering (only on last bar)
- `syminfo.tickerid` - Current symbol identifier for `request.security` calls
- `timeframe.period` - Current chart timeframe string
- `format.mintick` - Price formatting at minimum tick precision
## Custom Type System
| Type | Purpose | Key Fields |
|------|---------|------------|
| `FVG` | Fair Value Gap | `top`, `bottom`, `mid`, `start_bar`, `end_bar`, `is_bullish`, `status`, `timeframe`, `box_id`, `label_id` |
| `SwingPoint` | Swing high/low | `price`, `bar_idx`, `is_high`, `is_internal`, `is_valid` |
| `Liquidity` | EQH/EQL/ITH/ITL levels | `level`, `liq_type`, `quality`, `touch_count`, `is_swept`, `is_valid`, `line_id`, `label_id` |
| `DeliveryFVG` | Lightweight FVG for delivery tracking | `top`, `bottom`, `is_bullish`, `was_traversed`, `timeframe` |
| `IFVG` | Inverted FVG with full grading | `grade`, `entry_valid`, `be_level`, `sl_level`, `has_sweep`, `has_delivery`, `momentum`, plus 7 visual element references |
## Data Storage
- All state stored in `var` arrays (persist across bars)
- 7 primary arrays declared in Section 3 (lines 289-304):
- `box` references stored on FVG/IFVG types
- `line` references stored on Liquidity and IFVG types
- `label` references stored on all visual types
- `table` for dashboard (1 persistent `var table` at line 2312)
## Platform Resource Limits
- `max_bars_back=500` - Maximum historical bars accessible
- `max_boxes_count=500` - Maximum simultaneous box drawings
- `max_lines_count=500` - Maximum simultaneous line drawings
- `max_labels_count=500` - Maximum simultaneous label drawings
- `cleanup_fvg_array()` - Caps at `i_max_fvgs` (default 20, max 50)
- `cleanup_ifvg_array()` - Caps at `i_max_ifvgs` (default 30, max 100)
- `cleanup_liquidity_array()` - Caps at `i_max_liquidity` (default 30, max 100)
- Swing arrays capped at 50 entries each
- HTF arrays capped at same limits as LTF
## Configuration
- No environment variables. All configuration via TradingView `input.*` functions.
- 11 input groups with ~40 configurable parameters (Section 2, lines 124-283).
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
- Any text editor for editing `src/IFVG_Indicator.pine`
- TradingView account (free or paid) for testing and deployment
- Web browser to access TradingView platform
- TradingView platform (web-based, no self-hosting)
- Pine Script v6 runtime (automatically provided by TradingView)
- No server, no database, no external infrastructure
- Any instrument available on TradingView (indices, forex, crypto, commodities)
- Market-agnostic via ATR-based dynamic sizing
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

## Language & Platform
## Naming Patterns
- Use **PascalCase**: `FVG`, `IFVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`
- Defined in Section 1 of `src/IFVG_Indicator.pine` (lines 46-122)
- Each type includes inline comments for every field
- Use **snake_case**: `detect_fvg()`, `check_inversions()`, `render_fvg_boxes()`, `find_previous_swing_high()`
- Naming pattern: `verb_noun()` or `verb_adjective_noun()`
- Detection: `detect_*()`, `check_*()`, `find_*()`
- Rendering: `render_*()`, `draw_*()` (not currently used but implied by ARCHITECTURE.md)
- Utilities: `get_*()`, `is_*()`, `calculate_*()`, `assess_*()`
- Cleanup: `cleanup_*_array()`
- Use `i_` prefix with **snake_case**: `i_show_indicator`, `i_max_fvgs`, `i_fvg_atr_period`
- Always declare with full `input.*()` call on the same line or continued with indentation
- Use `g_` prefix with **snake_case**: `g_fvg_array`, `g_ifvg_array`, `g_swing_highs`, `g_liquidity_array`, `g_delivery_history`
- Always declared with `var` keyword for persistence across bars
- Use `GROUP_` prefix with **UPPER_CASE**: `GROUP_GENERAL`, `GROUP_FVG`, `GROUP_HTF`, `GROUP_LIQ`
- Declared as `string` type constants immediately before the inputs they group
- Use **snake_case** without prefix: `result`, `new_fvg`, `bullish_gap_size`, `right_edge`
- Boolean locals: descriptive names like `inverted`, `exists`, `recent_intact`, `should_display`
- Typed declarations when Pine Script requires it: `float result = na`, `bool exists = false`, `int closest_bar = 999999`
- Use `htf_` or `htf2_` prefix: `htf_high`, `htf_low`, `htf2_close`, `htf_bar_changed`
- Previous-bar trackers: `prev_htf_bar`, `prev_htf2_bar`
## Code Organization
### Section Structure
### Current Section Layout
| Section | Lines | Purpose |
|---------|-------|---------|
| Header  | 1-34  | Version banner, indicator declaration |
| 1       | 36-122 | Type definitions |
| 2       | 124-283 | Input configuration |
| 3       | 284-307 | Global variables & data stores |
| 4       | 309-509 | Utility functions |
| 5       | 598-643 | LTF FVG detection |
| 5B      | 645-761 | HTF FVG detection (Phase 3) |
| 6       | 865-1223 | Swing point & liquidity detection |
| 7       | 1224-1464 | BE point & grading functions |
| 8       | 1466-1636 | Inversion detection |
| 9       | 1638-1749 | BE status & mitigation detection |
| 10      | 1751-2288 | Rendering |
| 11      | 2308-2387 | Dashboard |
| 12      | 2388-2511 | Main execution loop |
### Sub-Section Separators
### When to Use Sub-Sub Separators
## Input Organization
### Group Naming Pattern
### Input Declaration Pattern
### Input Grouping Order (top to bottom in TradingView settings)
## Pine Script Idioms
### Confirmed Bars Only (No Repainting)
### `na` Handling
- Initialize optional results to `na`: `FVG result = na`, `float result = na`
- Check before using: `if not na(old_fvg.box_id)`
- Check before deleting drawing objects: always guard `box.delete()`, `line.delete()`, `label.delete()` with `not na()` checks
- Use `na` as default for drawing object references in `*.new()` constructors: `box_id = na, label_id = na`
### Ternary Operators
### `var` Declarations
### Array Bounds Safety
### Function Return Pattern
### Drawing Object Lifecycle
## Color Scheme Conventions
### User-Configurable Colors
| Variable | Default | Purpose |
|----------|---------|---------|
| `i_bullish_color` | `#089981` (teal green) | All bullish FVG elements |
| `i_bearish_color` | `#F23645` (red) | All bearish FVG elements |
| `i_liq_color` | `color.orange` | EQH/EQL liquidity lines |
| `i_ithl_color` | `color.yellow` | ITH/ITL internal structure lines |
| `i_be_color` | `color.white` | Break-even level lines |
| `i_sl_color` | `color.red` | Stop loss level lines |
| `i_entry_color_bull` | `#2962FF` (blue) | Bullish entry lines |
| `i_entry_color_bear` | `#F23645` (red) | Bearish entry lines |
| `i_delivery_color` | `#FF9800` (orange) | Delivery FVG highlight |
| `i_ifvg_box_color` | `color.gray` | IFVG box fill |
### Grade Color Mapping (hardcoded in `grade_to_color()`)
| Grade | Color | Hex |
|-------|-------|-----|
| A+ | Bright green | `#00FF00` |
| A | Green | `#00CC00` |
| A- | Yellow-green | `#66CC00` |
| B+ | Yellow | `#FFCC00` |
| B | Orange | `#FF9900` |
| B- | Dark orange | `#FF6600` |
| C | Red | `#FF3333` |
### Opacity Convention
- Active FVG boxes: user-configurable via `i_fvg_opacity` (default 85%)
- IFVG boxes: user-configurable via `i_ifvg_box_opacity` (default 60%)
- HTF boxes: user-configurable via `i_htf_box_opacity` (default 75%)
- Delivery boxes: user-configurable via `i_delivery_opacity` (default 70%)
- Swept/invalid elements: add 50-70% opacity to gray them out
- Fully transparent: `color.new(color.black, 100)` for invisible label backgrounds
### EQH/EQL Quality Colors (hardcoded in `render_liquidity_lines()`)
| Quality | Color |
|---------|-------|
| Perfect | `#FF6600` (bright orange), line width 2 |
| Relative | `i_liq_color` (standard orange), line width 1 |
| Swept | `color.gray` at 50% opacity, dotted style |
| Broken | `color.gray` at 70% opacity, dotted style |
## How to Add New Features
### Adding a New Section
### Adding New Inputs
### Adding a New Custom Type
### Adding a New Detection Function
### Adding New Visual Elements
## Comment Conventions
### Function Documentation
- What it does
- Parameters (if not obvious)
- Return value
### Inline Comments
- Use `//` with a space after
- Place on same line for field documentation in types
- Place on own line for logic explanations
- Use `// NOTE:` prefix for important behavioral notes (see lines 978, 1073, 1122, 1157)
- Use `// RULE N:` prefix for numbered business rules within algorithm functions
### Status Enums (String Constants)
## Git Commit Conventions
- **No AI attribution**: Do not include mentions of AI, Claude, or AI assistance in commit messages, PR descriptions, or code comments
- **No Co-Authored-By tags**: Do not add `Co-Authored-By: Claude` or similar
- **Message style**: Short descriptive messages
- **Phase prefix**: Use `Phase X:` prefix for major feature commits
- **Examples**: `Phase 3: Multi-Timeframe HTF Analysis`, `Phase 2.1: Bug fixes and UX improvements`, `Add PDA delivery detection for IFVG grading system`
## File Header Convention
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

## Pattern Overview
- Bar-by-bar execution model -- the main loop (Section 12) runs once per confirmed bar
- No repainting -- all detection logic gates on `barstate.isconfirmed`
- State persisted via `var` arrays that survive across bars
- Pipeline pattern: detect -> update state -> check inversions -> grade -> render
- Multi-timeframe data pulled via `request.security()` calls (Phase 3)
## Layers
- Purpose: User-configurable parameters organized into input groups
- Location: `src/IFVG_Indicator.pine` lines 124-283
- Contains: 9 input groups with `input.bool`, `input.int`, `input.float`, `input.string`, `input.color`, `input.timeframe` declarations
- Depends on: Nothing
- Used by: Every other section reads `i_*` prefixed variables
- Purpose: Custom type definitions for all domain objects
- Location: `src/IFVG_Indicator.pine` lines 36-123
- Contains: 5 custom types: `FVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`, `IFVG`
- Depends on: Nothing
- Used by: All data store arrays, all detection/rendering functions
- Purpose: Global `var` arrays that persist state across bars
- Location: `src/IFVG_Indicator.pine` lines 284-307
- Contains: 7 typed arrays initialized once with `var`
- Depends on: Type definitions (Section 1)
- Used by: Engine and Rendering layers read/write these arrays
- Purpose: Helper functions for color, grading, cleanup, delivery detection, swing validation
- Location: `src/IFVG_Indicator.pine` lines 310-597
- Contains: Grade conversion, color helpers, array cleanup (FIFO), delivery tracking functions, swing integrity checks, EQH/EQL quality classification
- Depends on: Input layer, Data store layer
- Used by: Engine and Rendering layers
- Purpose: Core FVG detection (LTF + HTF) and liquidity/swing detection
- Location: `src/IFVG_Indicator.pine` lines 598-1223
- Contains: `detect_fvg()`, `detect_htf_fvg()`, HTF data via `request.security()`, `detect_swing_points()`, `check_equal_highs()`, `check_equal_lows()`, `create_internal_levels()`, `check_liquidity_sweeps()`
- Depends on: Input layer, Data store, Utility layer, ATR calculation
- Used by: Main loop (Section 12)
- Purpose: BE/SL calculation, DOL finding, sweep detection, momentum assessment, grading algorithm, and FVG->IFVG inversion logic
- Location: `src/IFVG_Indicator.pine` lines 1224-1637
- Contains: `find_previous_swing_high/low()`, `find_dol()`, `check_recent_sweep()`, `assess_momentum()`, `calculate_stop_loss()`, `calculate_grade()`, `check_inversions()`
- Depends on: Data store, swing point arrays, liquidity arrays
- Used by: Main loop (Section 12)
- Purpose: Update BE/SL status, refresh DOL targets, detect IFVG mitigations
- Location: `src/IFVG_Indicator.pine` lines 1638-1749
- Contains: `update_be_status()`, `update_dol_status()`, `check_mitigations()`
- Depends on: Data store (g_ifvg_array, g_liquidity_array)
- Used by: Main loop (Section 12)
- Purpose: Draw all visual elements (boxes, lines, labels, dashboard table)
- Location: `src/IFVG_Indicator.pine` lines 1751-2387
- Contains: `render_fvg_boxes()`, `render_ifvg_boxes()`, `render_htf_fvg_boxes()`, `render_htf_ifvg_boxes()`, `render_liquidity_lines()`, `render_dashboard()`
- Depends on: Data store arrays, Input layer (visibility/style settings)
- Used by: Main loop (Section 12)
- Purpose: Orchestrates the entire pipeline in correct order
- Location: `src/IFVG_Indicator.pine` lines 2388-2511
- Contains: Sequential calls to all detection, update, and rendering functions
- Depends on: All other sections
- Used by: TradingView runtime (called each bar)
## Data Flow
- All state lives in 7 global `var` arrays declared at lines 289-304
- `var` keyword in Pine Script means the array is initialized once and persists across bars
- Arrays are modified in-place; objects are mutated directly via field assignment (e.g., `fvg.status := "inverted"`)
- Each array has a max size enforced by FIFO cleanup functions that `array.shift()` the oldest entry when exceeded
## Key Abstractions
- Purpose: Represents a 3-candle price gap (imbalance zone)
- Defined at: `src/IFVG_Indicator.pine` lines 46-56
- Lifecycle: `"active"` -> `"inverted"` (becomes IFVG) or `"mitigated"` (removed)
- Key fields: `top`, `bottom`, `is_bullish`, `status`, `timeframe`, `box_id`
- Created by: `detect_fvg()` (line 605) or `detect_htf_fvg()` (line 685)
- Purpose: An FVG that has been inverted by a body close through its zone; the primary trading setup
- Defined at: `src/IFVG_Indicator.pine` lines 92-122
- Lifecycle: Created when FVG inverts -> `"inverted"` (active setup) -> `"mitigated"` (removed)
- Key fields: `grade`, `entry_valid`, `be_level`, `be_status`, `sl_level`, `has_sweep`, `has_delivery`, `momentum`, `dol`
- Created by: `check_inversions()` (line 1470) or `check_htf_inversions()` (line 765)
- Purpose: Represents a swing high or swing low used for structure analysis
- Defined at: `src/IFVG_Indicator.pine` lines 58-64
- Pattern: Detected at `[lookback]` offset using left/right bar comparison
- Created by: `detect_swing_points()` (line 872)
- Used for: EQH/EQL formation, BE level calculation, SL placement
- Purpose: Represents a liquidity level (EQH, EQL, ITH, ITL) that can be swept
- Defined at: `src/IFVG_Indicator.pine` lines 67-79
- Lifecycle: created -> `is_valid=true` -> swept (`is_swept=true`) or broken (`is_valid=false`)
- Quality classification: `"perfect"` (within 0.02 ATR) or `"relative"` (within 0.10 ATR)
- Used for: Grading (sweep detection), DOL targeting, dashboard display
- Purpose: Lightweight FVG record tracking whether price was "delivered" from a prior same-direction FVG
- Defined at: `src/IFVG_Indicator.pine` lines 82-89
- Pattern: Recorded when any FVG forms, checked when inversion occurs
- Created by: `record_fvg_for_delivery()` (line 426)
- Checked by: `check_delivery()` (line 480)
## Entry Points
- Location: `src/IFVG_Indicator.pine` line 30 (`indicator(...)`)
- Triggers: TradingView calls the script once per bar
- Responsibilities: Configures overlay mode, sets max_bars_back/boxes/lines/labels limits
- Location: `src/IFVG_Indicator.pine` line 2392 (`if i_show_indicator`)
- Triggers: Every bar, but only if the indicator is enabled
- Responsibilities: Runs the entire detection -> update -> render pipeline
- Location: `src/IFVG_Indicator.pine` lines 653-680 (`request.security(...)` calls)
- Triggers: Evaluated by TradingView on each bar automatically
- Responsibilities: Pulls OHLC and ATR data from two configurable higher timeframes
## Key Algorithms
- 3-candle pattern: bullish if `low[0] > high[2]`, bearish if `high[0] < low[2]`
- Minimum gap size filter: gap must exceed `ATR * i_fvg_min_size_mult` (default 0.25)
- Only one FVG detected per bar (bullish checked first)
- Iterates active FVGs in reverse (newest first)
- Bullish FVG inversion: price enters zone AND body closes below `fvg.bottom`
- Bearish FVG inversion: price enters zone AND body closes above `fvg.top`
- On inversion: creates IFVG with full grading data, removes FVG from active array
- Step 1 (Tier): Must have DOL target or grade is "C". Has sweep+delivery = "A" tier. Has sweep OR delivery = "A" tier. Neither = "B" tier.
- Step 2 (Modifier): Quality score from momentum (+1/-1), FVG clarity (+1/-1), bonus for both sweep AND delivery (+1)
- Step 3 (Combine): A tier + score>=2 = "A+", score>=1 = "A", score>=0 = "A-", else "B+". B tier + score>=1 = "B+", score>=0 = "B", else "B-".
- BSL sweep (EQH/ITH): `high > level AND close < level` (wick above, body stays below)
- SSL sweep (EQL/ITL): `low < level AND close > level` (wick below, body stays above)
- Complete break: close through level invalidates without sweep marker
- Compares most recent swing against up to 10 previous swings
- Both swings must be intact (not broken through by close)
- Validates formation direction (EQH: new <= old, EQL: new >= old)
- Price difference must be within ATR-based tolerance
- Liquidity must NOT have been swept between the two swings
- Quality: "perfect" if within `ATR * 0.02`, "relative" if within `ATR * 0.10`
- Searches `g_delivery_history` for a prior FVG matching IFVG direction
- Delivery FVG must have formed before source FVG
- Must be within `i_delivery_lookback` bars
- Price must have traversed the delivery FVG zone
## Error Handling
- Every array access is guarded by `i < array.size(arr)` bounds checks
- `na()` checks on all float/object values before use (e.g., `not na(atr_value)`, `not na(fvg.box_id)`)
- Fallback values when swing points not found: uses FVG boundary as BE/SL default
- Drawing objects (box, line, label) always deleted before recreating to prevent orphans
- `bar_index` clamping with `math.max(start_bar, bar_index - 400)` to prevent "bar index too far" errors
## Memory Management
- `max_bars_back = 500` -- maximum historical bars accessible
- `max_boxes_count = 500` -- maximum simultaneous box drawings
- `max_lines_count = 500` -- maximum simultaneous line drawings
- `max_labels_count = 500` -- maximum simultaneous label drawings
- `g_fvg_array`: capped at `i_max_fvgs` (default 20, max 50)
- `g_ifvg_array`: capped at `i_max_ifvgs` (default 30, max 100)
- `g_liquidity_array`: capped at `i_max_liquidity` (default 30, max 100)
- `g_swing_highs` / `g_swing_lows`: hardcoded cap at 50 entries each (line 899, 923)
- `g_delivery_history`: cleaned by lookback period, no hard cap
- HTF arrays: use same `i_max_fvgs` / `i_max_ifvgs` limits
- FIFO (`array.shift()`) -- oldest entries removed first
- Drawing cleanup on removal: every cleanup function deletes associated `box`, `line`, `label` objects
- Delivery history cleaned by age (`bar_index - record.end_bar > i_delivery_lookback`)
- Mitigated IFVGs removed from array entirely (not just marked)
- Rendering: all drawings deleted and recreated each bar to prevent stale visuals
## Cross-Cutting Concerns
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
