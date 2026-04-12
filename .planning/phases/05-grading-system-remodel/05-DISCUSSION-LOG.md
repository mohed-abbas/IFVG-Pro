# Phase 5: Grading System Remodel - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-12
**Phase:** 05-grading-system-remodel
**Areas discussed:** Delivery from FVG, Algorithm structure, Momentum levels, PD zone role

---

## Delivery from FVG

### Detection Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Prior FVG respect check | Look for active opposite-direction FVG within lookback. Check bodies respected it before displacement. | ✓ |
| FVG-to-FVG chain detection | Track whether displacement leg originated from another FVG zone boundary. | |
| Simplified: any recent FVG in path | Check if any active FVG exists between sweep point and IFVG. | |

**User's choice:** Prior FVG respect check
**Notes:** Most faithful reading of the PDF's "delivery from another FVG where bodies respect it absolutely perfectly."

### A+ Hard Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Hard requirement | A+ requires BOTH sweep AND delivery. Without delivery, best is A. | ✓ |
| Strong signal with override | Delivery is +2 quality score. Can still reach A+ without it. | |

**User's choice:** Hard requirement
**Notes:** Exactly matches the PDF specification.

### Lookback Window

| Option | Description | Selected |
|--------|-------------|----------|
| Same as sweep lookback | Use existing i_sweep_lookback input (default 20 bars). | ✓ |
| Separate configurable input | New i_delivery_lookback (default 30 bars). | |
| ATR-adaptive | Scale lookback based on ATR/timeframe. | |

**User's choice:** Same as sweep lookback
**Notes:** Keeps it consistent — delivery and sweep share the same temporal window.

### Body Respect Definition

| Option | Description | Selected |
|--------|-------------|----------|
| No body close through | No candle body closes through the source FVG zone. Wicks OK. | ✓ |
| Majority respect (80%+) | At least 80% of candles have bodies respecting. | |
| At least one clean bounce | Price must touch/enter and bounce with clean body rejection. | |

**User's choice:** No body close through
**Notes:** Strict — matches the PDF's "absolutely perfectly."

---

## Algorithm Structure

### Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Checklist scoring | 5 criteria each scored 0-2, total 0-10, mapped to grades. | ✓ |
| Adapted tier+modifier | Keep 2-step but fix tier logic with sweep+delivery. | |
| Profile matching | Define each grade as conditions, check A+ down to C. | |

**User's choice:** Checklist scoring
**Notes:** Holistic approach matching the PDF where all 5 criteria matter equally.

### A+ Gate Logic

| Option | Description | Selected |
|--------|-------------|----------|
| Hard gate + score | A+ requires sweep+delivery=2 AND total ≥ 9. | ✓ |
| Pure score only | Just use total score, no hard gates. | |

**User's choice:** Hard gate + score

### Threshold Configuration

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded | Lock thresholds based on PDF spec. | ✓ |
| Configurable | Add inputs for threshold boundaries. | |

**User's choice:** Hardcoded

---

## Momentum Levels

| Option | Description | Selected |
|--------|-------------|----------|
| 3-tier mapping | Score 2 = strong+displacement, Score 1 = either/or, Score 0 = weak/choppy. | ✓ |
| 4-tier with half points | 0, 0.5, 1, 1.5, 2 for all 5 PDF levels. | |
| Keep current 3 levels | Map existing string outputs to 0-2. | |

**User's choice:** 3-tier mapping
**Notes:** Score 2 requires BOTH strong inversion AND strong displacement. Score 1 = either/or.

---

## PD Zone Role

### Scoring

| Option | Description | Selected |
|--------|-------------|----------|
| Correct=2, neutral=1, wrong=0 | Full 3-tier scoring matching PDF grade descriptions. | ✓ |
| Binary: correct=2, else=0 | Only correct zone gets points. | |
| Keep as modifier (+1/0/-1) | Don't change weight. | |

**User's choice:** Correct=2, neutral=1, wrong=0

### A+ Zone Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Hard gate | A+ requires correct PD zone as additional hard gate. | ✓ |
| Score only | PD zone contributes to total but not a hard gate. | |

**User's choice:** Hard gate
**Notes:** A+ now has 3 hard gates: sweep+delivery, correct PD zone, total ≥ 9.

---

## Delivery Timeframe Source (Update Session)

### Which timeframe FVGs to search for delivery

| Option | Description | Selected |
|--------|-------------|----------|
| HTF FVGs only | Search only HTF arrays. LTF FVGs are noise. | |
| Both HTF and LTF | HTF first, fall back to LTF. Both count equally. | ✓ |
| Same timeframe as IFVG | Match the IFVG's own timeframe. | |
| Configurable | Add input for delivery TF source. | |

**User's choice:** Both HTF and LTF with priority cascade
**Notes:** First check HTF FVGs (from configured i_htf_timeframe/i_htf2_timeframe), fall back to LTF if no HTF delivery found. If current TF = configured HTF, just use current TF. Uses existing HTF parameters — no new inputs.

### Scoring weight by timeframe

| Option | Description | Selected |
|--------|-------------|----------|
| Equal once detected | Delivery is delivery regardless of source TF. | ✓ |
| HTF scores higher | HTF delivery = full score, LTF = partial. | |

**User's choice:** Equal once detected
**Notes:** Priority cascade determines search order, not scoring weight.

---

## Claude's Discretion

- Target clarity scoring thresholds
- FVG singularity 0-2 mapping details
- Delivery detection function implementation
- Whether momentum returns numeric or string
- HTF IFVG handling in new grading

## Deferred Ideas

- SMT divergence as bonus grading factor (requires correlated symbol data)
- LRLR trendline liquidity as DOL target type
- Data Highs/Data Lows as DOL targets (depends on Session Tracking phase)
