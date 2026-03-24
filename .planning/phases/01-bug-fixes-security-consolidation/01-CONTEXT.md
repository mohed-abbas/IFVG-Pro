# Phase 1: Bug Fixes & Security Consolidation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Fix the hardcoded `fvg_singular = true` bug that inflates all grades by +1, extract the duplicated HTF bias calculation into a shared function, and consolidate 14 individual `request.security()` calls into tuple syntax to free budget headroom. No new features — this phase establishes an accurate grading baseline and unblocks future phases.

</domain>

<decisions>
## Implementation Decisions

### FVG Singularity Detection (FIX-01)
- **D-01:** Implement a dual-check algorithm for FVG singularity: proximity check (no same-direction FVG within N bars) AND overlap check (zone doesn't overlap/nearly-overlap another same-direction FVG). Both must pass for singular = true.
- **D-02:** Natural grade recalibration after fix — keep current grade thresholds unchanged (A+: score>=2, A: score>=1, A-: score>=0, etc). Let grades drop naturally for non-singular FVGs. This matches the strategy's intent where singular FVGs are genuinely higher quality.

### HTF Bias Deduplication (FIX-02)
- **D-03:** Extract the HTF bias calculation logic (currently duplicated at lines ~1838-1851 and ~2360-2370) into a single shared function. Both render_ifvg_boxes and render_dashboard should call this shared function.

### Security Call Consolidation (FIX-03)
- **D-04:** Consolidate 14 request.security() calls into tuples. Claude's discretion on exact tuple structure — optimize for maximum consolidation (ideally 2 mega-tuples, 1 per timeframe) while maintaining code clarity. Pine Script v6 supports up to 127 tuple elements.

### Claude's Discretion
- Exact proximity threshold (N bars) for FVG singularity check — choose based on typical FVG spacing patterns in the codebase
- Overlap tolerance (how close zones need to be to count as overlapping) — use ATR-based threshold consistent with existing patterns
- Tuple variable naming and destructuring style — follow existing codebase conventions
- Shared HTF bias function signature and placement within section structure

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Strategy & Grading
- `strategy.md` §6 — Setup Rating System (defines what "singular FVG" means for each grade tier)
- `strategy.md` §7.1 — Series of Gaps (how to handle multiple consecutive FVGs)
- `PRD.md` §3.4 — Grading Algorithm specification (hybrid tier + quality scoring)
- `briefing/IFVG_Rating_System.pdf` — Reference grading system with visual examples

### Architecture & Code
- `ARCHITECTURE.md` §4 — Core Algorithms (grading algorithm, FVG detection)
- `.planning/codebase/CONCERNS.md` — Documents the fvg_singular bug, HTF bias duplication, and security budget pressure
- `.planning/codebase/ARCHITECTURE.md` — Current 12-section code organization
- `.planning/research/STACK.md` — request.security() tuple consolidation patterns and budget analysis

</canonical_refs>

<code_context>
## Existing Code Insights

### Bug Locations
- `src/IFVG_Indicator.pine:1595` — `bool fvg_singular = true` hardcode inside `check_inversions()`
- `src/IFVG_Indicator.pine:1398` — `calculate_grade()` function signature accepts `fvg_singular` parameter
- `src/IFVG_Indicator.pine:1432-1434` — Where fvg_singular affects quality_score (+1/-1)

### HTF Bias Duplication
- `src/IFVG_Indicator.pine:1838-1851` — Bias calc in render_ifvg_boxes (for LTF filtering)
- `src/IFVG_Indicator.pine:2360-2370` — Identical bias calc in render_dashboard

### Security Calls
- `src/IFVG_Indicator.pine:653-680` — All 14 request.security() calls (7 per HTF timeframe)
- Pattern: `request.security(syminfo.tickerid, i_htf_timeframe, expression, lookahead=barmerge.lookahead_off)`
- Values per TF: high, low, close, high[2], low[2], bar_index, ta.atr()

### Reusable Patterns
- ATR-based thresholds used throughout (e.g., EQH/EQL tolerance at `ATR * 0.1`) — use same pattern for FVG overlap detection
- `g_fvg_array` already stores all active FVGs with direction — can iterate for proximity/overlap checks
- Existing section separator conventions (═══ for major, ─── for minor)

### Integration Points
- `check_inversions()` at line ~1470 — where singularity check must run before calling `calculate_grade()`
- Section 4 (Utility functions, lines 310-597) — natural home for shared `get_htf_bias()` function
- Section 5B (HTF detection, lines 645-761) — where consolidated tuple calls should live

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches. Key constraint: all changes must produce zero visual regressions in existing FVG/IFVG/HTF rendering.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-bug-fixes-security-consolidation*
*Context gathered: 2026-03-24*
