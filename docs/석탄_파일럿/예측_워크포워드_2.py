import json,math,numpy as np
code=open("wf.py").read().split("res=[]")[0]
code=code.replace('"BDRY","COPPER"]','"BDRY","COPPER","SHENHUA","ADRO","ITMG","YAL","BTU"]')
exec(code)
for n,lab in [("SHENHUA","중국신화주가"),("ADRO","인니ADRO주가"),("ITMG","인니ITMG주가"),("YAL","YAL주가"),("BTU","BTU주가")]:
    if n in src and len(src[n])>100:
        for k in (1,3): add(f"{lab}_r{k}",lambda m,n=n,k=k:lg(src[n],m,k))
add("계절_sin",lambda m:math.sin(2*math.pi*int(m[5:])/12)); add("계절_cos",lambda m:math.cos(2*math.pi*int(m[5:])/12))
# 정책 점수: 최초 보도일 기준(사건 월 말까지 알려진 것만), 반감기 약 2개월
ev=json.load(open(D+"주요사건_일자.json"))
E=[(e["일자"][:7],{"상승":1,"하락":-1}[e["방향"]]) for e in ev if isinstance(e["일자"],str) and len(e["일자"])==10 and e["방향"] in("상승","하락")]
E=sorted(set(E))
def pol(m):
    s=0.0
    for em,d in E:
        if em<=m: s+=d*math.exp(-(idx[m]-idx[em])/3.0)
    return s
add("정책점수",pol)
add("정책점수_변화",lambda m:(pol(m)-pol(ms[idx[m]-1])) if idx[m]>=1 else None)
base=[f for f in feat if f.startswith("석탄_") and "괴리" not in f]
SETS={
 "A 석탄 추세":base,
 "A+계절":base+["계절_sin","계절_cos"],
 "B +가스·유가·환율·구리":base+[f for f in feat if f.split("_")[0] in("헨리허브","브렌트","호주달러","위안","루피아","구리")],
 "D A+정책점수(사건 기반)":base+["정책점수","정책점수_변화"],
 "E A+중국·인니·호주 석탄사 주가":base+[f for f in feat if f.split("_")[0] in("중국신화주가","인니ADRO주가","인니ITMG주가","WHC주가")],
 "F A+계절+정책+주가":base+["계절_sin","계절_cos","정책점수","정책점수_변화"]+[f for f in feat if f.split("_")[0] in("중국신화주가","인니ADRO주가","인니ITMG주가","WHC주가")],
}
res=[]
for h in (1,3):
    for name,fs in SETS.items():
        for lam in (100,300):
            out=run(fs,h,lam,start_oos="2014-01")
            if len(out)<30: print("표본부족",name);continue
            r=score(out,f"{name} (λ={lam})",h); res.append(r); print(r["구분"],h,r["월수"],r["기간"],"R2",r["OOS_R2"],"적중",r["방향적중"],"p",r["방향_p값"],"큰변동",r["큰변동_상위25퍼_적중"])
json.dump(res,open("wf2_out.json","w"),ensure_ascii=False)
