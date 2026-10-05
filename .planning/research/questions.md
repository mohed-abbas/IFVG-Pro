# Open Research Questions

Forward-looking investigations that don't fit a single phase. Each entry: question, why it matters, what would resolve it.

---

## Q1 — Singularity scoring coupling after merge tightening

**Posed:** 2026-05-17
**Related:** .planning/todos/pending/tighten-fvg-merge-opposite-color-break.md, .planning/notes/fvg-merge-rule-decision.md
**Code touched:** src/IFVG_Indicator.pine:538 (`merge_with_existing_fvg`), src/IFVG_Indicator.pine:1528 (`is_fvg_singular`)

**Question:** Once the FVG merge rule is tightened to block on opposite-color candles, does the singularity check at `is_fvg_singular()` over-penalize the newly-split FVGs? The two functions use different rules (merge: bar distance only; singularity: bar distance AND overlap within ATR×0.1) and they were designed assuming aggressive merge would collapse most clusters. With merge now stricter, the array will hold more entries that the singularity check will flag as non-singular → score 0 on Criterion 4 → grades drop.

**Why it matters:** Grade distribution is a v1 success criterion (no single grade > 40% of setups). If tightening merge inadvertently shifts the distribution toward B and C tiers because every cluster now scores 0 on singularity, we've fixed RR at the cost of grade meaningfulness — a worse trade than the original problem.

**What would resolve it:**
1. Implement the merge fix.
2. Collect grade distribution on a known chart period before and after.
3. If A/A- counts collapse, revisit the singularity rule:
   - Should the ATR×0.1 overlap tolerance be tightened (or made multiplicative on gap size)?
   - Should singularity consider the same "opposite candle between" signal — if there's a break between two same-direction FVGs, treat them as singular even when they overlap in price?
   - Should the 5-bar window match between merge and singularity, or should singularity use a wider window?

**Decision deferred until:** post-merge-fix visual verification.

---
