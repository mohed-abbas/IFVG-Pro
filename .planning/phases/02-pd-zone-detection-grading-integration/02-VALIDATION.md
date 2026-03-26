---
phase: 02
slug: pd-zone-detection-grading-integration
status: draft
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-26
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — Pine Script has no automated test framework |
| **Config file** | None |
| **Quick run command** | Manual: copy `src/IFVG_Indicator.pine` to TradingView Pine Script Editor, compile, apply to chart |
| **Full suite command** | Manual: visual verification on TradingView across multiple symbols/timeframes |
| **Estimated runtime** | ~2-5 minutes per visual check |

---

## Sampling Rate

- **After every task commit:** Compile in TradingView (catches syntax errors immediately)
- **After every plan wave:** Full visual verification on at least 2 instruments
- **Before `/gsd:verify-work`:** Full suite across 3+ instruments and timeframes
- **Max feedback latency:** ~120 seconds (compile + load)

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Verification Method | Status |
|---------|------|------|-------------|-----------|---------------------|--------|
| 02-01-* | 01 | 1 | PDZ-01, PDZ-02, PDZ-08 | manual | Compile + verify swing detection on Daily TF; check g_pd_swing_high/low update when new pivots confirm | ⬜ pending |
| 02-02-* | 02 | 1 | PDZ-03, PDZ-07 | manual | Compare IFVG grades with/without PD modifier; verify optimal-zone setups get +1, wrong-zone get -1 | ⬜ pending |
| 02-03-* | 03 | 2 | PDZ-04, PDZ-05, PDZ-06, DSH-01, DSH-02 | manual | Verify zone lines at correct price levels; EQ at 50%; OTE at 62%/79%; dashboard shows zone + range % | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. No test framework to install — Pine Script validation is entirely manual/visual.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTF swing detection accuracy | PDZ-01 | Pine Script — no unit tests | Compare indicator swing lines with manual chart analysis on ES/NQ Daily |
| Zone math correctness | PDZ-02 | Visual verification | EQ should be exactly between swing H and swing L; range % should be 0% at low, 50% at EQ, 100% at high |
| Grade impact | PDZ-03 | Compare before/after | Check same setup in discount vs premium produces different grades |
| Zone lines rendering | PDZ-04 | Visual | Lines at correct prices, dashed style, right-edge labels |
| Zone fill rendering | PDZ-05 | Visual | Enable fill toggle, verify colored regions between lines |
| OTE zone rendering | PDZ-06 | Visual | Enable OTE toggle, verify 62% and 79% lines appear |
| Grade distribution balance | PDZ-07 | Statistical | Run on 500+ bars, check no grade >40% of all setups |
| pd_zone stored on IFVG | PDZ-08 | Visual | IFVG label tooltip shows [PREMIUM]/[DISCOUNT] |
| Dashboard PD Zone row | DSH-01 | Visual | Dashboard shows PREMIUM/DISCOUNT with color coding |
| Dashboard Range % row | DSH-02 | Visual | Dashboard shows percentage value updating each bar |

---

## Validation Sign-Off

- [x] All tasks have manual verification procedures
- [x] No automated framework exists for Pine Script — all manual
- [x] Wave 0 is N/A (no test infrastructure to create)
- [x] No watch-mode flags
- [x] Feedback latency ~120s (compile + chart load)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
