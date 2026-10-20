import json,math,numpy as np
D="/home/user/muwon406/docs/석탄_파일럿/"
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf); idx={m:i for i,m in enumerate(ms)}
ev=json.load(open(D+"주요사건_일자.json"))
sg={"상승":1,"하락":-1}
u={}
for e in ev:
    dt=e["일자"]
    if not(isinstance(dt,str) and len(dt)==10 and dt[0] in "12") or e["방향"] not in sg: continue
    m=dt[:7]
    if m not in idx or idx[m]<1: continue
    u.setdefault((m,sg[e["방향"]]),[]).append(e["id"])
# 같은 달 같은 방향은 하나로, 2주 안 연쇄(같은 에피소드)도 월 단위로 묶임
items=sorted(u.items())
K=(0,1,2,3,6)
def resp(m,k):
    i=idx[m]
    return math.log(imf[ms[i+k]]/imf[ms[i-1]]) if i+k<len(ms) else None
rows=[]
for (m,d),ids in items:
    r={k:resp(m,k) for k in K}
    rows.append(dict(월=m,방향=d,사건=ids,**{f"k{k}":None if v is None else round(v*100,1) for k,v in r.items()},**{f"부호k{k}":None if v is None else round(d*v*100,1) for k,v in r.items()}))
for r in rows: print(r["월"],r["방향"],",".join(r["사건"]),[r[f"부호k{k}"] for k in K])
# 순열 검정: 같은 월 집합 무작위 방향 vs 무작위 월·방향
rng=np.random.default_rng(406)
allm=[m for m in ms if idx[m]>=1]
def stat(mset,ds,k):
    v=[ds[j]*resp(m,k) for j,m in enumerate(mset) if resp(m,k) is not None]
    return np.mean(v),len(v)
out={}
for k in K:
    obs,n=stat([m for (m,d),_ in items],[d for (m,d),_ in items],k)
    null=[]
    for _ in range(5000):
        ms_=list(rng.choice(allm,len(items),replace=True)); ds=list(rng.choice([-1,1],len(items)))
        null.append(stat(ms_,ds,k)[0])
    p=np.mean(np.array(null)>=obs)
    pos=np.mean([ (r["부호k%d"%k]>0) for r in rows if r["부호k%d"%k] is not None])
    out[k]=dict(평균_부호수익률_pct=round(float(obs*100),2),표본=n,방향일치율=round(float(pos),3),p값=round(float(p),4))
    print(k,out[k])
json.dump(dict(요약=out,행=rows),open("ev_out.json","w"),ensure_ascii=False,indent=1)
