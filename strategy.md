# IFVG (Inversion Fair Value Gap) Trading Strategy

> **Document Purpose**: Capture and validate understanding of the IFVG trading strategy before indicator development.
> **Source**: DodgysDD Strategy Documentation + IFVG Rating System PDF

---

## Table of Contents

1. [Core Concept](#1-core-concept)
2. [Primary Trade Models](#2-primary-trade-models)
3. [Entry Rules](#3-entry-rules)
4. [Stop Loss Placement](#4-stop-loss-placement)
5. [Liquidity & Targets](#5-liquidity--targets)
6. [Setup Rating System](#6-setup-rating-system)
7. [Advanced Discretion](#7-advanced-discretion)
8. [Multi-Timeframe Analysis](#8-multi-timeframe-analysis)
9. [Key Takeaways](#9-key-takeaways)

---

## 1. Core Concept

### What is a Fair Value Gap (FVG)?

A **Fair Value Gap** is a three-candle pattern where:
- The middle candle creates a gap between the high of candle 1 and the low of candle 3 (bullish FVG)
- OR a gap between the low of candle 1 and the high of candle 3 (bearish FVG)

This gap represents an "imbalance" in price where orders were not fully filled.

### What is an Inversion Fair Value Gap (IFVG)?

An **IFVG** occurs when:
1. Price returns to a Fair Value Gap
2. A candle **body closes** above (for bearish FVG) or below (for bullish FVG) the gap
3. This "inverts" the FVG - turning resistance into support (or vice versa)

**Key Point**: The inversion is confirmed by **candle body closure**, not just a wick through the zone.

---

## 2. Primary Trade Models

### 2.1 Reversal Model

**Trigger**: Clear sweep of obvious liquidity pool

**Sequence**:
1. **Step 1**: Identify a clear sweep of Buy Side Liquidity (BSL) or Sell Side Liquidity (SSL)
   - Must be obvious: EQH, EQL, LRLR, etc.
2. **Step 2**: After the sweep, look for a Fair Value Gap
   - Bearish FVG if BSL was swept (expecting reversal down)
   - Bullish FVG if SSL was swept (expecting reversal up)
3. **Step 3**: Wait for the FVG to get **inversed**
   - Candle body must close above/below the FVG
4. **Step 4**: Enter on the inversion, target the opposite liquidity pool

```
Bullish Reversal Example:

  Sell Side ----X---- (Swept)
       |
       v
    [Bullish FVG Forms]
       |
       v
    [Price returns, body closes ABOVE FVG = INVERSION]
       |
       v
    LONG ENTRY → Target Buy Side
```

### 2.2 Continuation Model

**Trigger**: After a reversal completes, price retraces to equilibrium

**Sequence**:
1. **Step 1**: A reversal model has already played out
2. **Step 2**: Price continues to displace in the new direction
3. **Step 3**: Price retraces to **50% equilibrium** of the initial move and/or into an FVG
4. **Step 4**: Look for an FVG on the retracement leg to get inversed
5. **Step 5**: Enter on inversion, target the next liquidity pool

**Key Requirement**: For a continuation entry to be valid, price must retrace to:
- 50% (equilibrium) of the initial price leg, AND/OR
- Into an FVG from the retracement

---

## 3. Entry Rules

### 3.1 Valid Entry Criteria

An entry is **VALID** only if:
- The **next internal high/low has NOT been taken** at the time of inversion
- The internal high/low serves as the **Break-Even (BE) point**
- If inversion happens simultaneously with taking the internal high/low → **INVALID**

```
VALID ENTRY:
                    BE (internal high)
                    ----------------
                         |
    [IFVG Zone] -------- | ←-- Entry here, BE still intact
                         |

INVALID ENTRY:
                    BE (internal high)
    [IFVG Zone] ----X--- ←-- Inversion happens AT the same time BE is taken
```

### 3.2 Entry Does Not Change Bias

**Important**: Even if an entry becomes invalid, **the bias does not change**.
- An entry remains possible if:
  - The model (reversal/continuation) is still present
  - The Draw on Liquidity (DOL) is still valid

### 3.3 Advanced Entry Exception

Sometimes a "mechanically invalid" entry can still be a quality setup if:
- The candle has **high momentum**
- We are in a **clear reversal model**
- Conviction and context support the trade

---

## 4. Stop Loss Placement

### 4.1 Three Stop Loss Options

| Type | Placement | When to Use |
|------|-----------|-------------|
| **Fail Stop** (Recommended) | Below/above the candle body close of the inversion | Default choice - if inversion fails, trade closes |
| **Swing Stop** | At the swing low/high | High RR setups where small retracement could stop out fail stop |
| **Narrow Stop** | Tight at the IFVG zone edge | High momentum close scenarios where price shouldn't return |

### 4.2 Stop Loss Decision Factors

Consider these when choosing stop type:
- **Trade quality** (A+ setup = can use tighter stop)
- **Conviction level**
- **Market conditions** (volatile = wider stop)
- **Risk-Reward ratio** (higher RR may justify wider stop)
- **Momentum** of the inversion candle

---

## 5. Liquidity & Targets

### 5.1 Seven Liquidity Types

| # | Type | Description |
|---|------|-------------|
| 1 | **EQH** | Equal Highs - multiple highs at same level |
| 2 | **EQL** | Equal Lows - multiple lows at same level |
| 3 | **ITH** | Internal High - swing high within a move |
| 4 | **ITL** | Internal Low - swing low within a move |
| 5 | **Data Highs** | Significant highs from economic data releases |
| 6 | **Data Lows** | Significant lows from economic data releases |
| 7 | **LRLR** | Trendline Liquidity - liquidity resting along trendlines |

### 5.2 Draw on Liquidity (DOL)

The **DOL** is the target - the liquidity pool price is expected to reach.

**Rule**: Every valid trade must have a clear DOL that is one of the 7 liquidity types.

### 5.3 Premium & Discount Zones

**Based on Daily Range**:
- **Premium Zone**: Upper 50% of the daily range (sell zone for shorts)
- **Discount Zone**: Lower 50% of the daily range (buy zone for longs)

**Optimal Setup Positioning**:
- **Longs**: Should be in **discount** (below 50% of daily range)
- **Shorts**: Should be in **premium** (above 50% of daily range)

---

## 6. Setup Rating System

### 6.1 A+ Setup (Highest Quality)

**Criteria**:
- [x] Liquidity sweep **AND** delivery from another FVG (bodies respect it perfectly)
- [x] Strong momentum with **no chop** through the IFVG
- [x] Quick reaction to the high/low after sweep
- [x] Clear target (one of the 7 liquidity types)
- [x] FVG is **singular** (not multiple gaps)
- [x] Longs in **discount**, Shorts in **premium**
- [x] SMT divergence is a bonus

### 6.2 A Setup

**Criteria**:
- [x] Liquidity sweep **OR** delivery from FVG (not both)
- [x] Good momentum on the break (no chop)
- [x] Clear target
- [x] Singular FVG
- [x] Delivery from FVG must be **obvious** and in correct zone

*Note: A setups on choppy/bad days are rated A-*

### 6.3 A- / B+ Setup

**Criteria**:
- [x] Liquidity sweep **OR** delivery from FVG
- [x] Momentum with **some chop** through the IFVG
- [x] Trade entry only after body fully closes over/under FVG
- [x] Clear target
- [x] Singular FVG
- [x] May have longs in premium / shorts in discount

*B+ = A- setup on very choppy days where gap and target are super obvious*

### 6.4 B Setup

**Criteria**:
- [ ] Usually **no** liquidity sweep and **no** delivery from FVG
- [x] May still align with bias
- [x] Likely momentum with **a lot of chop**
- [x] Target exists but unlikely to have multiple confluences
- [x] FVG may **not be obvious**
- [x] Longs in premium / shorts in discount (reversed)

### 6.5 B- Setup

**Criteria**:
- [ ] No major sweep or delivery
- [x] May work sometimes if bias is correct
- [x] **Low momentum** with chop or bad market conditions
- [x] **No real targets** - poor risk/reward
- [x] FVG **won't be obvious**, messy price action
- [x] Longs in premium / shorts in discount

### 6.6 C Setup (Avoid)

**Criteria**:
- [ ] No liquidity sweep
- [ ] No delivery from FVG
- [x] Trading in the middle of nowhere
- [x] Momentum unpredictable
- [x] **No clue what bias is**
- [x] No real targets
- [x] FVG not obvious, forcing a trade
- [x] Way too far in wrong premium/discount zone

---

## 7. Advanced Discretion

### 7.1 Series of Gaps

**Rule Exception**: Usually only trade singular FVGs, but...

When there are **multiple consecutive gaps**:
- Combine them into one zone
- Wait for **all** of them to get inverted before entering
- Treat as a single inversion

### 7.2 Inconspicuous Gaps

Small or hard-to-see FVGs can still be valid if:
- Everything else aligns perfectly (A+ liquidity draw)
- Clear continuation model present
- Strong bias and context

### 7.3 Taking Invalid Entries

Trades that hit the internal high/low (making entry "invalid") can still be taken if:
- Liquidity is **obvious**
- High conviction
- Statistically **profitable in the long run**

### 7.4 Alternate Break-Even Points

When there are **no internal highs/lows** to use as BE:
- Use the **FVG itself** as the BE point
- If price comes back to tap the FVG, move to BE

When FVG comes **before** the internal high/low:
- The FVG becomes a potential bounce area
- Go BE at the FVG, don't wait for the internal level

---

## 8. Multi-Timeframe Analysis

### 8.1 HTF for Bias, LTF for Entry

| Timeframe | Purpose | Usage |
|-----------|---------|-------|
| **HTF (1H, 4H)** | Identify Draw on Liquidity | Find obvious inversions that give directional bias |
| **LTF (5m, 30s)** | Execute entries | Find precise IFVG setups within HTF bias direction |

### 8.2 HTF Inversion Process

1. Identify HTF (e.g., 1H) bearish/bullish inversion
2. This gives you the DOL (target) on HTF
3. Drop to LTF and find setups **in the same direction**
4. The LTF setup should have:
   - Own liquidity sweep on LTF
   - Clean engineered setup
   - Target aligned with HTF DOL

### 8.3 Example Workflow

```
4H Chart:
- Obvious bearish inversion identified
- DOL = clear low/EQL below

5m Chart (next day):
- Price retraces back into the inversion area
- Find LTF IFVG setup targeting the same DOL
- Enter with LTF stop loss, target HTF DOL
```

---

## 9. Key Takeaways

### 9.1 Main Principles

1. **The model is simple; context matters**
   - Liquidity is essential for every trade
   - Understanding when to bend rules makes you better

2. **Liquidity is mandatory**
   - No obvious liquidity = no trade
   - Every valid trade has a clear DOL

3. **Rules are guidelines, not absolutes**
   - As you gain experience, learn when exceptions apply
   - Some "invalid" trades are still high probability

### 9.2 What Makes a Great Setup

| Factor | Importance |
|--------|------------|
| Clear liquidity sweep | Critical |
| Delivery from respected FVG | Critical |
| Singular, obvious FVG | High |
| Strong momentum, no chop | High |
| Correct premium/discount | High |
| Clear target | Critical |
| Clean break-even reference | Medium |

### 9.3 What to Avoid

- Trading without obvious liquidity
- Forcing FVGs that aren't there
- Taking C-grade setups
- Ignoring premium/discount positioning
- Trading against HTF bias

---

## Document Validation Checklist

Please review each section and confirm accuracy:

- [ ] **Core Concept**: FVG and IFVG definitions correct?
- [ ] **Reversal Model**: Sequence and logic accurate?
- [ ] **Continuation Model**: 50% equilibrium rule correct?
- [ ] **Entry Rules**: BE point logic and validity rules correct?
- [ ] **Stop Loss**: Three types and their usage correct?
- [ ] **Liquidity Types**: All 7 types identified correctly?
- [ ] **Rating System**: Criteria for each grade accurate?
- [ ] **Advanced Discretion**: Exceptions and special cases correct?
- [ ] **Multi-TF Analysis**: HTF/LTF workflow accurate?

---

*Document created for IFVG TradingView Indicator development*
*Last updated: 2026-01-20*
