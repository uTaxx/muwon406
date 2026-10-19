import json,subprocess,sys,time,datetime,calendar
sym,name,start,end=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
out={}
for y in range(start,end+1,3):
    p1=calendar.timegm((y,1,1,0,0,0)); p2=calendar.timegm((min(y+2,end),12,31,23,59,59))
    url=f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}?period1={p1}&period2={p2}&interval=1d"
    for k in range(4):
        r=subprocess.run(["curl","-s","-m","40","-A","Mozilla/5.0 (X11; Linux x86_64)",url],capture_output=True,text=True).stdout
        try:
            d=json.loads(r)["chart"]["result"]
            break
        except Exception: time.sleep(8); d=None
    if d:
        d=d[0]
        for t,c in zip(d.get("timestamp",[]),d["indicators"]["quote"][0]["close"]):
            if c is not None: out[datetime.datetime.utcfromtimestamp(t).date().isoformat()]=round(c,4)
    time.sleep(5)
json.dump(sorted(out.items()),open(name+"_daily.json","w"))
ks=sorted(out); print(sym,len(out),ks[:1],ks[-1:])
