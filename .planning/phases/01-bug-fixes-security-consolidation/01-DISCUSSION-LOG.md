# Phase 1: Bug Fixes & Security Consolidation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 01-bug-fixes-security-consolidation
**Areas discussed:** FVG singularity logic, Grade rebalancing, Security tuple strategy

---

## FVG Singularity Logic

| Option | Description | Selected |
|--------|-------------|----------|
| Proximity check | Singular if no same-direction FVG within N bars | |
| Overlap check | Singular if zone doesn't overlap another same-direction FVG | |
| Both checks combined | No same-direction FVG within N bars AND no zone overlap | ✓ |
| You decide | Claude picks best approach | |

**User's choice:** Both checks combined
**Notes:** Most strict approach — catches both proximity clusters and zone overlaps. Matches strategy definition of "singular" FVG.

---

## Grade Rebalancing

| Option | Description | Selected |
|--------|-------------|----------|
| Natural recalibration | Keep current thresholds, let grades drop naturally | ✓ |
| Adjust thresholds down | Lower thresholds by 1 to compensate | |
| Validate then decide | Fix bug first, check distribution, then decide | |

**User's choice:** Natural recalibration
**Notes:** Matches strategy intent — singular FVGs should genuinely be higher quality. No artificial threshold adjustment.

---

## Security Tuple Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| 2 mega-tuples | 1 call per timeframe, 7 values each (14→2) | |
| 4 focused tuples | 2 calls per timeframe, OHLC + historical (14→4) | |
| You decide | Claude picks based on Pine Script limits and clarity | ✓ |

**User's choice:** You decide (Claude's discretion)
**Notes:** Optimize for maximum consolidation while maintaining clarity.

## Claude's Discretion

- Exact proximity threshold (N bars) for singularity check
- Overlap tolerance for FVG zone comparison
- Tuple structure and variable naming
- Shared HTF bias function signature and placement

## Deferred Ideas

None — discussion stayed within phase scope
