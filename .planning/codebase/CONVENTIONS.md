# Coding Conventions

**Analysis Date:** 2026-03-23

## Language & Platform

**Pine Script v6** - TradingView's proprietary scripting language. Single-file architecture: all code lives in `src/IFVG_Indicator.pine` (2511 lines). No external dependencies, no build system, no package manager.

## Naming Patterns

**Custom Types:**
- Use **PascalCase**: `FVG`, `IFVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`
- Defined in Section 1 of `src/IFVG_Indicator.pine` (lines 46-122)
- Each type includes inline comments for every field

**Functions:**
- Use **snake_case**: `detect_fvg()`, `check_inversions()`, `render_fvg_boxes()`, `find_previous_swing_high()`
- Naming pattern: `verb_noun()` or `verb_adjective_noun()`
- Detection: `detect_*()`, `check_*()`, `find_*()`
- Rendering: `render_*()`, `draw_*()` (not currently used but implied by ARCHITECTURE.md)
- Utilities: `get_*()`, `is_*()`, `calculate_*()`, `assess_*()`
- Cleanup: `cleanup_*_array()`

**Input Variables:**
- Use `i_` prefix with **snake_case**: `i_show_indicator`, `i_max_fvgs`, `i_fvg_atr_period`
- Always declare with full `input.*()` call on the same line or continued with indentation

**Global Variables:**
- Use `g_` prefix with **snake_case**: `g_fvg_array`, `g_ifvg_array`, `g_swing_highs`, `g_liquidity_array`, `g_delivery_history`
- Always declared with `var` keyword for persistence across bars

**Input Group Constants:**
- Use `GROUP_` prefix with **UPPER_CASE**: `GROUP_GENERAL`, `GROUP_FVG`, `GROUP_HTF`, `GROUP_LIQ`
- Declared as `string` type constants immediately before the inputs they group

**Local Variables:**
- Use **snake_case** without prefix: `result`, `new_fvg`, `bullish_gap_size`, `right_edge`
- Boolean locals: descriptive names like `inverted`, `exists`, `recent_intact`, `should_display`
- Typed declarations when Pine Script requires it: `float result = na`, `bool exists = false`, `int closest_bar = 999999`

**HTF Variables:**
- Use `htf_` or `htf2_` prefix: `htf_high`, `htf_low`, `htf2_close`, `htf_bar_changed`
- Previous-bar trackers: `prev_htf_bar`, `prev_htf2_bar`

## Code Organization

### Section Structure

The file is divided into numbered sections (1-12) with major separator comments:

```pinescript
// ══════════════════════════════════════════════════════════════════════
// SECTION N: SECTION TITLE
// ══════════════════════════════════════════════════════════════════════
```

Use double-line box-drawing characters (`═`) for section separators. Each section gets a full-width line above and below the title.

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

Within sections, use single-line dash characters (`─`) for function/subsection headers:

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Function description or sub-section title
// ─────────────────────────────────────────────────────────────────────
```

### When to Use Sub-Sub Separators

Within long functions, use sub-comments with box-drawing characters for major logical blocks:

```pinescript
// ═══════════════════════════════════════════════════════════════════
// BE LEVEL - First swing point TO THE LEFT of the IFVG
// This is where you move your stop to breakeven (first target)
// ═══════════════════════════════════════════════════════════════════
```

This is used inside `check_inversions()` (lines 1514-1517, 1534-1538, 1565-1567) to separate the BE, SL, and Entry Validity computation blocks.

## Input Organization

### Group Naming Pattern

Input groups use decorative borders in their display names:

```pinescript
string GROUP_GENERAL = "═══ General Settings ═══"
string GROUP_FVG = "═══ FVG Detection ═══"
string GROUP_HTF = "═══ Higher Timeframe (HTF) ═══"
```

### Input Declaration Pattern

Every input follows this structure:
1. Type-appropriate `input.*()` call
2. Default value as first argument
3. Human-readable label as second argument
4. `group=GROUP_*` parameter
5. `tooltip=` parameter with user-facing explanation
6. For numeric inputs: `minval`, `maxval`, and optionally `step`

```pinescript
i_fvg_atr_period    = input.int(14, "ATR Period", minval=5, maxval=50, group=GROUP_FVG,
                      tooltip="ATR period used for minimum gap size calculation")
```

### Input Grouping Order (top to bottom in TradingView settings)

1. General Settings (`GROUP_GENERAL`)
2. FVG Detection (`GROUP_FVG`)
3. Higher Timeframe (`GROUP_HTF`)
4. Liquidity Detection (`GROUP_LIQ`)
5. EQH/EQL Detection (`GROUP_EQHL`)
6. Grading Settings (`GROUP_GRADE`)
7. Delivery Detection (`GROUP_DELIVERY`)
8. Visual Settings (`GROUP_VISUAL`)
9. IFVG Style Settings (`GROUP_IFVG_STYLE`)
10. Border Settings (`GROUP_BORDER`)

When adding new inputs, create a new `GROUP_*` constant and place it in logical order. Feature-specific settings come before visual/style settings.

## Pine Script Idioms

### Confirmed Bars Only (No Repainting)

All detection logic gates on `barstate.isconfirmed`:

```pinescript
detect_fvg() =>
    FVG result = na
    if barstate.isconfirmed and not na(atr_value)
        // ... detection logic
    result
```

**Rule:** Never perform detection or state changes on unconfirmed bars. The only exception is rendering on `barstate.islast` (dashboard).

### `na` Handling

- Initialize optional results to `na`: `FVG result = na`, `float result = na`
- Check before using: `if not na(old_fvg.box_id)`
- Check before deleting drawing objects: always guard `box.delete()`, `line.delete()`, `label.delete()` with `not na()` checks
- Use `na` as default for drawing object references in `*.new()` constructors: `box_id = na, label_id = na`

### Ternary Operators

Used extensively for concise conditional assignments:

```pinescript
bool ifvg_is_bullish = not fvg.is_bullish
be_level := ifvg_is_bullish ? fvg.top : fvg.bottom
entry_text = not na(latest_ifvg) ? (latest_ifvg.entry_valid ? "VALID" : "INVALID") : "-"
```

### `var` Declarations

Use `var` for persistent state that must survive across bars:

```pinescript
var array<FVG> g_fvg_array = array.new<FVG>()
var int prev_htf_bar = na
var table dashboard = table.new(position.top_right, 2, 10, ...)
```

**Rule:** Only global data stores and inter-bar tracking variables use `var`. Per-bar calculations do not.

### Array Bounds Safety

Always check array size before iteration and use fresh size checks inside loops when the array may be modified:

```pinescript
int fvg_size = array.size(g_fvg_array)
if barstate.isconfirmed and fvg_size > 0
    for i = fvg_size - 1 to 0
        if i >= 0 and i < array.size(g_fvg_array)  // Fresh size check
            fvg = array.get(g_fvg_array, i)
```

When removing elements during iteration, iterate **backwards** (from end to start) to avoid index shifting issues.

### Function Return Pattern

Functions that return optional values use `na` initialization and early return:

```pinescript
find_next_internal_high(int after_bar) =>
    float result = na
    int closest_bar = 999999
    // ... search logic that sets result
    result
```

Functions that return void (side-effect only) use `=>` with no explicit return:

```pinescript
detect_swing_points() =>
    if barstate.isconfirmed
        // ... modifies global arrays
```

### Drawing Object Lifecycle

Always delete old drawings before creating new ones in render functions:

```pinescript
if not na(fvg.box_id)
    box.delete(fvg.box_id)
if not na(fvg.label_id)
    label.delete(fvg.label_id)
// Then create new drawings
fvg.box_id := box.new(...)
```

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

1. Add a new `SECTION N` separator after the last existing section (before the Main Loop)
2. Number it sequentially (current last is Section 12)
3. Add corresponding step(s) in the Main Execution Loop (Section 12) in the correct processing order

### Adding New Inputs

1. Define a `GROUP_*` constant if creating a new settings group
2. Place the group constant immediately before its inputs
3. Use `i_` prefix for all input variables
4. Include `group=`, `tooltip=`, and bounds (`minval`/`maxval`) for every input
5. Place feature toggle (`input.bool`) first in each group

### Adding a New Custom Type

1. Define in Section 1 (Type Definitions)
2. Include inline comments for every field
3. Include drawing object references (`box_id`, `line_id`, `label_id`) if the type has visual representation
4. Create a corresponding `var array<TypeName>` in Section 3

### Adding a New Detection Function

1. Place in the appropriate engine section (5 for FVG, 6 for liquidity, 7 for BE/grading)
2. Gate all logic on `barstate.isconfirmed`
3. Return `na` for optional results
4. Use the sub-section separator pattern (`─────`)
5. Add a call in the Main Execution Loop in correct processing order

### Adding New Visual Elements

1. Add rendering function in Section 10 (Rendering)
2. Follow the delete-before-create lifecycle pattern
3. Store drawing references in the parent type
4. Guard all `*.delete()` calls with `not na()` checks
5. Respect user toggle inputs (check `i_show_*` before drawing)
6. Add cleanup logic in the type's `cleanup_*_array()` function

## Comment Conventions

### Function Documentation

Place a comment block above or as the sub-section header for each function explaining:
- What it does
- Parameters (if not obvious)
- Return value

```pinescript
// ─────────────────────────────────────────────────────────────────────
// Find nearest Draw on Liquidity (target)
// For bullish IFVG: find BSL (highs above)
// For bearish IFVG: find SSL (lows below)
// ─────────────────────────────────────────────────────────────────────
find_dol(bool is_bullish_ifvg, float current_price) =>
```

### Inline Comments

- Use `//` with a space after
- Place on same line for field documentation in types
- Place on own line for logic explanations
- Use `// NOTE:` prefix for important behavioral notes (see lines 978, 1073, 1122, 1157)
- Use `// RULE N:` prefix for numbered business rules within algorithm functions

### Status Enums (String Constants)

Document valid values as comments near the type definition:

```pinescript
// FVG Status Enum (using strings for clarity)
// "active"    - FVG detected, not yet inverted
// "inverted"  - FVG has been inverted (candle body closed through)
// "mitigated" - Price has fully closed through the inverted zone
```

## Git Commit Conventions

- **No AI attribution**: Do not include mentions of AI, Claude, or AI assistance in commit messages, PR descriptions, or code comments
- **No Co-Authored-By tags**: Do not add `Co-Authored-By: Claude` or similar
- **Message style**: Short descriptive messages
- **Phase prefix**: Use `Phase X:` prefix for major feature commits
- **Examples**: `Phase 3: Multi-Timeframe HTF Analysis`, `Phase 2.1: Bug fixes and UX improvements`, `Add PDA delivery detection for IFVG grading system`

## File Header Convention

The file starts with a decorative ASCII box listing version, creation date, and phase features:

```pinescript
// ╔══════════════════════════════════════════════════════════════════╗
// ║                     IFVG INDICATOR v3.0                          ║
// ║                     Phase 3: Multi-Timeframe                     ║
// ║                                                                  ║
// ║  Created: 2026-01-20                                             ║
// ║  Based on DodgysDD IFVG Strategy                                 ║
// ╚══════════════════════════════════════════════════════════════════╝
```

Update the version number and phase description when adding major features.

---

*Convention analysis: 2026-03-23*
