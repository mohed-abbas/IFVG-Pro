# FVG Detection & HTF Analysis — Complete Implementation Analysis

```
 ╔══════════════════════════════════════════════════════════════════════════╗
 ║                                                                        ║
 ║   ███████╗██╗   ██╗ ██████╗      ██╗  ██╗████████╗███████╗            ║
 ║   ██╔════╝██║   ██║██╔════╝      ██║  ██║╚══██╔══╝██╔════╝            ║
 ║   █████╗  ██║   ██║██║  ███╗     ███████║   ██║   █████╗              ║
 ║   ██╔══╝  ╚██╗ ██╔╝██║   ██║     ██╔══██║   ██║   ██╔══╝              ║
 ║   ██║      ╚████╔╝ ╚██████╔╝     ██║  ██║   ██║   ██║                ║
 ║   ╚═╝       ╚═══╝   ╚═════╝      ╚═╝  ╚═╝   ╚═╝   ╚═╝                ║
 ║                                                                        ║
 ║      FVG Detection + Higher Timeframe Multi-TF Analysis                ║
 ║      Source: src/IFVG_Indicator.pine (Pine Script v6)                  ║
 ╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [The FVG Type — Every Field](#2-the-fvg-type--every-field)
3. [LTF FVG Detection — Deep Dive](#3-ltf-fvg-detection--deep-dive)
4. [Series-of-Gaps Merging](#4-series-of-gaps-merging)
5. [HTF Analysis System — Deep Dive](#5-htf-analysis-system--deep-dive)
6. [HTF Bias Determination & LTF Filtering](#6-htf-bias-determination--ltf-filtering)
7. [Rendering Pipeline](#7-rendering-pipeline)
8. [Complete Parameter Reference](#8-complete-parameter-reference)
9. [Impact on the Whole Indicator](#9-impact-on-the-whole-indicator)
10. [request.security Budget Analysis](#10-requestsecurity-budget-analysis)
11. [Comparison with Best Practices](#11-comparison-with-best-practices)
12. [Summary & Gaps](#12-summary--gaps)

---

## 1. Architecture Overview

FVG detection and HTF analysis form the **foundation layer** of the indicator. Everything
downstream depends on them:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    TWO PARALLEL FVG PIPELINES                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                   LTF PIPELINE (current chart)                  │     │
│  │                                                                 │     │
│  │  detect_fvg() ──► merge check ──► g_fvg_array ──► inversion    │     │
│  │       │                                              │          │     │
│  │       │    Uses: high/low/close directly              │          │     │
│  │       │    Gate: barstate.isconfirmed                 │          │     │
│  │       │    Filter: ATR * min_size_mult                ▼          │     │
│  │       │                                          g_ifvg_array   │     │
│  │       │                                          (graded, BE,   │     │
│  │       │                                           SL, DOL)      │     │
│  │       └──► render_fvg_boxes()                                   │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐     │
│  │                   HTF PIPELINE (2 timeframes)                   │     │
│  │                                                                 │     │
│  │  request.security() ──► detect_htf_fvg() ──► dedup check       │     │
│  │       │                                          │              │     │
│  │       │    Uses: htf_high/low/close via tuples    │              │     │
│  │       │    Gate: bar_changed + isconfirmed        │              │     │
│  │       │    Filter: htf_atr * min_size_mult        ▼              │     │
│  │       │                                     g_htf_fvg_array     │     │
│  │       │                                     g_htf2_fvg_array    │     │
│  │       │                                          │              │     │
│  │       │    check_htf_inversions() ◄──────────────┘              │     │
│  │       │              │                                          │     │
│  │       │              ▼                                          │     │
│  │       │    g_htf_ifvg_array ──► get_htf_bias() ──► FILTER      │     │
│  │       │    g_htf2_ifvg_array         │              │           │     │
│  │       │                              │              ▼           │     │
│  │       │                         ┌────┴────┐   LTF IFVGs        │     │
│  │       │                         │Dashboard│   show/hide        │     │
│  │       │                         └─────────┘                     │     │
│  │       └──► render_htf_fvg_boxes() + render_htf_ifvg_boxes()    │     │
│  └─────────────────────────────────────────────────────────────────┘     │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

**Key distinction**: LTF FVGs get full grading (A+ to C) with BE/SL/DOL when they invert.
HTF FVGs get simplified inversion (grade = "HTF") and exist purely to establish directional
bias for filtering LTF setups.

---

## 2. The FVG Type — Every Field

Defined at `src/IFVG_Indicator.pine` lines 46-56.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          FVG TYPE DEFINITION                            │
├──────────────┬─────────┬────────────────────────────────────────────────┤
│ Field        │ Type    │ Purpose                                        │
├──────────────┼─────────┼────────────────────────────────────────────────┤
│ top          │ float   │ Upper boundary of the gap                      │
│ bottom       │ float   │ Lower boundary of the gap                      │
│ mid          │ float   │ Midpoint: (top + bottom) / 2                   │
│ start_bar    │ int     │ Bar index of candle 1 (leftmost of the 3)      │
│ end_bar      │ int     │ Bar index of candle 3 (rightmost of the 3)     │
│ is_bullish   │ bool    │ true = bullish (gap up), false = bearish       │
│ status       │ string  │ "active", "inverted", or "mitigated"           │
│ timeframe    │ string  │ "" = current TF, "60" = 1H, "240" = 4H, etc   │
│ box_id       │ box     │ Drawing reference for the FVG rectangle        │
│ label_id     │ label   │ Drawing reference for the "FVG ▲/▼" text       │
└──────────────┴─────────┴────────────────────────────────────────────────┘
```

The `timeframe` field is the only way to distinguish LTF from HTF FVGs. Empty string = LTF.

---

## 3. LTF FVG Detection — Deep Dive

**Location**: `detect_fvg()` at lines 526-564

### 3A. The 3-Candle Pattern

An FVG is a price imbalance where the wicks of candle 1 and candle 3 don't overlap,
creating a "gap" at candle 2:

```
  BULLISH FVG                              BEARISH FVG
  ═══════════                              ═══════════

  Candle 1    Candle 2    Candle 3         Candle 1    Candle 2    Candle 3
  (bar[2])    (bar[1])    (bar[0])         (bar[2])    (bar[1])    (bar[0])

                             ┌──┐             ┌──┐
                             │  │             │  │
                 ┌──┐        │  │             │  │        ┌──┐
                 │  │        └──┘             └──┘        │  │
                 │  │    ─── low[0] = top                 │  │
                 │  │        :                :           │  │
                 └──┘        :  ▲ GAP ▲       :  ▼ GAP ▼ └──┘
     ┌──┐                    :                :                    ┌──┐
     │  │    ─── high[2] = bottom         ─── high[0] = bottom    │  │
     │  │                                                         │  │
     │  │                                                         │  │
     └──┘                                                         └──┘
                                          ─── low[2] = top

  Condition:  low[0] > high[2]             Condition:  high[0] < low[2]
  Gap size:   low[0] - high[2]             Gap size:   low[2] - high[0]
  top:        low[0]                       top:        low[2]
  bottom:     high[2]                      bottom:     high[0]
```

### 3B. Detection Algorithm Step-by-Step

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     LTF FVG DETECTION FLOW                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. GUARD: barstate.isconfirmed AND not na(atr_value)                    │
│     │                                                                    │
│     │  ► Only confirmed bars (prevents repainting)                       │
│     │  ► ATR must be available (won't run on first 14 bars)              │
│     │                                                                    │
│  2. CALCULATE MINIMUM GAP SIZE                                           │
│     │                                                                    │
│     │  min_gap = atr_value * i_fvg_min_size_mult                         │
│     │         = ATR(14)   * 0.25    (defaults)                           │
│     │                                                                    │
│  3. CHECK BULLISH FVG FIRST                                              │
│     │                                                                    │
│     │  bullish_gap_size = low[0] - high[2]                               │
│     │  if bullish_gap_size > min_gap ──► CREATE bullish FVG              │
│     │                                                                    │
│  4. CHECK BEARISH FVG (only if no bullish found)                         │
│     │                                                                    │
│     │  bearish_gap_size = low[2] - high[0]                               │
│     │  if bearish_gap_size > min_gap AND na(result)                      │
│     │      ──► CREATE bearish FVG                                        │
│     │                                                                    │
│  5. RETURN: FVG object or na                                             │
│                                                                          │
│  ⚠ HARDCODED: Bullish checked FIRST — if both exist on same bar,        │
│    bullish wins. Bearish never detected on a dual-FVG bar.               │
│                                                                          │
│  ⚠ HARDCODED: Max ONE FVG per bar.                                       │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 3C. What Happens After Detection (Main Loop, lines 2267-2273)

```
  new_fvg = detect_fvg()
       │
       ▼
  not na(new_fvg)?
       │
       ├── YES ──► merge_with_existing_fvg(new_fvg)
       │                │
       │                ├── merged=true  ──► absorbed into existing (no new entry)
       │                └── merged=false ──► array.push(g_fvg_array, new_fvg)
       │                                          │
       │                                          ▼
       │                                   cleanup_fvg_array()
       │                                   (FIFO if > i_max_fvgs)
       │
       └── NO ──► nothing happens this bar
```

---

## 4. Series-of-Gaps Merging

**Location**: `merge_with_existing_fvg()` at lines 491-517

When multiple FVGs form in the same directional leg (common in strong displacement moves),
they are consolidated into one zone per the DodgysDD strategy.

### 4A. Merge Criteria

```
  All three must be true:
  ┌─────────────────────────────────────────────────────────┐
  │ 1. Same direction:  existing.is_bullish == new.is_bullish│
  │ 2. Active status:   existing.status == "active"          │
  │ 3. Proximity:       |new.end_bar - existing.end_bar| <= 5│
  └─────────────────────────────────────────────────────────┘
```

### 4B. Merge Operation

```
  BEFORE MERGE                         AFTER MERGE
  ════════════                         ═══════════

  ┌───────────┐                        ┌─────────────────────────────┐
  │ FVG #1    │                        │                             │
  │ top = 110 │     ┌───────────┐      │  MERGED FVG                 │
  │ bot = 105 │     │ FVG #2    │      │  top  = max(110,112) = 112  │
  │ bar = 50  │     │ top = 112 │ ──►  │  bot  = min(105,107) = 105  │
  └───────────┘     │ bot = 107 │      │  mid  = (112+105)/2 = 108.5 │
                    │ bar = 53  │      │  end  = max(50,53)  = 53    │
                    └───────────┘      └─────────────────────────────┘

  ► Envelope: max(tops), min(bottoms)
  ► end_bar: max of both
  ► start_bar: kept from the existing FVG (not updated)
  ► Old box/label deleted, redrawn on next render cycle
```

### 4C. No Overlap Check

Unlike the singularity check used in grading (which checks proximity AND overlap), merging
only checks proximity. Two FVGs 3 bars apart with non-overlapping price zones WILL still
merge if they have the same direction. This creates a zone spanning a wider price range.

---

## 5. HTF Analysis System — Deep Dive

**Location**: Section 5B, lines 566-771

### 5A. Data Acquisition via request.security

The HTF system uses **2 request.security calls** to pull data from 2 configurable timeframes.
Each call fetches a 7-element tuple:

```
┌──────────────────────────────────────────────────────────────────────────┐
│             request.security TUPLE STRUCTURE (per HTF)                  │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Line 575 (HTF 1):                                                       │
│  [htf_high, htf_low, htf_close, htf_high_2, htf_low_2,                 │
│   htf_bar_idx_raw, htf_atr]                                             │
│                                                                          │
│  = request.security(                                                     │
│      syminfo.tickerid,     // Same symbol                                │
│      i_htf_timeframe,      // e.g. "60" = 1H                            │
│      [high, low, close, high[2], low[2], bar_index, ta.atr(14)],        │
│      lookahead = barmerge.lookahead_off  // NO repainting                │
│    )                                                                     │
│                                                                          │
│  Element breakdown:                                                      │
│  ┌────────────────┬───────────────────────────────────────┐              │
│  │ htf_high       │ Current HTF bar's high                │              │
│  │ htf_low        │ Current HTF bar's low                 │              │
│  │ htf_close      │ Current HTF bar's close               │              │
│  │ htf_high_2     │ HTF bar 2 ago's high (for FVG candle 1│              │
│  │ htf_low_2      │ HTF bar 2 ago's low  (for FVG candle 1│              │
│  │ htf_bar_idx_raw│ HTF bar's bar_index (for change detect)│              │
│  │ htf_atr        │ HTF ATR(14) for sizing                │              │
│  └────────────────┴───────────────────────────────────────┘              │
│                                                                          │
│  Line 579 (HTF 2): identical structure with htf2_ prefix                 │
│                                                                          │
│  ⚠ lookahead_off: ensures data is only available AFTER the HTF           │
│    bar closes. Prevents future data leaking into current bar.            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5B. Bar Change Detection

HTF bars contain multiple LTF bars. We only want to check for new HTF FVGs when the
HTF bar actually changes:

```
  var int prev_htf_bar = na                                    (line 583)
  bool htf_bar_changed = na(prev_htf_bar) or                  (line 585)
                          htf_bar_idx != prev_htf_bar
  prev_htf_bar := htf_bar_idx                                 (line 587)

  TIMELINE EXAMPLE (chart = 5m, HTF = 1H):

  5m bars:    |  1  |  2  |  3  |  4  |  5  |  6  |  7  |  8  |  9  | 10 | 11 | 12 | 13 |
  1H bar:     |←── HTF bar A (bar_idx=100) ──────────────────→|←── HTF bar B (bar_idx=112)
  bar_changed:|  T  |  F  |  F  |  F  |  F  |  F  |  F  |  F  |  F  |  F |  F |  F |  T  |
                ▲                                                                      ▲
                │                                                                      │
           First 5m bar of new 1H bar                                    First 5m bar of next 1H bar
           triggers HTF FVG detection                                    triggers again
```

### 5C. HTF FVG Detection Algorithm

**Location**: `detect_htf_fvg()` at lines 593-631

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      HTF FVG DETECTION FLOW                             │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GUARDS (ALL must pass):                                                 │
│    ✓ i_enable_htf == true                                                │
│    ✓ bar_changed == true (new HTF bar)                                   │
│    ✓ barstate.isconfirmed (no repainting)                                │
│    ✓ not na(atr_val) (HTF ATR available)                                 │
│                                                                          │
│  DETECTION (same logic as LTF):                                          │
│    ► Bullish: htf_low > htf_high_2  (gap > htf_atr * min_size_mult)     │
│    ► Bearish: htf_high < htf_low_2  (gap > htf_atr * min_size_mult)     │
│    ► Bullish checked first (same priority as LTF)                        │
│                                                                          │
│  KEY DIFFERENCE FROM LTF:                                                │
│    ► Uses HTF ATR (htf_atr) for sizing, not LTF ATR                     │
│    ► start_bar = bar_index - 2 (APPROXIMATE LTF position)                │
│    ► timeframe field = tf string (e.g. "60", "240")                      │
│    ► No merge check (HTF FVGs are not merged)                            │
│                                                                          │
│  POST-DETECTION DEDUP (line 2281):                                       │
│    htf_fvg_exists() checks if a similar FVG already exists:              │
│    ► Same direction                                                      │
│    ► top within 0.1 ATR                                                  │
│    ► bottom within 0.1 ATR                                               │
│    If duplicate ──► discarded                                            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 5D. HTF Inversion (Simplified)

**Location**: `check_htf_inversions()` at lines 673-738

HTF inversions are **simpler** than LTF inversions — no grading, no BE/SL/DOL:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   HTF INVERSION vs LTF INVERSION                        │
├───────────────────────┬──────────────────────┬───────────────────────────┤
│ Feature               │ LTF                  │ HTF                       │
├───────────────────────┼──────────────────────┼───────────────────────────┤
│ Inversion trigger     │ Zone entry + body    │ Body close only           │
│                       │ close through         │ (no zone entry check)     │
│ Direction flip        │ Yes (NOT fvg)        │ Yes (NOT fvg)             │
│ Grade                 │ A+ to C (calculated) │ "HTF" (fixed string)      │
│ BE level              │ Swing-based          │ FVG boundary (simple)     │
│ SL level              │ Configurable         │ FVG boundary (simple)     │
│ DOL target            │ Liquidity search     │ na (none)                 │
│ Sweep check           │ 20-bar lookback      │ false (always)            │
│ Momentum              │ Body ratio analysis  │ "neutral" (always)        │
│ entry_valid           │ SL check on candle   │ true (always)             │
│ Purpose               │ Tradeable setup      │ Bias determination only   │
├───────────────────────┼──────────────────────┼───────────────────────────┤
│ Inversion check       │ Lines 1412-1428      │ Lines 686-694             │
│ (bullish FVG)         │ wick enters zone     │ htf_close < fvg.bottom    │
│                       │ AND close < bottom   │ (that's it)               │
├───────────────────────┼──────────────────────┼───────────────────────────┤
│ Inversion check       │ Lines 1422-1428      │ Lines 692-694             │
│ (bearish FVG)         │ wick enters zone     │ htf_close > fvg.top       │
│                       │ AND close > top      │ (that's it)               │
└───────────────────────┴──────────────────────┴───────────────────────────┘

  HTF INVERSION IS SIMPLER:
  ═════════════════════════

  LTF requires:  (price entered zone OR price through zone) AND body close
  HTF requires:  just body close through boundary

  HTF skips the zone-entry check entirely. This means an HTF candle that
  gaps completely past the zone still counts — which is more permissive
  but acceptable since HTF is only used for bias, not trading signals.
```

### 5E. HTF Mitigation

**Location**: `check_htf_mitigations()` at lines 743-770

Same logic as LTF mitigation:
- Bullish HTF IFVG mitigated when `htf_close < ifvg.bottom`
- Bearish HTF IFVG mitigated when `htf_close > ifvg.top`
- Drawing cleanup + array removal

**Uses HTF close**, not LTF close. The HTF zone can only be mitigated by an HTF-level
close through it.

---

## 6. HTF Bias Determination & LTF Filtering

### 6A. Bias Calculation

**Location**: `get_htf_bias()` at lines 473-483

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     HTF BIAS DETERMINATION                              │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  1. Check HTF 1 array: get LAST (most recent) IFVG                       │
│     ├── status == "inverted" AND is_bullish  ──► htf1_b = "bullish"      │
│     ├── status == "inverted" AND !is_bullish ──► htf1_b = "bearish"      │
│     └── otherwise                            ──► htf1_b = "neutral"      │
│                                                                          │
│  2. Check HTF 2 array: same logic ──► htf2_b                             │
│                                                                          │
│  3. COMBINE:                                                             │
│     if htf1_b != "neutral" ──► result = htf1_b   (HTF 1 takes priority)  │
│     else                   ──► result = htf2_b   (fallback to HTF 2)     │
│                                                                          │
│  ⚠ HTF 1 ALWAYS takes priority over HTF 2 when both have a bias.         │
│  ⚠ Only the MOST RECENT IFVG from each array matters.                    │
│  ⚠ If BOTH are neutral ──► result = "neutral" (no filtering applied).    │
│                                                                          │
│  EXAMPLE:                                                                │
│  ─────────                                                               │
│  HTF 1 (1H): Last IFVG is bullish  ──► htf1_b = "bullish"               │
│  HTF 2 (4H): Last IFVG is bearish  ──► htf2_b = "bearish"               │
│  Result: "bullish" (HTF 1 wins)                                          │
│                                                                          │
│  CONFLICT: No conflict resolution. Lower HTF always wins.                │
│  This means a 1H bullish bias overrides a 4H bearish bias.               │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### 6B. LTF Filtering by HTF Bias

**Location**: `render_ifvg_boxes()` at lines 1744-1757

```
  if i_enable_htf AND i_htf_filter_ltf:
      combined_bias = get_htf_bias()
      if combined_bias != "neutral":
          htf_aligned = (bias == "bullish" AND ifvg.is_bullish) OR
                        (bias == "bearish" AND NOT ifvg.is_bullish)

  ┌──────────────────────────────────────────────────────────────────┐
  │  HTF Bias  │  LTF Bullish IFVG  │  LTF Bearish IFVG            │
  ├────────────┼────────────────────┼────────────────────────────────┤
  │  bullish   │  ✓ SHOWN           │  ✗ HIDDEN                     │
  │  bearish   │  ✗ HIDDEN          │  ✓ SHOWN                      │
  │  neutral   │  ✓ SHOWN           │  ✓ SHOWN (no filtering)       │
  └────────────┴────────────────────┴────────────────────────────────┘

  ⚠ Filtering is RENDERING ONLY — LTF IFVGs are still TRACKED in memory.
     They are still graded, their BE/SL is still monitored, and they
     still appear in g_ifvg_array. They are just not drawn on the chart.

  ⚠ Filtering happens PER RENDER CYCLE. If HTF bias flips, previously
     hidden LTF IFVGs can suddenly appear (if they're still active).
```

### 6C. Dashboard Display

**Location**: Lines 2220-2240

```
  ┌───────────────────────┐
  │  HTF Bias:   BULLISH  │  ◄── Color-coded: green=bull, red=bear, gray=neutral
  │  HTF:     1H / 4H     │  ◄── Shows both timeframe labels
  └───────────────────────┘

  get_tf_label() converts raw strings to human-readable:
    "60"  → "1H"
    "240" → "4H"
    "15"  → "15m"
    etc.
```

---

## 7. Rendering Pipeline

### 7A. LTF FVG Rendering

**Location**: `render_fvg_boxes()` at lines 1667-1708

```
  For each FVG in g_fvg_array where status == "active":

  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │   ┌───────────────────────── right_edge         │
  │   │         FVG ZONE                   │        │
  │   │  bg: bullish/bearish color + opacity        │
  │   │  border: bullish/bearish color              │
  │   │  border_width: i_fvg_border_width           │
  │   │  border_style: i_fvg_border_style           │
  │   │                                    │        │
  │   └────────────────────────────────────┘        │
  │                           "FVG ▲" or "FVG ▼"   │
  │                           (bottom-right corner) │
  └─────────────────────────────────────────────────┘

  Gate: i_show_active_fvg must be true
  Delete-and-recreate pattern every bar (prevents stale drawings)
```

### 7B. HTF FVG Rendering

**Location**: `render_htf_fvg_boxes()` at lines 1895-1944

```
  For each FVG in g_htf_fvg_array / g_htf2_fvg_array where status == "active":

  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │   ┌─══════════════════════════ right_edge        │
  │   ║         HTF FVG ZONE                ║       │
  │   ║  bg: bullish/bearish + htf_opacity  ║       │
  │   ║  border: bullish/bearish color      ║       │
  │   ║  border_width: i_htf_border_width   ║       │
  │   ║  border_style: SOLID (always)       ║       │
  │   ║                                     ║       │
  │   ╚═════════════════════════════════════╝       │
  │                     "[1H] FVG ▲" or "[4H] FVG ▼"│
  │                     (at fvg.bottom or fvg.top)  │
  └─────────────────────────────────────────────────┘

  Key differences from LTF:
  ► Thicker borders (default 3 vs 1)
  ► Label includes "[TF]" prefix
  ► Left edge clamped: math.max(start_bar, bar_index - 400)
    (prevents "bar index too far" error for old HTF zones)
  ► Border style always solid (not configurable for HTF)
```

### 7C. HTF IFVG Rendering

**Location**: `render_htf_ifvg_boxes()` at lines 1949-1997

```
  ┌─────────────────────────────────────────────────┐
  │                                                 │
  │   ┌─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─  right_edge      │
  │   ┊         HTF IFVG ZONE              ┊       │
  │   ┊  bg: GRAY + htf_opacity            ┊       │
  │   ┊  border: bull/bear color            ┊       │
  │   ┊  border_width: i_htf_border_width   ┊       │
  │   ┊  border_style: DASHED (always)      ┊       │
  │   ┊                                     ┊       │
  │   └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─┘       │
  │                  "[1H] IFVG LONG" / "SHORT"     │
  └─────────────────────────────────────────────────┘

  ► Gray background (always) — distinguished from colored LTF FVGs
  ► Dashed border (always) — distinguished from solid HTF FVGs
  ► Label shows direction as "LONG"/"SHORT" (not "BUY"/"SELL")
  ► No BE/SL/entry lines (HTF IFVGs are bias indicators, not setups)
```

---

## 8. Complete Parameter Reference

### 8A. FVG Detection Parameters

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    FVG DETECTION PARAMETERS                            ║
╠══════════════════════╦═════════╦═══════╦════════════════════════════════╣
║ Parameter            ║ Default ║ Range ║ Impact                         ║
╠══════════════════════╬═════════╬═══════╬════════════════════════════════╣
║ i_fvg_atr_period     ║ 14      ║ 5-50  ║ ATR period for min gap sizing  ║
║ i_fvg_min_size_mult  ║ 0.25    ║.05-1.0║ Min gap = ATR * this value     ║
║ i_show_active_fvg    ║ true    ║ bool  ║ Show/hide active FVG boxes     ║
║ i_show_ifvg          ║ true    ║ bool  ║ Show/hide inverted FVG boxes   ║
║ i_max_fvgs           ║ 3       ║ 2-50  ║ Max active FVGs (FIFO cleanup) ║
║ i_max_ifvgs          ║ 10      ║ 2-100 ║ Max IFVGs tracked              ║
║ i_extend_bars        ║ 15      ║ 10-200║ Right edge extension (bars)    ║
╠══════════════════════╬═════════╬═══════╬════════════════════════════════╣
║                     VISUAL PARAMETERS                                  ║
╠══════════════════════╬═════════╬═══════╬════════════════════════════════╣
║ i_bullish_color      ║ #089981 ║ color ║ All bullish FVG elements       ║
║ i_bearish_color      ║ #F23645 ║ color ║ All bearish FVG elements       ║
║ i_fvg_opacity        ║ 85      ║ 50-95 ║ Active FVG box transparency    ║
║ i_fvg_border_width   ║ 1       ║ 1-4   ║ LTF FVG border thickness       ║
║ i_fvg_border_style   ║ "Solid" ║ 3 opts║ LTF FVG border style           ║
║ i_show_labels        ║ true    ║ bool  ║ Show/hide all labels           ║
║ i_label_size         ║ "small" ║ 3 opts║ tiny / small / normal          ║
╚══════════════════════╩═════════╩═══════╩════════════════════════════════╝
```

### 8B. HTF Analysis Parameters

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    HTF ANALYSIS PARAMETERS                             ║
╠══════════════════════╦═════════╦═══════╦════════════════════════════════╣
║ Parameter            ║ Default ║ Range ║ Impact                         ║
╠══════════════════════╬═════════╬═══════╬════════════════════════════════╣
║ i_enable_htf         ║ true    ║ bool  ║ Master switch for all HTF      ║
║ i_htf_timeframe      ║ "60"    ║ TF    ║ Primary HTF (default 1H)      ║
║ i_htf_timeframe_2    ║ "240"   ║ TF    ║ Secondary HTF (default 4H)    ║
║ i_show_htf_fvg       ║ true    ║ bool  ║ Show HTF FVG boxes on chart   ║
║ i_show_htf_ifvg      ║ true    ║ bool  ║ Show HTF IFVG boxes on chart  ║
║ i_htf_filter_ltf     ║ true    ║ bool  ║ Filter LTF IFVGs by HTF bias  ║
║ i_htf_box_opacity    ║ 75      ║ 50-95 ║ HTF box transparency           ║
║ i_htf_border_width   ║ 3       ║ 1-5   ║ HTF border thickness           ║
╚══════════════════════╩═════════╩═══════╩════════════════════════════════╝
```

### 8C. Hardcoded Constants

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    HARDCODED CONSTANTS                                  ║
╠══════════════════════════════╦═══════════╦═══════╦══════════════════════╣
║ Constant                     ║ Value     ║ Line  ║ Impact               ║
╠══════════════════════════════╬═══════════╬═══════╬══════════════════════╣
║ Bullish FVG priority         ║ Always 1st║ 550   ║ Bullish wins on tie  ║
║ Max FVGs per bar             ║ 1         ║ 550   ║ Only 1 detected/bar  ║
║ Merge proximity threshold    ║ 5 bars    ║ 500   ║ Series-of-gaps merge ║
║ HTF dedup tolerance          ║ 0.1 ATR   ║ 643   ║ Duplicate zone check ║
║ HTF FVG bar position         ║ bar_idx-2 ║ 606   ║ Approximate LTF pos  ║
║ HTF FVG border style         ║ Solid     ║ 1926  ║ Always solid         ║
║ HTF IFVG border style        ║ Dashed    ║ 1979  ║ Always dashed        ║
║ HTF IFVG background          ║ Gray      ║ 1965  ║ Always gray          ║
║ HTF IFVG grade               ║ "HTF"     ║ 718   ║ Not graded (A-C)     ║
║ HTF IFVG has_sweep           ║ false     ║ 725   ║ Never checked        ║
║ HTF IFVG momentum            ║ "neutral" ║ 726   ║ Never assessed       ║
║ HTF IFVG entry_valid         ║ true      ║ 719   ║ Always valid         ║
║ HTF IFVG dol                 ║ na        ║ 724   ║ No DOL target        ║
║ HTF bias priority            ║ HTF1 first║ 482   ║ HTF1 overrides HTF2  ║
║ HTF left edge clamp          ║ bar_idx-400║1916  ║ Prevent old-bar error║
║ request.security calls       ║ 2 used    ║ 575   ║ Of 40 max budget     ║
║ Tuple elements per call      ║ 7         ║ 575   ║ Of 127 max budget    ║
║ request.security lookahead   ║ off       ║ 575   ║ No future data       ║
║ Swing array cap              ║ 50        ║ 806   ║ Max stored swings    ║
║ LTF FVG label position       ║ bottom    ║ 1700  ║ Always at fvg.bottom ║
║ HTF FVG label position       ║ varies    ║ 1936  ║ bottom(bull)/top(bear)║
║ get_tf_label max recognized  ║ 240 (4H)  ║ 2019  ║ Higher TFs show raw  ║
╚══════════════════════════════╩═══════════╩═══════╩══════════════════════╝
```

---

## 9. Impact on the Whole Indicator

### 9A. FVG Detection Impact

```
  FVG Detection is the ROOT of ALL downstream processing:

  detect_fvg()
       │
       ├──► g_fvg_array ──────────────────────────────────────────┐
       │         │                                                │
       │         ├──► check_inversions() ──► IFVG created          │
       │         │         │                    │                  │
       │         │         │                    ├──► Grade (A+ - C)│
       │         │         │                    ├──► BE/SL levels  │
       │         │         │                    ├──► DOL target    │
       │         │         │                    ├──► Entry validity│
       │         │         │                    └──► Dashboard     │
       │         │         │                                       │
       │         ├──► is_fvg_singular() ──► quality_score for grade│
       │         │                                                │
       │         └──► render_fvg_boxes() ──► visual on chart       │
       │                                                           │
       │  If FVG detection is wrong, EVERYTHING downstream is wrong│
       └───────────────────────────────────────────────────────────┘
```

### 9B. HTF Analysis Impact

```
  HTF Analysis affects the indicator through TWO channels:

  Channel 1: VISUAL (direct)
  ──────────────────────────
  HTF FVG/IFVG boxes rendered on chart ──► visual confluence zones
  Traders can see where HTF structure aligns with LTF setups

  Channel 2: FILTER (indirect but powerful)
  ──────────────────────────────────────────
  HTF IFVGs ──► get_htf_bias() ──► "bullish" / "bearish" / "neutral"
                                        │
                                        ▼
                            render_ifvg_boxes() gate:
                            LTF IFVGs that conflict
                            with HTF bias are HIDDEN

  ⚠ This means HTF can SUPPRESS valid LTF setups.
    A perfectly graded A+ LTF bullish IFVG will NOT be shown
    if HTF bias is bearish and i_htf_filter_ltf is true.

  Channel 3: DASHBOARD (informational)
  ─────────────────────────────────────
  HTF bias displayed as "BULLISH" / "BEARISH" in dashboard
  HTF timeframes shown as "1H / 4H"
```

### 9C. Data Store Relationships

```
  ┌──────────────────────────────────────────────────────────────────┐
  │                     ARRAY ECOSYSTEM                             │
  ├──────────────────┬─────────────────────┬─────────────────────────┤
  │ Array            │ Max Size            │ Used By                 │
  ├──────────────────┼─────────────────────┼─────────────────────────┤
  │ g_fvg_array      │ i_max_fvgs (3)      │ LTF detection, merge,   │
  │                  │                     │ inversion, singularity  │
  │ g_ifvg_array     │ i_max_ifvgs (10)    │ LTF tracking, rendering,│
  │                  │                     │ dashboard               │
  │ g_htf_fvg_array  │ i_max_fvgs (3)      │ HTF1 FVG detection      │
  │ g_htf2_fvg_array │ i_max_fvgs (3)      │ HTF2 FVG detection      │
  │ g_htf_ifvg_array │ i_max_ifvgs (10)    │ HTF1 bias, rendering    │
  │ g_htf2_ifvg_array│ i_max_ifvgs (10)    │ HTF2 bias, rendering    │
  ├──────────────────┼─────────────────────┼─────────────────────────┤
  │ TOTAL ARRAYS     │ 6                   │ All use same limits     │
  │ TOTAL FVG OBJECTS│ up to 6+20+6+6+20+20│ = 78 max objects        │
  └──────────────────┴─────────────────────┴─────────────────────────┘

  ⚠ HTF arrays share the same i_max_fvgs / i_max_ifvgs limits as LTF.
     This is efficient but means i_max_fvgs=3 also limits HTF FVGs to 3.
```

---

## 10. request.security Budget Analysis

```
╔══════════════════════════════════════════════════════════════════════════╗
║                  request.security BUDGET STATUS                        ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  TradingView limits:                                                   ║
║    ► Max 40 request.security() calls per indicator                     ║
║    ► Max 127 tuple elements total across all calls                     ║
║                                                                        ║
║  Current usage:                                                        ║
║  ┌──────────────┬────────────┬──────────────────────────────┐          ║
║  │ Call         │ Elements   │ Purpose                       │          ║
║  ├──────────────┼────────────┼──────────────────────────────┤          ║
║  │ HTF 1 (L575)│ 7          │ high,low,close,high[2],low[2]│          ║
║  │              │            │ bar_index, ta.atr(14)        │          ║
║  │ HTF 2 (L579)│ 7          │ Same tuple for 2nd timeframe │          ║
║  ├──────────────┼────────────┼──────────────────────────────┤          ║
║  │ TOTAL        │ 2 calls    │ 14 elements                  │          ║
║  │ REMAINING    │ 38 calls   │ 113 elements                 │          ║
║  └──────────────┴────────────┴──────────────────────────────┘          ║
║                                                                        ║
║  ⚠ Phase 4 will need additional calls for:                             ║
║    - Session data (NY, London open/close times)                        ║
║    - PD Zone / dealing range from higher TF                            ║
║    - Possibly 3rd HTF for weekly structure                             ║
║                                                                        ║
║  Budget is healthy. 38 remaining calls is ample for Phase 4.           ║
║                                                                        ║
║  Optimization: Both calls use consolidated 7-element tuples rather     ║
║  than separate calls for each field. This is correct — one call per    ║
║  timeframe is optimal.                                                 ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 11. Comparison with Best Practices

### 11A. FVG Detection

```
┌──────────────────┬────────────────────────┬─────────────────────┬────────────┐
│ Aspect           │ Our Implementation     │ ICT Best Practice   │ Assessment │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ 3-candle pattern │ low[0]>high[2] (bull)  │ Standard ICT FVG    │ CORRECT    │
│                  │ high[0]<low[2] (bear)  │ definition          │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Boundary source  │ Wicks (high/low)       │ Wicks define FVG    │ CORRECT    │
│                  │                        │ boundaries in ICT   │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Size filter      │ ATR * 0.25 minimum     │ Many indicators     │ BETTER     │
│                  │                        │ don't filter at all │ than most  │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ ATR adaptation   │ Market-agnostic via    │ Essential for multi-│ CORRECT    │
│                  │ ATR-based sizing       │ instrument usage    │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Repainting guard │ barstate.isconfirmed   │ Required for        │ CORRECT    │
│                  │                        │ reliable signals    │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Per-bar limit    │ 1 FVG max (bull first) │ Not standardized.   │ DEBATABLE  │
│                  │                        │ Some detect both.   │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Series-of-gaps   │ Merge within 5 bars    │ DodgysDD-specific.  │ GOOD       │
│ handling         │                        │ ICT: each is        │ (custom)   │
│                  │                        │ separate             │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Midpoint calc    │ (top + bottom) / 2     │ Standard. Some add  │ CORRECT    │
│                  │                        │ CE (consequent       │            │
│                  │                        │ encroachment) at mid│            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ FVG aging/expiry │ No expiry — lives until│ Some indicators     │ OK         │
│                  │ inverted or FIFO'd     │ expire old FVGs     │ (FIFO acts │
│                  │                        │ after N bars        │ as expiry) │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Candle 2 role    │ Not checked at all     │ Candle 2 (middle)   │ MINOR GAP  │
│                  │                        │ is the "imbalance"  │            │
│                  │                        │ candle — some check │            │
│                  │                        │ its body size       │            │
└──────────────────┴────────────────────────┴─────────────────────┴────────────┘
```

### 11B. HTF Data Acquisition

```
┌──────────────────┬────────────────────────┬─────────────────────┬────────────┐
│ Aspect           │ Our Implementation     │ Best Practice       │ Assessment │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Method           │ request.security()     │ Standard TradingView│ CORRECT    │
│                  │ with tuple             │ approach            │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Lookahead        │ barmerge.lookahead_off │ Required to prevent │ CORRECT    │
│                  │                        │ future data leak    │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Tuple packing    │ 7 elements per call    │ Optimal — minimizes │ EXCELLENT  │
│                  │ (consolidated)         │ call count          │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Bar change detect│ Track prev_htf_bar     │ Standard pattern    │ CORRECT    │
│                  │ compare with current   │ for HTF detection   │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ # of timeframes  │ 2 (configurable)       │ 2-3 is typical for  │ GOOD       │
│                  │                        │ multi-TF analysis   │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ TF validation    │ No check if HTF > LTF  │ Should verify HTF   │ GAP        │
│                  │                        │ is actually higher  │            │
│                  │                        │ than chart TF       │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ HTF2 disable     │ Set same as HTF1       │ Works but not       │ OK         │
│                  │                        │ obvious UX          │ (adequate) │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Security calls   │ ALWAYS execute (even   │ Could be wrapped in │ MINOR      │
│ when disabled    │ when i_enable_htf=false)│ conditional — but   │ (Pine      │
│                  │                        │ Pine Script requires│ limitation)│
│                  │                        │ top-level calls     │            │
└──────────────────┴────────────────────────┴─────────────────────┴────────────┘
```

### 11C. HTF Bias & Filtering

```
┌──────────────────┬────────────────────────┬─────────────────────┬────────────┐
│ Aspect           │ Our Implementation     │ Best Practice       │ Assessment │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Bias source      │ Most recent HTF IFVG   │ Correct — the last  │ CORRECT    │
│                  │ direction              │ inverted zone shows │            │
│                  │                        │ current structure   │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Multi-TF combine │ HTF1 priority (if not  │ Higher TF should    │ INVERTED   │
│                  │ neutral, ignore HTF2)  │ take priority over  │            │
│                  │                        │ lower HTF — 4H bias │            │
│                  │                        │ should override 1H  │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Conflict resolve │ None — lower HTF wins  │ Options: higher wins│ GAP        │
│                  │                        │ agreement required, │            │
│                  │                        │ or weighted scoring │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Neutral handling │ No filter applied      │ Correct — neutral   │ CORRECT    │
│                  │                        │ means no bias       │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Filter scope     │ Rendering only (data   │ Correct — always    │ CORRECT    │
│                  │ still collected)       │ track, optionally   │            │
│                  │                        │ display             │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ # IFVGs for bias │ Only most recent 1     │ Some use aggregate  │ SIMPLE     │
│                  │                        │ of recent N IFVGs   │ (adequate) │
│                  │                        │ or volume-weighted  │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Bias staleness   │ No expiry — last IFVG  │ Old bias from 100+  │ GAP        │
│                  │ could be very old      │ bars ago may not be │            │
│                  │                        │ relevant            │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ HTF inversion    │ Simplified (close-only)│ Acceptable for bias │ CORRECT    │
│ logic            │                        │ — strictness not    │ (for bias) │
│                  │                        │ needed              │            │
└──────────────────┴────────────────────────┴─────────────────────┴────────────┘
```

### 11D. Rendering & Visual Differentiation

```
┌──────────────────┬────────────────────────┬─────────────────────┬────────────┐
│ Aspect           │ Our Implementation     │ Best Practice       │ Assessment │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ LTF vs HTF       │ Border width (1 vs 3)  │ Clear visual        │ GOOD       │
│ distinction      │ + "[TF]" label prefix  │ hierarchy needed    │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ HTF FVG vs IFVG  │ Solid border vs dashed │ Good differentiation│ GOOD       │
│ distinction      │ + gray bg for IFVG     │                     │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Stale drawing    │ Delete-recreate each   │ Necessary for Pine  │ CORRECT    │
│ prevention       │ bar                    │ Script rendering    │            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Left edge clamp  │ math.max(bar, idx-400) │ Prevents "bar index │ CORRECT    │
│ (HTF only)       │                        │ too far" runtime err│            │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ LTF label pos    │ Always at fvg.bottom   │ Some place at top   │ OK         │
│                  │                        │ for bearish FVGs    │ (minor)    │
├──────────────────┼────────────────────────┼─────────────────────┼────────────┤
│ Drawing limits   │ 500 boxes/lines/labels │ Platform maximum    │ CORRECT    │
│                  │ FIFO cleanup           │ with proper cleanup │            │
└──────────────────┴────────────────────────┴─────────────────────┴────────────┘
```

### 11E. Critical Issues

```
┌──────────────────────────────────────────────────────────────────────────┐
│  ISSUE 1: HTF Bias Priority is Inverted                                │
│  ══════════════════════════════════════                                 │
│                                                                          │
│  Current (line 482):                                                     │
│    result = htf1_b != "neutral" ? htf1_b : htf2_b                       │
│                                                                          │
│  This means HTF 1 (default 1H) OVERRIDES HTF 2 (default 4H).           │
│  In multi-timeframe analysis, the HIGHER timeframe should take           │
│  priority because it represents stronger structural bias.                │
│                                                                          │
│  A 4H bearish IFVG is a stronger signal than a 1H bullish IFVG.         │
│  Currently, the 1H bullish would win and incorrectly show bullish        │
│  LTF setups while the 4H is clearly bearish.                             │
│                                                                          │
│  Should be: result = htf2_b != "neutral" ? htf2_b : htf1_b              │
│  (or: compare TF values and pick the higher one)                         │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 2: No TF Hierarchy Validation                                    │
│  ═══════════════════════════════════                                     │
│                                                                          │
│  Nothing prevents the user from setting:                                 │
│    - Chart TF = 1H                                                       │
│    - HTF 1 = 15m (lower than chart!)                                     │
│    - HTF 2 = 5m  (even lower!)                                           │
│                                                                          │
│  request.security with a LOWER timeframe produces unreliable results     │
│  in Pine Script. It should validate that HTF > chart TF.                 │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 3: HTF FVG Bar Position is Approximate                           │
│  ═════════════════════════════════════════════                           │
│                                                                          │
│  Line 606: start_bar = bar_index - 2                                     │
│                                                                          │
│  This maps the HTF FVG to the CURRENT LTF bar minus 2. But the HTF      │
│  candle 1 (bar[2] on the HTF) could be 24+ LTF bars ago on a 1H         │
│  chart viewed at 5m. The box left edge doesn't represent the true        │
│  HTF candle 1 position.                                                  │
│                                                                          │
│  Impact: HTF FVG boxes appear narrower than they actually are on         │
│  the chart. The price zone (top/bottom) is correct, but the time         │
│  span is wrong.                                                          │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 4: No HTF Bias Expiry                                            │
│  ═══════════════════════════                                             │
│                                                                          │
│  If an HTF IFVG formed 200 bars ago and no new HTF IFVGs have formed,   │
│  that old bias still filters LTF setups. On a 5m chart with 1H HTF,     │
│  200 LTF bars = 200 * 5m = ~17 hours of stale bias.                     │
│                                                                          │
│  The bias should have an age limit or decay mechanism.                   │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 5: HTF FVGs Don't Merge (Series-of-Gaps)                        │
│  ═══════════════════════════════════════════════                         │
│                                                                          │
│  LTF FVGs have merge_with_existing_fvg() for series-of-gaps, but        │
│  HTF FVGs only have htf_fvg_exists() (dedup check, not merge).          │
│                                                                          │
│  If multiple HTF FVGs form in the same leg, they remain separate         │
│  rather than consolidating. This is inconsistent with LTF behavior       │
│  and could produce cluttered HTF boxes.                                  │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 6: i_max_fvgs = 3 is Shared Across LTF and HTF                  │
│  ═════════════════════════════════════════════════════                   │
│                                                                          │
│  All 4 FVG arrays (g_fvg_array, g_htf_fvg_array, g_htf2_fvg_array)     │
│  use i_max_fvgs for their cleanup limit. With a default of 3, each      │
│  array can hold max 3 FVGs. This is fine for LTF (you want few active   │
│  FVGs) but may be too restrictive for HTF where FVGs persist longer     │
│  and serve a different purpose (bias, not trading).                      │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│  ISSUE 7: request.security Always Executes                              │
│  ═════════════════════════════════════════                               │
│                                                                          │
│  Lines 575 and 579 execute UNCONDITIONALLY — even when i_enable_htf     │
│  is false. This is a Pine Script limitation: request.security must be   │
│  at the global scope, not inside conditionals. It wastes 2 security     │
│  calls when HTF is disabled, but doesn't affect correctness.            │
│                                                                          │
│  Not fixable — this is a platform constraint, not a code issue.          │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Summary & Gaps

### What Works Well

```
  ✔ Correct 3-candle FVG pattern (standard ICT definition)
  ✔ ATR-based sizing for market-agnostic detection
  ✔ barstate.isconfirmed guard on all detection (no repainting)
  ✔ lookahead_off on all request.security calls (no future data)
  ✔ Consolidated tuple packing (7 elements per call, efficient)
  ✔ Bar change detection for HTF new-bar triggering
  ✔ Series-of-gaps merging for LTF (DodgysDD-specific, correct)
  ✔ Deduplication check for HTF FVGs
  ✔ Clear visual hierarchy (border width, style, labels)
  ✔ Left edge clamping to prevent runtime errors
  ✔ Rendering-only filtering (data always collected)
  ✔ Separate arrays for each timeframe (clean separation)
  ✔ Healthy request.security budget (38 of 40 calls remaining)
```

### Prioritized Issues

```
  ┌──────────┬──────────────────────────────────────┬──────────────────────┐
  │ Priority │ Issue                                │ Recommendation       │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ HIGH     │ HTF bias priority is inverted:       │ Change line 482 so   │
  │          │ HTF1 (1H) overrides HTF2 (4H)       │ higher TF wins, or   │
  │          │ when it should be the opposite       │ let HTF2 take        │
  │          │                                      │ priority when set    │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ HIGH     │ No TF hierarchy validation:          │ Add runtime check    │
  │          │ user can set HTF < chart TF          │ timeframe.in_seconds │
  │          │                                      │ to verify HTF > LTF  │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ MEDIUM   │ HTF FVG bar position approximate:    │ Map htf_bar_idx to   │
  │          │ start_bar = bar_index - 2 doesn't    │ actual LTF bar_index │
  │          │ reflect true HTF candle 1 position   │ for correct width    │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ MEDIUM   │ No HTF bias expiry:                  │ Add age check —      │
  │          │ stale bias from 200+ bars ago still  │ ignore bias if       │
  │          │ filters LTF setups                   │ > N HTF bars old     │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ MEDIUM   │ HTF FVGs don't merge (series-of-gaps)│ Apply same merge     │
  │          │ inconsistent with LTF behavior       │ logic to HTF arrays  │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ LOW      │ Bullish FVG always wins on dual-FVG  │ Detect both, or let  │
  │          │ bars — bearish never detected        │ larger gap win       │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ LOW      │ Candle 2 (middle) not analyzed       │ Could check body     │
  │          │                                      │ size as quality      │
  │          │                                      │ signal               │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ LOW      │ i_max_fvgs shared across LTF/HTF     │ Consider separate    │
  │          │ arrays — 3 may be too low for HTF    │ HTF max parameter    │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ LOW      │ get_tf_label only recognizes up to   │ Add D, W, M labels   │
  │          │ "240" (4H) — daily/weekly show raw   │ for higher TFs       │
  ├──────────┼──────────────────────────────────────┼──────────────────────┤
  │ INFO     │ request.security always executes     │ Pine Script platform │
  │          │ even when HTF disabled               │ limitation — cannot  │
  │          │                                      │ fix                  │
  └──────────┴──────────────────────────────────────┴──────────────────────┘
```

---

*Analysis generated from src/IFVG_Indicator.pine (2359 lines, Pine Script v6)*
*Compared against ICT/SMC methodology and TradingView best practices*
