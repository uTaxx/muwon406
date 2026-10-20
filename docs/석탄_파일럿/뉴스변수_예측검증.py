import json,math,numpy as np,collections
D="/home/user/muwon406/docs/석탄_파일럿/"
rows=json.load(open("coal/news_rows2.json"))
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json"))); ms=sorted(imf); idx={m:i for i,m in enumerate(ms)}
topics=["중국 수입","중국 증산·안전","인도네시아","러시아 제재","공급 차질","LNG 차질"]
cnt={t:collections.Counter() for t in topics}; up=collections.Counter(); dn=collections.Counter(); tot=collections.Counter()
for r in rows:
    m=r["기사일"][:7]
    if not("2016-01"<=m<="2025-12"): continue
    cnt[r["질의"]][m]+=1; tot[m]+=1
    if r["규칙방향"]=="상승": up[m]+=1
    if r["규칙방향"]=="하락": dn[m]+=1
news_ms=[m for m in ms if "2016-01"<=m<="2025-12"]
ni={m:i for i,m in enumerate(news_ms)}
def ratio(c,m):
    i=ni[m]
    if i<12: return None
    base=np.mean([c[news_ms[j]] for j in range(i-12,i)])+1
    return math.log((c[m]+1)/base)
feat={}
for t in topics: feat["뉴스_"+t]={m:ratio(cnt[t],m) for m in news_ms if ratio(cnt[t],m) is not None}
feat["뉴스_전체"]={m:ratio(tot,m) for m in news_ms if ratio(tot,m) is not None}
feat["규칙방향점수"]={m:(up[m]-dn[m])/(tot[m]+5) for m in news_ms}
feat["규칙사건비중"]={m:(up[m]+dn[m])/(tot[m]+5) for m in news_ms}
r={ms[i]:math.log(imf[ms[i]]/imf[ms[i-1]]) for i in range(1,len(ms))}
rk=sorted(r); rv=np.array([r[m] for m in rk]); ri={m:i for i,m in enumerate(rk)}
def ewma(i,lam=0.94):
    v=rv[:12].var()
    for j in range(12,i+1): v=lam*v+(1-lam)*rv[j]**2
    return math.sqrt(v)   # i 월까지 알려진 변동성
def ridge(X,y,lam):
    mu,sd=X.mean(0),X.std(0)+1e-9; Z=(X-mu)/sd
    b=np.linalg.solve(Z.T@Z+lam*np.eye(Z.shape[1]),Z.T@(y-y.mean()))
    return lambda x:((x-mu)/sd)@b+y.mean()
def run(target,fs,lam,start="2019-06"):
    months=[m for m in rk if all(m in feat[f] for f in fs) and ri[m]+1<len(rk)]
    X=[];Y=[];M=[]
    for m in months:
        i=ri[m]; nxt=rk[i+1]
        y=abs(r[nxt]) if target=="abs" else r[nxt]
        row=[ewma(i),abs(rv[i])]+[feat[f][m] for f in fs]
        X.append(row);Y.append(y);M.append(m)
    X=np.array(X);Y=np.array(Y)
    P=[];A=[];B=[]
    for t,m in enumerate(M):
        if m<start: continue
        tr=list(range(0,t))
        if len(tr)<36: continue
        f=ridge(X[tr],Y[tr],lam); P.append(float(f(X[t]))); A.append(Y[t]); B.append(float(Y[tr].mean()))
    P=np.array(P);A=np.array(A);B=np.array(B)
    r2=1-((A-P)**2).sum()/((A-B)**2).sum()
    out=dict(n=len(A),R2=round(float(r2),3),상관=round(float(np.corrcoef(P,A)[0,1]),3))
    if target=="signed":
        rng=np.random.default_rng(1); da=np.mean(np.sign(P)==np.sign(A))
        out["방향적중"]=round(float(da),3); out["p"]=round(float(np.mean([np.mean(np.sign(P)==np.sign(rng.permutation(A)))>=da for _ in range(2000)])),3)
    return out
res=[]
sets={"기준(변동성만)":[],"+뉴스 전체량":["뉴스_전체"],"+주제별 뉴스량":["뉴스_"+t for t in topics],"+뉴스량+규칙방향":["뉴스_"+t for t in topics]+["규칙방향점수","규칙사건비중"]}
for tg in ("abs","signed"):
    for nm,fs in sets.items():
        for lam in (30,300):
            o=run(tg,fs,lam); o.update(대상=tg,입력=nm,lam=lam); res.append(o); print(o)
json.dump(res,open("news_an_out.json","w"),ensure_ascii=False)
# 단순 상관: 같은 달 |변동| vs 뉴스량, 다음 달 |변동| vs 뉴스량
for f in ["뉴스_전체","뉴스_중국 수입","뉴스_인도네시아","뉴스_러시아 제재","뉴스_공급 차질","뉴스_LNG 차질","뉴스_중국 증산·안전"]:
    ms2=[m for m in feat[f] if m in ri and ri[m]+1<len(rk)]
    x=np.array([feat[f][m] for m in ms2]); a0=np.array([abs(r[m]) for m in ms2]); a1=np.array([abs(r[rk[ri[m]+1]]) for m in ms2])
    print(f,"같은 달 |변동| 상관",round(float(np.corrcoef(x,a0)[0,1]),3),"다음 달",round(float(np.corrcoef(x,a1)[0,1]),3),len(x))
x=np.array([feat["규칙방향점수"][m] for m in ms2]); y0=np.array([r[m] for m in ms2]); y1=np.array([r[rk[ri[m]+1]] for m in ms2])
print("규칙방향점수 같은 달 수익률 상관",round(float(np.corrcoef(x,y0)[0,1]),3),"다음 달",round(float(np.corrcoef(x,y1)[0,1]),3))
