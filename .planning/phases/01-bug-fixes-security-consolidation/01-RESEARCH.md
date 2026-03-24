# Phase 1: Bug Fixes & Security Consolidation - Research

**Researched:** 2026-03-24
**Domain:** Pine Script v6 grading algorithm fixes, code deduplication, request.security() tuple consolidation
**Confidence:** HIGH

## Summary

Phase 1 addresses three distinct but interrelated issues in the IFVG Pro indicator: a hardcoded `fvg_singular = true` bug that inflates all grades by +1, duplicated HTF bias calculation logic across two render functions, and 14 individual `request.security()` calls consuming budget that future phases need.

The FVG singularity fix (FIX-01) is the most algorithmically complex task. It requires implementing a dual-check algorithm (proximity + overlap) against `g_fvg_array` to determine if an FVG at inversion time is truly singular. The codebase already has ATR-based tolerance patterns (used in EQH/EQL detection) that serve as a template. The HTF bias deduplication (FIX-02) is straightforward extraction of 13 lines of identical logic into a shared function. The security consolidation (FIX-03) is well-documented in existing STACK.md research -- replace 14 individual calls with 2 tuple calls, preserving the `int()` cast on `bar_index` returns.

All three fixes are code-only changes within the existing single file. No new types, inputs, or drawing objects are introduced. The success criterion of "zero visual regressions" means the planner must structure tasks so each fix can be verified independently on a TradingView chart.

**Primary recommendation:** Implement FIX-03 (security consolidation) first since it is the most mechanically straightforward and least likely to introduce behavioral changes, then FIX-02 (deduplication), then FIX-01 (singularity fix) which requires the most careful verification.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Implement a dual-check algorithm for FVG singularity: proximity check (no same-direction FVG within N bars) AND overlap check (zone doesn't overlap/nearly-overlap another same-direction FVG). Both must pass for singular = true.
- **D-02:** Natural grade recalibration after fix -- keep current grade thresholds unchanged (A+: score>=2, A: score>=1, A-: score>=0, etc). Let grades drop naturally for non-singular FVGs. This matches the strategy's intent where singular FVGs are genuinely higher quality.
- **D-03:** Extract the HTF bias calculation logic (currently duplicated at lines ~1838-1851 and ~2360-2370) into a single shared function. Both render_ifvg_boxes and render_dashboard should call this shared function.
- **D-04:** Consolidate 14 request.security() calls into tuples. Claude's discretion on exact tuple structure -- optimize for maximum consolidation (ideally 2 mega-tuples, 1 per timeframe) while maintaining code clarity. Pine Script v6 supports up to 127 tuple elements.

### Claude's Discretion
- Exact proximity threshold (N bars) for FVG singularity check -- choose based on typical FVG spacing patterns in the codebase
- Overlap tolerance (how close zones need to be to count as overlapping) -- use ATR-based threshold consistent with existing patterns
- Tuple variable naming and destructuring style -- follow existing codebase conventions
- Shared HTF bias function signature and placement within section structure

### Deferred Ideas (OUT OF SCOPE)
None -- discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FIX-01 | Fix hardcoded `fvg_singular = true` that inflates all quality scores by +1 | Dual-check algorithm pattern derived from existing EQH/EQL tolerance patterns; `g_fvg_array` iteration for proximity/overlap checks documented below |
| FIX-02 | Extract duplicated HTF bias calculation logic into a shared function | Exact duplication locations verified (lines 1838-1851 and 2360-2370); function extraction follows existing utility function patterns in Section 4 |
| FIX-03 | Consolidate request.security() calls into tuple syntax (14 to 2 calls, freeing 12 budget slots) | Tuple syntax verified against official Pine Script docs; 127-element limit is across ALL calls combined; `int()` cast required for bar_index |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- **Platform**: Pine Script v6 on TradingView -- no external dependencies, no build toolchain
- **Testing**: Visual verification only -- no automated test framework exists for Pine Script
- **Single file**: All code lives in `src/IFVG_Indicator.pine` -- must maintain section organization
- **No repainting**: All detection on `barstate.isconfirmed` only
- **Drawing limits**: Max 500 boxes, 500 lines, 500 labels -- FIFO cleanup required
- **Git commits**: No AI attribution, no Co-Authored-By tags, use "Phase X:" prefix style
- **Naming**: PascalCase for types, snake_case for functions, `i_` prefix for inputs, `g_` prefix for globals

## Standard Stack

This phase involves no new libraries or dependencies. All work is within Pine Script v6 built-in capabilities.

### Core APIs Used

| API | Purpose | Why Standard | Confidence |
|-----|---------|--------------|------------|
| `request.security()` with tuple syntax | Consolidate 14 HTF data calls into 2 | Official Pine Script v6 feature; documented at TradingView; max 127 tuple elements across all calls | HIGH |
| `array.size()` + `array.get()` | Iterate `g_fvg_array` for singularity checks | Already used extensively throughout codebase | HIGH |
| `ta.atr()` | ATR-based tolerance for overlap detection | Already the standard pattern for all tolerance calculations in this codebase | HIGH |

### Version Verification

No packages to verify -- Pine Script v6 is the sole runtime, controlled by TradingView. The indicator declares `//@version=6` at line 29.

## Architecture Patterns

### Current Section Layout (Relevant to This Phase)

```
Section 4  (lines 309-597)   - Utility functions     -- FIX-02: add get_htf_bias() here
Section 5B (lines 645-761)   - HTF FVG detection      -- FIX-03: consolidate security calls here
Section 7  (lines 1224-1464) - BE point & grading     -- FIX-01: calculate_grade() lives here
Section 8  (lines 1466-1636) - Inversion detection    -- FIX-01: check_inversions() calls grade
Section 10 (lines 1751-2288) - Rendering              -- FIX-02: render_ifvg_boxes() bias calc
Section 11 (lines 2308-2387) - Dashboard              -- FIX-02: render_dashboard() bias calc
```

### Pattern 1: FVG Singularity Detection (FIX-01)

**What:** A new function `is_fvg_singular()` that checks whether a given FVG is the only same-direction FVG in its neighborhood.

**When to use:** Called inside `check_inversions()` at line ~1595, replacing the hardcoded `true`.

**Algorithm design (dual-check per D-01):**

```pinescript
// Source: Derived from existing ATR-based tolerance patterns in codebase
is_fvg_singular(FVG source_fvg) =>
    bool singular = true
    int fvg_count = array.size(g_fvg_array)

    if fvg_count > 1 and not na(atr_value)
        for j = 0 to fvg_count - 1
            FVG other = array.get(g_fvg_array, j)

            // Skip self and opposite-direction FVGs
            if other.start_bar == source_fvg.start_bar and other.end_bar == source_fvg.end_bar
                continue
            if other.is_bullish != source_fvg.is_bullish
                continue
            if other.status != "active"
                continue

            // CHECK 1: Proximity -- is another same-direction FVG within N bars?
            int bar_distance = math.abs(source_fvg.end_bar - other.end_bar)
            bool too_close = bar_distance <= 5  // ~5 bars = typical FVG spacing

            // CHECK 2: Overlap -- do zones overlap or nearly overlap?
            float overlap_tolerance = atr_value * 0.1  // Same scale as EQH/EQL relative tolerance
            bool zones_overlap = source_fvg.top + overlap_tolerance >= other.bottom and
                                source_fvg.bottom - overlap_tolerance <= other.top

            // Both checks must PASS (i.e., be problematic) to mark as non-singular
            if too_close and zones_overlap
                singular := false
                break

    singular
```

**Key design decisions:**
- **Proximity threshold (N=5 bars):** Based on the 3-candle FVG pattern, two consecutive FVGs must be at minimum 3 bars apart. A threshold of 5 bars allows for a small gap between them. This is consistent with the strategy document section 7.1 which describes "multiple consecutive gaps."
- **Overlap tolerance (ATR * 0.1):** Matches the existing `i_relative_tolerance` default for EQH/EQL detection. This ensures zones that are nearly touching (within 10% of ATR) are treated as overlapping.
- **Both checks must fail:** Per D-01, both proximity AND overlap must be true to mark as non-singular. An FVG that is close in time but at a completely different price level is still singular. An FVG that overlaps in price but is far away in time is also still singular.

**Impact on grading:** With `fvg_singular = false`, quality_score loses +1 and gains -1 = net -2 change. For an FVG that was getting A (quality_score >= 1 with +1 from singular), removing singular drops it to quality_score -1 = B+. This is the intended natural recalibration per D-02.

### Pattern 2: HTF Bias Shared Function (FIX-02)

**What:** Extract duplicated bias logic into `get_htf_bias()` returning a string.

**Where:** Section 4 (Utility Functions, after line ~597), following the existing utility function pattern.

```pinescript
// Source: Extracted from render_ifvg_boxes (lines 1839-1851) and render_dashboard (lines 2362-2374)
get_htf_bias() =>
    string htf1_b = "neutral"
    string htf2_b = "neutral"
    if array.size(g_htf_ifvg_array) > 0
        IFVG htf1_r = array.get(g_htf_ifvg_array, array.size(g_htf_ifvg_array) - 1)
        htf1_b := htf1_r.status == "inverted" ? (htf1_r.is_bullish ? "bullish" : "bearish") : "neutral"
    if array.size(g_htf2_ifvg_array) > 0
        IFVG htf2_r = array.get(g_htf2_ifvg_array, array.size(g_htf2_ifvg_array) - 1)
        htf2_b := htf2_r.status == "inverted" ? (htf2_r.is_bullish ? "bullish" : "bearish") : "neutral"
    string result = htf1_b != "neutral" ? htf1_b : htf2_b
    result
```

**Callers:**
1. `render_ifvg_boxes()` -- replace lines 1839-1851 with `string combined_bias = get_htf_bias()`
2. `render_dashboard()` -- replace lines 2362-2370 with `string combined_bias = get_htf_bias()`

**Note:** The function accesses global arrays `g_htf_ifvg_array` and `g_htf2_ifvg_array` directly (not passed as parameters), which is consistent with how all other utility functions in Section 4 access globals.

### Pattern 3: Security Call Tuple Consolidation (FIX-03)

**What:** Replace 14 individual `request.security()` calls with 2 tuple calls (1 per HTF timeframe).

```pinescript
// Source: TradingView Pine Script docs + existing STACK.md research
// BEFORE: 14 individual calls (lines 653-680)
// AFTER: 2 tuple calls

// HTF 1 Data - Consolidated tuple (7 elements)
[htf_high, htf_low, htf_close, htf_high_2, htf_low_2, htf_bar_idx_raw, htf_atr] =
    request.security(syminfo.tickerid, i_htf_timeframe,
        [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
        lookahead = barmerge.lookahead_off)
int htf_bar_idx = int(htf_bar_idx_raw)

// HTF 2 Data - Consolidated tuple (7 elements)
[htf2_high, htf2_low, htf2_close, htf2_high_2, htf2_low_2, htf2_bar_idx_raw, htf2_atr] =
    request.security(syminfo.tickerid, i_htf_timeframe_2,
        [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
        lookahead = barmerge.lookahead_off)
int htf2_bar_idx = int(htf2_bar_idx_raw)
```

**Critical details:**
- Variable names remain identical to current code -- all downstream consumers (`detect_htf_fvg()`, `check_htf_inversions()`, `check_htf_mitigations()`, bar change detection at lines 671-676) work without changes.
- `int()` cast on `bar_index` return must be preserved -- `request.security()` returns all tuple elements as float-compatible types.
- The bar change tracking code (lines 670-676) stays untouched.
- Total tuple elements: 14 (7 per timeframe) out of 127 max = 11% used.
- Total `request.security()` calls: 2 out of 40 max = 5% used (down from 14 = 35%).

### Anti-Patterns to Avoid

- **Modifying grade thresholds alongside FIX-01:** Per D-02, thresholds stay unchanged. The grade distribution changes naturally from the singularity fix alone.
- **Passing arrays as parameters to `get_htf_bias()`:** Pine Script v6 supports passing arrays, but the existing codebase pattern is to access `g_*` globals directly from utility functions. Stay consistent.
- **Creating separate `request.security()` calls for bar_index vs OHLC:** There is no technical reason to separate them. The tuple handles mixed types (float + int-like values) correctly.
- **Adding `fvg_singular` as a field on the FVG type:** The singularity check needs to happen at inversion time against the current state of `g_fvg_array`, not at FVG creation time. An FVG's singularity status can change as other FVGs form or get mitigated.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| ATR-based tolerance thresholds | Custom absolute pixel/point thresholds | `atr_value * multiplier` (existing pattern) | Market-agnostic, already proven in EQH/EQL tolerance logic |
| Multiple-value HTF data retrieval | Individual `request.security()` calls | Tuple syntax `[a, b, c] = request.security(...)` | Saves 12 budget slots, no behavioral change, better performance |
| Bias string determination | Inline ternary chains | Dedicated `get_htf_bias()` function | Single source of truth, called from 2+ locations |

## Common Pitfalls

### Pitfall 1: Tuple Element Limit is Global, Not Per-Call
**What goes wrong:** Assuming each `request.security()` call can return up to 127 elements independently.
**Why it happens:** The limit documentation is easy to misread. The 127-element cap applies across ALL `request.*()` calls in the entire script combined.
**How to avoid:** After consolidation, this phase uses 14 elements. Future phases must track their additions against the 113 remaining. Document the budget in comments.
**Warning signs:** Compile error mentioning "tuple elements" limit.

### Pitfall 2: int() Cast on bar_index from request.security()
**What goes wrong:** `bar_index` is inherently `int`, but `request.security()` returns it as a float-compatible value. Without `int()` cast, comparisons like `htf_bar_idx != prev_htf_bar` may produce unexpected float comparison behavior.
**Why it happens:** `request.security()` does not preserve the original type of tuple elements.
**How to avoid:** Always cast: `int htf_bar_idx = int(htf_bar_idx_raw)`. The current code already does this -- preserve the pattern.
**Warning signs:** HTF bar change detection firing on every bar instead of only when HTF bars actually change.

### Pitfall 3: Singularity Check Timing (Inversion Time, Not Creation Time)
**What goes wrong:** Checking singularity when the FVG is first created and storing it on the FVG type.
**Why it happens:** It seems more efficient to compute once. But FVG singularity is contextual -- a singular FVG can become non-singular if another same-direction FVG forms nearby later.
**How to avoid:** Always compute `is_fvg_singular()` at inversion time inside `check_inversions()`, using the current state of `g_fvg_array`.
**Warning signs:** FVGs that form as singular retain their singular status even after cluster formation.

### Pitfall 4: Off-by-One in FVG Self-Comparison
**What goes wrong:** The singularity check iterates `g_fvg_array` to find nearby same-direction FVGs, but the source FVG being checked is also in `g_fvg_array`. Without a self-skip, every FVG matches itself.
**Why it happens:** The source FVG is still "active" in `g_fvg_array` when `check_inversions()` runs (it gets removed at line 1636 after grading).
**How to avoid:** Compare `start_bar` AND `end_bar` (or use array index) to skip the source FVG itself during iteration.
**Warning signs:** Every FVG is marked non-singular (always finds at least one "nearby" FVG -- itself).

### Pitfall 5: Shared Function Placement Relative to Global Declarations
**What goes wrong:** Placing `get_htf_bias()` in Section 4 before the HTF arrays are declared in Section 3.
**Why it happens:** Misunderstanding Pine Script's declaration order requirements.
**How to avoid:** Section 4 (lines 309-597) is after Section 3 (lines 284-307) where `g_htf_ifvg_array` and `g_htf2_ifvg_array` are declared. The function can safely reference them. Verify this before placement.
**Warning signs:** Pine Script compile error: "undeclared identifier."

### Pitfall 6: Tuple Destructuring Syntax
**What goes wrong:** Using the wrong syntax for tuple assignment, or trying to type-annotate individual tuple elements.
**Why it happens:** Pine Script tuple syntax is specific: `[a, b, c] = expression`.
**How to avoid:** Do NOT add type annotations to individual elements in the destructuring: `[float htf_high, float htf_low, ...]` is not valid. Assign to untyped names, then cast/annotate separately if needed.
**Warning signs:** Compile error on the tuple assignment line.

## Code Examples

### FIX-01: Integrating Singularity Check into check_inversions()

```pinescript
// Source: Current code at line 1595 in src/IFVG_Indicator.pine
// BEFORE:
bool fvg_singular = true  // Assuming singular for now

// AFTER:
bool fvg_singular = is_fvg_singular(fvg)

// Where is_fvg_singular() is defined in Section 7 (near calculate_grade)
// or Section 4 (utility functions) -- consistent with function placement patterns
```

### FIX-02: Replacing Duplicated Bias Code in render_ifvg_boxes()

```pinescript
// Source: Current code at lines 1838-1851 in src/IFVG_Indicator.pine
// BEFORE (13 lines):
string htf1_b = "neutral"
string htf2_b = "neutral"
if array.size(g_htf_ifvg_array) > 0
    IFVG htf1_r = array.get(g_htf_ifvg_array, array.size(g_htf_ifvg_array) - 1)
    htf1_b := htf1_r.status == "inverted" ? (htf1_r.is_bullish ? "bullish" : "bearish") : "neutral"
if array.size(g_htf2_ifvg_array) > 0
    IFVG htf2_r = array.get(g_htf2_ifvg_array, array.size(g_htf2_ifvg_array) - 1)
    htf2_b := htf2_r.status == "inverted" ? (htf2_r.is_bullish ? "bullish" : "bearish") : "neutral"
string combined_bias = htf1_b != "neutral" ? htf1_b : htf2_b

// AFTER (1 line):
string combined_bias = get_htf_bias()
```

### FIX-03: Full Tuple Consolidation Block

```pinescript
// Source: TradingView official docs + existing STACK.md pattern
// Replaces lines 653-680 in src/IFVG_Indicator.pine

// HTF 1 Data - Consolidated tuple (7 elements)
[htf_high, htf_low, htf_close, htf_high_2, htf_low_2, htf_bar_idx_raw, htf_atr] =
    request.security(syminfo.tickerid, i_htf_timeframe,
        [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
        lookahead = barmerge.lookahead_off)
int htf_bar_idx = int(htf_bar_idx_raw)

// HTF 2 Data - Consolidated tuple (7 elements)
[htf2_high, htf2_low, htf2_close, htf2_high_2, htf2_low_2, htf2_bar_idx_raw, htf2_atr] =
    request.security(syminfo.tickerid, i_htf_timeframe_2,
        [high, low, close, high[2], low[2], bar_index, ta.atr(i_fvg_atr_period)],
        lookahead = barmerge.lookahead_off)
int htf2_bar_idx = int(htf2_bar_idx_raw)

// Track HTF bar changes to detect new HTF bars (unchanged)
var int prev_htf_bar = na
var int prev_htf2_bar = na
bool htf_bar_changed = na(prev_htf_bar) or htf_bar_idx != prev_htf_bar
bool htf2_bar_changed = na(prev_htf2_bar) or htf2_bar_idx != prev_htf2_bar
prev_htf_bar := htf_bar_idx
prev_htf2_bar := htf2_bar_idx
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Individual `request.security()` per value | Tuple returns `[a, b, c] = request.security(...)` | Pine Script v4+ (2020) | Reduces call count dramatically; v6 adds dynamic requests |
| `security()` function name | `request.security()` namespace | Pine Script v5 (2021) | Namespaced under `request.*` family |
| Static `request.security()` at global scope only | Dynamic requests in conditionals | Pine Script v6 (2024) | Can use series arguments and place inside `if` blocks |

**Note on v6 dynamic requests:** While v6 allows `request.security()` inside conditional blocks, this phase should keep them at global scope (matching the current pattern) since the HTF data is needed unconditionally. Dynamic requests are relevant for future phases (e.g., conditionally loading PD zone data).

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None -- Pine Script has no automated test framework |
| Config file | None |
| Quick run command | Manual: paste into TradingView Pine Script Editor, apply to chart |
| Full suite command | Manual: verify on multiple charts (ES 5min, BTCUSD 15min, EURUSD 1H) |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Verification Method | Automated? |
|--------|----------|-----------|---------------------|------------|
| FIX-01 | Grades reflect actual setup quality -- no single grade exceeds 40% of setups | manual-visual | Apply to ES 5min chart, count grade distribution in dashboard or by scrolling through setups. Compare before/after the fix. | No |
| FIX-01 | Non-singular FVGs (consecutive/overlapping) get lower grades | manual-visual | Find a price region with multiple consecutive FVGs, verify their IFVG grades are lower (B/B-) vs isolated FVGs (A/A-) | No |
| FIX-02 | HTF bias in dashboard matches HTF bias used for LTF filtering | manual-visual | Enable HTF filter, verify dashboard "HTF Bias" row shows same direction as the filter is applying (bullish shows only bullish setups) | No |
| FIX-02 | Rendering unchanged after extraction | manual-visual | Toggle HTF filter on/off, verify identical behavior to pre-fix version | No |
| FIX-03 | Indicator compiles and loads without errors | manual-compile | Paste into TradingView, verify no compile errors | No |
| FIX-03 | HTF FVG detection, inversion, and mitigation unchanged | manual-visual | Compare HTF FVG boxes, IFVG boxes, and dashboard on same chart before/after. Side-by-side screenshots. | No |
| FIX-03 | request.security() call count is 2 | manual-count | Count `request.security(` in source code = exactly 2 | No (but trivially verifiable via grep) |
| ALL | No visual regressions in FVG/IFVG rendering or HTF overlays | manual-visual | Full chart comparison on 3+ instruments/timeframes | No |

### Sampling Rate
- **Per task:** Compile in TradingView and visually verify on at least 1 chart
- **Per fix completion:** Verify on 2+ charts across different instruments
- **Phase gate:** Full verification on 3 instruments (equity, crypto, forex) across 2 timeframes each

### Wave 0 Gaps
None -- there is no automated test infrastructure for Pine Script and none can be created. All validation is manual visual verification on TradingView charts. This is a platform constraint, not a gap that can be filled.

## Open Questions

1. **Proximity threshold for FVG singularity (N bars)**
   - What we know: FVGs are 3-candle patterns, so minimum spacing is 3 bars. Strategy doc section 7.1 describes "multiple consecutive gaps" as a special case.
   - What's unclear: Optimal threshold depends on typical FVG density per instrument/timeframe. 5 bars is a reasonable starting point but may need tuning.
   - Recommendation: Start with N=5 bars. This is a Claude's Discretion item. Can be adjusted post-verification if grade distribution doesn't look right.

2. **FVG singularity: should inverted/mitigated FVGs count?**
   - What we know: `g_fvg_array` contains only "active" FVGs (inverted and mitigated are removed). So the singularity check naturally only considers active FVGs.
   - What's unclear: Should recently-inverted FVGs (now in `g_ifvg_array`) also count as "nearby" for singularity purposes? The strategy doc focuses on "series of gaps" at the time of formation.
   - Recommendation: Only check `g_fvg_array` (active FVGs). An FVG that was already inverted is no longer "in the way" -- it has already been consumed by price.

3. **Actual request.security() count discrepancy**
   - What we know: The actual code has 14 calls (verified by grep). REQUIREMENTS.md says "16->2".
   - What's unclear: Whether the original count was 16 at some point and 2 were removed, or if it was always 14.
   - Recommendation: Use the actual count of 14 in all planning. After consolidation: 2 calls. Budget freed: 12 slots (not 14 as some docs state).

## Sources

### Primary (HIGH confidence)
- `src/IFVG_Indicator.pine` lines 653-680 -- Actual request.security() calls (14 total, verified by code inspection)
- `src/IFVG_Indicator.pine` lines 1398-1464 -- calculate_grade() function with quality_score logic
- `src/IFVG_Indicator.pine` lines 1595 -- Hardcoded `fvg_singular = true`
- `src/IFVG_Indicator.pine` lines 1838-1851, 2360-2374 -- Duplicated HTF bias calculation
- `.planning/research/STACK.md` -- Tuple consolidation patterns and budget analysis
- `.planning/codebase/CONCERNS.md` -- Bug documentation and impact analysis
- [TradingView Pine Script Docs: Limitations](https://www.tradingview.com/pine-script-docs/writing/limitations/) -- 40 call limit, 127 tuple element limit (across ALL calls)
- [TradingView Pine Script Docs: Other Timeframes and Data](https://www.tradingview.com/pine-script-docs/concepts/other-timeframes-and-data/) -- Tuple syntax for request.security()

### Secondary (MEDIUM confidence)
- [TradingView Blog: Tuple Support for Security Function](https://www.tradingview.com/blog/en/tuple-support-for-the-security-function-in-pine-script-18316/) -- Original announcement of tuple support
- [LuxAlgo: 5 Causes of Slow Pine Scripts](https://www.luxalgo.com/blog/5-causes-of-slow-pine-scripts-on-tradingview/) -- Performance data showing consolidation reduces execution time
- [TradersPost: Pine Script v6 Dynamic Requests](https://blog.traderspost.io/article/pine-script-v6-dynamic-requests) -- v6-specific dynamic request features

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- Pine Script v6 built-ins, no external dependencies, all patterns verified in codebase
- Architecture: HIGH -- All code locations verified by direct reading, patterns derived from existing codebase conventions
- Pitfalls: HIGH -- Based on actual code inspection and official TradingView documentation constraints

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable -- Pine Script v6 APIs change infrequently)
