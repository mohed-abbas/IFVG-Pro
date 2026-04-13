# Phase 2: PD Zone Detection & Grading Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-14
**Phase:** 02-pd-zone-detection-grading-integration
**Areas discussed:** Detection approach, Range update + timeframe, Visualization, Dashboard + grading calibration

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Detection approach | HOW to identify the dealing range H/L | ✓ |
| Range update + timeframe | WHEN range refreshes, default HTF, young-chart handling | ✓ |
| Visualization — lines/labels/OTE | Line style, label format, extension, OTE default | ✓ |
| Dashboard + grading calibration | DSH-01/02 display, PDZ-07 threshold action | ✓ |

**User's choice:** all four areas selected.

---

## Detection Approach

### Initial question — how to identify the dealing range

| Option | Description | Selected |
|--------|-------------|----------|
| HTF swings via request.security + alternation rule | Existing manual-pivot logic on HTF series with alternation enforced | |
| Reuse existing LTF swing arrays + larger lookback | Separate structural lookback, no request.security | |
| Last swept-then-reclaimed structure | Use liquidity arrays, most recent unswept pair | |
| Let's talk through it | Walk through tradeoffs | |

**User's choice (free-text):** "I want you use the selected HTF's ITH and ITL as the High and low for the Premium and discount area."
**Notes:** User introduced a fourth approach not in the original option set — reuse HTF's internal trend highs/lows (ITH/ITL) as the range boundaries. This is a clean fit because ITH/ITL already exist as first-class liquidity objects in the codebase.

### Follow-up — ITH/ITL pick rule

| Option | Description | Selected |
|--------|-------------|----------|
| A: Most recent unswept by bar_idx | Newest valid unswept ITH (top) and ITL (bottom); range rotates on new pivot or sweep | ✓ |
| C: Most recent + alternation enforced | Same as A but enforce H/L alternation in time | |
| B: Highest unswept ITH + lowest unswept ITL | Widest intact structure; more stable | |

**User's choice:** A: Most recent unswept by bar_idx.

---

## Range Update + Timeframe

### Timeframe + fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Daily default, configurable, auto-fallback when chart TF >= PD TF | Default D; on HTF chart, use chart-TF ITH/ITL | ✓ |
| Daily default, disable when chart TF >= PD TF | Same defaults, but hide feature on HTF charts | |
| 4H default instead of Daily | More active zone rotation intraday | |

**User's choice:** Daily default, configurable, auto-fallback.

### Empty state

| Option | Description | Selected |
|--------|-------------|----------|
| `pd_zone = "neutral"` until pair forms; no lines drawn | Graceful no-op | ✓ |
| Use fallback (highest/lowest of visible range) until ITH/ITL forms | Provisional range from chart extremes | |

**User's choice:** `pd_zone = "neutral"`, no lines.

**Range update trigger resolution:** Self-resolving under pick rule A — existing `is_swept`/`is_valid` liquidity machinery handles rotation automatically. No explicit question needed.

---

## Visualization

### Lines and fills

| Option | Description | Selected |
|--------|-------------|----------|
| 3 dashed lines (H/EQ/L), fills off by default | Clean reference-image look | ✓ |
| 3 dashed lines + zone fills ON by default | Faster visual read | |
| 5 lines (H/OTE-hi/EQ/OTE-lo/L), fills off | OTE lines inline | |

**User's choice:** 3 dashed lines, fills off by default.

### Label format

| Option | Description | Selected |
|--------|-------------|----------|
| Price + % at right edge: `1 (24,764.25)` style | Matches reference indicator exactly | ✓ |
| Price only, right edge | Cleaner, drops 0/0.5/1 reference | |
| Percentage only, right edge | Loses price context | |

**User's choice:** Price + % at right edge.

### Line extension

| Option | Description | Selected |
|--------|-------------|----------|
| Extend from swing bar to right edge + small buffer | Typical ICT visualization | ✓ |
| Bounded: swing bar to current bar only | Cleaner but no forward reference | |

**User's choice:** Extend to right edge + buffer.

### OTE zone default

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle, OFF by default | Secondary feature, opt-in | ✓ |
| Toggle, ON by default | Visible by default | |
| Not in this phase — defer | Ship H/EQ/L only | |

**User's choice:** Toggle, OFF by default.

---

## Dashboard + Grading Calibration

### PD Zone row (DSH-01)

| Option | Description | Selected |
|--------|-------------|----------|
| PREMIUM/DISCOUNT/EQ/— with color coding | Full state display | ✓ |
| PREMIUM/DISCOUNT only, no EQ state | Simpler | |

**User's choice:** Full color-coded state display.

### Range % row (DSH-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Integer %, `—` when no range | Clean compact display | ✓ |
| One decimal (e.g., `62.3%`) | More precise | |
| % + directional hint (e.g., `62% ↑`) | Includes trend arrow | |

**User's choice:** Integer %.

### Equilibrium threshold

| Option | Description | Selected |
|--------|-------------|----------|
| Strict: EQ only at exactly 50% | Simplest grading boundary | ✓ |
| Band: 45–55% = equilibrium | Wider EQ, rarer A+ | |
| Band: 48–52% = equilibrium | Tighter band | |

**User's choice:** Strict 50% exact.

### Grade calibration (PDZ-07)

| Option | Description | Selected |
|--------|-------------|----------|
| Ship as-is, measure, recalibrate only if needed | Avoid premature tuning | ✓ |
| Pre-emptively tighten thresholds | Raise A+ to total>=10 | |
| Add calibration as separate sub-phase | Explicit deferred tuning phase | |

**User's choice:** Ship as-is, measure first.

---

## Wrap-up

| Option | Description | Selected |
|--------|-------------|----------|
| I'm ready for context | Write CONTEXT.md | ✓ |
| Explore more gray areas | Surface additional concerns | |

**User's choice:** Ready for context.

---

## Claude's Discretion

- Exact `request.security` mechanism for fetching HTF ITH/ITL (tuple vs. multiple calls vs. rebuilding ITH/ITL on chart from HTF pivots).
- Input group placement and naming specifics (reference draft in `PHASE4_PD_ZONES_PLAN.md` is non-binding).
- Label `bar_idx` offset from current bar, line width defaults.
- Whether to add a lightweight `DealingRange` type vs. storing range snapshot in `var` globals.

## Deferred Ideas

- Directional hint on Range % (e.g., `62% ↑`) — v2 consideration.
- Equilibrium band (45–55%) — revisit only if PDZ-07 measurement reveals need.
- OTE as grading input — currently visual only.
- Zone fills on by default — kept off for chart clarity.
- Amend REQUIREMENTS.md PDZ-01 wording after Phase 2 verification (current text prescribes the failed `ta.pivothigh` approach).
- **Three prior failed approaches** preserved in CONTEXT.md deferred section to prevent retry.
