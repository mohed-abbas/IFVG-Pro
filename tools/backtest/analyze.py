"""Bucket the trades of an exported "List of Trades" by grade, exit, session and setup tag.
Usage: python3 tools/backtest/analyze.py <Trades.csv> <risk USD>
Reads the setup tag from the exit comment ("reason | tag", Series 2+) or from the entry
signal (Series 1 exports). PF and avg R are after commission."""
import csv, sys, datetime as dt
from collections import defaultdict
rows=list(csv.DictReader(open(sys.argv[1])))
risk=float(sys.argv[2]) if len(sys.argv)>2 else 250
T={}
for r in rows:
    n=r['Trade number']; t=T.setdefault(n,{})
    if r['Type'].startswith('Entry'):
        t['tag']=r['Signal']; t['side']=r['Type'].split()[1]; t['time']=float(r['Date and time']); t['qty']=float(r['Size (qty)'])
        t['pnl']=float(r['Net PnL USD']); t['comm']=float(r['Commission USD']); t['bars']=r['Duration (bars)']
    else:
        t['exit']=r['Signal']
trades=list(T.values())
# New format: entry = grade only, exit = "reason | tag"
for t in trades:
    if ' | ' in t.get('exit',''):
        t['exit'],t['tag']=t['exit'].split(' | ',1)
for t in trades:
    p=t['tag'].split('|'); t['grade']=p[0]
    for kv in p[1:]:
        k,v=kv.split('=',1); t[k]=v
    # excel serial -> NY time already (TV exports chart tz)
    d=dt.datetime(1899,12,30)+dt.timedelta(days=t['time']); t['dt']=d; t['hour']=d.hour; t['dow']=d.strftime('%a')
def rep(title,key):
    g=defaultdict(list)
    for t in trades: g[key(t)].append(t)
    print(f'\n## {title}'); print(f"{'bucket':<22}{'n':>5}{'win%':>7}{'PF':>7}{'net':>9}{'avgR':>7}")
    for k in sorted(g, key=lambda k:str(k)):
        L=g[k]; gp=sum(x['pnl'] for x in L if x['pnl']>0); gl=-sum(x['pnl'] for x in L if x['pnl']<=0)
        w=sum(1 for x in L if x['pnl']>0); net=gp-gl
        pf=gp/gl if gl else float('inf')
        print(f"{str(k):<22}{len(L):>5}{100*w/len(L):>6.0f}%{pf:>7.2f}{net:>9.0f}{net/len(L)/risk:>7.2f}")
rep('All',lambda t:'all')
rep('Grade',lambda t:t['grade'])
rep('Exit reason',lambda t:t['exit'])
rep('Session',lambda t:t.get('ss'))
rep('HTF bias',lambda t:t.get('bi'))
rep('Delivery',lambda t:t.get('dl'))
rep('Sweep kind',lambda t:t.get('sw'))
rep('Sweep source',lambda t:t.get('sx'))
rep('Target src',lambda t:t.get('tt'))
rep('PD zone',lambda t:t.get('pd'))
rep('Momentum',lambda t:t.get('mo'))
rep('Side',lambda t:t['side'])
rep('Day',lambda t:t['dow'])
rep('Hour (chart tz)',lambda t:t['hour'])
print('\nloss exits worse than -1.2R:', sum(1 for t in trades if t['pnl']<-1.2*risk))
print('commission total', sum(t['comm'] for t in trades), 'avg qty', sum(t['qty'] for t in trades)/len(trades))
