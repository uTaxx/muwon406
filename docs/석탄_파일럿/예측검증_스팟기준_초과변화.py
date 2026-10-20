exec(open("m2.py").read().split("sets={")[0])
# 1) 기준선 비교: 다음 달 평균을 (a) 이번 달 평균 그대로, (b) 말일 현물 그대로, (c) 릿지 모델로 예측
def tgt_spot(m):   # 다음 달 MTF 평균 / 이번 달 말일 MTF — 현물을 기준으로 한 초과 변화
    n=nxt(m); 
    if n in agg["MTF"] and m in agg["MTF"]: return lr(agg["MTF"][n]["avg"],agg["MTF"][m]["end"])
months=[m for m in ms if m>="2014-01" and tgt_mtf(m) is not None and m in feat["MTF_gap"]]
A=np.array([tgt_mtf(m) for m in months]); G=np.array([feat["MTF_gap"][m] for m in months])
def r2(P,A): return 1-((A-P)**2).sum()/((A**2).sum())
print("기준선(이번 달 평균 유지) R2 0.000 | 현물 유지(β=1) R2",round(float(r2(G,A)),3),"방향",round(float(np.mean(np.sign(G)==np.sign(A))),3),"n",len(A))
# 2) 현물 기준 초과 변화 예측
res=[]
sets2={
 "초과0 현물만(가스·유가 없음)":["석탄_r1","석탄_이평괴리12"],
 "초과1 +말일 괴리·5일":["MTF_gap","MTF_5d","석탄_r1"],
 "초과2 +가스·유가·환율":["MTF_5d","BZ_5d","NG_5d","AUDUSD_5d","BZ_gap","NG_gap"],
 "초과3 +TTF":["MTF_5d","TTF_5d","TTF_gap","BZ_5d"],
 "초과4 +주가·구리":["MTF_5d","WHC_gap","SHENHUA_gap","COPPER_gap","ADRO_gap"],
}
for nm,fs in sets2.items():
    for lam in (30,300):
        try: P,A2,MM=wf(fs,tgt_spot,lam)
        except Exception as e: print("skip",nm,e); continue
        if len(A2)<30: continue
        da=np.mean(np.sign(P)==np.sign(A2)); rng=np.random.default_rng(1)
        p=np.mean([np.mean(np.sign(P)==np.sign(rng.permutation(A2)))>=da for _ in range(2000)])
        o=dict(구분=nm,lam=lam,n=len(A2),기간=[MM[0],MM[-1]],R2=round(float(1-((A2-P)**2).sum()/((A2-0)**2).sum()),3),방향적중=round(float(da),3),p=round(float(p),3),상관=round(float(np.corrcoef(P,A2)[0,1]),3))
        res.append(o); print(o)
json.dump(res,open("m3_out.json","w"),ensure_ascii=False)
