# Phase 2: PD Zone Detection & Grading Integration - Context

**Gathered:** 2026-04-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Detect the ICT dealing range on a user-selected HTF using the existing ITH/ITL liquidity detection, compute price position within that range (0–100%), feed `pd_zone` ("premium"/"discount"/"equilibrium"/"neutral") into the already-wired `score_pd_zone()` grading criterion so A+ grades become reachable, visualize H/EQ/L boundaries on the chart, and expose current zone + range percentage in the dashboard.

**Out of scope (new capabilities belong in other phases):** session tracking (Phase 3), alerts (Phase 4), SMT/LRLR (v2), auto-trading, mobile UI.
</domain>

<decisions>
## Implementation Decisions

### Detection Approach
- **D-01:** The dealing range top and bottom are the selected HTF's **ITH and ITL** — not raw swing points, not `ta.pivothigh`+`valuewhen` (approach #1, failed), not zigzag (approach #2, failed), not `ta.highest`/`ta.lowest` (approach #3, failed). Reuse existing `create_internal_levels()` logic against HTF-resampled data.
- **D-02:** Pick rule: **most recent unswept by `bar_idx`.** `swing_high_dr` = newest ITH where `is_valid=true AND is_swept=false`. `swing_low_dr` = newest ITL with same criteria. Range rotates automatically when a new ITH/ITL forms or the current boundary gets swept — no custom update trigger needed; existing `is_swept`/`is_valid` machinery handles rotation.
- **D-03:** `pd_zone` computation at IFVG creation time (PDZ-08): if a valid ITH+ITL pair exists AND IFVG midpoint falls strictly above 50% → `"premium"`; strictly below 50% → `"discount"`; exactly at 50% → `"equilibrium"`; otherwise → `"neutral"`. `"neutral"` is used when no valid ITH/ITL pair exists yet (young chart).

### Timeframe & Fallback
- **D-04:** Default PD timeframe = `D` (Daily). User-configurable via `input.timeframe()` — typical values 1H / 4H / D / W.
- **D-05:** When chart TF >= PD TF, fall back to using chart-TF ITH/ITL directly (no `request.security` call needed). This keeps the feature functional on Daily/Weekly charts without disabling.
- **D-06:** When no valid ITH/ITL pair exists: `pd_zone = "neutral"` (scoring returns 1, A+ remains unreachable for those setups), no zone lines rendered, dashboard shows `—` for PD row and Range %.

### Visualization
- **D-07:** Render **3 dashed lines** — swing H (top of premium), EQ (50%), swing L (bottom of discount). Line style: dashed, width configurable. Default line extension: from the swing bar's `bar_idx` to the right edge with a small buffer (standard ICT extension behavior). Lines redrawn when range rotates (delete old, create new).
- **D-08:** **Label format:** `percentage (price)` at the right edge — e.g., `1 (24,764.25)`, `0.5 (24,270.00)`, `0 (23,775.50)`. Matches the user's reference indicator exactly. Labels move with the lines when range rotates.
- **D-09:** **Zone fills** — optional, `input.bool` toggle, **default OFF**. When on, render premium zone fill above EQ and discount fill below EQ using `linefill`.
- **D-10:** **OTE zone (PDZ-06)** — optional, `input.bool` toggle named `i_show_ote`, **default OFF**. When on, render a subtly-shaded fill between 62% and 79% retracements. Visual only — no grading effect in this phase.

### Dashboard
- **D-11:** **PD Zone row (DSH-01):** displays `PREMIUM` (red), `DISCOUNT` (green), `EQ` (yellow), or `—` (gray) when no valid range. Color mapping is semantic (red = suboptimal-for-longs, green = optimal-for-longs).
- **D-12:** **Range % row (DSH-02):** displays integer 0–100 (e.g., `62%`, `35%`), or `—` when no valid range. No decimals, no directional arrows.
- **D-13:** **Equilibrium threshold:** strict — EQ only at exactly 50.00% position, everything else is premium (>50%) or discount (<50%). No equilibrium band. Simplifies grading boundaries.

### Grading Integration (PDZ-03, PDZ-07)
- **D-14:** The existing `score_pd_zone()` function (line 1486) and the calculate_grade integration (lines 1499–1520) are already wired from Phase 5. This phase only supplies real `pd_zone` values at IFVG creation (lines 732 and 1684 — remove the hardcoded `pd_zone = "neutral"`).
- **D-15:** **Calibration (PDZ-07):** ship current thresholds as-is (`total>=9 AND sweep_delivery=2 AND pd_score=2` → A+). Deploy, observe A+ frequency on a representative test chart, only adjust thresholds if A+ exceeds ~10% of setups. No pre-emptive threshold tuning.

### Claude's Discretion
- Exact `request.security` mechanism for fetching HTF ITH/ITL (tuple call vs. two calls vs. rebuilding ITH/ITL on chart from HTF pivots) — planner/researcher decides based on security-call budget and performance. Budget: 3/40 used after Phase 1, 37 free.
- Exact input group placement (existing PD zone input group draft in `PHASE4_PD_ZONES_PLAN.md` is a reference, not binding).
- Label `bar_idx` placement offset (how many bars past `bar_index` to anchor labels) and line width defaults.
- Whether to reuse `Liquidity` type or introduce a lightweight `DealingRange` type for storing the current range snapshot.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap
- `.planning/REQUIREMENTS.md` §Premium/Discount Zones — PDZ-01 through PDZ-08 (note: PDZ-01 prescribes `ta.pivothigh via request.security`; **D-01 supersedes this** — use HTF ITH/ITL instead).
- `.planning/REQUIREMENTS.md` §Dashboard — DSH-01, DSH-02.
- `.planning/ROADMAP.md` §Phase 2 — success criteria and scope.

### Prior phase context
- `.planning/phases/01-bug-fixes-security-consolidation/01-CONTEXT.md` — Phase 1 context (request.security consolidation, grading baseline).
- `.planning/phases/05-grading-system-remodel/` — Phase 5 PLAN/RESEARCH files; defines the 5-criterion checklist grading that this phase plugs into.

### Project & codebase intel
- `CLAUDE.md` §Pine Script v6 Syntax Rules — MUST follow (esp. no blank lines in block bodies, parens around multi-line `and`/`or`, casting to `int()`).
- `.planning/codebase/CONVENTIONS.md` — naming (`i_` inputs, `g_` globals, snake_case functions), section structure, color conventions.
- `.planning/codebase/ARCHITECTURE.md` — main loop order, data store arrays, drawing object lifecycle.
- `.planning/codebase/CONCERNS.md` — memory/drawing limits.

### External reference (user-supplied)
- `PHASE4_PD_ZONES_PLAN.md` (repo root) — earlier draft plan. Input group structure and global variable names are a **reference only**. The detection approach (`ta.pivothigh` + `valuewhen`) in that document is the approach that **failed** — do not follow. Use D-01/D-02 from this CONTEXT instead.
- `briefing/IFVG_Rating_System.pdf` — grading methodology reference.
- `strategy.md` — trading strategy rules.

### Code locations (current state in `src/IFVG_Indicator.pine`)
- Lines 732, 1684 — hardcoded `pd_zone = "neutral"` at IFVG creation. **Remove** and replace with computed value.
- Lines 1032–1097 — `create_internal_levels()` ITH/ITL creation logic to reuse/adapt for HTF.
- Line 1486 — `score_pd_zone()` (no changes needed; already scores 0/1/2 correctly).
- Lines 1499–1520 — `calculate_grade()` (no changes needed; A+ gate already requires `pd_score=2`).
- Lines 2018–2023 — existing dashboard `tt_pd` and `zone_text` references (dashboard row likely needs new render block, not edit here).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`Liquidity` type** (lines 67–79) and `create_internal_levels()` (line 1035) — ITH/ITL are already first-class in the codebase with `is_valid`/`is_swept` tracking. The HTF variant can mirror this structure.
- **Phase 1 request.security tuple pattern** — already established for HTF data; extending to fetch HTF ITH/ITL bounds should reuse the same tuple call style.
- **`score_pd_zone()` + A+ gate** — complete Phase 5 integration. Phase 2 does **not** edit grading logic, only supplies `pd_zone` at inversion.
- **Drawing-object lifecycle pattern** — dashed lines, right-extension, labels, linefill for zone shading all have precedent elsewhere in Section 10 rendering.

### Established Patterns
- Detection runs on `barstate.isconfirmed` only (no repainting).
- `var` arrays with FIFO cleanup; drawing objects deleted before recreating.
- Bar-index clamping with `math.max(start_bar, bar_index - 400)` for extended lines.
- Semantic color conventions (green = optimal, red = suboptimal) already in use for grading colors.

### Integration Points
- **IFVG creation:** lines 732 and 1684 — inject computed `pd_zone` value.
- **Main loop (Section 12):** add HTF ITH/ITL detection step before `check_inversions()` so the zone value is available when IFVG is created.
- **Dashboard render (Section 11, ~lines 2308–2387):** add PD Zone row and Range % row.
- **Input section (Section 2):** add new input group for PD zone settings.

</code_context>

<specifics>
## Specific Ideas

- Label format is a specific user requirement: `percentage (price)` — e.g., `1 (24,764.25)`, `0.5 (24,270.00)`, `0 (23,775.50)`. Matches the reference indicator used for comparison.
- "Current market structure" semantics: most recent unswept ITH/ITL — ICT dealing range interpretation, not highest/lowest of visible range.
- Three prior detection attempts are on record as failures (see deferred section for why). Planner should not revisit them.

</specifics>

<deferred>
## Deferred Ideas

- **Failed approaches (do not retry without strong evidence):**
  1. `ta.pivothigh` + `ta.valuewhen` via `request.security` — swings did not alternate, range covered entire chart history.
  2. Zigzag state machine — produced micro-swings and tiny wrong ranges.
  3. `ta.highest`/`ta.lowest` over N bars — range too wide, covered entire visible chart.
- **Directional hint on Range %** (e.g., `62% ↑`) — requires previous-bar tracking; low value for now, could revisit in v2.
- **Equilibrium band** (45–55% as EQ) — more conservative grading, but user chose strict 50% exact. Reconsider only if A+ distribution analysis (PDZ-07 measurement) shows too many "equilibrium-adjacent" setups getting full credit unfairly.
- **OTE as grading input** — currently visual only (D-10). Could feed into grading in a future phase if traders ask for OTE-weighted setups.
- **Zone fills on by default** — kept off to reduce chart clutter; user can opt in.
- **PDZ-01 wording in REQUIREMENTS.md** — still reads "ta.pivothigh via request.security." Consider amending to reflect HTF-ITH/ITL approach once Phase 2 is verified.

</deferred>

---

*Phase: 02-pd-zone-detection-grading-integration*
*Context gathered: 2026-04-14*
