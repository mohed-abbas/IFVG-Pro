---
phase: 1
slug: bug-fixes-security-consolidation
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — Pine Script has no automated test framework |
| **Config file** | N/A |
| **Quick run command** | `grep -c "request.security" src/IFVG_Indicator.pine` |
| **Full suite command** | Manual: copy to TradingView, apply to chart, verify visually |
| **Estimated runtime** | ~60 seconds (manual verification) |

---

## Sampling Rate

- **After every task commit:** Run quick grep checks (security call count, function existence)
- **After every plan wave:** Manual TradingView verification
- **Before `/gsd:verify-work`:** Full manual chart verification
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| FIX-01 | 01 | 1 | FIX-01 | grep + manual | `grep "fvg_singular = true" src/IFVG_Indicator.pine` (should return 0) | N/A | ⬜ pending |
| FIX-02 | 01 | 1 | FIX-02 | grep | `grep -c "get_htf_bias" src/IFVG_Indicator.pine` (should be >= 3: def + 2 calls) | N/A | ⬜ pending |
| FIX-03 | 02 | 1 | FIX-03 | grep | `grep -c "request.security" src/IFVG_Indicator.pine` (should be <= 3) | N/A | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Pine Script has no test framework — validation is via grep checks and manual TradingView chart verification.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Grade distribution balance | FIX-01 | Requires visual chart inspection | Apply to ES/NQ 5m chart, check that no single grade exceeds 40% of displayed IFVGs |
| HTF overlay rendering | FIX-03 | Requires visual inspection | Enable HTF overlays on 5m chart with 1H/4H timeframes, verify boxes render correctly |
| IFVG box rendering | ALL | Regression check | Compare IFVG boxes, lines, labels before and after changes |

---

## Validation Sign-Off

- [x] All tasks have automated verify or manual verification steps
- [x] Sampling continuity: grep checks after each task
- [x] Wave 0 covers all MISSING references (N/A — no test framework)
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
