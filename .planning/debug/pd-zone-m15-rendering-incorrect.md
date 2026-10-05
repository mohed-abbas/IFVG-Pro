---
slug: pd-zone-m15-rendering-incorrect
status: resolved
trigger: User-reported visual bug on M15 chart with PD timeframe = M15
created: 2026-05-11
goal: find_and_fix
tdd_mode: false
---

# Debug Session: PD Zone M15 Rendering Incorrect

## Symptoms

On M15 chart with PD timeframe = M15, the PD Zone is rendering incorrectly. Lower timeframes intermittently show/hide the zone.

### Screenshot diagnostic label readout
- TF=15 chart=15
- src=CHART
- pd_sw_H/L=50/50
- pd_liq=50, chart_liq=35
- valid ITH/ITL=2/12
- swept ITH/ITL=13/7
- range=YES

### Visual symptom
The orange/yellow PD range lines span ~28,300 to ~29,500 — far too wide for an M15 dealing range with price near ~29,437.

## Current Focus

**hypothesis (final):**
1. F1 (src=CHART) — stale screenshot. Code now always says `src=PD (relation)`. No source-selection bug.
2. F2 (aggressive sweep marking) — `check_pd_sweeps()` has NO close-through bug. Real cause is sweep-threshold sensitivity: ANY 1-tick wick above + close below permanently marks ITH swept. On M15 chart with M15 PD, every minor wick burns levels.
3. F3 (range too wide) — pair-search confirmed broken. With only 2 valid ITH and 7 valid ITL, the algorithm grabs newest valid ITH (~29,500) and walks down ITL candidates, picking the first ITL below it — which may be an ancient swing at ~28,300. Needs price-containment constraint.

## Prior Context

Recent on-disk (uncommitted) edits already in file:
1. `check_liquidity_sweeps` ITH/ITL close-through invalidation removed (lines 1214-1222 now scope close-through to EQH/EQL only).
2. Main loop Step 4C uses candidate-list pair-search (lines 2770-2796).
3. `select_dealing_range_source()` (line 1289) unconditionally returns `g_pd_liquidity_array`.
4. Diagnostic label `g_pd_debug_label` at lines 2887-2920.

## Evidence

### F1: `src=CHART` is stale — current label always shows `src=PD (relation)`

Lines 2895-2898 produce `dbg_src = "PD (" + dbg_relation + ")"` unconditionally. The string `"CHART"` does not appear anywhere in the label code. The user's screenshot predates the source-unification edit. **Action: no source-logic fix; the unconditional `select_dealing_range_source()` change has taken effect.**

### F2: `check_pd_sweeps()` is correct on close-through — only wick-and-revert marks swept

Lines 1266-1282: `check_pd_sweeps()` only has wick-and-revert detection (no close-through invalidation). So 13/7 swept counts come from genuine wick-and-revert events.

On M15 chart with PD=M15, every M15 candle's high that pokes above a recent ITH and closes below marks it swept permanently. This is too aggressive: a single tick wick should not nuke a structural level. Need a minimum wick-protrusion threshold (e.g. fraction of ATR) before counting as a sweep.

### F3: Pair-search picks newest ITH + first ITL below it — wide range bug confirmed

Lines 2770-2796:

```pine
for i = array.size(src) - 1 to 0  // newest-to-oldest
    Liquidity liq = array.get(src, i)
    if liq.is_valid and not liq.is_swept
        if (liq.liq_type == "PD_ITH" or liq.liq_type == "ITH")
            array.push(ith_candidates, liq)  // newest-first
        if (liq.liq_type == "PD_ITL" or liq.liq_type == "ITL")
            array.push(itl_candidates, liq)  // newest-first

// pair newest ITH with first ITL below it
for i = 0 to n_ith - 1
    ith = ith_candidates[i]
    for j = 0 to n_itl - 1
        itl = ith_candidates[j]
        if ith.level > itl.level
            sel_ith := ith
            sel_itl := itl
            break
    if not na(sel_ith): break
```

Picks the *newest valid ITH* (call it 29,500) then walks ITL candidates newest-to-oldest, taking the first whose level < ITH level. With most recent ITLs swept, the only surviving valid ITL may be ancient (28,300). Result: a 1200-point range straddling all of recent history.

**Fix:** Require the chosen pair to *contain current close* (so the range is meaningful for current price action). If multiple pairs contain price, prefer the **narrowest** (most recent meaningful structure). If none contain price, fall back to narrowest pair where ITH > price > ITL is closest.

## Resolution

### Root cause
Two real bugs identified:

1. **Pair-search has no recency / price-containment constraint.** Picks first ITH (newest) paired with any ITL below it, even if that ITL is hundreds of bars old, producing a wide nonsense range.
2. **Sweep threshold is binary (any wick above + close below = swept).** On chart-TF == PD-TF on a low timeframe (M15), normal noise wicks permanently burn levels.

### Fix applied

**Fix 1 (F3 — primary visual bug):** Rewrote Step 4C pair-search to choose narrowest valid (ITH > close > ITL) range containing current price. Falls back to narrowest pair regardless of containment if none contain price.

**Fix 2 (F2 — sweep sensitivity):** Added ATR-fraction minimum wick-protrusion gate to `check_pd_sweeps()`. A wick must protrude beyond the level by at least `i_pd_sweep_min_atr_mult` * chart-TF ATR to count as a sweep. Default 0.05 ATR — large enough to filter noise wicks, small enough to catch real sweeps.

**Fix 3 (F1 — debug label cosmetics):** No code change. Stale screenshot — current code is correct.

### Files changed
- `src/IFVG_Indicator.pine` — Step 4C pair-search rewrite, `check_pd_sweeps()` ATR gate, new input `i_pd_sweep_min_atr_mult`.

### Verification steps for user
1. Copy updated `src/IFVG_Indicator.pine` into TradingView Pine Editor.
2. Apply to M15 chart with `PD Timeframe = 15` (default ATR mult = 0.05).
3. Confirm debug label now shows `src=PD (PD=chart)` (was stale "CHART" from prior screenshot).
4. Confirm PD range lines no longer span 28,300–29,500. Range should now contain current price tightly.
5. Confirm `valid ITH/ITL` counts in label increase (fewer false sweeps).
6. Try with PD Timeframe = 1H on M15 chart — range should reflect 1H structure.
7. If sweeps still too aggressive: increase `i_pd_sweep_min_atr_mult` in the new "PD Zones" input group.

---

## Cycle 2 — narrowest-containing heuristic regressed, replaced with newest+walkback

### New evidence (post-cycle-1 fixes)

User tested cycle-1 build (narrowest-containing-price + ATR-gated sweep + new input + source-unification + debug label) across 4 symbols on 5m chart with PD timeframe = 15m:

| Symbol | `i_pd_swing_lookback` | Result | Range span | Valid ITH/ITL | Range % |
|---|---|---|---|---|---|
| NQ1! | 5 | working | — | — | — |
| NQ1! | 6+ | **BROKEN** ("just collapses") | — | — | — |
| GBPJPY | 5 | **BROKEN** | 213.48 → 216 (~2.5 pts), tucked at right edge | 2 / 9 | 27% (DISCOUNT) |
| XAUUSD | 5 | working | 4650 → 4750 (~100 pts) | 5 / 7 | 26% (PREMIUM) |
| BTCUSD | 5 | working | 80,400 → 82,500 (~2100 pts) | 2 / 8 | 79% (PREMIUM) |

Key observation: GBPJPY has nearly identical valid ITH/ITL counts to BTC (2/9 vs 2/8) yet collapses to a micro-range while BTC produces a structural range. The difference is **not** sweep aggressiveness — it's WHICH pair the algorithm chooses.

### Investigation

Re-read Step 4C (lines 2772–2816 pre-fix). The narrowest-containing-price loop:

```pine
if contains_price and width < best_contain_width
    best_contain_width := width
    best_contain_ith := ith
    best_contain_itl := itl
```

actively prefers tight micro-ranges that happen to envelope current price. On GBPJPY the most-recent unswept ITH/ITL pair (~213.48 → ~216) sat right around price, so the algorithm picked it — even though valid ITLs at ~211.5 (recent structural lows) and older ITHs at ~216+ existed and would form the true dealing range a trader expects.

The fallback branch ("narrowest pair overall if none contain price") has the same bias.

Strategy doc (`strategy.md` §5.3) describes Premium/Discount as "based on Daily Range" — the structural recent range, not a micro-consolidation containing price.

### Root cause (cycle 2)

**Selection heuristic is wrong.** Preferring "narrowest containing price" biases toward micro-consolidations and ignores the structural dealing range. ICT methodology defines PD by the **most recent unswept liquidity on each side**, regardless of whether price currently sits inside the range. Sweeps then trigger rotation — not "price is outside" → "shrink the range."

The `i_pd_swing_lookback` regression at 6+ on NQ is a downstream effect of the same bug: stricter pivot detection on noisy LTF (NQ, GBPJPY) clusters the most-recent valid pairs tightly; narrowest-containing then latches onto the cluster. Cleaner symbols (Gold, BTC) produce widely-spaced pivots, so narrowest-containing happens to still pick something reasonable.

### Fix applied (cycle 2)

Replaced Step 4C selection block (`src/IFVG_Indicator.pine` lines 2772–2822) with **newest-newest + cross-walkback** heuristic:

1. Collect unswept ITH and ITL candidates in newest-first order (unchanged collection logic).
2. Start with `ith = candidates[0]`, `itl = candidates[0]` (most recent on each side).
3. If `ith.level > itl.level` → done.
4. Otherwise (inverted anchor): advance whichever candidate is chronologically **older** (smaller `bar_idx`) to its next-older instance. Repeat until non-crossing or candidates exhausted.
5. If walkback exhausts candidates, leave `sel_ith`/`sel_itl` as `na` → range marked invalid (downstream branch at line 2823 clears drawings).

No "containing price" preference. No "narrowest" preference. Pure structural recency.

### Files changed

- `src/IFVG_Indicator.pine` — Step 4C selection block replaced. ATR-gated sweep, new input, source-unification, and debug label from cycle 1 unchanged.

### Verification steps for user

1. Copy updated `src/IFVG_Indicator.pine` into TradingView.
2. Apply to **GBPJPY 5m, PD TF = 15** — range should now anchor on the most-recent valid M15 swing high above price and the most-recent valid M15 swing low below the recent action (NOT the ~213.48 micro-bottom).
3. **NQ1! 5m, PD TF = 15, swing lookback = 6**, then 7, then 8 — range should stay structurally meaningful (no collapse).
4. **XAUUSD 5m, PD TF = 15** — should still produce ~4650→4750 range (regression check).
5. **BTCUSD 5m, PD TF = 15** — should still produce ~80,400→82,500 range (regression check).
6. Debug label `valid ITH/ITL` counts unchanged from cycle 1 (selection change does not affect sweep marking).
7. If a pair-cross occurs (e.g. all newest ITHs sit below all newest ITLs due to fast trend), the range should temporarily disappear rather than render an inverted box — confirm by watching strong trending bars.

### Notes on cycle-1 fixes (unchanged)

- `check_pd_sweeps()` ATR-protrusion gate (`i_pd_sweep_min_atr_mult`, default 0.05) retained.
- `select_dealing_range_source()` still unconditionally returns `g_pd_liquidity_array`.
- `g_pd_debug_label` still rendered each `barstate.islast`.

---

## Cycle 3 — lookback-driven regression traced to PD pivot ingestion (lag + close-through gap)

### New evidence (post-cycle-2)

User retested cycle-2 build on 5m chart with PD TF = 15:

| Symbol | Cycle-1 breakpoint | Cycle-2 breakpoint | Cycle-2 result |
|---|---|---|---|
| NQ1! | lookback >=6 | lookback >=10 | works 5..9, breaks 10+ |
| GBPJPY | broken at all lookbacks | lookback >=6 | works at 5, breaks 6+ |
| XAUUSD | works | works | works (regression check OK) |
| BTCUSD | works | works | works (regression check OK) |

Cycle 2 moved the needle but the symptom did not resolve. The breakpoint scales with symbol volatility (NQ tolerates higher lookback than GBPJPY) — telling us the regression is a function of *how far price has drifted from the pivot by the time we see it*, not of the selection algorithm.

### Investigation

The only thing controlled by `i_pd_swing_lookback` is the `right` argument to `ta.pivothigh(N,N)` / `ta.pivotlow(N,N)` inside `request.security` (line 669). `right` is the confirmation lag — at right=N the pivot is reported N HTF bars after it occurred. Pulled across `request.security` with `lookahead_off`, the value surfaces on the chart side on the first chart bar of HTF bar (X + N + 1). On a 5m chart with PD = 15m and lookback = 10, that is ~33 chart bars after the actual pivot.

Two distinct bugs follow from that lag:

**Bug A — push records the wrong `bar_idx`.** The main-loop push (`src/IFVG_Indicator.pine:2762..2769` pre-fix) stamps `bar_idx = bar_index` at push time. That is `~(N+1) * (PD_TF / chart_TF)` chart bars later than the true pivot bar. The cycle-2 selection walks pivots by `bar_idx` to decide which side is older — when both an ITH and an ITL are pushed on the same chart bar boundary the comparison degenerates and a stale candidate becomes the "newest" anchor. Line rendering is also pinned to the wrong x-position (lines extend from a too-recent left edge).

**Bug B — no close-through invalidation for PD levels.** `check_pd_sweeps()` (lines 1267..1284 pre-fix) only marks a level swept on wick-and-revert (`high > level AND close < level`). For chart-TF ITH/ITL this is correct by design (cycle-1 comment: "ITH/ITL persist as dealing-range references"). But PD pivots arrive *with* lag — during the lag window price often closes fully through the level. A PD_ITH at 29,500 exposed on a chart bar where `close = 29,700` never satisfies `close < level`, so the wick-and-revert rule does not fire. The level enters the pool already broken yet is_valid=true. The cycle-2 selection then picks it as the dealing-range high. Wide / collapsed range bug.

Volatility scaling confirms the mechanism: at higher N the lag window is longer, so price drifts further; on fast-moving symbols (NQ, GBPJPY) the level is "born broken" at lower N than on slow symbols (Gold, BTC). Matches the observed breakpoint matrix exactly.

### Root cause (cycle 3)

Two-part. (1) Pivot's `bar_idx` is the chart bar where we *learned* about the pivot, not where it occurred. (2) Close-through is not recognised as an invalidation event for PD-source levels. Together they let stale levels into the candidate pool and corrupt chronological reasoning when they get picked.

### Fix applied (cycle 3)

`src/IFVG_Indicator.pine`:

1. **PD pivot push block (lines 2775..2799 post-fix).** Before pushing, compute true pivot chart bar:
   `lag_bars = ceil((i_pd_swing_lookback + 1) * (PD_TF_secs / chart_TF_secs))`,
   `pivot_bar = max(0, bar_index - lag_bars)`. Stamp `bar_idx = pivot_bar` on the pushed SwingPoint. Subsequent PD_ITH/PD_ITL creation inherits the corrected `bar_idx` via `create_pd_internal_levels()` (which copies `recent_high.bar_idx`).

2. **`check_pd_sweeps()` (lines 1267..1301 post-fix).** After the existing wick-and-revert block, added a close-through invalidation step scoped to PD_ITH/PD_ITL only: `close > level` (ITH) or `close < level` (ITL) sets `is_valid := false` without setting `is_swept` (so swept counters in the debug label still report wick-and-revert sweeps separately). Behaviour mirrors what `check_liquidity_sweeps()` already does for EQH/EQL.

Cycle-1 ATR-protrusion gate, cycle-2 newest-newest walkback, and the unconditional `select_dealing_range_source()` are all unchanged.

### Why this removes the lookback sensitivity

The two regressions (NQ breaks at 10+, GBPJPY at 6+) are both caused by stale levels being exposed at higher lag and surviving as `is_valid=true`. The close-through gate prunes them at the moment they would otherwise enter the candidate pool. The corrected `bar_idx` keeps the cycle-2 walkback well-ordered when multiple pivots surface near the same chart-bar boundary. Combined, the selection now sees only levels current price has not closed past, ordered by true age — the lookback value should no longer change the qualitative outcome, only the granularity of pivot detection.

### Files changed

- `src/IFVG_Indicator.pine` — `check_pd_sweeps()` (close-through invalidation appended) and Step 4C PD pivot push (true `bar_idx` from confirmation lag).

### Verification matrix for user

| Symbol | Chart | PD TF | `i_pd_swing_lookback` | Expected |
|---|---|---|---|---|
| NQ1! | 5m | 15 | 5 | works (regression check vs cycle 2) |
| NQ1! | 5m | 15 | 6 | works |
| NQ1! | 5m | 15 | 9 | works (regression check vs cycle 2) |
| NQ1! | 5m | 15 | 10 | **works (cycle-3 fix)** |
| NQ1! | 5m | 15 | 15 | works |
| GBPJPY | 5m | 15 | 5 | works (regression check vs cycle 2) |
| GBPJPY | 5m | 15 | 6 | **works (cycle-3 fix)** |
| GBPJPY | 5m | 15 | 7 | works |
| GBPJPY | 5m | 15 | 10 | works |
| XAUUSD | 5m | 15 | 5 / 10 | works, ~4650 -> ~4750 range |
| BTCUSD | 5m | 15 | 5 / 10 | works, ~80,400 -> ~82,500 range |

Also check:
- PD line `left_edge` should now sit visibly earlier on the chart (where the true pivot occurred) instead of 18-33 bars to the right of it.
- Debug label `valid ITH/ITL` counts should DROP at higher lookback (stale broken levels are now invalidated). `swept ITH/ITL` counts unchanged (close-through does not set is_swept).
- If `range = NO` appears with cycle-3 build, the structural range genuinely has no unswept ITH+ITL pair — confirm by eyeballing chart. Should be rare with default lookback.

### Notes on prior cycles (unchanged)

- Cycle 1: `check_pd_sweeps()` ATR-protrusion gate (`i_pd_sweep_min_atr_mult`, default 0.05) retained.
- Cycle 1: `select_dealing_range_source()` still unconditionally returns `g_pd_liquidity_array`.
- Cycle 2: newest-newest + cross-walkback selection unchanged.
- Debug label `g_pd_debug_label` still rendered each `barstate.islast`.


---

## Cycle 4 — structural-extremes fallback for steep-trend regimes

### New evidence (post-cycle-3)

User reports cycle-3 build works on most charts and most lookback values across symbols (NQ, GBPJPY, XAUUSD, BTCUSD) — the broad lookback regression is resolved. Residual failure mode: on **NQ during steeply bullish or bearish sessions** the PD zone occasionally fails to render.

This matches the cycle-2 verification caveat verbatim: "If a pair-cross occurs (e.g. all newest ITHs sit below all newest ITLs due to fast trend), the range should temporarily disappear rather than render an inverted box." Confirmed: behaviour is "by design" under the cycle-2 walkback heuristic when the walkback exhausts. But the user expectation — and the ICT methodology — is for the dealing range to still render in strong trends, anchored on the structural extremes of the recent impulse leg.

### Investigation

Re-read Step 4C selection (`src/IFVG_Indicator.pine` lines 2810..2876 post cycle-3). Flow confirmed:

1. Collect unswept PD_ITH and PD_ITL candidates newest-first.
2. Anchor on index-0 of each. If `ith.level > itl.level`, done.
3. Else walk back the chronologically older anchor by `bar_idx` until non-crossing OR candidates exhausted.
4. If walkback exhausts without `resolved`, leave selections as `na` → downstream branch clears all PD drawings.

The exhaust branch is the gap. During a steep impulse, every newest unswept ITH may sit below every newest unswept ITL (the trend has dragged the freshest pivots to one side of price). The cycle-2 heuristic finds no non-crossing pair and surrenders. But there ARE still structurally meaningful candidates in the pool — just not chronologically newest ones.

ICT methodology (`strategy.md` and `ARCHITECTURE.md`): in strong trends the dealing range collapses to the most recent impulse leg, defined by the **highest unswept ITH above price** paired with the **lowest unswept ITL below price**. Structural extremes, not chronological recency, when the two notions disagree.

### Root cause (cycle 4)

The cycle-2 walkback is correct as the primary heuristic but has no fallback when it exhausts. The selector goes from "pick the chronologically newest valid pair that doesn't cross" straight to "give up." There is no intermediate "pick the structural extremes" branch — even though that branch is what an ICT trader's eye sees during a strong directional leg.

### Fix applied (cycle 4)

`src/IFVG_Indicator.pine`:

1. **New global flag** (line 316): `var bool g_pd_used_fallback = false`. Persisted across bars so the debug label can report which selection branch fired on the current bar.

2. **Step 4C selection** (lines 2825, 2855..2876). Reset `g_pd_used_fallback := false` at the top of every selection pass. After the cycle-2 walkback loop, if `resolved` is false, scan `ith_candidates` for the entry with the **highest level** and `itl_candidates` for the entry with the **lowest level**. If `highest_ith.level > lowest_itl.level`, adopt that pair as the dealing range and set `g_pd_used_fallback := true`. If even that pair crosses, truly no range exists — selections remain `na` (preserves prior behaviour: drawings cleared).

3. **Debug label** (line 3003). `range=YES` becomes `range=YES*` when the fallback fired. Makes it trivial to confirm in screenshots whether a rendered zone came from cycle-2 walkback (`YES`) or cycle-4 fallback (`YES*`).

Loop guards added: the candidate-scan `for k = 1 to n - 1` loops are wrapped in `if n >= 2`, because Pine v6's `for a to b` is bidirectional — `for k = 1 to 0` would iterate `k=1,0` and out-of-bound the array. With `n_ith == 1` or `n_itl == 1` the loops are skipped and `hi_ith`/`lo_itl` keep their initial index-0 values.

### Why this preserves all prior cycles

- Cycle 1 (ATR-protrusion sweep gate, source unification, debug label): untouched.
- Cycle 2 (newest-newest + walkback): runs first and short-circuits on success. The fallback fires ONLY when the walkback hits `break` (candidate exhaustion) without resolving.
- Cycle 3 (corrected `bar_idx` from confirmation lag, PD close-through invalidation): untouched. The fallback consumes the same already-pruned candidate pool the walkback uses.

If cycles 1–3 working symbols still resolve via walkback, they hit `if resolved` and never reach the fallback branch. `g_pd_used_fallback` stays false and the label still shows `range=YES`. No regression possible for those cases.

### Files changed

- `src/IFVG_Indicator.pine` — Step 4C structural-extremes fallback appended after walkback, new `g_pd_used_fallback` var, debug label marker.

### Verification steps for user

1. Copy updated `src/IFVG_Indicator.pine` into TradingView Pine Editor.
2. **Regression check** — apply to symbols that worked at end of cycle 3 (NQ / GBPJPY / XAUUSD / BTCUSD at default lookback 5 and a higher value like 10). Debug label should show `range=YES` (no asterisk). Range positions unchanged from cycle 3.
3. **Target case** — apply to NQ during a clearly trending session (e.g. open the chart at a strong bullish or bearish run). If the walkback exhausts, the fallback should now render a zone anchored at the **highest unswept ITH and lowest unswept ITL** visible in the recent pivot history. Debug label should show `range=YES*`.
4. The structural-extremes pair may produce a wider range than a typical walkback-resolved pair — that is expected behaviour during strong trends (the entire recent impulse leg becomes the dealing range).
5. If `range=NO` still appears during a steep trend, the candidate pool truly has no `ITH > ITL` pair at all — `valid ITH/ITL` counts in the label should both be > 0 but `max(ITH).level <= min(ITL).level`. Rare; investigate sweep gate parameters.
6. Toggle `i_pd_swing_lookback` across 5..15 on the trending NQ chart. Behaviour should remain stable (cycle-3 lag fix is the dominant guarantor of this; cycle 4 only adds the trend-resilient fallback on top).

---

## Cycle 5 — cycle-3 close-through over-pruned legitimate older pivots in sustained trends

### New evidence (post-cycle-4)

User retested cycle-4 build on **H1 chart with PD timeframe = H1** (i.e. `src=PD (PD=chart)`) during a steep multi-day bullish impulse. Diagnostic label:

| Field | Value |
|---|---|
| TF | 60 / chart 60 |
| src | PD (PD=chart) |
| pd_sw_H / pd_sw_L | 50 / 50 |
| pd_liq | 50 |
| chart_liq | 35 |
| **valid ITH / ITL** | **0 / 13** |
| swept ITH / ITL | 25 / 12 |
| **range** | **NO** |

Dashboard PD Zone row was blank. Cycle 4's structural-extremes fallback did **not** fire.

### Investigation

Cycle 4 fallback is gated on the primary branch's `if n_ith > 0 and n_itl > 0`. With **zero** valid ITHs in the candidate pool, the primary branch is skipped entirely and the fallback inside that `else` never executes — `sel_ith` / `sel_itl` stay `na`, downstream branch clears drawings.

Why zero valid ITHs in a chart obviously full of historical highs? Two compounding mechanisms:

1. **Wick-and-revert sweeps** (ATR-gated) marked 25 ITHs `is_swept` over the trend's life — correct behaviour, those were genuine sweep events.
2. **Cycle 3's close-through invalidation** then nuked every remaining ITH the moment a chart-TF close pierced it. Cycle 3 was designed to drop levels that materialise already broken during the `(N+1) * ratio` confirmation-lag window — pivots with no real structural meaning. But its scope was unconditional: it also fired on legitimate older pivots that lived through the lag window successfully and only got penetrated later as the trend developed. Those pivots had real structural meaning (they ARE the high side of the dealing range during the impulse) and should have survived for cycle 4's fallback to anchor on.

The volatility-scaling evidence supports this read: cycle 3 chose the right *kind* of fix but applied it too broadly. The "born already broken" case needs the close-through gate; the "legitimately broken much later by the same trend" case does not.

### Root cause (cycle 5)

Cycle 3 over-pruned. Close-through is an invalidation signal **only inside the confirmation-lag window** (when a level entering the pool is already broken proves it was never structurally meaningful). After the lag window expires, a close-through is merely "price has moved past a prior structural level" — which is exactly the dealing-range scenario cycle 4's fallback was designed for. By marking those pivots invalid, cycle 3 starved cycle 4 of the candidates it needs.

Secondary issue: the cycle 4 fallback itself is wholly inside `if n_ith > 0 and n_itl > 0`, so even if Option A leaves more candidates intact, a one-sided wipeout (e.g. every ITH wick-swept legitimately during a long bullish run) still skips the fallback. Needs an outer rescue path that consumes the full PD pool including swept/invalid entries.

### Fix applied (cycle 5)

`src/IFVG_Indicator.pine`:

1. **Time-gate cycle-3 close-through invalidation in `check_pd_sweeps()` (lines 1268..1314).** Inside the function, recompute the confirmation-lag window using the same formula Step 4C uses:
   `lag_bars = ceil((i_pd_swing_lookback + 1) * (PD_TF_secs / chart_TF_secs))`.
   The close-through block now runs only when `bar_index - liq.bar_idx <= lag_bars`. Wick-and-revert sweep (the ATR-gated block above) still applies at any age — it's a legitimate sweep signal whenever it occurs. Outside the lag window, close-through no longer invalidates a level; the pivot survives and becomes available to cycle 4's structural-extremes fallback when needed.

2. **Cycle 4 fallback safety net (Step 4C, after the `if n_ith > 0 and n_itl > 0` block, lines 2893..2928).** Added an outer guard: if either `sel_ith` or `sel_itl` is still `na` after the cycle-4 branches, scan the **entire `src` (PD liquidity) array** — including swept and invalid entries — and pick the **highest PD_ITH** and **lowest PD_ITL** seen. Only fills in the missing side(s); a side that resolved via cycle 4 keeps its valid pick. If the resulting pair satisfies `ith.level > itl.level`, adopt it and set `g_pd_used_fallback := true` (debug label `range=YES*`). If it crosses, leave `na` (range truly invalid).

Both fixes coexist. Option A is the more correct semantic fix and should be sufficient for most steep-trend cases; Option B catches the residual case where wick-and-revert sweeps (still firing legitimately) wipe out one side entirely.

### Why prior cycles remain intact

- **Cycle 1** (ATR-protrusion sweep gate, source unification, debug label, `i_pd_sweep_min_atr_mult` input): untouched.
- **Cycle 2** (newest-newest + cross-walkback selection): untouched. Runs first and short-circuits on success in all non-trend cases.
- **Cycle 3** ("born already broken" close-through): **scope narrowed**, not removed. Still fires while a pivot is inside its confirmation-lag window — exactly the regime cycle 3 targeted. Behaviour is identical to cycle 3 for the (N+1)*ratio chart bars after pivot push; only the older-than-lag tail is changed.
- **Cycle 4** (structural-extremes fallback for trend regimes): untouched in its own logic. Cycle 5's Option A simply makes more candidates available to it; cycle 5's Option B extends it to one-sided wipeouts.

For symbols and TFs where cycles 1–4 already worked, the candidate pool now contains the same valid candidates it did before PLUS some older pivots that previously got close-through invalidated. Cycle 2's walkback still anchors on index 0 (newest valid) — those older pivots only become visible if the walkback reaches them. Cycle 4's fallback still reads from the same pool. The only behavioural change in working scenarios is potentially a more inclusive candidate list, never less.

### Files changed

- `src/IFVG_Indicator.pine` — `check_pd_sweeps()` close-through block time-gated; Step 4C selection block extended with full-pool safety-net fallback.

### Verification matrix for user

| Scenario | Chart | PD TF | Lookback | Expected |
|---|---|---|---|---|
| **Target case — steep H1 bullish trend** (the reported screenshot) | H1 | 60 | 15 | PD zone renders. `range=YES*` (cycle 4 fallback fired — possibly via Option B if all ITHs are wick-swept). `valid ITH` may still be 0; safety net pulls highest historical PD_ITH from full pool. |
| **Mirror case — steep H1 bearish trend** | H1 | 60 | 15 | Same expectation, mirrored. `range=YES*`. |
| **Normal ranging H1** | H1 | 60 | 5 | `range=YES` (no asterisk — cycle 2 walkback still primary). Range matches recent structural pivots. |
| **Cycle-3 regression check — fast-trend "born already broken" scenario** | 5m | 15 | 10 | Still works. The lag-window close-through still fires for stale freshly-pushed pivots. Verify by inspecting debug label `valid ITH/ITL` is non-zero with reasonable counts. |
| **Cycle-2 regression — NQ 5m / GBPJPY 5m** | 5m | 15 | 5..10 | `range=YES`, no behavioural change vs cycle 4 build. |
| **Cycle-1 regression — XAUUSD / BTCUSD** | 5m | 15 | 5 / 10 | `range=YES`, original wide structural ranges preserved. |

Diagnostic check: if cycle 5 over-relaxes (some unwanted stale pivot leaks into selection), the debug label's `valid ITH/ITL` counts should rise visibly versus cycle 4 on identical chart state. If counts look correct but range still wrong, the issue is in selection ordering, not the sweep gate.

### Notes on prior cycles (unchanged)

- Cycle 1: `check_pd_sweeps()` ATR-protrusion gate (`i_pd_sweep_min_atr_mult`, default 0.05) retained.
- Cycle 1: `select_dealing_range_source()` still unconditionally returns `g_pd_liquidity_array`.
- Cycle 2: newest-newest + cross-walkback selection unchanged.
- Cycle 3: close-through invalidation retained, now time-gated to the confirmation-lag window.
- Cycle 4: structural-extremes fallback unchanged; cycle 5 adds an outer safety-net rescue around it.
- Debug label `g_pd_debug_label` still rendered each `barstate.islast`. `range=YES*` marker now also lights up when the cycle-5 safety net fires.

---

## Resolution

User verified across multiple symbols and lookback values that cycles 1–5 fixes resolve the PD zone rendering issue, including the steep-trend case (range=YES* via fallback).

Diagnostic instrumentation removed in finalization commit:
- `var label g_pd_debug_label` declaration
- `var bool g_pd_used_fallback` declaration
- All `g_pd_used_fallback` assignment sites in Step 4C
- The `if barstate.islast` PD DEBUG label-construction block at end of main loop

Final file size: 3012 lines (down from ~3056 with diagnostics).
