#!/usr/bin/env python3
"""Build src/IFVG_Strategy.pine from src/IFVG_Indicator.pine.

The strategy is the indicator with a strategy() declaration and the order block in
tools/strategy_orders.pine appended. Edit the indicator, then run:
    python3 tools/build_strategy.py
"""
import pathlib
import re
import sys

root = pathlib.Path(__file__).resolve().parent.parent
src = (root / "src" / "IFVG_Indicator.pine").read_text()
orders = (root / "tools" / "strategy_orders.pine").read_text()

declaration = '''// GENERATED from src/IFVG_Indicator.pine by tools/build_strategy.py - do not edit by hand
strategy("IFVG Strategy", shorttitle="IFVG Strat", overlay=true,
         max_bars_back=500,
         max_boxes_count=500,
         max_lines_count=500,
         max_labels_count=500,
         initial_capital=10000,
         currency=currency.USD,
         pyramiding=0,
         process_orders_on_close=true,
         commission_type=strategy.commission.cash_per_contract,
         commission_value=0.62,
         slippage=1)'''

out, n = re.subn(r'indicator\("IFVG Indicator".*?max_labels_count=500\)', lambda m: declaration, src, count=1, flags=re.S)
if n != 1:
    sys.exit("indicator() declaration not found")
(root / "src" / "IFVG_Strategy.pine").write_text(out.rstrip("\n") + "\n" + orders)
print("wrote src/IFVG_Strategy.pine")
