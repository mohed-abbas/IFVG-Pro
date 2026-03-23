# Codebase Structure

**Analysis Date:** 2026-03-23

## Directory Layout

```
IFVG-Pro/
├── src/
│   └── IFVG_Indicator.pine    # Main (and only) source file (2511 lines)
├── briefing/
│   ├── IFVG_Rating_System.pdf # Reference grading system from strategy creator
│   ├── strategy.zip           # Archived strategy screenshots
│   └── strategy/              # Strategy reference images (12 PNGs)
│       ├── 01-tableofcontent.png
│       ├── 02-basicModel.png
│       ├── 03-Entries.png
│       ├── 03-inversionModel.png
│       ├── 05-InversionEntries.png
│       ├── 06-StopLoses.png
│       ├── 07-StopLossPlacement.png
│       ├── 08-AdvanceDiscretion.png
│       ├── 09-BreakingTheRules.png
│       ├── 010-AlternateBEPoint.png
│       ├── 011-DrawOnLiquidity.png
│       └── 012-KeyTakeAway.png
├── .planning/
│   └── codebase/              # GSD analysis documents (this directory)
├── .claude/
│   └── settings.local.json    # Claude Code local settings
├── ARCHITECTURE.md            # Detailed technical specification (project doc)
├── PRD.md                     # Product requirements document (28KB)
├── CLAUDE.md                  # Claude Code project instructions
├── strategy.md                # Trading strategy rules reference
├── README.md                  # Project overview and documentation
├── PHASE4_PD_ZONES_PLAN.md   # Phase 4 implementation plan (uncommitted)
└── .gitignore                 # Git ignore rules
```

## Directory Purposes

**`src/`:**
- Purpose: Contains the indicator source code
- Contains: Single Pine Script v6 file
- Key files: `IFVG_Indicator.pine` -- the entire indicator implementation

**`briefing/`:**
- Purpose: Reference materials from the strategy creator (DodgysDD)
- Contains: PDF of the grading system, strategy screenshots
- Key files: `IFVG_Rating_System.pdf` -- the authoritative grading reference

**`.planning/codebase/`:**
- Purpose: GSD-generated analysis documents for development planning
- Contains: Architecture, structure, conventions, testing, concerns docs
- Generated: Yes (by GSD commands)
- Committed: Typically yes

**`.claude/`:**
- Purpose: Claude Code tool configuration
- Contains: Local settings
- Committed: Partially (settings.local.json is modified but tracked)

## Key File Locations

**Entry Points:**
- `src/IFVG_Indicator.pine`: The only source file. TradingView loads this directly.

**Configuration:**
- `CLAUDE.md`: Development workflow rules, commit conventions, architecture overview for AI assistants
- `.claude/settings.local.json`: Claude Code local tool settings

**Core Logic:**
- `src/IFVG_Indicator.pine`: All logic lives here -- 12 sections in a single file

**Documentation:**
- `ARCHITECTURE.md`: Full technical spec with algorithms, data types, module structure
- `PRD.md`: Product requirements, feature matrix, phase definitions
- `strategy.md`: Trading strategy rules (entries, stop losses, grading criteria)
- `briefing/IFVG_Rating_System.pdf`: Visual reference for the A+ to C grading system

## Code Organization Within `src/IFVG_Indicator.pine`

The file is organized into 12 numbered sections separated by `// ═══════` comment banners.

### Section Map

| Section | Name | Lines | Purpose |
|---------|------|-------|---------|
| Header | Version banner | 1-34 | Indicator declaration, `max_bars_back`/`max_boxes_count` limits |
| 1 | Type Definitions | 36-123 | 5 custom types: `FVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`, `IFVG` |
| 2 | Input Configuration | 124-283 | 9 input groups with 40+ user-configurable parameters |
| 3 | Global Variables & Data Stores | 284-307 | 7 `var` arrays for persistent state |
| 4 | Utility Functions | 310-597 | Helpers: colors, grades, cleanup, delivery, swing validation |
| 5 | FVG Detection | 598-643 | LTF 3-candle FVG pattern detection |
| 5B | HTF FVG Detection | 645-863 | HTF data via `request.security()`, HTF FVG/IFVG detection + mitigation |
| 6 | Swing Point & Liquidity Detection | 865-1223 | Swing detection, EQH/EQL, ITH/ITL, sweep detection |
| 7 | BE Point & Grading Functions | 1224-1465 | Swing search, DOL finding, momentum, SL calc, grading algorithm |
| 8 | Inversion Detection | 1466-1637 | FVG->IFVG conversion with full Phase 2 enhancements |
| 9 | BE Status & Mitigation Detection | 1638-1749 | BE/SL updates, DOL refresh, IFVG mitigation removal |
| 10 | Rendering | 1751-2289 | FVG boxes, IFVG boxes, HTF boxes, liquidity lines |
| 11 | Dashboard | 2308-2387 | Table widget showing counts, latest setup, HTF bias |
| 12 | Main Execution Loop | 2388-2511 | Orchestrates all steps in correct order |

### Section Dependencies

```
Section 12 (Main Loop) orchestrates everything:
  └─> Section 6 (Swing/Liquidity Detection)
  │     └─> Section 4 (Utilities: swing validation, EQH/EQL quality)
  │     └─> Section 3 (Data: g_swing_highs, g_swing_lows, g_liquidity_array)
  └─> Section 5/5B (FVG Detection)
  │     └─> Section 2 (Inputs: ATR period, min size mult)
  │     └─> Section 4 (Utilities: record_fvg_for_delivery, cleanup)
  │     └─> Section 3 (Data: g_fvg_array, g_htf_fvg_array)
  └─> Section 8 (Inversion Detection)
  │     └─> Section 7 (Grading: BE, SL, DOL, grade calculation)
  │     │     └─> Section 3 (Data: swing arrays, liquidity array)
  │     └─> Section 4 (Utilities: delivery check)
  │     └─> Section 3 (Data: g_fvg_array -> g_ifvg_array)
  └─> Section 9 (BE/Mitigation Updates)
  │     └─> Section 3 (Data: g_ifvg_array, g_liquidity_array)
  └─> Section 10/11 (Rendering/Dashboard)
        └─> Section 2 (Inputs: visual settings, visibility toggles)
        └─> Section 4 (Utilities: color/style helpers)
        └─> Section 3 (Data: all arrays for drawing)
```

### Input Group Organization (Section 2)

| Group Constant | Display Name | Lines | Parameters |
|---------------|--------------|-------|------------|
| `GROUP_GENERAL` | General Settings | 131-140 | Enable, max FVGs/IFVGs, display limit, extend bars |
| `GROUP_FVG` | FVG Detection | 145-154 | ATR period, min gap size, show active/inverted |
| `GROUP_HTF` | Higher Timeframe (HTF) | 159-175 | Enable, 2 timeframes, show HTF FVG/IFVG, filter LTF, opacity/border |
| `GROUP_LIQ` | Liquidity Detection | 180-186 | Swing lookback, show ITH/ITL, max levels |
| `GROUP_EQHL` | EQH/EQL Detection | 191-205 | Show EQH/EQL, perfect/relative tolerance, require intact, show swept |
| `GROUP_GRADE` | Grading Settings | 210-222 | Min grade display, show BE/SL, SL type, show grade label |
| `GROUP_DELIVERY` | Delivery Detection | 227-239 | Enable, lookback, body respect, show box, color/opacity |
| `GROUP_VISUAL` | Visual Settings | 244-258 | Bull/bear colors, opacity, label size/show, liquidity colors |
| `GROUP_IFVG_STYLE` | IFVG Style Settings | 263-273 | IFVG box color/opacity, entry line show/colors |
| `GROUP_BORDER` | Border Settings | 278-282 | FVG/IFVG border width and style |

### Type Definitions (Section 1)

| Type | Lines | Fields | Purpose |
|------|-------|--------|---------|
| `FVG` | 46-56 | 10 fields | Fair Value Gap with boundaries, direction, status, drawing refs |
| `SwingPoint` | 58-64 | 5 fields | Swing high/low with bar index and validity |
| `Liquidity` | 67-79 | 12 fields | EQH/EQL/ITH/ITL level with quality, sweep status, drawing refs |
| `DeliveryFVG` | 82-89 | 7 fields | Lightweight FVG record for delivery tracking |
| `IFVG` | 92-122 | 30 fields | Full trading setup with grade, BE, SL, entry, delivery, drawing refs |

### Global Data Store Arrays (Section 3)

| Array | Type | Line | Purpose |
|-------|------|------|---------|
| `g_fvg_array` | `array<FVG>` | 289 | Active (not yet inverted) LTF FVGs |
| `g_ifvg_array` | `array<IFVG>` | 290 | Active LTF inverted FVGs (trading setups) |
| `g_htf_fvg_array` | `array<FVG>` | 293 | HTF timeframe 1 active FVGs |
| `g_htf2_fvg_array` | `array<FVG>` | 294 | HTF timeframe 2 active FVGs |
| `g_htf_ifvg_array` | `array<IFVG>` | 295 | HTF timeframe 1 IFVGs (for bias) |
| `g_htf2_ifvg_array` | `array<IFVG>` | 296 | HTF timeframe 2 IFVGs (for bias) |
| `g_swing_highs` | `array<SwingPoint>` | 299 | Detected swing high points |
| `g_swing_lows` | `array<SwingPoint>` | 300 | Detected swing low points |
| `g_liquidity_array` | `array<Liquidity>` | 301 | All liquidity levels (EQH/EQL/ITH/ITL) |
| `g_delivery_history` | `array<DeliveryFVG>` | 304 | FVG records for delivery detection |

## Naming Conventions

**Files:**
- Single source file: `IFVG_Indicator.pine` (PascalCase with underscores)
- Documentation: UPPERCASE.md for major docs (`ARCHITECTURE.md`, `PRD.md`, `CLAUDE.md`)

**Variables:**
- Input variables: `i_` prefix (e.g., `i_show_indicator`, `i_fvg_atr_period`)
- Global arrays: `g_` prefix (e.g., `g_fvg_array`, `g_swing_highs`)
- Input group constants: `GROUP_` prefix in SCREAMING_SNAKE_CASE (e.g., `GROUP_GENERAL`)
- Local variables: snake_case (e.g., `bullish_gap_size`, `right_edge`)
- HTF variables: `htf_` or `htf2_` prefix (e.g., `htf_high`, `htf2_bar_idx`)

**Functions:**
- All functions: snake_case (e.g., `detect_fvg()`, `check_equal_highs()`, `render_ifvg_boxes()`)
- Cleanup functions: `cleanup_*_array()` pattern
- Detection functions: `detect_*()` or `check_*()` pattern
- Rendering functions: `render_*()` pattern
- Lookup functions: `find_*()` pattern

**Types:**
- Custom types: PascalCase (e.g., `FVG`, `IFVG`, `SwingPoint`, `Liquidity`, `DeliveryFVG`)

**Section Comments:**
- Major sections: `// ═══════` double-line separator with `SECTION N: NAME` label
- Sub-sections: `// ─────────` single-line separator with function purpose description

## Where to Add New Code

**New Detection Algorithm:**
- Add function in Sections 5-6 area (after existing detection, before grading)
- Add corresponding data type in Section 1 if needed
- Add `var array<Type>` in Section 3
- Add cleanup function in Section 4
- Wire into main loop in Section 12 (respect processing order)

**New Input Group:**
- Add in Section 2 after existing groups, before Section 3
- Follow pattern: `string GROUP_NAME = "═══ Name ═══"` then `i_var_name = input.type(..., group=GROUP_NAME)`

**New Rendering Function:**
- Add in Section 10 (before dashboard, Section 11)
- Follow pattern: delete old drawings first, then create new ones
- Call from Section 12 in the rendering step (after step 8)

**New Dashboard Row:**
- Add in `render_dashboard()` in Section 11 (line 2314)
- Increment table row count in `table.new()` at line 2312
- Add new `table.cell()` calls following existing pattern

**New Phase Feature (e.g., Phase 4):**
- Sessions: New Section between 6 and 7, new input group in Section 2
- PD Zones: New Section near 7, integrate with grading in `calculate_grade()`
- Alerts: New Section 12B after main loop, using `alertcondition()`
- Reference `PHASE4_PD_ZONES_PLAN.md` for detailed Phase 4 plans

## Special Directories

**`briefing/`:**
- Purpose: Original strategy reference materials from DodgysDD
- Generated: No (manually collected)
- Committed: Yes
- Note: Contains the authoritative grading system PDF that `calculate_grade()` implements

**`.planning/`:**
- Purpose: GSD development planning and analysis
- Generated: Yes (by GSD commands)
- Committed: Yes

---

*Structure analysis: 2026-03-23*
