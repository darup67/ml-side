import json,urllib.request,datetime,collections
from zoneinfo import ZoneInfo
u="https://query1.finance.yahoo.com/v8/finance/chart/MNQ=F?interval=5m&range=60d"
r=json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'})))['chart']['result'][0]
q=r['indicators']['quote'][0]
ny=ZoneInfo('America/New_York')
days=collections.defaultdict(list)
for t,o,h,l,c in zip(r['timestamp'],q['open'],q['high'],q['low'],q['close']):
    if None in (o,h,l,c): continue
    dt=datetime.datetime.fromtimestamp(t,ny); m=dt.hour*60+dt.minute
    if dt.weekday()<5 and 570<=m<960: days[dt.date()].append((o,h,l,c))
days={k:v for k,v in days.items() if len(v)>=70}
print(len(days),'RTH days with 5m bars',min(days),max(days))
json.dump({str(k):v for k,v in days.items()},open('mnq_5m_rth.json','w'))
def sim(bars,side,tgt,stp):
    e=bars[0][0]
    for o,h,l,c in bars:
        if side=='L': hit_t=h>=e+tgt; hit_s=l<=e-stp
        else: hit_t=l<=e-tgt; hit_s=h>=e+stp
        if hit_s: return 'stop',-stp            # same-bar ambiguity resolved against you
        if hit_t: return 'win',tgt
    c=bars[-1][3]; p=(c-e) if side=='L' else (e-c)
    return 'time',p
print('contracts tgt_pts | stop | side | win% stop% time% | avg $/day')
for n in (3,4,5,6):
    tgt=500/(2*n)
    for stp in (tgt,tgt/2):
        for side in 'LS':
            res=[sim(b,side,tgt,stp) for b in days.values()]
            w=sum(x[0]=='win' for x in res)/len(res); s=sum(x[0]=='stop' for x in res)/len(res); t=sum(x[0]=='time' for x in res)/len(res)
            pnl=sum(x[1] for x in res)/len(res)*2*n
            print(f"{n}c {tgt:5.1f}pt | stop {stp:5.1f} | {'long ' if side=='L' else 'short'} | {w:4.0%} {s:4.0%} {t:4.0%} | ${pnl:7.0f}")
