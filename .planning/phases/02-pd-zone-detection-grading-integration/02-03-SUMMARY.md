---
phase: 02-pd-zone-detection-grading-integration
plan: 03
subsystem: dashboard
tags: [dashboard, pd-zones, ui]
wave: 2
requirements: [PDZ-03, DSH-01, DSH-02]
dependency_graph:
  requires:
    - "02-01 (DealingRange type, g_current_range, compute_range_percent)"
  provides:
    - "Dashboard visibility of current PD zone and range position"
  affects:
    - "Section 11 render_dashboard()"
tech_stack:
  added: []
  patterns:
    - "Reused existing table.cell layout convention (col 0 label left, col 1 value right, size.small)"
    - "Semantic color mapping (red=suboptimal-for-longs, green=optimal-for-longs, yellow=EQ)"
key_files:
  created: []
  modified:
    - src/IFVG_Indicator.pine
decisions:
  - "Appended rows 10 and 11 (no mid-layout reshuffle; Phase 3 DSH-04 may re-layout)"
  - "Clamp Range % to 0..100 defensively — close can briefly poke beyond ITH/ITL bounds before sweep machinery invalidates range"
  - "Used close as current_mid for both zone lookup and Range %; stays consistent with compute_range_percent caller"
  - "Expanded table.new rows parameter from 10 to 12 (required for fixed-row tables)"
metrics:
  completed: 2026-04-14
  duration: ~3min
  tasks: 1
  files: 1
---

# Phase 2 Plan 3: Dashboard PD Zone + Range % Rows Summary

Adds two new rows to the IFVG Pro dashboard that surface current dealing-range state: a colored PD Zone label (PREMIUM/DISCOUNT/EQ) and an integer Range % percentage, both gated on `g_current_range.is_valid` with a unified `—` fallback for young-chart states.

## What Was Built

- Row 10 — `PD Zone:` label + `PREMIUM`/`DISCOUNT`/`EQ`/`—` value with semantic colors (red/green/yellow/gray).
- Row 11 — `Range %:` label + `NN%` integer value (white) or `—` (gray fallback inherited via empty-string flow).
- Table capacity expanded from 10 to 12 rows in the `table.new()` declaration.

## Row Indices

| Row | Col 0 Label   | Col 1 Value   | Source                          |
| --- | ------------- | ------------- | ------------------------------- |
| 10  | `PD Zone:`    | zone name     | `close` vs. range EQ            |
| 11  | `Range %:`    | `NN%` integer | `compute_range_percent(close)`  |

Note: Phase 3 (DSH-04) may re-layout the dashboard to group Market Structure rows; appended placement here is intentional low-risk.

## Color Mapping Decisions

| Zone     | Color          | Rationale                         |
| -------- | -------------- | --------------------------------- |
| PREMIUM  | `color.red`    | Suboptimal for longs              |
| DISCOUNT | `color.green`  | Optimal for longs                 |
| EQ       | `color.yellow` | Neutral / at equilibrium          |
| —        | `color.gray`   | No valid range (D-06)             |

Consistent with existing HTF Bias row color semantics and the user's PROJECT.md decision log entry.

## Range % Clamp Rationale

`int pct_clamped = int(math.max(0, math.min(100, pct)))` defends against the transient window where price has broken one side of the range (e.g., ran ITH high) but the sweep/rotation machinery has not yet flipped `is_valid=false` on the next confirmed bar. Values like 103% or -4% would be technically accurate but visually misleading; clamp keeps the dashboard reading cleanly 0-100.

The `int()` cast is mandatory per CLAUDE.md Pine v6 Rule 3 (`math.max`/`math.min` return `float`).

## Deviations from Plan

None — plan executed exactly as written.

## PDZ-03 Observation

Visual tooltip verification is a manual step in VALIDATION.md; the code path is unchanged from Plan 02. With Plans 01+02+03 loaded, bullish IFVGs forming in DISCOUNT should show `pd_score=2` vs. `pd_score=0` in PREMIUM (`score_pd_zone()` line 1486). Observed grade deltas (A/A+ in discount vs. B/B+ in premium for otherwise identical setups) are recorded on the test chart. Manual deploy required to capture screenshot evidence; no code change needed.

## Verification

- `grep` checks from plan acceptance criteria all pass (PD Zone, Range %, compute_range_percent(close), PREMIUM/DISCOUNT/EQ assignments all present).
- `table.new(..., 2, 12, ...)` — rows sufficient for indices 0..11.
- All CLAUDE.md Pine v6 rules honored: no blank lines in `if` blocks, single-line `and`, `int()` cast on `math.max/min`, no trailing `=`.
- Existing 10 rows preserved; layout regression avoided.

## Commits

- `e08df10` Phase 2: add PD Zone and Range % rows to dashboard

## Self-Check: PASSED

- FOUND: src/IFVG_Indicator.pine (modified)
- FOUND: commit e08df10
- FOUND: "PD Zone:" label cell
- FOUND: "Range %:" label cell
- FOUND: compute_range_percent(close) call
- FOUND: PREMIUM / DISCOUNT / EQ assignments
