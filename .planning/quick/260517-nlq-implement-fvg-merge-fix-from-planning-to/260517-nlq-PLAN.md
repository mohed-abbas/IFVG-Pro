---
phase: quick-260517-nlq
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - src/IFVG_Indicator.pine
autonomous: false
requirements:
  - FVG-MERGE-OPPCOLOR
must_haves:
  truths:
    - "Two same-direction FVGs within 5 bars with NO opposite-color candle between them still merge (no regression)."
    - "Two same-direction FVGs within 5 bars separated by >=1 opposite-color candle in the strict-between range no longer merge."
    - "Doji bars (close == open) between two same-direction FVGs do not block the merge."
    - "Bearish-side behavior is symmetric (green bar blocks bearish merge)."
    - "The merge_with_existing_fvg() function remains the only code path affected; no new request.security() calls; no changes to grading, IFVG creation, or singularity logic."
  artifacts:
    - path: "src/IFVG_Indicator.pine"
      provides: "Updated merge_with_existing_fvg() with opposite-color scan over [existing.end_bar+1, new_fvg.start_bar-1]"
      contains: "opposite_found"
  key_links:
    - from: "merge_with_existing_fvg() (src/IFVG_Indicator.pine ~line 538)"
      to: "g_fvg_array entries pushed by detect_fvg() / detect_fvg series caller"
      via: "early-exit (continue scan) when opposite_found is true; merge proceeds only when no opposite-color bar in strict-between range"
      pattern: "opposite_found"
---

<objective>
Implement the FVG merge rule tightening defined in `.planning/todos/pending/tighten-fvg-merge-opposite-color-break.md`: block a same-direction FVG merge when any opposite-color candle exists strictly between the two FVGs' 3-candle windows. Dojis are neutral.

Purpose: The current temporal-only merge absorbs gaps across visible counter-direction bars, producing oversized IFVG zones with bloated stop-losses. This fix restores tighter, ICT-correct setups without changing any other system.

Output: A single-file edit inside `merge_with_existing_fvg()` at `src/IFVG_Indicator.pine:538`, plus a manual TradingView visual verification.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@./CLAUDE.md
@.planning/todos/pending/tighten-fvg-merge-opposite-color-break.md
@.planning/notes/fvg-merge-rule-decision.md
@src/IFVG_Indicator.pine

<interfaces>
<!-- Key facts the executor needs. The function lives at line 538; the FVG type is defined in Section 1 lines 46-56. -->

Function under edit (src/IFVG_Indicator.pine:538-564, current body):

merge_with_existing_fvg(FVG new_fvg) =>
    bool merged = false
    int fvg_count = array.size(g_fvg_array)
    if fvg_count > 0
        for j = fvg_count - 1 to 0
            FVG existing = array.get(g_fvg_array, j)
            if existing.is_bullish == new_fvg.is_bullish and existing.status == "active"
                int bar_distance = int(math.abs(new_fvg.end_bar - existing.end_bar))
                if bar_distance <= 5
                    // Merge: extend existing FVG to encompass new one
                    ...
                    merged := true
                    break
    merged

Relevant FVG fields used: `is_bullish` (bool), `status` (string, "active"|"inverted"|"mitigated"),
`start_bar` (int — bar_index of first bar of the 3-candle window), `end_bar` (int — bar_index of
the third/confirming bar), `top`, `bottom`, `mid`, `box_id`, `label_id`.

Pine v6 bar-offset rule: to read OHLC at absolute bar position k (where k is a value of
`bar_index` at some prior bar), convert to a historical offset:
    offset = bar_index - k
then access via `open[offset]` and `close[offset]`. `offset == 0` is the current bar.

Strict-between scan range, expressed as absolute bar indices (inclusive):
    scan_from = existing.end_bar + 1
    scan_to   = new_fvg.start_bar - 1
If `scan_to < scan_from`, the range is empty and the merge proceeds (no scan).

Opposite-color rules:
    bullish merge candidate: red bar iff `close[offset] < open[offset]`
    bearish merge candidate: green bar iff `close[offset] > open[offset]`
    doji (`close[offset] == open[offset]`): neutral, never blocks.
</interfaces>
</context>

<tasks>

<task type="auto" tdd="false">
  <name>Task 1: Add opposite-color scan inside merge_with_existing_fvg()</name>
  <files>src/IFVG_Indicator.pine</files>
  <behavior>
    - When `bar_distance &lt;= 5` and `existing.is_bullish == new_fvg.is_bullish` and `existing.status == "active"`, compute `scan_from = existing.end_bar + 1` and `scan_to = new_fvg.start_bar - 1`.
    - If `scan_to &lt; scan_from`: skip the scan (adjacent FVGs) — proceed to merge as today.
    - Otherwise, iterate `k` from `scan_from` to `scan_to` inclusive. For each `k`, compute `offset = bar_index - k` and read `open[offset]` / `close[offset]`.
    - Bullish candidate: set `opposite_found := true` when `close[offset] &lt; open[offset]`.
    - Bearish candidate: set `opposite_found := true` when `close[offset] &gt; open[offset]`.
    - Doji bars (`close[offset] == open[offset]`) MUST NOT set `opposite_found`.
    - If `opposite_found` is true after the scan: DO NOT merge with this `existing`; continue the outer loop to the next (older) candidate FVG in `g_fvg_array`.
    - If `opposite_found` is false: perform the existing merge logic unchanged (extend top/bottom/mid/end_bar, delete and clear box_id/label_id, set `merged := true`, break).
    - No changes to grading, IFVG creation, singularity, dashboard, rendering, or HTF code paths. No new `request.security()` calls.
  </behavior>
  <action>
    Open `src/IFVG_Indicator.pine` and edit `merge_with_existing_fvg()` starting at line 538. Implement per the behavior block above, honoring Pine Script v6 syntax rules from `./CLAUDE.md`:

    1. Declare `bool opposite_found = false` immediately at the top of the inner `if bar_distance &lt;= 5` block (before the existing merge logic).
    2. Compute `int scan_from = existing.end_bar + 1` and `int scan_to = new_fvg.start_bar - 1` on their own lines (right-hand side on the same line as `=`; never leave `=` as the last token on a line).
    3. Guard the scan with `if scan_to &gt;= scan_from`. Inside, use `for k = scan_from to scan_to` with a CONTIGUOUS body (no blank lines inside the `for` block — this is a v6 parser hazard called out in CLAUDE.md rule 1).
    4. Inside the loop body, compute `int offset = bar_index - k` on one line, then use nested `if` blocks (CLAUDE.md rule 4 prefers nested `if` over `continue`):
        - `if new_fvg.is_bullish` then `if close[offset] &lt; open[offset]` then `opposite_found := true`
        - `if not new_fvg.is_bullish` then `if close[offset] &gt; open[offset]` then `opposite_found := true`
       Do NOT introduce multi-line `and`/`or` chains; if combining, wrap the whole expression in parentheses (CLAUDE.md rule 2).
    5. After the scan block, guard the existing merge body with `if not opposite_found`. The existing merge body (extend top/bottom/mid/end_bar, delete box_id/label_id, set `merged := true`, `break`) moves inside this guard with NO behavior change. Keep the `int(math.max(...))` cast on `end_bar` and `int(math.abs(...))` on `bar_distance` exactly as they are (CLAUDE.md rule 3).
    6. When `opposite_found` is true, DO NOT `break` — the outer `for j` loop must continue scanning older entries in `g_fvg_array`. (If an older same-direction FVG further back has a clean strict-between range, the rule does not prescribe merging with it; in practice the 5-bar distance gate filters those, but the loop structure must not be cut short by an opposite-color hit on a closer candidate.)
    7. Do not add any user input, any new global, or any new `request.security()` call. Do not touch other functions.

    Pine v6 specific reminders during the edit:
    - Operator-at-end-of-line for any line continuation (CLAUDE.md rule 5).
    - Never leave `=` as the last token of a line (CLAUDE.md rule 6).
    - Keep section banners (`// ───`) intact above and below the function.
  </action>
  <verify>
    <automated>grep -n "opposite_found" src/IFVG_Indicator.pine | grep -v '^[[:space:]]*//' | grep -c opposite_found</automated>
    Expected: `>= 3` matches (declaration + at least two assignment sites for bullish and bearish branches).

    Secondary structural check (run all in sequence; each must succeed):

    ```
    grep -n "merge_with_existing_fvg" src/IFVG_Indicator.pine
    grep -n "scan_from" src/IFVG_Indicator.pine
    grep -n "scan_to" src/IFVG_Indicator.pine
    grep -n "bar_index - k" src/IFVG_Indicator.pine
    grep -c "if not opposite_found" src/IFVG_Indicator.pine
    ```

    Expected:
    - `merge_with_existing_fvg` appears at least at its definition and at its existing call site.
    - `scan_from` and `scan_to` each appear at least 2 times (assignment + use).
    - `bar_index - k` appears at least once (offset conversion).
    - `if not opposite_found` appears exactly 1 time (the guard wrapping the original merge body).

    Pine v6 syntax sanity check (no trailing `=` and no blank lines inside the new `for`):

    ```
    awk '/merge_with_existing_fvg/,/^merged$/' src/IFVG_Indicator.pine | grep -nE '=[[:space:]]*$' | grep -v '//'
    ```

    Expected: zero matches (no line ends with bare `=`).

    Manual confirmation: open `src/IFVG_Indicator.pine` and re-read lines around 538–600 to confirm no blank lines exist inside the `for k = scan_from to scan_to` body or inside any nested `if` body within it.
  </verify>
  <done>
    - `merge_with_existing_fvg()` contains an opposite-color scan over the strict-between range `[existing.end_bar+1, new_fvg.start_bar-1]`.
    - When `opposite_found` is true, the merge body is skipped for that `existing`; otherwise behavior is byte-identical to today.
    - All Pine v6 syntax rules from `./CLAUDE.md` are honored (no blank lines in `for`/`if` bodies, no trailing `=`, `int()` casts retained, no multi-line `and`/`or` without parens, operator-at-end-of-line for any continuations).
    - No changes outside this function. No new `request.security()` calls. No new user inputs.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <name>Task 2: TradingView visual verification</name>
  <what-built>
    `merge_with_existing_fvg()` now blocks merging across opposite-color candles in the strict-between range, while preserving merges across continuous same-direction impulses and doji-only gaps.
  </what-built>
  <how-to-verify>
    1. Copy the entire contents of `src/IFVG_Indicator.pine` into the TradingView Pine Script Editor.
    2. Compile — confirm no Pine v6 errors (especially no "end of line without line continuation" errors around the `merge_with_existing_fvg` region).
    3. Apply to chart. Test on NQ1! or ES1! 15m, and BTCUSD 1H (per the TODO acceptance criteria).
    4. Find a bullish FVG cluster with at least one red candle between gap groups within 5 bars. Confirm: TWO (or more) separate bullish boxes appear where previously a single oversized merged box did. Acceptance criterion #1 and #3.
    5. Find a continuous bullish impulse with two same-direction FVGs and NO red candle between them (or only doji bars between them). Confirm the merge still happens — one combined box. Acceptance criterion #2 and #5.
    6. Repeat the symmetric check on a bearish setup: green candle between two bearish FVGs blocks the merge; absence of green candles preserves the merge. Acceptance criterion #4.
    7. Spot-check that A+/A IFVG counts have not collapsed to zero across a few historical sessions — some setups may be reclassified (expected, per decision record).
    8. Confirm no new repainting (all behavior still gated by `barstate.isconfirmed` upstream of `detect_fvg`/merge — no changes there).
  </how-to-verify>
  <resume-signal>Type "approved" or paste a screenshot of any regression observed.</resume-signal>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| TradingView runtime → Pine script | Script reads OHLC via `open[offset]` / `close[offset]` and accesses `g_fvg_array` and `bar_index`. No external/user-supplied data crosses any boundary in this change. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-quick-260517-01 | Tampering | `merge_with_existing_fvg()` offset arithmetic | mitigate | Convert absolute `bar_index`-based positions to historical offsets exactly as documented in `<interfaces>` (`offset = bar_index - k`). Bounded by `bar_distance <= 5`, so `offset` is always within `[1, 5]` for the strict-between range — well under `max_bars_back=500`. |
| T-quick-260517-02 | Denial of Service | Inner scan loop | accept | Inner loop iterates at most 5 bars (bar_distance ≤ 5). No new arrays, no new `request.security()` calls. Resource impact: negligible. |
| T-quick-260517-03 | Information Disclosure | Visual output (FVG boxes) | accept | More small boxes may render after the fix, but max box cap `max_boxes_count=500` and `cleanup_fvg_array()` FIFO continue to bound output. No leakage of internal state to chart consumers. |
| T-quick-260517-SC | Tampering | npm/pip/cargo installs | accept | No package installs in this task. Pine Script has no package manager; deployment is manual copy-paste to TradingView. |
</threat_model>

<verification>
- Static (automated grep checks): see `<verify>` block in Task 1.
- Dynamic (manual): TradingView visual regression per Task 2 against the chart described in `.planning/todos/pending/tighten-fvg-merge-opposite-color-break.md` (NQ1!/ES1! 15m and BTCUSD 1H).
- Cross-check against the decision record's acceptance criteria 1–7 — all must hold.
</verification>

<success_criteria>
- [ ] `merge_with_existing_fvg()` contains an opposite-color scan over `[existing.end_bar+1, new_fvg.start_bar-1]`.
- [ ] Bullish merges are blocked by any single red bar (`close < open`) in the strict-between range.
- [ ] Bearish merges are blocked by any single green bar (`close > open`) in the strict-between range.
- [ ] Doji bars (`close == open`) never block the merge.
- [ ] Adjacent FVGs (empty strict-between range) still merge.
- [ ] All Pine v6 syntax rules from `./CLAUDE.md` are honored (no blank lines in `for`/`if` bodies, no trailing `=`, `int()` casts retained, multi-line boolean expressions wrapped in parens).
- [ ] Only `src/IFVG_Indicator.pine` is modified. No new `request.security()` calls. No new user inputs. No changes to grading, IFVG creation, singularity, or HTF code paths.
- [ ] TradingView visual checks confirm split clusters where previously merged, and intact merges on continuous impulses and doji-only gaps.
</success_criteria>

<output>
Create `.planning/quick/260517-nlq-implement-fvg-merge-fix-from-planning-to/260517-nlq-SUMMARY.md` when done, summarizing the exact line range changed, the before/after diff of `merge_with_existing_fvg()`, and the TradingView verification result.
</output>
