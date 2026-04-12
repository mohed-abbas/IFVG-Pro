# Phase 5: Grading System Remodel - Research

**Researched:** 2026-04-12
**Domain:** Pine Script v6 algorithmic grading logic (IFVG setup quality assessment)
**Confidence:** HIGH

## Summary

This phase replaces the current tier+modifier grading algorithm (`calculate_grade()`) with a checklist scoring system (5 criteria, each 0-2, total 0-10) and adds delivery-from-FVG detection as a new grading input. The work is entirely within Pine Script v6 in a single file (`src/IFVG_Indicator.pine`), affecting Section 7 (grading functions), Section 8 (inversion detection call site), and Section 10 (tooltip rendering).

The current `calculate_grade()` function (lines 1396-1456) uses a 2-step tier+modifier approach: sweep presence determines the tier (A or B), then momentum and singularity adjust by +/-1 to get the final grade. The new system scores 5 independent criteria (sweep+delivery, momentum, target clarity, FVG singularity, PD zone) each 0-2 for a total of 0-10, with hard gates for A+ (both sweep AND delivery, correct PD zone, total >= 9). The `assess_momentum()` function (lines 1332-1362) currently returns strings ("strong_no_chop", "neutral", "weak_or_choppy") and needs enhancement to distinguish the D-08 3-tier scoring more precisely. A new `check_delivery_from_fvg()` function must be created to search HTF and LTF FVG arrays for an opposite-direction FVG with body-respected candles.

**Primary recommendation:** Implement in 3 waves: (1) add `has_delivery` field to IFVG type + delivery detection function, (2) rewrite `calculate_grade()` and `assess_momentum()` with checklist scoring, (3) update tooltip rendering to show all 5 criteria with numeric scores. PD zone scoring defaults to neutral (score 1) since PD zone detection code was removed and Phase 2 hasn't been re-implemented yet.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Detect "delivery from FVG" by searching for an active opposite-direction FVG within the sweep lookback window before the IFVG. Check that candle bodies respected (did not close through) that source FVG before the displacement move into the IFVG zone.
- **D-02:** A+ requires BOTH liquidity sweep AND delivery from FVG present. Hard gate.
- **D-03:** Delivery detection shares the existing `i_sweep_lookback` input (default 20 bars).
- **D-04:** "Bodies respecting" means no candle body closes through the source FVG zone. Wicks can penetrate.
- **D-05:** Replace tier+modifier with checklist scoring. Five criteria, each 0-2. Total 0-10. Grade mapping: A+=9-10, A=7-8, A-=6, B+=5, B=3-4, B-=2, C=0-1.
- **D-06:** A+ hard gates: sweep+delivery=2, pd_zone=2, total>=9. Failing any gate caps at A.
- **D-07:** Grade thresholds hardcoded. No configurable inputs.
- **D-08:** 3-tier momentum scoring: 2=strong inversion AND displacement, 1=either/or, 0=weak/choppy.
- **D-09:** PD zone scored 0-2: correct=2, neutral/equilibrium/no dealing range=1, wrong=0.
- **D-10:** Correct PD zone is a hard gate for A+ (see D-06).
- **D-11:** Delivery detection uses priority cascade: HTF FVGs first, then LTF fallback.
- **D-12:** HTF and LTF delivery scored equally.

### Claude's Discretion
- Target clarity scoring thresholds (score 2 vs score 1 for DOL quality)
- FVG singularity scoring (how to distinguish score 2 "singular and obvious" from score 1 "singular but not obvious")
- Exact implementation of delivery detection function (data structure, iteration pattern)
- Whether `assess_momentum()` returns numeric score or string that gets mapped
- How to handle HTF IFVGs in the new grading system (currently get pd_zone='neutral')

### Deferred Ideas (OUT OF SCOPE)
- SMT divergence as bonus grading factor (requires correlated symbol data)
- LRLR trendline liquidity as DOL target type (complex diagonal rendering)
- Data Highs/Data Lows as DOL targets (depends on Session Tracking, Phase 3)
</user_constraints>

## Project Constraints (from CLAUDE.md)

- **Single file**: All code in `src/IFVG_Indicator.pine` -- maintain section organization
- **Pine Script v6 syntax**: No blank lines in block bodies, operators must end lines for continuation, `=` never last token, `math.abs()`/`math.max()` return float (cast to int), no `continue` (use nested `if`)
- **No repainting**: All detection on `barstate.isconfirmed` only
- **Drawing limits**: Max 500 boxes/lines/labels -- FIFO cleanup
- **Security call budget**: 3 calls used (2 HTF tuples + 1 PD swing), max 40 -- delivery detection must NOT add new calls
- **Git commits**: No AI attribution, no Co-Authored-By tags, use "Phase 5:" prefix
- **Naming**: Functions use `snake_case` with `verb_noun()` pattern, types use `PascalCase`, inputs use `i_` prefix
- **Testing**: Visual verification on TradingView only -- no automated tests

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Pine Script | v6 | Sole language | TradingView platform requirement |

### Supporting
No external libraries. Pine Script is self-contained.

## Architecture Patterns

### Code Organization for New/Modified Functions

All grading functions live in **Section 7** (lines 1224-1456). The new `check_delivery_from_fvg()` function goes here, alongside existing `check_recent_sweep()`, `assess_momentum()`, `is_fvg_singular()`, and the rewritten `calculate_grade()`. [VERIFIED: codebase grep]

```
Section 7 (Grading & Analysis Functions):
├── find_previous_swing_high/low()  [KEEP]
├── find_dol()                      [KEEP]
├── check_recent_sweep()            [KEEP]
├── assess_momentum()               [MODIFY - enhance to return int 0-2]
├── is_fvg_singular()               [KEEP]
├── check_delivery_from_fvg()       [NEW]
├── score_target_clarity()          [NEW - discretion]
├── score_singularity()             [NEW - discretion]
└── calculate_grade()               [REWRITE]
```

### Pattern 1: Delivery Detection Algorithm

**What:** Search for an opposite-direction FVG that price "delivered from" before forming the IFVG. [VERIFIED: CONTEXT.md D-01, D-04, D-11]

**Key constraints:**
- Source FVG must be OPPOSITE direction to the IFVG (e.g., bullish IFVG looks for bearish source FVG)
- Source FVG must exist within `i_sweep_lookback` bars of the IFVG formation
- All candle bodies between source FVG formation and IFVG must respect (not close through) the source FVG zone
- Search order: `g_htf_fvg_array` first, then `g_htf2_fvg_array`, then `g_fvg_array`

**Implementation approach:**
```pine
// Source: Architecture decision from CONTEXT.md D-01, D-04, D-11
check_delivery_from_fvg(bool ifvg_is_bullish, int ifvg_bar, int lookback) =>
    bool result = false
    // For bullish IFVG, look for bearish source FVG (price came DOWN from it)
    // For bearish IFVG, look for bullish source FVG (price came UP from it)
    bool look_for_bullish_source = not ifvg_is_bullish
    // Priority cascade: HTF1 -> HTF2 -> LTF
    // Search each array for opposite-direction active/inverted FVGs within lookback
    // For each candidate: check body respect from source FVG end_bar to ifvg_bar
    // Body respect check: iterate candles, verify no close through source zone
    result
```

**Body respect check pattern:**
```pine
// For bearish source FVG (bullish IFVG looking for delivery):
// No candle body should close ABOVE source_fvg.top
// Wicks above are OK per D-04
bool bodies_respected = true
for k = 1 to bar_distance
    if k <= bar_distance
        float body_top = math.max(close[k], open[k])
        float body_bottom = math.min(close[k], open[k])
        // For bearish source: body must not close above top
        if look_for_bullish_source
            if close[k] < source_fvg.bottom  // body closed through bottom
                bodies_respected := false
                break
        else
            if close[k] > source_fvg.top  // body closed through top
                bodies_respected := false
                break
```

### Pattern 2: Checklist Scoring Algorithm

**What:** Replace the tier+modifier grading with 5 independent scores summed to 0-10. [VERIFIED: CONTEXT.md D-05]

**Structure:**
```pine
calculate_grade(bool has_sweep, bool has_delivery, int momentum_score, 
                bool has_dol, int dol_quality, bool fvg_singular, int fvg_size_quality,
                string pd_zone) =>
    // Score each criterion 0-2
    int sweep_delivery_score = 0
    if has_sweep and has_delivery
        sweep_delivery_score := 2
    else if has_sweep or has_delivery
        sweep_delivery_score := 1
    // momentum_score already 0-2 from assess_momentum()
    // target_clarity: 2=clear DOL, 1=weak target, 0=none
    int target_score = score_target_clarity(has_dol, dol_quality)
    // singularity: 2=singular+obvious, 1=singular not obvious, 0=not singular
    int singular_score = score_singularity(fvg_singular, fvg_size_quality)
    // pd_zone: 2=correct, 1=neutral, 0=wrong
    int pd_score = score_pd_zone(pd_zone, ifvg_is_bullish)
    int total = sweep_delivery_score + momentum_score + target_score + singular_score + pd_score
    // Hard gates for A+
    string result = "C"
    if total >= 9 and sweep_delivery_score == 2 and pd_score == 2
        result := total >= 10 ? "A+" : "A+"  // 9-10 both A+ per D-05
    else if total >= 9
        result := "A"  // Hard gate failed, cap at A
    // ... threshold mapping per D-05
    result
```

### Pattern 3: PD Zone Scoring Without PD Zone Detection

**What:** PD zone code was removed from the codebase (commit `33e0085`). Phase 2 is reset and hasn't been re-implemented. The IFVG type does NOT currently have a `pd_zone` field. [VERIFIED: codebase grep found no premium/discount/pd_zone references]

**Implication:** PD zone scoring (D-09) must default to `"neutral"` (score 1) for all IFVGs until Phase 2 re-implements PD zone detection. This is explicitly covered by D-09: "neutral/equilibrium = 1 (in equilibrium zone or **no dealing range detected**)."

**Approach:** Add `pd_zone` field to IFVG type with default `"neutral"`. The `score_pd_zone()` function maps string to score. When Phase 2 is re-implemented, it will populate `pd_zone` with actual values. Until then, A+ is unreachable via the hard gate (D-06 requires pd_score=2), which means the best achievable grade is A -- this is acceptable and correctly reflects that full grading requires PD zone data.

**Important:** This means A+ is blocked until Phase 2 re-implements PD zone detection. The user should be aware of this implication.

### Anti-Patterns to Avoid

- **Blank lines inside `for`/`if` blocks:** Pine Script v6 uses indentation for block boundaries. A blank line terminates the block. Keep all lines contiguous. [VERIFIED: CLAUDE.md]
- **Splitting expressions across lines without trailing operator:** The operator (`and`, `or`, `+`) must be the LAST token before newline. [VERIFIED: CLAUDE.md]
- **Returning float from math.abs() to int field:** Always cast: `int(math.abs(...))`. [VERIFIED: CLAUDE.md]
- **Adding new request.security() calls for delivery detection:** Delivery detection must use existing `g_htf_fvg_array` and `g_htf2_fvg_array` arrays -- no new security calls needed. [VERIFIED: existing arrays in codebase]
- **Modifying `var` globals inside `=>` functions:** Pine Script v6 constraint. Read from globals, don't write. [VERIFIED: memory/feedback_pd_zone_approach.md]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sweep detection | New sweep checker | Existing `check_recent_sweep()` | Already handles BSL/SSL with lookback, tested |
| DOL finding | New target finder | Existing `find_dol()` | Already handles all liquidity types |
| Singularity check | New FVG proximity check | Existing `is_fvg_singular()` | Dual-check (proximity + overlap) already correct |
| Grade-to-color mapping | New color function | Existing `grade_to_color()` | Grade strings unchanged, no modification needed |
| Grade comparison | New comparison logic | Existing `grade_to_value()` / `grade_meets_minimum()` | Works on grade strings, no modification needed |

## Common Pitfalls

### Pitfall 1: IFVG Type Field Addition Requires All .new() Call Sites
**What goes wrong:** Adding `has_delivery` and `pd_zone` fields to the IFVG type but missing one of the `.new()` call sites causes a compile error.
**Why it happens:** There are 2 IFVG creation sites: LTF `check_inversions()` (line 1583) and HTF `check_htf_inversions()` (line 719). Both must include the new fields.
**How to avoid:** Search for all `IFVG.new(` occurrences. There are exactly 2: line 1583 (LTF) and line 719 (HTF). HTF IFVGs get `has_delivery = false, pd_zone = "neutral"`.
**Warning signs:** Pine Script compile error mentioning missing field. [VERIFIED: codebase grep found 2 IFVG.new() sites]

### Pitfall 2: Body Respect Check Using Wrong Bar Indexing
**What goes wrong:** The delivery detection iterates candles between source FVG and IFVG using `close[k]` but gets the offset math wrong.
**Why it happens:** `close[k]` references k bars back from current bar. The source FVG's `end_bar` is an absolute bar_index. Need to convert: `offset = bar_index - source_fvg.end_bar`.
**How to avoid:** Calculate the bar distance between IFVG formation (current bar_index) and source FVG end_bar. Iterate with offsets from 1 to that distance (or a capped maximum to avoid deep lookback issues).
**Warning signs:** Delivery always detected (or never detected) regardless of actual price action.

### Pitfall 3: Assess Momentum Bug -- Current Code Has Incorrect Logic
**What goes wrong:** The current `assess_momentum()` (lines 1356-1361) treats `strong_inversion OR strong_displacement` the same as `strong_inversion AND strong_displacement` -- both map to "strong_no_chop".
**Why it happens:** Lines 1358-1359 show `else if strong_inversion or strong_displacement` also returns "strong_no_chop", which contradicts D-08's requirement that score 2 requires BOTH and score 1 requires only one.
**How to avoid:** The rewrite must clearly separate: score 2 = both present, score 1 = either/or. This is already mandated by D-08.
**Warning signs:** Too many setups getting momentum score 2. [VERIFIED: codebase lines 1356-1359]

### Pitfall 4: A+ Being Permanently Unreachable
**What goes wrong:** Since PD zone code is removed, `pd_score` always equals 1 (neutral), which fails the A+ hard gate (requires pd_score=2). No setup can ever get A+.
**Why it happens:** Phase 2 PD zone detection is pending re-implementation.
**How to avoid:** This is expected and acceptable. Document it clearly. When Phase 2 ships, A+ becomes achievable. Alternatively, the planner could add a "pd_zone_available" guard that relaxes the hard gate when no PD zone data exists -- but this contradicts D-06.
**Warning signs:** Zero A+ grades on any chart.

### Pitfall 5: HTF FVG Arrays May Be Empty When HTF Is Disabled
**What goes wrong:** Delivery detection searches `g_htf_fvg_array` and `g_htf2_fvg_array` first, but if HTF is disabled (`i_enable_htf = false`), these arrays are always empty.
**Why it happens:** HTF FVG detection only runs when HTF is enabled.
**How to avoid:** The cascade naturally handles this: empty HTF arrays produce no delivery match, falling through to LTF search. Ensure the function doesn't error on empty arrays. [VERIFIED: arrays are initialized as empty in Section 3]

### Pitfall 6: Tooltip String Length and Readability
**What goes wrong:** Adding 5 criteria with numeric scores to the tooltip makes it too long or hard to read.
**Why it happens:** Current tooltip is 7 lines. Adding delivery status, PD zone, singularity, and numeric scores could push to 12+ lines.
**How to avoid:** Use concise format: `"[2] Sweep+Delivery"` instead of `"Sweep and Delivery: Score 2/2"`. Keep the existing checklist visual style (checkbox icons).

## Code Examples

### Current IFVG Type (needs modification)
```pine
// Source: src/IFVG_Indicator.pine lines 82-105
// CURRENT -- missing has_delivery and pd_zone fields
type IFVG
    float top
    float bottom
    float mid
    int start_bar
    int inversion_bar
    float inversion_close
    bool is_bullish
    string status
    string grade
    bool entry_valid
    float be_level
    string be_status
    float sl_level
    string sl_type
    Liquidity dol
    bool has_sweep
    string momentum        // Currently string, will need score mapping
    box box_id
    label label_id
    line be_line_id
    line sl_line_id
    line entry_line_id
    label entry_label_id
```
[VERIFIED: codebase lines 82-105]

### Current calculate_grade() (to be replaced)
```pine
// Source: src/IFVG_Indicator.pine lines 1396-1456
// CURRENT tier+modifier approach -- 4 inputs, no delivery, no PD zone
calculate_grade(bool has_sweep, string momentum, bool has_dol, bool fvg_singular) =>
    // Step 1: tier from sweep (A or B)
    // Step 2: quality_score from momentum +/-1, singularity +/-1
    // Step 3: combine tier + modifier
```
[VERIFIED: codebase lines 1396-1456]

### Current assess_momentum() Bug
```pine
// Source: src/IFVG_Indicator.pine lines 1356-1361
// BUG: both AND and OR cases return "strong_no_chop"
if strong_inversion and strong_displacement
    result := "strong_no_chop"
else if strong_inversion or strong_displacement    // <-- should be different tier
    result := "strong_no_chop"                     // <-- same result, incorrect
else if body_ratio < 0.3 or candle_range < atr_value * 0.5
    result := "weak_or_choppy"
```
[VERIFIED: codebase lines 1354-1362]

### Current Tooltip Format (needs update)
```pine
// Source: src/IFVG_Indicator.pine lines 1924-1937
// CURRENT -- 4 criteria with checkboxes
tooltip_text = "Grade: " + ifvg.grade + "\n" +
              "─────────────\n" +
              sweep_check + " Sweep\n" +
              momentum_check + " Momentum: " + momentum_text + "\n" +
              dol_check + " DOL: " + dol_text + "\n" +
              "─────────────\n" +
              "Entry: " + entry_status
```
[VERIFIED: codebase lines 1931-1937]

### Current IFVG.new() Call Sites
```pine
// LTF: src/IFVG_Indicator.pine line 1583-1606
// HTF: src/IFVG_Indicator.pine line 719-742
// Both must be updated to include new fields
```
[VERIFIED: codebase grep found exactly 2 IFVG.new() calls]

## Discretion Recommendations

### Target Clarity Scoring (Claude's Discretion)

**Recommendation:** [ASSUMED]
- Score 2 (clear DOL): `find_dol()` returns a non-na Liquidity object AND the target has quality "perfect" or touch_count >= 2 (multiple touches = stronger level)
- Score 1 (weak target): `find_dol()` returns a non-na object but it's a single-touch level (touch_count == 1) -- less established
- Score 0 (no target): `find_dol()` returns na

**Rationale:** The existing `find_dol()` returns a Liquidity object which has `quality` ("perfect" vs "relative") and `touch_count` fields. This provides natural granularity without new detection logic.

### FVG Singularity Scoring (Claude's Discretion)

**Recommendation:** [ASSUMED]
- Score 2 (singular and obvious): `is_fvg_singular()` returns true AND FVG size >= ATR * 0.5 (large, visually obvious gap)
- Score 1 (singular but not obvious): `is_fvg_singular()` returns true AND FVG size < ATR * 0.5 (singular but small/inconspicuous)
- Score 0 (not singular): `is_fvg_singular()` returns false (clustered with other FVGs)

**Rationale:** Strategy.md section 7.2 discusses "inconspicuous gaps" -- small FVGs that are hard to see. The ATR-relative size check distinguishes obvious from inconspicuous. ATR * 0.5 is a reasonable threshold (the minimum detection size is ATR * 0.25).

### assess_momentum() Return Type (Claude's Discretion)

**Recommendation:** Return `int` (0-2) directly instead of a string. The string return was only used for tooltip display, and the tooltip will be rewritten anyway. Returning an int avoids a redundant string-to-score mapping step. If the tooltip needs text, map score-to-string in the rendering section.

### HTF IFVG Grading (Claude's Discretion)

**Recommendation:** Keep HTF IFVGs with `grade = "HTF"` (no grading). They serve as bias indicators, not trade setups. The new checklist grading only applies to LTF IFVGs. HTF IFVG creation in `check_htf_inversions()` gets `has_delivery = false, pd_zone = "neutral"` as defaults.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Tier + modifier (sweep determines tier, quality adjusts) | Checklist scoring (5 criteria x 0-2) | This phase | More granular, matches PDF spec |
| Binary sweep detection (has/hasn't) | Sweep + delivery combined criterion | This phase | Captures "delivery from FVG" concept |
| 3-string momentum ("strong"/"neutral"/"weak") | 3-tier numeric (0/1/2) with precise thresholds | This phase | Fixes AND/OR bug, adds granularity |
| No PD zone in grading | PD zone as full scoring criterion (0-2) | This phase | Elevates zone from modifier to criterion |
| No delivery detection | Full delivery-from-FVG detection with body respect | This phase | New capability enabling A+ grades |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Target clarity score 2 should use touch_count >= 2 as quality threshold | Discretion: Target Clarity | Minor -- threshold is adjustable, affects grade spread |
| A2 | FVG size >= ATR * 0.5 is good threshold for "obvious" singularity | Discretion: Singularity Scoring | Minor -- threshold is adjustable |
| A3 | `assess_momentum()` should return int instead of string | Discretion: Return Type | Very low -- tooltip mapping is trivial either way |
| A4 | HTF IFVGs should remain ungraded (grade="HTF") | Discretion: HTF Grading | Low -- HTF setups are bias indicators, not entries |
| A5 | PD zone defaulting to "neutral" (score 1) is acceptable until Phase 2 re-implementation | Architecture: PD Zone | Medium -- A+ is unreachable until PD zones exist. User should confirm this is acceptable |

## Open Questions

1. **A+ unreachable until Phase 2 re-implements PD zones**
   - What we know: PD zone code was removed (commit 33e0085). D-06 requires pd_score=2 for A+. Without PD zone detection, pd_score is always 1.
   - What's unclear: Should Phase 5 proceed knowing A+ is blocked, or should PD zone detection be included in this phase?
   - Recommendation: Proceed with Phase 5 as-is. A+ being blocked accurately reflects that the grading system needs PD zone data for its highest grade. Phase 2 re-implementation will unlock A+.

2. **Delivery detection for "inverted" vs "active" source FVGs**
   - What we know: D-01 says search for "active opposite-direction FVG." But some source FVGs may have been inverted themselves by the time the IFVG forms.
   - What's unclear: Should delivery detection only check `status == "active"` FVGs, or also recently inverted ones?
   - Recommendation: Check `status == "active"` only. An inverted FVG has been closed through by definition, so "bodies respecting" cannot hold. However, FVGs that were just inverted on the current bar could be edge cases -- the planner should consider this.

3. **Momentum score thresholds for "moderate" (score 1)**
   - What we know: D-08 says score 1 = "moderate: either strong inversion OR displacement, not both. Or: body > 50%, range > 0.7x ATR."
   - What's unclear: The "Or" clause adds a secondary threshold (`body > 50%, range > 0.7x ATR`) that doesn't fit the AND/OR logic. Is this an alternative path to score 1?
   - Recommendation: Treat it as an alternative: score 1 if (strong_inversion XOR strong_displacement) OR (body_ratio > 0.5 AND range > 0.7 * ATR). This gives a wider "moderate" band.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None -- Pine Script has no automated testing |
| Config file | N/A |
| Quick run command | Copy `src/IFVG_Indicator.pine` to TradingView, apply to chart |
| Full suite command | Visual verification across multiple chart symbols/timeframes |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| D-01 | Delivery detection finds opposite FVG with body respect | manual-only | Visual: check delivery indicator on chart tooltips | N/A |
| D-05 | Checklist scoring produces correct grades | manual-only | Visual: compare grade labels to expected criteria | N/A |
| D-06 | A+ hard gates block correctly | manual-only | Visual: verify no A+ appears (since PD zones absent) | N/A |
| D-08 | Momentum scoring 3-tier | manual-only | Visual: check tooltip momentum scores on various candles | N/A |
| D-11 | HTF priority cascade for delivery | manual-only | Visual: enable/disable HTF, verify delivery detection changes | N/A |

**Justification for manual-only:** Pine Script has no test framework. All validation requires deploying to TradingView and visually verifying on live charts. [VERIFIED: CLAUDE.md]

### Wave 0 Gaps
None -- no test infrastructure to set up. Validation is manual.

## Security Domain

Security enforcement is not applicable to this phase. This is a TradingView Pine Script indicator with no authentication, sessions, input validation beyond TradingView's input.* functions, or cryptography. All inputs are handled by TradingView's built-in input system with min/max constraints.

## Sources

### Primary (HIGH confidence)
- `src/IFVG_Indicator.pine` -- Full codebase analysis (type definitions, grading functions, inversion call site, tooltip rendering, IFVG.new() sites)
- `.planning/phases/05-grading-system-remodel/05-CONTEXT.md` -- All locked decisions D-01 through D-12
- `strategy.md` section 6 -- Setup Rating System reference
- `docs/ISSUES.md` Issue 8 -- Grading remodel description

### Secondary (MEDIUM confidence)
- Memory: `feedback_pd_zone_approach.md` -- Pine Script v6 `var` global modification constraint
- Git history: commit `33e0085` confirming PD zone code removal

### Tertiary (LOW confidence)
None -- all findings verified against codebase.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- single file Pine Script, no dependencies
- Architecture: HIGH -- all code paths verified via codebase grep, all modification points identified
- Pitfalls: HIGH -- verified bugs (momentum AND/OR), verified missing fields (IFVG type), verified PD zone absence

**Research date:** 2026-04-12
**Valid until:** 2026-05-12 (stable -- Pine Script v6 and codebase structure unlikely to change)
