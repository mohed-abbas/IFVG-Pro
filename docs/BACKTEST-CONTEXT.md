# Backtest Context

Working notes for the strategy backtests: who trades it, how, and the rules we follow so
results stay comparable. Read this before running or analysing a backtest. Results live in
[`BACKTEST-LOG.md`](BACKTEST-LOG.md), exports in `backtesting/<series>/`.

## The trader's setup

- **Market:** MNQ1! (micro Nasdaq), prop account **Lucid Flex 50K** ($2,000 trailing EOD
  drawdown, $3,000 target, 50% consistency, flat by 16:45 NY), commission **0.5 per
  contract**.
- **Entry timeframes:** **1m, 3m and 5m**. 15m is not traded; 15m results do not decide
  anything.
- **Exit:** size to the IFVG box edge and exit on a **candle close beyond the box** (Stop Mode
  "Close beyond box"), with **Stop Loss Type Strong High/Low** as the safety stop (S2-3:
  same trades, tail losses cut from −5.9R to −2.6R).
- **Risk:** **$150 per trade** with this exit, because a close beyond the box overshoots the
  box edge (losses average about 1.15–1.3R). Comfortable loss is about $200; $200–250 per
  trade only if results justify it.
- **Take profit:** **Fixed R:R 1:1.5** in every test so far. Setup-based targets (DOL/LRLR)
  are not tested yet.

### Indicator inputs (baseline S2-3b)

| Group | Setting |
|---|---|
| FVG Detection | ATR 14, **Min Gap 0.5** (the trader's usual 0.1 lost money: tiny boxes, big size, high commission) |
| HTF | 1h / 1h, Filter LTF by HTF Bias off (display only) |
| PD Zones | PD Timeframe 1h, sweep wick 0.05 |
| EQH/EQL | Perfect 0.02, Relative 0.05, Require Intact on |
| Grading | Stop Loss Type Strong High/Low |
| Risk | Account 50000, USD, Risk 150, Fixed R:R 1.5, **Min Grade (Stats & Strategy) B-** |
| Strategy | Stop Mode Close beyond box, HTF Bias Filter All, all sessions, flat at 1645 |
| Properties | Initial capital 50,000, **leverage 50x long and short**, commission 0.5/contract, slippage 1 tick |

## Rules for testing

1. **Change one setting per run** and compare with the run it came from. S2-2 changed two
   settings at once and could not be read.
2. **Confirm on another window before acting on a finding.** In-sample S2-3b said "B+ loses,
   A- wins"; out-of-sample (Jul 3 – Aug 3) flipped it. Only findings that hold in both
   windows count. Use Bar Replay or Trade From/Until for older windows (TradingView
   Essential loads ~10K bars: ~7 days on 1m, ~3 weeks on 3m, ~5 weeks on 5m).
3. **Trust the Strategy Tester, not the chart's grade table.** The grade table is the
   indicator's own model: every setup, close-beyond exits, no commission.
4. **Do not read grades from "By signals" across runs with a different Stop Loss Type**
   (fixed now, see below) or different detection settings: the trade set changes.
5. **Settings that change the trade set:** Min Gap Size, ATR period, Min Grade, HTF Bias
   Filter, session checkboxes. With Min Grade B- or All, HTF/PD timeframes only change grades
   and tags, not which trades are taken.
6. The strategy has its **own copy of every indicator input**. Changing the strategy's
   settings never changes the indicator on the chart, and the other way round. Hide the
   indicator while backtesting; copy settings into both when they are final.

## Workflow

1. Run in TradingView and export (Strategy Tester → export List of Trades and settings).
   Name it `IFVG_Strat_CME_MINI_MNQ1!_<RUN>.xlsx`. Screenshot the chart tables (monthly
   returns, streaks, prop check): they are not in the export.
2. Copy the export into `backtesting/<series>/<RUN>_<tf>_<change>.xlsx`.
3. Analyse with `tools/backtest/` (`xl2csv.py`, then `analyze.py` / `grade_features.py`).
4. Add the run and its findings to `BACKTEST-LOG.md`.
5. The strategy `src/IFVG_Strategy.pine` is generated: edit `src/IFVG_Indicator.pine` or
   `tools/strategy_orders.pine`, then run `python3 tools/build_strategy.py`. Never edit the
   strategy by hand.
6. Backtesting work runs outside the GSD workflow (the trader's decision).

## Pitfalls already hit

- **0 trades:** Properties leverage left at 1x. One MNQ contract (~$59.6K notional) exceeds
  $50K, and TradingView silently rejects every order. Set 50x.
- **Stop Loss Type changed grades:** the "target closer than the stop" check measured the
  SL line. Fixed: it now measures the box edge, so Stop Loss Type only sets the safety stop.
- **"By signals" showed 5 trades + "Other":** every entry had a unique tag. Fixed: the entry
  comment is the grade, the exit comment is `reason | tag`.
- **"Filter LTF by HTF Bias"** (indicator) only hides boxes; the strategy's own **HTF Bias
  Filter** is the one that filters entries.

## Where we stand (2026-10-15)

- Baseline S2-3b on 5m: PF 1.11 in-sample (Sep 21 – Oct 15), **PF 1.24 out-of-sample**
  (Jul 3 – Aug 3). The first result that held on unseen data.
- Grade rankings are not stable across windows: **do not filter by grade yet.**
- Consistent on 5m: a **minor internal high/low target** does worse than a strong high/low
  target (all 7 5m runs); **Asia** session positive in every run; **NY PM** negative in every
  Series 2 run.
- Next: a "Skip internal-high/low targets" strategy option, tested on both windows; then 3m
  and 1m runs.
