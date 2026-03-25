# Phase 2: PD Zone Detection & Grading Integration - Context

**Gathered:** 2026-03-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Calculate and display the HTF dealing range (Premium/Discount zones) using swing-based detection on a dedicated timeframe, visualize zone boundaries with equilibrium and OTE overlays, integrate zone positioning into IFVG grading as a quality modifier, and add PD zone + range % rows to the dashboard. Session tracking and alerts are separate phases.

</domain>

<decisions>
## Implementation Decisions

### HTF Swing Source
- **D-01:** Dedicated PD timeframe input (`i_pd_timeframe`), separate from existing HTF1/HTF2 timeframes. Costs 2 extra `request.security()` calls (4 of 40 total). Traders get independent control — e.g., 4H for FVG detection but Daily for dealing range.
- **D-02:** Default PD zone timeframe is Daily. Standard ICT dealing range timeframe, works across all chart timeframes.

### OTE Zone (62-79%)
- **D-03:** Display as two dashed lines at 62% and 79% retracement levels with optional fill between them (separate toggle from PD zone fill).
- **D-04:** OTE is visual only — no extra grading modifier beyond the basic premium/discount +1/-1. Keeps grading simple, avoids double-counting zone position.
- **D-05:** OTE visual display is off by default (opt-in toggle). However, the PD zone grading modifier (+1/-1 for premium/discount) is always active when PD zones are enabled, regardless of OTE visual state. Visual and grading toggles are independent.

### Grade Recalibration
- **D-06:** Keep current grade thresholds unchanged initially (A tier: score>=2 → A+, >=1 → A, >=0 → A-, etc.). Quality score range expands from [-2,+3] to [-3,+4]. Verify grade distribution on real charts after implementation. Recalibrate in a follow-up only if >40% of setups cluster in a single grade.
- **D-07:** Separate toggle for PD zone grading modifier (`i_pd_grade_modifier`, default: true). Traders can see zones without affecting grades.

### IFVG Zone Display
- **D-08:** Show `pd_zone` in the IFVG label tooltip — e.g., "A+ Bull IFVG [DISCOUNT]". No extra visual elements, leverages existing labels.
- **D-09:** `pd_zone` is frozen at inversion time and never changes. Reflects market context when the setup formed, consistent with how grade is already frozen at inversion.

### Visual Density
- **D-10:** PD zone lines span full chart width (left edge to right edge). PD zones are structural reference — always visible.
- **D-11:** Zone fills (premium/discount background) are off by default (opt-in). Lines + labels show zone structure without overwhelming busy charts.
- **D-12:** Right-edge price labels: "Swing H (100%)", "EQ (50%)", "Swing L (0%)". Clean, out of the way.

### Claude's Discretion
- OTE zone colors and opacity values
- Exact line widths for zone boundary lines (EQ likely width=2 solid, swing H/L likely width=1 dashed — as sketched in PHASE4_PD_ZONES_PLAN.md)
- Pivot lookback default value (plan suggests 5 — verify against typical swing spacing)
- Dashboard PD Zone and Range % row styling details
- OTE fill color and opacity
- How to handle edge case where swing high < swing low or no swings detected

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Implementation Reference
- `PHASE4_PD_ZONES_PLAN.md` — Detailed pre-GSD implementation sketch covering inputs, globals, HTF swing detection via ta.pivothigh/ta.pivotlow + request.security(), zone calculation, grading integration, visualization, and dashboard changes. Use as starting point but adapt to decisions captured above.

### Strategy & Grading
- `strategy.md` — Trading strategy rules, ICT dealing range concept, zone-based trade selection
- `PRD.md` §3.6 — Premium/Discount zone feature specification
- `briefing/IFVG_Rating_System.pdf` — Reference grading system with visual examples

### Architecture & Code
- `ARCHITECTURE.md` — Complete technical specification with algorithms
- `.planning/codebase/ARCHITECTURE.md` — Current 12-section code organization and layer descriptions
- `.planning/codebase/CONVENTIONS.md` — Naming patterns (PascalCase types, snake_case functions, i_/g_ prefixes)
- `.planning/phases/01-bug-fixes-security-consolidation/01-CONTEXT.md` — Phase 1 decisions: tuple consolidation pattern, get_htf_bias() placement, singularity algorithm

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `request.security()` tuple pattern (line 704-708): 7-element tuples per TF — use same pattern for PD swing data
- `calculate_grade()` (line 1463): Current signature `(has_sweep, has_delivery, momentum, has_dol, fvg_singular)` — needs `pd_zone_modifier` parameter added
- `get_htf_bias()` (Section 4): Shared HTF function pattern — follow same placement for PD zone utility functions
- `grade_to_color()` (Section 4): Grade-to-color mapping — no changes needed but reference for consistency

### Established Patterns
- ATR-based thresholds throughout (e.g., EQH/EQL tolerance at `ATR * 0.1`) — use for PD zone calculations
- `var` arrays + FIFO cleanup for persistent state — PD zone uses `var` globals (no arrays needed, single dealing range)
- Drawing object lifecycle: delete-before-recreate pattern on each bar
- `barstate.isconfirmed` gate for all detection logic

### Integration Points
- **IFVG type** (lines 92-122): Add `pd_zone` string field ("premium"/"discount"/"equilibrium"/"neutral")
- **calculate_grade()** (line 1463): Add `pd_zone_modifier` int parameter, apply to quality_score
- **check_inversions()** (line ~1470): Set pd_zone on IFVG at inversion time using current g_pd_current_zone
- **Dashboard** (Section 11, line ~2312): Expand table rows from 10 to 12, add PD Zone and Range % rows
- **Rendering** (Section 10): Add new `render_pd_zones()` function after existing render functions
- **Main loop** (Section 12): Add `update_pd_zones()` after swing detection, `render_pd_zones()` after other rendering
- **Inputs** (Section 2): Add GROUP_PD_ZONES input group after existing groups
- **Globals** (Section 3): Add PD zone `var` globals and visual element references

</code_context>

<specifics>
## Specific Ideas

- The existing `PHASE4_PD_ZONES_PLAN.md` provides a solid implementation blueprint — use it as the primary reference, adapting for decisions made here (OTE zone details, visual defaults, grading toggle separation)
- PD zone grading modifier should be independent of ALL visual toggles — even with every visual element hidden, the +1/-1 modifier still applies to grades when `i_pd_grade_modifier` is enabled

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-pd-zone-detection-grading-integration*
*Context gathered: 2026-03-25*
