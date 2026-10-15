"""Feature breakdown (tag keys) for the trades of the given grades.
Usage: python3 tools/backtest/grade_features.py <Trades.csv> <risk USD> "A-,A"
Prints the net result in R per value of each tag key (sw, dl, mo, si, tg, pd, tt, sx, ss, bi, lr, exit)."""
import csv,sys
from collections import defaultdict
risk=float(sys.argv[2])
T={}
for r in csv.DictReader(open(sys.argv[1])):
    t=T.setdefault(r['Trade number'],{})
    if r['Type'].startswith('Entry'):
        t['tag']=r['Signal']; t['pnl']=float(r['Net PnL USD'])
    else: t['exit']=r['Signal']
tr=[]
for t in T.values():
    if ' | ' in t.get('exit',''): t['exit'],t['tag']=t['exit'].split(' | ',1)
    p=t['tag'].split('|'); t['grade']=p[0]
    for kv in p[1:]:
        k,v=kv.split('=',1); t[k]=v
    tr.append(t)
grades=sys.argv[3].split(',')
sel=[t for t in tr if t['grade'] in grades]
def show(key):
    b=defaultdict(list)
    for t in sel: b[t.get(key,'?')].append(t['pnl'])
    print(key,' '.join(f"{k}:n{len(v)} {sum(v)/risk:+.1f}R" for k,v in sorted(b.items())))
print(grades,len(sel),f"{sum(t['pnl'] for t in sel)/risk:+.1f}R")
for k in ['sw','dl','mo','si','tg','pd','tt','sx','ss','bi','lr','exit']: show(k)
