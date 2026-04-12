# Phase 5: Grading System Remodel - Context

**Gathered:** 2026-04-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Complete redesign of the IFVG grading algorithm to accurately reflect the DodgysDD rating system. This involves: (1) adding "delivery from FVG" detection as a new grading input, (2) replacing the tier+modifier algorithm with a checklist scoring system where 5 criteria are each scored 0-2, (3) expanding momentum assessment granularity, (4) elevating PD zone from a modifier to a full scoring criterion, and (5) adding hard gates for A+ grade. The grade color mapping and display infrastructure remain unchanged.

</domain>

<decisions>
## Implementation Decisions

### Delivery from FVG Detection (NEW)
- **D-01:** Detect "delivery from FVG" by searching for an active opposite-direction FVG within the sweep lookback window before the IFVG. Check that candle bodies respected (did not close through) that source FVG before the displacement move into the IFVG zone. This is the PDF's key concept: price delivering FROM another FVG where bodies respect it "absolutely perfectly."
- **D-02:** A+ requires BOTH liquidity sweep AND delivery from FVG present. This is a hard gate — without both, the best achievable grade is A regardless of total score.
- **D-03:** Delivery detection shares the existing `i_sweep_lookback` input (default 20 bars) for its lookback window. No separate input needed.
- **D-04:** "Bodies respecting" means no candle body closes through the source FVG zone between the source FVG and the IFVG formation. Wicks can penetrate the zone — only body closes count as violations.

### Algorithm Structure
- **D-05:** Replace the current tier+modifier algorithm with a checklist scoring system. Five criteria, each scored 0-2:
  1. **Sweep+Delivery** (0-2): 2 = both sweep AND delivery, 1 = sweep OR delivery, 0 = neither
  2. **Momentum** (0-2): 2 = strong displacement + no chop, 1 = moderate (either strong inversion or strong displacement, not both), 0 = weak/choppy
  3. **Target clarity** (0-2): 2 = clear DOL target exists, 1 = target exists but weak, 0 = no real target
  4. **FVG singularity** (0-2): 2 = singular and obvious, 1 = singular but not obvious, 0 = not singular/messy
  5. **PD zone** (0-2): 2 = correct zone (longs in discount, shorts in premium), 1 = neutral/equilibrium, 0 = wrong zone
  Total range: 0-10. Grade mapping: A+=9-10, A=7-8, A-=6, B+=5, B=3-4, B-=2, C=0-1.
- **D-06:** A+ has hard gates that must ALL pass before score is checked: (1) sweep+delivery score = 2 (both present), (2) correct PD zone (pd_zone score = 2), (3) total score ≥ 9. Failing any gate caps the grade at A maximum.
- **D-07:** Grade thresholds (A+=9-10, A=7-8, etc.) are hardcoded. No configurable inputs for threshold boundaries.

### Momentum Scoring
- **D-08:** 3-tier momentum scoring mapped to 0-2 scale:
  - Score 2 (strong, no chop): Inversion candle has body > 70% of range AND range > ATR, AND displacement leg has 2+ same-direction candles with leg range > 1.5x ATR. Both inversion strength AND displacement must be present.
  - Score 1 (moderate, some chop): Either strong inversion OR strong displacement (not both). Or: body > 50%, range > 0.7x ATR.
  - Score 0 (weak/choppy): Body < 30% OR range < 0.5x ATR OR no displacement candles OR contradicting displacement direction.

### PD Zone Scoring
- **D-09:** PD zone scored 0-2: Correct zone = 2 (bullish IFVG in discount, bearish IFVG in premium), neutral/equilibrium = 1 (in equilibrium zone or no dealing range detected), wrong zone = 0 (bullish IFVG in premium, bearish IFVG in discount).
- **D-10:** Correct PD zone is a hard gate for A+ (see D-06). Without correct zone positioning, A+ is unreachable regardless of total score.

### Claude's Discretion
- Target clarity scoring thresholds (what distinguishes "clear DOL" score 2 from "weak target" score 1)
- FVG singularity scoring (how to distinguish "singular and obvious" score 2 from "singular but not obvious" score 1 — likely based on FVG size relative to ATR)
- Exact implementation of the delivery detection function (data structure, iteration pattern)
- Whether `assess_momentum()` returns the numeric score directly or a string that gets mapped
- How to handle HTF IFVGs in the new grading system (they currently get pd_zone='neutral')

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Rating System Specification
- `briefing/IFVG_Rating_System.pdf` — The authoritative reference for grade definitions. Each grade (A+ through C) has 5 criteria with specific descriptions. This is the spec being implemented.
- `strategy.md` §6 — Setup Rating System text version of the PDF criteria
- `strategy.md` §7.1 — Series of Gaps (singular FVG handling rules)

### Current Implementation (to be rewritten)
- `src/IFVG_Indicator.pine` lines 1396-1456 — Current `calculate_grade()` function (will be replaced)
- `src/IFVG_Indicator.pine` lines 1332-1362 — Current `assess_momentum()` (will be enhanced)
- `src/IFVG_Indicator.pine` lines 1310-1327 — Current `check_recent_sweep()` (kept, reused)
- `src/IFVG_Indicator.pine` lines 1370-1391 — Current `is_fvg_singular()` (kept, reused)
- `src/IFVG_Indicator.pine` lines 1278-1305 — Current `find_dol()` (kept, reused)
- `src/IFVG_Indicator.pine` lines 1576-1580 — Call site in `check_inversions()` (will be updated)

### Prior Phase Context
- `.planning/phases/01-bug-fixes-security-consolidation/01-CONTEXT.md` — D-01 singularity detection, D-02 grade threshold decisions (superseded by this phase)

### Issue Tracker
- `docs/ISSUES.md` — Issue 8 documents this grading remodel as pending

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (keep as-is)
- `check_recent_sweep()` — Sweep detection, already working correctly
- `is_fvg_singular()` — FVG singularity dual-check (proximity + overlap), working
- `find_dol()` — DOL target detection, working
- `grade_to_color()` — Grade-to-color mapping, no changes needed
- `grade_to_value()` / `grade_meets_minimum()` — Grade comparison helpers, no changes needed
- IFVG type definition — `grade`, `has_sweep`, `momentum`, `dol` fields exist; need to add `has_delivery` field

### Needs Modification
- `calculate_grade()` — Complete rewrite from tier+modifier to checklist scoring
- `assess_momentum()` — Enhance to return numeric score (0-2) or add mapping layer
- `check_inversions()` call site — Add delivery detection call, update parameter passing

### Needs Creation
- `check_delivery_from_fvg()` — New function to detect delivery from prior FVG with body respect check
- Potentially `score_target_clarity()` — Separate scoring for DOL target quality (currently binary has_dol)
- Potentially `score_singularity()` — Map singularity to 0-2 (currently binary)

### Integration Points
- Section 7 (lines 1224-1464) — Where grading functions live; new delivery function goes here
- Section 8 (lines 1466-1636) — `check_inversions()` call site where grading inputs are gathered
- IFVG type (lines 81-105) — Add `has_delivery` bool field

</code_context>

<specifics>
## Specific Ideas

- The PDF is the authoritative source. Each grade (A+ through B-) has a specific page with 5 checkmark criteria and chart examples. The algorithm must produce grades that match these examples.
- A+ chart examples show: price delivering from a prior FVG, sweeping liquidity (EQH/ITL), then forming the IFVG with clean displacement — all in the correct PD zone.
- B chart example annotation: "Not the most obvious FVG, also in discount, also not delivering from anywhere and no major sweep" — confirming that B grade = no sweep + no delivery + wrong zone.
- B- chart example annotation: "Second setup is B- since first iFVG was broken but then disrespected so just bad PA + not at anywhere important" — confirming B- = messy price action + no confluence.

</specifics>

<deferred>
## Deferred Ideas

- **SMT divergence as bonus grading factor** — The PDF mentions "SMTs are a bonus" for several grade levels. Requires correlated symbol data via additional `request.security()` calls. Deferred per PROJECT.md out-of-scope decision.
- **LRLR trendline liquidity as DOL target type** — The PDF lists 7 target types including trendline liquidity (LRLR). Complex diagonal rendering deferred per PROJECT.md.
- **Data Highs/Data Lows as DOL targets** — Listed in the PDF's 7 target types. Depends on Session Tracking (Phase 3 in roadmap). Will be available as DOL targets once sessions are implemented.

</deferred>

---

*Phase: 05-grading-system-remodel*
*Context gathered: 2026-04-12*
