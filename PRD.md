# IFVG Indicator - Product Requirements Document (PRD)

> **Version**: 1.0
> **Created**: 2026-01-20
> **Status**: Draft - Pending User Approval
> **Platform**: TradingView (Pine Script v5)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Product Overview](#2-product-overview)
3. [Feature Requirements](#3-feature-requirements)
4. [Technical Specifications](#4-technical-specifications)
5. [User Interface Design](#5-user-interface-design)
6. [Alert System](#6-alert-system)
7. [Configuration Options](#7-configuration-options)
8. [Edge Cases & Rules](#8-edge-cases--rules)
9. [Implementation Phases](#9-implementation-phases)
10. [Acceptance Criteria](#10-acceptance-criteria)

---

## 1. Executive Summary

### 1.1 Product Vision

Build a TradingView indicator that automates the detection, grading, and visualization of **Inversion Fair Value Gap (IFVG)** setups based on the DodgysDD methodology, enabling traders to identify high-probability trade entries with clear risk management levels.

### 1.2 Key Value Propositions

| Value | Description |
|-------|-------------|
| **Automated Detection** | Identify FVGs, inversions, and liquidity across multiple timeframes |
| **Setup Grading** | Automatically rate setups from A+ to C based on defined criteria |
| **Risk Management** | Display break-even points and stop loss levels |
| **Multi-TF Analysis** | HTF bias with LTF entry precision |
| **Entry Validation** | Track and alert on valid/invalid entry conditions |

### 1.3 Target Users

- ICT/SMC methodology traders
- Intraday and swing traders
- Traders seeking systematic setup identification
- Multi-market participants (indices, forex, crypto)

---

## 2. Product Overview

### 2.1 Core Functionality Matrix

| Feature | Priority | Description |
|---------|----------|-------------|
| FVG Detection | P0 | Identify Fair Value Gaps on current and HTF timeframes |
| IFVG Detection | P0 | Detect when FVGs get inverted (body close through) |
| Setup Grading | P0 | Auto-rate setups A+ through C based on criteria |
| Liquidity Detection | P0 | Identify EQH, EQL, ITH, ITL, Data H/L, LRLR |
| BE Point Tracking | P0 | Track internal highs/lows as break-even references |
| HTF Overlay | P1 | Project HTF FVGs/IFVGs onto LTF chart |
| Premium/Discount | P1 | Calculate and display daily range zones |
| Dashboard | P1 | Information panel with current state |
| Alert System | P1 | Entry-focused notifications |
| Session Tracking | P2 | Asian, London, NY session highs/lows |

### 2.2 Supported Markets

- **Indices**: NQ, ES, YM, RTY, DAX, FTSE
- **Forex**: All major and minor pairs
- **Crypto**: BTC, ETH, and liquid alts
- **Commodities**: Gold, Oil, etc.

*Design Principle*: Market-agnostic logic with ATR-based dynamic sizing.

### 2.3 Supported Timeframes

| Type | Timeframes | Purpose |
|------|------------|---------|
| **LTF (Entry)** | User configurable (30s - 15m typical) | Precise entry execution |
| **HTF (Bias)** | 15m, 30m, 1H, 2H, 4H, Daily | Directional bias and DOL |

---

## 3. Feature Requirements

### 3.1 FVG Detection Engine

#### 3.1.1 FVG Identification

**Definition**: A 3-candle pattern where middle candle creates a gap.

```
Bullish FVG:
  Candle 1 High < Candle 3 Low = Gap exists

Bearish FVG:
  Candle 1 Low > Candle 3 High = Gap exists
```

**Requirements**:
- [ ] Detect bullish and bearish FVGs on current timeframe
- [ ] Detect FVGs on user-selected HTF timeframes
- [ ] Filter FVGs by minimum size (ATR-based)
- [ ] Store FVG data: high, low, midpoint, timeframe, bar index

#### 3.1.2 ATR-Based Minimum Size

```
Minimum FVG Size = ATR(14) * Multiplier

Default Multiplier: 0.25 (25% of ATR)
User Configurable: 0.1 - 1.0
```

**Rationale**: Filters out insignificant micro-gaps while adapting to volatility.

### 3.2 IFVG Detection Engine

#### 3.2.1 Inversion Logic

**Definition**: FVG is inverted when candle BODY closes through the zone.

```
Bullish FVG Inversion:
  candle.close < FVG.low  →  FVG becomes resistance-turned-support

Bearish FVG Inversion:
  candle.close > FVG.high  →  FVG becomes support-turned-resistance
```

**Requirements**:
- [ ] Detect inversion on candle close (not intrabar)
- [ ] Track inversion candle properties (momentum, size)
- [ ] Mark FVG status change: FVG → IFVG
- [ ] Calculate stop loss levels based on inversion candle

#### 3.2.2 Inversion Validation

An inversion triggers entry consideration. Validity depends on:

| Check | Condition | Result if Failed |
|-------|-----------|------------------|
| BE Point Intact | Internal H/L not taken at inversion time | Entry Invalid |
| Model Present | Reversal or Continuation model active | No Setup |
| DOL Exists | Clear liquidity target identified | No Setup |

### 3.3 Liquidity Detection (Swing Structure Based)

#### 3.3.1 Structure Detection Algorithm

```
Swing High Detection:
  - Bar makes higher high than N bars left AND N bars right
  - Confirmed by structure break (lower low after)

Swing Low Detection:
  - Bar makes lower low than N bars left AND N bars right
  - Confirmed by structure break (higher high after)

Default N = 5 bars (configurable 3-10)
```

#### 3.3.2 Liquidity Types

| Type | Detection Rule | Visual |
|------|---------------|--------|
| **EQH** | 2+ swing highs within tolerance (ATR * 0.1) | Horizontal line with "EQH" label |
| **EQL** | 2+ swing lows within tolerance | Horizontal line with "EQL" label |
| **ITH** | Internal swing high (within larger structure) | Dashed line with "ITH" label |
| **ITL** | Internal swing low (within larger structure) | Dashed line with "ITL" label |
| **Data High** | Session high (Asian/London/NY) | Dotted line with session label |
| **Data Low** | Session low (Asian/London/NY) | Dotted line with session label |
| **LRLR** | Trendline with 3+ touches | Diagonal line |

#### 3.3.3 Liquidity Sweep Detection

```
BSL Sweep: price.high > liquidity.level AND price.close < liquidity.level
SSL Sweep: price.low < liquidity.level AND price.close > liquidity.level
```

**Requirements**:
- [ ] Detect sweep (wick through, body respects)
- [ ] Mark swept liquidity as "taken"
- [ ] Trigger reversal model consideration on sweep

### 3.4 Setup Grading System

#### 3.4.1 Grading Criteria Matrix

| Criterion | A+ | A | A-/B+ | B | B- | C |
|-----------|----|----|-------|---|----|---|
| **Liquidity** | Sweep AND FVG delivery | Sweep OR delivery | Sweep OR delivery | Neither | No major | None |
| **Momentum** | Strong, no chop | Good, no chop | Some chop | Lot of chop | Low | Unpredictable |
| **Target** | Clear (7 types) | Clear | Clear | Exists, weak | No real target | None |
| **FVG Singular** | Yes | Yes | Yes | May not be | Not obvious | Forced |
| **Premium/Discount** | Optimal zone | Obvious in zone | May be reversed | Reversed | Wrong zone | Way off |

#### 3.4.2 Grading Algorithm (Hybrid Approach)

The grading uses a **two-step hybrid approach**:
1. **Mandatory Criteria** → Determines the tier (A, B, or C)
2. **Quality Criteria** → Determines the modifier (+, -, or none)

```python
def calculate_grade(setup):
    """
    Hybrid Grading Algorithm
    Step 1: Mandatory criteria determine tier
    Step 2: Quality criteria determine modifier
    """

    # ============================================
    # STEP 1: MANDATORY CRITERIA → DETERMINE TIER
    # ============================================

    # MANDATORY: Must have clear Draw on Liquidity (target)
    if not setup.has_clear_dol:
        return "C"  # No target = automatic C grade

    # MANDATORY: Must have identifiable FVG
    if not setup.fvg_exists:
        return "C"  # No FVG = automatic C grade

    # TIER DETERMINATION based on liquidity context
    if setup.has_sweep AND setup.has_fvg_delivery:
        tier = "A"  # Both sweep AND delivery = A-tier
    elif setup.has_sweep OR setup.has_fvg_delivery:
        tier = "A"  # Either sweep OR delivery = A-tier (modifier will adjust)
    else:
        tier = "B"  # Neither sweep nor delivery = B-tier maximum

    # ============================================
    # STEP 2: QUALITY CRITERIA → DETERMINE MODIFIER
    # ============================================

    quality_score = 0  # Range: -3 to +3

    # Momentum Quality (-1 to +1)
    if setup.momentum == "strong_no_chop":
        quality_score += 1
    elif setup.momentum == "weak_or_choppy":
        quality_score -= 1
    # else: neutral, no change

    # Premium/Discount Positioning (-1 to +1)
    if setup.in_optimal_zone:  # Long in discount, short in premium
        quality_score += 1
    elif setup.in_wrong_zone:  # Long in premium, short in discount
        quality_score -= 1
    # else: neutral zone, no change

    # FVG Clarity (-1 to +1)
    if setup.fvg_is_singular AND setup.fvg_is_obvious:
        quality_score += 1
    elif not setup.fvg_is_singular OR not setup.fvg_is_obvious:
        quality_score -= 1
    # else: average clarity, no change

    # BONUS: Additional confluences (can push to A+ or prevent drop)
    if setup.has_sweep AND setup.has_fvg_delivery:
        quality_score += 1  # Having BOTH is exceptional
    if setup.has_smt_divergence:
        quality_score += 1  # SMT is bonus confluence

    # ============================================
    # STEP 3: COMBINE TIER + MODIFIER
    # ============================================

    if tier == "A":
        if quality_score >= 3:
            return "A+"
        elif quality_score >= 1:
            return "A"
        elif quality_score >= -1:
            return "A-"
        else:
            return "B+"  # Poor quality demotes to B+

    elif tier == "B":
        if quality_score >= 2:
            return "B+"  # Exceptional quality can promote to B+
        elif quality_score >= 0:
            return "B"
        else:
            return "B-"

    else:  # tier == "C"
        return "C"  # C stays C regardless of quality


def assess_momentum(inversion_candle, atr):
    """
    Assess momentum quality of the inversion candle
    Returns: "strong_no_chop", "neutral", or "weak_or_choppy"
    """
    candle_body = abs(inversion_candle.close - inversion_candle.open)
    candle_range = inversion_candle.high - inversion_candle.low

    # Strong momentum: body is >70% of range and range > ATR
    if candle_body / candle_range > 0.7 and candle_range > atr:
        return "strong_no_chop"

    # Weak/choppy: small body relative to wicks or small overall
    elif candle_body / candle_range < 0.3 or candle_range < atr * 0.5:
        return "weak_or_choppy"

    else:
        return "neutral"
```

**Grading Logic Summary**:

| Mandatory Check | Result if Failed |
|-----------------|------------------|
| Clear DOL exists | → C grade |
| FVG identifiable | → C grade |
| Sweep AND/OR delivery | → A-tier (both) or B-tier (neither) |

| Quality Factor | Effect |
|----------------|--------|
| Strong momentum, no chop | +1 |
| Optimal PD zone | +1 |
| Singular & obvious FVG | +1 |
| Sweep + Delivery (both) | +1 bonus |
| SMT divergence | +1 bonus |
| Weak momentum / chop | -1 |
| Wrong PD zone | -1 |
| Non-singular / unclear FVG | -1 |

| Tier + Quality Score | Final Grade |
|---------------------|-------------|
| A-tier, score ≥ 3 | A+ |
| A-tier, score 1-2 | A |
| A-tier, score -1 to 0 | A- |
| A-tier, score ≤ -2 | B+ (demoted) |
| B-tier, score ≥ 2 | B+ (promoted) |
| B-tier, score 0-1 | B |
| B-tier, score < 0 | B- |
| C-tier | C |

### 3.5 Break-Even (BE) Point System

#### 3.5.1 BE Point Identification

```
For Bullish IFVG:
  BE Point = Next Internal High after FVG formation

For Bearish IFVG:
  BE Point = Next Internal Low after FVG formation

If no internal H/L exists:
  BE Point = FVG zone itself (alternate BE)
```

#### 3.5.2 Entry Validation Logic

```
Entry is VALID if:
  - IFVG occurs (body close through FVG)
  - BE point has NOT been taken at time of inversion

Entry is INVALID if:
  - Inversion and BE point breach happen simultaneously
  - Price already passed through BE before inversion
```

**Requirements**:
- [ ] Track internal highs/lows relative to each FVG
- [ ] Validate entry at moment of inversion
- [ ] Update entry status if BE taken post-entry
- [ ] Display BE level on chart with label

### 3.6 Premium/Discount Zone System

#### 3.6.1 Daily Range Calculation

```
Daily High = Highest high of current day (or previous if pre-market)
Daily Low = Lowest low of current day
Daily Range = Daily High - Daily Low

Equilibrium (50%) = Daily Low + (Daily Range * 0.5)
Premium Zone = Above Equilibrium
Discount Zone = Below Equilibrium
```

#### 3.6.2 Visualization

- **Premium Zone**: Light red background shading (25% opacity)
- **Discount Zone**: Light green background shading (25% opacity)
- **Equilibrium Line**: Dashed white/gray line at 50%

### 3.7 Multi-Timeframe Analysis

#### 3.7.1 HTF Data Retrieval

```pinescript
// Request HTF data
htf_high = request.security(syminfo.tickerid, htf_timeframe, high)
htf_low = request.security(syminfo.tickerid, htf_timeframe, low)
htf_close = request.security(syminfo.tickerid, htf_timeframe, close)
```

#### 3.7.2 HTF Overlay Display

HTF FVGs/IFVGs projected onto LTF chart:
- Larger box outline (thicker border)
- Label indicates source timeframe: "[1H] IFVG A"
- Semi-transparent fill to not obscure LTF action

### 3.8 Session Tracking

#### 3.8.1 Session Definitions (UTC)

| Session | Start | End |
|---------|-------|-----|
| **Asian** | 00:00 | 08:00 |
| **London** | 08:00 | 16:00 |
| **New York** | 13:00 | 21:00 |

*Note: User can configure for their timezone offset*

#### 3.8.2 Session High/Low Tracking

- Track and display previous session highs/lows
- Mark as potential liquidity (Data Highs/Lows)
- Clear/reset at session boundaries

---

## 4. Technical Specifications

### 4.1 Pine Script Requirements

| Requirement | Specification |
|-------------|---------------|
| **Version** | Pine Script v6 |
| **Type** | Overlay indicator |
| **Max Bars Back** | 500 (configurable) |
| **Security Calls** | Max 3 HTF timeframes (dynamic requests by default in v6) |
| **Arrays** | For storing FVG/IFVG/Liquidity data (v6 supports negative indexing) |
| **Labels/Lines/Boxes** | Dynamic creation with cleanup |

### 4.1.1 Pine Script v6 Advantages for This Indicator

| v6 Feature | Benefit for IFVG Indicator |
|------------|---------------------------|
| **Dynamic Requests** | HTF can be changed via input without recompilation; `request.security()` accepts series string for timeframe |
| **Lazy Evaluation** | Safer array bounds checking with `and`/`or` operators; e.g., `array.size(arr) > 0 and array.get(arr, 0) > x` |
| **No Scope Limit** | Complex nested logic for grading algorithm won't hit 550 scope limit |
| **Negative Array Indexing** | `array.get(fvg_array, -1)` to get most recent FVG easily |
| **Point-based Text Size** | Precise dashboard text sizing (e.g., 12pt, 14pt) instead of size.normal/large |
| **No Implicit Bool Cast** | Cleaner conditional logic, explicit comparisons required |

### 4.1.2 v6 Migration Considerations

```pinescript
// v5 → v6 Changes to be aware of:

// 1. Boolean handling - explicit comparisons required
// v5: if myValue    // worked if myValue was int/float
// v6: if myValue != 0  // explicit comparison needed

// 2. Division returns float
// v5: 5 / 2 = 2 (int)
// v6: 5 / 2 = 2.5 (float)

// 3. Dynamic requests enabled by default
// v6: request.security(syminfo.tickerid, htf_input, close)
//     htf_input can be series string, changes dynamically

// 4. Negative array indexing
// v6: array.get(myArray, -1)  // last element
//     array.get(myArray, -2)  // second to last
```

### 4.2 Data Structures

```pinescript
// FVG Storage
type FVG
    float top
    float bottom
    float mid
    int start_bar
    int end_bar
    bool is_bullish
    bool is_inverted
    string grade
    string status  // "active", "inverted", "mitigated"
    int tf_minutes

// Liquidity Storage
type Liquidity
    float level
    string type  // "EQH", "EQL", "ITH", "ITL", etc.
    int bar_index
    bool is_swept

// Setup Storage
type Setup
    FVG fvg
    Liquidity dol
    float be_level
    bool entry_valid
    string grade
    float stop_loss
```

### 4.3 Performance Considerations

| Concern | Mitigation |
|---------|------------|
| **Too many objects** | Limit to 50 active FVGs, auto-cleanup old |
| **Repainting** | Use confirmed bars only (`barstate.isconfirmed`) |
| **HTF calls** | Cache HTF data, minimize `request.security` calls |
| **Array growth** | Implement circular buffer or FIFO cleanup |

### 4.4 IFVG Lifecycle State Machine

```
[NEW FVG]
    ↓ (detected on current TF or HTF)
[ACTIVE FVG]
    ↓ (candle body closes through)
[INVERTED → IFVG]
    ↓ (price returns and closes through zone)
[MITIGATED] → Remove from chart
```

---

## 5. User Interface Design

### 5.1 Visual Elements

#### 5.1.1 FVG Boxes

| State | Fill Color | Border | Label |
|-------|------------|--------|-------|
| **Bullish FVG** | Green (15% opacity) | Green solid | "FVG" |
| **Bearish FVG** | Red (15% opacity) | Red solid | "FVG" |
| **Bullish IFVG** | Green (30% opacity) | Green dashed | "IFVG [Grade]" |
| **Bearish IFVG** | Red (30% opacity) | Red dashed | "IFVG [Grade]" |
| **HTF Overlay** | Same + thicker border | "[TF] IFVG [Grade]" |

#### 5.1.2 Liquidity Lines

| Type | Line Style | Color | Label |
|------|------------|-------|-------|
| **EQH/EQL** | Solid | Orange | "EQH" / "EQL" |
| **ITH/ITL** | Dashed | Yellow | "ITH" / "ITL" |
| **Data H/L** | Dotted | Cyan | "Asia H" / "LDN L" etc. |
| **LRLR** | Solid diagonal | Purple | "LRLR" |
| **Swept** | Same + strikethrough effect | Grayed out |

#### 5.1.3 BE Point Display

- Horizontal line at BE level
- Label: "BE" with price
- Color: White/neutral
- Updates to "BE HIT" if invalidated (color change to gray)

### 5.2 Dashboard Panel

**Location**: Top-right corner of chart (configurable)

```
┌─────────────────────────────────┐
│  IFVG INDICATOR v1.0            │
├─────────────────────────────────┤
│  HTF Bias: BULLISH (1H)         │
│  DOL: EQH @ 18,450              │
│  ───────────────────────        │
│  Active Setup: A IFVG           │
│  Entry: VALID                   │
│  BE Level: 18,320               │
│  ───────────────────────        │
│  Zone: DISCOUNT (42%)           │
│  Session: NY                    │
└─────────────────────────────────┘
```

### 5.3 Visual Density Rules (Balanced Mode)

| Element | Always Visible | On Hover/Select |
|---------|----------------|-----------------|
| Active IFVG boxes | Yes | Full details |
| Best grade IFVG | Yes (highlighted) | - |
| Liquidity levels (untouched) | Yes | Type + price |
| Liquidity levels (swept) | No (faded) | Sweep time |
| BE point | Yes | - |
| HTF overlays | Yes (subtle) | TF + grade |
| PD zones | Yes (shading) | % level |

---

## 6. Alert System

### 6.1 Entry-Focused Alerts

| Alert | Trigger | Message Template |
|-------|---------|------------------|
| **Valid Entry** | IFVG forms with grade A- or better, entry valid | "[Symbol] [TF]: [Grade] IFVG - Valid [Long/Short] Entry @ [Price]. BE: [Level], DOL: [Target]" |
| **Entry Invalidated** | BE point taken after valid entry formed | "[Symbol]: Entry invalidated - BE taken @ [Price]" |
| **Setup Mitigated** | Price fully mitigates the IFVG zone | "[Symbol]: IFVG mitigated @ [Price]" |

### 6.2 Alert Configuration

```pinescript
// User inputs for alert filtering
input.string min_alert_grade = "A-"  // Options: "A+", "A", "A-", "B+", "B", "All"
input.bool alert_on_invalidation = true
input.bool alert_on_mitigation = false
```

### 6.3 Alert Conditions (Pine Script)

```pinescript
// Valid entry alert
alertcondition(
    valid_entry AND grade_meets_threshold,
    title="IFVG Valid Entry",
    message="{{ticker}} {{interval}}: {{plot_0}} IFVG - Valid Entry"
)

// Invalidation alert
alertcondition(
    be_point_taken AND had_valid_entry,
    title="IFVG Entry Invalidated",
    message="{{ticker}}: Entry invalidated - BE taken"
)
```

---

## 7. Configuration Options

### 7.1 Input Groups

#### Group 1: General Settings

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `show_indicator` | bool | true | - | Master on/off |
| `max_fvgs_display` | int | 20 | 5-50 | Max FVGs to show |
| `lookback_bars` | int | 500 | 100-1000 | Historical analysis depth |

#### Group 2: FVG Detection

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `fvg_atr_period` | int | 14 | 5-50 | ATR period for sizing |
| `fvg_min_size_mult` | float | 0.25 | 0.1-1.0 | Min FVG size as ATR multiple |
| `detect_htf_fvgs` | bool | true | - | Enable HTF FVG detection |
| `htf_timeframe_1` | string | "60" | TF list | First HTF for analysis |
| `htf_timeframe_2` | string | "240" | TF list | Second HTF for analysis |

#### Group 3: Liquidity Detection

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `swing_lookback` | int | 5 | 3-10 | Bars for swing detection |
| `eqhl_tolerance` | float | 0.1 | 0.05-0.25 | ATR multiple for equal H/L detection |
| `show_eqh_eql` | bool | true | - | Show equal highs/lows |
| `show_ith_itl` | bool | true | - | Show internal highs/lows |
| `show_session_hl` | bool | true | - | Show session highs/lows |
| `show_lrlr` | bool | true | - | Show trendline liquidity |

#### Group 4: Sessions

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `timezone_offset` | int | 0 | -12 to +12 | UTC offset |
| `asian_start` | string | "00:00" | Time | Asian session start |
| `asian_end` | string | "08:00" | Time | Asian session end |
| `london_start` | string | "08:00" | Time | London session start |
| `london_end` | string | "16:00" | Time | London session end |
| `ny_start` | string | "13:00" | Time | NY session start |
| `ny_end` | string | "21:00" | Time | NY session end |

#### Group 5: Visuals

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `bullish_color` | color | green | - | Bullish FVG/IFVG color |
| `bearish_color` | color | red | - | Bearish FVG/IFVG color |
| `fvg_opacity` | int | 15 | 5-50 | FVG box fill opacity |
| `ifvg_opacity` | int | 30 | 10-60 | IFVG box fill opacity |
| `show_pd_zones` | bool | true | - | Show premium/discount shading |
| `pd_opacity` | int | 25 | 10-50 | PD zone opacity |
| `show_dashboard` | bool | true | - | Show info dashboard |
| `dashboard_position` | string | "top_right" | Position list | Dashboard location |

#### Group 6: Alerts

| Input | Type | Default | Range | Description |
|-------|------|---------|-------|-------------|
| `min_alert_grade` | string | "A-" | Grade list | Minimum grade to trigger alert |
| `alert_valid_entry` | bool | true | - | Alert on valid entries |
| `alert_invalidation` | bool | true | - | Alert on entry invalidation |
| `alert_mitigation` | bool | false | - | Alert on IFVG mitigation |

---

## 8. Edge Cases & Rules

### 8.1 Multiple IFVGs Handling

**Rule**: Display only the **best grade** IFVG when multiple are active.

```
Selection Priority:
1. Highest grade (A+ > A > A- > B+ > B > B- > C)
2. If same grade: Most recent inversion
3. If same time: Nearest to current price
```

### 8.2 IFVG Mitigation Rules

**Rule**: Remove IFVG after **full mitigation** (candle body closes through the zone).

```
Bullish IFVG Mitigation:
  candle.close < IFVG.bottom  →  IFVG removed

Bearish IFVG Mitigation:
  candle.close > IFVG.top  →  IFVG removed
```

### 8.3 Series of Gaps Handling

When multiple consecutive FVGs exist:
1. Combine into single zone (top of highest, bottom of lowest)
2. Treat as one FVG for inversion detection
3. Require all to be inverted before marking as IFVG

### 8.4 HTF/LTF Alignment

HTF IFVG creates bias; LTF setup must align:
- If HTF bias = Bullish → Only show bullish LTF setups
- If HTF bias = Bearish → Only show bearish LTF setups
- If no HTF IFVG → Show both directions on LTF

### 8.5 Market Hours Consideration

- Pre-market/after-hours gaps may behave differently
- Consider adding option to filter/flag extended hours FVGs
- Session-based liquidity only tracked during defined session times

---

## 9. Implementation Phases

### Phase 1: Core Engine (MVP)

**Deliverables**:
- [ ] FVG detection (current timeframe)
- [ ] IFVG detection with basic validation
- [ ] Visual boxes with bullish/bearish colors
- [ ] Basic grade calculation (simplified)
- [ ] Single timeframe operation

**Acceptance**: Can identify and display FVGs that become inverted.

### Phase 2: Liquidity & Grading

**Deliverables**:
- [ ] Swing structure liquidity detection (EQH, EQL, ITH, ITL)
- [ ] Full grading algorithm implementation
- [ ] BE point tracking and validation
- [ ] Entry valid/invalid status
- [ ] Stop loss level calculation

**Acceptance**: Setups are graded and validated correctly per strategy rules.

### Phase 3: Multi-Timeframe

**Deliverables**:
- [ ] HTF FVG/IFVG detection via `request.security`
- [ ] HTF overlay projection on LTF chart
- [ ] HTF bias determination
- [ ] LTF setup filtering based on HTF bias

**Acceptance**: HTF zones visible on LTF, bias correctly identified.

### Phase 4: Sessions & Zones

**Deliverables**:
- [ ] Session tracking (Asian, London, NY)
- [ ] Data Highs/Lows detection
- [ ] Premium/Discount zone calculation
- [ ] Zone visualization (background shading)

**Acceptance**: Sessions tracked, PD zones displayed correctly.

### Phase 5: Dashboard & Alerts

**Deliverables**:
- [ ] Dashboard panel implementation
- [ ] Alert conditions for valid entries
- [ ] Alert conditions for invalidations
- [ ] All user configuration options

**Acceptance**: Dashboard shows correct state, alerts fire appropriately.

### Phase 6: Polish & Optimization

**Deliverables**:
- [ ] Performance optimization
- [ ] Edge case handling
- [ ] Visual refinements
- [ ] Documentation/tooltips

**Acceptance**: Smooth operation, no visual glitches, handles all edge cases.

---

## 10. Acceptance Criteria

### 10.1 Functional Requirements

| ID | Requirement | Test Method |
|----|-------------|-------------|
| FR-01 | Indicator detects all valid FVGs based on ATR threshold | Visual inspection + manual count |
| FR-02 | Inversions detected only on candle body close | Step through bars, verify timing |
| FR-03 | Grades match expected values for known setups | Compare against strategy examples |
| FR-04 | BE points correctly identified and tracked | Verify against internal H/L |
| FR-05 | Entry validity correctly determined | Test with various scenarios |
| FR-06 | HTF zones project correctly onto LTF | Multi-TF chart comparison |
| FR-07 | Liquidity levels detected per swing rules | Compare with manual identification |
| FR-08 | Alerts fire for configured conditions | Set alerts, verify triggers |
| FR-09 | Dashboard displays accurate real-time state | Cross-reference with chart |
| FR-10 | Mitigation removes IFVG correctly | Verify removal on body close through |

### 10.2 Non-Functional Requirements

| ID | Requirement | Acceptance Threshold |
|----|-------------|---------------------|
| NFR-01 | No repainting on confirmed bars | 0 repaint instances |
| NFR-02 | Responsive performance | < 1 second load time |
| NFR-03 | Memory efficient | < 50 objects at any time |
| NFR-04 | Clean visual hierarchy | User survey approval |
| NFR-05 | Cross-market compatibility | Works on 5+ different instruments |

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **FVG** | Fair Value Gap - 3-candle imbalance pattern |
| **IFVG** | Inversion FVG - FVG that has been inverted |
| **BE** | Break-Even point - Internal H/L used for trade management |
| **DOL** | Draw on Liquidity - Target liquidity pool |
| **BSL** | Buy Side Liquidity - Liquidity above price (highs) |
| **SSL** | Sell Side Liquidity - Liquidity below price (lows) |
| **EQH/EQL** | Equal Highs/Lows - Multiple swings at same level |
| **ITH/ITL** | Internal High/Low - Swing within larger structure |
| **LRLR** | Trendline liquidity |
| **HTF** | Higher Timeframe |
| **LTF** | Lower Timeframe |
| **PD** | Premium/Discount zones |

---

## Appendix B: Reference Chart Examples

*See `briefing/strategy/` folder for visual examples of:*
- A+ setups (page 2 of rating PDF)
- A setups (page 4)
- A-/B+ setups (page 6)
- B setups (page 8)
- B- setups (page 10)
- C setups (page 12)

---

## Document Approval

### Stakeholder Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Product Owner | | | [ ] Approved |
| Developer | | | [ ] Reviewed |

### Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-20 | Claude | Initial PRD creation |
| 1.1 | 2026-01-20 | Claude | Updated to Pine Script v6, added v6-specific features and migration notes |

---

*This PRD is a living document and will be updated as requirements evolve during development.*
