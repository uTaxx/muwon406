import json,math,numpy as np
exec(open("ev.py").read().split("rows=[]")[0])
rng=np.random.default_rng(406)
allm=[m for m in ms if idx[m]>=1]
def cont(m,k):
    i=idx[m]
    return math.log(imf[ms[i+k]]/imf[ms[i]]) if i+k<len(ms) else None   # 사건 월 평균 이후의 순수 미래 구간
def test(sel,k,label):
    ms_=[m for (m,d),_ in sel]; ds=[d for (m,d),_ in sel]
    v=[d*cont(m,k) for m,d in zip(ms_,ds) if cont(m,k) is not None]
    obs=np.mean(v); n=len(v)
    null=[]
    for _ in range(5000):
        mm=rng.choice(allm,n,replace=True); dd=rng.choice([-1,1],n)
        w=[x*cont(m,k) for m,x in zip(mm,dd) if cont(m,k) is not None]
        null.append(np.mean(w))
    p=np.mean(np.array(null)>=obs); hit=np.mean(np.array(v)>0)
    return dict(구분=label,k=k,표본=n,평균_pct=round(float(obs*100),2),방향일치=round(float(hit),3),p값=round(float(p),4),무작위_표준편차_pct=round(float(np.std(null)*100),2))
res=[]
cl=lambda m:"2021-12"<=m<="2022-04"
sets={"전체":items,"2021-12~2022-04 제외":[x for x in items if not cl(x[0][0])],
 "러시아·인니 군집 제외+홍수":[x for x in items if not cl(x[0][0])],
 "정책 사건만(중국·인니)":[x for x in items if any(i.startswith(("E01","E02","E03","E06","E07","E10")) for i in x[1])]}
for name,sel in sets.items():
    if name.startswith("러시아"): continue
    for k in (1,2,3):
        r=test(sel,k,name); res.append(r); print(r)
json.dump(res,open("ev2_out.json","w"),ensure_ascii=False,indent=1)
