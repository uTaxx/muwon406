import json,math,datetime,numpy as np
D="/home/user/muwon406/docs/석탄_파일럿/"
m=json.load(open("MTF_daily.json")); d=[k for k,_ in m]; v=np.array([x for _,x in m])
lr=np.r_[0,np.diff(np.log(v))]
roll=np.zeros(len(d),bool)
for i in range(2,len(d)-1):
    new=d[i][:7]!=d[i-1][:7]; nxt=d[i+1][:7]!=d[i][:7]; second=d[i-1][:7]!=d[i-2][:7]
    if abs(lr[i])>0.08 and (new or second or nxt): roll[i]=True
adj=np.where(roll,0,lr); cum=np.cumsum(adj)
ev=json.load(open(D+"주요사건_일자.json")); sg={"상승":1,"하락":-1}
cand=[]
for e in ev:
    dt=e["일자"]
    if not(isinstance(dt,str) and len(dt)==10 and dt[0] in "12") or e["방향"] not in sg: continue
    if not("2010-12-20"<=dt<="2025-11-01"): continue
    cand.append((dt,sg[e["방향"]],e["id"]))
cand.sort()
# 5일 이내 같은 방향은 하나
ev_u=[]
for c in cand:
    if ev_u and ev_u[-1][1]==c[1] and (datetime.date.fromisoformat(c[0])-datetime.date.fromisoformat(ev_u[-1][0])).days<=14:
        ev_u[-1][2].append(c[2]); continue
    ev_u.append([c[0],c[1],[c[2]]])
import bisect
H=(5,21,63)
def r_after(i,h): return cum[i+h]-cum[i] if i+h<len(d) else None
rows=[]
for dt,s,ids in ev_u:
    i=bisect.bisect_left(d,dt)
    rows.append(dict(일자=dt,방향=s,사건=ids,**{f"h{h}":None if (x:=r_after(i,h)) is None else round(s*x*100,1) for h in H}))
for r in rows: print(r)
rng=np.random.default_rng(406)
valid=np.arange(5,len(d)-64)
res=[]
for h in H:
    v_=[r[f"h{h}"] for r in rows if r[f"h{h}"] is not None]; obs=np.mean(v_)/100; n=len(v_)
    null=[]
    for _ in range(5000):
        ii=rng.choice(valid,n); ss=rng.choice([-1,1],n); null.append(np.mean([s*(cum[i+h]-cum[i]) for i,s in zip(ii,ss)]))
    p=np.mean(np.array(null)>=obs)
    res.append(dict(h거래일=h,표본=n,평균_부호수익률_pct=round(obs*100,2),방향일치=round(float(np.mean(np.array(v_)>0)),3),p값=round(float(p),4),무작위_표준편차_pct=round(float(np.std(null)*100),2)))
    print(res[-1])
json.dump(dict(요약=res,행=rows),open("ev3_out.json","w"),ensure_ascii=False,indent=1)
# 월평균 모멘텀의 기계적 자기상관
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf)
r=np.diff(np.log([imf[x] for x in ms])); print("IMF 월수익률 1차 자기상관",round(float(np.corrcoef(r[1:],r[:-1])[0,1]),3))
