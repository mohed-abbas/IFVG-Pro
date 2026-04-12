---
phase: 5
slug: grading-system-remodel
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-12
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Pine Script v6 — no automated testing framework |
| **Config file** | none — Pine Script has no test runner |
| **Quick run command** | `grep -c "syntax error" /dev/null` (placeholder — validation is manual) |
| **Full suite command** | Copy `src/IFVG_Indicator.pine` to TradingView and verify visually |
| **Estimated runtime** | ~60 seconds (manual chart inspection) |

---

## Sampling Rate

- **After every task commit:** Verify Pine Script compiles (no syntax errors via structural grep checks)
- **After every plan wave:** Full TradingView visual verification
- **Before `/gsd-verify-work`:** Full suite must be green on TradingView
- **Max feedback latency:** 60 seconds (compilation check)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | — | — | N/A | structural | `grep -c "has_delivery" src/IFVG_Indicator.pine` | ✅ | ⬜ pending |
| 05-01-02 | 01 | 1 | — | — | N/A | structural | `grep -c "check_delivery_from_fvg" src/IFVG_Indicator.pine` | ✅ | ⬜ pending |
| 05-02-01 | 02 | 2 | — | — | N/A | structural | `grep -c "sweep_delivery_score\|score_target_clarity\|score_singularity\|score_pd_zone" src/IFVG_Indicator.pine` | ✅ | ⬜ pending |
| 05-02-02 | 02 | 2 | — | — | N/A | structural | `grep "A+" src/IFVG_Indicator.pine \| grep -c "hard_gate\|has_sweep.*has_delivery"` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

*Existing infrastructure covers all phase requirements. Pine Script has no test framework — validation is structural (grep for expected patterns) and visual (TradingView chart inspection).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grade distribution spread | SC-2 | Requires visual chart with multiple setups | Apply indicator to ES 15m chart, verify grades span A through C |
| Tooltip shows 5 criteria scores | SC-3 | Requires TradingView UI interaction | Hover IFVG label, verify all 5 scoring criteria visible with numeric scores |
| A+ hard gate blocks incorrect grades | SC-1 | Requires setup without sweep+delivery in correct zone | Find setup missing one gate condition, verify grade caps at A |
| Delivery detection accuracy | SC-1 | Requires chart with known delivery-from-FVG pattern | Find FVG with body-respecting candles before IFVG, verify has_delivery=true |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [x] All tasks have structural verify or manual verification instructions
- [x] Sampling continuity: structural grep after each task
- [x] Wave 0 covers all MISSING references (N/A — no test framework)
- [x] No watch-mode flags
- [x] Feedback latency < 60s (grep checks are instant)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
