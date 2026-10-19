import json,math,os,sys,numpy as np
from collections import defaultdict
D="/home/user/muwon406/docs/석탄_파일럿/"
imf=dict(json.load(open(D+"뉴캐슬_월별가격.json")))
ms=sorted(imf)
def mon(n):
    g=defaultdict(list)
    for k,v in json.load(open(n+"_daily.json")): g[k[:7]].append(v)
    return {m:sum(x)/len(x) for m,x in g.items()}
src={n:mon(n) for n in ["TTF","NG","BZ","AUDUSD","CNY","KRW","IDR","WHC","BDRY","COPPER"] if os.path.exists(n+"_daily.json")}
idx={m:i for i,m in enumerate(ms)}
def lg(d,m,k):
    i=idx[m]
    if i-k<0: return None
    a,b=d.get(m),d.get(ms[i-k])
    return math.log(a/b) if a and b else None
P=dict(imf)
feat={}  # name -> {m:val}
def add(name,fn):
    feat[name]={m:v for m in ms if (v:=fn(m)) is not None}
for k in (1,3,6,12): add(f"석탄_r{k}",lambda m,k=k:lg(P,m,k))
def dev(m):
    i=idx[m]
    if i<12: return None
    return math.log(P[m]/np.mean([P[ms[j]] for j in range(i-11,i+1)]))
add("석탄_이평괴리12",dev)
for n,lab in [("TTF","TTF"),("NG","헨리허브"),("BZ","브렌트"),("AUDUSD","호주달러"),("CNY","위안"),("IDR","루피아"),("WHC","WHC주가"),("COPPER","구리"),("BDRY","건화물ETF")]:
    if n in src:
        for k in (1,3): add(f"{lab}_r{k}",lambda m,n=n,k=k:lg(src[n],m,k))
if "BZ" in src:
    add("석탄/브렌트_괴리",lambda m:(math.log(P[m]/src["BZ"][m]) - np.mean([math.log(P[ms[j]]/src["BZ"][ms[j]]) for j in range(max(0,idx[m]-35),idx[m]+1) if ms[j] in src["BZ"]])) if m in src["BZ"] and idx[m]>=36 else None)
def target(m,h):
    i=idx[m]
    return math.log(P[ms[i+h]]/P[m]) if i+h<len(ms) else None
SETS={
 "A 석탄 자체 추세":[f for f in feat if f.startswith("석탄_")],
 "B +가스·유가·환율":[f for f in feat if f.startswith("석탄_") or f.split("_")[0] in("헨리허브","브렌트","호주달러","위안","루피아","구리","석탄/브렌트")],
 "C +TTF·주가·ETF":[f for f in feat if not f.startswith("건화물")],
}
def ridge(X,y,lam):
    mu,sd=X.mean(0),X.std(0)+1e-9; Z=(X-mu)/sd
    b=np.linalg.solve(Z.T@Z+lam*np.eye(Z.shape[1]),Z.T@(y-y.mean()))
    return lambda x:((x-mu)/sd)@b+y.mean()
def run(fs,h,lam,start_oos="2014-01"):
    rows=[m for m in ms if all(m in feat[f] for f in fs) and target(m,h) is not None]
    X=np.array([[feat[f][m] for f in fs] for m in rows]); y=np.array([target(m,h) for m in rows])
    out=[]
    for t,m in enumerate(rows):
        if m<start_oos: continue
        tr=[j for j in range(t) if idx[rows[j]]+h<=idx[m]]  # 정보 시점 이후 타깃 제외
        if len(tr)<48: continue
        f=ridge(X[tr],y[tr],lam)
        out.append((m,float(f(X[t])),float(y[t]),float(y[tr].mean()),float(X[t][0]) if fs[0]=="석탄_r1" else 0.0))
    return out
def score(out,label,h):
    p=np.array([o[1] for o in out]);a=np.array([o[2] for o in out]);b=np.array([o[3] for o in out])
    r2=1-((a-p)**2).sum()/((a-b)**2).sum()
    da=np.mean(np.sign(p)==np.sign(a))
    c=np.corrcoef(p,a)[0,1]
    # 순열 검정
    rng=np.random.default_rng(1); perm=[np.mean(np.sign(p)==np.sign(rng.permutation(a))) for _ in range(2000)]
    pv=np.mean(np.array(perm)>=da)
    big=np.abs(a)>np.quantile(np.abs(a),.75)
    dab=np.mean(np.sign(p[big])==np.sign(a[big]))
    return dict(구분=label,h=h,월수=len(out),기간=[out[0][0],out[-1][0]],OOS_R2=round(float(r2),3),방향적중=round(float(da),3),방향_p값=round(float(pv),3),상관=round(float(c),3),큰변동_상위25퍼_적중=round(float(dab),3),적중_기준=round(float(np.mean(a>0)),3))
res=[]
for h in (1,3):
    for name,fs in SETS.items():
        for lam in (30,300):
            out=run(fs,h,lam)
            if len(out)<30: continue
            r=score(out,f"{name} (λ={lam})",h); res.append(r); print(r)
json.dump(res,open("wf_out.json","w"),ensure_ascii=False)
