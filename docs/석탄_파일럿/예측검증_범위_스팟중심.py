exec(open("m2.py").read().split("sets={")[0])
import json
mt=agg["MTF"]; mm=sorted(mt)
mi={m:i for i,m in enumerate(mm)}
# 말일 현물 월간 수익률(말일→말일). 계약 전환 구간 영향을 줄이려고 월 단위로만 쓴다.
ret_end={mm[i]:lr(mt[mm[i]]["end"],mt[mm[i-1]]["end"]) for i in range(1,len(mm))}
def ewma_sig(m,lam=0.9):
    ks=[k for k in mm if k<=m and k in ret_end]
    v=np.var([ret_end[k] for k in ks[:12]]) if len(ks)>=12 else 0.01
    for k in ks[12:]: v=lam*v+(1-lam)*ret_end[k]**2
    return math.sqrt(v)
def target(m,h):
    n=nxt(m,h)
    return lr(mt[n]["avg"],mt[m]["end"]) if (n in mt and m in mt) else None
Q=[0.1,0.5,0.9]
def pin(q,y,p): return max(q*(y-p),(q-1)*(y-p))
out=[]
start="2015-01"
for h in (1,2,3):
    rows=[(m,target(m,h),ewma_sig(m)) for m in mm if target(m,h) is not None and m>="2011-01"]
    # 변형: A) 중심=말일 현물, 폭=EWMA×경험분위수 / B) 같은 폭이지만 중심=이번 달 평균(기존 방식) / C) 고정 폭
    res={k:dict(cov=[],pin=0,w=[],n=0) for k in "ABC"}
    for t,(m,y,s) in enumerate(rows):
        if m<start: continue
        past=[(yy,ss) for (mm_,yy,ss) in rows[:t] if mm_<=prv(m,h)]  # 정보 시점 이후 타깃 제외
        if len(past)<36: continue
        z=np.array([yy/ss for yy,ss in past]); qz=np.quantile(z,Q)
        lo,md,hi=[s*x for x in qz]
        # A
        for key,(a,b,c) in {"A":(lo,md,hi)}.items():
            res[key]["cov"].append(a<=y<=c); res[key]["w"].append(c-a); res[key]["pin"]+=sum(pin(q,y,v) for q,v in zip(Q,(a,b,c))); res[key]["n"]+=1
        # B: 중심을 이번 달 평균으로(= 말일 현물 대비 평균 괴리 gap 만큼 이동한 구간)
        gap=lr(mt[m]["avg"],mt[m]["end"])
        a,b,c=lo+gap,md+gap,hi+gap
        res["B"]["cov"].append(a<=y<=c); res["B"]["w"].append(c-a); res["B"]["pin"]+=sum(pin(q,y,v) for q,v in zip(Q,(a,b,c))); res["B"]["n"]+=1
        # C: 고정 폭(전 기간 경험 분위수)
        qy=np.quantile([yy for yy,_ in past],Q)
        res["C"]["cov"].append(qy[0]<=y<=qy[2]); res["C"]["w"].append(qy[2]-qy[0]); res["C"]["pin"]+=sum(pin(q,y,v) for q,v in zip(Q,qy)); res["C"]["n"]+=1
    for k,nm in [("A","현물 중심+변동성 폭"),("B","이번 달 평균 중심+변동성 폭(기존 방식)"),("C","현물 중심+고정 폭")]:
        r=res[k]; o=dict(h=h,모델=nm,n=r["n"],구간적중=round(float(np.mean(r["cov"])),3),평균폭=round(float(np.mean(r["w"])),3),핀볼=round(r["pin"]/r["n"],4)); out.append(o); print(o)
json.dump(out,open("m4_out.json","w"),ensure_ascii=False)
