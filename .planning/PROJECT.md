# IFVG Pro

## What This Is

A TradingView Pine Script v6 overlay indicator that automates the detection, grading, and visualization of Inversion Fair Value Gap (IFVG) setups based on ICT/SMC methodology. It identifies FVGs, tracks their inversions, detects liquidity levels, grades setups from A+ to C, and provides multi-timeframe HTF analysis — enabling traders to spot high-probability entries without manual chart analysis.

## Core Value

Accurately detect and grade IFVG setups so traders can identify high-probability trade entries with clear risk management levels, across any market and timeframe.

## Requirements

### Validated

- ✓ FVG detection with ATR-based minimum sizing (bullish & bearish) — Phase 1
- ✓ IFVG inversion detection on confirmed candle close — Phase 1
- ✓ Visual boxes with grade labels and color coding — Phase 1
- ✓ Swing structure liquidity detection (EQH, EQL, ITH, ITL) — Phase 2
- ✓ Liquidity sweep detection (BSL/SSL) — Phase 2
- ✓ Full grading algorithm (A+ to C, hybrid tier + quality scoring) — Phase 2
- ✓ Break-even point tracking and entry validation — Phase 2
- ✓ Stop loss level calculation — Phase 2
- ✓ HTF FVG/IFVG detection via request.security — Phase 3
- ✓ HTF overlay projection on LTF chart — Phase 3
- ✓ HTF bias determination — Phase 3
- ✓ PDA delivery detection for grading — Phase 3

### Active

- [ ] Fix hardcoded fvg_singular = true inflating all grades
- [ ] Review and fix duplicated HTF bias calculation logic
- [ ] Premium/Discount zone calculation using HTF swing detection
- [ ] PD zone grading integration (+1/-1 quality modifier)
- [ ] PD zone visualization (lines, fills, labels)
- [ ] Session tracking (Asian, London, NY highs/lows)
- [ ] Session-based data highs/lows as liquidity targets
- [ ] Enhanced dashboard with PD zone and session info
- [ ] Alert system for valid entries (grade-filtered)
- [ ] Alert for entry invalidation (BE taken)
- [ ] Alert for IFVG mitigation
- [ ] Performance optimization and edge case hardening

### Out of Scope

- LRLR trendline liquidity — complex diagonal rendering, defer to future
- SMT divergence detection — requires correlated symbol data, defer to future
- Mobile app or web interface — TradingView-only indicator
- Backtesting engine — TradingView strategy scripts are a separate tool
- Real-time chat/social features — not applicable

## Context

- **Platform**: TradingView Pine Script v6, overlay indicator
- **Markets**: Market-agnostic (indices, forex, crypto, commodities) via ATR-based sizing
- **Methodology**: Based on DodgysDD / ICT Smart Money Concepts
- **Current state**: 2,511 lines in single file (src/IFVG_Indicator.pine), Phases 1-3 complete
- **Known issues**: Hardcoded `fvg_singular = true` at line ~1595 inflates grades; duplicated HTF bias calc in two render functions; 16 of 40 request.security() calls consumed
- **Resource constraints**: TradingView limits — 500 drawing objects each (boxes/lines/labels), 40 request.security() calls, single-file architecture
- **Reference materials**: PRD.md, ARCHITECTURE.md, strategy.md, briefing/IFVG_Rating_System.pdf, PHASE4_PD_ZONES_PLAN.md

## Constraints

- **Platform**: Pine Script v6 on TradingView — no external dependencies, no build toolchain
- **Testing**: Visual verification only — no automated test framework exists for Pine Script
- **Drawing limits**: Max 500 boxes, 500 lines, 500 labels — FIFO cleanup required
- **Security calls**: Max 40 request.security() calls — 16 already used, Phase 4+ needs careful budgeting
- **Single file**: All code lives in src/IFVG_Indicator.pine — must maintain section organization
- **No repainting**: All detection on barstate.isconfirmed only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Pine Script v6 over v5 | Dynamic requests, no scope limit, negative array indexing | ✓ Good |
| ATR-based sizing over fixed pip values | Market-agnostic across indices/forex/crypto | ✓ Good |
| Single-file architecture | Pine Script limitation, no module system | ⚠️ Revisit — 2,500+ lines, consider section discipline |
| barstate.isconfirmed only | Prevents repainting — critical for trading decisions | ✓ Good |
| HTF swing-based PD zones over daily range | More accurate ICT dealing range concept | — Pending |
| Hybrid grading (tier + quality score) | Separates mandatory criteria from quality modifiers | ✓ Good |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-23 after initialization*
