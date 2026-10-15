# Backtest Log

Strategy backtests of `src/IFVG_Strategy.pine` (generated from the indicator by
`tools/build_strategy.py`). Each run changes **one** setting from the run it is compared to.
Raw TradingView exports (List of Trades + all settings) live in `backtesting/<series>/`.

## Common setup

| Item | Value |
|---|---|
| Symbol | CME_MINI:MNQ1! (micro Nasdaq, $2/point) |
| Plan | TradingView Essential (no Deep Backtesting, ~10K bars loaded) |
| Capital | 50,000 USD, Account Size input = 50000 |
| Properties | Commission 0.5/contract (Lucid), slippage 1 tick, leverage 50x long/short |
| Fills | `process_orders_on_close=true`: entry at the inversion candle close |
| Day end | Flat at 16:45 NY, no entries until the 18:00 reopen |
| Prop check | Lucid Flex 50K: $2,000 trailing EOD, $3,000 target, 50% consistency, 40 micros |

**Pitfall:** leverage must be raised from the 1x default. At 1x one MNQ contract (~$59.6K
notional) exceeds the $50K capital and TradingView silently rejects every order (0 trades).

**Analysis:** the per-bucket numbers below are computed from the exported List of Trades,
splitting each trade by its setup tag (`grade|sw=|sx=|tt=|dl=|mo=|si=|tg=|pd=|lr=|ss=|bi=`)
and its exit comment. Series 1 exports carry the tag on the entry row; since Series 2 the
entry comment is the grade alone and the exit comment is `reason | tag`. That makes
TradingView's "Profits and losses → By signals" panel group by grade (with a unique tag per
entry it showed only the 5 most profitable trades and lumped the rest into "Other").

Scripts (standard library only) in `tools/backtest/`:
`xl2csv.py <export.xlsx> <outdir>` splits an export into one CSV per sheet;
`analyze.py <Trades.csv> <risk>` prints the buckets; `grade_features.py <Trades.csv> <risk> "A-,A"`
breaks chosen grades down by tag key.

---

## Series 1: `backtesting/defaults/` (2026-10-15)

All indicator inputs at default (ATR 14, min gap 0.25 ATR, HTF 60/240, PD timeframe D,
Stop Loss Type Strong High/Low, Min Grade All). Only the risk/exit/filter settings in the
table change.

### Runs

| Run | File | TF / range | Risk | R:R | Stop Mode | Bias filter | Trades | Win % | PF | Net | Max DD | Max L streak | Prop (pass/fail) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0 | `00_baseline_5m.xlsx` | 5m, Sep 21 – Oct 15 | $250 | 2 | Close beyond box | n/a | 219 | 32.0% | 0.92 | −$2,393 | $7,260 | 10 | 1 / 4 |
| A | `A_5m_rr1.5.xlsx` | 5m, Sep 21 – Oct 15 | $200 | 1.5 | Close beyond box | All | 233 | 42.9% | 1.01 | +$169 | $4,748 | 10 | 1 / 2 |
| B | `B_5m_sltype-fvg-boundary_INVALID.xlsx` | 5m | $200 | 1.5 | Close beyond box | All | 230 | 43.5% | 0.98 | −$440 | $4,888 | 9 | 0 / 1 |
| B2 | `B2_5m_box-edge.xlsx` | 5m, Sep 21 – Oct 15 | $200 | 1.5 | **Box edge (wick)** | All | 253 | 36.0% | 0.98 | −$343 | $3,144 | 8 | 0 / 2 |
| C1 | `C1_5m_with-bias.xlsx` | 5m, Sep 21 – Oct 15 | $200 | 1.5 | Box edge | **With** | 135 | 33.3% | 0.90 | −$1,298 | $2,716 | 9 | 0 / 1 |
| C2 | `C2_5m_against-bias.xlsx` | 5m, Sep 21 – Oct 15 | $200 | 1.5 | Box edge | **Against** | 131 | 35.9% | 0.97 | −$370 | $1,926 | 5 | 0 / 0 |
| E | `E_15m_box-edge.xlsx` | **15m, Jul 1 – Oct 15** | $200 | 1.5 | Box edge | All | 332 | 34.6% | 0.93 | −$1,952 | $4,648 | 7 | 0 / 2 |

Max L streak excludes BE exits. Run B is **invalid as the planned test**: it changed Stop Loss
Type (Strong High/Low → FVG Boundary) instead of Stop Mode. That removed the hard stop and
re-graded setups (SL level feeds grading); losers worsened to −1.46R.

Run E by month: Jul +$346 · Aug −$2.6k · Sep +$531 · Oct (to the 15th) −$254. First prop
fail 2026-08-14. The loss is concentrated in August; the other months are near flat.

The grade table on the chart (bottom right) is the indicator's own stats model, not the
strategy: every setup counted (no one-position limit), "close beyond box" exits, no
commission. Its numbers will not match the Strategy Tester.

### Exits

| Run | TP | Close beyond box | Hard stop | Box edge | BE |
|---|---|---|---|---|---|
| 0 | 64 × +1.76R | 74 × **−1.32R** | 9 × **−2.15R** | — | 63 × −0.10R |
| A | 95 × +1.27R | 73 × −1.28R | 10 × −2.09R | — | 47 × −0.13R |
| B2 | 86 × +1.27R | — | — | 113 × −0.94R | 47 × −0.12R |
| E | 108 × +1.20R | — | — | 163 × −0.85R | 52 × −0.08R |

R is measured against the $200/$250 risk setting (size is rounded down, so TP ≈ 1.27R at 1:1.5
after commission).

### Bucket profit factors across runs

| Bucket | 0 | A | B2 | C1 | C2 | E (15m) | Verdict |
|---|---|---|---|---|---|---|---|
| Grade B | 1.24 | 1.39 | 1.51 | 1.86 | 1.23 | 1.08 | Holds, weak on 15m |
| Grade B+ | 0.58 | 0.66 | 0.61 | 0.33 | 0.92 | 0.80 | Consistently weak |
| Delivery same-TF | 1.44 | 1.72 | 1.32 | 1.34 | 1.19 | **0.72** | Flipped on 15m |
| Delivery HTF | 0.74 | 0.82 | 0.83 | 0.71 | 0.90 | **1.03** | Flipped on 15m |
| HTF bias with | 0.78 | 0.83 | 0.90 | 0.90 | — | **1.05** | Flipped on 15m |
| HTF bias against | 1.14 | 1.25 | 1.08 | — | 0.97 | **0.82** | Flipped on 15m |
| Session Asia | 1.23 | 1.74 | 1.48 | 1.56 | 1.13 | 1.17 | **Positive in all 6** |
| Session NY AM | 0.55 | 0.62 | 0.79 | 0.64 | 0.91 | 0.64 | **Negative in all 6** |
| Session London | 1.03 | 0.89 | 0.70 | 0.81 | 0.51 | 0.67 | Mostly negative |
| Session NY PM | 0.56 | 0.56 | 0.98 | 0.20 | 1.87 | 1.70 | Noise |

Runs 0–C2 share the same 3.5 weeks, so they are not independent; E (15m, 3.5 months) is the
out-of-sample check.

### Findings

1. **No edge at default settings.** PF 0.90–1.01 on 5m and 0.93 on 15m.
2. **1:1.5 beats 1:2** (Run 0 → A): win rate 32% → 43%, PF 0.92 → 1.01.
3. **"Close beyond box" exits cost more than 1R** (−1.3R average, hard stops −2.1R).
   **Box edge (wick)** caps losses at ~−0.9R and cuts drawdown by a third, but stops out
   ~30 trades that would have recovered to TP, so net is about the same. Box edge kept as the
   default for further tests (predictable loss, prop-friendly drawdown).
4. **HTF bias filter adds nothing**: neither "with" nor "against" is an edge, and their
   relative order flips between 5m and 15m.
5. **Grading does not rank setups**: A and B+ underperform B in every run. The A+ path
   requires strong momentum and HTF delivery, two features that tested neutral to negative.
   A+ is very rare (2 of 253 on 5m) by design: it needs sweep + HTF delivery + strong
   momentum + singular FVG + target beyond stop + correct PD zone.
6. **Only session effects held across timeframes**: Asia positive, NY AM negative.
7. **With Min Grade = All and Bias Filter = All, HTF/PD timeframes do not change which trades
   are taken**, only their grade and tags. Entries depend on FVG detection (ATR period, Min
   Gap Size); exits depend on R:R, Stop Mode and the BE level (swing structure). HTF/PD
   tuning only matters once trades are filtered by grade.

### Code changes made during this series

- `tools/strategy_orders.pine`: **Stop Mode** (Close beyond box / Box edge (wick)),
  **HTF Bias Filter** (All / With / Against, neutral always passes) and **session
  checkboxes** for entries. Defaults reproduce the previous behaviour.
- Noted: the indicator's "Filter LTF by HTF Bias" (HTF Analysis group) only hides IFVG boxes
  on the chart (`src/IFVG_Indicator.pine:3248`); it never filtered strategy entries.

### Next

1. Session filter: untick NY AM (optionally London) on 5m and 15m → `F5`, `F15`.
2. Min Gap Size 0.25 → 0.4 → 0.5 on 15m (detection quality, changes the trade set).
3. Then revisit HTF/PD timeframes and the grading weights (momentum, HTF delivery), testing
   with a grade filter.

---

## Series 2: `backtesting/my-settings/` (2026-10-15)

The settings the trader actually uses, on 5m first (1m and 3m to follow):
ATR 14, **Min Gap 0.1**, HTF **1h / 1h**, PD timeframe **1h**, EQH/EQL perfect 0.02 /
**relative 0.05**, Require Intact on, Stop Loss Type **FVG Boundary**, **Min Grade B-**.
Exit **Close beyond box** (sized to the box edge; with FVG Boundary there is **no safety stop**,
the trade exits only on a candle close),
**risk $150** (this exit overshoots 1R), Fixed 1:1.5, Bias Filter All, all sessions.
Take profit is **Fixed R:R** in every Series 2 run; setup-based targets (DOL/LRLR) are not
tested yet.

### Runs

| Run | File | TF / range | Trades | Win % | PF | Net | Max DD | Max L streak | Prop (pass/fail) |
|---|---|---|---|---|---|---|---|---|---|
| S2-0 | `S2-0_5m_baseline.xlsx` | 5m, Sep 21 – Oct 15 | 308 | 43.8% | 1.00 | −$54 | $4,072 | 7 | 0 / 1 |
| S2-1 | `S2-1_5m_min-gap-0.5.xlsx` | 5m, Sep 21 – Oct 15, **Min Gap 0.5** | 131 | 42.0% | 1.07 | +$669 | $2,175 | 5 | **0 / 0** |
| S2-2 | `S2-2_5m_gap-0.25_sl-strong.xlsx` | 5m, **Min Gap 0.25 + Stop Loss Type Strong High/Low** (two changes) | 238 | 43.3% | 1.06 | +$970 | $3,387 | 9 | 0 / 1 |
| S2-3 | `S2-3_5m_gap-0.5_sl-strong.xlsx` | 5m, S2-1 + **Stop Loss Type Strong High/Low** | 132 | 41.7% | **1.11** | **+$994** | **$1,734** | 5 | **0 / 0** |
| S2-4 | `S2-4_5m_oos_jul3-aug3.xlsx` | 5m, **Jul 3 – Aug 3 (Bar Replay, out-of-sample)**, S2-3b settings | 156 | 43.6% | **1.24** | **+$2,210** | **$1,118** | | |

Exits: 132 TP × +1.26R, 108 close beyond box × **−1.48R**, 64 BE × −0.11R, 4 day end.
Commission $1,421 (5.7% load, avg 4.6 contracts).

### By grade (R = $150)

| Grade | n | Win % | PF | Net |
|---|---|---|---|---|
| A+ | 3 | 67% | 2.44 | +$193 |
| A | 25 | 36% | 0.52 | −$1,595 |
| A- | 55 | 44% | 0.67 | −$2,275 |
| B+ | 72 | 47% | 0.99 | −$40 |
| **B** | 133 | 44% | **1.64** | **+$4,141** |
| B- | 20 | 35% | 0.72 | −$478 |

### Why A / A- lose

The A band is "sweep or delivery" with steps down; two weaknesses are not penalised:

| A / A- trades | S2-0 | Run A | B2 | E (15m) |
|---|---|---|---|---|
| Small gap (singular, < 0.5 ATR, `si=1`) | n67 **−32.6R** | n39 −12.4R | n41 −11.5R | n44 −5.4R |
| Big gap (≥ 0.5 ATR, `si=2`) | n12 **+6.0R** | n15 +8.9R | n16 +6.9R | n22 +2.6R |
| Internal sweep (`sx=int`) | n33 −17.5R | −8.6R | −5.7R | −2.4R |

Over all S2-0 trades, internal sweeps lose (n69, PF 0.54) while strong-level sweeps
(n84, PF 1.31) and session-level sweeps (n9, PF 8.8) win. Min Gap 0.1 makes small gaps the
majority (si=1 is 67 of 80 A/A- trades), and A/A- close-beyond losses average −1.71R.

### Other buckets (S2-0)

- Sessions again: Asia (PF 1.27) and London (1.38) positive; NY AM (0.59), NY PM (0.37),
  Pre-NY (0.70) negative.
- HTF bias with 1.28 vs against 0.80; delivery HTF 0.82 vs same-TF 1.18; PD premium 1.39 vs
  discount 0.83. Single-run, not yet confirmed.

### S2-1: Min Gap 0.1 → 0.5

| Grade | n | Win % | PF | Net |
|---|---|---|---|---|
| A+ | 1 | 0% | 0.00 | −$2 (open at export) |
| A | 4 | 50% | 0.82 | −$75 |
| A- | 19 | 58% | **2.62** | **+$1,260** |
| B+ | 29 | 34% | **0.44** | **−$2,173** |
| B | 57 | 39% | 1.17 | +$604 |
| B- | 21 | 48% | 2.52 | +$1,054 |

- By month: Sep +$927 · Oct (to the 15th) −$257. Prop check never failed (no pass either:
  +$669 is short of the $3,000 target).
- Trades 308 → 131, contracts per trade 4.6 → 2.7, commission $1,421 → $360, max DD
  $4,072 → $2,175. Net −$54 → +$669 (+0.03R per trade): most of the gain is commission and
  the removed small-gap A/A- losers.
- A/A- turned positive (+7.9R); 18 of their 23 trades are big gaps (`si=2`, +9.7R), as
  predicted from S2-0.
- Exits: TP 53 × +1.24R, close beyond box 45 × −1.30R (was −1.48R). Worst loss −5.9R ($884):
  FVG Boundary leaves no safety stop.
- **B+ is weak again (PF 0.44): weak in all 8 runs so far.**
- Sessions: Asia positive again (8 of 8 runs). NY AM positive this time (PF 1.60, n20), the
  first run where it is; Pre-NY and NY PM negative.
- Grade buckets are 4–57 trades over the same 3.5 weeks as S2-0: in-sample only, not proof.

### S2-2: Min Gap 0.25 and Stop Loss Type Strong High/Low (two changes at once)

Both settings changed from S2-1, so their effects cannot be separated.

| Grade | n | Win % | PF | Net |
|---|---|---|---|---|
| A+ | 2 | 100% | — | +$292 |
| A | 9 | 33% | 0.77 | −$172 |
| A- | 36 | 47% | 1.09 | +$277 |
| B+ | 41 | 39% | **0.69** | **−$1,388** |
| B | 119 | 44% | 1.33 | +$2,263 |
| B- | 31 | 42% | 0.89 | −$302 |

- Exits: TP 98 × +1.26R, close beyond box 74 × −1.23R, **hard stop 10 × −2.10R**, BE 49,
  day end 7. Worst loss −3.2R (S2-1: −5.9R). Commission $856, 3.6 contracts per trade.
- By month (chart): Sep +$1.5k, Oct −$164. Prop fail 2026-10-14. Max loss streak 9.
- Gap size again: small gaps (`si=1`) n119 −9.0R, big gaps (`si=2`) n101 +11.2R.
- B+ weak again (9 of 9 runs). Its loss is in **HTF-delivery** B+ setups (n27, −19.0R);
  same-TF delivery B+ made +7.1R. HTF delivery was also below PF 1 on 5m in all Series 1
  runs, yet the grading treats it as the strongest kind of delivery.
- Asia PF 1.90 (positive in 9 of 9 runs). HTF bias "against" beat "with" this time
  (1.27 vs 0.88): the bias split keeps flipping.

### S2-3: S2-1 with Stop Loss Type Strong High/Low (clean one-change test)

- 130 of 132 trades are the same entries as S2-1. On those, net is **+$630 better**, all of
  it from the safety stop: 4 hard stops at −1.81R average. The three that were close-beyond
  exits in S2-1 went −5.89R → −2.37R, −2.80R → −2.63R, −1.69R → −1.19R.
- Max DD $2,175 → **$1,734**, close-beyond losses −1.30R → −1.14R, prop never failed, max
  loss streak 5. By month (chart): Sep +$927, Oct +$68.
- **Verdict: keep Strong High/Low.** Same trades, smaller tail losses.
- **Stop Loss Type regrades setups**: 30 of the 130 shared trades changed grade (17 B+ → B,
  7 B → B-, 5 A- → B+). The S2-1 B+ losers are now in B, so B shows PF 0.83 and B+ 1.36.
  Grade buckets are only comparable between runs with the same Stop Loss Type; the
  features (gap size, delivery source, sweep source) are the stable signal.
- **Cause of the regrading:** the rating system (`briefing/IFVG_Rating_System.pdf`,
  `strategy.md` §6) never ties the grade to the stop type; its only reward/risk wording is
  B- "Risk: Reward sucks". The code turns that into the target check `score_target()`
  (target closer than the stop → one step down) and measures the stop with the SL line, so
  Strong High/Low (a wider stop) fails the check more often. All 30 regraded trades changed
  only in `tg` (2 → 1).
- **Fixed** (`src/IFVG_Indicator.pine`, strategy rebuilt): the target check now measures
  against the IFVG box edge (the planned 1R) whatever the Stop Loss Type, so Stop Loss Type
  only sets the safety stop. With Min Grade B- the trade list cannot change (the target
  step never pushes below B-); only grade labels do. Expected S2-3 retest: same +$994 /
  PF 1.11, grades as in S2-1 (A- 19–20, B+ 29, B 57, B- 20–21).

### S2-3b: S2-3 retested after the target-check fix (`S2-3b_5m_target-fix.xlsx`)

Verified: the same 132 entries with identical exits and P&L (+$994, PF 1.11, max DD $1,734,
prop never failed), and every trade shared with S2-1 now has the same grade as in S2-1.
Stop Loss Type no longer changes grades.

| Grade | n | Win % | PF | Net |
|---|---|---|---|---|
| A+ | 1 | 0% | 0.00 | −$2 |
| A | 5 | 40% | 0.60 | −$224 |
| A- | 19 | 58% | **2.62** | **+$1,260** |
| B+ | 29 | 34% | **0.52** | **−$1,619** |
| B | 57 | 39% | 1.20 | +$680 |
| B- | 21 | 48% | 2.06 | +$898 |

### S2-4: out-of-sample, S2-3b settings on Jul 3 – Aug 3 (Bar Replay)

The edge held on unseen data: 156 trades, PF **1.24**, **+$2,210**, max DD **$1,118**,
commission $283 (2.5%). Exits: TP 65 × +1.16R, close beyond box 46 × −1.13R, hard stop
5 × −1.44R, BE 37.

| Grade | n | Win % | PF | Net | S2-3b PF |
|---|---|---|---|---|---|
| A+ | 1 | 100% | — | +$41 | 0.00 |
| A | 7 | 57% | 1.60 | +$300 | 0.60 |
| A- | 21 | 43% | 0.96 | −$53 | **2.62** |
| B+ | 50 | 48% | **1.44** | **+$1,285** | **0.52** |
| B | 60 | 35% | 0.99 | −$44 | 1.20 |
| B- | 17 | 53% | 1.75 | +$682 | 2.06 |

- **The grade ranking flipped**: B+ (worst in-sample) is the best grade here, A- (best
  in-sample) is flat. Grade buckets are not a stable edge yet; do not filter by grade.
- **Target kind** (`tt`, the nearest liquidity the setup points to) is the most consistent
  split on 5m: an internal high/low target is weaker than a strong high/low target in all
  7 5m runs (S2-4: PF 0.31 vs 1.71; S2-3b: 0.65 vs 1.33; S2-0: 0.72 vs 1.19). On 15m (E) it
  was the other way round.
- Asia positive again (PF 1.67; positive in every run so far). NY PM negative (0.47; below 1 in every
  Series 2 run). HTF bias "with" 1.50 vs "against" 1.01.
