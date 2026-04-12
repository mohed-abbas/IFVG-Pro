---
phase: 05-grading-system-remodel
plan: 02
subsystem: grading-engine
tags: [checklist-scoring, grade-algorithm, hard-gates, pine-script]
dependency_graph:
  requires: [has_delivery-field, pd_zone-field, int-momentum-scoring]
  provides: [checklist-grading, score_target_clarity, score_singularity, score_pd_zone, a-plus-hard-gates]
  affects: [calculate_grade, check_inversions, IFVG-grading-output]
tech_stack:
  added: []
  patterns: [checklist-scoring-0-10, hard-gate-pattern, helper-score-functions]
key_files:
  created: []
  modified:
    - src/IFVG_Indicator.pine
decisions:
  - PD zone hardcoded to "neutral" at call site making A+ unreachable until PD zone detection re-implemented (intentional per D-10)
  - Passing full Liquidity object to calculate_grade instead of bool has_dol to enable quality/touch_count scoring
  - Removed old tier+modifier algorithm entirely rather than keeping it as fallback
metrics:
  duration: 160s
  completed: "2026-04-12T21:09:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 5 Plan 2: Checklist Scoring Algorithm Summary

Rewrote calculate_grade() from tier+modifier to 5-criterion checklist scoring (0-10) with A+ hard gates, added three scoring helper functions (target clarity, singularity, PD zone), and updated check_inversions() call site with expanded parameters.

## Completed Tasks

| Task | Name | Commit | Key Changes |
|------|------|--------|-------------|
| 1 | Create scoring helper functions | 3d8ac8e | Added score_target_clarity (DOL quality/touch count), score_singularity (singular + ATR-relative size), score_pd_zone (zone vs direction) |
| 2 | Rewrite calculate_grade() and update call site | 437e610 | New 5-criterion scoring with A+ hard gates per D-06, updated check_inversions() call with expanded params, removed old tier+modifier |

## Deviations from Plan

None - plan executed exactly as written.

## Key Implementation Details

### Checklist Scoring System (calculate_grade)
- **Criterion 1 - Sweep + Delivery (0-2):** Both present=2, either=1, neither=0
- **Criterion 2 - Momentum (0-2):** Direct from assess_momentum() int return
- **Criterion 3 - Target Clarity (0-2):** Perfect quality or multi-touch=2, weak target=1, no DOL=0
- **Criterion 4 - FVG Singularity (0-2):** Singular and large (>=0.5 ATR)=2, singular but small=1, not singular=0
- **Criterion 5 - PD Zone (0-2):** Correct zone=2, neutral/equilibrium=1, wrong zone=0

### Grade Mapping (per D-07)
| Score | Grade | Hard Gate |
|-------|-------|-----------|
| 9-10 | A+ | Requires sweep_delivery=2 AND pd_score=2 |
| 9-10 | A | If hard gates fail |
| 7-8 | A | - |
| 6 | A- | - |
| 5 | B+ | - |
| 3-4 | B | - |
| 2 | B- | - |
| 0-1 | C | - |

### A+ Unreachable (Intentional)
PD zone is hardcoded to "neutral" (score 1) at the check_inversions() call site. D-06 requires pd_score=2 for A+. This means A+ is unreachable until Phase 2 re-implements PD zone detection. Maximum achievable grade is A (total 7-8 with pd_score capped at 1).

## Verification Results

- Scoring function references: 6 (3 definitions + 3 calls from calculate_grade)
- A+ hard gate line: confirmed (total >= 9 and sweep_delivery_score == 2 and pd_score == 2)
- Updated call site: confirmed (calculate_grade with 8 parameters)
- Old tier/quality_score references: 0 (fully removed)
- File line count: 2496 lines (was 2475, net +21 lines)

## Self-Check: PASSED
