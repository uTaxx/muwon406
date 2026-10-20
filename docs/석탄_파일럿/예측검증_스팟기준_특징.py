import json,math,os,numpy as np
from collections import defaultdict
D="/home/user/muwon406/docs/석탄_파일럿/"
def load(n): return json.load(open(n+"_daily.json"))
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf)
names=["MTF","TTF","NG","BZ","AUDUSD","CNY","EURUSD","IDR","WHC","SHENHUA","ADRO","COPPER","BDRY"]
ser={n:load(n) for n in names if os.path.exists(n+"_daily.json")}
# 월별 집계: 평균, 말일 값, 5거래일 전 값
agg={}
for n,rows in ser.items():
    g=defaultdict(list)
    for d,v in rows: g[d[:7]].append(v)
    a={}
    for m,vs in g.items():
        a[m]=dict(avg=float(np.mean(vs)),end=vs[-1],ago5=vs[-6] if len(vs)>=6 else vs[0],n=len(vs))
    agg[n]=a
def lr(a,b): return math.log(a/b)
def nxt(m,k=1):
    y,mo=map(int,m.split("-")); mo+=k
    while mo>12: y+=1; mo-=12
    return f"{y}-{mo:02d}"
def prv(m,k=1): return nxt(m,-k)
feat={}
def F(name,fn):
    out={}
    for m in ms:
        try:
            v=fn(m)
        except Exception: v=None
        if v is not None and np.isfinite(v): out[m]=v
    feat[name]=out
for n in ["MTF","TTF","NG","BZ","AUDUSD","CNY","EURUSD","WHC","SHENHUA","ADRO","COPPER"]:
    if n in agg:
        F(n+"_gap",lambda m,n=n: lr(agg[n][m]["end"],agg[n][m]["avg"]))
        F(n+"_5d",lambda m,n=n: lr(agg[n][m]["end"],agg[n][m]["ago5"]))
        F(n+"_r1",lambda m,n=n: lr(agg[n][m]["avg"],agg[n][prv(m)]["avg"]))
F("석탄_r1",lambda m: lr(imf[m],imf[prv(m)]))
F("석탄_r3",lambda m: lr(imf[m],imf[prv(m,3)]))
F("석탄_이평괴리12",lambda m: lr(imf[m],np.mean([imf[prv(m,k)] for k in range(0,12)])))
def tgt(m):  # 다음 달 IMF 월평균 로그수익률
    n=nxt(m); return lr(imf[n],imf[m]) if n in imf else None
def tgt_mtf(m):
    n=nxt(m); return lr(agg["MTF"][n]["avg"],agg["MTF"][m]["avg"]) if n in agg["MTF"] and m in agg["MTF"] else None
def ridge(X,y,lam):
    mu,sd=X.mean(0),X.std(0)+1e-9; Z=(X-mu)/sd
    b=np.linalg.solve(Z.T@Z+lam*np.eye(Z.shape[1]),Z.T@(y-y.mean()))
    return lambda x:((x-mu)/sd)@b+y.mean()
def wf(fs,tgtfn,lam,start="2014-01",minn=36):
    months=[m for m in ms if all(m in feat[f] for f in fs) and tgtfn(m) is not None]
    X=np.array([[feat[f][m] for f in fs] for m in months]);Y=np.array([tgtfn(m) for m in months])
    P=[];A=[];MM=[]
    for t,m in enumerate(months):
        if m<start or t<minn: continue
        f=ridge(X[:t],Y[:t],lam); P.append(float(f(X[t])));A.append(Y[t]);MM.append(m)
    return np.array(P),np.array(A),MM
def score(P,A,label,extra={}):
    r2=1-((A-P)**2).sum()/((A**2).sum())   # 기준: 다음 달 평균 = 이번 달 평균(변화 0)
    da=np.mean(np.sign(P)==np.sign(A)); rng=np.random.default_rng(1)
    p=np.mean([np.mean(np.sign(P)==np.sign(rng.permutation(A)))>=da for _ in range(2000)])
    out=dict(구분=label,n=len(A),R2=round(float(r2),3),방향적중=round(float(da),3),p=round(float(p),3),상관=round(float(np.corrcoef(P,A)[0,1]),3))
    out.update(extra); return out
sets={
 "S0 현물괴리만(MTF_gap)":["MTF_gap"],
 "S1 +5일":["MTF_gap","MTF_5d"],
 "S2 +모멘텀":["MTF_gap","MTF_5d","석탄_r1","석탄_r3"],
 "S3 +가스·유가 말일 정보":["MTF_gap","MTF_5d","BZ_gap","NG_gap","BZ_5d","NG_5d","AUDUSD_5d"],
 "S4 +TTF(2017.11~)":["MTF_gap","MTF_5d","TTF_gap","TTF_5d","BZ_gap","BZ_5d"],
 "S5 +주가·구리":["MTF_gap","MTF_5d","WHC_gap","SHENHUA_gap","COPPER_gap","ADRO_gap"],
}
res=[]
for tg,fn in [("IMF 다음달 평균",tgt),("MTF 다음달 평균",tgt_mtf)]:
    for nm,fs in sets.items():
        for lam in (10,100):
            try:
                P,A,MM=wf(fs,fn,lam)
            except Exception as e:
                print("skip",nm,e); continue
            if len(A)<30: continue
            r=score(P,A,f"{tg} | {nm}",dict(lam=lam,기간=[MM[0],MM[-1]])); res.append(r); print(r)
json.dump(res,open("m2_out.json","w"),ensure_ascii=False)
