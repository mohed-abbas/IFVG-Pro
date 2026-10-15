"""Split a TradingView Strategy Tester export (.xlsx) into one CSV per sheet.
Usage: python3 tools/backtest/xl2csv.py <export.xlsx> <outdir>
Standard library only (no openpyxl)."""
import sys, zipfile, csv, re
import xml.etree.ElementTree as ET
ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
src, outdir = sys.argv[1], sys.argv[2]
z=zipfile.ZipFile(src)
names=[s.get('name') for s in ET.fromstring(z.read('xl/workbook.xml')).find('m:sheets',ns)]
def col(ref):
    c=re.match(r'[A-Z]+',ref).group(); n=0
    for ch in c: n=n*26+ord(ch)-64
    return n-1
for i,name in enumerate(names,1):
    root=ET.fromstring(z.read(f'xl/worksheets/sheet{i}.xml'))
    rows=[]
    for r in root.iter('{%s}row'%ns['m']):
        row={}
        for c in r.findall('m:c',ns):
            t=c.get('t'); v=None
            if t=='inlineStr':
                v=''.join(x.text or '' for x in c.iter('{%s}t'%ns['m']))
            else:
                e=c.find('m:v',ns); v=e.text if e is not None else ''
            row[col(c.get('r'))]=v
        if row:
            rows.append([row.get(k,'') for k in range(max(row)+1)])
    with open(f'{outdir}/{name}.csv','w',newline='') as f: csv.writer(f).writerows(rows)
    print(name,len(rows))
