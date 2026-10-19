import json,math,numpy as np
from collections import defaultdict
D="/home/user/muwon406/docs/석탄_파일럿/"
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf)
def mon(n):
    g=defaultdict(list)
    for k,v in json.load(open(n+"_daily.json")): g[k[:7]].append(v)
    return {m:sum(x)/len(x) for m,x in g.items()}
ttf=mon("TTF"); bz=mon("BZ")
r={ms[i]:math.log(imf[ms[i]]/imf[ms[i-1]]) for i in range(1,len(ms))}
rk=sorted(r)
def gr(d): return {rk[i]:math.log(d[rk[i]]/d[rk[i-1]]) for i in range(1,len(rk)) if rk[i] in d and rk[i-1] in d}
gt=gr(ttf); gb=gr(bz)
z=1.2816  # 80% 구간
res={}
def evalm(name,sig_fn,start=48):
    cov=0;n=0;wid=[];pin=0
    for i in range(start,len(rk)):
        m=rk[i]; s=sig_fn(i)
        if s is None: continue
        a=r[m]; lo,hi=-z*s,z*s   # 평균 0 가정(예측 불가 확인됨)
        cov+=lo<=a<=hi; n+=1; wid.append(hi-lo)
        # 구간점수(Winkler)
        pin+=(hi-lo)+(10 if a<lo else 0)*(lo-a)+(10 if a>hi else 0)*(a-hi)
    return dict(모델=name,월수=n,구간적중=round(cov/n,3),평균폭=round(float(np.mean(wid)),3),Winkler=round(pin/n,4))
rv=np.array([r[m] for m in rk])
def const(i): return rv[:i].std()
def roll12(i): return rv[i-12:i].std()
def ewma(i,lam=0.94):
    v=rv[:12].var()
    for j in range(12,i): v=lam*v+(1-lam)*rv[j]**2
    return math.sqrt(v)
def ewma_gas(i):
    base=ewma(i)
    # 가스·유가 최근 3개월 변동성 비율로 조정
    ks=[rk[j] for j in range(i-3,i)]
    if not all(k in gt for k in ks) or i<60: return None
    gv=np.sqrt(np.mean([gt[k]**2 for k in ks])); hist=[gt[rk[j]]**2 for j in range(i) if rk[j] in gt]
    if len(hist)<12: return None
    return base*(0.5+0.5*gv/np.sqrt(np.mean(hist)))
out=[]
start=48
for nm,f in [("전 기간 고정 변동성",const),("직전 12개월 변동성",roll12),("EWMA(λ=0.94)",ewma)]:
    out.append(evalm(nm,f))
# 같은 기간(가스 데이터 있는 구간) 비교
def only(f): return lambda i: f(i) if rk[i]>="2020-01" else None
for nm,f in [("[2020~] 전 기간 고정",const),("[2020~] EWMA",ewma),("[2020~] EWMA+TTF 변동성",ewma_gas)]:
    out.append(evalm(nm,only(f)))
for o in out: print(o)
# 다음 달 |변동| 예측력: 직전 EWMA와 실제 |r| 상관
pred=np.array([ewma(i) for i in range(start,len(rk))]); act=np.abs(rv[start:])
print("EWMA vs 실제 |변동| 상관",round(float(np.corrcoef(pred,act)[0,1]),3), "순위상관", round(float(np.corrcoef(np.argsort(np.argsort(pred)),np.argsort(np.argsort(act)))[0,1]),3))
json.dump(out,open("vol_out.json","w"),ensure_ascii=False)
