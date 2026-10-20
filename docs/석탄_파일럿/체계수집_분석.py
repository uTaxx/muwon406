import json,math,glob,numpy as np
D="/home/user/muwon406/docs/석탄_파일럿/"
S="/tmp/claude-0/-home-user-muwon406/1aa32843-9b55-5f8f-baa1-b5a6498813ea/scratchpad/coal/"
rows=[]
for f in sorted(glob.glob(S+"sys_S?.json")): rows+=json.load(open(f))
rows.sort(key=lambda r:r["월"])
print("월",len(rows),"사건",sum(len(r["사건"]) for r in rows))
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf); idx={m:i for i,m in enumerate(ms)}
W={"상":3,"중":2,"하":1}; sg={"상승":1,"하락":-1}
def score(r,minimp=2):
    s=0
    for e in r["사건"]:
        if e.get("방향") in sg and W.get(e.get("중요도"),0)>=minimp: s+=sg[e["방향"]]*W[e["중요도"]]
    return s
sc={r["월"]:score(r) for r in rows}
sc_all={r["월"]:score(r,1) for r in rows}
# 통계량
from collections import Counter
print("월별 점수 분포(중요도 중 이상)",Counter(np.sign(list(sc.values()))))
ret=np.array([math.log(imf[ms[i]]/imf[ms[i-1]]) for i in range(1,len(ms))]); rm=ms[1:]; ri={m:i for i,m in enumerate(rm)}
phi=float(np.corrcoef(ret[1:],ret[:-1])[0,1]*ret[1:].std()/ret[:-1].std())
resid=np.r_[0,ret[1:]-phi*ret[:-1]]
def fwd(m,k,adj=True):
    j=ri[m]; 
    if j+k>=len(ret): return None
    return (resid if adj else ret)[j+1:j+1+k].sum()
def same(m): return ret[ri[m]]
rng=np.random.default_rng(406)
out={}
months=[r["월"] for r in rows if r["월"] in ri]
def corrtest(x,y,label):
    x=np.array(x,float);y=np.array(y,float)
    c=np.corrcoef(x,y)[0,1]; null=[np.corrcoef(rng.permutation(x),y)[0,1] for _ in range(5000)]
    p=float(np.mean(np.abs(null)>=abs(c)))
    # 부호 일치(점수≠0)
    nz=x!=0; hit=float(np.mean(np.sign(x[nz])==np.sign(y[nz]))) if nz.any() else None
    return dict(구분=label,표본=len(x),상관=round(float(c),3),p값=round(p,4),점수0아닌_월=int(nz.sum()),방향일치=None if hit is None else round(hit,3))
res=[]
x=[sc[m] for m in months]
res.append(corrtest(x,[same(m) for m in months],"같은 달 수익률"))
for k in (1,2,3):
    mm=[m for m in months if fwd(m,k) is not None]
    res.append(corrtest([sc[m] for m in mm],[fwd(m,k) for m in mm],f"이후 {k}개월 누적(AR1 보정)"))
    res.append(corrtest([sc_all[m] for m in mm],[fwd(m,k) for m in mm],f"[중요도 하 포함] 이후 {k}개월 누적(AR1 보정)"))
for r in res: print(r)
# 점수 부호별 평균
for name,sel in [("순상승(+)",lambda s:s>0),("순하락(-)",lambda s:s<0),("없음/상쇄(0)",lambda s:s==0)]:
    for k in (1,3):
        v=[fwd(m,k) for m in months if sel(sc[m]) and fwd(m,k) is not None]
        print(name,k,"n",len(v),"평균 %.1f%%"%(np.mean(v)*100))
out=dict(요약=res,월수=len(months),사건수=sum(len(r['사건']) for r in rows),phi=round(phi,3))
json.dump(out,open("sys_out.json","w"),ensure_ascii=False,indent=1)
# 워크포워드: 체계 수집 점수를 특징으로
exec(open("wf2.py").read().split("# 정책 점수")[0])
def pol_sys(m):
    s=0.0
    for em,v in sc.items():
        if em<=m and m in idx and em in idx: s+=v*math.exp(-(idx[m]-idx[em])/3.0)
    return s
first=min(sc)
add("체계정책점수",lambda m:pol_sys(m) if m>=first else None)
add("체계점수_당월",lambda m:float(sc.get(m,0)) if m>=first else None)
base=[f for f in feat if f.startswith("석탄_") and "괴리" not in f]
SETS2={"A 석탄 추세":base,"G A+체계 정책점수":base+["체계정책점수","체계점수_당월"],
 "H A+체계+가스·유가":base+["체계정책점수","체계점수_당월"]+[f for f in feat if f.split("_")[0] in("브렌트","헨리허브","호주달러","위안","구리")]}
wres=[]
for h in (1,3):
    for name,fs in SETS2.items():
        for lam in (100,300):
            o=run(fs,h,lam,start_oos="2019-06")
            if len(o)<30: print("표본부족",name,len(o)); continue
            r=score(o,f"{name} (λ={lam})",h); wres.append(r); print(r["구분"],h,r["월수"],r["기간"],"R2",r["OOS_R2"],"적중",r["방향적중"],"p",r["방향_p값"])
json.dump(wres,open("sys_wf_out.json","w"),ensure_ascii=False)
