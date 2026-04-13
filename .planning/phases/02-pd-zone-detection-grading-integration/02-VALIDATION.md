---
phase: 02
slug: pd-zone-detection-grading-integration
status: draft
nyquist_compliant: false
wave_0_complete: true
created: 2026-04-14
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | None — Pine Script has no automated test runner |
| **Config file** | None |
| **Quick run command** | Manual: paste `src/IFVG_Indicator.pine` into TradingView Pine Editor — compile check (syntax-only gate) |
| **Full suite command** | Manual: load on 1H / 4H / D on ≥3 instruments (e.g., NQ1!, EURUSD, BTCUSD) and visually verify all affected features |
| **Estimated runtime** | ~30s per compile check; ~5 min per full visual sweep |

---

## Sampling Rate

- **After every task commit:** Paste-and-compile check in Pine Editor — compile error = fail.
- **After every plan wave:** Load on 1H/4H/D on one test instrument; visually verify all affected features render correctly and no regression in FVG/IFVG/liquidity detection.
- **Before `/gsd-verify-work`:** Full multi-TF / multi-instrument visual sweep must pass.
- **Max feedback latency:** ~60s (compile); ~5 min (visual per chart).

---

## Per-Task Verification Map

> Pine Script has no unit-test framework. "Automated Command" below is the compile-check gate; behavioral verification is visual (see Manual-Only section). Status tracked per task during execution.

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-XX-YY | TBD | TBD | PDZ-01..08, DSH-01..02 | — | N/A (client-side indicator, no auth/IO surface) | compile + visual | Paste into TV Pine Editor (syntax gate) | ✅ | ⬜ pending |

*Task IDs will be populated by gsd-planner once PLAN.md files are generated. Every task inherits the compile-check gate; behavioral gates map to the Manual-Only table below.*

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — no test framework to install, no fixtures to scaffold. Wave 0 is trivially complete for Pine Script projects.

---

## Manual-Only Verifications

Pine Script behaviors cannot be automatically verified; all behavioral checks are visual on TradingView.

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTF dealing range lines render at distinct swing levels | PDZ-01 | Pine Script output is a chart overlay — only visual confirmation possible | Load NQ1! 15m chart, set PD TF = D. Verify 3 dashed lines appear between a specific HTF ITH/ITL pair (not spanning entire chart history). |
| EQ line at 50% midpoint | PDZ-02 | Visual geometric check | Verify EQ label reads `0.5 (midprice)` and sits halfway between high/low lines. Cross-check: `(swing_high + swing_low) / 2`. |
| Grading +1/-1 effect on identical setups | PDZ-03 | Requires comparing two IFVGs; Pine has no print/log introspection | On a chart with both premium and discount IFVGs, verify bullish IFVG in discount receives higher grade than bullish IFVG in premium (same other modifiers). Hover IFVG label; tooltip should show `pd_score = 2` vs `pd_score = 0`. |
| 3 dashed lines + label format | PDZ-04 | Visual style check | Verify dashed style, width per input, label format `percentage (price)` exactly matches D-08 (e.g., `1 (24,764.25)`, `0.5 (24,270.00)`, `0 (23,775.50)`). |
| Zone fill toggle | PDZ-05 | Visual toggle | Toggle `i_show_pd_fills` — verify `linefill` shading appears/disappears between correct line pairs (premium above EQ, discount below EQ). |
| OTE band toggle | PDZ-06 | Visual toggle | Toggle `i_show_ote` — verify 62%–79% band renders within range; visual only (no grading change). |
| Grade distribution balanced | PDZ-07 | Requires manual tally over N setups | On representative chart (~50 IFVGs), count grade distribution. No single grade >40%. |
| `pd_zone` stored on IFVG | PDZ-08 | Tooltip inspection | Hover IFVG label; tooltip reflects current zone ("premium"/"discount"/"equilibrium"/"neutral") and `pd_score`. |
| Dashboard PD Zone row | DSH-01 | Visual | Verify row shows PREMIUM (red) / DISCOUNT (green) / EQ (yellow) / — (gray) matching current price position. |
| Dashboard Range % row | DSH-02 | Visual | Verify integer 0–100% displayed; cross-check `(mid - low) / (high - low) * 100`. No decimals, no arrows. |
| HTF fallback (chart TF ≥ PD TF) | D-05 | Visual | On Daily chart with PD TF = D, verify feature still functions using chart-TF ITH/ITL (no repaint, no missing lines). |
| Rotation on new ITH/ITL | D-02 | Multi-bar observation | Wait for or backtest a chart where a new unswept ITH forms above current; verify lines rotate (old deleted, new drawn) within 1–2 bars of confirmation. |
| No repainting | Convention | Historical comparison | Compare real-time and replayed chart at same bar; lines/zones should match. |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` compile-check gate + mapped Manual-Only behavioral verification
- [ ] Sampling continuity: no 3 consecutive tasks without compile check
- [ ] Wave 0 trivially complete (no framework needed)
- [ ] No watch-mode flags
- [ ] Feedback latency: compile ~60s, visual ~5min per chart
- [ ] `nyquist_compliant: true` set in frontmatter once planner populates task IDs

**Approval:** pending
