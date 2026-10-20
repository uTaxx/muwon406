exec(open("m4.py").read().split("Q=[0.1")[0])
tt=agg["TTF"]; tk=sorted(tt)
rt={tk[i]:lr(tt[tk[i]]["end"],tt[tk[i-1]]["end"]) for i in range(1,len(tk))}
def ew(rd,m,lam=0.9):
    ks=[k for k in sorted(rd) if k<=m]
    if len(ks)<12: return None
    v=np.var([rd[k] for k in ks[:12]])
    for k in ks[12:]: v=lam*v+(1-lam)*rd[k]**2
    return math.sqrt(v)
def pin(q,y,p): return max(q*(y-p),(q-1)*(y-p))
Q=[0.1,0.5,0.9]
for h in (1,2,3):
    rows=[]
    for m in mm:
        n=nxt(m,h)
        if n in mt and m in tt:
            s=ewma_sig(m); g=ew(rt,m); 
            if g and m>="2019-01": rows.append((m,lr(mt[n]["avg"],mt[m]["end"]),s,g))
    for alpha in (0.0,0.25,0.5,1.0):
        pins=0;cov=[];n=0
        for t,(m,y,s,g) in enumerate(rows):
            if m<"2021-01": continue
            past=rows[:t]; past=[r for r in past if r[0]<=prv(m,h)]
            if len(past)<24: continue
            gm=np.mean([r[3] for r in past])
            adj=lambda s_,g_: s_*(1-alpha+alpha*g_/gm)
            z=np.array([r[1]/adj(r[2],r[3]) for r in past]); qz=np.quantile(z,Q)
            lo,md,hi=[adj(s,g)*x for x in qz]
            cov.append(lo<=y<=hi); pins+=sum(pin(q,y,v) for q,v in zip(Q,(lo,md,hi))); n+=1
        print(h,"alpha",alpha,"n",n,"적중",round(float(np.mean(cov)),3),"핀볼",round(pins/n,4))
