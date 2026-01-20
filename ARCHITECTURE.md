# IFVG Indicator - Technical Architecture

> **Version**: 1.0
> **Created**: 2026-01-20
> **Platform**: TradingView Pine Script v6
> **Document Type**: Technical Design Specification

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Module Structure](#2-module-structure)
3. [Data Types & Structures](#3-data-types--structures)
4. [Core Algorithms](#4-core-algorithms)
5. [Data Flow](#5-data-flow)
6. [Memory Management](#6-memory-management)
7. [Multi-Timeframe Architecture](#7-multi-timeframe-architecture)
8. [Rendering Pipeline](#8-rendering-pipeline)
9. [Alert System Architecture](#9-alert-system-architecture)
10. [Configuration System](#10-configuration-system)
11. [File Structure](#11-file-structure)

---

## 1. Architecture Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        IFVG INDICATOR                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────┐ │
│  │   INPUTS    │───▶│   ENGINE    │───▶│      RENDERING          │ │
│  │  (Config)   │    │   (Core)    │    │   (Visualization)       │ │
│  └─────────────┘    └─────────────┘    └─────────────────────────┘ │
│         │                  │                       │                │
│         │                  ▼                       │                │
│         │          ┌─────────────┐                 │                │
│         │          │    DATA     │                 │                │
│         └─────────▶│   STORE     │◀────────────────┘                │
│                    │  (Arrays)   │                                  │
│                    └─────────────┘                                  │
│                          │                                          │
│                          ▼                                          │
│                    ┌─────────────┐                                  │
│                    │   ALERTS    │                                  │
│                    └─────────────┘                                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Modularity** | Separate functions for detection, grading, rendering |
| **Efficiency** | Process only on confirmed bars, cache calculations |
| **Clarity** | Clear naming, documented functions |
| **Maintainability** | Logical groupings, consistent patterns |
| **No Repainting** | All calculations on `barstate.isconfirmed` |

---

## 2. Module Structure

### 2.1 Logical Modules

```
IFVG_Indicator/
│
├── 📦 INPUTS MODULE
│   ├── General Settings
│   ├── FVG Detection Settings
│   ├── Liquidity Detection Settings
│   ├── Session Settings
│   ├── Visual Settings
│   └── Alert Settings
│
├── 📦 TYPES MODULE
│   ├── type FVG
│   ├── type IFVG
│   ├── type Liquidity
│   ├── type Setup
│   └── type SessionData
│
├── 📦 DETECTION ENGINE
│   ├── FVG Detection
│   │   ├── detect_fvg()
│   │   └── detect_htf_fvg()
│   │
│   ├── Inversion Detection
│   │   ├── check_inversion()
│   │   └── validate_inversion()
│   │
│   └── Liquidity Detection
│       ├── detect_swing_points()
│       ├── find_equal_levels()
│       ├── detect_internal_levels()
│       └── check_liquidity_sweep()
│
├── 📦 GRADING ENGINE
│   ├── assess_mandatory_criteria()
│   ├── calculate_quality_score()
│   ├── determine_grade()
│   └── assess_momentum()
│
├── 📦 BE TRACKING
│   ├── find_be_point()
│   ├── check_be_validity()
│   └── update_be_status()
│
├── 📦 ZONE CALCULATOR
│   ├── calculate_daily_range()
│   ├── determine_pd_zone()
│   └── get_zone_percentage()
│
├── 📦 SESSION TRACKER
│   ├── is_in_session()
│   ├── update_session_levels()
│   └── get_session_data()
│
├── 📦 RENDERING ENGINE
│   ├── draw_fvg_box()
│   ├── draw_liquidity_line()
│   ├── draw_be_level()
│   ├── draw_pd_zones()
│   ├── draw_dashboard()
│   └── cleanup_old_drawings()
│
└── 📦 ALERT SYSTEM
    ├── check_alert_conditions()
    └── format_alert_message()
```

### 2.2 Pine Script Organization

```pinescript
//@version=6
indicator("IFVG Indicator", overlay=true, max_bars_back=500, max_boxes_count=500, max_lines_count=500, max_labels_count=500)

// ══════════════════════════════════════════════════════════════════
// SECTION 1: TYPE DEFINITIONS
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 2: INPUT CONFIGURATION
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 3: GLOBAL VARIABLES & DATA STORES
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 4: UTILITY FUNCTIONS
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 5: FVG DETECTION
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 6: LIQUIDITY DETECTION
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 7: INVERSION & BE TRACKING
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 8: GRADING SYSTEM
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 9: ZONE CALCULATIONS
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 10: SESSION TRACKING
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 11: RENDERING
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 12: DASHBOARD
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 13: ALERTS
// ══════════════════════════════════════════════════════════════════

// ══════════════════════════════════════════════════════════════════
// SECTION 14: MAIN EXECUTION LOOP
// ══════════════════════════════════════════════════════════════════
```

---

## 3. Data Types & Structures

### 3.1 Core Type Definitions

```pinescript
// ══════════════════════════════════════════════════════════════════
// TYPE: FVG (Fair Value Gap)
// ══════════════════════════════════════════════════════════════════
type FVG
    float top           // Upper boundary of gap
    float bottom        // Lower boundary of gap
    float mid           // Midpoint (for reference)
    int start_bar       // Bar index where FVG starts
    int end_bar         // Bar index where FVG ends (extends until mitigated)
    bool is_bullish     // true = bullish FVG, false = bearish FVG
    string status       // "active", "inverted", "mitigated"
    string timeframe    // Source timeframe ("" for current, "60" for 1H, etc.)
    box box_id          // Reference to drawn box (na if not drawn)

// ══════════════════════════════════════════════════════════════════
// TYPE: IFVG (Inverted Fair Value Gap)
// ══════════════════════════════════════════════════════════════════
type IFVG
    FVG source_fvg      // Original FVG that was inverted
    int inversion_bar   // Bar index where inversion occurred
    float inversion_close  // Close price of inversion candle
    string grade        // "A+", "A", "A-", "B+", "B", "B-", "C"
    bool entry_valid    // true if BE point intact at inversion
    float be_level      // Break-even level (internal H/L)
    float stop_loss     // Calculated stop loss level
    string be_status    // "intact", "taken"
    Liquidity dol       // Draw on Liquidity (target)
    box box_id          // Reference to drawn box
    label label_id      // Reference to grade label
    line be_line_id     // Reference to BE line

// ══════════════════════════════════════════════════════════════════
// TYPE: Liquidity
// ══════════════════════════════════════════════════════════════════
type Liquidity
    float level         // Price level
    string liq_type     // "EQH", "EQL", "ITH", "ITL", "DATA_H", "DATA_L", "LRLR"
    int bar_index       // Bar where liquidity was identified
    int touch_count     // Number of touches (for EQH/EQL)
    bool is_swept       // true if liquidity has been taken
    int swept_bar       // Bar index where sweep occurred
    line line_id        // Reference to drawn line
    label label_id      // Reference to label

// ══════════════════════════════════════════════════════════════════
// TYPE: SwingPoint
// ══════════════════════════════════════════════════════════════════
type SwingPoint
    float price         // Swing high/low price
    int bar_index       // Bar index of swing
    bool is_high        // true = swing high, false = swing low
    bool is_internal    // true = internal structure, false = external

// ══════════════════════════════════════════════════════════════════
// TYPE: SessionData
// ══════════════════════════════════════════════════════════════════
type SessionData
    string name         // "Asian", "London", "NY"
    float high          // Session high
    float low           // Session low
    int high_bar        // Bar index of high
    int low_bar         // Bar index of low
    bool is_active      // Currently in this session

// ══════════════════════════════════════════════════════════════════
// TYPE: Setup (Complete trade setup)
// ══════════════════════════════════════════════════════════════════
type Setup
    IFVG ifvg           // The inverted FVG
    bool has_sweep      // Liquidity sweep present
    bool has_fvg_delivery  // Delivery from another FVG
    string momentum     // "strong_no_chop", "neutral", "weak_or_choppy"
    bool in_optimal_zone   // Long in discount / Short in premium
    bool in_wrong_zone     // Long in premium / Short in discount
    bool fvg_is_singular   // Single FVG (not series)
    bool fvg_is_obvious    // Clearly visible FVG
    bool has_smt        // SMT divergence present (bonus)
    string grade        // Final calculated grade

// ══════════════════════════════════════════════════════════════════
// TYPE: DailyRange
// ══════════════════════════════════════════════════════════════════
type DailyRange
    float high          // Daily high
    float low           // Daily low
    float range         // high - low
    float equilibrium   // 50% level
    float premium_start // Start of premium zone
    float discount_end  // End of discount zone
```

### 3.2 Global Data Stores

```pinescript
// ══════════════════════════════════════════════════════════════════
// GLOBAL ARRAYS (Data Stores)
// ══════════════════════════════════════════════════════════════════

// FVG Storage
var array<FVG> g_fvg_array = array.new<FVG>()
var array<FVG> g_htf_fvg_array = array.new<FVG>()

// IFVG Storage
var array<IFVG> g_ifvg_array = array.new<IFVG>()
var array<IFVG> g_htf_ifvg_array = array.new<IFVG>()

// Liquidity Storage
var array<Liquidity> g_liquidity_array = array.new<Liquidity>()
var array<SwingPoint> g_swing_array = array.new<SwingPoint>()

// Session Storage
var array<SessionData> g_sessions = array.new<SessionData>()

// Current State
var IFVG g_best_ifvg = na           // Best grade active IFVG
var string g_htf_bias = "neutral"    // "bullish", "bearish", "neutral"
var DailyRange g_daily_range = na    // Current daily range data

// Drawing References (for cleanup)
var array<box> g_boxes = array.new<box>()
var array<line> g_lines = array.new<line>()
var array<label> g_labels = array.new<label>()
```

---

## 4. Core Algorithms

### 4.1 FVG Detection Algorithm

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: detect_fvg()
// PURPOSE: Detect Fair Value Gaps on current timeframe
// RETURNS: FVG object or na
// ══════════════════════════════════════════════════════════════════
detect_fvg() =>
    FVG result = na

    // Only process on confirmed bars
    if barstate.isconfirmed
        // Calculate minimum gap size (ATR-based)
        atr_val = ta.atr(i_fvg_atr_period)
        min_gap = atr_val * i_fvg_min_size_mult

        // Check for Bullish FVG: low[0] > high[2]
        bullish_gap = low - high[2]
        if bullish_gap > min_gap
            result := FVG.new(
                top = low,
                bottom = high[2],
                mid = (low + high[2]) / 2,
                start_bar = bar_index - 2,
                end_bar = bar_index,
                is_bullish = true,
                status = "active",
                timeframe = "",
                box_id = na
            )

        // Check for Bearish FVG: high[0] < low[2]
        bearish_gap = low[2] - high
        if bearish_gap > min_gap
            result := FVG.new(
                top = low[2],
                bottom = high,
                mid = (low[2] + high) / 2,
                start_bar = bar_index - 2,
                end_bar = bar_index,
                is_bullish = false,
                status = "active",
                timeframe = "",
                box_id = na
            )

    result
```

### 4.2 Inversion Detection Algorithm

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: check_inversion()
// PURPOSE: Check if any active FVG has been inverted
// RETURNS: Array of newly inverted IFVGs
// ══════════════════════════════════════════════════════════════════
check_inversion() =>
    array<IFVG> new_inversions = array.new<IFVG>()

    if barstate.isconfirmed
        for i = 0 to array.size(g_fvg_array) - 1
            fvg = array.get(g_fvg_array, i)

            if fvg.status == "active"
                // Bullish FVG inversion: candle body closes BELOW the FVG
                if fvg.is_bullish
                    // For bullish FVG to invert, we need price to come back
                    // and close below it (turns into support)
                    body_close = close
                    if body_close > fvg.top
                        // Price closed above bullish FVG = INVERTED
                        fvg.status := "inverted"

                        // Find BE point (next internal low)
                        be_level = find_next_internal_low(fvg.start_bar)

                        // Check if BE is still intact
                        entry_valid = low > be_level

                        // Create IFVG
                        new_ifvg = IFVG.new(
                            source_fvg = fvg,
                            inversion_bar = bar_index,
                            inversion_close = close,
                            grade = "",  // Will be calculated
                            entry_valid = entry_valid,
                            be_level = be_level,
                            stop_loss = calculate_stop_loss(fvg, close),
                            be_status = entry_valid ? "intact" : "taken",
                            dol = find_nearest_bsl(),  // Find buy-side liquidity
                            box_id = na,
                            label_id = na,
                            be_line_id = na
                        )

                        array.push(new_inversions, new_ifvg)

                // Bearish FVG inversion: candle body closes ABOVE the FVG
                else
                    body_close = close
                    if body_close < fvg.bottom
                        // Price closed below bearish FVG = INVERTED
                        fvg.status := "inverted"

                        // Find BE point (next internal high)
                        be_level = find_next_internal_high(fvg.start_bar)

                        // Check if BE is still intact
                        entry_valid = high < be_level

                        // Create IFVG
                        new_ifvg = IFVG.new(
                            source_fvg = fvg,
                            inversion_bar = bar_index,
                            inversion_close = close,
                            grade = "",
                            entry_valid = entry_valid,
                            be_level = be_level,
                            stop_loss = calculate_stop_loss(fvg, close),
                            be_status = entry_valid ? "intact" : "taken",
                            dol = find_nearest_ssl(),  // Find sell-side liquidity
                            box_id = na,
                            label_id = na,
                            be_line_id = na
                        )

                        array.push(new_inversions, new_ifvg)

    new_inversions
```

### 4.3 Swing Structure Detection Algorithm

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: detect_swing_points()
// PURPOSE: Identify swing highs and lows using structure-based logic
// ══════════════════════════════════════════════════════════════════
detect_swing_points() =>
    if barstate.isconfirmed
        lookback = i_swing_lookback

        // Detect swing high
        is_swing_high = true
        for j = 1 to lookback
            if high[lookback] <= high[lookback - j] or high[lookback] <= high[lookback + j]
                is_swing_high := false
                break

        if is_swing_high
            // Determine if internal or external based on structure
            is_internal = check_if_internal_structure(bar_index - lookback, true)

            new_swing = SwingPoint.new(
                price = high[lookback],
                bar_index = bar_index - lookback,
                is_high = true,
                is_internal = is_internal
            )
            array.push(g_swing_array, new_swing)

            // Check for EQH formation
            check_equal_highs(new_swing)

        // Detect swing low
        is_swing_low = true
        for j = 1 to lookback
            if low[lookback] >= low[lookback - j] or low[lookback] >= low[lookback + j]
                is_swing_low := false
                break

        if is_swing_low
            is_internal = check_if_internal_structure(bar_index - lookback, false)

            new_swing = SwingPoint.new(
                price = low[lookback],
                bar_index = bar_index - lookback,
                is_high = false,
                is_internal = is_internal
            )
            array.push(g_swing_array, new_swing)

            // Check for EQL formation
            check_equal_lows(new_swing)

// ══════════════════════════════════════════════════════════════════
// FUNCTION: check_equal_highs()
// PURPOSE: Check if new swing high forms EQH with existing highs
// ══════════════════════════════════════════════════════════════════
check_equal_highs(SwingPoint new_high) =>
    atr_val = ta.atr(14)
    tolerance = atr_val * i_eqhl_tolerance

    for i = 0 to array.size(g_liquidity_array) - 1
        liq = array.get(g_liquidity_array, i)
        if liq.liq_type == "EQH" and not liq.is_swept
            // Check if within tolerance
            if math.abs(new_high.price - liq.level) <= tolerance
                // Update existing EQH
                liq.touch_count := liq.touch_count + 1
                liq.level := (liq.level + new_high.price) / 2  // Average
                return

    // No existing EQH found, check recent swing highs for match
    for i = array.size(g_swing_array) - 2 to math.max(0, array.size(g_swing_array) - 20) by 1
        swing = array.get(g_swing_array, i)
        if swing.is_high and math.abs(swing.price - new_high.price) <= tolerance
            // Create new EQH
            new_liq = Liquidity.new(
                level = (swing.price + new_high.price) / 2,
                liq_type = "EQH",
                bar_index = new_high.bar_index,
                touch_count = 2,
                is_swept = false,
                swept_bar = 0,
                line_id = na,
                label_id = na
            )
            array.push(g_liquidity_array, new_liq)
            break
```

### 4.4 Grading Algorithm (Pine Script Implementation)

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: calculate_grade()
// PURPOSE: Calculate setup grade using hybrid approach
// RETURNS: Grade string ("A+", "A", "A-", "B+", "B", "B-", "C")
// ══════════════════════════════════════════════════════════════════
calculate_grade(Setup setup) =>
    string result = "C"

    // ═══════════════════════════════════════════════════════════
    // STEP 1: MANDATORY CRITERIA → DETERMINE TIER
    // ═══════════════════════════════════════════════════════════

    // Must have clear DOL
    if na(setup.ifvg.dol) or setup.ifvg.dol.level == 0
        result := "C"
    else
        // Must have identifiable FVG (always true if we got here)
        string tier = "C"

        // Tier based on liquidity context
        if setup.has_sweep and setup.has_fvg_delivery
            tier := "A"
        else if setup.has_sweep or setup.has_fvg_delivery
            tier := "A"
        else
            tier := "B"

        // ═══════════════════════════════════════════════════════
        // STEP 2: QUALITY CRITERIA → DETERMINE MODIFIER
        // ═══════════════════════════════════════════════════════

        int quality_score = 0

        // Momentum (+1 / -1)
        if setup.momentum == "strong_no_chop"
            quality_score := quality_score + 1
        else if setup.momentum == "weak_or_choppy"
            quality_score := quality_score - 1

        // Premium/Discount (+1 / -1)
        if setup.in_optimal_zone
            quality_score := quality_score + 1
        else if setup.in_wrong_zone
            quality_score := quality_score - 1

        // FVG Clarity (+1 / -1)
        if setup.fvg_is_singular and setup.fvg_is_obvious
            quality_score := quality_score + 1
        else if not setup.fvg_is_singular or not setup.fvg_is_obvious
            quality_score := quality_score - 1

        // Bonus: Both sweep AND delivery
        if setup.has_sweep and setup.has_fvg_delivery
            quality_score := quality_score + 1

        // Bonus: SMT divergence
        if setup.has_smt
            quality_score := quality_score + 1

        // ═══════════════════════════════════════════════════════
        // STEP 3: COMBINE TIER + MODIFIER
        // ═══════════════════════════════════════════════════════

        if tier == "A"
            if quality_score >= 3
                result := "A+"
            else if quality_score >= 1
                result := "A"
            else if quality_score >= -1
                result := "A-"
            else
                result := "B+"

        else if tier == "B"
            if quality_score >= 2
                result := "B+"
            else if quality_score >= 0
                result := "B"
            else
                result := "B-"

        else
            result := "C"

    result

// ══════════════════════════════════════════════════════════════════
// FUNCTION: assess_momentum()
// PURPOSE: Assess momentum quality of inversion candle
// RETURNS: "strong_no_chop", "neutral", "weak_or_choppy"
// ══════════════════════════════════════════════════════════════════
assess_momentum(int inversion_bar) =>
    string result = "neutral"

    candle_body = math.abs(close[bar_index - inversion_bar] - open[bar_index - inversion_bar])
    candle_range = high[bar_index - inversion_bar] - low[bar_index - inversion_bar]
    atr_val = ta.atr(14)

    if candle_range > 0
        body_ratio = candle_body / candle_range

        if body_ratio > 0.7 and candle_range > atr_val
            result := "strong_no_chop"
        else if body_ratio < 0.3 or candle_range < atr_val * 0.5
            result := "weak_or_choppy"

    result
```

---

## 5. Data Flow

### 5.1 Main Execution Flow

```
┌────────────────────────────────────────────────────────────────────┐
│                     MAIN EXECUTION LOOP                            │
│                    (Runs on each bar)                              │
└────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────┐
                    │ barstate.isconfirmed? │
                    └───────────────────┘
                          │ Yes
                          ▼
        ┌─────────────────────────────────────────┐
        │         1. UPDATE DAILY RANGE           │
        │    calculate_daily_range()              │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         2. UPDATE SESSIONS              │
        │    update_session_data()                │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         3. DETECT SWING POINTS          │
        │    detect_swing_points()                │
        │    → Updates g_swing_array              │
        │    → Updates g_liquidity_array (EQH/L)  │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         4. CHECK LIQUIDITY SWEEPS       │
        │    check_liquidity_sweeps()             │
        │    → Marks swept liquidity              │
        │    → Triggers reversal model check      │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         5. DETECT NEW FVGs              │
        │    detect_fvg()                         │
        │    detect_htf_fvg()                     │
        │    → Adds to g_fvg_array                │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         6. CHECK INVERSIONS             │
        │    check_inversion()                    │
        │    → Creates IFVG from FVG              │
        │    → Calculates BE point                │
        │    → Validates entry                    │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         7. CHECK MITIGATIONS            │
        │    check_mitigation()                   │
        │    → Removes mitigated IFVGs            │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         8. UPDATE BE STATUS             │
        │    update_be_status()                   │
        │    → Checks if BE points taken          │
        │    → Updates entry_valid                │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         9. GRADE SETUPS                 │
        │    For each new IFVG:                   │
        │    build_setup() → calculate_grade()   │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         10. SELECT BEST IFVG            │
        │    find_best_ifvg()                     │
        │    → Updates g_best_ifvg                │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         11. RENDER                      │
        │    render_fvg_boxes()                   │
        │    render_liquidity_lines()             │
        │    render_pd_zones()                    │
        │    render_dashboard()                   │
        └─────────────────────────────────────────┘
                          │
                          ▼
        ┌─────────────────────────────────────────┐
        │         12. CHECK & FIRE ALERTS         │
        │    check_alert_conditions()             │
        └─────────────────────────────────────────┘
```

### 5.2 FVG Lifecycle

```
┌──────────────┐    Detection    ┌──────────────┐
│   Candles    │ ─────────────▶  │  FVG Created │
│   Form Gap   │                 │   (active)   │
└──────────────┘                 └──────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
            │   No Touch   │    │   Inverted   │    │  Mitigated   │
            │  (remains    │    │  (body close │    │  (body close │
            │   active)    │    │   through)   │    │   through    │
            └──────────────┘    └──────────────┘    │   opposite)  │
                                       │            └──────────────┘
                                       │                   │
                                       ▼                   │
                               ┌──────────────┐            │
                               │ IFVG Created │            │
                               │  + Graded    │            │
                               └──────────────┘            │
                                       │                   │
                    ┌──────────────────┼──────────────────┐│
                    │                  │                  ││
                    ▼                  ▼                  ▼▼
            ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
            │  Entry Valid │   │Entry Invalid │   │   Removed    │
            │  (BE intact) │   │  (BE taken)  │   │ from chart   │
            └──────────────┘   └──────────────┘   └──────────────┘
                    │                  │
                    ▼                  │
            ┌──────────────┐           │
            │   ALERT!     │           │
            │ (if grade    │           │
            │  meets min)  │           │
            └──────────────┘           │
                    │                  │
                    └────────┬─────────┘
                             ▼
                     ┌──────────────┐
                     │  Mitigated   │
                     │  → Removed   │
                     └──────────────┘
```

---

## 6. Memory Management

### 6.1 Array Size Limits

```pinescript
// ══════════════════════════════════════════════════════════════════
// CONSTANTS: Memory Limits
// ══════════════════════════════════════════════════════════════════
MAX_FVGS = 50           // Maximum FVGs to track
MAX_IFVGS = 20          // Maximum IFVGs to track
MAX_LIQUIDITY = 100     // Maximum liquidity levels
MAX_SWINGS = 200        // Maximum swing points
MAX_DRAWINGS = 500      // TradingView limit per type
```

### 6.2 Cleanup Functions

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: cleanup_old_fvgs()
// PURPOSE: Remove old FVGs when array exceeds limit
// ══════════════════════════════════════════════════════════════════
cleanup_old_fvgs() =>
    while array.size(g_fvg_array) > MAX_FVGS
        old_fvg = array.shift(g_fvg_array)  // Remove oldest
        if not na(old_fvg.box_id)
            box.delete(old_fvg.box_id)

// ══════════════════════════════════════════════════════════════════
// FUNCTION: cleanup_mitigated()
// PURPOSE: Remove mitigated IFVGs from tracking
// ══════════════════════════════════════════════════════════════════
cleanup_mitigated() =>
    for i = array.size(g_ifvg_array) - 1 to 0 by 1
        ifvg = array.get(g_ifvg_array, i)
        if ifvg.source_fvg.status == "mitigated"
            // Delete drawings
            if not na(ifvg.box_id)
                box.delete(ifvg.box_id)
            if not na(ifvg.label_id)
                label.delete(ifvg.label_id)
            if not na(ifvg.be_line_id)
                line.delete(ifvg.be_line_id)
            // Remove from array
            array.remove(g_ifvg_array, i)

// ══════════════════════════════════════════════════════════════════
// FUNCTION: cleanup_swept_liquidity()
// PURPOSE: Remove old swept liquidity levels
// ══════════════════════════════════════════════════════════════════
cleanup_swept_liquidity() =>
    // Keep swept liquidity visible for N bars, then remove
    for i = array.size(g_liquidity_array) - 1 to 0 by 1
        liq = array.get(g_liquidity_array, i)
        if liq.is_swept and bar_index - liq.swept_bar > 100
            if not na(liq.line_id)
                line.delete(liq.line_id)
            if not na(liq.label_id)
                label.delete(liq.label_id)
            array.remove(g_liquidity_array, i)
```

### 6.3 Drawing Management

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: manage_drawings()
// PURPOSE: Ensure we don't exceed TradingView drawing limits
// ══════════════════════════════════════════════════════════════════
manage_drawings() =>
    // Count current drawings
    box_count = array.size(g_boxes)
    line_count = array.size(g_lines)
    label_count = array.size(g_labels)

    // If approaching limits, remove oldest
    while box_count > MAX_DRAWINGS - 50
        old_box = array.shift(g_boxes)
        box.delete(old_box)
        box_count := box_count - 1

    while line_count > MAX_DRAWINGS - 50
        old_line = array.shift(g_lines)
        line.delete(old_line)
        line_count := line_count - 1

    while label_count > MAX_DRAWINGS - 50
        old_label = array.shift(g_labels)
        label.delete(old_label)
        label_count := label_count - 1
```

---

## 7. Multi-Timeframe Architecture

### 7.1 HTF Data Request Pattern

```pinescript
// ══════════════════════════════════════════════════════════════════
// HTF DATA REQUESTS (v6 Dynamic Requests)
// ══════════════════════════════════════════════════════════════════

// User-selected HTF timeframes (series string - v6 feature)
string htf1 = i_htf_timeframe_1
string htf2 = i_htf_timeframe_2

// Request HTF OHLC data
[htf1_open, htf1_high, htf1_low, htf1_close] = request.security(
    syminfo.tickerid,
    htf1,
    [open, high, low, close],
    lookahead = barmerge.lookahead_off
)

[htf2_open, htf2_high, htf2_low, htf2_close] = request.security(
    syminfo.tickerid,
    htf2,
    [open, high, low, close],
    lookahead = barmerge.lookahead_off
)

// ══════════════════════════════════════════════════════════════════
// FUNCTION: detect_htf_fvg()
// PURPOSE: Detect FVGs on HTF using requested data
// ══════════════════════════════════════════════════════════════════
detect_htf_fvg(string tf, float h2, float l0, float h0, float l2) =>
    FVG result = na

    atr_val = ta.atr(14)  // Use current TF ATR as reference
    min_gap = atr_val * i_fvg_min_size_mult * 2  // HTF gaps should be larger

    // Bullish FVG check
    if l0 - h2 > min_gap
        result := FVG.new(
            top = l0,
            bottom = h2,
            mid = (l0 + h2) / 2,
            start_bar = bar_index,
            end_bar = bar_index,
            is_bullish = true,
            status = "active",
            timeframe = tf,
            box_id = na
        )

    // Bearish FVG check
    if l2 - h0 > min_gap
        result := FVG.new(
            top = l2,
            bottom = h0,
            mid = (l2 + h0) / 2,
            start_bar = bar_index,
            end_bar = bar_index,
            is_bullish = false,
            status = "active",
            timeframe = tf,
            box_id = na
        )

    result
```

### 7.2 HTF Overlay Projection

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: project_htf_to_ltf()
// PURPOSE: Draw HTF FVG/IFVG zones on LTF chart
// ══════════════════════════════════════════════════════════════════
project_htf_to_ltf(FVG htf_fvg) =>
    if i_show_htf_overlay and not na(htf_fvg)
        // Determine colors based on bullish/bearish and status
        bg_color = htf_fvg.is_bullish ? color.new(i_bullish_color, 85) : color.new(i_bearish_color, 85)
        border_color = htf_fvg.is_bullish ? i_bullish_color : i_bearish_color

        // Create box with thicker border for HTF
        htf_box = box.new(
            left = htf_fvg.start_bar,
            top = htf_fvg.top,
            right = bar_index + 20,  // Extend into future
            bottom = htf_fvg.bottom,
            bgcolor = bg_color,
            border_color = border_color,
            border_width = 3,  // Thicker than LTF boxes
            border_style = line.style_solid
        )

        // Label with timeframe
        htf_label = label.new(
            x = bar_index,
            y = htf_fvg.top,
            text = "[" + htf_fvg.timeframe + "] " + (htf_fvg.status == "inverted" ? "IFVG" : "FVG"),
            style = label.style_label_down,
            color = color.new(border_color, 50),
            textcolor = color.white,
            size = size.small
        )

        // Track drawings
        array.push(g_boxes, htf_box)
        array.push(g_labels, htf_label)
```

---

## 8. Rendering Pipeline

### 8.1 Rendering Order

```
1. Background Layer
   └── Premium/Discount zone shading

2. Zone Layer
   └── FVG/IFVG boxes (HTF first, then LTF)

3. Level Layer
   └── Liquidity lines
   └── BE point lines
   └── Session H/L lines

4. Label Layer
   └── FVG/IFVG grade labels
   └── Liquidity type labels
   └── BE labels

5. Dashboard Layer (Table)
   └── Info panel
```

### 8.2 Box Rendering Function

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: render_ifvg_box()
// PURPOSE: Draw IFVG box with grade label
// ══════════════════════════════════════════════════════════════════
render_ifvg_box(IFVG ifvg) =>
    if not na(ifvg) and ifvg.source_fvg.status == "inverted"
        fvg = ifvg.source_fvg

        // Color based on direction
        bg_color = fvg.is_bullish ? color.new(i_bullish_color, 100 - i_ifvg_opacity) : color.new(i_bearish_color, 100 - i_ifvg_opacity)
        border_color = fvg.is_bullish ? i_bullish_color : i_bearish_color
        border_style = line.style_dashed  // Dashed for IFVG

        // Delete old box if exists
        if not na(ifvg.box_id)
            box.delete(ifvg.box_id)

        // Create new box
        ifvg.box_id := box.new(
            left = fvg.start_bar,
            top = fvg.top,
            right = bar_index + 10,
            bottom = fvg.bottom,
            bgcolor = bg_color,
            border_color = border_color,
            border_width = 2,
            border_style = border_style
        )

        // Delete old label if exists
        if not na(ifvg.label_id)
            label.delete(ifvg.label_id)

        // Grade label
        label_text = "IFVG " + ifvg.grade
        label_color = grade_to_color(ifvg.grade)

        ifvg.label_id := label.new(
            x = bar_index,
            y = fvg.is_bullish ? fvg.bottom : fvg.top,
            text = label_text,
            style = fvg.is_bullish ? label.style_label_up : label.style_label_down,
            color = color.new(label_color, 20),
            textcolor = color.white,
            size = size.normal
        )

        // Track drawings
        array.push(g_boxes, ifvg.box_id)
        array.push(g_labels, ifvg.label_id)
```

### 8.3 Dashboard Rendering

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: render_dashboard()
// PURPOSE: Draw info dashboard panel
// ══════════════════════════════════════════════════════════════════
render_dashboard() =>
    if i_show_dashboard
        // Create table
        var table dashboard = table.new(
            position = position_from_string(i_dashboard_position),
            columns = 2,
            rows = 8,
            bgcolor = color.new(color.black, 30),
            border_width = 1,
            border_color = color.gray
        )

        // Row 0: Title
        table.cell(dashboard, 0, 0, "IFVG INDICATOR", text_color=color.white, text_size=size.normal)
        table.merge_cells(dashboard, 0, 0, 1, 0)

        // Row 1: HTF Bias
        bias_color = g_htf_bias == "bullish" ? color.green : g_htf_bias == "bearish" ? color.red : color.gray
        table.cell(dashboard, 0, 1, "HTF Bias:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 1, str.upper(g_htf_bias), text_color=bias_color, text_size=size.small)

        // Row 2: DOL
        dol_text = not na(g_best_ifvg) and not na(g_best_ifvg.dol) ?
            g_best_ifvg.dol.liq_type + " @ " + str.tostring(g_best_ifvg.dol.level, format.mintick) : "None"
        table.cell(dashboard, 0, 2, "DOL:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 2, dol_text, text_color=color.white, text_size=size.small)

        // Row 3: Active Setup
        setup_text = not na(g_best_ifvg) ? g_best_ifvg.grade + " IFVG" : "None"
        setup_color = not na(g_best_ifvg) ? grade_to_color(g_best_ifvg.grade) : color.gray
        table.cell(dashboard, 0, 3, "Setup:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 3, setup_text, text_color=setup_color, text_size=size.small)

        // Row 4: Entry Status
        entry_text = not na(g_best_ifvg) ? (g_best_ifvg.entry_valid ? "VALID" : "INVALID") : "-"
        entry_color = not na(g_best_ifvg) and g_best_ifvg.entry_valid ? color.green : color.red
        table.cell(dashboard, 0, 4, "Entry:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 4, entry_text, text_color=entry_color, text_size=size.small)

        // Row 5: BE Level
        be_text = not na(g_best_ifvg) ? str.tostring(g_best_ifvg.be_level, format.mintick) : "-"
        table.cell(dashboard, 0, 5, "BE Level:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 5, be_text, text_color=color.white, text_size=size.small)

        // Row 6: Zone
        zone_pct = not na(g_daily_range) ?
            ((close - g_daily_range.low) / g_daily_range.range) * 100 : 50
        zone_text = zone_pct > 50 ? "PREMIUM" : "DISCOUNT"
        zone_text := zone_text + " (" + str.tostring(zone_pct, "#.0") + "%)"
        zone_color = zone_pct > 50 ? color.red : color.green
        table.cell(dashboard, 0, 6, "Zone:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 6, zone_text, text_color=zone_color, text_size=size.small)

        // Row 7: Session
        session_text = get_current_session_name()
        table.cell(dashboard, 0, 7, "Session:", text_color=color.gray, text_size=size.small)
        table.cell(dashboard, 1, 7, session_text, text_color=color.white, text_size=size.small)
```

---

## 9. Alert System Architecture

### 9.1 Alert Conditions

```pinescript
// ══════════════════════════════════════════════════════════════════
// ALERT CONDITIONS
// ══════════════════════════════════════════════════════════════════

// Track state changes for alerts
var bool prev_valid_entry = false
var string prev_best_grade = ""

// Valid Entry Alert
new_valid_entry = not na(g_best_ifvg) and
                  g_best_ifvg.entry_valid and
                  grade_meets_minimum(g_best_ifvg.grade, i_min_alert_grade) and
                  (na(prev_best_grade) or prev_best_grade != g_best_ifvg.grade)

// Entry Invalidation Alert
entry_invalidated = prev_valid_entry and
                    not na(g_best_ifvg) and
                    not g_best_ifvg.entry_valid

// Update previous state
prev_valid_entry := not na(g_best_ifvg) and g_best_ifvg.entry_valid
prev_best_grade := not na(g_best_ifvg) ? g_best_ifvg.grade : na

// Define alert conditions
alertcondition(
    new_valid_entry and i_alert_valid_entry,
    title = "IFVG Valid Entry",
    message = "{{ticker}} {{interval}}: Valid Entry - Check chart for details"
)

alertcondition(
    entry_invalidated and i_alert_invalidation,
    title = "IFVG Entry Invalidated",
    message = "{{ticker}}: Entry Invalidated - BE point taken"
)
```

### 9.2 Alert Helper Functions

```pinescript
// ══════════════════════════════════════════════════════════════════
// FUNCTION: grade_meets_minimum()
// PURPOSE: Check if grade meets minimum threshold for alerts
// ══════════════════════════════════════════════════════════════════
grade_meets_minimum(string grade, string min_grade) =>
    int grade_value = grade_to_value(grade)
    int min_value = grade_to_value(min_grade)
    grade_value >= min_value

// ══════════════════════════════════════════════════════════════════
// FUNCTION: grade_to_value()
// PURPOSE: Convert grade string to numeric value for comparison
// ══════════════════════════════════════════════════════════════════
grade_to_value(string grade) =>
    int result = 0
    switch grade
        "A+" => result := 7
        "A"  => result := 6
        "A-" => result := 5
        "B+" => result := 4
        "B"  => result := 3
        "B-" => result := 2
        "C"  => result := 1
        => result := 0
    result
```

---

## 10. Configuration System

### 10.1 Input Grouping

```pinescript
// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: General
// ══════════════════════════════════════════════════════════════════
string GROUP_GENERAL = "═══ General Settings ═══"
i_show_indicator = input.bool(true, "Enable Indicator", group=GROUP_GENERAL)
i_max_fvgs = input.int(20, "Max FVGs to Display", minval=5, maxval=50, group=GROUP_GENERAL)
i_lookback = input.int(500, "Lookback Bars", minval=100, maxval=1000, group=GROUP_GENERAL)

// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: FVG Detection
// ══════════════════════════════════════════════════════════════════
string GROUP_FVG = "═══ FVG Detection ═══"
i_fvg_atr_period = input.int(14, "ATR Period", minval=5, maxval=50, group=GROUP_FVG)
i_fvg_min_size_mult = input.float(0.25, "Min Size (ATR Multiple)", minval=0.1, maxval=1.0, step=0.05, group=GROUP_FVG)
i_detect_htf = input.bool(true, "Detect HTF FVGs", group=GROUP_FVG)
i_htf_timeframe_1 = input.timeframe("60", "HTF 1", group=GROUP_FVG)
i_htf_timeframe_2 = input.timeframe("240", "HTF 2", group=GROUP_FVG)

// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: Liquidity
// ══════════════════════════════════════════════════════════════════
string GROUP_LIQ = "═══ Liquidity Detection ═══"
i_swing_lookback = input.int(5, "Swing Lookback", minval=3, maxval=10, group=GROUP_LIQ)
i_eqhl_tolerance = input.float(0.1, "EQH/EQL Tolerance (ATR)", minval=0.05, maxval=0.25, step=0.01, group=GROUP_LIQ)
i_show_eqh_eql = input.bool(true, "Show EQH/EQL", group=GROUP_LIQ)
i_show_ith_itl = input.bool(true, "Show ITH/ITL", group=GROUP_LIQ)
i_show_session_hl = input.bool(true, "Show Session H/L", group=GROUP_LIQ)
i_show_lrlr = input.bool(true, "Show LRLR", group=GROUP_LIQ)

// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: Sessions
// ══════════════════════════════════════════════════════════════════
string GROUP_SESSION = "═══ Session Settings ═══"
i_timezone_offset = input.int(0, "Timezone Offset (UTC)", minval=-12, maxval=12, group=GROUP_SESSION)
i_asian_start = input.session("0000-0800", "Asian Session", group=GROUP_SESSION)
i_london_start = input.session("0800-1600", "London Session", group=GROUP_SESSION)
i_ny_start = input.session("1300-2100", "New York Session", group=GROUP_SESSION)

// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: Visuals
// ══════════════════════════════════════════════════════════════════
string GROUP_VISUAL = "═══ Visual Settings ═══"
i_bullish_color = input.color(color.green, "Bullish Color", group=GROUP_VISUAL)
i_bearish_color = input.color(color.red, "Bearish Color", group=GROUP_VISUAL)
i_fvg_opacity = input.int(15, "FVG Opacity", minval=5, maxval=50, group=GROUP_VISUAL)
i_ifvg_opacity = input.int(30, "IFVG Opacity", minval=10, maxval=60, group=GROUP_VISUAL)
i_show_pd_zones = input.bool(true, "Show Premium/Discount", group=GROUP_VISUAL)
i_pd_opacity = input.int(25, "P/D Zone Opacity", minval=10, maxval=50, group=GROUP_VISUAL)
i_show_htf_overlay = input.bool(true, "Show HTF Overlay", group=GROUP_VISUAL)
i_show_dashboard = input.bool(true, "Show Dashboard", group=GROUP_VISUAL)
i_dashboard_position = input.string("top_right", "Dashboard Position", options=["top_left", "top_right", "bottom_left", "bottom_right"], group=GROUP_VISUAL)

// ══════════════════════════════════════════════════════════════════
// INPUT GROUP: Alerts
// ══════════════════════════════════════════════════════════════════
string GROUP_ALERT = "═══ Alert Settings ═══"
i_min_alert_grade = input.string("A-", "Minimum Grade for Alert", options=["A+", "A", "A-", "B+", "B", "All"], group=GROUP_ALERT)
i_alert_valid_entry = input.bool(true, "Alert on Valid Entry", group=GROUP_ALERT)
i_alert_invalidation = input.bool(true, "Alert on Invalidation", group=GROUP_ALERT)
i_alert_mitigation = input.bool(false, "Alert on Mitigation", group=GROUP_ALERT)
```

---

## 11. File Structure

### 11.1 Recommended File Organization

Since Pine Script doesn't support multiple files, we'll organize the code in a single file with clear sections. However, for development and documentation purposes:

```
IFVG/
├── 📄 strategy.md              # Trading strategy documentation
├── 📄 PRD.md                   # Product requirements document
├── 📄 ARCHITECTURE.md          # This technical architecture doc
│
├── 📁 src/
│   └── 📄 IFVG_Indicator.pine  # Main Pine Script file
│
├── 📁 tests/
│   ├── 📄 test_cases.md        # Manual test scenarios
│   └── 📄 edge_cases.md        # Edge case documentation
│
└── 📁 docs/
    ├── 📄 user_guide.md        # User documentation
    └── 📄 changelog.md         # Version history
```

### 11.2 Code Section Template

```pinescript
// ╔══════════════════════════════════════════════════════════════════╗
// ║                     IFVG INDICATOR v1.0                          ║
// ║                                                                  ║
// ║  Created: 2026-01-20                                             ║
// ║  Author: [Your Name]                                             ║
// ║  License: [License Type]                                         ║
// ║                                                                  ║
// ║  Based on DodgysDD IFVG Strategy                                 ║
// ╚══════════════════════════════════════════════════════════════════╝

//@version=6
indicator("IFVG Indicator", shorttitle="IFVG", overlay=true,
          max_bars_back=500,
          max_boxes_count=500,
          max_lines_count=500,
          max_labels_count=500)

// ══════════════════════════════════════════════════════════════════════
// SECTION 1: TYPE DEFINITIONS
// Description: Custom type definitions for FVG, IFVG, Liquidity, etc.
// ══════════════════════════════════════════════════════════════════════

[... type definitions ...]

// ══════════════════════════════════════════════════════════════════════
// SECTION 2: INPUT CONFIGURATION
// Description: User-configurable inputs organized by category
// ══════════════════════════════════════════════════════════════════════

[... inputs ...]

// [Continue with other sections...]
```

---

## Appendix A: Utility Functions Reference

```pinescript
// ══════════════════════════════════════════════════════════════════════
// UTILITY: grade_to_color()
// ══════════════════════════════════════════════════════════════════════
grade_to_color(string grade) =>
    color result = color.gray
    switch grade
        "A+" => result := color.new(#00FF00, 0)  // Bright green
        "A"  => result := color.new(#00CC00, 0)  // Green
        "A-" => result := color.new(#66CC00, 0)  // Yellow-green
        "B+" => result := color.new(#FFCC00, 0)  // Yellow
        "B"  => result := color.new(#FF9900, 0)  // Orange
        "B-" => result := color.new(#FF6600, 0)  // Dark orange
        "C"  => result := color.new(#FF0000, 0)  // Red
    result

// ══════════════════════════════════════════════════════════════════════
// UTILITY: position_from_string()
// ══════════════════════════════════════════════════════════════════════
position_from_string(string pos) =>
    position result = position.top_right
    switch pos
        "top_left"     => result := position.top_left
        "top_right"    => result := position.top_right
        "bottom_left"  => result := position.bottom_left
        "bottom_right" => result := position.bottom_right
    result

// ══════════════════════════════════════════════════════════════════════
// UTILITY: tf_to_minutes()
// ══════════════════════════════════════════════════════════════════════
tf_to_minutes(string tf) =>
    int result = 0
    switch tf
        "1"    => result := 1
        "5"    => result := 5
        "15"   => result := 15
        "30"   => result := 30
        "60"   => result := 60
        "240"  => result := 240
        "D"    => result := 1440
        "W"    => result := 10080
    result
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-01-20 | Initial architecture document |

---

*This document serves as the technical blueprint for the IFVG TradingView Indicator implementation.*
