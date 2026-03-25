# Phase 2: PD Zone Detection & Grading Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-25
**Phase:** 02-pd-zone-detection-grading-integration
**Areas discussed:** HTF Swing Source, OTE Zone (62-79%), Grade Recalibration, Visual Density

---

## HTF Swing Source

| Option | Description | Selected |
|--------|-------------|----------|
| Dedicated PD timeframe | Separate input (i_pd_timeframe, default Daily). Costs 2 extra request.security() calls (4 of 40 total). Independent control. | ✓ |
| Reuse HTF1 timeframe | PD zones always use HTF1. Saves 2 calls but couples TFs. | |
| Hybrid: default to HTF1 with override | Defaults to HTF1 but adds optional override input. | |

**User's choice:** Dedicated PD timeframe
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Daily | Standard ICT dealing range. Works across all chart timeframes. | ✓ |
| 4H | Tighter dealing range, updates more frequently. | |
| Weekly | Wider dealing range for swing traders. | |

**User's choice:** Daily (default TF)
**Notes:** None

---

## OTE Zone (62-79%)

| Option | Description | Selected |
|--------|-------------|----------|
| Two dashed lines + optional fill | Show 62% and 79% as dashed lines with subtle fill between (separate toggle). | ✓ |
| Shaded zone only (no lines) | Just colored background fill, no boundary lines. | |
| Label only (no visual zone) | No lines or fill, just annotate IFVG when in OTE. | |

**User's choice:** Two dashed lines + optional fill
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| No extra modifier | OTE is visual only. +1/-1 from premium/discount is enough. | ✓ |
| Extra +1 bonus in OTE | Additional +1 for setups in 62-79%. | |

**User's choice:** No extra modifier
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Off by default | Traders toggle on if wanted. Cleaner initial chart. | ✓ |
| On by default | Visible immediately when PD zones enabled. | |

**User's choice:** Off by default
**Notes:** "Off by default but even if it is visually turned off it will still be counted in the setup grading." — Clarification: OTE visual toggle is independent from PD zone grading modifier. The +1/-1 premium/discount modifier always applies when PD zones are enabled, regardless of OTE visual state.

---

## Grade Recalibration

| Option | Description | Selected |
|--------|-------------|----------|
| Keep current thresholds | Same thresholds as Phase 1. PD modifier naturally differentiates. | |
| Shift thresholds up by 1 | Compensate for expanded range. Harder to reach top grades. | |
| Visual verification first | Keep as-is, verify on charts, adjust later if >40% cluster. | ✓ |

**User's choice:** Visual verification first
**Notes:** Pragmatic approach — avoid premature optimization of grade thresholds.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Separate toggle | i_pd_grade_modifier input (default: true). Zones visible without grade impact. | ✓ |
| Always active | If PD zones enabled, grading always affected. | |

**User's choice:** Separate toggle
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Grade label tooltip | Add pd_zone to existing IFVG label (e.g., "A+ Bull IFVG [DISCOUNT]"). | ✓ |
| Dashboard only | Show in dashboard, IFVG labels unchanged. | |
| Both label and dashboard | Zone info in both places. | |

**User's choice:** Grade label tooltip
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Frozen at inversion | pd_zone set when FVG inverts, never changes. Consistent with grade freezing. | ✓ |
| Dynamic (updates live) | pd_zone recalculates each bar. | |

**User's choice:** Frozen at inversion
**Notes:** None

---

## Visual Density

| Option | Description | Selected |
|--------|-------------|----------|
| Full chart width | Lines span left to right edge. Structural reference always visible. | ✓ |
| From swing bar to right edge | Lines start at swing detection bar. | |
| Recent N bars + right extension | Lines cover ~100 bars plus extension. | |

**User's choice:** Full chart width
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Off by default | Fills are opt-in. Lines + labels show structure. | ✓ |
| On by default | Immediate visual context. More educational. | |

**User's choice:** Zone fills off by default
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Right-edge price labels | "Swing H (100%)", "EQ (50%)", "Swing L (0%)". Clean. | ✓ |
| Price + zone name | Show actual price levels: "5598 Swing H". | |
| You decide | Claude picks best format. | |

**User's choice:** Right-edge price labels
**Notes:** None

---

## Claude's Discretion

- OTE zone colors and opacity
- Exact line widths for zone lines
- Pivot lookback default value
- Dashboard row styling details
- Edge case handling (no swings, invalid range)

## Deferred Ideas

None — discussion stayed within phase scope
