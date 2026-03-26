# Requirements: IFVG Pro

**Defined:** 2026-03-23
**Core Value:** Accurately detect and grade IFVG setups so traders can identify high-probability entries with clear risk management levels

## v1 Requirements

Requirements for the current milestone. Each maps to roadmap phases.

### Bug Fixes & Optimization

- [x] **FIX-01**: Fix hardcoded `fvg_singular = true` that inflates all quality scores by +1
- [x] **FIX-02**: Extract duplicated HTF bias calculation logic into a shared function
- [x] **FIX-03**: Consolidate request.security() calls into tuple syntax (16→2 calls, freeing 14 budget slots)

### Premium/Discount Zones

- [x] **PDZ-01**: Detect HTF swing-based dealing range using ta.pivothigh/ta.pivotlow via request.security()
- [x] **PDZ-02**: Calculate equilibrium (50%), premium zone (above EQ), and discount zone (below EQ)
- [x] **PDZ-03**: Integrate PD zone positioning into grading algorithm (+1 optimal zone, -1 wrong zone)
- [ ] **PDZ-04**: Visualize zone boundaries with dashed lines, labels showing Swing H/L and EQ levels
- [ ] **PDZ-05**: Optional zone fill (linefill) between swing high/EQ and EQ/swing low
- [ ] **PDZ-06**: Visualize OTE zone (62%-79% retracement) with optional toggle
- [x] **PDZ-07**: Recalibrate grade thresholds after adding PD modifier to prevent grade inflation
- [x] **PDZ-08**: Store pd_zone field ("premium"/"discount"/"equilibrium"/"neutral") on IFVG type

### Session Tracking

- [ ] **SES-01**: Detect Asian, London, and NY sessions using time() with IANA timezone strings (DST-safe)
- [ ] **SES-02**: Track session highs and lows in real-time within each session window
- [ ] **SES-03**: Visualize previous session highs/lows as horizontal lines with session labels
- [ ] **SES-04**: User-configurable session times with sensible defaults
- [ ] **SES-05**: Integrate session H/L as Data High/Data Low liquidity type in DOL finder
- [ ] **SES-06**: Auto-disable session tracking on timeframes > 1H (sessions lose meaning)

### Dashboard

- [ ] **DSH-01**: Add PD Zone row showing current zone (PREMIUM/DISCOUNT) with color coding
- [ ] **DSH-02**: Add Range % row showing current position within dealing range (0-100%)
- [ ] **DSH-03**: Add Current Session row showing active session name
- [ ] **DSH-04**: Expand dashboard table from 10 to ~14 rows while maintaining readability

### Alerts

- [ ] **ALT-01**: Valid entry alert with dynamic message (symbol, timeframe, grade, direction, price, BE level, DOL target, PD zone)
- [ ] **ALT-02**: Entry invalidation alert when BE point is taken after valid entry formed
- [ ] **ALT-03**: IFVG mitigation alert when price fully mitigates the zone
- [ ] **ALT-04**: Minimum grade filter input (A+, A, A-, B+, B, All) for entry alerts
- [ ] **ALT-05**: Dual implementation: alertcondition() at global scope for UI + alert() for dynamic messages
- [ ] **ALT-06**: All alerts use freq_once_per_bar_close to prevent repainting alerts

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Advanced Features

- **ADV-01**: SMT divergence detection using correlated symbol data
- **ADV-02**: LRLR trendline liquidity detection (diagonal line rendering)
- **ADV-03**: Killzone time highlighting (background color during active sessions)
- **ADV-04**: Collapsible/tabbed dashboard sections for smaller screens
- **ADV-05**: Extended hours FVG filtering/flagging option

## Out of Scope

| Feature | Reason |
|---------|--------|
| Mobile app / web interface | TradingView-only indicator -- platform handles distribution |
| Backtesting engine | Pine Script strategy scripts are a separate tool type |
| Real-time notifications (push/SMS) | TradingView handles alert delivery -- indicator only sets conditions |
| Reversal/Continuation model detection | Requires complex pattern recognition beyond current scope -- grading captures the essence |
| Auto-trading / order execution | Out of scope -- indicator is decision support, not execution |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FIX-01 | Phase 1 | Complete |
| FIX-02 | Phase 1 | Complete |
| FIX-03 | Phase 1 | Complete |
| PDZ-01 | Phase 2 | Complete |
| PDZ-02 | Phase 2 | Complete |
| PDZ-03 | Phase 2 | Complete |
| PDZ-04 | Phase 2 | Pending |
| PDZ-05 | Phase 2 | Pending |
| PDZ-06 | Phase 2 | Pending |
| PDZ-07 | Phase 2 | Complete |
| PDZ-08 | Phase 2 | Complete |
| DSH-01 | Phase 2 | Pending |
| DSH-02 | Phase 2 | Pending |
| SES-01 | Phase 3 | Pending |
| SES-02 | Phase 3 | Pending |
| SES-03 | Phase 3 | Pending |
| SES-04 | Phase 3 | Pending |
| SES-05 | Phase 3 | Pending |
| SES-06 | Phase 3 | Pending |
| DSH-03 | Phase 3 | Pending |
| DSH-04 | Phase 3 | Pending |
| ALT-01 | Phase 4 | Pending |
| ALT-02 | Phase 4 | Pending |
| ALT-03 | Phase 4 | Pending |
| ALT-04 | Phase 4 | Pending |
| ALT-05 | Phase 4 | Pending |
| ALT-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0

---
*Requirements defined: 2026-03-23*
*Last updated: 2026-03-23 after roadmap creation*
