import json,math,numpy as np
exec(open("ev.py").read().split("rows=[]")[0])
r=np.array([math.log(imf[ms[i]]/imf[ms[i-1]]) for i in range(1,len(ms))]); rm=ms[1:]; ri={m:i for i,m in enumerate(rm)}
phi=float(np.corrcoef(r[1:],r[:-1])[0,1]*r[1:].std()/r[:-1].std())
res_=np.r_[0,r[1:]-phi*r[:-1]]   # 월 평균화로 생기는 기계적 연속분을 제거한 잔차(res_[j]: rm[j] 월)
print("φ",round(phi,3))
rng=np.random.default_rng(406)
def path(j,k): return res_[j+1:j+1+k].sum() if j+k<len(r) else None
out=[]
for k in (1,2,3):
    sel=[(ri[m],d) for (m,d),_ in items if m in ri and path(ri[m],k) is not None]
    v=[d*path(j,k) for j,d in sel]; obs=float(np.mean(v)); n=len(v)
    pool=np.arange(1,len(r)-k)
    null=[np.mean([s*path(j,k) for j,s in zip(rng.choice(pool,n),rng.choice([-1,1],n))]) for _ in range(5000)]
    p=float(np.mean(np.array(null)>=obs))
    out.append(dict(k=k,표본=n,평균_pct=round(obs*100,2),방향일치=round(float(np.mean(np.array(v)>0)),3),p값=round(p,4),무작위_표준편차_pct=round(float(np.std(null)*100),2)))
    print(out[-1])
json.dump(dict(phi=round(phi,3),요약=out),open("ev4_out.json","w"),ensure_ascii=False,indent=1)
