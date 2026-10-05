# IFVG (Inversion Fair Value Gap) — Complete Implementation Analysis

```
 ╔══════════════════════════════════════════════════════════════════════════╗
 ║                                                                        ║
 ║   ██╗███████╗██╗   ██╗ ██████╗     ██████╗ ██████╗  ██████╗           ║
 ║   ██║██╔════╝██║   ██║██╔════╝     ██╔══██╗██╔══██╗██╔═══██╗          ║
 ║   ██║█████╗  ██║   ██║██║  ███╗    ██████╔╝██████╔╝██║   ██║          ║
 ║   ██║██╔══╝  ╚██╗ ██╔╝██║   ██║    ██╔═══╝ ██╔══██╗██║   ██║          ║
 ║   ██║██║      ╚████╔╝ ╚██████╔╝    ██║     ██║  ██║╚██████╔╝          ║
 ║   ╚═╝╚═╝      ╚═══╝   ╚═════╝     ╚═╝     ╚═╝  ╚═╝ ╚═════╝          ║
 ║                                                                        ║
 ║              Implementation Analysis & Best Practice Review            ║
 ║              Source: src/IFVG_Indicator.pine (Pine Script v6)          ║
 ╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Table of Contents

1. [The Big Picture](#1-the-big-picture)
2. [The IFVG Type — Every Field](#2-the-ifvg-type--every-field)
3. [How an IFVG is Born (Step-by-Step)](#3-how-an-ifvg-is-born)
4. [Post-Creation Lifecycle](#4-post-creation-lifecycle)
5. [Complete Parameter Reference](#5-complete-parameter-reference)
6. [Impact on the Whole Indicator](#6-impact-on-the-whole-indicator)
7. [Comparison with Best Practices](#7-comparison-with-best-practices)
8. [Liquidity System Analysis](#8-liquidity-system-analysis)
9. [Summary & Gaps](#9-summary--gaps)

---

## 1. The Big Picture

The IFVG is the **core output** of the entire indicator. Everything else (FVGs, swing
points, liquidity levels, HTF analysis) exists to serve it — either to create it, grade
it, or manage its lifecycle.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        IFVG LIFECYCLE PIPELINE                          │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  FVG Detection ──► Merge Check ──► Inversion Detection ──► Grading       │
│       │                                                        │         │
│       │    ┌───────────────────────────────────────────────────┘         │
│       │    │                                                             │
│       │    ▼                                                             │
│       │  IFVG Created                                                    │
│       │    │                                                             │
│       │    ├──► BE/SL Monitoring (every bar)                             │
│       │    ├──► DOL Refresh (every bar)                                  │
│       │    ├──► Rendering (with filters)                                 │
│       │    └──► Mitigation Check ──► Removal                             │
│       │                                                                  │
│  ┌────┴─────────────────────────────────────────────────────┐            │
│  │  SUPPORT SYSTEMS (all feed into IFVG creation/grading)   │            │
│  │                                                          │            │
│  │  Swing Detection ─────► BE Level, SL Level               │            │
│  │  Liquidity Levels ────► DOL Target, Sweep Detection      │            │
│  │  Candle Analysis ─────► Momentum Score                   │            │
│  │  HTF Analysis ────────► Bias Filter (display gate)       │            │
│  └──────────────────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. The IFVG Type — Every Field

Defined at `src/IFVG_Indicator.pine` lines 82-105.

```
┌────────────────────────────────────────────────────────────────────────┐
│                         IFVG TYPE DEFINITION                          │
├──────────────────┬─────────┬────────────────┬──────────────────────────┤
│ Field            │ Type    │ Source         │ Purpose                  │
├──────────────────┼─────────┼────────────────┼──────────────────────────┤
│ top              │ float   │ From FVG       │ Upper boundary of zone   │
│ bottom           │ float   │ From FVG       │ Lower boundary of zone   │
│ mid              │ float   │ From FVG       │ Midpoint (top+bottom)/2  │
│ start_bar        │ int     │ From FVG       │ Original FVG candle 1    │
│ inversion_bar    │ int     │ At creation    │ Bar where inversion hit  │
│ inversion_close  │ float   │ At creation    │ Close of inversion candle│
│                  │         │                │ (= ENTRY PRICE)          │
│ is_bullish       │ bool    │ INVERTED       │ Opposite of source FVG   │
│ status           │ string  │ Lifecycle      │ "inverted" or "mitigated"│
│ grade            │ string  │ Grading algo   │ A+, A, A-, B+, B, B-, C  │
│ entry_valid      │ bool    │ SL check       │ true if SL not hit yet   │
│ be_level         │ float   │ Swing lookup   │ First profit target      │
│ be_status        │ string  │ Price tracking │ "intact" or "taken"      │
│ sl_level         │ float   │ User config    │ FVG boundary or swing    │
│ sl_type          │ string  │ User config    │ "fvg_boundary" / "swing" │
│ dol              │Liquidity│ Liq search     │ Draw on Liquidity target │
│ has_sweep        │ bool    │ Liq check      │ Sweep in last 20 bars    │
│ momentum         │ string  │ Candle check   │ strong/neutral/weak      │
├──────────────────┼─────────┼────────────────┼──────────────────────────┤
│ box_id           │ box     │ Rendering      │ Gray IFVG zone box       │
│ label_id         │ label   │ Rendering      │ Tiny "IFVG" text         │
│ be_line_id       │ line    │ Rendering      │ White dashed BE line     │
│ sl_line_id       │ line    │ Rendering      │ Red solid SL line        │
│ entry_line_id    │ line    │ Rendering      │ Colored entry price line │
│ entry_label_id   │ label   │ Rendering      │ "A+ BUY" / "B- SELL"    │
└──────────────────┴─────────┴────────────────┴──────────────────────────┘
```

---

## 3. How an IFVG is Born

### Step 1: FVG Detection

**Location**: `detect_fvg()` at lines 526-564

The raw material. A 3-candle imbalance pattern:

```
  BULLISH FVG                        BEARISH FVG
  ═══════════                        ═══════════

     ┌──┐                               ┌──┐
     │  │ Candle 3 (current)            │  │ Candle 1 (bar[2])
     │  │                               │  │
     └──┘                               └──┘ ─── low[2]
       ─── low[0]                          :
       :                                   :  GAP (FVG Zone)
       :  GAP (FVG Zone)                   :
       :                               ┌──┐ ─── high[0]
     ┌──┐ ─── high[2]                  │  │
     │  │                               │  │ Candle 3 (current)
     │  │ Candle 1 (bar[2])            │  │
     └──┘                               └──┘

  top    = low[0]                     top    = low[2]
  bottom = high[2]                    bottom = high[0]
  gap    = low[0] - high[2]          gap    = low[2] - high[0]
```

**Detection rules**:
- Bullish: `low[0] > high[2]` — current candle's low above candle-2-ago's high
- Bearish: `high[0] < low[2]` — current candle's high below candle-2-ago's low
- Gap must exceed `ATR(14) * 0.25` (default) to filter micro-gaps
- Only on `barstate.isconfirmed` (no repainting)
- One FVG per bar max (bullish checked first — **hardcoded priority**)

### Step 2: Series-of-Gaps Merge

**Location**: `merge_with_existing_fvg()` at lines 491-517

Before a new FVG is stored, the system checks for merging with existing FVGs:

```
  BEFORE MERGE                        AFTER MERGE
  ════════════                        ═══════════

  ┌─────────┐                         ┌─────────────────────┐
  │ FVG #1  │                         │                     │
  │ top=110 │   ┌─────────┐          │   MERGED FVG        │
  │ bot=105 │   │ FVG #2  │   ──►    │   top  = max(110,112) = 112  │
  └─────────┘   │ top=112 │          │   bot  = min(105,107) = 105  │
                │ bot=107 │          │   bars = combined    │
                └─────────┘          └─────────────────────┘

  Criteria: same direction + active + within 5 bars
```

Per strategy: "combine series of gaps into one zone, wait for all to be inverted."

### Step 3: Inversion Detection

**Location**: `check_inversions()` at lines 1399-1547

The critical transformation where an FVG becomes an IFVG:

```
  BULLISH FVG INVERSION (becomes BEARISH IFVG)
  ═════════════════════════════════════════════

     Price action:
                 │
        ┌──┐     │
        │  │     │
        └──┘     │
     ───────── fvg.top ────────────
        :        │     :
        :  FVG   │     :  Now the IFVG zone
        :  Zone  │     :  (bearish - sell zone)
        :        │     :
     ───────── fvg.bottom ─────────
                 │   ┌──┐
                 │   │  │◄── Inversion candle:
                 │   │  │    close < fvg.bottom
                 │   └──┘

  Conditions (ALL must be true):
  1. Price entered zone (low <= top AND low >= bottom)
     OR price through zone (low < bottom)
  2. Body closes below: close < fvg.bottom
  3. FVG age >= 1 bar


  BEARISH FVG INVERSION (becomes BULLISH IFVG)
  ═════════════════════════════════════════════

                 │   ┌──┐
                 │   │  │◄── Inversion candle:
                 │   │  │    close > fvg.top
                 │   └──┘
     ───────── fvg.top ────────────
        :        │     :
        :  FVG   │     :  Now the IFVG zone
        :  Zone  │     :  (bullish - buy zone)
        :        │     :
     ───────── fvg.bottom ─────────
        ┌──┐     │
        │  │     │
        └──┘     │
                 │

  Conditions (ALL must be true):
  1. Price entered zone (high >= bottom AND high <= top)
     OR price through zone (high > top)
  2. Body closes above: close > fvg.top
  3. FVG age >= 1 bar
```

**Direction flip**: `ifvg_is_bullish = NOT fvg.is_bullish`

A bullish support zone that gets violated becomes bearish resistance (sell zone), and
vice versa. This is the fundamental IFVG concept.

### Step 4: Enrichment (6 Calculations at Inversion Time)

When inversion is confirmed, 6 calculations happen simultaneously on the inversion candle:

```
┌──────────────────────────────────────────────────────────────────┐
│              IFVG ENRICHMENT AT INVERSION TIME                   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4A. BE  │  find_previous_swing_high/low(fvg.start_bar)      │
│  │  Level   │  Bullish IFVG → swing HIGH to the left             │
│  │          │  Bearish IFVG → swing LOW to the left              │
│  │          │  Fallback: FVG boundary                            │
│  └──────────┘                                                    │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4B. SL  │  Mode 1 "FVG Boundary": fvg.bottom / fvg.top     │
│  │  Level   │  Mode 2 "Swing Stop": swing low/high to left      │
│  │          │  Configurable via i_sl_type                        │
│  └──────────┘                                                    │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4C.     │  Bullish: entry_valid = low > sl_level             │
│  │  Entry   │  Bearish: entry_valid = high < sl_level            │
│  │  Valid   │  (did inversion candle already hit SL?)            │
│  └──────────┘                                                    │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4D. DOL │  find_dol(ifvg_is_bullish, close)                 │
│  │  Target  │  Bullish → nearest EQH/ITH ABOVE price             │
│  │          │  Bearish → nearest EQL/ITL BELOW price              │
│  └──────────┘                                                    │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4E.     │  check_recent_sweep(not is_bullish, 20)           │
│  │  Sweep   │  Bullish IFVG → look for SSL sweep (lows taken)   │
│  │  Check   │  Bearish IFVG → look for BSL sweep (highs taken)  │
│  │          │  Window: 20 bars (hardcoded)                       │
│  └──────────┘                                                    │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  4F.     │  assess_momentum(open, high, low, close)          │
│  │ Momentum │  body_ratio = |close - open| / (high - low)       │
│  │          │  strong: ratio > 70% AND range > ATR               │
│  │          │  weak:   ratio < 30% OR  range < 0.5 ATR           │
│  │          │  neutral: everything else                          │
│  └──────────┘                                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Step 5: Grading Algorithm

**Location**: `calculate_grade()` at lines 1333-1393

```
┌──────────────────────────────────────────────────────────────────┐
│                     GRADING ALGORITHM                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  STEP 1: MANDATORY CRITERIA ──► DETERMINE TIER                   │
│  ─────────────────────────────────────────────                   │
│                                                                  │
│    No DOL? ────► "C" (forced, no further evaluation)             │
│    Has sweep? ─► "A" tier                                        │
│    No sweep? ──► "B" tier                                        │
│                                                                  │
│  STEP 2: QUALITY SCORE ──► DETERMINE MODIFIER                    │
│  ────────────────────────────────────────────                    │
│                                                                  │
│    Factor        │  +1               │  -1                       │
│    ──────────────┼───────────────────┼────────────────            │
│    Momentum      │ "strong_no_chop"  │ "weak_or_choppy"          │
│    FVG Clarity   │ singular          │ clustered                  │
│                                                                  │
│    Score range: -2 to +2  ("neutral" momentum = 0)               │
│                                                                  │
│  STEP 3: COMBINE TIER + SCORE                                    │
│  ────────────────────────────                                    │
│                                                                  │
│    ┌──────────┬──────────┬──────────┬──────────┬──────────┐      │
│    │          │ Score>=2 │ Score>=1 │ Score>=0 │ Score<0  │      │
│    ├──────────┼──────────┼──────────┼──────────┼──────────┤      │
│    │ Tier "A" │   A+     │    A     │    A-    │    B+    │      │
│    │ Tier "B" │    -     │   B+     │    B     │    B-    │      │
│    │ Tier "C" │    C     │    C     │    C     │    C     │      │
│    └──────────┴──────────┴──────────┴──────────┴──────────┘      │
│                                                                  │
│    Note: A-tier with score < 0 DEMOTES to B+                     │
│          B-tier cannot exceed B+                                  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Singularity check** (`is_fvg_singular()`, lines 1307-1328):
An FVG is non-singular if another same-direction, active FVG is BOTH:
- Within **5 bars** (proximity)
- Has **overlapping** price zones (with 0.1 ATR tolerance)

Both must be true to mark as clustered.

---

## 4. Post-Creation Lifecycle

```
┌──────────────────────────────────────────────────────────────────┐
│              IFVG POST-CREATION MONITORING                       │
│              (runs every confirmed bar)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─ update_be_status() ──────────────────────────────────┐       │
│  │                                                        │       │
│  │  BE tracking:                                          │       │
│  │    Bullish: high >= be_level ──► be_status = "taken"   │       │
│  │    Bearish: low  <= be_level ──► be_status = "taken"   │       │
│  │                                                        │       │
│  │  SL monitoring:                                        │       │
│  │    Bullish: low  < sl_level ──► entry_valid = false    │       │
│  │    Bearish: high > sl_level ──► entry_valid = false    │       │
│  └────────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ update_dol_status() ─────────────────────────────────┐       │
│  │                                                        │       │
│  │  If DOL swept or broken ──► find_dol() for new target  │       │
│  │  If DOL was na ───────────► try to find one now         │       │
│  │                                                        │       │
│  │  DOL can CHANGE over the IFVG's lifetime               │       │
│  └────────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ check_mitigations() ─────────────────────────────────┐       │
│  │                                                        │       │
│  │  Bullish: close < ifvg.bottom ──► MITIGATED            │       │
│  │  Bearish: close > ifvg.top    ──► MITIGATED            │       │
│  │                                                        │       │
│  │  On mitigation:                                        │       │
│  │    - Delete all 6 drawing objects                      │       │
│  │    - Remove from g_ifvg_array entirely                 │       │
│  └────────────────────────────────────────────────────────┘       │
│                                                                  │
│  ┌─ render_ifvg_boxes() ─────────────────────────────────┐       │
│  │                                                        │       │
│  │  Display gates (ALL must pass):                        │       │
│  │    1. i_show_ifvg == true                              │       │
│  │    2. Grade meets i_min_grade_display threshold         │       │
│  │    3. HTF bias aligned (if filter enabled)             │       │
│  │    4. displayed_count < i_max_recent_display           │       │
│  │                                                        │       │
│  │  Visual elements per IFVG:                             │       │
│  │    [1] Gray translucent box (zone)                     │       │
│  │    [2] Tiny "IFVG" label                               │       │
│  │    [3] Red SL line (solid)                             │       │
│  │    [4] White BE line (dashed/dotted if taken)          │       │
│  │    [5] Colored entry line at inversion close           │       │
│  │    [6] "A+ BUY" / "B- SELL" label with tooltip        │       │
│  └────────────────────────────────────────────────────────┘       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Tooltip Content (on entry label)

```
┌─────────────────────┐
│ Grade: A+            │
│ ─────────────        │
│ ☑ Sweep              │
│ ☑ Momentum: Strong   │
│ ☑ DOL: EQH @ 5234.50│
│ ─────────────        │
│ Entry: VALID         │
└─────────────────────┘
```

---

## 5. Complete Parameter Reference

### 5A. Configurable Parameters (User Inputs)

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     CONFIGURABLE PARAMETERS                            ║
╠════════════════════╦═════════╦═══════════════╦═════════════════════════╣
║ Parameter          ║ Default ║ Group         ║ Impact on IFVG          ║
╠════════════════════╬═════════╬═══════════════╬═════════════════════════╣
║ i_show_ifvg        ║ true    ║ FVG Detection ║ Master IFVG visibility  ║
║ i_max_fvgs         ║ 3       ║ General       ║ Source FVGs available   ║
║ i_max_ifvgs        ║ 10      ║ General       ║ Max IFVGs tracked (FIFO)║
║ i_max_recent_display║ 2      ║ General       ║ Max IFVGs on chart      ║
║ i_extend_bars      ║ 15      ║ General       ║ Right edge extension    ║
║ i_fvg_atr_period   ║ 14      ║ FVG Detection ║ ATR for all sizing      ║
║ i_fvg_min_size_mult║ 0.25    ║ FVG Detection ║ Min gap size            ║
║ i_min_grade_display║ "B-"    ║ Grading       ║ Grade filter threshold  ║
║ i_show_be_level    ║ true    ║ Grading       ║ BE line visibility      ║
║ i_show_sl_level    ║ true    ║ Grading       ║ SL line visibility      ║
║ i_sl_type          ║"FVG Bnd"║ Grading       ║ SL placement method     ║
║ i_show_grade_label ║ true    ║ Grading       ║ Grade text on label     ║
║ i_show_entry_line  ║ true    ║ IFVG Style    ║ Entry line + label      ║
║ i_ifvg_box_color   ║ gray    ║ IFVG Style    ║ Box fill color          ║
║ i_ifvg_box_opacity ║ 60      ║ IFVG Style    ║ Box transparency        ║
║ i_entry_color_bull ║ #2962FF ║ IFVG Style    ║ Bullish entry color     ║
║ i_entry_color_bear ║ #F23645 ║ IFVG Style    ║ Bearish entry color     ║
║ i_be_color         ║ white   ║ Visual        ║ BE line color           ║
║ i_sl_color         ║ red     ║ Visual        ║ SL line color           ║
║ i_enable_htf       ║ true    ║ HTF           ║ HTF bias filtering      ║
║ i_htf_filter_ltf   ║ true    ║ HTF           ║ Filter by HTF direction ║
╚════════════════════╩═════════╩═══════════════╩═════════════════════════╝
```

### 5B. Hardcoded Constants (Not Configurable)

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     HARDCODED CONSTANTS                                ║
╠════════════════════════════╦════════════╦═══════╦══════════════════════╣
║ Constant                   ║ Value      ║ Line  ║ Impact               ║
╠════════════════════════════╬════════════╬═══════╬══════════════════════╣
║ Min FVG age for inversion  ║ 1 bar      ║ 1409  ║ No same-bar invert   ║
║ Bullish FVG priority       ║ Always 1st ║ 550   ║ Bullish wins on tie  ║
║ Merge distance             ║ 5 bars     ║ 500   ║ Series-of-gaps merge ║
║ Direction inversion        ║ Always NOT ║ 1441  ║ Core IFVG concept    ║
║ Sweep lookback             ║ 20 bars    ║ 1510  ║ A vs B tier window   ║
║ Strong momentum body ratio ║ 70%        ║ 1278  ║ Body/range threshold ║
║ Weak momentum body ratio   ║ 30%        ║ 1281  ║ Body/range threshold ║
║ Strong momentum range      ║ 1.0 ATR    ║ 1278  ║ Min candle range     ║
║ Weak momentum range        ║ 0.5 ATR    ║ 1281  ║ Max for weak         ║
║ Singularity proximity      ║ 5 bars     ║ 1320  ║ Cluster detection    ║
║ Singularity overlap tol    ║ 0.1 ATR    ║ 1322  ║ Zone overlap check   ║
║ SL creation check          ║ exclusive  ║ 1500  ║ low > sl (not >=)    ║
║ SL ongoing check           ║ strict     ║ 1581  ║ low < sl (not <=)    ║
║ BE check                   ║ inclusive  ║ 1570  ║ high >= be           ║
║ IFVG box border            ║ invisible  ║ 1773  ║ width=0, transparent ║
║ IFVG label text            ║ "IFVG"     ║ 1783  ║ Always "IFVG"        ║
║ Entry label format         ║ "GRD DIR"  ║ 1877  ║ e.g. "A+ BUY"       ║
║ Swing array cap            ║ 50         ║ 806   ║ Max swing history    ║
╚════════════════════════════╩════════════╩═══════╩══════════════════════╝
```

---

## 6. Impact on the Whole Indicator

```
╔══════════════════════════════════════════════════════════════════════════╗
║               HOW EVERY SUBSYSTEM FEEDS THE IFVG                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║                  ┌──── Swing Points ──────► BE Level                   ║
║                  │                    ──────► SL Level (Swing Stop)     ║
║                  │                                                     ║
║                  ├──── Liquidity ─────────► DOL Target                 ║
║                  │    (ITH/ITL/EQH/EQL)──► Sweep Detection             ║
║                  │                    ──────► Grade Tier (A/B/C)        ║
║                  │                                                     ║
║  FVG Detection ──┤                                                     ║
║                  ├──── Candle Analysis ───► Momentum Score              ║
║                  │                    ──────► Grade Modifier (+1/-1)    ║
║                  │                                                     ║
║                  ├──── FVG Array ─────────► Singularity Check          ║
║                  │                    ──────► Grade Modifier (+1/-1)    ║
║                  │                                                     ║
║                  └──── HTF IFVGs ─────────► Bias Filter                ║
║                                       ──────► Display Gate             ║
║                           │                                            ║
║                           ▼                                            ║
║                      IFVG Created                                      ║
║                           │                                            ║
║                           ├──► Dashboard (latest setup info)           ║
║                           ├──► Entry Label ("A+ BUY" tooltip)          ║
║                           └──► Alerts (Phase 4 - not yet)              ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

Without IFVGs, the indicator produces FVG boxes and liquidity lines but **no actionable
trade setups**. The IFVG is where all signals converge into a graded, entry-ready
recommendation.

---

## 7. Comparison with Best Practices

### 7A. FVG Detection

```
┌──────────────────┬─────────────────────────┬────────────────────┬────────────┐
│ Aspect           │ Our Implementation      │ ICT Best Practice  │ Assessment │
├──────────────────┼─────────────────────────┼────────────────────┼────────────┤
│ 3-candle pattern │ low[0]>high[2] (bull)   │ Standard ICT       │ CORRECT    │
│                  │ high[0]<low[2] (bear)   │ definition         │            │
│ Data source      │ Wicks (high/low)        │ Wicks for FVG      │ CORRECT    │
│ Size filter      │ ATR-based minimum       │ Many don't filter  │ BETTER     │
│ Confirmed bars   │ barstate.isconfirmed    │ Required, no       │ CORRECT    │
│                  │                         │ repainting         │            │
│ Per-bar limit    │ 1 FVG (bullish first)   │ Not standardized   │ OK         │
└──────────────────┴─────────────────────────┴────────────────────┴────────────┘
```

### 7B. Inversion Detection

```
┌──────────────────┬─────────────────────────┬────────────────────┬────────────┐
│ Aspect           │ Our Implementation      │ ICT Best Practice  │ Assessment │
├──────────────────┼─────────────────────────┼────────────────────┼────────────┤
│ Inversion trigger│ Body close through zone │ Body close through │ CORRECT    │
│                  │ boundary                │ the FVG zone       │            │
│ Zone entry check │ Wick touched OR price   │ Some require zone  │ SLIGHTLY   │
│                  │ gapped through          │ interaction only   │ PERMISSIVE │
│ Body close req.  │ Close must breach       │ Standard ICT       │ CORRECT    │
│                  │ opposite boundary       │ inversion signal   │            │
│ Direction flip   │ Always inverts          │ Core IFVG concept  │ CORRECT    │
│ Min age          │ 1 bar                   │ At least next bar  │ CORRECT    │
│ Partial inversion│ Not supported           │ Some track "tapped"│ MINOR GAP  │
└──────────────────┴─────────────────────────┴────────────────────┴────────────┘
```

**Key finding**: The `price_through_zone` check (lines 1415, 1424) allows a candle that
completely gaps past the FVG zone — never entering it — to count as inversion. In strict
ICT methodology, the zone should be "respected" (price trades within it) before inversion.

```
  POTENTIAL FALSE INVERSION SCENARIO
  ════════════════════════════════════

     Bullish FVG at 100-105:

                    │
     ─────────── 105 ── fvg.top ─────
        :           │          :
        :  FVG Zone │          :
        :           │          :
     ─────────── 100 ── fvg.bottom ──
                    │
                    │  Gap down!
                    │
               ┌────┤
               │    │ low=95 (price_through_zone = true)
               │    │ close=96 (body_closes_below = true)
               └────┘

  Result: Counts as inversion, but price NEVER TRADED INSIDE the zone.
  In strict ICT: This should NOT be an inversion — zone wasn't "respected."
```

### 7C. Grading System

```
┌──────────────────┬─────────────────────────┬────────────────────┬────────────┐
│ Aspect           │ Our Implementation      │ ICT Best Practice  │ Assessment │
├──────────────────┼─────────────────────────┼────────────────────┼────────────┤
│ Sweep as top tier│ Sweep = A, No = B       │ #1 confluence in   │ CORRECT    │
│                  │                         │ ICT methodology    │            │
│ DOL mandatory    │ No DOL = forced C       │ Setup without      │ CORRECT    │
│                  │                         │ target is low-qual │            │
│ Momentum         │ Single inversion candle │ ICT "displacement" │ BASIC      │
│                  │ body ratio + range      │ is multi-candle    │ (adequate) │
│ PD Zone position │ NOT IMPLEMENTED         │ Longs in discount  │ MISSING    │
│                  │ (Phase 4 planned)       │ Shorts in premium  │ (critical) │
│ Session timing   │ NOT IMPLEMENTED         │ Kill zones (LO,NY) │ MISSING    │
│                  │ (Phase 4 planned)       │ improve probability│ (planned)  │
│ FVG clarity      │ Singular vs clustered   │ DodgysDD-specific  │ GOOD       │
│                  │ +1/-1 modifier          │ "clean" vs "messy" │ (custom)   │
│ Entry validity   │ SL check on inv. candle │ Standard practice  │ CORRECT    │
└──────────────────┴─────────────────────────┴────────────────────┴────────────┘
```

### 7D. BE/SL Placement

```
┌──────────────────┬─────────────────────────┬────────────────────┬────────────┐
│ Aspect           │ Our Implementation      │ Best Practice      │ Assessment │
├──────────────────┼─────────────────────────┼────────────────────┼────────────┤
│ BE level         │ First swing in trade    │ First structural   │ CORRECT    │
│                  │ direction, LEFT of FVG  │ target             │            │
│ SL at FVG bound. │ Bottom (bull) / Top     │ Zone boundary =    │ CORRECT    │
│                  │ (bear)                  │ invalidation point │            │
│ SL at swing stop │ Swing before FVG in     │ More conservative, │ CORRECT    │
│                  │ opposite direction      │ gives more room    │ alternative│
│ Mitigation       │ Body close through zone │ Same as inversion  │ CORRECT    │
│                  │                         │ logic              │            │
│ Partial mitigat. │ Not tracked             │ 50% retracement    │ MINOR GAP  │
│                  │                         │ as entry signal    │            │
└──────────────────┴─────────────────────────┴────────────────────┴────────────┘
```

### 7E. SL Check Asymmetry (Edge Case)

```
  AT CREATION (line 1500):     entry_valid = low > sl_level   (exclusive)
  DURING TRACKING (line 1581): if low < sl_level              (strict)

  Scenario:
  - sl_level = 100.00
  - Inversion candle: low = 100.00

  At creation:  100.00 > 100.00  = FALSE  ──► entry_valid = false
  WAIT: actually 100 > 100 = false, so the entry IS correctly invalid.

  But if low = 100.01:
  At creation:  100.01 > 100.00  = TRUE   ──► entry_valid = true
  Next bar:     if low = 100.00 → 100.00 < 100.00 = FALSE → still valid

  The asymmetry is: at creation, exact touch = INVALID.
  During tracking, exact touch = still VALID (needs to breach).
```

---

## 8. Liquidity System Analysis

The liquidity system provides critical inputs to IFVG grading. Here is how it works:

### 8A. Swing Detection

```
  SWING HIGH DETECTION (lookback = 5 default)
  ════════════════════════════════════════════

  Check: high[5] must be STRICTLY GREATER than all highs
  within bars [lookback-j] to [lookback+j] for j = 1 to 5

       high[5] is the HIGHEST point
            ▼
  ──┐   ┌──●──┐   ┌──
    │   │     │   │
    │   │     │   │
    └───┘     └───┘
    ◄─── 5 bars ──►◄─── 5 bars ──►
     (left check)    (right check)

  - Uses WICKS (high/low), not bodies
  - Detection at [lookback] offset = built-in delay of 5 bars
  - Equal-height candles DISQUALIFY (strict >)
  - Swing arrays capped at 50 entries (FIFO)
```

### 8B. Liquidity Types

```
╔══════════╦════════════════════════════════════════════════════════════╗
║ Type     ║ Description                                              ║
╠══════════╬════════════════════════════════════════════════════════════╣
║ ITH      ║ Internal High — most recent swing high, auto-created     ║
║ ITL      ║ Internal Low  — most recent swing low, auto-created      ║
║ EQH      ║ Equal Highs   — two swing highs at similar price         ║
║ EQL      ║ Equal Lows    — two swing lows at similar price          ║
╠══════════╬════════════════════════════════════════════════════════════╣
║          ║ All share g_liquidity_array (max 4 entries by default!)  ║
║          ║ ITH/ITL can crowd out EQH/EQL due to FIFO cleanup       ║
╚══════════╩════════════════════════════════════════════════════════════╝
```

### 8C. EQH/EQL Detection Rules

```
  RULE 1: Both swings must be intact (close never breached them)
  RULE 2: Formation direction:
          EQH: new high <= old high (resistance holding)
          EQL: new low  >= old low  (support holding)
  RULE 3: Price diff within tolerance (ATR * i_relative_tolerance)
  RULE 4: No wick sweep between the two swings

  Quality tiers:
    Perfect:  diff <= ATR * 0.02  (★ on chart)
    Relative: diff <= ATR * 0.10  (R. prefix on chart)
```

### 8D. Sweep Detection

```
  BSL SWEEP (Buy-Side Liquidity)         SSL SWEEP (Sell-Side Liquidity)
  ══════════════════════════════         ════════════════════════════════

  Applies to: EQH, ITH                  Applies to: EQL, ITL

  ─────── level ───────────              ─────── level ───────────
              ┌──┐                                    │
              │  │◄── wick above                      │
              │  │    close below                ┌──┤
              └──┘                               │  │◄── wick below
                                                 │  │    close above
                                                 └──┘

  high > level AND close < level         low < level AND close > level

  vs COMPLETE BREAK:
  close > level (for highs) ──► is_valid = false (not a sweep)
  close < level (for lows)  ──► is_valid = false (not a sweep)
```

### 8E. Liquidity Parameters

```
╔══════════════════════════╦═════════╦══════════════════════════════════════╗
║ Parameter                ║ Default ║ Impact                               ║
╠══════════════════════════╬═════════╬══════════════════════════════════════╣
║ i_swing_lookback         ║ 5       ║ Left/right bars for pivot detection  ║
║ i_max_liquidity          ║ 4       ║ Max entries in shared array (LOW!)   ║
║ i_show_ith_itl           ║ true    ║ ITH/ITL visibility (data collected)  ║
║ i_show_eqh_eql           ║ true    ║ EQH/EQL visibility (data collected)  ║
║ i_perfect_tolerance      ║ 0.02    ║ ATR mult for "perfect" quality       ║
║ i_relative_tolerance     ║ 0.10    ║ ATR mult for "relative" quality      ║
║ i_require_intact         ║ true    ║ Swings must not be broken through    ║
║ i_show_perfect_only      ║ false   ║ Filter rendering only                ║
║ i_show_swept_eqhl        ║ false   ║ Show mitigated EQH/EQL              ║
╠══════════════════════════╬═════════╬══════════════════════════════════════╣
║ Swing array cap          ║ 50      ║ HARDCODED - max swing history        ║
║ EQH/EQL lookback depth   ║ 10      ║ HARDCODED - compare 10 prev swings  ║
║ Intact check limit       ║ 500 bars║ HARDCODED - max history scan         ║
║ Sweep lookback (grading) ║ 20 bars ║ HARDCODED - doesn't scale with TF   ║
╚══════════════════════════╩═════════╩══════════════════════════════════════╝
```

---

## 9. Summary & Gaps

### What Works Well

```
  ✔ Correct ICT inversion definition (body close through zone)
  ✔ Direction inversion logic (bullish FVG → bearish IFVG)
  ✔ Series-of-gaps merging per DodgysDD strategy rules
  ✔ Grading tiers with sweep as primary differentiator
  ✔ DOL as mandatory criterion for meaningful grades
  ✔ Live BE/SL tracking with ongoing validation
  ✔ DOL refresh when targets get swept
  ✔ ATR-based sizing for market-agnostic behavior
  ✔ Comprehensive tooltip with full grade breakdown
  ✔ Swept-between validation for EQH/EQL (Rule 4)
  ✔ Separation of data collection from rendering
```

### What Could Be Improved

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │  PRIORITY   │ ISSUE                         │ STATUS                  │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  HIGH       │ PD Zone positioning missing   │ Phase 4 planned         │
  │             │ from grading                  │                         │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  HIGH       │ Session/kill zone awareness   │ Phase 4 planned         │
  │             │ missing from grading          │                         │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  MEDIUM     │ Gap-through inversion:        │ Consider requiring      │
  │             │ price_through_zone allows      │ price_entered_zone only │
  │             │ gap-past without zone entry   │                         │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  MEDIUM     │ Momentum is single-candle     │ Extend to multi-candle  │
  │             │ only (inversion candle)       │ displacement assessment │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  MEDIUM     │ Sweep lookback 20 bars        │ Make configurable or    │
  │             │ doesn't scale with TF         │ ATR-adaptive            │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  LOW        │ i_max_liquidity=4 too low     │ ITH/ITL can crowd out   │
  │             │ for shared array              │ EQH/EQL                 │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  LOW        │ No partial mitigation         │ Zone retest / 50%       │
  │             │ tracking                      │ retracement not tracked │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  LOW        │ calculate_stop_loss() at      │ Dead code — SL is       │
  │             │ lines 1289-1300 is dead code  │ calculated inline       │
  ├─────────────┼───────────────────────────────┼─────────────────────────┤
  │  LOW        │ is_internal field on          │ Always false — internal │
  │             │ SwingPoint is unused          │ vs external not tracked │
  └─────────────┴───────────────────────────────┴─────────────────────────┘
```

### Main Loop Execution Order (Section 12, lines 2246-2358)

```
  ┌─ Step 1: detect_swing_points()
  ├─ Step 2: check_equal_highs() + check_equal_lows() + create_internal_levels()
  │          + cleanup_liquidity_array()
  ├─ Step 3: check_liquidity_sweeps()
  ├─ Step 4: detect_fvg() + merge_with_existing_fvg() + cleanup
  ├─ Step 4B: detect_htf_fvg() (Phase 3)
  ├─ Step 5: check_inversions() ◄── THIS IS WHERE IFVGs ARE BORN
  │          + cleanup_ifvg_array()
  ├─ Step 5B: check_htf_inversions() (Phase 3)
  ├─ Step 5C: check_htf_mitigations() (Phase 3)
  ├─ Step 6: update_be_status()
  ├─ Step 6.5: update_dol_status()
  ├─ Step 7: check_mitigations()
  ├─ Step 8: find_most_recent_ifvg() (for dashboard)
  ├─ Step 9: render_fvg_boxes() + render_ifvg_boxes()
  ├─ Step 9B: render_htf_fvg_boxes() + render_htf_ifvg_boxes() (Phase 3)
  └─ Step 10: render_liquidity_lines() + render_dashboard()
```

---

*Analysis generated from src/IFVG_Indicator.pine (2359 lines, Pine Script v6)*
*Compared against ICT/SMC methodology and DodgysDD strategy rules*
